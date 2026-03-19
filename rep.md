# REP XXXX -- OpenUSD Conventions for Simulation Asset Interoperability

| Field | Value |
| :--- | :--- |
| **REP** | XXXX |
| **Title** | OpenUSD Conventions for Simulation Asset Interoperability |
| **Author** | Adam Dabrowski, Mateusz Zak (Robotec.ai) |
| **Status** | Draft |
| **Type** | Standards Track |
| **Content-Type** | text/markdown |
| **Created** | 2026-03-03 |
| **Requires** | REP 103, REP 105, OpenUSD Core Spec v1.0.1 |

## Abstract

This REP defines a standard schema and strict profile of OpenUSD (Universal Scene Description) for the interchange of robotics simulation assets. The scope includes robots, sensors, static environments (e.g., warehouse racks), and dynamic props. This REP aims to ensure that a single asset functions consistently across:

1.  **Simulation and physics engines** (Gazebo, Isaac Sim, Newton, Genesis, MuJoCo, O3DE).
2.  **Runtime integrations** (ROS 2 Interfaces).
3.  **Converters and web visualization** (especially glTF 2.0 conversion).

To achieve this, the specification is concerned with three areas:
*   **Section 1** ratifies existing upstream standards and recommendations (AOUSD, ASWF, NVIDIA) to establish a baseline for correct simulation assets.
*   **Section 2** defines novel, declarative API schemas for ROS 2 interfaces to ensure engine-agnostic runtime behavior.
*   **Section 3** defines a strict interoperability profile to support export pathways to other formats, ensuring compatibility with standards like glTF 2.0.

## Specification

The keywords "must", "must not", "required", "shall", "shall not", "should", "should not", "recommended", "may", and "optional" in this document are to be interpreted as described in RFC 2119.

---

## 1. Simulation Assets Baseline

This section confirms and standardizes prior work and recommendations for OpenUSD simulation assets. It draws from the Alliance for OpenUSD (AOUSD), the ASWF USD Working Group, and NVIDIA Asset Requirements. *Note: As AOUSD domain-specific working groups formalize physics and robotics specifications, recommendations in this section are subject to evolution and alignment.*

### 1.1 Coordinate Systems & Units
To ensure alignment with ROS standards (REP 103) and stability across solvers:

*   **Units:** All linear dimensions in the USD stage must be defined in meters, and all mass values in kilograms.
    *   `metersPerUnit` and `kilogramsPerUnit` metadata must be set to `1.0` in the root layer.
    *   Simulators importing these assets must apply this scaling factor to all derived physical quantities (torque, stiffness, inertia) at runtime.
*   **Up-Axis & Chirality:** The stage `upAxis` must be set to `"Z"` and follow the Right-Hand Rule.
*   **Root Transforms:** Assets must not rely on root-node rotations (e.g., `xformOp:rotateX = -90`) to align geometry. Points and normals should be transform-applied (frozen) to Z-up at the source level.
*   **Asset Pivots:** For assets intended to be placed on the ground (e.g., warehouse racks), the root origin should be located at the bottom-center of the asset bounding box (Z=0) to facilitate predictable drag-and-drop scene composition in simulators. Mobile bases should adhere to REP 105 origin conventions.

### 1.2 Asset Structure & Composition
This REP adopts the ASWF Guidelines for Structuring USD Assets.

#### 1.2.1 The Composition Model
*   **Components:** Atomic assets (e.g., a `LidarSensor`, a `Box`) must have `kind="component"` on their root prim.
*   **Assemblies:** Aggregates (e.g., a `Warehouse` containing racks) must have `kind="assembly"` or `kind="group"`.
*   A `component` must not contain another `component`, allowing converters to easily identify the "atomic units" of the scene.

#### 1.2.2 Composition Arcs (LIVERPS Constraints)
To guarantee that simulation assets remain self-contained, portable, and predictable across different simulator parsers, asset authors must adhere to the following constraints regarding OpenUSD's LIVERPS composition arcs:
*   **[L] Local:** Primary authoring of overrides and properties on the asset is fully supported.
*   **[I] Inherits & [S] Specializes:** Asset authors should not rely on `Inherits` or `Specializes` arcs for core robot kinematics, physics APIs, or ROS schemas when distributing standalone assets. These arcs create hard dependencies on external class hierarchies; if a simulator's environment lacks the base class definitions, the asset will fail to parse correctly.
*   **[V] VariantSets:** Permitted and encouraged for asset reusability (see Section 1.2.3).
*   **[R] References:** Permitted for logical assembly (e.g., composing a robot by referencing an independent `arm.usd` and `base.usd`).
*   **[P] Payloads (The Payload Pattern):** Heavy data (high-resolution meshes, point clouds, large textures) must be referenced via Payloads rather than standard References. 
    *   Payloads must not gate joint or link prims themselves. The kinematic topology (Prims bearing `PhysicsRigidBodyAPI`, `PhysicsJoint` schemas, and `Ros2*API` schemas) must reside in the primarily loaded scene graph (e.g., via Local authoring or standard References). 
    *   The Payload should solely encapsulate the nested geometric and material data. This enables ROS parsers and web converters to traverse the lightweight kinematic tree efficiently without loading heavy buffers.

