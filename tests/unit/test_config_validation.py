"""Unit tests for configuration validation."""

import pytest
from pydantic import ValidationError

from labelme_augmentor.config import ConfigValidator, MainConfig
from labelme_augmentor.utils.exceptions import ConfigError


class TestConfigSchema:
    """Test Pydantic configuration schema."""
    
    def test_minimal_config(self, temp_dir):
        """Test minimal valid configuration."""
        config_dict = {
            "paths": {
                "input_json_dir": str(temp_dir),
                "output_dir": str(temp_dir / "output")
            }
        }
        config = MainConfig(**config_dict)
        assert config.general.seed == 42  # Default value
        assert config.paths.input_json_dir == str(temp_dir)
    
    def test_invalid_num_workers(self):
        """Test validation of num_workers."""
        with pytest.raises(ValidationError):
            MainConfig(
                paths={"input_json_dir": "/tmp", "output_dir": "/tmp/out"},
                general={"num_workers": 0}  # Invalid: must be >= 1 or None
            )
    
    def test_invalid_probability(self):
        """Test validation of transform probability."""
        with pytest.raises(ValidationError):
            MainConfig(
                paths={"input_json_dir": "/tmp", "output_dir": "/tmp/out"},
                global_augmentations={
                    "transforms": [
                        {"name": "HorizontalFlip", "probability": 1.5}  # Invalid: > 1.0
                    ]
                }
            )
    
    def test_validation_config(self):
        """Test validation configuration."""
        config = MainConfig(
            paths={"input_json_dir": "/tmp", "output_dir": "/tmp/out"},
            validation={
                "min_defect_area": 20,
                "max_defect_area": 1000,
                "max_area_change_ratio": 0.5
            }
        )
        assert config.validation.min_defect_area == 20
        assert config.validation.max_defect_area == 1000
    
    def test_invalid_area_constraints(self):
        """Test that max_defect_area must be >= min_defect_area."""
        with pytest.raises(ValidationError):
            MainConfig(
                paths={"input_json_dir": "/tmp", "output_dir": "/tmp/out"},
                validation={
                    "min_defect_area": 100,
                    "max_defect_area": 50  # Invalid: less than min
                }
            )
    
    def test_custom_colors_validation(self):
        """Test custom colors validation."""
        with pytest.raises(ValidationError):
            MainConfig(
                paths={"input_json_dir": "/tmp", "output_dir": "/tmp/out"},
                visualization={
                    "custom_colors": {
                        "defect1": [255, 0]  # Invalid: not RGB triplet
                    }
                }
            )


class TestConfigValidator:
    """Test ConfigValidator class."""
    
    def test_validate_config_success(self, sample_config):
        """Test successful configuration validation."""
        config = ConfigValidator.validate_config(sample_config)
        assert isinstance(config, MainConfig)
        assert config.general.seed == 42
    
    def test_validate_config_failure(self):
        """Test configuration validation failure."""
        invalid_config = {
            "paths": {
                "input_json_dir": "",  # Empty path
                "output_dir": "/tmp/out"
            }
        }
        with pytest.raises(ConfigError):
            ConfigValidator.validate_config(invalid_config)
    
    def test_validate_paths_no_json_files(self, temp_dir):
        """Test path validation when no JSON files exist."""
        config_dict = {
            "paths": {
                "input_json_dir": str(temp_dir),
                "output_dir": str(temp_dir / "output")
            }
        }
        config = MainConfig(**config_dict)
        
        with pytest.raises(ConfigError, match="No JSON files found"):
            ConfigValidator.validate_paths(config)
    
    def test_validate_paths_with_json_files(self, sample_dataset, temp_dir):
        """Test path validation with JSON files."""
        config_dict = {
            "paths": {
                "input_json_dir": str(sample_dataset),
                "output_dir": str(temp_dir / "output")
            }
        }
        config = MainConfig(**config_dict)
        
        # Should not raise
        ConfigValidator.validate_paths(config)
    
    def test_validate_transforms_success(self, sample_config):
        """Test transform validation success."""
        config = MainConfig(**sample_config)
        # Should not raise
        ConfigValidator.validate_transforms(config)
    
    def test_validate_transforms_invalid(self, sample_config):
        """Test transform validation with invalid transform."""
        sample_config["global_augmentations"]["transforms"] = [
            {"name": "InvalidTransformName", "probability": 0.5}
        ]
        config = MainConfig(**sample_config)
        
        with pytest.raises(ConfigError, match="Unknown transforms"):
            ConfigValidator.validate_transforms(config)
    
    def test_validate_and_prepare_complete(self, sample_dataset, temp_dir):
        """Test complete validation and preparation."""
        config_dict = {
            "paths": {
                "input_json_dir": str(sample_dataset),
                "output_dir": str(temp_dir / "output")
            },
            "global_augmentations": {
                "num_augmentations_per_image": 2,
                "transforms": [
                    {"name": "HorizontalFlip", "probability": 0.5}
                ]
            }
        }
        
        config = ConfigValidator.validate_and_prepare(config_dict)
        assert isinstance(config, MainConfig)
        assert config.paths.input_json_dir == str(sample_dataset)
