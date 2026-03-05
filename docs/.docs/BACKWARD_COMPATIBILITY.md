# Backward Compatibility Note

## Important: Config Loading

The new Pydantic validation is **optional** to maintain 100% backward compatibility.

### Default Behavior (Backward Compatible)
```python
from labelme_augmentor.config import load_config

# Returns dict (no validation) - works with all existing code
config = load_config('config.yaml')
processor = DatasetProcessor(config)  # ✅ Works!
```

### Optional: Enable Validation
```python
from labelme_augmentor.config import load_config

# Returns validated dict
config = load_config('config.yaml', validate=True)
processor = DatasetProcessor(config)  # ✅ Works with validation!
```

### New: Type-Safe Config Object
```python
from labelme_augmentor.config import load_config_validated

# Returns MainConfig object (Pydantic model)
config = load_config_validated('config.yaml')
# Use config.general.seed, config.paths.input_json_dir, etc.
# Convert to dict when needed: config.to_dict()
```

## Summary

- **Default**: `load_config()` returns dict (no breaking changes)
- **Opt-in**: `load_config(validate=True)` returns validated dict
- **New**: `load_config_validated()` returns MainConfig object

All existing code continues to work without changes!
