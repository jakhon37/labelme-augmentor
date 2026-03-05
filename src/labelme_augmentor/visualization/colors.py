"""Color palette management for visualization."""

import colorsys
from typing import Dict, List


class ConfigurableColorPalette:
    """Generate unlimited colors for visualization."""

    @staticmethod
    def generate_colors(n_colors: int) -> List[List[int]]:
        """Generate n distinct colors using HSV color space.
        
        Args:
            n_colors: Number of colors to generate
            
        Returns:
            List of RGB color triplets
        """
        colors = []
        for i in range(n_colors):
            hue = i / n_colors
            saturation = 0.9
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append([int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)])
        return colors

    @staticmethod
    def get_color(
        class_idx: int,
        custom_colors: Dict[str, List[int]],
        default_colors: List[List[int]],
        class_name: str = None,
    ) -> List[int]:
        """Get color for a class with custom override support.
        
        Args:
            class_idx: Index of the class
            custom_colors: Custom color mapping by class name
            default_colors: Default color palette
            class_name: Name of the class (optional)
            
        Returns:
            RGB color triplet
        """
        if class_name and class_name in custom_colors:
            return custom_colors[class_name]
        if class_idx - 1 < len(default_colors):
            return default_colors[class_idx - 1]
        # Generate on-the-fly for classes beyond default palette
        return ConfigurableColorPalette.generate_colors(class_idx)[-1]
