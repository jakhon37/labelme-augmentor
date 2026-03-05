#!/usr/bin/env python3
"""
Example using the programmatic API for fine-grained control.

This shows how to use individual components directly.
"""

import numpy as np
from pathlib import Path

from labelme_augmentor.io import ImageLoader, MaskConverter, LabelMeReader
from labelme_augmentor.transforms import TransformBuilder
from labelme_augmentor.validation import MaskValidator
from labelme_augmentor.visualization import DebugVisualizer


def process_single_image(json_path: str, config: dict):
    """Process a single image with full control."""
    
    # Setup components
    reader = LabelMeReader()
    image_loader = ImageLoader(config)
    
    # Define class mapping
    class_names = ["scratch", "dent", "discoloration"]
    class_map = {name: idx + 1 for idx, name in enumerate(class_names)}
    idx_to_class = {idx: name for name, idx in class_map.items()}
    
    # Create mask converter
    mask_converter = MaskConverter(class_map, idx_to_class)
    
    # Load data
    labelme_data = reader.load_json(json_path)
    json_dir = str(Path(json_path).parent)
    image = reader.load_image_from_json(labelme_data, json_dir, image_loader)
    
    # Convert to mask
    mask = mask_converter.labelme_to_mask(labelme_data)
    
    # Build transforms
    transforms_config = [
        {"name": "HorizontalFlip", "probability": 1.0},
        {"name": "Rotate", "probability": 0.5, "params": {"limit": 15}}
    ]
    transform = TransformBuilder.build_transform(transforms_config)
    
    # Apply transforms
    augmented = transform(image=image, mask=mask)
    aug_image = augmented['image']
    aug_mask = augmented['mask']
    
    # Validate
    validator = MaskValidator(config)
    if validator.validate_mask(aug_mask, mask):
        print("✅ Augmentation passed validation")
        
        # Convert back to shapes
        shapes = mask_converter.mask_to_labelme_shapes(aug_mask)
        print(f"✅ Generated {len(shapes)} shapes")
        
        # Create debug visualization
        visualizer = DebugVisualizer(
            idx_to_class=idx_to_class,
            custom_colors={},
            default_colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255]]
        )
        debug_viz = visualizer.create_overlay(image, aug_image, aug_mask)
        print(f"✅ Created debug visualization: {debug_viz.shape}")
    else:
        print("❌ Augmentation failed validation")


def main():
    """Run programmatic API example."""
    
    config = {
        "image_processing": {
            "output_format": "png"
        },
        "validation": {
            "enabled": True,
            "min_defect_area": 20,
            "max_area_change_ratio": 0.5
        }
    }
    
    # Process a single file
    # process_single_image("path/to/your/file.json", config)
    
    print("See function 'process_single_image' for usage example")


if __name__ == "__main__":
    main()
