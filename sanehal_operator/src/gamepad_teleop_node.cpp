#include "sanehal_operator/gamepad_teleop_node.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <unordered_set>

namespace sanehal_operator
{

namespace
{
const std::unordered_set<std::string> kSupportedButtons = {
  "L1", "R1", "L2", "R2", "Cross", "Circle", "Square", "Triangle"};
}

GamepadTeleopNode::GamepadTeleopNode(const rclcpp::NodeOptions & options)
: Node("gamepad_teleop", options)
{
  const auto hardware = declare_parameter<std::string>("hw_type", "DualSense");
  deadman_button_ = declare_parameter<std::string>("deadman_button", "L1");
  turbo_button_ = declare_parameter<std::string>("turbo_button", "R1");
  frame_id_ = declare_parameter<std::string>("frame_id", "base_footprint");
  linear_speed_ = declare_parameter<double>("linear_speed", 0.05);
  angular_speed_ = declare_parameter<double>("angular_speed", 0.30);
  turbo_linear_speed_ = declare_parameter<double>("turbo_linear_speed", 0.10);
  turbo_angular_speed_ = declare_parameter<double>("turbo_angular_speed", 0.60);
  deadzone_ = declare_parameter<double>("deadzone", 0.10);
  const auto timeout = declare_parameter<double>("joy_timeout", 0.25);
  const auto joy_topic = declare_parameter<std::string>("joy_topic", "joy");
  const auto command_topic = declare_parameter<std::string>(
    "cmd_vel_topic", "/sanehal_base_controller/cmd_vel");

  if (kSupportedButtons.count(deadman_button_) == 0 ||
    kSupportedButtons.count(turbo_button_) == 0 || deadman_button_ == turbo_button_)
  {
    throw std::invalid_argument(
            "deadman_button and turbo_button must be different supported PlayStation buttons");
  }
  if (!(deadzone_ >= 0.0 && deadzone_ < 1.0) || timeout <= 0.0 ||
    linear_speed_ < 0.0 || angular_speed_ < 0.0 ||
    turbo_linear_speed_ < linear_speed_ || turbo_angular_speed_ < angular_speed_)
  {
    throw std::invalid_argument("Invalid teleop speed, deadzone, or timeout parameter");
  }

  gamepad_ = std::make_unique<p9n_interface::PlayStationInterface>(
    p9n_interface::getHwType(hardware));
  joy_timeout_ = std::chrono::duration<double>(timeout);
  last_joy_time_ = std::chrono::steady_clock::now();

  command_publisher_ = create_publisher<TwistStamped>(
    command_topic, rclcpp::QoS(1).reliable().durability_volatile());
  joy_subscription_ = create_subscription<Joy>(
    joy_topic, rclcpp::SensorDataQoS().keep_last(1),
    std::bind(&GamepadTeleopNode::on_joy, this, std::placeholders::_1));
  watchdog_timer_ = create_wall_timer(
    std::chrono::milliseconds(50), std::bind(&GamepadTeleopNode::on_watchdog, this));

  RCLCPP_INFO(
    get_logger(), "PlayStation teleop ready: hw=%s deadman=%s turbo=%s output=%s",
    hardware.c_str(), deadman_button_.c_str(), turbo_button_.c_str(), command_topic.c_str());
}

bool GamepadTeleopNode::button_pressed(const std::string & name) const
{
  if (name == "L1") {return gamepad_->pressedL1();}
  if (name == "R1") {return gamepad_->pressedR1();}
  if (name == "L2") {return gamepad_->pressedL2();}
  if (name == "R2") {return gamepad_->pressedR2();}
  if (name == "Cross") {return gamepad_->pressedCross();}
  if (name == "Circle") {return gamepad_->pressedCircle();}
  if (name == "Square") {return gamepad_->pressedSquare();}
  if (name == "Triangle") {return gamepad_->pressedTriangle();}
  return false;
}

double GamepadTeleopNode::apply_deadzone(double value, double deadzone)
{
  if (!std::isfinite(value) || std::abs(value) <= deadzone) {return 0.0;}
  const double scaled = (std::abs(value) - deadzone) / (1.0 - deadzone);
  return std::copysign(std::clamp(scaled, 0.0, 1.0), value);
}

void GamepadTeleopNode::on_joy(Joy::ConstSharedPtr message)
{
  std::lock_guard<std::mutex> lock(mutex_);
  last_joy_time_ = std::chrono::steady_clock::now();
  joy_received_ = true;
  timeout_stop_sent_ = false;

  try {
    gamepad_->setJoyMsg(message);
    if (!button_pressed(deadman_button_)) {
      if (command_active_) {publish_stop();}
      command_active_ = false;
      return;
    }

    const bool turbo = button_pressed(turbo_button_);
    const double linear_axis = apply_deadzone(gamepad_->tiltedStickLY(), deadzone_);
    const double angular_axis = apply_deadzone(gamepad_->tiltedStickLX(), deadzone_);
    publish_command(
      (turbo ? turbo_linear_speed_ : linear_speed_) * linear_axis,
      (turbo ? turbo_angular_speed_ : angular_speed_) * angular_axis);
    command_active_ = true;
  } catch (const std::exception & error) {
    RCLCPP_ERROR_THROTTLE(
      get_logger(), *get_clock(), 2000, "Invalid Joy message: %s", error.what());
    publish_stop();
    command_active_ = false;
  }
}

void GamepadTeleopNode::on_watchdog()
{
  std::lock_guard<std::mutex> lock(mutex_);
  if (!joy_received_ || timeout_stop_sent_) {return;}
  if (std::chrono::steady_clock::now() - last_joy_time_ > joy_timeout_) {
    RCLCPP_WARN(get_logger(), "Joy input timed out; commanding stop");
    publish_stop();
    command_active_ = false;
    timeout_stop_sent_ = true;
  }
}

void GamepadTeleopNode::publish_command(double linear, double angular)
{
  TwistStamped command;
  command.header.stamp = now();
  command.header.frame_id = frame_id_;
  command.twist.linear.x = linear;
  command.twist.angular.z = angular;
  command_publisher_->publish(command);
}

void GamepadTeleopNode::publish_stop()
{
  publish_command(0.0, 0.0);
}

}  // namespace sanehal_operator

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  try {
    rclcpp::spin(std::make_shared<sanehal_operator::GamepadTeleopNode>());
  } catch (const std::exception & error) {
    RCLCPP_FATAL(rclcpp::get_logger("gamepad_teleop"), "%s", error.what());
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}
