# LabelMe Augmentor

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-yellow)

Advanced data augmentation tool for LabelMe annotated datasets with support for class-specific augmentation strategies, validation, and multiprocessing.

## 🌟 Features

- ✅ **Class-Specific Augmentation**: Different augmentation strategies per defect class
- ✅ **Multi-Class Mask Handling**: Seamless conversion between LabelMe JSON and numpy masks
- ✅ **Validation System**: Ensures defects survive augmentation with configurable rules
- ✅ **Checkpoint/Resume**: Restart interrupted jobs without losing progress
- ✅ **Multiprocessing**: Parallel processing for faster augmentation
- ✅ **Debug Visualizations**: Color-coded overlays for quality checking
- ✅ **Flexible Configuration**: YAML-based configuration with extensive options
- ✅ **Robust Image Loading**: Handles 16-bit, grayscale, RGBA formats automatically
- ✅ **Albumentations Integration**: 40+ dual transforms (image + mask) with access to 100+ total transforms

## 📦 Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd labelme-augmentor

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Using pip (when published)

```bash
pip install labelme-augmentor
```

## 🚀 Quick Start

### Basic Usage

```bash
# Run with config file
labelme-augment --config configs/examples/white_background.yaml

# Override paths
labelme-augment --config config.yaml \
    --input /path/to/input \
    --output /path/to/output

# Use multiple workers
labelme-augment --config config.yaml --workers 8
```

### Python API

```python
from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config

# Load configuration
config = load_config('config/my_config.yaml')

# Process dataset
processor = DatasetProcessor(config)
processor.process_dataset()
```

## 📝 Configuration

### Minimal Configuration

```yaml
# General settings
general:
  seed: 42
  num_workers: null  # auto-detect

# Input/Output paths
paths:
  input_json_dir: "/path/to/input/json"
  output_dir: "/path/to/output"

# Output structure
output:
  images_subdir: "images"
  annotations_subdir: "annotations"
  debug_subdir: "debug"
  create_debug_visualizations: true

# Global augmentations (applied to all classes)
global_augmentations:
  num_augmentations_per_image: 5
  transforms:
    - name: HorizontalFlip
      probability: 0.5
    - name: VerticalFlip
      probability: 0.5
    - name: Rotate
      probability: 0.3
      params:
        limit: [-15, 15]
```

### Advanced Configuration with Class-Specific Settings

```yaml
# Class-specific augmentation overrides
class_specific:
  # Rare defect - needs more augmentation
  T2-Depress:
    num_augmentations_per_image: 400
    max_area_change_ratio: 0.2
    transforms:
      - name: HorizontalFlip
        probability: 0.9
      - name: Rotate
        probability: 0.8
        params:
          limit: [-45, 45]
  
  # Color-sensitive defect - avoid color transforms
  T10-Discoloration:
    num_augmentations_per_image: 50
    min_defect_area: 100  # Larger minimum for this class
    max_area_change_ratio: 0.3  # More tolerant
    transforms:
      - name: HorizontalFlip
        probability: 0.5
      - name: VerticalFlip
        probability: 0.5
      # No color transforms
  
  # Small defect - strict validation
  T1-Pinhole:
    min_defect_area: 5  # Much smaller threshold
    max_area_change_ratio: 0.1  # Very strict preservation
    min_contour_points: 4
  
  # Edge defect - border-aware validation
  T5-EdgeCrack:
    reject_border_defects: true
    border_margin: 10

# Validation settings
validation:
  enabled: true
  min_defect_area: 20           # Minimum area in pixels
  max_defect_area: 50000        # Maximum area in pixels
  min_defect_length: null       # Minimum length (major axis) in pixels
  max_defect_length: null       # Maximum length (major axis) in pixels
  min_contour_points: 3
  check_defect_preservation: true
  max_area_change_ratio: 0.5    # Defect area as % of image (handles resizing correctly)
  reject_border_defects: false
  border_margin: 5
```

Each class can override **any validation parameter** (9 total):
- `min_defect_area` / `max_defect_area` - for different size ranges per defect type
- `min_defect_length` / `max_defect_length` - major axis length (works at any angle, great for scratches/cracks)
- `min_contour_points` - complex shapes need more points
- `check_defect_preservation` - disable for classes that tolerate deformation
- `max_area_change_ratio` - stricter/looser preservation thresholds (relative to image size, works correctly with resize transforms)
- `reject_border_defects` - enable for classes that shouldn't touch edges
- `border_margin` - different margin requirements per class

**Notes:**
- `max_area_change_ratio` compares defect area as a **percentage of total image area**, not absolute pixel counts. This ensures correct validation even when using resize transforms (e.g., `Resize`, `RandomResizedCrop`).
- `min/max_defect_length` measures the **major axis** (longest dimension) of the defect using a rotated bounding box. This works correctly for defects at any angle, making it ideal for linear defects like scratches, cracks, or abrasions.

All parameters fall back to global `validation` settings when not specified per-class.

## 🏗️ Project Structure

```
labelme-augmentor/
├── src/labelme_augmentor/
│   ├── core/              # Core augmentation logic
│   │   ├── augmentor.py   # Single image augmentation
│   │   └── processor.py   # Batch dataset processing
│   ├── io/                # Input/Output operations
│   │   ├── image.py       # Image loading/saving
│   │   ├── labelme.py     # LabelMe JSON I/O
│   │   └── mask.py        # Mask conversion
│   ├── transforms/        # Transform building
│   │   └── builder.py     # Build transforms from config
│   ├── validation/        # Validation utilities
│   │   └── validator.py   # Mask validation
│   ├── visualization/     # Visualization tools
│   │   ├── colors.py      # Color palette
│   │   └── debug.py       # Debug overlays
│   ├── config/            # Configuration management
│   │   └── loader.py      # Config loading
│   └── utils/             # Utilities
│       ├── checkpoint.py  # Checkpoint management
│       └── exceptions.py  # Custom exceptions
├── configs/               # Configuration files
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/              # Usage examples
```

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/labelme_augmentor

# Run specific test file
pytest tests/unit/test_augmentor.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api/)
- [Examples](examples/)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🐛 Known Issues

- None currently

## 🗺️ Roadmap

- [ ] Add support for COCO format
- [ ] Add support for YOLO format
- [ ] Add GUI for augmentation preview
- [ ] Add plugin system for custom transforms
- [ ] Add data quality metrics
- [ ] Publish to PyPI

## 📊 Supported Defect Types

The tool has been tested with the following defect types:
- T1-Scratch
- T2-Depress
- T4-AbrasionScratch
- T5-WhiteDot
- T7-MultipleDot
- T8-LightDot
- T9-DarkDot
- T10-Discoloration
- T13-ShinyDot
- T14-MatteDot
- T15-Stripe
- T18-EmbeddedForeignFiber
- T19-BlackLine
- T20-ShortScratch
- And more...

## 💡 Use Cases

- **Defect Detection**: Balance imbalanced defect datasets
- **Quality Control**: Augment rare defect samples
- **Computer Vision**: General-purpose LabelMe augmentation
- **Research**: Reproducible augmentation experiments

## 🙏 Acknowledgments

- Built with [Albumentations](https://albumentations.ai/) for powerful augmentations
- Designed for [LabelMe](https://github.com/wkentaro/labelme) annotation format

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ for the Computer Vision community**
