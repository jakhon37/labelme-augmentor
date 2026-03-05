# Migration Guide: v1.0 → v2.0

This guide helps you migrate from the monolithic `auglabelme.py` to the new modular architecture.

## 🔄 Quick Migration Checklist

- [ ] Install new dependencies: `pip install -r requirements.txt`
- [ ] Update import statements (if using as library)
- [ ] Update CLI commands (if using command-line)
- [ ] Test with existing configuration files
- [ ] Update any custom scripts

## 📋 What Changed?

### Architecture
- **Old**: Single 991-line file (`auglabelme.py`)
- **New**: Modular package with 22 files across 8 modules

### Installation
```bash
# Old (no installation)
python auglabelme.py --config config.yaml

# New (install as package)
pip install -e .
labelme-augment --config config.yaml
```

## 🔧 Command-Line Usage

### Option 1: New CLI Command (Recommended)
```bash
# After installation
labelme-augment --config config/labelme_augmentation_config.yaml

# With options
labelme-augment --config config.yaml --input /path/to/input --output /path/to/output
```

### Option 2: Backward Compatible Wrapper
```bash
# Use the compatibility wrapper
python auglabelme_v2.py --config config/labelme_augmentation_config.yaml
```

### Option 3: Keep Using Old Version
```bash
# The old file still works
python auglabelme.py --config config/labelme_augmentation_config.yaml
```

## 📚 Python API Changes

### Importing Modules

#### Old Way
```python
# Old monolithic import
from auglabelme import (
    DatasetProcessor,
    LabelMeAugmentor,
    ImageValidator,
    CheckpointManager,
    ConfigurableColorPalette,
)
```

#### New Way
```python
# New modular imports
from labelme_augmentor import DatasetProcessor, Augmentor
from labelme_augmentor.validation import MaskValidator
from labelme_augmentor.utils import CheckpointManager
from labelme_augmentor.visualization import ConfigurableColorPalette
from labelme_augmentor.config import load_config
```

### Using the API

#### Old Way
```python
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Process dataset
processor = DatasetProcessor(config)
processor.process_dataset()
```

#### New Way (Same!)
```python
from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config

# Load config (cleaner)
config = load_config('config.yaml')

# Process dataset (identical API)
processor = DatasetProcessor(config)
processor.process_dataset()
```

## 🎯 Benefits of Migration

### For Users
1. **Cleaner CLI**: `labelme-augment` instead of `python auglabelme.py`
2. **Better Error Messages**: Custom exceptions with clear messages
3. **Improved Performance**: Optimized module loading
4. **Type Safety**: Full type hints for IDE support

### For Developers
1. **Testability**: Each module can be tested independently
2. **Maintainability**: ~50-150 lines per file instead of 991
3. **Extensibility**: Easy to add new transforms, validators, formats
4. **Documentation**: Auto-generated from docstrings

## 🔍 Module Mapping

Old monolithic file → New modular structure:

| Old Class/Function | New Location |
|-------------------|--------------|
| `LabelMeAugmentor` | `labelme_augmentor.core.Augmentor` |
| `DatasetProcessor` | `labelme_augmentor.core.DatasetProcessor` |
| `ImageValidator` | `labelme_augmentor.validation.MaskValidator` |
| `CheckpointManager` | `labelme_augmentor.utils.CheckpointManager` |
| `ConfigurableColorPalette` | `labelme_augmentor.visualization.ConfigurableColorPalette` |
| Image loading logic | `labelme_augmentor.io.ImageLoader` |
| Image saving logic | `labelme_augmentor.io.ImageSaver` |
| LabelMe JSON I/O | `labelme_augmentor.io.LabelMeReader/Writer` |
| Mask conversion | `labelme_augmentor.io.MaskConverter` |
| Transform building | `labelme_augmentor.transforms.TransformBuilder` |
| Debug visualization | `labelme_augmentor.visualization.DebugVisualizer` |
| Config loading | `labelme_augmentor.config.load_config` |

## ⚙️ Configuration Files

**Good news**: All existing YAML configuration files work without changes!

```yaml
# Your existing config files remain compatible
general:
  seed: 42
  num_workers: null

paths:
  input_json_dir: "/path/to/input"
  output_dir: "/path/to/output"

global_augmentations:
  num_augmentations_per_image: 5
  transforms:
    - name: HorizontalFlip
      probability: 0.5
    # ... rest of your config
```

## 🧪 Testing Your Migration

### 1. Install the New Package
```bash
cd /path/to/labelme-augmentor
pip install -e .
```

### 2. Test Imports
```python
python3 -c "
from labelme_augmentor import DatasetProcessor, Augmentor
from labelme_augmentor.config import load_config
print('✅ All imports successful!')
"
```

### 3. Test CLI
```bash
labelme-augment --help
```

### 4. Run with Your Config
```bash
# Test with a small dataset first
labelme-augment --config config/labelme_augmentation_config.yaml --workers 1
```

## 🐛 Common Issues

### Issue 1: Module Not Found
```
ModuleNotFoundError: No module named 'labelme_augmentor'
```

**Solution**: Install the package
```bash
pip install -e .
```

### Issue 2: Import Errors
```
ImportError: cannot import name 'LabelMeAugmentor'
```

**Solution**: Update imports
```python
# Old
from auglabelme import LabelMeAugmentor

# New
from labelme_augmentor import Augmentor  # renamed for clarity
```

### Issue 3: Old auglabelme.py Still Running
**Solution**: Use the new CLI command explicitly
```bash
labelme-augment --config config.yaml  # not python auglabelme.py
```

## 📞 Getting Help

If you encounter issues during migration:

1. Check this guide thoroughly
2. Look at the [examples/](examples/) directory
3. Open an issue on GitHub with:
   - Your migration step
   - Error message
   - Python version
   - Operating system

## 🎉 Migration Complete!

After successful migration, you should see:
- ✅ Cleaner code organization
- ✅ Better error messages
- ✅ Improved performance
- ✅ IDE autocomplete support
- ✅ Easier debugging
- ✅ Professional package structure

**Next Steps:**
- Explore new features in the [README.md](README.md)
- Check out [examples/](examples/) for advanced usage
- Consider contributing improvements!

---

**Questions?** Open an issue on GitHub or check the documentation.
