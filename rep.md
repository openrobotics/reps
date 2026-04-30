---
layout: post
REP: 0158:2026
title: OpenUSD Conventions for Simulation Asset Interoperability
authors: Adam Dabrowski, Mateusz Zak, Michal Pelka (Robotec.ai), Ayush Ghosh, Renato Gasoto (NVIDIA), Franco Cipollone (Ekumen)
PMC Sponsor: Michael Carroll <mjcarroll@intrinsic.ai>
PMCs: ROS
discussion: Pending
tag: Draft
category: Standard
date: 2026-03-03
requires: REP 103, REP 105
pin: true
---

## Abstract

This REP defines a standard schema and strict profile of OpenUSD (Universal Scene Description) for the interchange of robotics simulation assets. The scope includes robots, sensors, static environments (e.g., warehouse racks), and dynamic props. This REP aims to ensure that a single asset functions consistently across:

1.  **Simulation and physics engines** (Gazebo, Isaac Sim, Newton, Genesis, MuJoCo, O3DE).
2.  **Runtime integrations** (ROS Interfaces).
3.  **Converters and web visualization** (especially glTF 2.0 conversion).

To achieve this, the specification addresses four key areas:
*   **Section 1** adopts existing upstream standards and recommendations (AOUSD, ASWF, NVIDIA) to establish a baseline for correct simulation assets.
*   **Section 2** defines novel, declarative API schemas for ROS interfaces to ensure engine-agnostic runtime behavior.
*   **Section 3** defines a strict interoperability profile to support export pathways to other formats, ensuring compatibility with standards like glTF 2.0.
*   **Section 4** establishes the interoperability ecosystem registries for extending sensor and control schemas.

Following the OpenUSD and glTF 2.0 model, this REP establishes a Core Standard, and proposes general rules for handling of extension schemas, including for control interfaces and sensor simulation.

## Motivation

The ROS ecosystem chiefly relies on URDF and SDF for describing robots and environments. These formats are almost entirely confined to the ROS and Gazebo ecosystems. OpenUSD has emerged as an industry standard supported by a multitude of tools and allows artists to collaborate with simulation engineers without problematic conversions between a variety of 3D and XML formats. Ensuring OpenUSD works well with ROS integrations across robotics simulators will increase ecosystem interoperability and strengthen ROS's position in physical AI workflows such as synthetic data and generative pipelines. OpenUSD is a powerful format with an extensible architecture allowing it to capture all the semantics of other popular formats.

While OpenUSD adoption is growing quickly, only the core standard specification has been ratified so far, leaving many key features for robotics uncovered. OpenUSD lacks standardized semantic representations for ROS interfaces and standard rules for mapping to ROS concepts such as frames and TF trees. OpenUSD's flexibility also permits practices that degrade interoperability, such as proprietary extensions, defining execution instead of intent, and overfitting to particular workflows.

OpenUSD is championed by the Alliance for OpenUSD (AOUSD) and the ASWF USD Working Group. NVIDIA also plays a key role both as a founding member of AOUSD and in developing OpenUSD for robotics through Omniverse, Isaac Sim and Newton. This REP builds on top of significant work done by all these entities, extending it by addressing what is not yet standardized but urgently needed for OpenUSD interoperability in the ROS simulation ecosystem, and standardizing against practices that result in a vendor lock-in. As such, this REP is designed to adapt upstream standards for the ROS community, while serving as a reference to influence future decisions by AOUSD and ASWF.

The motivation is not to replace any of existing formats, but to regulate a widely adopted, powerful standard so that it serves the ROS community, strengthening ROS role in the development of Physical AI.

## Specification

The keywords "must", "must not", "required", "shall", "shall not", "should", "should not", "recommended", "may", and "optional" in this document are to be interpreted as described in RFC 2119.

---

## 1. Simulation Assets Baseline

This section confirms and standardizes prior work and recommendations for OpenUSD simulation assets. It draws from the Alliance for OpenUSD (AOUSD), the ASWF USD Working Group, and NVIDIA Asset Requirements. 

*Note: As AOUSD domain-specific working groups formalize physics and robotics specifications, recommendations in this section are subject to evolution and alignment.*

### 1.1 Coordinate Systems & Units
To ensure alignment with ROS standards (REP 103) and stability across solvers:

*   **Standard Units (MKS):** Assets must use MKS (Meters, Kilograms, Seconds). Root layer metadata `metersPerUnit` and `kilogramsPerUnit` must be explicitly set to `1.0`. `timeCodesPerSecond` must also be set to `1.0` so that one USD time code equals one second, ensuring time-sampled data (e.g., animated joint trajectories) plays back at the correct rate without additional scaling. All upstream units (e.g., CAD millimeters) must be baked into geometry and physics during the Extract-Transform-Load (ETL) pipeline. Simulators are entitled to assume `1.0` scaling.
*   **Up-Axis & Chirality:** The stage `upAxis` must be `"Z"`. Assets must follow the strict ROS Right-Handed convention: X-forward, Y-left, Z-up.
*   **Transform Operations:** To guarantee a parity with ROS `geometry_msgs/Transform`, kinematic prims must use a minimal `xformOpOrder` stack: exactly one `xformOp:translate` and one `xformOp:orient` (quaternion). Baked 4x4 matrices (`xformOp:transform`) are prohibited on final assets, as they obscure scale and force costly runtime decomposition. While Euler angles (`xformOp:rotateXYZ`) are acceptable in source assets for human readability and URDF rpy alignment, ETL pipelines must convert all Euler rotations (translating URDF radians to USD degrees) and decompose all CAD matrices into this translate/orient format.
*   **Scale Operations:** Kinematic prims (rigid bodies and joints) must maintain identity scale or omit `xformOp:scale` entirely. Scaling must be applied exclusively to the leaf visual or collision geometry prims.
*   **Root Transforms:** Assets must not rely on root-node rotations (e.g., `xformOp:rotateX = -90`) to align geometry. Points and normals should be transform-applied (frozen) to Z-up at the source level.
*   **Asset Pivots:** For assets intended to be placed on the ground (e.g., warehouse racks), the root origin should be located at the bottom-center of the bounding box (Z=0) to facilitate predictable drag-and-drop scene composition in simulators. Mobile bases should adhere to REP 105 origin conventions.

### 1.2 Asset Structure & Composition
This REP adopts the ASWF Guidelines for Structuring USD Assets.

#### 1.2.1 Schema Isolation and Functional Layering (The ETL Pipeline)


