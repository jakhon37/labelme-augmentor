# Installation & Setup Guide

## Quick Installation

The package structure is complete. To use it, you need to install it:

```bash
# Install in editable mode (recommended for development)
pip install -e .

# Or install normally
pip install .
```

## Verification

After installation, verify everything works:

```bash
# Run the verification script
python scripts/verify_installation.py

# Or manually test imports
python -c "from labelme_augmentor import __version__; print(f'Version: {__version__}')"
```

## Development Setup

For development with all tools:

```bash
# 1. Install package in editable mode
pip install -e .

# 2. Install development dependencies
pip install -r requirements-dev.txt

# 3. Setup pre-commit hooks
pre-commit install

# 4. Run tests to verify
pytest

# 5. Run verification script
python scripts/verify_installation.py
```

## What Gets Installed

When you run `pip install -e .`, Python will:

1. Add `src/labelme_augmentor` to your Python path
2. Create the `labelme-augment` CLI command
3. Make all modules importable:
   ```python
   from labelme_augmentor import Augmentor, DatasetProcessor
   from labelme_augmentor.config import load_config, MainConfig
   # etc.
   ```

## Usage After Installation

### CLI Usage
```bash
labelme-augment --config config/labelme_augmentation_config.yaml
```

### Python API
```python
from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config

config = load_config('config.yaml')
processor = DatasetProcessor(config)
processor.process_dataset()
```

## Troubleshooting

### "No module named 'labelme_augmentor'"

**Solution**: Install the package:
```bash
pip install -e .
```

### "Command 'labelme-augment' not found"

**Solution**: Reinstall the package:
```bash
pip install -e . --force-reinstall
```

### Missing dependencies

**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

## Package Structure Is Complete!

All code is ready. You just need to install it to use it.

✅ 34 Python modules created
✅ 30+ tests written
✅ Complete documentation
✅ CI/CD configured
✅ Pre-commit hooks ready
✅ Examples provided

**Next step**: Run `pip install -e .`
