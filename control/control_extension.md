# REP XXXX -- OpenUSD Conventions for Simulation Asset Interoperability - Control Extension

## Abstract

This document defines conventions for simulating robotic systems in OpenUSD, with a focus on control interfaces and integration with ROS 2.
It proposes standardized API schemas for exposing robot control interfaces to external control algorithms and for instantiating robot controllers directly within the simulated scene.
The goal is to enable modular and scalable robotic simulation that can be easily integrated with ROS 2-based control frameworks.

## 1. Controllers

In robotic simulation there are two approaches to simulating a robotic system — application level and control level simulation.
In control level simulation, the focus is on the individual components.
This approach is to be used for advanced use cases or validating low level robot controllers. 
In this case the simulator is to expose joint state and command interface to control algorithm using API.
Good example of such API is `hardware_interface` in `ros2_control` package.
The REP-XXXX does not propose shape of the API and interface, and simulators are to build and maintain compatibility with external control frameworks, 
it can be both ROS communication, inter-process communication, a shared library loaded by a simulator process or hardware-in-the loop solution (e.g. CAN bus link).

In application level simulation, the simulator simulates the robot as a whole, including its physical properties, kinematics, and dynamics.
This approach is meant to be used for application testing (e.g. whole robotics stacks, mapping, localization frameworks).
In this approach the controller is integrated in the simulator codebase and managed by parameters of the prim and ROS communication.


### 1.1 External Control Interfaces

The ROS 2 external control `RosControlExternalAPI` is a schema for exposing robot control interfaces to external control algorithms.
This schema is to be included as a built-in schema via `prepend apiSchemas` by a simulator-specific interface for controller.
Simulator loading prim with this schema should establish connection, load controller plugin, spawn a controller instance or set up hardware-in-the-loop connection to the robot controller, 
and expose the control and state interfaces to control entity.

### 1.2 Integrated Controller Simulation

`RosControlIntegratedAPI` allows instantiating robot controllers directly in the simulated scene.
It must reference one or more prims that have [RosTopicAPI](#24-topic-interface-rostopicapi), [RosServiceAPI](#25-service-interface-rosserviceapi) or [RosActionAPI](#26-action-interface-rosactionapi).
This schema is to be included as a built-in schema via `prepend apiSchemas` by a simulator-specific controller schema in the simulator.
Example can be `simulatorXYZ::RosCustomTwistControllerAPI` which will include as built-in `RosControlIntegratedAPI` and reference prims:
- `RosTopicAPI` for subscription of control message.
- `PhysicsRigidBodyAPI` for interaction with the physics engine.

USD does not enforce API schema constraints on referenced prims at the  schema definition level. It is the responsibility of the simulator to validate that all prims referenced by RosControlAPI have at least one of the following API schemas applied: `RosTopicAPI`, `RosServiceAPI` or `RosActionAPI`. 

### 1.2.1 Built-in Controllers

The following schemas are built-in controller schemas that include `RosControlIntegratedAPI` as a built-in via `prepend apiSchemas`. 
Simulators may implement these schemas to provide a standardized control interface for common use cases. 
Such usecase can be different robot locomotion (e.g. Ackermann car-like robot) or application specific interfaces (e.g., joint control interface for robot policy).
The following controllers are proposed as minimal for initial compliance. 
The parameters and logic should follow established controllers in the ROS ecosystem and allow bootstrapping robot simulation with minimal custom development against 
the typical use cases. 
Simulators may choose to implement additional controllers as needed for their specific use cases and robot types, but these four are proposed as a baseline for compliance for 
application level simulation.
The implementation should allow performing multi-robot simulation and control by leveraging the namespaces.

#### 1.2.1.1 RosControlRigidBodyTwistAPI

Controls a rigid body by subscribing to a topic with type `geometry_msgs/Twist`
and applying the commanded linear and angular velocities directly to the robot's body
with optional acceleration and velocity limits. 
This implementation provides a general-purpose controller for applying velocity to a rigid body in a generalized manner.
- `rel ros:rigid_body_twist:subscriber`: Reference to a prim with `RosTopicAPI` 
  for subscribing to twist control messages.
- `rel ros:rigid_body_twist:body`: Reference to a prim with 
  `UsdPhysicsRigidBodyAPI` for applying velocities.

#### 1.2.1.2 RosControlDiffDriveAPI

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

#### 1.2.1.3 RosControlJointTrajectoryAPI

Executes a joint trajectory by accepting a `control_msgs/FollowJointTrajectory` action goal and commanding
the simulator to follow the specified trajectory.
Implementation should follow logic similar to the `joint_trajectory_controller` in `ros2_controllers` package.
Implementation needs to check the name for [custom joint names](rep.md#29-custom-names-to-ros-joints) in `ros:joint:name` property of the joint prims and 
use it for mapping trajectory points to joints in the simulator.

- `rel ros:joint_trajectory:server`: Reference to a prim with `RosActionAPI` 
  for receiving trajectory action goals.
- `rel ros:joint_trajectory:command_joints`: References to prims with `UsdPhysicsJoint`.
- `double ros:joint_trajectory:action_monitor_rate`: Frequency in Hz for 
  monitoring trajectory execution progress.
- `double ros:joint_trajectory:stopped_velocity_tolerance`: Velocity tolerance at the end of the trajectory that indicates the controlled system has stopped. Exposed as dynamic parameter.
- `double ros:joint_trajectory:timeout`: Maximum time allowed to reach the trajectory goal.

#### 1.2.1.4 RosControlJointStateBroadcasterAPI

Reads joint states from the simulator and publishes them as `sensor_msgs/JointState` messages to a ROS topic.
Implementation should follow logic similar to the `joint_state_broadcaster` in `ros2_controllers` package.
Implementation needs to check the name for [custom joint names](rep.md#29-custom-names-to-ros-joints) in `ros:joint:name` 
property of the joint prims and use it for mapping joints in the simulator to those in robot description or application.

- `rel ros:joint_state_broadcaster:publisher`: relationship targeting a prim with the RosTopicAPI with `role="publisher"` for joint state data.
- `rel ros:joint_state_broadcaster:joints`: References to prims with `UsdPhysicsJoint` representing the joints whose states are to be broadcast.
- `string ros:joint_state_broadcaster:frame_id`: The TF frame ID to be used in the published JointState messages.

## Tools

### Schema Definition
The normative OpenUSD schema definition for all `RosControl*API` schemas is provided in `schema/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.

