# REP XXXX -- OpenUSD Conventions for Simulation Asset Interoperability - Integrated Control Extension

## Abstract

This document defines conventions for simulating robotic systems in OpenUSD using integrated controller algorithms running inside the simulation environment.
This enables application-level testing, where the robotic system is simulated as a whole, including its physical properties, kinematics, and dynamics.
In this approach the controller is integrated in the simulator codebase and managed by parameters of the prim and ROS communication.

## Integrated Controller Simulation

`RosControlIntegratedAPI` allows instantiating robot controllers directly in the simulated scene.
It must reference one or more prims that have [RosTopicAPI](../../rep.md#24-topic-interface-rostopicapi), [RosServiceAPI](../../rep.md#25-service-interface-rosserviceapi) or [RosActionAPI](../../rep.md#26-action-interface-rosactionapi).
This schema is to be included as a built-in schema via `prepend apiSchemas` by a simulator-specific controller schema in the simulator.
For example, `simulatorXYZ::RosCustomTwistControllerAPI` would include `RosControlIntegratedAPI` as a built-in and reference prims:
- `RosTopicAPI` for subscription of control messages.
- `PhysicsRigidBodyAPI` for interaction with the physics engine.

USD does not enforce API schema constraints on referenced prims at the schema definition level. It is the responsibility of the simulator to validate that all prims referenced by a controller have at least one of the following API schemas applied: `RosTopicAPI`, `RosServiceAPI` or `RosActionAPI`.

### Built-in Controllers

The following schemas are built-in controller schemas that include `RosControlIntegratedAPI` as a built-in via `prepend apiSchemas`.
Simulators may implement these schemas to provide a standardized control interface for common use cases,
such as different robot locomotion paradigms (e.g. Ackermann steering) or application-specific interfaces (e.g. joint control for robot policies).
The following controllers are proposed as a minimal baseline for initial compliance.
The parameters and logic should follow established controllers in the ROS ecosystem and allow bootstrapping robot simulation with minimal custom development.
Simulators may implement additional controllers as needed, but these four are proposed as the baseline for application-level simulation compliance.
The implementation should support multi-robot simulation and control by leveraging namespaces.

## Controller Schemas

Individual controllers have their schema definitions in `<controller_name>/schema/schema.usda`. The sibling directories of this file each contain one such controller.

## Schema Definition

The OpenUSD schema definition for `RosControlIntegratedAPI` is provided in `schema/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.
