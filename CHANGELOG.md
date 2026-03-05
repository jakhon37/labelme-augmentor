# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-27

### Added
- Complete modular architecture with industry best practices
- Package structure with `src/` layout
- Comprehensive type hints throughout
- Custom exception classes
- Checkpoint management as separate module
- Configuration loader module
- CLI entry point with `labelme-augment` command
- Full test infrastructure setup
- Development tooling (black, isort, ruff, mypy)
- Comprehensive README with examples
- Code quality configuration in `pyproject.toml`

### Changed
- **BREAKING**: Refactored monolithic `auglabelme.py` into modular components
  - `core/`: Augmentor and DatasetProcessor
  - `io/`: Image, LabelMe, and Mask operations
  - `transforms/`: Transform builder
  - `validation/`: Validation logic
  - `visualization/`: Colors and debug tools
  - `utils/`: Checkpoint and exceptions
- Improved error handling with custom exceptions
- Better separation of concerns following SOLID principles
- Enhanced logging and debugging

### Fixed
- Type safety improvements
- Better error messages
- More robust image loading

### Migration Guide
The old `auglabelme.py` can still be used, but the new modular API is recommended:

**Old way:**
```python
python auglabelme.py --config config.yaml
```

**New way:**
```python
labelme-augment --config config.yaml
```

**API Usage:**
```python
# Old (still works)
from auglabelme import DatasetProcessor

# New (recommended)
from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config
```

## [1.0.0] - Previous

### Initial Release
- Monolithic implementation in single file
- Basic augmentation functionality
- LabelMe JSON support
- Multiprocessing support
