# 🔧 Backward Compatibility Fix Applied

## Issue
The new Pydantic validation was breaking existing code because `load_config()` was returning a `MainConfig` object instead of a dict by default.

## Fix
Changed `load_config()` default behavior to maintain 100% backward compatibility:

### Before (Breaking)
```python
config = load_config('config.yaml')  # Returned MainConfig object
config.get('general')  # ❌ AttributeError!
```

### After (Fixed)
```python
config = load_config('config.yaml')  # Returns dict by default
config.get('general')  # ✅ Works!
```

## Three Ways to Load Config

### 1. Default (Backward Compatible)
```python
from labelme_augmentor.config import load_config

config = load_config('config.yaml')  # Returns dict, no validation
processor = DatasetProcessor(config)  # ✅ All existing code works!
```

### 2. With Validation (Opt-in)
```python
from labelme_augmentor.config import load_config

config = load_config('config.yaml', validate=True)  # Returns validated dict
processor = DatasetProcessor(config)  # ✅ Works with validation!
```

### 3. Type-Safe (New Feature)
```python
from labelme_augmentor.config import load_config_validated

config = load_config_validated('config.yaml')  # Returns MainConfig object
print(config.general.seed)  # Type-safe access
dict_config = config.to_dict()  # Convert to dict when needed
```

## Summary

✅ **100% Backward Compatible** - All existing code works without changes
✅ **Opt-in Validation** - Enable with `validate=True` parameter
✅ **New Features Available** - Use `load_config_validated()` for type safety

No breaking changes! All existing configs and code continue to work.

---

**Your command should now work:**
```bash
labelme-augment --config config/labelme_augmentation_config45black.yaml
```
