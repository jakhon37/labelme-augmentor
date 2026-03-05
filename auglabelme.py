import os
import numpy as np
import albumentations as A
from glob import glob
import cv2
from PIL import Image
from tqdm import tqdm
import json
import base64
from io import BytesIO
import yaml
import hashlib
from multiprocessing import Pool, cpu_count
from functools import partial
import logging
from typing import Dict, List, Optional, Tuple, Any
import colorsys


class ConfigurableColorPalette:
    """Generate unlimited colors for visualization."""
    
    @staticmethod
    def generate_colors(n_colors: int) -> List[List[int]]:
        """Generate n distinct colors using HSV color space."""
        colors = []
        for i in range(n_colors):
            hue = i / n_colors
            saturation = 0.9
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append([int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)])
        return colors
    
    @staticmethod
    def get_color(class_idx: int, custom_colors: Dict[str, List[int]], 
                  default_colors: List[List[int]], class_name: str = None) -> List[int]:
        """Get color for a class with custom override support."""
        if class_name and class_name in custom_colors:
            return custom_colors[class_name]
        if class_idx - 1 < len(default_colors):
            return default_colors[class_idx - 1]
        # Generate on-the-fly for classes beyond default palette
        return ConfigurableColorPalette.generate_colors(class_idx)[-1]


class ImageValidator:
    """Validate images and augmentation results."""
    
    def __init__(self, config: Dict):
        self.config = config.get('validation', {})
        self.min_defect_area = self.config.get('min_defect_area', 20)
        self.max_defect_area = self.config.get('max_defect_area')
        self.min_contour_points = self.config.get('min_contour_points', 3)
        self.check_preservation = self.config.get('check_defect_preservation', True)
        self.max_area_change = self.config.get('max_area_change_ratio', 0.5)
        self.reject_border = self.config.get('reject_border_defects', False)
        self.border_margin = self.config.get('border_margin', 5)
    
    def validate_mask(self, mask: np.ndarray, original_mask: np.ndarray = None) -> bool:
        """Validate augmented mask."""
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
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Check minimum area
                if area < self.min_defect_area:
                    logging.debug(f"Defect area {area} below minimum {self.min_defect_area}")
                    return False
                
                # Check maximum area
                if self.max_defect_area and area > self.max_defect_area:
                    logging.debug(f"Defect area {area} above maximum {self.max_defect_area}")
                    return False
                
                # Check contour points
                if len(contour) < self.min_contour_points:
                    logging.debug(f"Contour has {len(contour)} points, minimum is {self.min_contour_points}")
                    return False
                
                # Check if defect touches border
                if self.reject_border:
                    if self._touches_border(contour, mask.shape, self.border_margin):
                        logging.debug("Defect touches image border")
                        return False
        
        # Check preservation if original mask provided
        if self.check_preservation and original_mask is not None:
            if not self._check_preservation(mask, original_mask):
                return False
        
        return True
    
    def _touches_border(self, contour: np.ndarray, shape: Tuple[int, int], margin: int) -> bool:
        """Check if contour touches image border."""
        x, y, w, h = cv2.boundingRect(contour)
        height, width = shape
        return (x <= margin or y <= margin or 
                x + w >= width - margin or y + h >= height - margin)
    
    def _check_preservation(self, aug_mask: np.ndarray, orig_mask: np.ndarray) -> bool:
        """Check if augmentation preserved defect reasonably."""
        for class_idx in np.unique(orig_mask):
            if class_idx == 0:
                continue
            
            orig_area = np.sum(orig_mask == class_idx)
            aug_area = np.sum(aug_mask == class_idx)
            
            if orig_area == 0:
                continue
            
            area_change_ratio = abs(aug_area - orig_area) / orig_area
            if area_change_ratio > self.max_area_change:
                logging.debug(f"Area changed by {area_change_ratio:.2%}, max allowed is {self.max_area_change:.2%}")
                return False
        
        return True


