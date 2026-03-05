"""Pydantic schemas for type-safe configuration validation."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class LogLevel(str, Enum):
    """Available logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class GeneralConfig(BaseModel):
    """General application settings."""
    
    seed: int = Field(default=42, description="Random seed for reproducibility")
    num_workers: Optional[int] = Field(
        default=None, 
        description="Number of worker processes (None = auto-detect)"
    )
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    enable_base64: bool = Field(
        default=False, 
        description="Enable base64 encoding in LabelMe JSON"
    )
    resume_from_checkpoint: bool = Field(
        default=True,
        description="Resume from checkpoint if available"
    )
    checkpoint_file: str = Field(
        default="augmentation_checkpoint.json",
        description="Checkpoint filename"
    )
    
    @field_validator('num_workers')
    @classmethod
    def validate_num_workers(cls, v: Optional[int]) -> Optional[int]:
        """Validate number of workers."""
        if v is not None and v < 1:
            raise ValueError("num_workers must be >= 1 or None")
        return v


class PathsConfig(BaseModel):
    """Input/Output path configuration."""
    
    input_json_dir: str = Field(description="Directory containing input LabelMe JSON files")
    output_dir: str = Field(description="Output directory for augmented data")
    
    @field_validator('input_json_dir', 'output_dir')
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Validate that paths are not empty."""
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_input_exists(self) -> 'PathsConfig':
        """Validate that input directory exists."""
        input_path = Path(self.input_json_dir)
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {self.input_json_dir}")
        if not input_path.is_dir():
            raise ValueError(f"Input path is not a directory: {self.input_json_dir}")
        return self


class OutputConfig(BaseModel):
    """Output structure configuration."""
    
    images_subdir: str = Field(default="images", description="Images subdirectory name")
    annotations_subdir: str = Field(
        default="annotations",
        description="Annotations subdirectory name"
    )
    debug_subdir: str = Field(default="debug", description="Debug subdirectory name")
    create_debug_visualizations: bool = Field(
        default=True,
        description="Create debug overlay visualizations"
    )


class TransformConfig(BaseModel):
    """Single transform configuration."""
    
    name: str = Field(description="Transform name (albumentations class name)")
    probability: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Probability of applying transform"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Transform parameters"
    )


class GlobalAugmentationsConfig(BaseModel):
    """Global augmentation settings."""
    
    num_augmentations_per_image: int = Field(
        default=5,
        ge=0,
        description="Number of augmentations per image"
    )
    transforms: List[TransformConfig] = Field(
        default_factory=list,
        description="List of transforms to apply"
    )


class ClassSpecificConfig(BaseModel):
    """Class-specific augmentation settings."""
    
    num_augmentations_per_image: Optional[int] = Field(
        default=None,
        ge=0,
        description="Override number of augmentations for this class"
    )
    transforms: Optional[List[TransformConfig]] = Field(
        default=None,
        description="Override transforms for this class"
    )
    
    # Validation overrides
    min_defect_area: Optional[float] = Field(
        default=None,
        ge=0,
        description="Override minimum defect area in pixels for this class"
    )
    max_defect_area: Optional[float] = Field(
        default=None,
        ge=0,
        description="Override maximum defect area in pixels for this class"
    )
    min_defect_length: Optional[float] = Field(
        default=None,
        ge=0,
        description="Override minimum defect length (major axis) in pixels for this class"
    )
    max_defect_length: Optional[float] = Field(
        default=None,
        ge=0,
        description="Override maximum defect length (major axis) in pixels for this class"
    )
    min_contour_points: Optional[int] = Field(
        default=None,
        ge=3,
        description="Override minimum contour points for this class"
    )
    check_defect_preservation: Optional[bool] = Field(
        default=None,
        description="Override defect preservation check for this class"
    )
    max_area_change_ratio: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Override max allowed area change ratio for this class"
    )
    reject_border_defects: Optional[bool] = Field(
        default=None,
        description="Override border defect rejection for this class"
    )
    border_margin: Optional[int] = Field(
        default=None,
        ge=0,
        description="Override border margin in pixels for this class"
    )


class ValidationConfig(BaseModel):
    """Validation settings."""
    
    enabled: bool = Field(default=True, description="Enable validation")
    min_defect_area: float = Field(
        default=20.0,
        ge=0,
        description="Minimum defect area in pixels"
    )
    max_defect_area: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum defect area in pixels"
    )
    min_defect_length: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum defect length (major axis) in pixels"
    )
    max_defect_length: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum defect length (major axis) in pixels"
    )
    min_contour_points: int = Field(
        default=3,
        ge=3,
        description="Minimum contour points"
    )
    check_defect_preservation: bool = Field(
        default=True,
        description="Check if defects are preserved after augmentation"
    )
    max_area_change_ratio: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Maximum allowed area change ratio"
    )
    reject_border_defects: bool = Field(
        default=False,
        description="Reject defects touching image border"
    )
    border_margin: int = Field(
        default=5,
        ge=0,
        description="Border margin in pixels"
    )
    
    @model_validator(mode='after')
    def validate_areas(self) -> 'ValidationConfig':
        """Validate area and length constraints."""
        if self.max_defect_area is not None:
            if self.max_defect_area < self.min_defect_area:
                raise ValueError(
                    f"max_defect_area ({self.max_defect_area}) must be >= "
                    f"min_defect_area ({self.min_defect_area})"
                )
        
        if self.min_defect_length is not None and self.max_defect_length is not None:
            if self.max_defect_length < self.min_defect_length:
                raise ValueError(
                    f"max_defect_length ({self.max_defect_length}) must be >= "
                    f"min_defect_length ({self.min_defect_length})"
                )
        return self


class VisualizationConfig(BaseModel):
    """Visualization settings."""
    
    auto_generate_colors: bool = Field(
        default=True,
        description="Auto-generate colors for unlimited classes"
    )
    custom_colors: Dict[str, List[int]] = Field(
        default_factory=dict,
        description="Custom colors per class name"
    )
    default_colors: List[List[int]] = Field(
        default_factory=lambda: [
            [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0],
            [255, 0, 255], [0, 255, 255], [128, 0, 0], [0, 128, 0],
            [0, 0, 128], [128, 128, 0]
        ],
        description="Default color palette"
    )
    
    @field_validator('custom_colors')
    @classmethod
    def validate_custom_colors(cls, v: Dict[str, List[int]]) -> Dict[str, List[int]]:
        """Validate custom colors are RGB triplets."""
        for class_name, color in v.items():
            if len(color) != 3:
                raise ValueError(f"Color for '{class_name}' must be RGB triplet, got {len(color)} values")
            if not all(0 <= c <= 255 for c in color):
                raise ValueError(f"Color values for '{class_name}' must be 0-255")
        return v


class ImageProcessingConfig(BaseModel):
    """Image processing settings."""
    
    supported_formats: List[str] = Field(
        default=['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'],
        description="Supported image formats"
    )
    output_format: str = Field(default='png', description="Output image format")
    output_quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="Output JPEG quality (1-100)"
    )
    normalize_16bit: bool = Field(
        default=True,
        description="Normalize 16-bit images to 8-bit"
    )
    handle_grayscale: bool = Field(
        default=True,
        description="Convert grayscale to RGB"
    )
    handle_rgba: bool = Field(
        default=True,
        description="Convert RGBA to RGB"
    )
    validate_loaded_images: bool = Field(
        default=True,
        description="Validate image dimensions"
    )
    min_image_size: List[int] = Field(
        default=[32, 32],
        description="Minimum image size [width, height]"
    )
    max_image_size: List[int] = Field(
        default=[8192, 8192],
        description="Maximum image size [width, height]"
    )


class MainConfig(BaseModel):
    """Main configuration schema."""
    
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    paths: PathsConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    global_augmentations: GlobalAugmentationsConfig = Field(
        default_factory=GlobalAugmentationsConfig
    )
    class_specific: Dict[str, ClassSpecificConfig] = Field(
        default_factory=dict,
        description="Class-specific augmentation overrides"
    )
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    image_processing: ImageProcessingConfig = Field(default_factory=ImageProcessingConfig)
    
    model_config = {
        "extra": "allow",  # Allow extra fields for backward compatibility
        "validate_assignment": True,
    }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for legacy code."""
        return self.model_dump(exclude_none=True)
