#pragma once

#include <chrono>
#include <functional>
#include <memory>
#include <mutex>
#include <string>

#include <geometry_msgs/msg/twist_stamped.hpp>
#include <p9n_interface/p9n_interface.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>

namespace sanehal_operator
{

class GamepadTeleopNode : public rclcpp::Node
{
public:
  explicit GamepadTeleopNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

private:
  using Joy = sensor_msgs::msg::Joy;
  using TwistStamped = geometry_msgs::msg::TwistStamped;

  bool button_pressed(const std::string & name) const;
  void on_joy(Joy::ConstSharedPtr message);
  void on_watchdog();
  void publish_command(double linear, double angular);
  void publish_stop();
  static double apply_deadzone(double value, double deadzone);

  std::unique_ptr<p9n_interface::PlayStationInterface> gamepad_;
  rclcpp::Subscription<Joy>::SharedPtr joy_subscription_;
  rclcpp::Publisher<TwistStamped>::SharedPtr command_publisher_;
  rclcpp::TimerBase::SharedPtr watchdog_timer_;

  std::string deadman_button_;
  std::string turbo_button_;
  std::string frame_id_;
  double linear_speed_;
  double angular_speed_;
  double turbo_linear_speed_;
  double turbo_angular_speed_;
  double deadzone_;
  std::chrono::duration<double> joy_timeout_;
  std::chrono::steady_clock::time_point last_joy_time_;
  bool joy_received_{false};
  bool command_active_{false};
  bool timeout_stop_sent_{false};
  mutable std::mutex mutex_;
};

}  // namespace sanehal_operator
