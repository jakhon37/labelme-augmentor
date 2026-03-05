"""Integration tests for end-to-end workflows."""

import json

import pytest

from labelme_augmentor import Augmentor, DatasetProcessor
from labelme_augmentor.config import load_config_dict


class TestEndToEndAugmentation:
    """Test complete augmentation pipeline."""
    
    def test_augmentor_process_file(self, sample_dataset, temp_dir, class_names):
        """Test Augmentor processing a single file."""
        config = {
            "general": {"seed": 42},
            "global_augmentations": {
                "num_augmentations_per_image": 2,
                "transforms": [
                    {"name": "HorizontalFlip", "probability": 1.0}
                ]
            },
            "class_specific": {},
            "validation": {"enabled": True, "min_defect_area": 5},
            "visualization": {"auto_generate_colors": True, "custom_colors": {}, "default_colors": []},
            "image_processing": {"output_format": "png"}
        }
        
        output_images = temp_dir / "images"
        output_json = temp_dir / "json"
        debug_dir = temp_dir / "debug"
        output_images.mkdir()
        output_json.mkdir()
        debug_dir.mkdir()
        
        augmentor = Augmentor(class_names, config)
        json_file = list(sample_dataset.glob("*.json"))[0]
        
        num_saved = augmentor.process_file(
            str(json_file),
            str(output_images),
            str(output_json),
            str(debug_dir),
            create_debug=True
        )
        
        # Should save original + augmentations
        assert num_saved >= 1
        assert len(list(output_images.iterdir())) >= 1
        assert len(list(output_json.iterdir())) >= 1
    
    def test_dataset_processor_full_pipeline(self, sample_dataset, temp_dir):
        """Test DatasetProcessor processing entire dataset."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        config = {
            "general": {
                "seed": 42,
                "num_workers": 1,
                "log_level": "INFO",
                "resume_from_checkpoint": False
            },
            "paths": {
                "input_json_dir": str(sample_dataset),
                "output_dir": str(output_dir)
            },
            "output": {
                "images_subdir": "images",
                "annotations_subdir": "annotations",
                "debug_subdir": "debug",
                "create_debug_visualizations": False  # Skip for speed
            },
            "global_augmentations": {
                "num_augmentations_per_image": 1,
                "transforms": [
                    {"name": "HorizontalFlip", "probability": 1.0}
                ]
            },
            "class_specific": {},
            "validation": {"enabled": True, "min_defect_area": 5},
            "visualization": {"auto_generate_colors": True, "custom_colors": {}, "default_colors": []},
            "image_processing": {"output_format": "png"}
        }
        
        processor = DatasetProcessor(config)
        processor.process_dataset()
        
        # Check outputs were created
        images_dir = output_dir / "images"
        json_dir = output_dir / "annotations"
        
        assert images_dir.exists()
        assert json_dir.exists()
        assert len(list(images_dir.iterdir())) > 0
        assert len(list(json_dir.iterdir())) > 0
    
    def test_checkpoint_resume(self, sample_dataset, temp_dir):
        """Test checkpoint and resume functionality."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        config = {
            "general": {
                "seed": 42,
                "num_workers": 1,
                "resume_from_checkpoint": True,
                "checkpoint_file": "test_checkpoint.json"
            },
            "paths": {
                "input_json_dir": str(sample_dataset),
                "output_dir": str(output_dir)
            },
            "output": {
                "images_subdir": "images",
                "annotations_subdir": "annotations",
                "create_debug_visualizations": False
            },
            "global_augmentations": {
                "num_augmentations_per_image": 1,
                "transforms": [{"name": "HorizontalFlip", "probability": 1.0}]
            },
            "class_specific": {},
            "validation": {"enabled": True},
            "visualization": {"auto_generate_colors": True, "custom_colors": {}, "default_colors": []},
            "image_processing": {"output_format": "png"}
        }
        
        # First run
        processor1 = DatasetProcessor(config)
        processor1.process_dataset()
        
        checkpoint_file = output_dir / "test_checkpoint.json"
        assert checkpoint_file.exists()
        
        # Load checkpoint
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)
        assert len(checkpoint_data["processed_files"]) > 0
        
        # Second run (should skip already processed)
        processor2 = DatasetProcessor(config)
        # Should load checkpoint and skip files
        assert len(processor2.checkpoint_manager.processed_files) > 0


class TestConfigValidationIntegration:
    """Test configuration validation in real scenarios."""
    
    def test_load_and_validate_config(self, temp_dir):
        """Test loading and validating a complete config."""
        config_path = temp_dir / "test_config.yaml"
        
        # Create a valid config file
        config_content = """
general:
  seed: 42
  num_workers: 1

paths:
  input_json_dir: "{input_dir}"
  output_dir: "{output_dir}"

global_augmentations:
  num_augmentations_per_image: 2
  transforms:
    - name: HorizontalFlip
      probability: 0.5
""".format(input_dir=str(temp_dir), output_dir=str(temp_dir / "output"))
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Should load successfully
        config = load_config_dict(str(config_path))
        assert config["general"]["seed"] == 42
