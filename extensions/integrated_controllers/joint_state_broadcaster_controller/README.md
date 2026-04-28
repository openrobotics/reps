# RosControlJointStateBroadcasterAPI

Reads joint states from the simulator and publishes them as `sensor_msgs/JointState` messages to a ROS topic.
Implementation should follow logic similar to the `joint_state_broadcaster` in `ros2_controllers` package.
Implementation needs to check the name for [custom joint names](../../../rep.md#210-custom-names-to-ros-joints) in `ros:joint:name`
property of the joint prims and use it for mapping joints in the simulator to those in robot description or application.

- `rel ros:joint_state_broadcaster:publisher`: relationship targeting a prim with the RosTopicAPI with `role="publisher"` for joint state data.
- `rel ros:joint_state_broadcaster:joints`: References to prims with `UsdPhysicsJoint` representing the joints whose states are to be broadcast.
- `string ros:joint_state_broadcaster:frame_id`: The TF frame ID to be used in the published JointState messages.

## Tools

### Schema Definition
The normative OpenUSD schema definition for `RosControlJointStateBroadcasterAPI` is provided in `schema/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.
