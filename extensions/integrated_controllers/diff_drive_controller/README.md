# RosControlDiffDriveAPI

Controls a differential drive robot by subscribing to a topic with type
`geometry_msgs/Twist` message and converting the commanded linear
and angular velocities into individual wheel velocities applied
to the simulator joints.
The computed velocities should be applied to prims with `UsdPhysicsDriveAPI` (part of the native `USDPhysics`) representing the wheel joints,
and the controller should publish odometry data to a topic with type `nav_msgs/Odometry`.
Implementation should follow logic similar to the `diff_drive_controller` in `ros2_controllers` package.

- `rel ros:diff_drive:subscriber`: relationship targeting a prim with the RosTopicAPI with `role="subscription"` that provides the velocity commands for this controller.
- `rel ros:diff_drive:odom`: Reference to prim with `RosTopicAPI` for publishing odometry data.
- `rel ros:diff_drive:left_wheels`: References to prims with `UsdPhysicsDriveAPI` representing left wheel joints.
- `rel ros:diff_drive:right_wheels`: References to prims with `UsdPhysicsDriveAPI` representing right wheel joints.
- `double ros:diff_drive:wheel_separation`: Distance between left and right wheels in meters.
- `double ros:diff_drive:wheel_radius`: Radius of the wheels in meters.
- `double ros:diff_drive:cmd_vel_timeout`: Timeout in seconds after which the command is considered stale. Exposed as dynamic parameter.
- `double ros:diff_drive:linear:x:max_velocity`: Maximum linear velocity in m/s.
- `double ros:diff_drive:linear:x:max_acceleration`: Maximum linear acceleration in m/s².
- `double ros:diff_drive:angular:z:max_velocity`: Maximum angular velocity in rad/s.
- `double ros:diff_drive:angular:z:max_acceleration`: Maximum angular acceleration in rad/s².

## Tools

### Schema Definition
The normative OpenUSD schema definition for `RosControlDiffDriveAPI` is provided in `schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.
