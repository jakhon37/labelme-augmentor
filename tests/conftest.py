"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Dict, Generator

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image() -> np.ndarray:
    """Create a sample RGB image."""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_mask() -> np.ndarray:
    """Create a sample mask with multiple classes."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Add some defects
    mask[20:40, 20:40] = 1  # Class 1
    mask[60:80, 60:80] = 2  # Class 2
    return mask


@pytest.fixture
def sample_labelme_json(temp_dir: Path, sample_image: np.ndarray) -> Dict:
    """Create a sample LabelMe JSON structure."""
    return {
        "version": "5.0.1",
        "flags": {},
        "shapes": [
            {
                "label": "defect1",
                "points": [[20, 20], [40, 20], [40, 40], [20, 40]],
                "group_id": None,
                "shape_type": "polygon",
                "flags": {}
            },
            {
                "label": "defect2",
                "points": [[60, 60], [80, 60], [80, 80], [60, 80]],
                "group_id": None,
                "shape_type": "polygon",
                "flags": {}
            }
        ],
        "imagePath": "test_image.jpg",
        "imageData": None,
        "imageHeight": 100,
        "imageWidth": 100
    }


@pytest.fixture
def sample_config(temp_dir: Path) -> Dict:
    """Create a sample configuration dictionary."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    return {
        "general": {
            "seed": 42,
            "num_workers": 1,
            "log_level": "INFO"
        },
        "paths": {
            "input_json_dir": str(input_dir),
            "output_dir": str(output_dir)
        },
        "output": {
            "images_subdir": "images",
            "annotations_subdir": "annotations",
            "debug_subdir": "debug",
            "create_debug_visualizations": True
        },
        "global_augmentations": {
            "num_augmentations_per_image": 2,
            "transforms": [
                {"name": "HorizontalFlip", "probability": 0.5},
                {"name": "VerticalFlip", "probability": 0.5}
            ]
        },
        "class_specific": {},
        "validation": {
            "enabled": True,
            "min_defect_area": 10,
            "max_defect_area": None,
            "min_contour_points": 3
        },
        "visualization": {
            "auto_generate_colors": True,
            "custom_colors": {},
            "default_colors": [[255, 0, 0], [0, 255, 0]]
        },
        "image_processing": {
            "output_format": "png",
            "output_quality": 95
        }
    }


@pytest.fixture
def sample_dataset(temp_dir: Path, sample_image: np.ndarray, sample_labelme_json: Dict) -> Path:
    """Create a sample dataset with images and JSON files."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create 3 sample files
    for i in range(3):
        # Save image
        img_path = input_dir / f"image_{i}.jpg"
        Image.fromarray(sample_image).save(img_path)
        
        # Save JSON
        json_path = input_dir / f"image_{i}.json"
        json_data = sample_labelme_json.copy()
        json_data["imagePath"] = f"image_{i}.jpg"
        with open(json_path, 'w') as f:
            json.dump(json_data, f)
    
    return input_dir


@pytest.fixture
def class_names() -> list:
    """Sample class names."""
    return ["defect1", "defect2", "defect3"]
