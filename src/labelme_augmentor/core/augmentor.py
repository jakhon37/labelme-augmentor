"""Core augmentation logic for single images."""

import logging
import os
from typing import Dict, List, Optional, Set

import albumentations as A
import numpy as np

from ..io import ImageSaver, LabelMeReader, LabelMeWriter, MaskConverter
from ..transforms import TransformBuilder
from ..validation import MaskValidator
from ..visualization import ConfigurableColorPalette, DebugVisualizer


class Augmentor:
    """
    LabelMe augmentation handler with configurable augmentation.
    Supports per-class settings, validation, and flexible output options.
    """

    def __init__(self, class_names: List[str], config: Dict) -> None:
        """Initialize the augmentor with configuration.
        
        Args:
            class_names: List of class names (background excluded)
            config: Configuration dictionary
        """
        self.class_names = class_names
        self.config = config

        # Create class mapping (0 = background)
        self.class_map = {name: idx + 1 for idx, name in enumerate(class_names)}
        self.idx_to_class = {idx: name for name, idx in self.class_map.items()}

        # Setup color palette
        self._setup_colors()

        # Setup components
        self.validator = MaskValidator(config, self.idx_to_class)
        self.mask_converter = MaskConverter(self.class_map, self.idx_to_class)
        self.image_saver = ImageSaver(config)
        self.labelme_reader = LabelMeReader()

        # Global augmentation settings
        global_config = config.get('global_augmentations', {})
        self.num_augmentations = global_config.get('num_augmentations_per_image', 5)

        # Build transforms
        self.global_transform = TransformBuilder.build_transform(
            global_config.get('transforms', [])
        )

        # Build per-class transforms
        class_specific = config.get('class_specific', {})
        self.class_transforms, self.class_aug_counts = TransformBuilder.build_class_transforms(
            class_names, global_config, class_specific
        )

        # Base64 option
        self.enable_base64 = config.get('general', {}).get('enable_base64', False)

        # Image processing config
        self.image_config = config.get('image_processing', {})

        # LabelMe writer
        self.labelme_writer = LabelMeWriter(self.enable_base64, self.image_config)

        # Debug visualizer
        self.debug_visualizer = DebugVisualizer(
            self.idx_to_class, self.custom_colors, self.default_colors
        )

    def _setup_colors(self) -> None:
        """Setup color palette from config."""
        viz_config = self.config.get('visualization', {})
        self.auto_generate_colors = viz_config.get('auto_generate_colors', True)
        self.custom_colors = viz_config.get('custom_colors', {})
        self.default_colors = viz_config.get(
            'default_colors',
            [
                [255, 0, 0],
                [0, 255, 0],
                [0, 0, 255],
                [255, 255, 0],
                [255, 0, 255],
                [0, 255, 255],
                [128, 0, 0],
                [0, 128, 0],
                [0, 0, 128],
                [128, 128, 0],
            ],
        )

        if self.auto_generate_colors and len(self.class_names) > len(self.default_colors):
            self.default_colors = ConfigurableColorPalette.generate_colors(len(self.class_names))

    def process_file(
        self,
        json_path: str,
        output_images_dir: str,
        output_json_dir: str,
        debug_dir: Optional[str],
        create_debug: bool = True,
    ) -> int:
        """Process a single LabelMe JSON file with per-class augmentation support.
        
        Args:
            json_path: Path to input LabelMe JSON file
            output_images_dir: Directory to save augmented images
            output_json_dir: Directory to save augmented JSON files
            debug_dir: Directory to save debug visualizations
            create_debug: Whether to create debug visualizations
            
        Returns:
            Number of augmentations saved
        """
        case_id = os.path.splitext(os.path.basename(json_path))[0]
        json_dir = os.path.dirname(json_path)

        # Load LabelMe JSON
        labelme_data = self.labelme_reader.load_json(json_path)

        # Load image
        try:
            from ..io import ImageLoader
            image_loader = ImageLoader(self.config)
            image = self.labelme_reader.load_image_from_json(labelme_data, json_dir, image_loader)
        except Exception as e:
            logging.error(f"Error loading image for {case_id}: {e}")
            return 0

        # Convert LabelMe shapes to mask (pass image to ensure matching dimensions)
        mask = self.mask_converter.labelme_to_mask(labelme_data, image)

        # Determine which classes are present
        present_classes: Set[str] = set()
        for shape in labelme_data['shapes']:
            present_classes.add(shape['label'])

        # Determine max augmentations needed for any present class
        max_aug_count = self.num_augmentations
        for class_name in present_classes:
            if class_name in self.class_aug_counts:
                max_aug_count = max(max_aug_count, self.class_aug_counts[class_name])

        # Get output format
        output_format = self.image_config.get('output_format', 'png')

        # Save original
        orig_img_filename = f"{case_id}_org.{output_format}"
        orig_json_filename = f"{case_id}_org.json"

        self.image_saver.save(image, os.path.join(output_images_dir, orig_img_filename))

        orig_shapes = labelme_data['shapes']
        orig_labelme = self.labelme_writer.create_json(image, orig_shapes, orig_img_filename)
        self.labelme_writer.save(orig_labelme, os.path.join(output_json_dir, orig_json_filename))

        # Generate augmentations
        num_saved = 1  # Count original
        num_valid = 0
        aug_idx = 0

        # Try to generate valid augmentations
        max_attempts = max_aug_count * 3  # Allow some failed attempts
        attempts = 0

        while num_valid < max_aug_count and attempts < max_attempts:
            attempts += 1

            # Select transform based on present classes
            # Use the most specific transform if multiple classes present
            transform = self.global_transform
            for class_name in present_classes:
                if class_name in self.class_transforms:
                    transform = self.class_transforms[class_name]
                    break  # Use first matching class-specific transform

            # Apply transform
            try:
                augmented = transform(image=image, mask=mask)
                aug_image = augmented['image']
                aug_mask = augmented['mask']
            except Exception as e:
                logging.debug(f"Augmentation failed for {case_id}: {e}")
                continue

            # Validate augmented mask
            if not self.validator.validate_mask(aug_mask, mask):
                logging.debug(f"Validation failed for {case_id} augmentation {aug_idx}")
                continue

            # Convert mask back to shapes
            aug_shapes = self.mask_converter.mask_to_labelme_shapes(aug_mask)

            if not aug_shapes:
                logging.debug(f"No shapes after augmentation for {case_id}")
                continue

            # Save augmented files
            aug_img_filename = f"{case_id}_aug_{aug_idx:03d}.{output_format}"
            aug_json_filename = f"{case_id}_aug_{aug_idx:03d}.json"

            self.image_saver.save(aug_image, os.path.join(output_images_dir, aug_img_filename))

            aug_labelme = self.labelme_writer.create_json(aug_image, aug_shapes, aug_img_filename)
            self.labelme_writer.save(
                aug_labelme, os.path.join(output_json_dir, aug_json_filename)
            )

            # Create debug visualization if enabled
            if create_debug and debug_dir:
                debug_viz = self.debug_visualizer.create_overlay(image, aug_image, aug_mask)
                debug_viz_path = os.path.join(
                    debug_dir, f"{case_id}_aug_{aug_idx:03d}_overlay.png"
                )
                import cv2
                cv2.imwrite(debug_viz_path, cv2.cvtColor(debug_viz, cv2.COLOR_RGB2BGR))

            num_saved += 1
            num_valid += 1
            aug_idx += 1

        if num_valid < max_aug_count:
            logging.warning(
                f"{case_id}: Only generated {num_valid}/{max_aug_count} valid augmentations"
            )

        return num_saved