class CheckpointManager:
    """Manage checkpoint for resume functionality."""
    
    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self.processed_files = set()
        self.load_checkpoint()
    
    def load_checkpoint(self):
        """Load checkpoint if exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                logging.info(f"Loaded checkpoint: {len(self.processed_files)} files already processed")
            except Exception as e:
                logging.warning(f"Failed to load checkpoint: {e}")
                self.processed_files = set()
    
    def save_checkpoint(self):
        """Save current checkpoint."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({'processed_files': list(self.processed_files)}, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")
    
    def mark_processed(self, file_path: str):
        """Mark file as processed."""
        self.processed_files.add(file_path)
    
    def is_processed(self, file_path: str) -> bool:
        """Check if file was already processed."""
        return file_path in self.processed_files
    
    def clear(self):
        """Clear checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        self.processed_files = set()


class LabelMeAugmentor:
    """
    LabelMe JSON augmentation handler with configurable augmentation.
    Supports per-class settings, validation, and flexible output options.
    """
    
    def __init__(self, class_names: List[str], config: Dict):
        """
        Initialize the augmentor with configuration.
        
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
        
        # Setup validator
        self.validator = ImageValidator(config)
        
        # Global augmentation settings
        global_config = config.get('global_augmentations', {})
        self.num_augmentations = global_config.get('num_augmentations_per_image', 5)
        
        # Build global transform
        self.global_transform = self._build_transform(global_config.get('transforms', []))
        
        # Build per-class transforms
        self.class_transforms = {}
        self.class_aug_counts = {}
        class_specific = config.get('class_specific', {})
        for class_name in class_names:
            if class_name in class_specific:
                class_config = class_specific[class_name]
                self.class_transforms[class_name] = self._build_transform(
                    class_config.get('transforms', global_config.get('transforms', []))
                )
                self.class_aug_counts[class_name] = class_config.get(
                    'num_augmentations_per_image', 
                    self.num_augmentations
                )
            else:
                self.class_transforms[class_name] = self.global_transform
                self.class_aug_counts[class_name] = self.num_augmentations
        
        # Base64 option
        self.enable_base64 = config.get('general', {}).get('enable_base64', False)
        
        # Image processing config
        self.image_config = config.get('image_processing', {})
    
    def _setup_colors(self):
        """Setup color palette from config."""
        viz_config = self.config.get('visualization', {})
        self.auto_generate_colors = viz_config.get('auto_generate_colors', True)
        self.custom_colors = viz_config.get('custom_colors', {})
        self.default_colors = viz_config.get('default_colors', [
            [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0],
            [255, 0, 255], [0, 255, 255], [128, 0, 0], [0, 128, 0],
            [0, 0, 128], [128, 128, 0]
        ])
        
        if self.auto_generate_colors and len(self.class_names) > len(self.default_colors):
            self.default_colors = ConfigurableColorPalette.generate_colors(len(self.class_names))
    
    def _build_transform(self, transforms_config: List[Dict]) -> A.Compose:
        """Build albumentations transform from config."""
        if not transforms_config:
            return A.Compose([A.NoOp()], p=1.0)
        
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
        
        return A.Compose(transforms, p=1.0)
    
    @staticmethod
    def load_labelme_json(json_path):
        """Load and parse LabelMe JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    
    def labelme_to_mask(self, labelme_data):
        """
        Convert LabelMe JSON shapes to multi-class mask.
        
        Args:
            labelme_data: LabelMe JSON data dictionary
        
        Returns:
            mask: np.array of shape (H, W) with class indices
        """
        height = labelme_data['imageHeight']
        width = labelme_data['imageWidth']
        
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
                cv2.fillPoly(mask, [points_array], class_idx)
            elif shape_type == 'rectangle':
                # Draw rectangle
                x1, y1 = points_array[0]
                x2, y2 = points_array[1]
                cv2.rectangle(mask, (x1, y1), (x2, y2), class_idx, -1)
            elif shape_type == 'circle':
                # Draw circle
                center = tuple(points_array[0].astype(int))
                edge = tuple(points_array[1].astype(int))
                radius = int(np.linalg.norm(points_array[1] - points_array[0]))
                cv2.circle(mask, center, radius, class_idx, -1)
            elif shape_type == 'line' or shape_type == 'linestrip':
                # Draw line
                cv2.polylines(mask, [points_array], False, class_idx, thickness=2)
            elif shape_type == 'point':
                # Draw point
                cv2.circle(mask, tuple(points_array[0].astype(int)), 3, class_idx, -1)
        
        return mask
    
    def mask_to_labelme_shapes(self, mask):
        """
        Convert multi-class mask back to LabelMe shapes.
        
        Args:
            mask: np.array of shape (H, W) with class indices
        
        Returns:
            shapes: List of shape dictionaries for LabelMe JSON
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
                binary_mask, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
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
                    "flags": {}
                }
                shapes.append(shape)
        
        return shapes
    
    def create_labelme_json(self, image, shapes, image_filename):
        """
        Create LabelMe JSON structure with optional base64 encoding.
        
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
            "imageWidth": image.shape[1]
        }
        
        return labelme_json
    
    def load_image_from_labelme(self, labelme_data, json_dir):
        """
        Load image from LabelMe JSON with improved format handling.
        
        Args:
            labelme_data: LabelMe JSON data
            json_dir: Directory containing the JSON file
        
        Returns:
            image: RGB numpy array
        """
        if 'imageData' in labelme_data and labelme_data['imageData']:
            # Decode base64 image
            img_data = base64.b64decode(labelme_data['imageData'])
            pil_img = Image.open(BytesIO(img_data))
            image = np.array(pil_img)
        else:
            # Load from imagePath
            image_path = os.path.join(json_dir, labelme_data['imagePath'])
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Try loading with different methods
            image = self._load_image_robust(image_path)
        
        # Normalize and convert format
        image = self._normalize_image_format(image)
        
        return image
    
    def _load_image_robust(self, image_path: str) -> np.ndarray:
        """Load image with robust format handling."""
        # Try OpenCV first
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        
        if image is None:
            # Try PIL for other formats
            try:
                pil_img = Image.open(image_path)
                image = np.array(pil_img)
            except Exception as e:
                raise ValueError(f"Failed to load image {image_path}: {e}")
        else:
            # Convert BGR to RGB for OpenCV images
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        
        return image
    
    def _normalize_image_format(self, image: np.ndarray) -> np.ndarray:
        """Normalize image to RGB 8-bit format."""
        # Handle 16-bit images
        if image.dtype == np.uint16:
            if self.image_config.get('normalize_16bit', True):
                image = (image / 256).astype(np.uint8)
            else:
                image = image.astype(np.uint8)
        
        # Handle float images
        elif image.dtype in [np.float32, np.float64]:
            image = (image * 255).astype(np.uint8)
        
        # Handle different channel counts
        if len(image.shape) == 2:
            # Grayscale to RGB
            if self.image_config.get('handle_grayscale', True):
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image = np.stack([image] * 3, axis=-1)
        
        elif len(image.shape) == 3:
            if image.shape[2] == 4:
                # RGBA to RGB
                if self.image_config.get('handle_rgba', True):
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                else:
                    image = image[:, :, :3]
            elif image.shape[2] == 1:
                # Single channel to RGB
                image = np.repeat(image, 3, axis=2)
        
        # Validate image size
        if self.image_config.get('validate_loaded_images', True):
            min_size = self.image_config.get('min_image_size', [32, 32])
            max_size = self.image_config.get('max_image_size', [8192, 8192])
            h, w = image.shape[:2]
            
            if h < min_size[1] or w < min_size[0]:
                raise ValueError(f"Image too small: {w}x{h}, minimum is {min_size[0]}x{min_size[1]}")
            if h > max_size[1] or w > max_size[0]:
                logging.warning(f"Image very large: {w}x{h}, consider resizing")
        
        return image
    
    def create_debug_visualization(self, original_image, augmented_image, augmented_mask):
        """
        Create debug visualization with color-coded mask overlay.
        
        Args:
            original_image: Original RGB image
            augmented_image: Augmented RGB image
            augmented_mask: Augmented multi-class mask
        
        Returns:
            stacked: Side-by-side comparison image
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
            original_image, 
            (augmented_image.shape[1], augmented_image.shape[0])
        )
        stacked = np.hstack([orig_resized, overlay])
        
        return stacked
    
    def process_file(self, json_path, output_images_dir, output_json_dir, debug_dir, 
                     create_debug=True):
        """
        Process a single LabelMe JSON file with per-class augmentation support.
        
        Args:
            json_path: Path to input LabelMe JSON file
            output_images_dir: Directory to save augmented images
            output_json_dir: Directory to save augmented JSON files
            debug_dir: Directory to save debug visualizations
            create_debug: Whether to create debug visualizations
        
        Returns:
            num_saved: Number of augmentations saved
        """
        case_id = os.path.splitext(os.path.basename(json_path))[0]
        json_dir = os.path.dirname(json_path)
        
        # Load LabelMe JSON
        labelme_data = self.load_labelme_json(json_path)
        
        # Load image
        try:
            image = self.load_image_from_labelme(labelme_data, json_dir)
        except Exception as e:
            logging.error(f"Error loading image for {case_id}: {e}")
            return 0
        
        # Convert LabelMe shapes to mask
        mask = self.labelme_to_mask(labelme_data)
        
        # Determine which classes are present
        present_classes = set()
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
        
        self._save_image(image, os.path.join(output_images_dir, orig_img_filename))
        
        orig_shapes = labelme_data['shapes']
        orig_labelme = self.create_labelme_json(image, orig_shapes, orig_img_filename)
        with open(os.path.join(output_json_dir, orig_json_filename), 'w') as f:
            json.dump(orig_labelme, f, indent=2)
        
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
            aug_shapes = self.mask_to_labelme_shapes(aug_mask)
            
            if not aug_shapes:
                logging.debug(f"No shapes after augmentation for {case_id}")
                continue
            
            # Save augmented files
            aug_img_filename = f"{case_id}_aug_{aug_idx:03d}.{output_format}"
            aug_json_filename = f"{case_id}_aug_{aug_idx:03d}.json"
            
            self._save_image(aug_image, os.path.join(output_images_dir, aug_img_filename))
            
            aug_labelme = self.create_labelme_json(aug_image, aug_shapes, aug_img_filename)
            with open(os.path.join(output_json_dir, aug_json_filename), 'w') as f:
                json.dump(aug_labelme, f, indent=2)
            
            # Create debug visualization if enabled
            if create_debug and debug_dir:
                debug_viz = self.create_debug_visualization(image, aug_image, aug_mask)
                debug_viz_path = os.path.join(
                    debug_dir, 
                    f"{case_id}_aug_{aug_idx:03d}_overlay.png"
                )
                cv2.imwrite(debug_viz_path, cv2.cvtColor(debug_viz, cv2.COLOR_RGB2BGR))
            
            num_saved += 1
            num_valid += 1
            aug_idx += 1
        
        if num_valid < max_aug_count:
            logging.warning(f"{case_id}: Only generated {num_valid}/{max_aug_count} valid augmentations")
        
        return num_saved
    
    def _save_image(self, image: np.ndarray, path: str):
        """Save image with proper format handling."""
        output_format = self.image_config.get('output_format', 'png').lower()
        
        if output_format in ['jpg', 'jpeg']:
            quality = self.image_config.get('output_quality', 95)
            cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR), 
                       [cv2.IMWRITE_JPEG_QUALITY, quality])
        else:
            cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


