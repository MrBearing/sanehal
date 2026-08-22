cmake_minimum_required(VERSION 3.8)
project(sanehal_operator)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(p9n_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(gamepad_teleop_node src/gamepad_teleop_node.cpp)
target_compile_features(gamepad_teleop_node PUBLIC cxx_std_17)
target_include_directories(gamepad_teleop_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(gamepad_teleop_node
  geometry_msgs p9n_interface rclcpp sensor_msgs)

install(TARGETS gamepad_teleop_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY include/ DESTINATION include)

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
  ament_add_pytest_test(operator_contract test/test_operator_contract.py)
endif()

ament_package()
