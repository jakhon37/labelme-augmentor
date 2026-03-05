#!/usr/bin/env python3
"""
Custom augmentation example with class-specific settings.

This example shows how to apply different augmentation strategies
to different defect classes.
"""

from labelme_augmentor import DatasetProcessor


def main():
    """Custom augmentation with class-specific settings."""
    
    # Define configuration programmatically
    config = {
        "general": {
            "seed": 42,
            "num_workers": 4,
            "log_level": "INFO"
        },
        "paths": {
            "input_json_dir": "data/imbalanced/train",
            "output_dir": "data/balanced/train"
        },
        "output": {
            "images_subdir": "images",
            "annotations_subdir": "annotations",
            "create_debug_visualizations": True
        },
        # Light augmentation for common classes
        "global_augmentations": {
            "num_augmentations_per_image": 5,
            "transforms": [
                {"name": "HorizontalFlip", "probability": 0.5},
                {"name": "VerticalFlip", "probability": 0.5},
                {"name": "Rotate", "probability": 0.3, "params": {"limit": [-15, 15]}}
            ]
        },
        # Heavy augmentation for rare classes
        "class_specific": {
            "RareDefect": {
                "num_augmentations_per_image": 50,
                "transforms": [
                    {"name": "HorizontalFlip", "probability": 0.9},
                    {"name": "VerticalFlip", "probability": 0.9},
                    {"name": "Rotate", "probability": 0.8, "params": {"limit": [-45, 45]}},
                    {"name": "RandomRotate90", "probability": 0.9},
                    {"name": "ElasticTransform", "probability": 0.5}
                ]
            },
            "ColorSensitiveDefect": {
                "num_augmentations_per_image": 10,
                "transforms": [
                    # Only geometric transforms, no color changes
                    {"name": "HorizontalFlip", "probability": 0.5},
                    {"name": "VerticalFlip", "probability": 0.5}
                ]
            }
        },
        "validation": {
            "enabled": True,
            "min_defect_area": 20,
            "max_area_change_ratio": 0.5
        },
        "visualization": {
            "auto_generate_colors": True,
            "custom_colors": {
                "RareDefect": [255, 0, 0],  # Red
                "ColorSensitiveDefect": [0, 255, 0]  # Green
            }
        },
        "image_processing": {
            "output_format": "png"
        }
    }
    
    # Create and run processor
    processor = DatasetProcessor(config)
    processor.process_dataset()
    
    print("✅ Custom augmentation complete!")


if __name__ == "__main__":
    main()
