"""Image loading and saving utilities."""

import logging
from typing import Dict

import cv2
import numpy as np
from PIL import Image

from ..utils.exceptions import ImageLoadError


class ImageLoader:
    """Load images with robust format handling."""

    def __init__(self, config: Dict) -> None:
        """Initialize image loader.
        
        Args:
            config: Image processing configuration
        """
        self.config = config.get('image_processing', {})

    def load(self, image_path: str) -> np.ndarray:
        """Load image with robust format handling.
        
        Args:
            image_path: Path to image file
            
        Returns:
            RGB numpy array
            
        Raises:
            ImageLoadError: If image cannot be loaded
        """
        # Try OpenCV first
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None:
            # Try PIL for other formats
            try:
                pil_img = Image.open(image_path)
                image = np.array(pil_img)
            except Exception as e:
                raise ImageLoadError(f"Failed to load image {image_path}: {e}")
        else:
            # Convert BGR to RGB for OpenCV images
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # Normalize format
        image = self.normalize_format(image)

        return image

    def normalize_format(self, image: np.ndarray) -> np.ndarray:
        """Normalize image to RGB 8-bit format.
        
        Args:
            image: Input image array
            
        Returns:
            Normalized RGB image
            
        Raises:
            ImageLoadError: If image format is invalid
        """
        # Handle 16-bit images
        if image.dtype == np.uint16:
            if self.config.get('normalize_16bit', True):
                image = (image / 256).astype(np.uint8)
            else:
                image = image.astype(np.uint8)

        # Handle float images
        elif image.dtype in [np.float32, np.float64]:
            image = (image * 255).astype(np.uint8)

        # Handle different channel counts
        if len(image.shape) == 2:
            # Grayscale to RGB
            if self.config.get('handle_grayscale', True):
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image = np.stack([image] * 3, axis=-1)

        elif len(image.shape) == 3:
            if image.shape[2] == 4:
                # RGBA to RGB
                if self.config.get('handle_rgba', True):
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                else:
                    image = image[:, :, :3]
            elif image.shape[2] == 1:
                # Single channel to RGB
                image = np.repeat(image, 3, axis=2)

        # Validate image size
        if self.config.get('validate_loaded_images', True):
            self._validate_size(image)

        return image

    def _validate_size(self, image: np.ndarray) -> None:
        """Validate image dimensions.
        
        Args:
            image: Image to validate
            
        Raises:
            ImageLoadError: If image size is invalid
        """
        min_size = self.config.get('min_image_size', [32, 32])
        max_size = self.config.get('max_image_size', [8192, 8192])
        h, w = image.shape[:2]

        if h < min_size[1] or w < min_size[0]:
            raise ImageLoadError(
                f"Image too small: {w}x{h}, minimum is {min_size[0]}x{min_size[1]}"
            )
        if h > max_size[1] or w > max_size[0]:
            logging.warning(f"Image very large: {w}x{h}, consider resizing")


class ImageSaver:
    """Save images with proper format handling."""

    def __init__(self, config: Dict) -> None:
        """Initialize image saver.
        
        Args:
            config: Image processing configuration
        """
        self.config = config.get('image_processing', {})

    def save(self, image: np.ndarray, path: str) -> None:
        """Save image with proper format handling.
        
        Args:
            image: RGB image to save
            path: Output path
        """
        output_format = self.config.get('output_format', 'png').lower()

        if output_format in ['jpg', 'jpeg']:
            quality = self.config.get('output_quality', 95)
            cv2.imwrite(
                path,
                cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, quality],
            )
        else:
            cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
