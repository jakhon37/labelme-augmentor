"""Sample data fixtures for testing."""

import numpy as np


def create_sample_defect_mask(height: int = 100, width: int = 100) -> np.ndarray:
    """Create a sample defect mask with various shapes.
    
    Args:
        height: Mask height
        width: Mask width
        
    Returns:
        Multi-class mask
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Add various defect shapes
    # Rectangular defect (class 1)
    mask[10:30, 10:40] = 1
    
    # Square defect (class 2)
    mask[50:70, 50:70] = 2
    
    # Circular defect (class 3)
    y, x = np.ogrid[:height, :width]
    circle_mask = (x - 80) ** 2 + (y - 20) ** 2 <= 10 ** 2
    mask[circle_mask] = 3
    
    return mask


def create_sample_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
    """Create a sample RGB image.
    
    Args:
        height: Image height
        width: Image width
        seed: Random seed
        
    Returns:
        RGB image array
    """
    np.random.seed(seed)
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)


def create_labelme_shape(label: str, points: list, shape_type: str = "polygon") -> dict:
    """Create a LabelMe shape dictionary.
    
    Args:
        label: Class label
        points: List of [x, y] coordinates
        shape_type: Shape type (polygon, rectangle, etc.)
        
    Returns:
        LabelMe shape dictionary
    """
    return {
        "label": label,
        "points": points,
        "group_id": None,
        "shape_type": shape_type,
        "flags": {}
    }
