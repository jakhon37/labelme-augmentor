"""Configuration validation utilities."""

import logging
from pathlib import Path
from typing import Any, Dict

from pydantic import ValidationError

from .schema import MainConfig
from ..utils.exceptions import ConfigError


class ConfigValidator:
    """Validate and normalize configuration."""

    @staticmethod
    def validate_config(config_dict: Dict[str, Any]) -> MainConfig:
        """Validate configuration dictionary using Pydantic schema.
        
        Args:
            config_dict: Raw configuration dictionary from YAML
            
        Returns:
            Validated MainConfig instance
            
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            validated_config = MainConfig(**config_dict)
            logging.info("✓ Configuration validated successfully")
            return validated_config
        except ValidationError as e:
            error_msg = ConfigValidator._format_validation_errors(e)
            raise ConfigError(f"Configuration validation failed:\n{error_msg}")
    
    @staticmethod
    def _format_validation_errors(error: ValidationError) -> str:
        """Format Pydantic validation errors for user-friendly display.
        
        Args:
            error: Pydantic ValidationError
            
        Returns:
            Formatted error message
        """
        errors = []
        for err in error.errors():
            location = " → ".join(str(loc) for loc in err['loc'])
            message = err['msg']
            errors.append(f"  • {location}: {message}")
        return "\n".join(errors)
    
    @staticmethod
    def validate_paths(config: MainConfig) -> None:
        """Additional path validation and warnings.
        
        Args:
            config: Validated configuration
        """
        # Check input directory has JSON files
        input_path = Path(config.paths.input_json_dir)
        json_files = list(input_path.glob("*.json"))
        
        if not json_files:
            raise ConfigError(
                f"No JSON files found in input directory: {config.paths.input_json_dir}"
            )
        
        logging.info(f"✓ Found {len(json_files)} JSON files in input directory")
        
        # Check output directory doesn't exist or is empty (warning only)
        output_path = Path(config.paths.output_dir)
        if output_path.exists():
            output_contents = list(output_path.iterdir())
            if output_contents:
                logging.warning(
                    f"Output directory is not empty: {config.paths.output_dir}. "
                    f"Existing files may be overwritten."
                )
    
    @staticmethod
    def validate_transforms(config: MainConfig) -> None:
        """Validate that all transforms are available in albumentations.
        
        Args:
            config: Validated configuration
        """
        try:
            import albumentations as A
        except ImportError:
            raise ConfigError("albumentations package not installed")
        
        # Collect all transform names
        transform_names = set()
        
        # Global transforms
        for t in config.global_augmentations.transforms:
            transform_names.add(t.name)
        
        # Class-specific transforms
        for class_config in config.class_specific.values():
            if class_config.transforms:
                for t in class_config.transforms:
                    transform_names.add(t.name)
        
        # Validate each transform
        invalid_transforms = []
        for name in transform_names:
            if not hasattr(A, name):
                invalid_transforms.append(name)
        
        if invalid_transforms:
            raise ConfigError(
                f"Unknown transforms: {', '.join(invalid_transforms)}. "
                f"Check albumentations documentation for available transforms."
            )
        
        logging.info(f"✓ All {len(transform_names)} transforms are valid")
    
    @staticmethod
    def validate_and_prepare(config_dict: Dict[str, Any]) -> MainConfig:
        """Complete validation and preparation of configuration.
        
        Args:
            config_dict: Raw configuration dictionary
            
        Returns:
            Validated and prepared MainConfig
            
        Raises:
            ConfigError: If validation fails
        """
        # Step 1: Validate schema
        config = ConfigValidator.validate_config(config_dict)
        
        # Step 2: Validate paths
        ConfigValidator.validate_paths(config)
        
        # Step 3: Validate transforms
        ConfigValidator.validate_transforms(config)
        
        # Step 4: Log summary
        logging.info("✓ Configuration validation complete")
        logging.info(f"  - Input: {config.paths.input_json_dir}")
        logging.info(f"  - Output: {config.paths.output_dir}")
        logging.info(f"  - Workers: {config.general.num_workers or 'auto'}")
        logging.info(
            f"  - Global augmentations: {config.global_augmentations.num_augmentations_per_image}"
        )
        logging.info(f"  - Class overrides: {len(config.class_specific)}")
        
        return config
