# Architecture Overview

This document describes the architecture and design decisions of LabelMe Augmentor.

## Design Principles

### 1. Modularity (Single Responsibility Principle)
Each module has one clear responsibility:
- `core/` - Augmentation orchestration
- `io/` - Data input/output
- `validation/` - Quality checks
- `transforms/` - Transform building
- `visualization/` - Visual debugging
- `config/` - Configuration management
- `utils/` - Utilities and helpers

### 2. Type Safety
- Full type hints throughout the codebase
- Pydantic for runtime validation
- mypy for static type checking

### 3. Extensibility
- Easy to add new transforms (via albumentations)
- Easy to add new validators
- Easy to add new I/O formats

### 4. Performance
- Multiprocessing support for batch processing
- Checkpoint/resume for long-running jobs
- Efficient numpy operations

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI / API                            │
│                    (cli.py, __init__.py)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Layer                       │
│               (config/loader.py, schema.py)                  │
│                                                              │
│  ┌────────────┐    ┌──────────────┐    ┌────────────────┐ │
│  │   YAML     │───>│   Pydantic   │───>│   Validated   │ │
│  │   Config   │    │   Validation │    │    Config     │ │
│  └────────────┘    └──────────────┘    └────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                     Core Processing                          │
│                                                              │
│  ┌──────────────────┐          ┌──────────────────────┐    │
│  │ DatasetProcessor │          │     Augmentor        │    │
│  │                  │          │                      │    │
│  │ - Batch process  │────────> │ - Single image      │    │
│  │ - Multiprocess   │          │ - Per-class config  │    │
│  │ - Checkpoint     │          │ - Validation        │    │
│  └──────────────────┘          └──────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          v                v                v
┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│   I/O Layer     │ │  Validation  │ │  Visualization  │
│                 │ │              │ │                 │
│ - ImageLoader   │ │ - Mask       │ │ - Colors        │
│ - ImageSaver    │ │   Validator  │ │ - Debug         │
│ - LabelMeReader │ │ - Config     │ │   Overlays      │
│ - LabelMeWriter │ │   Validator  │ │                 │
│ - MaskConverter │ │              │ │                 │
└─────────────────┘ └──────────────┘ └─────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           v
                    ┌──────────────┐
                    │   Utilities  │
                    │              │
                    │ - Checkpoint │
                    │ - Exceptions │
                    │ - Logging    │
                    └──────────────┘
```

## Data Flow

### 1. Configuration Loading
```
YAML File → load_config() → Pydantic Validation → MainConfig
```

### 2. Dataset Processing
```
Input Directory
    ↓
DatasetProcessor.process_dataset()
    ↓
For each JSON file:
    ↓
Augmentor.process_file()
    ↓
    ├─> Load Image (ImageLoader)
    ├─> Convert to Mask (MaskConverter)
    ├─> Apply Transforms (TransformBuilder)
    ├─> Validate (MaskValidator)
    ├─> Convert to Shapes (MaskConverter)
    └─> Save (ImageSaver, LabelMeWriter)
    ↓
Output Directory
```

### 3. Transform Pipeline
```
Config → TransformBuilder → Albumentations Compose → Apply
```

## Module Details

### Core (`core/`)

#### Augmentor
- **Purpose**: Process single images with augmentation
- **Key Methods**:
  - `process_file()` - Main processing logic
  - `_setup_colors()` - Color palette setup
- **Dependencies**: io, validation, transforms, visualization

#### DatasetProcessor
- **Purpose**: Batch process datasets with multiprocessing
- **Key Methods**:
  - `process_dataset()` - Main entry point
  - `collect_class_names()` - Discover classes
- **Features**: Checkpoint support, multiprocessing

### I/O (`io/`)

#### ImageLoader
- **Purpose**: Robust image loading
- **Features**: 16-bit support, grayscale→RGB, RGBA→RGB
- **Methods**: `load()`, `normalize_format()`

#### MaskConverter
- **Purpose**: Convert between LabelMe and masks
- **Methods**: 
  - `labelme_to_mask()` - JSON shapes → numpy mask
  - `mask_to_labelme_shapes()` - numpy mask → JSON shapes

### Validation (`validation/`)

#### MaskValidator
- **Purpose**: Ensure augmentation quality
- **Checks**:
  - Minimum/maximum defect area
  - Contour point count
  - Border touching
  - Area preservation

### Configuration (`config/`)

#### Pydantic Schemas
- **MainConfig**: Root configuration
- **GeneralConfig**: General settings
- **PathsConfig**: Input/output paths
- **ValidationConfig**: Validation rules
- **And more...**

### Transforms (`transforms/`)

#### TransformBuilder
- **Purpose**: Build albumentations pipelines
- **Methods**:
  - `build_transform()` - Single transform list
  - `build_class_transforms()` - Per-class transforms

## Design Patterns

### 1. Factory Pattern
`TransformBuilder` creates transform pipelines from configuration.

### 2. Strategy Pattern
Different augmentation strategies per class via `class_specific` config.

### 3. Builder Pattern
Configuration building with Pydantic schemas.

### 4. Singleton Pattern
CheckpointManager per process.

## Error Handling

### Custom Exceptions
```python
LabelMeAugmentorError
├── ConfigError
├── ValidationError
├── ImageLoadError
├── AugmentationError
└── CheckpointError
```

### Error Flow
```
Try Operation
    ↓
Catch Specific Exception
    ↓
Log Detailed Error
    ↓
Raise Custom Exception
```

## Performance Considerations

### 1. Multiprocessing
- Default: `cpu_count() - 1` workers
- Each worker has own `Augmentor` instance
- Checkpoint updated after batch

### 2. Memory Management
- Images processed one at a time
- No caching by default
- Memory released after each file

### 3. I/O Optimization
- Batch checkpoint saves
- Efficient numpy operations
- CV2 for fast image operations

## Testing Strategy

### Unit Tests
- Test individual functions
- Mock external dependencies
- Fast execution

### Integration Tests
- Test module interactions
- Use real data
- Verify end-to-end flow

### Fixtures
- Sample images, masks, configs
- Reusable across tests

## Future Enhancements

### Planned Features
1. Support for COCO format
2. Support for YOLO format
3. Real-time augmentation preview
4. Web UI for configuration
5. Plugin system for custom transforms

### Performance Improvements
1. Caching for repeated operations
2. GPU acceleration (albumentations + cv2.cuda)
3. Streaming processing for huge datasets

### Quality Improvements
1. More sophisticated validation
2. Automatic quality metrics
3. Data distribution analysis
