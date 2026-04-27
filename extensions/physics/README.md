# Extended Physics Schema

This schema provides an extended feature set for OpenUSD physics. It draws inspiration from work on [Newton Schemas](https://github.com/newton-physics/newton-usd-schemas), but ensures neutral naming and focus on full interoperabilty.


## Mimic Joints

Joints whose position is a linear function of another joint (e.g., parallel gripper fingers, coupled mechanisms) must declare the coupling declaratively using `ExtendedPhysicsMimicJointAPI`, a **SingleApply** API schema applied to the follower joint. `ExtendedPhysicsMimicJointAPI` must only be applied to `UsdPhysicsRevoluteJoint` or `UsdPhysicsPrismaticJoint` prims. The coupling operates on the joint's native positional value.
*   `rel mimic:joint`: Relationship to the source joint. Must use a USD relationship (not a string attribute) to ensure correct path remapping under composition arcs. Mimic relationships must form a Directed Acyclic Graph (DAG); chained couplings are valid, but cycles are prohibited.
*   `float mimic:multiplier` (Default: `1.0`): Scale factor. `follower_position = multiplier * source_position + offset`.
*   `float mimic:offset` (Default: `0.0`): Constant offset in the source joint's native units.
*   *Note: UsdPhysics does not currently provide a joint coupling mechanism. This schema fills that gap. Should AOUSD/ASWF standardize an equivalent under `UsdPhysics`, this REP would adopt the upstream schema.*

