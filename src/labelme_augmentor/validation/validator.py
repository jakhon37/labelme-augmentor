"""Validation utilities for images and masks."""

import logging
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from ..utils.exceptions import ValidationError


class MaskValidator:
    """Validate images and augmentation results."""

    def __init__(self, config: Dict, idx_to_class: Optional[Dict[int, str]] = None) -> None:
        """Initialize validator with configuration.
        
        Args:
            config: Validation configuration dictionary
            idx_to_class: Optional mapping from class index to class name
        """
        self.config = config.get('validation', {})
        self.min_defect_area = self.config.get('min_defect_area', 20)
        self.max_defect_area = self.config.get('max_defect_area')
        self.min_defect_length = self.config.get('min_defect_length')
        self.max_defect_length = self.config.get('max_defect_length')
        self.min_contour_points = self.config.get('min_contour_points', 3)
        self.check_preservation = self.config.get('check_defect_preservation', True)
        self.max_area_change = self.config.get('max_area_change_ratio', 0.5)
        self.reject_border = self.config.get('reject_border_defects', False)
        self.border_margin = self.config.get('border_margin', 5)
        self.idx_to_class = idx_to_class or {}

        # Per-class validation overrides
        class_specific = config.get('class_specific', {}) or {}
        self.class_validation_params: Dict[str, Dict] = {}
        
        for class_name, class_cfg in class_specific.items():
            class_params = {}
            
            # Extract validation parameters from class config
            if isinstance(class_cfg, dict):
                if 'min_defect_area' in class_cfg:
                    class_params['min_defect_area'] = class_cfg['min_defect_area']
                if 'max_defect_area' in class_cfg:
                    class_params['max_defect_area'] = class_cfg['max_defect_area']
                if 'min_defect_length' in class_cfg:
                    class_params['min_defect_length'] = class_cfg['min_defect_length']
                if 'max_defect_length' in class_cfg:
                    class_params['max_defect_length'] = class_cfg['max_defect_length']
                if 'min_contour_points' in class_cfg:
                    class_params['min_contour_points'] = class_cfg['min_contour_points']
                if 'check_defect_preservation' in class_cfg:
                    class_params['check_preservation'] = class_cfg['check_defect_preservation']
                if 'max_area_change_ratio' in class_cfg:
                    class_params['max_area_change'] = class_cfg['max_area_change_ratio']
                if 'reject_border_defects' in class_cfg:
                    class_params['reject_border'] = class_cfg['reject_border_defects']
                if 'border_margin' in class_cfg:
                    class_params['border_margin'] = class_cfg['border_margin']
            else:
                # Pydantic model
                if getattr(class_cfg, 'min_defect_area', None) is not None:
                    class_params['min_defect_area'] = class_cfg.min_defect_area
                if getattr(class_cfg, 'max_defect_area', None) is not None:
                    class_params['max_defect_area'] = class_cfg.max_defect_area
                if getattr(class_cfg, 'min_contour_points', None) is not None:
                    class_params['min_contour_points'] = class_cfg.min_contour_points
                if getattr(class_cfg, 'check_defect_preservation', None) is not None:
                    class_params['check_preservation'] = class_cfg.check_defect_preservation
                if getattr(class_cfg, 'max_area_change_ratio', None) is not None:
                    class_params['max_area_change'] = class_cfg.max_area_change_ratio
                if getattr(class_cfg, 'reject_border_defects', None) is not None:
                    class_params['reject_border'] = class_cfg.reject_border_defects
                if getattr(class_cfg, 'border_margin', None) is not None:
                    class_params['border_margin'] = class_cfg.border_margin
            
            if class_params:
                self.class_validation_params[class_name] = class_params
    
    def _get_class_param(self, class_idx: int, param_name: str, default_value):
        """Get validation parameter with class-specific override support.
        
        Args:
            class_idx: Class index
            param_name: Parameter name
            default_value: Default value from global config
            
        Returns:
            Parameter value (class-specific if available, else global default)
        """
        if self.idx_to_class and class_idx in self.idx_to_class:
            class_name = self.idx_to_class[class_idx]
            if class_name in self.class_validation_params:
                return self.class_validation_params[class_name].get(param_name, default_value)
        return default_value

    def validate_mask(
        self, mask: np.ndarray, original_mask: Optional[np.ndarray] = None
    ) -> bool:
        """Validate augmented mask.
        
        Args:
            mask: Augmented mask to validate
            original_mask: Original mask for comparison (optional)
            
        Returns:
            True if mask is valid, False otherwise
        """
        if not self.config.get('enabled', True):
            return True

        # Check if mask has defects
        if np.max(mask) == 0:
            logging.warning("Mask has no defects after augmentation")
            return False

        # Validate each class
        for class_idx in np.unique(mask):
            if class_idx == 0:
                continue

            binary_mask = (mask == class_idx).astype(np.uint8) * 255
            contours, _ = cv2.findContours(
                binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                area = cv2.contourArea(contour)

                # Get class-specific parameters
                min_area = self._get_class_param(class_idx, 'min_defect_area', self.min_defect_area)
                max_area = self._get_class_param(class_idx, 'max_defect_area', self.max_defect_area)
                min_length = self._get_class_param(class_idx, 'min_defect_length', self.min_defect_length)
                max_length = self._get_class_param(class_idx, 'max_defect_length', self.max_defect_length)
                min_points = self._get_class_param(class_idx, 'min_contour_points', self.min_contour_points)
                reject_border = self._get_class_param(class_idx, 'reject_border', self.reject_border)
                border_margin = self._get_class_param(class_idx, 'border_margin', self.border_margin)

                # Check minimum area
                if area < min_area:
                    logging.debug(f"Defect area {area} below minimum {min_area}")
                    return False

                # Check maximum area
                if max_area and area > max_area:
                    logging.debug(f"Defect area {area} above maximum {max_area}")
                    return False
                
                # Check defect length
                if min_length is not None or max_length is not None:
                    length = self._calculate_defect_length(contour)
                    
                    if min_length is not None and length < min_length:
                        logging.debug(f"Defect length {length:.1f} below minimum {min_length}")
                        return False
                    
                    if max_length is not None and length > max_length:
                        logging.debug(f"Defect length {length:.1f} above maximum {max_length}")
                        return False

                # Check contour points
                if len(contour) < min_points:
                    logging.debug(
                        f"Contour has {len(contour)} points, minimum is {min_points}"
                    )
                    return False

                # Check if defect touches border
                if reject_border:
                    if self._touches_border(contour, mask.shape, border_margin):
                        logging.debug("Defect touches image border")
                        return False

        # Check preservation if original mask provided
        if self.check_preservation and original_mask is not None:
            if not self._check_preservation(mask, original_mask):
                return False

        return True

    def _touches_border(
        self, contour: np.ndarray, shape: Tuple[int, int], margin: int
    ) -> bool:
        """Check if contour touches image border.
        
        Args:
            contour: Contour to check
            shape: Image shape (height, width)
            margin: Border margin in pixels
            
        Returns:
            True if contour touches border, False otherwise
        """
        x, y, w, h = cv2.boundingRect(contour)
        height, width = shape
        return (
            x <= margin
            or y <= margin
            or x + w >= width - margin
            or y + h >= height - margin
        )
    
    def _calculate_defect_length(self, contour: np.ndarray) -> float:
        """Calculate the major axis length of a defect contour.
        
        Uses rotated bounding box to find the longest dimension,
        which works correctly for defects at any angle.
        
        Args:
            contour: Defect contour
            
        Returns:
            Major axis length (longer dimension of rotated bounding box)
        """
        # Need at least 5 points to fit a rotated rectangle
        if len(contour) < 5:
            # For very small contours, use simple bounding box
            x, y, w, h = cv2.boundingRect(contour)
            return max(w, h)
        
        try:
            # Get minimum area rotated rectangle
            # Returns: ((center_x, center_y), (width, height), angle)
            rect = cv2.minAreaRect(contour)
            width, height = rect[1]
            
            # Return the longer dimension as the "length"
            return max(width, height)
        except:
            # Fallback to axis-aligned bounding box
            x, y, w, h = cv2.boundingRect(contour)
            return max(w, h)

    def _check_preservation(self, aug_mask: np.ndarray, orig_mask: np.ndarray) -> bool:
        """Check if augmentation preserved defect reasonably.
        
        Compares defect area as percentage of total image size to handle
        cases where augmentation changes image dimensions (e.g., resize, crop).
        
        Args:
            aug_mask: Augmented mask
            orig_mask: Original mask
            
        Returns:
            True if defects are preserved, False otherwise
        """
        # Calculate total image areas
        orig_img_area = orig_mask.shape[0] * orig_mask.shape[1]
        aug_img_area = aug_mask.shape[0] * aug_mask.shape[1]
        
        for class_idx in np.unique(orig_mask):
            if class_idx == 0:
                continue
            
            # Check if preservation check is enabled for this class
            check_preservation = self._get_class_param(
                class_idx, 'check_preservation', self.check_preservation
            )
            
            if not check_preservation:
                continue

            # Count defect pixels
            orig_defect_pixels = np.sum(orig_mask == class_idx)
            aug_defect_pixels = np.sum(aug_mask == class_idx)

            if orig_defect_pixels == 0:
                continue

            # Calculate relative areas (as percentage of image)
            orig_relative_area = orig_defect_pixels / orig_img_area
            aug_relative_area = aug_defect_pixels / aug_img_area
            
            # Compare relative areas, not absolute pixel counts
            area_change_ratio = abs(aug_relative_area - orig_relative_area) / orig_relative_area

            # Use per-class max area change
            max_area_allowed = self._get_class_param(
                class_idx, 'max_area_change', self.max_area_change
            )

            if area_change_ratio > max_area_allowed:
                logging.debug(
                    f"Relative area changed by {area_change_ratio:.2%} "
                    f"(orig: {orig_relative_area:.4%}, aug: {aug_relative_area:.4%}), "
                    f"max allowed is {max_area_allowed:.2%}"
                )
                return False

        return True
