# API Reference

Complete API reference for LabelMe Augmentor.

## Core Modules

### Augmentor

::: labelme_augmentor.core.Augmentor
    options:
      show_root_heading: true
      show_source: false

The main augmentation class for processing individual images.

**Example:**
```python
from labelme_augmentor import Augmentor

augmentor = Augmentor(class_names=["defect1", "defect2"], config=config)
num_saved = augmentor.process_file(
    json_path="input.json",
    output_images_dir="output/images",
    output_json_dir="output/json",
    debug_dir="output/debug"
)
```

### DatasetProcessor

::: labelme_augmentor.core.DatasetProcessor
    options:
      show_root_heading: true
      show_source: false

Batch processor for entire datasets with multiprocessing support.

**Example:**
```python
from labelme_augmentor import DatasetProcessor

processor = DatasetProcessor(config)
processor.process_dataset()
```

## I/O Modules

### ImageLoader

::: labelme_augmentor.io.ImageLoader
    options:
      show_root_heading: true

Robust image loading with format normalization.

### ImageSaver

::: labelme_augmentor.io.ImageSaver
    options:
      show_root_heading: true

Image saving with format control.

### LabelMeReader

::: labelme_augmentor.io.LabelMeReader
    options:
      show_root_heading: true

Read LabelMe JSON files.

### LabelMeWriter

::: labelme_augmentor.io.LabelMeWriter
    options:
      show_root_heading: true

Write LabelMe JSON files.

### MaskConverter

::: labelme_augmentor.io.MaskConverter
    options:
      show_root_heading: true

Convert between LabelMe shapes and numpy masks.

## Validation

### MaskValidator

::: labelme_augmentor.validation.MaskValidator
    options:
      show_root_heading: true

Validate augmented masks meet quality criteria.

## Configuration

### MainConfig

::: labelme_augmentor.config.MainConfig
    options:
      show_root_heading: true

Main configuration schema with Pydantic validation.

### ConfigValidator

::: labelme_augmentor.config.ConfigValidator
    options:
      show_root_heading: true

Validate and prepare configurations.

## Utilities

### CheckpointManager

::: labelme_augmentor.utils.CheckpointManager
    options:
      show_root_heading: true

Manage checkpoints for resume functionality.

## Visualization

### ConfigurableColorPalette

::: labelme_augmentor.visualization.ConfigurableColorPalette
    options:
      show_root_heading: true

Generate colors for visualization.

### DebugVisualizer

::: labelme_augmentor.visualization.DebugVisualizer
    options:
      show_root_heading: true

Create debug visualizations.

## Transforms

### TransformBuilder

::: labelme_augmentor.transforms.TransformBuilder
    options:
      show_root_heading: true

Build albumentations transforms from configuration.
