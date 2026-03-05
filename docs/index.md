# LabelMe Augmentor Documentation

Welcome to the LabelMe Augmentor documentation!

## Overview

LabelMe Augmentor is an advanced data augmentation tool specifically designed for LabelMe annotated datasets. It provides class-specific augmentation strategies, validation, and multiprocessing support.

## Features

- ✅ **Class-Specific Augmentation**: Different strategies per defect class
- ✅ **Multi-Class Mask Handling**: Seamless LabelMe JSON ↔ mask conversion
- ✅ **Validation System**: Ensures defects survive augmentation
- ✅ **Checkpoint/Resume**: Restart interrupted jobs
- ✅ **Multiprocessing**: Parallel processing for speed
- ✅ **Debug Visualizations**: Color-coded overlays
- ✅ **Type-Safe**: Full Pydantic validation
- ✅ **Flexible Configuration**: YAML-based with extensive options

## Quick Links

- [Installation Guide](installation.md)
- [Quick Start Tutorial](quickstart.md)
- [Configuration Reference](configuration.md)
- [API Documentation](api/index.md)
- [Examples](examples/index.md)
- [Architecture](architecture.md)

## Installation

```bash
pip install labelme-augmentor
```

Or from source:

```bash
git clone <repository-url>
cd labelme-augmentor
pip install -e .
```

## Quick Example

```python
from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config

# Load configuration
config = load_config('config.yaml')

# Process dataset
processor = DatasetProcessor(config)
processor.process_dataset()
```

## CLI Usage

```bash
labelme-augment --config config.yaml
```

## Support

- 📖 Documentation: [Read the Docs](https://labelme-augmentor.readthedocs.io)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/labelme-augmentor/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/labelme-augmentor/discussions)

## License

MIT License - see [LICENSE](../LICENSE) for details.
