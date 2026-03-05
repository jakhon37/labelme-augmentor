"""Mask conversion utilities between LabelMe and numpy formats."""

from typing import Dict, List

import cv2
import numpy as np


class MaskConverter:
    """Convert between LabelMe shapes and numpy masks."""

    def __init__(self, class_map: Dict[str, int], idx_to_class: Dict[int, str]) -> None:
        """Initialize mask converter.
        
        Args:
            class_map: Mapping from class name to index
            idx_to_class: Mapping from index to class name
        """
        self.class_map = class_map
        self.idx_to_class = idx_to_class

    def labelme_to_mask(self, labelme_data: Dict, image: np.ndarray = None) -> np.ndarray:
        """Convert LabelMe JSON shapes to multi-class mask.
        
        Args:
            labelme_data: LabelMe JSON data dictionary
            image: Optional image array to match dimensions (H, W, C)
            
        Returns:
            Multi-class mask array of shape (H, W) with class indices
        """
        # Use actual image dimensions if provided, otherwise use JSON dimensions
        if image is not None:
            height, width = image.shape[:2]
        else:
            height = int(np.round(labelme_data['imageHeight']))
            width = int(np.round(labelme_data['imageWidth']))

        # Initialize mask with zeros (background)
        mask = np.zeros((height, width), dtype=np.uint8)

        # Draw each shape on the mask
        for shape in labelme_data['shapes']:
            label = shape['label']
            points = shape['points']
            shape_type = shape['shape_type']

            if label not in self.class_map:
                print(f"Warning: Unknown class '{label}', skipping...")
                continue

            class_idx = self.class_map[label]

            # Convert points to numpy array
            points_array = np.array(points, dtype=np.int32)

            if shape_type == 'polygon':
                # Fill polygon
                cv2.fillPoly(mask, [points_array], int(class_idx))
            elif shape_type == 'rectangle':
                # Draw rectangle
                x1, y1 = points_array[0]
                x2, y2 = points_array[1]
                cv2.rectangle(mask, (int(x1), int(y1)), (int(x2), int(y2)), int(class_idx), -1)
            elif shape_type == 'circle':
                # Draw circle
                center = tuple(points_array[0].astype(int))
                edge = tuple(points_array[1].astype(int))
                radius = int(np.linalg.norm(points_array[1] - points_array[0]))
                cv2.circle(mask, center, radius, int(class_idx), -1)
            elif shape_type == 'line' or shape_type == 'linestrip':
                # Draw line
                cv2.polylines(mask, [points_array], False, int(class_idx), thickness=2)
            elif shape_type == 'point':
                # Draw point
                cv2.circle(mask, tuple(points_array[0].astype(int)), 3, int(class_idx), -1)

        return mask

    def mask_to_labelme_shapes(self, mask: np.ndarray) -> List[Dict]:
        """Convert multi-class mask back to LabelMe shapes.
        
        Args:
            mask: Multi-class mask array of shape (H, W) with class indices
            
        Returns:
            List of shape dictionaries for LabelMe JSON
        """
        shapes = []

        # Process each class
        for class_idx in np.unique(mask):
            if class_idx == 0:  # Skip background
                continue

            class_name = self.idx_to_class.get(class_idx, f"class_{class_idx}")

            # Create binary mask for this class
            binary_mask = (mask == class_idx).astype(np.uint8) * 255

            # Find contours
            contours, _ = cv2.findContours(
                binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Convert each contour to a shape
            for contour in contours:
                if len(contour) < 3:  # Skip tiny contours
                    continue

                # Convert contour to points list
                points = []
                for point in contour:
                    x, y = point[0]
                    points.append([float(x), float(y)])

                # Create shape dict
                shape = {
                    "label": class_name,
                    "points": points,
                    "group_id": None,
                    "shape_type": "polygon",
                    "flags": {},
                }
                shapes.append(shape)

        return shapes
