"""Unit tests for I/O modules."""

import json

import numpy as np
import pytest
from PIL import Image

from labelme_augmentor.io import ImageLoader, ImageSaver, LabelMeReader, LabelMeWriter, MaskConverter


class TestImageLoader:
    """Test ImageLoader class."""
    
    def test_load_rgb_image(self, temp_dir, sample_image):
        """Test loading RGB image."""
        config = {"image_processing": {}}
        loader = ImageLoader(config)
        
        # Save test image
        img_path = temp_dir / "test.png"
        Image.fromarray(sample_image).save(img_path)
        
        # Load
        loaded = loader.load(str(img_path))
        assert loaded.shape == (100, 100, 3)
        assert loaded.dtype == np.uint8
    
    def test_load_grayscale_converts_to_rgb(self, temp_dir):
        """Test that grayscale images are converted to RGB."""
        config = {"image_processing": {"handle_grayscale": True}}
        loader = ImageLoader(config)
        
        # Create grayscale image
        gray_img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        img_path = temp_dir / "gray.png"
        Image.fromarray(gray_img, mode='L').save(img_path)
        
        # Load
        loaded = loader.load(str(img_path))
        assert loaded.shape == (100, 100, 3)  # Should be RGB
    
    def test_load_nonexistent_file(self, temp_dir):
        """Test loading non-existent file raises error."""
        config = {"image_processing": {}}
        loader = ImageLoader(config)
        
        with pytest.raises(Exception):
            loader.load(str(temp_dir / "nonexistent.jpg"))


class TestImageSaver:
    """Test ImageSaver class."""
    
    def test_save_png(self, temp_dir, sample_image):
        """Test saving PNG image."""
        config = {"image_processing": {"output_format": "png"}}
        saver = ImageSaver(config)
        
        output_path = temp_dir / "output.png"
        saver.save(sample_image, str(output_path))
        
        assert output_path.exists()
        # Verify can be loaded back
        loaded = np.array(Image.open(output_path))
        assert loaded.shape == sample_image.shape
    
    def test_save_jpg(self, temp_dir, sample_image):
        """Test saving JPG image."""
        config = {"image_processing": {"output_format": "jpg", "output_quality": 95}}
        saver = ImageSaver(config)
        
        output_path = temp_dir / "output.jpg"
        saver.save(sample_image, str(output_path))
        
        assert output_path.exists()


class TestMaskConverter:
    """Test MaskConverter class."""
    
    def test_labelme_to_mask(self, sample_labelme_json):
        """Test converting LabelMe JSON to mask."""
        class_map = {"defect1": 1, "defect2": 2}
        idx_to_class = {1: "defect1", 2: "defect2"}
        converter = MaskConverter(class_map, idx_to_class)
        
        mask = converter.labelme_to_mask(sample_labelme_json)
        
        assert mask.shape == (100, 100)
        assert mask.dtype == np.uint8
        assert 1 in mask  # Has class 1
        assert 2 in mask  # Has class 2
    
    def test_mask_to_labelme_shapes(self, sample_mask):
        """Test converting mask to LabelMe shapes."""
        class_map = {"defect1": 1, "defect2": 2}
        idx_to_class = {1: "defect1", 2: "defect2"}
        converter = MaskConverter(class_map, idx_to_class)
        
        shapes = converter.mask_to_labelme_shapes(sample_mask)
        
        assert len(shapes) == 2  # Two defects
        assert all(s["shape_type"] == "polygon" for s in shapes)
        labels = {s["label"] for s in shapes}
        assert labels == {"defect1", "defect2"}
    
    def test_roundtrip_conversion(self, sample_labelme_json):
        """Test that conversion is reversible."""
        class_map = {"defect1": 1, "defect2": 2}
        idx_to_class = {1: "defect1", 2: "defect2"}
        converter = MaskConverter(class_map, idx_to_class)
        
        # JSON -> Mask -> JSON
        mask = converter.labelme_to_mask(sample_labelme_json)
        shapes = converter.mask_to_labelme_shapes(mask)
        
        # Should have same classes
        original_labels = {s["label"] for s in sample_labelme_json["shapes"]}
        converted_labels = {s["label"] for s in shapes}
        assert original_labels == converted_labels


class TestLabelMeWriter:
    """Test LabelMeWriter class."""
    
    def test_create_json_without_base64(self, sample_image):
        """Test creating LabelMe JSON without base64."""
        writer = LabelMeWriter(enable_base64=False)
        
        shapes = [
            {
                "label": "test",
                "points": [[10, 10], [20, 10], [20, 20], [10, 20]],
                "shape_type": "polygon",
                "group_id": None,
                "flags": {}
            }
        ]
        
        json_data = writer.create_json(sample_image, shapes, "test.jpg")
        
        assert json_data["version"] == "5.0.1"
        assert json_data["imagePath"] == "test.jpg"
        assert json_data["imageData"] is None
        assert json_data["imageHeight"] == 100
        assert json_data["imageWidth"] == 100
        assert len(json_data["shapes"]) == 1
    
    def test_save_json(self, temp_dir, sample_image):
        """Test saving JSON to file."""
        writer = LabelMeWriter(enable_base64=False)
        
        shapes = [{"label": "test", "points": [[10, 10]], "shape_type": "point", "group_id": None, "flags": {}}]
        json_data = writer.create_json(sample_image, shapes, "test.jpg")
        
        output_path = temp_dir / "test.json"
        writer.save(json_data, str(output_path))
        
        assert output_path.exists()
        # Verify can be loaded
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["imagePath"] == "test.jpg"


class TestLabelMeReader:
    """Test LabelMeReader class."""
    
    def test_load_json(self, temp_dir, sample_labelme_json):
        """Test loading LabelMe JSON file."""
        json_path = temp_dir / "test.json"
        with open(json_path, 'w') as f:
            json.dump(sample_labelme_json, f)
        
        reader = LabelMeReader()
        data = reader.load_json(str(json_path))
        
        assert data["version"] == "5.0.1"
        assert len(data["shapes"]) == 2
