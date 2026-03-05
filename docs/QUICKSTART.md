# 🚀 Quick Start Guide - LabelMe Augmentor v2.0

## Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Package (Optional but Recommended)
```bash
# Install in editable mode for development
pip install -e .

# This enables the 'labelme-augment' command globally
```

## Usage Options

### Option 1: CLI Command (Recommended)
After installation, use the professional CLI command:

```bash
# Basic usage
labelme-augment --config config/labelme_augmentation_config45black.yaml

# Override paths
labelme-augment --config config.yaml \
    --input /path/to/input \
    --output /path/to/output

# Use multiple workers
labelme-augment --config config.yaml --workers 8

# Debug mode
labelme-augment --config config.yaml --debug --workers 1

# Clear checkpoint and restart
labelme-augment --config config.yaml --clear-checkpoint
```

### Option 2: Python API
Use as a library in your Python code:

```python
from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config

# Load configuration
config = load_config('config/labelme_augmentation_config45black.yaml')

# Process dataset
processor = DatasetProcessor(config)
processor.process_dataset()
```

### Option 3: Compatibility Wrapper (For Migration)
If you're migrating from v1.0:

```bash
python auglabelme_v2.py --config config/labelme_augmentation_config45black.yaml
```

### Option 4: Original Script (Still Works)
Your old script still works unchanged:

```bash
python auglabelme.py --config config/labelme_augmentation_config45black.yaml
```

## Configuration

All your existing YAML configuration files work without changes!

### Minimal Config Example
```yaml
general:
  seed: 42
  num_workers: null  # auto-detect

paths:
  input_json_dir: "/path/to/labelme/json/files"
  output_dir: "/path/to/output"

global_augmentations:
  num_augmentations_per_image: 5
  transforms:
    - name: HorizontalFlip
      probability: 0.5
    - name: VerticalFlip
      probability: 0.5
```

## Testing Your Setup

### Test 1: Verify Installation
```bash
python3 -c "from labelme_augmentor import __version__; print(f'✅ Version: {__version__}')"
```

### Test 2: Run with Existing Config
```bash
# Use one of your existing configs
labelme-augment --config config/labelme_augmentation_config45black.yaml --workers 1
```

### Test 3: Check Help
```bash
labelme-augment --help
```

## Common Commands

### Process Dataset with Default Settings
```bash
labelme-augment --config config.yaml
```

### Process with Custom Paths
```bash
labelme-augment --config config.yaml \
    --input /path/to/input \
    --output /path/to/output
```

### Process with Specific Number of Workers
```bash
labelme-augment --config config.yaml --workers 4
```

### Debug Mode (Single Worker, Verbose)
```bash
labelme-augment --config config.yaml --debug --workers 1
```

### Clear Checkpoint and Reprocess All
```bash
labelme-augment --config config.yaml --clear-checkpoint
```

### Disable Checkpoint System
```bash
labelme-augment --config config.yaml --no-checkpoint
```

## Advanced Usage

### Use Individual Components
```python
from labelme_augmentor.io import ImageLoader, MaskConverter
from labelme_augmentor.validation import MaskValidator
from labelme_augmentor.transforms import TransformBuilder

# Load configuration
config = {'image_processing': {...}}

# Create image loader
loader = ImageLoader(config)
image = loader.load('path/to/image.jpg')

# Build transforms
transform = TransformBuilder.build_transform([
    {'name': 'HorizontalFlip', 'probability': 0.5},
    {'name': 'Rotate', 'probability': 0.3, 'params': {'limit': 15}}
])

# Apply transforms
augmented = transform(image=image, mask=mask)
```

## Troubleshooting

### ModuleNotFoundError
```bash
# If you get "ModuleNotFoundError: No module named 'labelme_augmentor'"
# Solution: Install the package
pip install -e .
```

### Command Not Found: labelme-augment
```bash
# If 'labelme-augment' command is not found
# Solution: Install the package in editable mode
pip install -e .

# Or use direct Python execution
python -m labelme_augmentor.cli --config config.yaml
```

### Old Import Errors
```python
# If you get import errors with old code
# Old: from auglabelme import LabelMeAugmentor
# New: from labelme_augmentor import Augmentor

# See MIGRATION_GUIDE.md for complete migration instructions
```

## Next Steps

1. ✅ Install the package: `pip install -e .`
2. ✅ Test with your existing config
3. ✅ Read the full README.md for advanced features
4. ✅ Check MIGRATION_GUIDE.md if migrating from v1.0

## Support

- 📖 Full documentation: [README.md](README.md)
- 🔄 Migration guide: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- 📝 Change history: [CHANGELOG.md](CHANGELOG.md)
- 📊 Refactoring details: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

---

**Happy Augmenting! 🎉**
