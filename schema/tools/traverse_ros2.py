# ABOUTME: Traverses a composed USD stage and discovers all ROS 2 interface
# ABOUTME: schemas (Ros2*API), printing a summary table of interfaces and attributes.

import sys
from collections import defaultdict
from pxr import Usd, Sdf


def get_ros2_schemas(prim):
    """Extract Ros2*API schema names from a prim's apiSchemas metadata.

    Works both with and without the codeless plugin loaded.
    With plugin: GetAppliedSchemas() returns Ros2 schemas directly.
    Without plugin: falls back to reading raw apiSchemas listOp metadata.
    """
    # Try the proper API first (works when plugin is registered)
    applied = prim.GetAppliedSchemas()
    ros2 = [s for s in applied if s.startswith("Ros2")]
    if ros2:
        return ros2

    # Fallback: read the raw apiSchemas metadata listOp and extract
    # the composed explicit items (result of all prepend/append/delete ops)
    meta = prim.GetMetadata("apiSchemas")
    if meta is None:
        return []
    items = list(meta.explicitItems) if meta.explicitItems else []
    return [s for s in items if s.startswith("Ros2")]


def get_ros2_attributes(prim):
    """Read all ros2:* authored attributes from a prim."""
    attrs = {}
    for attr in prim.GetAttributes():
        name = attr.GetName()
        if name.startswith("ros2:"):
            value = attr.Get()
            authored = attr.IsAuthored()
            attrs[name] = (value, authored)
    return attrs


def traverse_ros2_interfaces(stage_path):
    """Load a USD stage and print all ROS 2 interface schemas found."""
    stage = Usd.Stage.Open(stage_path)
    if not stage:
        print(f"ERROR: Could not open stage: {stage_path}")
        return 1

    print(f"=== ROS 2 Interface Summary for {stage_path} ===")
    print(f"Stage up axis: {stage.GetMetadata('upAxis')}")
    print(f"Stage meters/unit: {stage.GetMetadata('metersPerUnit')}")
    print()

    # Collect prims grouped by schema type
    schema_prims = defaultdict(list)
    total = 0

    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        ros2_schemas = get_ros2_schemas(prim)
        if not ros2_schemas:
            continue
        total += 1
        attrs = get_ros2_attributes(prim)
        for schema in ros2_schemas:
            schema_prims[schema].append((prim.GetPath(), attrs))

    print(f"Found {total} prims with Ros2 API schemas\n")

    # Print grouped by schema type
    for schema in sorted(schema_prims.keys()):
        prims = schema_prims[schema]
        print(f"--- {schema} ({len(prims)} prim{'s' if len(prims) != 1 else ''}) ---")
        for path, attrs in prims:
            print(f"  {path}")
            for attr_name in sorted(attrs.keys()):
                value, authored = attrs[attr_name]
                marker = "" if authored else " (fallback)"
                print(f"    {attr_name} = {value!r}{marker}")
        print()

    return 0


if __name__ == "__main__":
    stage_path = sys.argv[1] if len(sys.argv) > 1 else "../examples/otto600/OTTO600.usda"
    sys.exit(traverse_ros2_interfaces(stage_path))
