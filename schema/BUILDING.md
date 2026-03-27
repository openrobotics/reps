# Building the usdRos2 Schema Plugin

All commands run from `schema/`.

## Prerequisites

- OpenUSD v26.03+ built with Python support
- Set environment:
  ```bash
  source env.sh
  ```

## Codeless Plugin (schema awareness only, no C++ build)

Add `bool skipCodeGeneration = true` to `schema.usda` GLOBAL customData, then:

```bash
mkdir -p plugin/usdRos2/resources
usdGenSchema schema.usda plugin/usdRos2/resources
```

Fix paths in `plugin/usdRos2/resources/plugInfo.json`:
```json
"LibraryPath": "",
"ResourcePath": ".",
"Root": ".",
"Type": "resource"
```

Register:
```bash
export PXR_PLUGINPATH_NAME=$(pwd)/plugin/usdRos2/resources
```

## Full C++ + Python Code Generation

Remove `skipCodeGeneration` from `schema.usda` if present, then:

```bash
usdGenSchema schema.usda plugin/usdRos2
```

This generates per schema: `{name}.h`, `{name}.cpp`, `wrap{Name}.cpp`,
plus shared `tokens.h/.cpp`, `plugInfo.json`, `generatedSchema.usda`.

Only changed files are rewritten on subsequent runs.

## Validation

```bash
usdchecker ../examples/otto600/OTTO600.usda
```
```bash
PXR_PLUGINPATH_NAME=$(pwd)/plugin/usdRos2/resources python3 tools/traverse_ros2.py
```
