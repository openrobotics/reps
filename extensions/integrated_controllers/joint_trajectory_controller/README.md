# RosControlJointTrajectoryAPI

Executes a joint trajectory by accepting a `control_msgs/FollowJointTrajectory` action goal and commanding
the simulator to follow the specified trajectory.
Implementation should follow logic similar to the `joint_trajectory_controller` in `ros2_controllers` package.
Implementation needs to check the name for [custom joint names](../../../rep.md#210-custom-names-to-ros-joints) in `ros:joint:name` property of the joint prims and
use it for mapping trajectory points to joints in the simulator.

- `rel ros:joint_trajectory:server`: Reference to a prim with `RosActionAPI`
  for receiving trajectory action goals.
- `rel ros:joint_trajectory:command_joints`: References to prims with `UsdPhysicsJoint`.
- `double ros:joint_trajectory:action_monitor_rate`: Frequency in Hz for
  monitoring trajectory execution progress.
- `double ros:joint_trajectory:stopped_velocity_tolerance`: Velocity tolerance at the end of the trajectory that indicates the controlled system has stopped. Exposed as dynamic parameter.
- `double ros:joint_trajectory:timeout`: Maximum time allowed to reach the trajectory goal.

## Tools

### Schema Definition
The normative OpenUSD schema definition for `RosControlJointTrajectoryAPI` is provided in `schema/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.