class DatasetProcessor:
    """
    Main processor with multiprocessing and checkpoint support.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the dataset processor with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Setup logging
        log_level = config.get('general', {}).get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Paths
        paths = config.get('paths', {})
        self.input_json_dir = paths.get('input_json_dir')
        self.output_dir = paths.get('output_dir')
        
        if not self.input_json_dir or not self.output_dir:
            raise ValueError("input_json_dir and output_dir must be specified in config")
        
        # Output structure
        output_config = config.get('output', {})
        self.output_images_dir = os.path.join(self.output_dir, output_config.get('images_subdir', 'images'))
        self.output_json_dir = os.path.join(self.output_dir, output_config.get('annotations_subdir', 'annotations'))
        self.debug_dir = os.path.join(self.output_dir, output_config.get('debug_subdir', 'debug'))
        self.create_debug = output_config.get('create_debug_visualizations', True)
        
        for d in [self.output_images_dir, self.output_json_dir]:
            os.makedirs(d, exist_ok=True)
        
        if self.create_debug:
            os.makedirs(self.debug_dir, exist_ok=True)
        
        # Get JSON files
        self.json_files = sorted(glob(os.path.join(self.input_json_dir, "*.json")))
        
        if not self.json_files:
            raise ValueError(f"No JSON files found in {self.input_json_dir}")
        
        logging.info(f"Found {len(self.json_files)} LabelMe JSON files to process.")
        
        # Checkpoint manager
        general_config = config.get('general', {})
        checkpoint_file = general_config.get('checkpoint_file', 'augmentation_checkpoint.json')
        checkpoint_path = os.path.join(self.output_dir, checkpoint_file)
        self.checkpoint_manager = CheckpointManager(checkpoint_path)
        self.use_checkpoint = general_config.get('resume_from_checkpoint', True)
        
        # Multiprocessing
        num_workers = general_config.get('num_workers')
        if num_workers is None:
            self.num_workers = max(1, cpu_count() - 1)
        else:
            self.num_workers = max(1, num_workers)
        
        logging.info(f"Using {self.num_workers} worker(s) for processing")
    
    def collect_class_names(self) -> List[str]:
        """
        Collect all unique class names from all JSON files.
        
        Returns:
            class_names: Sorted list of unique class names
        """
        all_class_names = set()
        
        for json_path in self.json_files:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            for shape in data.get('shapes', []):
                all_class_names.add(shape['label'])
        
        class_names = sorted(list(all_class_names))
        logging.info(f"Found {len(class_names)} classes: {class_names}")
        
        return class_names
    
    def process_dataset(self):
        """
        Process entire dataset with augmentations using multiprocessing.
        """
        # Collect class names
        class_names = self.collect_class_names()
        
        # Initialize augmentor
        augmentor = LabelMeAugmentor(class_names, self.config)
        
        # Filter files based on checkpoint
        files_to_process = []
        for json_path in self.json_files:
            if self.use_checkpoint and self.checkpoint_manager.is_processed(json_path):
                logging.debug(f"Skipping {json_path} (already processed)")
                continue
            files_to_process.append(json_path)
        
        if not files_to_process:
            logging.info("All files already processed. Use resume_from_checkpoint: false to reprocess.")
            return
        
        logging.info(f"Processing {len(files_to_process)} files ({len(self.json_files) - len(files_to_process)} skipped from checkpoint)")
        
        # Process files
        total_saved = 0
        
        if self.num_workers == 1:
            # Single-threaded processing
            for json_path in tqdm(files_to_process, desc="Processing files", unit="file"):
                result = self._process_single_file(json_path, augmentor)
                total_saved += result['num_saved']
                
                if result['success']:
                    self.checkpoint_manager.mark_processed(json_path)
                    self.checkpoint_manager.save_checkpoint()
        else:
            # Multi-threaded processing
            process_func = partial(
                self._process_single_file_static,
                output_images_dir=self.output_images_dir,
                output_json_dir=self.output_json_dir,
                debug_dir=self.debug_dir,
                create_debug=self.create_debug,
                class_names=class_names,
                config=self.config
            )
            
            with Pool(processes=self.num_workers) as pool:
                results = list(tqdm(
                    pool.imap(process_func, files_to_process),
                    total=len(files_to_process),
                    desc="Processing files",
                    unit="file"
                ))
            
            for json_path, result in zip(files_to_process, results):
                total_saved += result['num_saved']
                if result['success']:
                    self.checkpoint_manager.mark_processed(json_path)
            
            # Save checkpoint after batch
            self.checkpoint_manager.save_checkpoint()
        
        # Print summary
        self.print_summary(class_names, total_saved)
    
    def _process_single_file(self, json_path: str, augmentor: LabelMeAugmentor) -> Dict:
        """Process a single file (instance method)."""
        case_id = os.path.splitext(os.path.basename(json_path))[0]
        
        try:
            num_saved = augmentor.process_file(
                json_path,
                self.output_images_dir,
                self.output_json_dir,
                self.debug_dir,
                self.create_debug
            )
            logging.info(f"✓ {case_id}: Generated {num_saved} files")
            return {'success': True, 'num_saved': num_saved, 'case_id': case_id}
        
        except Exception as e:
            logging.error(f"✗ {case_id}: Error - {e}")
            return {'success': False, 'num_saved': 0, 'case_id': case_id, 'error': str(e)}
    
    @staticmethod
    def _process_single_file_static(json_path: str, output_images_dir: str, 
                                     output_json_dir: str, debug_dir: str,
                                     create_debug: bool, class_names: List[str], 
                                     config: Dict) -> Dict:
        """Process a single file (static method for multiprocessing)."""
        # Create augmentor in worker process
        augmentor = LabelMeAugmentor(class_names, config)
        case_id = os.path.splitext(os.path.basename(json_path))[0]
        
        try:
            num_saved = augmentor.process_file(
                json_path,
                output_images_dir,
                output_json_dir,
                debug_dir,
                create_debug
            )
            return {'success': True, 'num_saved': num_saved, 'case_id': case_id}
        
        except Exception as e:
            logging.error(f"✗ {case_id}: Error - {e}")
            return {'success': False, 'num_saved': 0, 'case_id': case_id, 'error': str(e)}
    
    def print_summary(self, class_names: List[str], total_saved: int):
        """Print processing summary."""
        print("\n" + "="*70)
        print("AUGMENTATION COMPLETE!")
        print("="*70)
        print(f"Input directory: {self.input_json_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nDirectories created:")
        print(f"  • Images: {self.output_images_dir}")
        print(f"  • Annotations: {self.output_json_dir}")
        if self.create_debug:
            print(f"  • Debug visualizations: {self.debug_dir}")
        print(f"\nClasses processed ({len(class_names)}):")
        for i, cls in enumerate(class_names, 1):
            print(f"  {i}. {cls}")
        print(f"\nTotal files generated: {total_saved}")
        print(f"Checkpoint saved to: {self.checkpoint_manager.checkpoint_file}")
        print("="*70)


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    """Main execution function with CLI support."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='LabelMe Augmentation Tool with configurable per-class augmentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use config file
  python auglabelme.py --config config/labelme_augmentation_config.yaml
  
  # Override specific paths
  python auglabelme.py --config config/labelme_augmentation_config.yaml \\
      --input /path/to/input --output /path/to/output
  
  # Clear checkpoint and reprocess all
  python auglabelme.py --config config/labelme_augmentation_config.yaml --clear-checkpoint
  
  # Single-threaded for debugging
  python auglabelme.py --config config/labelme_augmentation_config.yaml --workers 1
        """
    )
    configpath = 'config/labelme_augmentation_config45black.yaml'
    # configpath = 'config/labelme_augmentation_config45black.yaml'
    parser.add_argument('--config', type=str, required=False, default=configpath,
                        help='Path to YAML configuration file')
    parser.add_argument('--input', type=str, default=None,
                        help='Override input JSON directory')
    parser.add_argument('--output', type=str, default=None,
                        help='Override output directory')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of worker processes (overrides config)')
    parser.add_argument('--clear-checkpoint', action='store_true',
                        help='Clear checkpoint and reprocess all files')
    parser.add_argument('--no-checkpoint', action='store_true',
                        help='Disable checkpoint/resume functionality')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command-line arguments
    if args.input:
        config.setdefault('paths', {})['input_json_dir'] = args.input
    if args.output:
        config.setdefault('paths', {})['output_dir'] = args.output
    if args.workers is not None:
        config.setdefault('general', {})['num_workers'] = args.workers
    if args.no_checkpoint:
        config.setdefault('general', {})['resume_from_checkpoint'] = False
    if args.debug:
        config.setdefault('general', {})['log_level'] = 'DEBUG'
    
    # Initialize processor
    processor = DatasetProcessor(config)
    
    # Clear checkpoint if requested
    if args.clear_checkpoint:
        logging.info("Clearing checkpoint...")
        processor.checkpoint_manager.clear()
    
    # Process dataset
    processor.process_dataset()


if __name__ == "__main__":
    main() 