# REP XXXX -- OpenUSD Conventions for Simulation Asset Interoperability - External Controller Extension

## Abstract

This document defines conventions for the external control interface in OpenUSD-based robot simulation, where the control algorithm runs outside the simulator.
It enables test scenarios where the simulator provides a physics digital twin of the robot and exposes its low-level hardware interfaces (e.g. joint position, velocity, and effort command interfaces) to an external control entity.

## External Control Interfaces

The ROS 2 external control `RosControlExternalAPI` is a schema for exposing robot control interfaces to external control algorithms.
This schema is to be included as a built-in schema via `prepend apiSchemas` by a simulator-specific interface for a controller.
A simulator loading a prim with this schema should establish a connection, load a controller plugin, spawn a controller instance, or set up a hardware-in-the-loop connection to the robot controller,
and expose the control and state interfaces to the control entity.

## Tools

### Schema Definition
The normative OpenUSD schema definition for `RosControlExternalAPI` is provided in `schema/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.
