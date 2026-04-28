# RosControlRigidBodyTwistAPI

Controls a rigid body by subscribing to a topic with type `geometry_msgs/Twist`
and applying the commanded linear and angular velocities directly to the robot's body,
with optional acceleration and velocity limits.
This provides a general-purpose controller for applying velocity commands to a rigid body without wheel kinematics or joint decomposition.

- `rel ros:rigid_body_twist:subscriber`: Reference to a prim with `RosTopicAPI`
  for subscribing to twist control messages.
- `rel ros:rigid_body_twist:body`: Reference to a prim with
  `UsdPhysicsRigidBodyAPI` to which the commanded velocities are applied.

## Tools

### Schema Definition
The normative OpenUSD schema definition for `RosControlRigidBodyTwistAPI` is provided in `schema/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.
