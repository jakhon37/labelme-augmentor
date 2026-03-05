#!/usr/bin/env python3
"""
Basic usage example for LabelMe Augmentor.

This example shows the simplest way to use the augmentor.
"""

from labelme_augmentor import DatasetProcessor
from labelme_augmentor.config import load_config


def main():
    """Basic augmentation example."""
    # Load configuration from YAML file
    config = load_config('configs/minimal_example.yaml', validate=False)
    
    # Update paths for your data
    config['paths']['input_json_dir'] = 'path/to/your/labelme/json/files'
    config['paths']['output_dir'] = 'path/to/output/directory'
    
    # Create processor and run
    processor = DatasetProcessor(config)
    processor.process_dataset()
    
    print("✅ Augmentation complete!")


if __name__ == "__main__":
    main()
