"""Custom exceptions for labelme-augmentor package."""


class LabelMeAugmentorError(Exception):
    """Base exception for all labelme-augmentor errors."""
    pass


class ConfigError(LabelMeAugmentorError):
    """Raised when there's an error in configuration."""
    pass


class ValidationError(LabelMeAugmentorError):
    """Raised when validation fails."""
    pass


class ImageLoadError(LabelMeAugmentorError):
    """Raised when image loading fails."""
    pass


class AugmentationError(LabelMeAugmentorError):
    """Raised when augmentation fails."""
    pass


class CheckpointError(LabelMeAugmentorError):
    """Raised when checkpoint operations fail."""
    pass
