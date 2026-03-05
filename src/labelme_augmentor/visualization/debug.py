"""Debug visualization utilities."""

from typing import Dict

import cv2
import numpy as np

from .colors import ConfigurableColorPalette


class DebugVisualizer:
    """Create debug visualizations for augmented images."""

    def __init__(
        self,
        idx_to_class: Dict[int, str],
        custom_colors: Dict[str, list],
        default_colors: list,
    ) -> None:
        """Initialize debug visualizer.
        
        Args:
            idx_to_class: Mapping from class index to name
            custom_colors: Custom color mapping
            default_colors: Default color palette
        """
        self.idx_to_class = idx_to_class
        self.custom_colors = custom_colors
        self.default_colors = default_colors

    def create_overlay(
        self, original_image: np.ndarray, augmented_image: np.ndarray, augmented_mask: np.ndarray
    ) -> np.ndarray:
        """Create debug visualization with color-coded mask overlay.
        
        Args:
            original_image: Original RGB image
            augmented_image: Augmented RGB image
            augmented_mask: Augmented multi-class mask
            
        Returns:
            Side-by-side comparison image
        """
        # Create colored mask
        colored_mask = np.zeros_like(augmented_image)

        for class_idx in np.unique(augmented_mask):
            if class_idx == 0:
                continue
            class_name = self.idx_to_class.get(class_idx)
            color = ConfigurableColorPalette.get_color(
                class_idx, self.custom_colors, self.default_colors, class_name
            )
            colored_mask[augmented_mask == class_idx] = color

        # Blend image with mask
        overlay = cv2.addWeighted(augmented_image, 0.7, colored_mask, 0.3, 0)

        # Stack original and augmented
        orig_resized = cv2.resize(
            original_image, (augmented_image.shape[1], augmented_image.shape[0])
        )
        stacked = np.hstack([orig_resized, overlay])

        return stacked
