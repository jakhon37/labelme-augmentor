"""Configuration loading utilities."""

from typing import Dict, Union

import yaml

from .schema import MainConfig
from .validator import ConfigValidator


def load_config(config_path: str, validate: bool = False) -> Dict:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        validate: If True, perform Pydantic validation (default False for backward compat)
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If validation fails (when validate=True)
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if validate:
        # Validate with Pydantic and convert back to dict
        validated = ConfigValidator.validate_and_prepare(config)
        return validated.to_dict()
    
    # Return raw dict for backward compatibility
    return config


def load_config_validated(config_path: str) -> MainConfig:
    """Load and validate configuration, returning MainConfig object.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Validated MainConfig instance
        
    Raises:
        ConfigError: If validation fails
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return ConfigValidator.validate_and_prepare(config)


def load_config_dict(config_path: str) -> Dict:
    """Load configuration as dictionary (explicit backward compatible function).
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
    """
    return load_config(config_path, validate=False)
