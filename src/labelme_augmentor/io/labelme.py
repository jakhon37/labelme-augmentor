"""LabelMe JSON file I/O operations."""

import base64
import json
import os
from io import BytesIO
from typing import Dict, List

import numpy as np
from PIL import Image

from .image import ImageLoader


class LabelMeReader:
    """Read and parse LabelMe JSON files."""

    @staticmethod
    def load_json(json_path: str) -> Dict:
        """Load and parse LabelMe JSON file.
        
        Args:
            json_path: Path to LabelMe JSON file
            
        Returns:
            Parsed JSON data
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data

    def load_image_from_json(
        self, labelme_data: Dict, json_dir: str, image_loader: ImageLoader
    ) -> np.ndarray:
        """Load image from LabelMe JSON with improved format handling.
        
        Args:
            labelme_data: LabelMe JSON data
            json_dir: Directory containing the JSON file
            image_loader: ImageLoader instance for loading images
            
        Returns:
            RGB numpy array
        """
        if 'imageData' in labelme_data and labelme_data['imageData']:
            # Decode base64 image
            img_data = base64.b64decode(labelme_data['imageData'])
            pil_img = Image.open(BytesIO(img_data))
            image = np.array(pil_img)
            image = image_loader.normalize_format(image)
        else:
            # Load from imagePath
            image_path = os.path.join(json_dir, labelme_data['imagePath'])
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            image = image_loader.load(image_path)

        return image


class LabelMeWriter:
    """Write LabelMe JSON files."""

    def __init__(self, enable_base64: bool = False, image_config: Dict = None) -> None:
        """Initialize LabelMe writer.
        
        Args:
            enable_base64: Whether to encode images as base64 in JSON
            image_config: Image processing configuration
        """
        self.enable_base64 = enable_base64
        self.image_config = image_config or {}

    def create_json(
        self, image: np.ndarray, shapes: List[Dict], image_filename: str
    ) -> Dict:
        """Create LabelMe JSON structure with optional base64 encoding.
        
        Args:
            image: RGB image array (H, W, 3)
            shapes: List of shape dictionaries
            image_filename: Name of the image file
            
        Returns:
            Dictionary in LabelMe JSON format
        """
        # Conditionally encode image to base64
        img_base64 = None
        if self.enable_base64:
            pil_img = Image.fromarray(image)
            buffered = BytesIO()

            # Get output format from config
            output_format = self.image_config.get('output_format', 'png').upper()
            quality = self.image_config.get('output_quality', 95)

            if output_format == 'JPG':
                output_format = 'JPEG'

            save_kwargs = {}
            if output_format == 'JPEG':
                save_kwargs['quality'] = quality

            pil_img.save(buffered, format=output_format, **save_kwargs)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Create LabelMe JSON structure
        labelme_json = {
            "version": "5.0.1",
            "flags": {},
            "shapes": shapes,
            "imagePath": image_filename,
            "imageData": img_base64,
            "imageHeight": image.shape[0],
            "imageWidth": image.shape[1],
        }

        return labelme_json

    def save(self, labelme_data: Dict, output_path: str) -> None:
        """Save LabelMe JSON to file.
        
        Args:
            labelme_data: LabelMe JSON data
            output_path: Output file path
        """
        with open(output_path, 'w') as f:
            json.dump(labelme_data, f, indent=2)