![Extract-Transform-Load Pipeline for Robots in USD](etl_pipeline_diagram.png)
*Figure 1: The Extract-Transform-Load (ETL) composition pipeline for OpenUSD robotics assets. Source: [NVIDIA Developer Blog](https://developer.nvidia.com/blog/using-openusd-for-modular-and-scalable-robotic-simulation-and-development/)*

As illustrated in Figure 1, assets should be divided into functional layers composed via References and Payloads:

*   **Layer Separation:** Assets must use functional layering (ETL) to isolate core OpenUSD data from simulation and ROS-specific schemas. This prevents "Unknown Schema" errors in standard tools and enables modular updates.
*   **Layer Encoding:** Schema- and relationship-bearing layers must be authored as ASCII (`.usda`); heavy-data layers as binary Crate (`.usdc`).
*   **The Base Layer:** The core data must be decomposed into granular, functional files to maximize deduplication and performance:
    *   `geometries.usdc`: Contains pure mesh topology and vertices (no physics, no schemas).
    *   `materials.usda`: Contains material and look-dev definitions.
    *   `instances.usda`: (Optional, recommended): Assembles geometries and materials via references.
    *   `base.usda`: The pure kinematic hierarchy (Xforms), referencing the underlying instances and geometries without physical or execution logic.
*   **Features (The Domain-Specific Layers):** Domain metadata must be isolated into overlay files, including:
    *    `physics.usda`: Contains `UsdPhysics` rigid bodies and joints.
    *    `ros.usda`: Contains the `Ros*API` schemas.
*   **Entry Point (`[asset_name].usda`):** The final distributed asset must be a lightweight interface layer that uses **Payloads** to load the Features.
*   **Proprietary Layer:** Simulator-specific implementations (e.g., proprietary execution graphs) must be limited to what is strictly necessary and confined to a separate proprietary layer (e.g., `isaac.usda`, `o3de.usda`).


#### 1.2.2 The Composition Model
Assets must adhere to the OpenUSD Model Hierarchy to ensure predictable selection and traversal:
*   **Components:** Individual distributable assets (e.g., a sensor, a box) must have `kind="component"` on their root prim.
*   **Assemblies:** Aggregates (e.g., a `Warehouse` containing racks) must have `kind="assembly"` or `kind="group"`.
*   **Granularity:** Authors should use kind="subcomponent" for organizational prims within a component.

#### 1.2.3 Composition Arcs (LIVRPS Constraints)
To guarantee that simulation assets remain self-contained, portable, and predictable across different simulator parsers, asset authors must adhere to the following constraints regarding OpenUSD's LIVRPS composition arcs:
*   **[L] Local:** Primary authoring of overrides and properties on the asset is fully supported.
*   **[I] Inherits & [S] Specializes:** Asset authors should not rely on `Inherits` or `Specializes` arcs that target class definitions outside the asset's own layer stack for core robot kinematics, physics APIs, or ROS schemas when distributing standalone assets. The inherits-instanceable pattern, where the class prim is defined within the same asset, remains valid and is recommended for applying uniform overrides across instances.
*   **[V] VariantSets:** Permitted and encouraged for asset reusability (see Section 1.2.4).
*   **[R] References:** Permitted for logical assembly (e.g., composing a robot by referencing an independent `arm.usda` and `base.usda`).
*   **[P] Payloads (The Payload Pattern):** Heavy data (high-resolution meshes, point clouds, large textures) must be referenced via Payloads rather than standard References. 
    *   Payloads must not encapsulate joint or link prims themselves. The kinematic topology (Prims bearing `PhysicsRigidBodyAPI`, `PhysicsJoint` schemas, and `Ros*API` schemas) must reside in the primarily loaded scene graph (e.g., via Local authoring or standard References). 
    *   The Payload should solely encapsulate the nested geometric and material data. This enables ROS parsers and web converters to traverse the lightweight kinematic tree efficiently without loading heavy buffers.

#### 1.2.4 Variants
OpenUSD `VariantSets` are the normative mechanism for asset reusability (e.g., encapsulating multiple furniture styles, different robot end-effectors, or optional sensor suites within a single asset).
*   **Default Variant Fallback:** Any asset utilizing `VariantSets` must author a default variant selection. This ensures that if the asset is loaded by a simulator or automated pipeline without explicit variant overrides, it resolves to a valid, physically and visually complete state.
*   **ROS Interface Resolution:** A change in a variant selection may add or remove Prims containing `Ros*API` schemas (e.g., swapping a generic robot head for a sensor-equipped head). Simulators and tooling must only evaluate and instantiate ROS interfaces that are active within the currently resolved variant state of the stage.

#### 1.2.5 Asset Management
*   **Default Prim:** All distributable assets must set `defaultPrim` metadata on the root layer, pointing to the asset's primary entrypoint prim. Without it, referencing `@robot.usda@` without an explicit prim path is undefined behavior and the Payload pattern breaks silently.
*   **Asset Identification (`assetInfo`):** All distributable assets must populate the `assetInfo` dictionary on the `defaultPrim` with at minimum:
    *   `string assetInfo:identifier`: A unique, stable identifier for the asset (e.g., a URI or canonical name).
    *   `string assetInfo:version`: A version string (e.g., `"1.0.0"`).
    *   To carry robotics-specific provenance (e.g., URDF package origin, original SDFormat model URI, or component catalog IDs), authors should use a namespaced sub-dictionary: assetInfo["ros"].
        *Example: `assetInfo["ros"]["package_uri"] = "package://my_robot/urdf/robot.urdf"`.*
    *   *Note: This REP aligns with the domain convention requested in the active AOUSD proposal: [Separation of Concerns for Identifiers in USD (PR #105)](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105) Once AOUSD ratifies a standardized mechanism for external identifiers, this REP will adopt it.*
*   **Path Resolution:** Internal references must use relative paths (`./geo/mesh.usdc`). For distributed, highly interoperable assets, all file dependencies should be self-contained and rely exclusively on relative paths.
*   **ROS packages:** External dependencies targeting other ROS packages must use the package:// URI scheme. Absolute paths or proprietary schemes (e.g., omniverse://) are prohibited for external package references. Tooling and simulators aiming for ROS interoperability must provide a custom OpenUSD ArResolver plugin to resolve these URIs.
*   **Native Composition vs. Custom Prefabs:** Assets must not use custom or vendor-specific string attributes (e.g., `custom string my_sim:prefabPath = "robot.usd"`) to dynamically load, instantiate, or compose assets at runtime. Asset composition must rely purely on native OpenUSD references or payloads.
*   **FileFormat Plugins:** OpenUSD supports FileFormat plugins (e.g.,`usdMjcf`) to dynamically translate legacy formats into USD stages at runtime. While these plugins are recommended for import pathways, this REP governs the *resulting in-memory OpenUSD data*. Plugins interfacing with the ROS ecosystem must generate stages that conform to the physical hierarchies and API schemas defined in this document.

#### 1.2.6 Parallel Simulation and Instancing
OpenUSD's native instancing mechanisms are designed for repetitive visual and structural geometry. They must not be used to clone articulated physics assets to create massive parallel arrays (e.g., for reinforcement learning).
*    **Canonical Assets:** Authors must distribute a single, self-contained canonical environment.
*    **Runtime Delegation:** Simulators supporting massive parallelism are expected to handle environment replication natively at runtime via their own APIs. Authors must not bake arrays of physics-enabled clones into the source file.

### 1.3 Physics
*   **Joint Placement:** Asset authors should place the joint prim as a sibling adjacent to the child link it connects, within the scope of the parent link, to ensure self-contained modularity. Note that `UsdPhysicsJoint` prims rely on relational targeting (`body0` and `body1`) rather than hierarchy, which means parsers must reconstruct the kinematic tree exclusively from these relationships.
*   **Joint Limits:** Non-continuous joints (e.g., revolute, prismatic) must author explicit `physics:lowerLimit` and `physics:upperLimit` attributes.
*   **Articulation Roots:** A composed simulation stage must contain at most one `UsdPhysicsArticulationRootAPI` per connected kinematic tree. 
    *   Assets (e.g., a modular gripper) should be self-contained with an articulation root for standalone use. 
    *   When composed into a larger kinematic tree, the composing stage should use the OpenUSD list-edit operation `delete apiSchemas = ["PhysicsArticulationRootAPI"]` to prune nested articulation roots. This prevents reduced-coordinate physics solvers from fracturing the robot.
*   **Loop Closures:** Articulations must form a spanning tree. Joints that close a kinematic loop (e.g., parallel linkages, four-bar mechanisms) must set `physics:excludeFromArticulation = true`. Parsers building the kinematic tree must treat these joints as standalone maximal-coordinate constraints rather than parent-child links.
*   **Mass Properties:** Assets and simulators must follow `UsdPhysicsMassAPI` guidelines. Dynamic bodies must define a strictly positive mass (mass > 0). Setting mass = 0 to imply infinite/static mass violates the UsdPhysics specification, which ignores 0.0 and falls back to a computed default mass. Instead, authors must use standard mechanisms for non-dynamic bodies:
    * *Static Environments:* Fixed props (e.g., walls, racks) must possess a PhysicsCollisionAPI but omit the PhysicsRigidBodyAPI. OpenUSD implicitly treats these as having zero velocity and infinite mass.
    * *Robot Anchors:* A fixed robot base must have a valid mass > 0 and be anchored via a UsdPhysicsFixedJoint with an empty physics:body0 relationship (which natively represents the world).
    * *Kinematic Bodies:* Moving bodies that are animated but not dynamically driven by physics should set the physics:kinematicEnabled attribute to true.
    * *Dummy Frames:* Non-physical dummy frames (e.g., `camera_optical_frame`) must not possess a `PhysicsRigidBodyAPI`. They should be tracked using the `RosFrameAPI` as defined in Section 2.7.
*   **Inertia Representation:** Unlike URDF and SDFormat's 6-value symmetric matrix, OpenUSD requires an eigendecomposed inertia tensor. Converters must mathematically decompose the source matrix into physics:diagonalInertia (eigenvalues) and physics:principalAxes (quaternion). This native decomposed form is the strict single source of truth; custom 6-value array attributes must not be authored or parsed.
*   **Extended Physics:** Many physics features are missing in `UsdPhysics`, including mimic joints, deformable bodies and advanced friction. Authors must use `ExtendedPhysics*` schemas for interoperability, following Section 4.2.2. When interoperable schema is not available, assets must isolate the specific feature, e.g. deformable soft-body physics into a feature layer for specific domain or vendor (see Section 1.2.1). 


#### 1.3.1 Collisions
Collision geometries should explicitly specify `purpose="guide"` and `physics:approximation="none"`. To ensure assets function across both standard physics engines and advanced contact-rich solvers (e.g., Newton), assets should employ a "Dual-Fidelity Pattern" utilizing a `collision_fidelity` OpenUSD `VariantSet`:
1.  **Baseline Approximation (Default Variant):** The default variant must contain "convexHull" or primitive shapes.
2.  **Advanced Approximation (Optional Variant):** A secondary variant may contain high-fidelity concave trimeshes intended for Signed Distance Field (SDF) or Hydroelastic collision generation, provided the target simulator supports these paradigms.

#### 1.3.2 Visual Representation
Each link's visual and collision scopes should be organized as sibling children (e.g., `/{link}/visual`, `/{link}/collision`).

To ensure assets function across high-end renderers (Isaac Sim, O3DE), CPU-bound physics simulators (Gazebo, MuJoCo), and lightweight tooling, assets should provide multiple visual representations via a `visual_representation` VariantSet on the visual scope. This VariantSet covers both mesh fidelity tiers and alternative representation modalities.
1.  **`mesh_medium` (Default Variant):** Decimated mesh geometry for real-time engines and standard simulation workloads.
2.  **`mesh_high` (Optional Variant):** Full-fidelity source mesh geometry (e.g. CAD). Suitable for ray-traced rendering and high-end visualization.
3.  **`mesh_low` (Optional Variant):** Simplified mesh for lightweight tools, large-scale batch simulation, and GPU-instanced scenes (e.g., Genesis).
4.  **`volumetric_splat` (Optional Variant):** 3D Gaussian Splat radiance field authored using the `UsdVolParticleField3DGaussianSplat` schema (OpenUSD 26.03).

Collision meshes are not subject to this VariantSet; their fidelity is governed by the `collision_fidelity` VariantSet (Section 1.3.1).

#### 1.3.3 Self-Collision Filtering
`UsdPhysicsJoint` disables collisions between its connected links by default (`physics:collisionEnabled = false`). Assets should use `UsdPhysicsCollisionGroup` to define collision group filtering and may use `UsdPhysicsFilteredPairsAPI` for fine-grained exceptions.

#### 1.3.4 Contact Physics
To ensure deterministic contact dynamics across engines, authors must bind a `UsdShadeMaterial` bearing the `UsdPhysicsMaterialAPI` to collision geometries. This material must define `physics:staticFriction`, `physics:dynamicFriction`, and `physics:restitution`. To prevent conflicts with visual shading networks, the physical material must be bound to the collision geometry explicitly using the physics material purpose (`material:binding:physics`), rather than the default all-purpose binding. Because engines utilize distinct friction models, converters must approximate these baseline values into their specific representations (e.g., SDF `<surface>` or MJCF `<friction>`).

### 1.4 Isolation of vendor and physics specific extensions

To guarantee interoperability across different solvers, physical properties and engine-specific parameters must be explicitly decoupled into separate functional layers:

*   **Neutral Physics (`physics.usda`):** A universally shared layer containing exclusively core `UsdPhysics` schemas (rigid bodies, joints, limits, mass properties). This file must adhere to the standard OpenUSD Physics specification and must not contain any vendor-specific extensions.
*   **Engine Tuning (`physx.usda`, `mujoco.usda`, `isaac.usda`):** Engine-specific parameters (e.g., proprietary solver iterations, specialized friction models, GPU tensors) not covered by core OpenUSD schemas must be explicitly namespaced with a vendor prefix (e.g., `mujoco:`, `isaac:`). These must be isolated within discrete "Proprietary Layers" (Section 1.2.1) and never authored in the baseline simulation payload or neutral physics layer. Authors must strive to minimize this proprietary layer to what is strictly necessary.

---

## 2. ROS Integration Schemas

Neither OpenUSD nor glTF 2.0 currently standardize the specification of ROS interfaces. This section defines a set of declarative, engine-agnostic API schemas (of type `SingleApply`). Simulators are responsible for reading these schemas and generating their respective underlying execution logic. Assets must not duplicate the same ROS interface in another form (e.g., a hand-authored execution graph publishing the same topic alongside the authored `Ros*API` schema); persisted runtime artifacts belong in the simulator's proprietary layer (Section 1.2.1), not in the neutral ROS layer.

### 2.1 The ROS Context (`RosContextAPI`)
The root prim of a ROS-interfaced simulation asset may define its context namespace.
*   `string ros:context:namespace`: Prefixes all topics within this scope (e.g., `robot_1`). Multiple values across the hierarchy are concatenated in top-down order. See Section 2.1.1 for full rules.
*   `int ros:context:domain_id` (Optional): Overrides the default ROS Domain ID for interfaces descending from this context.
*   `string ros:context:parent_frame` (Optional, Default: `"world"`): Defines the parent `frame_id` used when the simulator broadcasts the ground-truth transform of this context's root prim. It is only valid for the top-most context in the resolved USD Stage and ignored otherwise.

#### 2.1.1 Hierarchical Namespace Concatenation

The effective namespace is the top-down concatenation of `ros:context:namespace` attributes along the ancestor chain, automatically joined by `/` (e.g., `"robot_1"` and `"left_camera"` produce `/robot_1/left_camera`). An absent or empty attribute contributes no segment. Segments follow two authoring modes:
*   **Composable (default):** A bare name with no leading or trailing `/` and no runtime substitutions (`~`, `{}`).
*   **Absolute:** A leading `/` resets the chain, ignoring all ancestor values.

`ros:context:domain_id` is resolved from the nearest ancestor `RosContextAPI` prim; the simulator's default applies if none is set. `ros:context:parent_frame` is only valid on the outermost `RosContextAPI` in the stage and must be ignored on nested contexts.

TF frames for all joints and links within one robot must be published on a single `/tf` and `/tf_static` topic, scoped using only the outermost `RosContextAPI` namespace. Sub-namespace segments must not be appended to the TF topic name.

Each robot instance must carry a unique `ros:context:namespace` on its root prim; authors should use the stage prim name (e.g., `robot_1`, `robot_2`).

A modular asset's root namespace must be authored on its `defaultPrim`. When referencing that asset elsewhere, namespace overrides must be placed on the entry-point prim containing the composition arc to preserve `instanceable = true` compatibility. For duplicate sub-assets, each reference's entry-point prim must carry a distinct namespace via a local opinion — no source file modification is required. For example:

<details>
<summary>Example: Overriding namespace on duplicate sub-asset references</summary>

```
def Xform "robot" (
    prepend apiSchemas = ["RosContextAPI"]
) {
    string ros:context:namespace = "robot_1"

    def Xform "camera_left" (
        references = @./camera_module.usda@
        prepend apiSchemas = ["RosContextAPI"]
    ) {
        string ros:context:namespace = "camera_left"  # overrides "camera" from source
    }

    def Xform "camera_right" (
        references = @./camera_module.usda@
        prepend apiSchemas = ["RosContextAPI"]
    ) {
        string ros:context:namespace = "camera_right"  # overrides "camera" from source
    }
}
```

</details>

`RosContextAPI` prims must reside outside Payload arcs so the namespace graph can be resolved without loading heavy geometry (see Section 2.2). Sub-assets intended for per-instance namespace override should not set `instanceable = true`, as descendant prims become instance proxies whose attributes cannot be overridden; any override must be authored on the reference root prim or an ancestor outside the Payload arc.


### 2.2 Interface Placement

ROS interface schemas (`RosTopicAPI`, `RosServiceAPI`, `RosActionAPI`) must be applied to prims according to these placement rules:

*   **Robot-wide interfaces:** Aggregate interfaces spanning a kinematic tree (e.g., `JointState` publisher, `FollowJointTrajectory` server) should be decoupled from the physical rigid-body hierarchy. Authors should place them on dedicated, non-physical logical prims (e.g., `/Robot/Interfaces`) descendant from the `RosContextAPI` prim.
*   **Sensor interfaces:** Localized interfaces (e.g., `Image`, `LaserScan`) must be placed on a child `UsdGeomXform` of the physical link. Multiple interfaces for the same sensor (e.g., `image_raw` and `camera_info`) must distribute them across separate child prims, one interface per prim.
*   **Interface prims must reside outside payloads.** Prims bearing `Ros*API` schemas are part of the lightweight kinematic/interface graph and must be traversable without loading geometry payloads.

### 2.3 Interface Resolution
For all schema types (Topics, Services, Actions) defined below:
*   **Type Resolution:** Tooling and compliant simulators must attempt to resolve the `ros:*:type` string (e.g., `sensor_msgs/msg/Image`) dynamically against the sourced ROS environment. If the interface type is not found, the simulator must safely disable that specific interface, allow the rest of the asset to function normally, and emit a distinct warning/error.
*   **Name Validation:** All `ros:*:name` values must adhere to ROS topic naming rules (alphanumeric, underscores, and forward slashes only; cannot start with a number).
*   **Initialization State:** All ROS interfaces (`RosTopicAPI`, `RosServiceAPI`, `RosActionAPI`) support a `bool ros:*:starts_enabled` attribute (`Optional`, `Default: true`). This dictates the initialization state of the interface at load time, preventing startup conflicts or unwanted compute overhead. Runtime lifecycle management (e.g., dynamically disabling the publisher mid-simulation) is the responsibility of the simulator.

### 2.4 Topic Interface (`RosTopicAPI`)
Applies to Prims that exchange streaming ROS data.

**Core Attributes (Required):**
*   `token ros:topic:role`: Values: `["publisher", "subscription"]`.
*   `string ros:topic:name`: The topic name relative to the active namespace.
*   `string ros:topic:type`: The ROS message type.
*   `double ros:topic:publish_rate`: Target publication frequency in Hz. Required for publishers; ignored for subscriptions.

**Optional Override**

*   `string ros:topic:override_frame_id (Optional):` Overrides the `header.frame_id` populated in the published ROS message. This must only be used to reference external global frames (e.g., "map", "earth") that cannot exist natively within the USD stage. Relevant only for message types containing a `std_msgs/Header`.

**Quality of Service (QoS):**
Maps directly to `rmw_qos_profile_t` policies. If an attribute is omitted, simulators must assume the specified defaults. *(Note: As per REP 2003, simulated sensors should default to `"system_default"` which maps to best-effort, while map publishers should use `"transient_local"`).*
*   `bool ros:topic:qos:match_publisher` (Optional, Default: `false`). For subscriptions only. If `true`, the simulator bridge must attempt to use ROS QoS matching to adapt to the discovered publisher, ignoring explicit reliability/durability settings.
*   `token ros:topic:qos:reliability`: Values: `["system_default", "reliable", "best_effort"]`. (Default: `"system_default"`).
*   `token ros:topic:qos:durability`: Values: `["system_default", "transient_local", "volatile"]`. (Default: `"system_default"`).
*   `token ros:topic:qos:history`: Values: `["system_default", "keep_last", "keep_all"]`. (Default: `"system_default"`).
*   `int ros:topic:qos:depth`: Queue size. Evaluated only when history is `keep_last`. (Default: `10`).

### 2.5 Service Interface (`RosServiceAPI`)
Applies to Prims handling synchronous requests (e.g., blinking lights).
*   `token ros:service:role`: Values: `["server", "client"]`. (Simulation assets are typically `server`).
*   `string ros:service:name`: The service name.
*   `string ros:service:type`: The service type (e.g., `std_srvs/srv/SetBool`).

### 2.6 Action Interface (`RosActionAPI`)
Applies to Prims handling asynchronous, long-running behaviors.
*   `token ros:action:role`: Values: `["server", "client"]`. (Simulation assets are typically `server`).
*   `string ros:action:name`: The action name.
*   `string ros:action:type`: The action type (e.g., `control_msgs/action/FollowJointTrajectory`).

### 2.7 Frame Publishing and TF2 (`RosFrameAPI`)
Mapping a deeply nested OpenUSD scene graph directly to a ROS TF tree can cause significant performance overhead. To prevent flooding the `/tf` topic with generic physical props (e.g., warehouse boxes), compliant simulators should not broadcast transforms for every `PhysicsRigidBodyAPI`. 

Instead, simulators should follow a hybrid implicit/explicit approach for broadcasting `tf2` transforms:

*   **Implicit TF Broadcasting (The Asset Tree):** Simulators should automatically infer and broadcast TF frames (using the ROS-validated Prim name) for Prims that represent a ROS interface structure:
    1.  **The ROS Root:** Any Prim possessing the `RosContextAPI` (often the `base_link`).
    2.  **Kinematic Chains:** Any Prim possessing a `PhysicsRigidBodyAPI` that is connected (directly or recursively) via a `UsdPhysicsJoint` to a Prim already in the TF tree. This captures robot arms and wheeled bases automatically.
    *   **Routing Rule:** If the implicit frame is connected to its parent via a `PhysicsFixedJoint`, or has no joint but is rigidly parented in the USD hierarchy, the simulator must broadcast it to `/tf_static`. All movable joint connections must be broadcast to `/tf`.
    *   Prims bearing only `RosTopicAPI`, `RosServiceAPI`, or `RosActionAPI` do not generate TF frames. An interface prim's `frame_id` is determined by its nearest ancestor that is a TF frame (implicit or explicit).

*   **Explicit TF Broadcasting (`RosFrameAPI`):** To publish TFs for non-physical dummy frames (e.g., a kinematic `grasp_point`, a `camera_optical_frame`), asset authors must apply the `RosFrameAPI` schema to the target `UsdGeomXform` Prim.
    *   `string ros:frame:id` (Optional): Overrides the TF frame name. If omitted, the validated Prim name is used.
    *   `bool ros:frame:static` (Optional, Default: `true`): Defines the broadcast destination. If `true`, the simulator must broadcast the frame to `/tf_static` relative to its USD parent. If `false` (e.g., an Xform animated by USD TimeSamples), it must be broadcast to `/tf`.

Note: The broadcast frequency of TF frames is an implementation detail left to the simulator's runtime configuration.

### 2.8 Optical Frames
OpenUSD cameras natively face the -Z axis, whereas ROS optical frames (REP 103) must face +Z. To bridge this without opaque simulator-side rotations, authors must decouple the physical sensor from its optical interface. Authors must create a child UsdGeomXform (e.g., `camera_optical_frame`) rotated 180 degrees around its local X-axis. All RosTopicAPI and RosFrameAPI schemas must be applied exclusively to this optical frame, ensuring deterministic data orientation in RViz.

### 2.9 Prohibited Interfaces

Simulator-level interfaces are prohibited in assets to avoid clashes, including:

*   `/clock` topic (`rosgraph_msgs/msg/Clock` interface) for simulation time.
*   Any interfaces included in the `simulation_interfaces` package (e.g. spawning, simulation control).

### 2.10 Custom ROS joint names.

A number of concepts in ROS (e.g. robot descriptions, controllers) rely on joints names. 
To ensure that joints are correctly identified and mapped to said concepts, the custom property `ros:joint:name` may be applied to all Prims bearing built-in `UsdPhysicsJoint` schema. If this property is authored, its value is the single source of truth for ROS-facing joint identity, including mapping for `FollowJointTrajectory` action goals, `JointState` messages, integration with `ros2_control`, and for conversion to other formats (e.g., MJCF's `<joint name="">`). Authors should keep the property value and the prim name aligned where naming rules permit. If this property is missing, simulators must fall back to using the prim name.

## 3. Export and Conversion

To guarantee that assets can be converted to glTF 2.0 and successfully exported to work with lightweight applications and standard ROS tools (e.g., RViz, MoveIt), such as for publishing of a URDF string to `/robot_description`, without mandating native OpenUSD support, assets must adhere to this constrained subset.

### 3.1 Material Portability
*   **Normative Surface:** Assets must use UsdPreviewSurface as the normative surface definition to ensure a direct mapping to glTF 2.0's pbrMetallicRoughness workflow. Target converters may also support OpenPBR[AOUSD-OPENPBR].
*   **Material Terminals (Render Contexts)**: A UsdShadeMaterial acts as a container. Proprietary shaders (e.g., MDL, OSL) must not replace the universal surface output. Assets should bind a single Material universally. Inside that Material, the UsdPreviewSurface must be wired to the universal outputs:surface terminal (which glTF/web converters natively parse), while proprietary shaders may be included by wiring them to renderer-specific terminals (e.g., outputs:mdl:surface).
*   **Texture Coordinates & UDIMs:** Multi-tile UV mapping (UDIMs) is unsupported by glTF 2.0 and many real-time engines, and must not be used. Unique UVs must be packed into the [0, 1] space (Texture Atlasing). If multiple high-resolution textures are required for a single mesh, authors must partition the geometry using UsdGeomSubset (with `familyName="materialBind"`) and assign separate materials. UV coordinates outside [0, 1] are reserved for seamless tiling textures using repeat wrap modes.

### 3.2 Texture File Formats
To ensure native portability across OpenUSD, lightweight simulators, and glTF 2.0, texture formats are constrained:
*   **Surface Maps (PNG/JPEG):** 8-bit PNG and JPEG are the only permitted formats for materials.
    *   **Data Maps:** Normal, Metallic, Roughness, and packed ORM maps must use lossless PNG. JPEG compression artifacts destructively alter PBR math.
    *   **Color Maps:** BaseColor and Emissive maps may use JPEG to reduce footprint, provided they lack an alpha channel.
*   **KTX2** — Treat KTX2 strictly as a downstream glTF export target via `KHR_texture_basisu` glTF extension. Standard OpenUSD lacks native plugins for KTX2.
*   **Prohibited formats:** EXR, TIFF, and other HDR/DCC formats must not be used for albedo, normal, or ORM maps in distributed assets. These formats have no glTF pathway and introduce unacceptable payload overhead for lightweight tooling.
*   **Environment**: As an exception, High Dynamic Range (.hdr) files are permitted only for UsdLuxDomeLight environment maps.

### 3.3 Texture Baking
Procedural texture graphs (noise generation, math nodes, node graphs) are not interoperable and must be baked down into explicit data using either:
1.  **Image-Backed Textures:** Standard UV-mapped image files routed through standard UsdUVTexture shader nodes.
2.  **Mesh primitive variables (Primvars)** such as baked vertex colors using standard OpenUSD interpolations. `"vertex"` interpolation is recommended, as `"uniform"` and `"faceVarying"` require converters to split the mesh vertices to comply with glTF’s vertex attribute requirements.

### 3.4 Geometry Constraints
*   **Triangulation:** Collision meshes must be explicitly triangulated by the author. Visual meshes may use quads or n-gons, but converters targeting glTF 2.0 must triangulate all geometry at export time.
*   **Face Orientation:** Meshes must use `orientation = "rightHanded"` (the OpenUSD default), which defines counter-clockwise vertex winding as front-facing. This aligns with glTF 2.0's mandatory CCW front faces. Assets must not rely on `doubleSided = true` to mask incorrect winding.
*   **Manifold topology:** Collision meshes must be watertight (closed, manifold) and free of self-intersections to ensure stable physics and mass derivation. Non-manifold geometry (e.g., open edges) is limited to purely visual meshes.

### 3.5 Instanceable Leaves
Repetitive geometry (bolts, LED arrays on a sensor) must utilize native OpenUSD instancing to minimize memory footprint. Authors must only instance leaf geometry (visuals and colliders), not logical Prims containing PhysicsRigidBodyAPI, Joints, or Ros*API schemas, as OpenUSD instance proxies obscure child prims from relationship targeting. Authors must use one of two mechanisms to ensure correct glTF conversion:
*   **Scenegraph instancing (`instanceable=true`):** Used for identical structural components (e.g., bolts). Note: The OpenUSD specification requires the prim to compose its geometry via a composition arc (Reference or Payload) for this flag to be valid. Converters must map this to native glTF Node sharing (multiple nodes referencing a single mesh index).
*   **Point instancing (`UsdGeomPointInstancer`):** Used for massive arrays of atomic meshes (e.g., LED grids, warehouse clutter). It scatters a prototype using flat arrays of transforms. Converters must map this directly to the glTF EXT_mesh_gpu_instancing extension.

### 3.6 Lighting
Lighting must be authored using core UsdLux schemas. To ensure deterministic illumination across standard rasterization-based simulators (e.g., Gazebo, MuJoCo, O3DE) and compatibility with web converters, authors must adhere to the following:
*    **Punctual lights:** Assets should prioritize standard punctual lights: `UsdLuxDistantLight` (Directional), `UsdLuxSphereLight` (Point), and `UsdLuxSphereLight` modified by the `UsdLuxShapingAPI` (Spot). Converters must map these directly to the glTF `KHR_lights_punctual` extension.
*    **Area lights:** Complex area lights (e.g., `UsdLuxRectLight`, `UsdLuxCylinderLight`) lack universal support outside of path-traced engines and should be avoided for interoperable assets.
*    **Emissive materials and functional lights:** The `emissiveColor` attribute on a `UsdPreviewSurface` must be used for indicators such as robot status LEDs so the source itself appears bright. However, emissive geometry must not be used for primary scene illumination, as standard simulator rasterizers will not compute their light transport. If a robot component must actively illuminate its surroundings, authors must co-locate a standard `UsdLux` punctual light with the emissive geometry under the same parent `Xform`. The material provides the visible glow of the source, while the paired `UsdLux` prim provides the interoperable scene illumination.

### 3.7 Variant Baking for Export
While OpenUSD natively handles structural variants, many of the simulation tools and formats in the ecosystem don't, including URDF, SDF and glTF 2.0. Due to the burden of implementation, this REP proposes both a baseline and an advanced compliance:
*    **Baseline compliance:** Converters must export only the resolved variant: an explicit selection if provided, otherwise the default authored per Section 1.2.4, destructively discarding all others. This resolved state must be baked by flattening OpenUSD composition arcs into a static, logically nested kinematic tree. Never flatten into world-space, as this permanently destroys local joint transforms and ROS TF trees.
*    **Advanced compliance (material variants support):** Capable exporters may preserve material variations via the `KHR_materials_variants` extension. Because OpenUSD can arbitrarily override granular shader parameters, tools must evaluate each variant state, bake them into distinct glTF Material IDs in memory, and author the swap mapping.
*    **Fallback:** The glTF extension is invalid if a variant alters underlying mesh topology or applied schemas. If geometry or structure changes, or if the exporter lacks discrete state-evaluation logic, tools must safely fall back to Baseline Compliance.

### 3.8 Lossy Conversion

OpenUSD and robotics XML formats (URDF, SDF, MJCF) are fundamentally mismatched paradigms. Because OpenUSD lacks native schemas for domain-specific data (e.g., URDF `<transmission>`, MJCF `<actuator>`), conversions are inherently lossy. Exporters must adhere to the following:
*   **Payload Resolution:** The active simulation payload (kinematics, inertia, colliders) is the extraction priority. OpenUSD composition arcs and instance proxies must be fully baked into explicit geometry and transforms, never discarded.
*   **API Translation:** Ros*API schemas must map exclusively to modern extension blocks (e.g., SDF `<plugin>`, MJCF `<extension>`). Obsolete approaches such as injecting legacy `<gazebo>` tags into URDF are not allowed.
*   **Discard, not inject:** OpenUSD-native metadata (layer stacks, unselected variants) must be cleanly discarded. Injecting custom, non-standard XML elements to store unmappable OpenUSD states is not recommended. If pipeline necessitates it for practicality, such metadata must be confined to valid, format-native extension points.

## 4. The Interoperability Ecosystem

A canonical repository for core schema, extension schemas and compliance tooling is `ros-simulation/openusd-schemas`. 

### 4.1 Core ROS Schema Definition
The normative OpenUSD schema definition for all `Ros*API` schemas is provided in `core/ros/schema.usda`. It can be used with `usdGenSchema` to produce either a codeless plugin (schema awareness and fallback values only) or full C++ and Python bindings for simulator integration.


### 4.2 Schema Registry

Due to the number and dynamic nature of extensions for physics, controls and sensors, they will be handled as extension schemas to interoperability profile compliance. Extension schemas will be submitted and ratified independently. The following is mandated:

- A submission must follow the rules of this REP where applicable, e.g. including declarative parameters that can be implemented across simulators, and adhering to general rules for sensors and control schemas (e.g. graceful degradation). A submission may include one or more vendor or physic engine specific layers as outlined in Section 1.4.
- A submission must include addition to Compliance Checker and any other supplementary conversion tools within the repository, which allows the use of new schema to be validated. A submission must also include documentation of use and a minimal example asset.

#### 4.2.1 General Extension Schema Rules

Additional schemas are to be defined through extensions, chiefly for sensors and controls. They must follow these general rules:

*   **Use of Native Schemas:** Schema definitions must leverage core OpenUSD primitives to prevent attribute duplication. For example, `SensorCameraAPI` must apply to a `UsdGeomCamera` to append digital hardware metadata while natively reusing its optical properties. If no native analogue exists, schemas must be applied to a standard `UsdGeomXform`.
*   **Separation of Transport:** Extension schemas must not include metadata to handle ROS communication (e.g., topic names, QoS). Instead, they should utilize relationships to target distinct transport prims (e.g., `RosTopicAPI`) to expose their data or commands.
*   **Deprecation Policy:** If the core OpenUSD specification formally ratifies an equivalent schema, the corresponding extension schema will be deprecated. Tooling will subsequently migrate assets to the official core standard.

#### 4.2.2 Physics Schemas

To leverage emerging simulation features without violating vendor-neutrality (Section 1.4), the registry will host physics extension schemas based on upstream proposals (e.g., from Linux Foundation Newton USD Schemas[NEWTON-SCHEMAS] or AOUSD working groups), as "Incubating Schemas". These schemas must adhere to the following rules:

*   **Namespace:** To prevent collisions with core OpenUSD updates, incubating physics schemas must use the `ExtendedPhysics` class prefix and the `ext_physics:` property prefix, followed by a concept-specific sub-namespace (e.g. `ext_physics::mimic`). Vendor prefixes (e.g., `newton:`) and core prefixes (e.g., `physics:`) are prohibited.
*   **Translation:** OpenUSD does not natively support schema aliasing. Assets generated by tools using vendor-specific staging schemas must be processed via ecosystem tooling (e.g., automated compliance fixers) to replace them with their `ExtendedPhysics*` equivalents prior to distribution.

**Schema Lifecycle:** Physics extensions progress through three namespaces: vendor prefixes (e.g., `newton:`) during in-tool development, the neutral `ext_physics:` prefix for cross-engine incubation in the schema registry, and `physics:` once AOUSD ratifies the schema into core OpenUSD. The `rep_sanitizer` tool handles the first transition; the deprecation policy in Section 4.2.1 handles the second. Vendor prefixes are prohibited in distributed assets because they encode engine identity into properties that should be engine-neutral; the `physics:` prefix is reserved for AOUSD-ratified schemas. `ext_physics:` exists to fill the gap between the two.

#### 4.2.3 Control Schemas

In addition to general extension schema rules, control interfaces and controllers must follow these rules:
*   **Explicit Targeting:** Controllers should be decoupled from the physical rigid-body hierarchy: authors should place them on dedicated logical prims (e.g., `/Robot/Controllers`) and explicitly target their actuated mechanisms. Simulators must not rely on Xform scene graph nesting to infer a controller's scope. Controllers must declare targets using OpenUSD relationships (`rel`) or standard `UsdCollectionAPI` collections.
*   **Actuation via Physics:** Control schemas should interface with dynamic bodies through the simulation's physics pipeline. Position, velocity, and effort targets must be routed through normative OpenUSD dynamics paradigms (e.g., `UsdPhysicsDriveAPI`) or universally ratified extension schemas, deferring to isolated vendor extensions only when a ratified standard for the required actuation modality does not exist. Controllers that directly manipulate spatial transforms should only actuate prims where `physics:kinematicEnabled = true`. Control schemas should not handle simulator-level state changes (e.g., native simulator state APIs or ROS `simulation_interfaces`), including resets for RL training or entity state manipulation.
*   **Runtime selection:** A single asset may contain multiple, mutually exclusive control paradigms for the same hardware (e.g., trajectory control vs. direct effort control). While `VariantSets` remain the standard for structural hardware changes, simulators should provide dynamic lifecycle management of controllers to support runtime switching. The asset's authored state must prevent write conflicts at load time by ensuring controllers actuating the same targets are not simultaneously active (e.g., via a `bool control:starts_enabled` schema property).

#### 4.2.4 Sensor Schemas

In addition to general extension schema rules, sensor schemas must follow these rules:
*   **Ground Truth:** Sensor schemas must emulate measurable phenomena to ensure valid Software-in-the-Loop (SiL) testing. Simulator-generated Ground Truth artifacts (e.g., semantic segmentations, bounding boxes) must not be bundled into physical sensor schemas; they should be explicitly requested via dedicated annotator schemas.
*   **Traversal:** Sensor schemas must be applied directly to the `UsdGeomXform` or `UsdGeomCamera` defining their physical origin and local coordinate frame. To ensure efficient parser discovery, these prims must reside in the asset's lightweight, traversable kinematic hierarchy.
*   **Graceful Degradation:** Sensor schemas must define a functional, universal baseline of parameters. Advanced, engine-specific behaviors (e.g., proprietary rendering profiles, custom noise models) must be authored exclusively via vendor-namespaced custom attributes (e.g., `isaac:`, `gazebo:`). Simulators must safely ignore unrecognized namespaces and gracefully fall back to the universal baseline.

### 4.3 Compliant Assets 

A canonical repository of open-source, compliant simulation assets is to be established as `ros-simulation/openusd-assets`. These assets will have payloads hosted independently (e.g. in a dedicated repository such as Hugging Face) and must pass the Compliance Checker.

## Rationale

- **Why OpenUSD?:** This REP does not argue against any other formats. OpenUSD is useful for robotics due to:
    - Volume and quality of assets authored and a value such assets have for building robotic simulations.
    - Adoption and existing drive for the standard towards robotics.
    - Connection to a broad ecosystem and tooling.
- **Extensions:** A version of this REP with sensor and control schemas was considered, but the scale of dealing with all of these at once speaks against such an approach. Thus, the REP takes on a core + extensions model, following OpenUSD and glTF 2.0 practice.
- **Scope limit:** This REP does not regulate how simulation-level interfaces (such as `/clock` topic) are to be implemented, only that they are not a part of compliant assets. This scope limit is important so that diverse implementations of ROS communication in simulators can be supported.
- **glTF:** glTF 2.0 was selected as primary export pathway due to support in multiple ROS simulators, its complementary lightweight nature, and an ongoing development of the format in direction of robotics simulation.
- **Upstream dependency:** This REP intentionally tracks active work at AOUSD, including the Separation of Concerns proposal for asset identifiers (Section 1.2.5), incubating physics schemas (Section 4.2.2), and forthcoming output from the physics and robotics Working Groups. As these are ratified, this REP will adopt the official mechanisms and deprecate its provisional equivalents. This imposes a maintenance burden on REP and schema-registry maintainers and a migration burden on simulator vendors and asset authors, but is the correct trade-off: the alternative is a ROS-specific dialect of OpenUSD that forfeits the ecosystem advantages motivating its adoption in the first place.

## How to Teach This

The standard introduced by this REP is a subject of automation through compliance, assistant and conversion tooling. It is to be used by simulation asset authors (including use of new schemas), developers of simulation import and export features, and developers of compliance and conversion tooling. However, resulting compliant assets are beneficial for a broad robotics community. 

### Documentation Updates

-  **ROS Tutorials->Simulators:** add a new chapter on interoperable assets and cross-reference the compliant asset repository.

### Other Resources

-  **Reference assets:** the canonical asset repository (Section 4.3) serves as worked examples; each asset is documented with the layer structure, applied schemas and compliance notes, making it easy to replicate.
-  **Compliance checker:** the compliance checker will output exact violations with references to the corresponding REP sections, making it easy to adjust assets step-by-step and learn the standard in the process.

## Implementation

This REP is implemented through the core schema and the registry described in Section 4, as well as tools to be provided within `ros-simulation/openusd-schemas` repository:

### Compliance Checker
A REP compliance checker is to be developed and shared with the community. The tool will provide validation of all REP recommendations for OpenUSD assets and supply actionable feedback for the user for every violation or non-conformance.

### Supplementary migration tools

A compliance fixer (e.g., `rep_sanitizer`) will be provided for common issues that can be handled by automated scripting, including:

*   **Schema Translation:** Stripping proprietary staging schemas and replacing them with their neutral `ExtendedPhysics` equivalents (see Section 4.2.2).
*   **Transform Standardization:** Automatically decomposing baked 4x4 CAD matrices (`xformOp:transform`) into the mandated `translate` and `orient` operations (Section 1.1).
*   **Vendor Isolation:** Scanning for and extracting engine-specific properties (e.g., `isaac:`, `mujoco:`) from the baseline payload into isolated proprietary overlays (Section 1.4).


## References
*   **[NVIDIA-ETL-PIPELINE]** NVIDIA, Intrinsic, Disney Research. "Using OpenUSD for Modular and Scalable Robotic Simulation and Development". URL: `https://developer.nvidia.com/blog/using-openusd-for-modular-and-scalable-robotic-simulation-and-development/`
*   **[NVIDIA-ASSETS]** NVIDIA, "Content Guidelines and Requirements". URL: `https://docs.omniverse.nvidia.com/kit/docs/asset-requirements/latest/index.html`
*   **[ASWF-USD-ASSETS]** Academy Software Foundation USD Working Group, "Guidelines for Structuring USD Assets". (Targeting Commit: `main` as of March 2026).
*   **[AOUSD-OPENPBR]** Alliance for OpenUSD, "OpenPBR Surface Specification".
*   **[REP-2003]** ROS Enhancement Proposal 2003, "Sensor Data and Map QoS Settings".
*   **[GLTF-2.0]** Khronos Group, "glTF 2.0 Specification".
*   **[GLTF-EXT-INSTANCING]** Khronos Group, "EXT_mesh_gpu_instancing Extension Specification".
*   **[NEWTON-SCHEMAS]** Linux Foundation Newton Project. "Newton USD Schemas". URL: `https://github.com/newton-physics/newton-usd-schemas`

## License

This document is marked CC0 1.0 Universal.
To view a copy of this mark, visit [https://creativecommons.org/publicdomain/zero/1.0/](https://creativecommons.org/publicdomain/zero/1.0/).
