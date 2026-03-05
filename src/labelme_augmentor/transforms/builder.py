"""Transform builder from configuration."""

import logging
from typing import Dict, List

import albumentations as A


class TransformBuilder:
    """Build albumentations transforms from configuration."""

    @staticmethod
    def build_transform(transforms_config: List[Dict]) -> A.Compose:
        """Build albumentations transform from config.
        
        Args:
            transforms_config: List of transform configurations
            
        Returns:
            Composed albumentations transform
        """
        if not transforms_config:
            return A.Compose([A.NoOp()], p=1.0, is_check_shapes=False)

        transforms = []
        for t_config in transforms_config:
            name = t_config.get('name')
            prob = t_config.get('probability', 1.0)
            params = t_config.get('params', {})

            # Get albumentations transform class
            if hasattr(A, name):
                transform_class = getattr(A, name)
                transforms.append(transform_class(p=prob, **params))
            else:
                logging.warning(f"Unknown transform: {name}")

        return A.Compose(transforms, p=1.0, is_check_shapes=False)

    @staticmethod
    def build_class_transforms(
        class_names: List[str],
        global_config: Dict,
        class_specific_config: Dict,
    ) -> tuple[Dict[str, A.Compose], Dict[str, int]]:
        """Build per-class transforms and augmentation counts.
        
        Args:
            class_names: List of class names
            global_config: Global augmentation configuration
            class_specific_config: Class-specific augmentation configuration
            
        Returns:
            Tuple of (class_transforms, class_aug_counts)
        """
        global_transform = TransformBuilder.build_transform(
            global_config.get('transforms', [])
        )
        num_augmentations = global_config.get('num_augmentations_per_image', 5)

        class_transforms = {}
        class_aug_counts = {}

        for class_name in class_names:
            if class_name in class_specific_config:
                class_config = class_specific_config[class_name]
                class_transforms[class_name] = TransformBuilder.build_transform(
                    class_config.get('transforms', global_config.get('transforms', []))
                )
                class_aug_counts[class_name] = class_config.get(
                    'num_augmentations_per_image', num_augmentations
                )
            else:
                class_transforms[class_name] = global_transform
                class_aug_counts[class_name] = num_augmentations

        return class_transforms, class_aug_counts