#### 1.2.3 Variants and Reusability
OpenUSD `VariantSets` are the normative mechanism for asset reusability (e.g., encapsulating multiple furniture styles, different robot end-effectors, or optional sensor suites within a single asset).
*   **Default Variant Fallback:** Any asset utilizing `VariantSets` must author a default variant selection. This ensures that if the asset is loaded by a simulator or CI/CD pipeline without explicit variant overrides, it resolves to a valid, predictable physical and visual state.
*   **ROS Interface Resolution:** A change in a variant selection may add or remove Prims containing `Ros2*API` schemas (e.g., swapping a generic robot head for a sensor-equipped head). Simulators and tooling must only evaluate and spawn ROS interfaces that are active within the currently resolved variant state of the stage.

#### 1.2.4 Asset Management & FileFormat Plugins
*   **Path Resolution:** Internal references must use relative paths (`./geo/mesh.usdc`). External dependencies to other ROS packages must use the `package://` URI scheme. Absolute paths and proprietary schemes (e.g., `omniverse://`) are prohibited in distributed assets.
*   **Native Composition vs. Custom Prefabs:** The use of custom or vendor-specific string attributes (e.g., `custom string my_sim:prefabPath = "robot.usd"`) to dynamically load, instantiate, or compose assets at runtime is strictly prohibited for interoperable assets. Asset composition must rely purely on native OpenUSD references or payloads.
*   **FileFormat Plugins:** OpenUSD supports FileFormat plugins (e.g., MuJoCo's `usdMjcf` plugin) to dynamically translate legacy formats into USD stages at runtime. While these plugins are recommended for import pathways, this REP governs the *resulting in-memory OpenUSD data*. Plugins interfacing with the ROS 2 ecosystem must generate stages that conform to the physical hierarchies and API schemas defined in this document.

#### 1.2.5 ROS-Compatible Identifiers
OpenUSD allows flexible naming, but ROS 2 has strict lexical rules. Prim names intended to map to ROS TF Frames must be alphanumeric with underscores (`[a-zA-Z0-9_]`) and must not contain spaces (e.g., `Left_Arm`, not `Left Arm`).

### 1.3 Physics & Kinematics

*   **Rigid Body Hierarchy:** Assets should utilize Logical Nesting to represent kinematic chains (e.g., `Forearm` is a child of `UpperArm`). This preserves the Scene Graph for TF tree generation and MuJoCo compatibility.
    *   *Simulator Responsibility:* Simulators that require flat hierarchies are responsible for flattening the graph at import time. The asset itself must remain logically nested.
*   **Joint Placement:** While `UsdPhysicsJoint` prims rely on relational targeting (`body0` and `body1`) rather than hierarchy, asset authors should place the Joint prim as a sibling adjacent to the child link it connects, within the scope of the parent link. This ensures self-contained modularity.
*   **Articulation Roots:** A composed simulation stage must contain at most one `PhysicsArticulationRootAPI` per connected kinematic tree. 
    *   Assets (e.g., a modular gripper) should be self-contained with an articulation root for standalone use. 
    *   When composed into a larger kinematic tree, the composing stage should use the `delete apiSchemas` operation to prune nested articulation roots. This prevents reduced-coordinate physics solvers from fracturing the robot.
*   **Loop Closures:** Articulations must form a spanning tree. Joints introducing loop-closing constraints (e.g., parallel linkages) must use the newly introduced `RoboticsLoopClosureAPI` marker schema.
*   **Mass Properties:** Dynamic bodies must have a strictly positive mass (`mass > 0`). Anchors (e.g., the base of a robot arm bolted to the floor) must have a `PhysicsRigidBodyAPI` but may define `mass = 0` (which implies infinite mass/static in many solvers). 
    *   *Note:* Non-physical dummy frames (e.g., `camera_optical_frame`) must not possess a `PhysicsRigidBodyAPI`. They should be tracked using the `Ros2FrameAPI` as defined in Section 2.7.

#### 1.3.1 Collisions & The Dual-Fidelity Pattern
Collision geometries must explicitly specify `purpose="guide"` and `physics:approximation="none"`. To ensure assets function across both standard physics engines and advanced contact-rich solvers (e.g., Newton), assets should employ a "Dual-Fidelity Pattern" utilizing a `collision_fidelity` OpenUSD `VariantSet`:
1.  **Baseline Approximation (Default Variant):** The default variant must contain "convexHull" or primitive shapes.
2.  **Advanced Approximation (Optional Variant):** A secondary variant may contain high-fidelity concave trimeshes intended for Signed Distance Field (SDF) or Hydroelastic collision generation, provided the target simulator supports these paradigms.

---

## 2. ROS 2 Integration Schemas

Neither OpenUSD nor glTF 2.0 currently standardize the specification of ROS interfaces. This section defines a set of declarative, engine-agnostic API schemas. Simulators are responsible for reading these schemas and generating their respective underlying execution logic.

A Prim acts as a single logical interface. If a sensor needs multiple interfaces (e.g., `image_raw` and `camera_info`), a child prim for each interface should be utilized.

### 2.1 Schema Isolation and Functional Layering (The ETL Pipeline)

To avoid "Unknown Schema" errors in standard 3D authoring tools (e.g., Blender, Maya) and to ensure assets remain modular, functional layering (Extract-Transform-Load) should be utilized for ROS 2 interfaces, physics, and simulator-specific tooling syntax. 

This REP endorses the ETL composition architecture developed collaboratively by NVIDIA, Intrinsic, and Disney Research for OpenUSD robotics assets.

![Extract-Transform-Load Pipeline for Robots in USD](etl_pipeline_diagram.png)
*Figure 1: The Extract-Transform-Load (ETL) composition pipeline for OpenUSD robotics assets. Source: [NVIDIA Developer Blog](https://developer.nvidia.com/blog/using-openusd-for-modular-and-scalable-robotic-simulation-and-development/)*

As illustrated in Figure 1, assets should be divided into functional layers composed via References and Payloads:

*   **Asset Source & Transformation (The Base Layer):** The raw CAD data (`asset_base.usd`) is optimized into simulation-ready geometry (`asset_sim_optimized.usd`). This layer contains native OpenUSD schemas (`UsdGeom`, `UsdShade`).
*   **Features (The Domain-Specific Layers):** Domain metadata is isolated into specific overlay files that reference the Base Layer. For example, `asset_physics.usd` contains the rigid bodies and joints, while `asset_ros.usd` contains the `Ros2*API` schemas defined in this REP.
*   **Entry Point (`asset.usd`):** The final distributed asset is a lightweight interface layer that uses **Payloads** to load the Features. 
*   **Proprietary Layer:** Asset authors should avoid including heavy, simulator-specific implementations (e.g., proprietary execution graphs) within the interoperable asset package. If unavoidable, they must minimize this proprietary layer (e.g., `asset_isaac.usd`) to what is strictly necessary and keep it isolated as a separate Feature layer.

### 2.2 The ROS 2 Context (`Ros2ContextAPI`)
The root prim of a ROS-interfaced simulation asset may define its context namespace.
*   `string ros2:context:namespace`: Prefixes all topics within this scope (e.g., `/robot_1`). The namespace is additive in the asset hierarchy and with a top-level namespace set during simulation deployment (e.g., via the `SpawnEntity` service).
*   `int ros2:context:domain_id` (Optional): Overrides the default ROS Domain ID for interfaces descending from this context.
*   `string ros2:context:parent_frame` (Optional, Default: `"world"`): Defines the parent `frame_id` used when the simulator broadcasts the ground-truth transform of this context's root prim. It is only valid for the top-most context in the resolved USD Stage and ignored otherwise.

### 2.3 Interface Type Resolution & Naming
For all schema types (Topics, Services, Actions) defined below:
*   **Type Resolution:** Tooling and compliant simulators must attempt to resolve the `ros2:*:type` string (e.g., `sensor_msgs/msg/Image`) dynamically against the sourced ROS 2 environment. If the interface type is not found, the simulator must safely disable that specific interface, allow the rest of the asset to function normally, and emit a distinct warning/error.
*   **Name Validation:** All `ros2:*:name` values must strictly adhere to ROS 2 topic naming rules (alphanumeric, underscores, and forward slashes only; cannot start with a number).

### 2.4 Topic Interface (`Ros2TopicAPI`)
Applies to Prims that exchange streaming ROS data.

**Core Attributes (Required):**
*   `token ros2:topic:role`: Values: `["publisher", "subscription"]`.
*   `string ros2:topic:name`: The topic name relative to the active namespace.
*   `string ros2:topic:type`: The ROS message type.
*   `double ros2:topic:publish_rate`: Target publication frequency in Hz. Required for publishers; ignored for subscriptions.

**Quality of Service (QoS) Attributes:**
Maps directly to `rmw_qos_profile_t` policies. If an attribute is omitted, simulators must assume the specified defaults. *(Note: As per REP 2003, simulated sensors should default to `"system_default"` which maps to best-effort, while map publishers should use `"transient_local"`).*
*   `bool ros2:topic:qos:match_publisher` (Optional, Default: `false`). For subscriptions only. If `true`, the simulator bridge must attempt to use ROS 2 QoS matching to adapt to the discovered publisher, ignoring explicit reliability/durability settings.
*   `token ros2:topic:qos:reliability`: Values: `["system_default", "reliable", "best_effort"]`. (Default: `"system_default"`).
*   `token ros2:topic:qos:durability`: Values: `["system_default", "transient_local", "volatile"]`. (Default: `"system_default"`).
*   `token ros2:topic:qos:history`: Values: `["system_default", "keep_last", "keep_all"]`. (Default: `"system_default"`).
*   `int ros2:topic:qos:depth`: Queue size. Evaluated only when history is `keep_last`. (Default: `10`).

### 2.5 Service Interface (`Ros2ServiceAPI`)
Applies to Prims handling synchronous requests (e.g., resetting an environment).
*   `token ros2:service:role`: Values: `["server", "client"]`. (Simulation assets are typically `server`).
*   `string ros2:service:name`: The service name.
*   `string ros2:service:type`: The service type (e.g., `std_srvs/srv/SetBool`).

### 2.6 Action Interface (`Ros2ActionAPI`)
Applies to Prims handling asynchronous, long-running behaviors.
*   `token ros2:action:role`: Values: `["server", "client"]`. (Simulation assets are typically `server`).
*   `string ros2:action:name`: The action name.
*   `string ros2:action:type`: The action type (e.g., `control_msgs/action/FollowJointTrajectory`).

### 2.7 Frame Publishing and TF2 (`Ros2FrameAPI`)
Mapping a deeply nested OpenUSD scene graph directly to a ROS 2 TF tree can cause significant performance overhead. To prevent flooding the `/tf` topic with generic physical props (e.g., warehouse boxes), compliant simulators should not broadcast transforms for every `PhysicsRigidBodyAPI`. 

Instead, simulators should follow a hybrid implicit/explicit approach for broadcasting `tf2` transforms:

*   **Implicit TF Broadcasting (The Asset Tree):** Simulators should automatically infer and broadcast TF frames (using the ROS-validated Prim name) for Prims that represent a ROS interface structure:
    1.  **The ROS Root:** Any Prim possessing the `Ros2ContextAPI` (often the `base_link`).
    2.  **Kinematic Chains:** Any Prim possessing a `PhysicsRigidBodyAPI` that is connected (directly or recursively) via a `UsdPhysicsJoint` to a Prim already in the TF tree. This captures robot arms and wheeled bases automatically.
    3.  **Interface Frames:** Any Prim possessing a `Ros2TopicAPI`, `Ros2ServiceAPI`, or `Ros2ActionAPI`.
    *   *Routing Rule:* If the implicit frame is connected to its parent via a `PhysicsFixedJoint`, or has no joint but is rigidly parented in the USD hierarchy, the simulator must broadcast it to `/tf_static`. All movable joint connections must be broadcast to `/tf`.

*   **Explicit TF Broadcasting (`Ros2FrameAPI`):** To publish TFs for non-physical dummy frames (e.g., a kinematic `grasp_point`, a `camera_optical_frame`), asset authors must apply the `Ros2FrameAPI` schema to the target `UsdGeomXform` Prim.
    *   `string ros2:frame:id` (Optional): Overrides the TF frame name. If omitted, the validated Prim name is used.
    *   `bool ros2:frame:static` (Optional, Default: `true`): Defines the broadcast destination. If `true`, the simulator must broadcast the frame to `/tf_static` relative to its USD parent. If `false` (e.g., an Xform animated by USD TimeSamples), it must be broadcast to `/tf`.

### 2.8 Kinematic Loop Closures (`RoboticsLoopClosureAPI`)
OpenUSD `UsdPhysics` currently lacks a vendor-neutral (e.g., not `PhysxSchema` or `MjcPhysics`) mechanism to identify joints that close a kinematic loop. Because many robotics simulators use reduced-coordinate (e.g., Featherstone) solvers that require strict spanning trees, parsers must know which joint to exclude from the primary tree.
*   **Schema Application:** Asset authors must apply the `RoboticsLoopClosureAPI` to any `UsdPhysicsJoint` that closes a kinematic loop.
*   **Parser Responsibility:** Parsers traversing the `body0`/`body1` relationships to build the kinematic tree must prune their traversal when encountering this schema, handling the joint as a standalone constraint rather than a parent-child hierarchical link.

---

## 3. Interoperability and Distribution Profile

OpenUSD is a vast standard supporting complex features. To guarantee that assets can be distributed, viewed in desktop tools (e.g., `usdview`) or lightweight web tools (e.g., Foxglove, Webviz, Rerun), and successfully converted to glTF 2.0, assets must adhere to this constrained subset.

### 3.1 Material Portability
*   Assets must use `UsdPreviewSurface` or OpenPBR [AOUSD-OPENPBR] as the normative surface definition.
*   Proprietary shaders (MDL, OSL) must not be the primary binding, as they cannot be exported to web viewers or non-native raytracers.
*   UDIM (splitting textures across multiple files) must not be used.

### 3.2 Texture Baking
Procedural texture graphs (noise generation, math nodes, node graphs) are not interoperable and must be baked down into explicit data using either:
1.  **UV-mapped image files** (standard textures).
2.  **Mesh primitive variables (Primvars)** such as baked vertex colors using standard USD interpolations. `"vertex"` interpolation is recommended, as `"uniform"` and `"faceVarying"` require converters to split the mesh vertices to comply with glTF’s vertex attribute requirements.

### 3.3 Instanceable Leaves (Zero-Copy)
Repetitive geometry (bolts, LED arrays on a sensor) should be marked `instanceable=true` and referenced from a shared payload. 
*   *Benefit:* This maps directly to glTF GPU instancing [GLTF-EXT-INSTANCING], which is crucial for preventing out-of-memory errors when rendering complex sensor racks in browser-based tools.

### 3.4 Lighting
Lighting assemblies must use standard `UsdLux` schemas. Emissive meshes (geometry acting as light sources) should be avoided for primary illumination due to poor scaling in real-time engines.

### 3.5 Variant Baking for Export
While USD natively handles structural variants, many of the simulation tools in the ecosystem don't. Converters targeting formats like glTF 2.0 should "bake" the active structural and physical variant into static geometry during export. Material variants should be preserved and mapped to the `KHR_materials_variants` glTF extension.

### 3.6 Conversion and Round-Tripping
OpenUSD supports a superset of features compared to standard robotics formats (URDF, SDF) and web formats (glTF). Consequently, conversions between OpenUSD and these formats are generally **destructive (lossy)**. Importers and exporters should prioritize preserving kinematics, physics constraints, and ROS API schemas, while accepting the loss of USD-native composition features (like layers) during conversion.

---

## Tools & Reference Implementations
A REP 2040 compliance checker is to be developed and shared with the community. The tool will provide validation of all REP recommendations for OpenUSD assets and supply actionable feedback for the user for each divergence.

## References
*   **[NVIDIA-ETL-PIPELINE]** NVIDIA, Intrinsic, Disney Research. "Using OpenUSD for Modular and Scalable Robotic Simulation and Development". URL: `https://developer.nvidia.com/blog/using-openusd-for-modular-and-scalable-robotic-simulation-and-development/`
*   **[NVIDIA-ASSETS]** NVIDIA, "Content Guidelines and Requirements". URL: `https://docs.omniverse.nvidia.com/kit/docs/asset-requirements/latest/index.html`
*   **[ASWF-USD-ASSETS]** Academy Software Foundation USD Working Group, "Guidelines for Structuring USD Assets". (Targeting Commit: `main` as of March 2026).
*   **[AOUSD-OPENPBR]** Alliance for OpenUSD, "OpenPBR Surface Specification".
*   **[REP-2003]** ROS Enhancement Proposal 2003, "Sensor Data and Map QoS Settings".
*   **[GLTF-2.0]** Khronos Group, "glTF 2.0 Specification".
*   **[GLTF-EXT-INSTANCING]** Khronos Group, "EXT_mesh_gpu_instancing Extension Specification".
*   **[GLTF-KHR-RIGID]** Khronos Group, "KHR_rigid_bodies Extension Specification" (Draft).

## Copyright
This document has been placed in the public domain.

