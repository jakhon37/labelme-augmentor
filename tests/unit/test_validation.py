"""Unit tests for validation module."""

import numpy as np
import pytest

from labelme_augmentor.validation import MaskValidator


class TestMaskValidator:
    """Test MaskValidator class."""
    
    def test_init(self, sample_config):
        """Test validator initialization."""
        validator = MaskValidator(sample_config)
        assert validator.min_defect_area == 10
        assert validator.min_contour_points == 3
    
    def test_validate_mask_valid(self, sample_config, sample_mask):
        """Test validation of valid mask."""
        validator = MaskValidator(sample_config)
        result = validator.validate_mask(sample_mask)
        assert result is True
    
    def test_validate_mask_empty(self, sample_config):
        """Test validation of empty mask."""
        validator = MaskValidator(sample_config)
        empty_mask = np.zeros((100, 100), dtype=np.uint8)
        result = validator.validate_mask(empty_mask)
        assert result is False
    
    def test_validate_mask_too_small(self, sample_config):
        """Test validation of mask with too small defect."""
        validator = MaskValidator(sample_config)
        # Create tiny defect (< 10 pixels)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[0:2, 0:2] = 1  # 4 pixels - below min_defect_area
        
        result = validator.validate_mask(mask)
        assert result is False
    
    def test_validate_with_original_preservation(self, sample_config, sample_mask):
        """Test defect preservation check."""
        validator = MaskValidator(sample_config)
        
        # Create augmented mask with similar area
        aug_mask = sample_mask.copy()
        
        result = validator.validate_mask(aug_mask, sample_mask)
        assert result is True
    
    def test_validate_preservation_fail(self, sample_config, sample_mask):
        """Test preservation check failure."""
        validator = MaskValidator(sample_config)
        
        # Create augmented mask with very different area
        aug_mask = np.zeros_like(sample_mask)
        aug_mask[20:25, 20:25] = 1  # Much smaller than original
        
        result = validator.validate_mask(aug_mask, sample_mask)
        assert result is False
    
    def test_per_class_area_change_override(self, sample_config, sample_mask):
        """Test per-class max area change override is applied."""
        sample_config['class_specific'] = {
            'defect1': {'max_area_change_ratio': 0.1}
        }
        idx_to_class = {1: 'defect1', 2: 'defect2'}
        validator = MaskValidator(sample_config, idx_to_class)

        # Reduce defect1 area by 25% (global default 0.5 would pass, override 0.1 should fail)
        aug_mask = sample_mask.copy()
        aug_mask[35:40, 20:40] = 0

        result = validator.validate_mask(aug_mask, sample_mask)
        assert result is False
    
    def test_per_class_min_area_override(self, sample_config):
        """Test per-class min_defect_area override."""
        sample_config['class_specific'] = {
            'defect1': {'min_defect_area': 500}  # Very high threshold
        }
        idx_to_class = {1: 'defect1', 2: 'defect2'}
        validator = MaskValidator(sample_config, idx_to_class)
        
        # Create mask with defect1 (400 pixels) - should fail class-specific check
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 20:40] = 1  # 400 pixels, below 500 threshold
        
        result = validator.validate_mask(mask)
        assert result is False
    
    def test_per_class_border_rejection(self, sample_config):
        """Test per-class border rejection override."""
        sample_config['validation']['reject_border_defects'] = False  # Global: allow borders
        sample_config['class_specific'] = {
            'defect1': {'reject_border_defects': True, 'border_margin': 5}  # Class: reject borders
        }
        idx_to_class = {1: 'defect1', 2: 'defect2'}
        validator = MaskValidator(sample_config, idx_to_class)
        
        # Create defect1 touching border
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[0:20, 0:20] = 1  # Touches top-left corner
        
        result = validator.validate_mask(mask)
        assert result is False
    
    def test_per_class_check_preservation_disabled(self, sample_config, sample_mask):
        """Test per-class check_defect_preservation can be disabled."""
        sample_config['class_specific'] = {
            'defect1': {'check_defect_preservation': False}
        }
        idx_to_class = {1: 'defect1', 2: 'defect2'}
        validator = MaskValidator(sample_config, idx_to_class)
        
        # Drastically change defect1 area (would normally fail)
        # But keep it above min_defect_area (10)
        aug_mask = np.zeros_like(sample_mask)
        aug_mask[20:25, 20:25] = 1  # Smaller defect1 (25 pixels - above min 10)
        aug_mask[60:80, 60:80] = 2  # defect2 unchanged
        
        # Should pass for defect1 (preservation disabled) and defect2 unchanged
        result = validator.validate_mask(aug_mask, sample_mask)
        assert result is True  # defect1 preservation ignored
    
    def test_disabled_validation(self, sample_config):
        """Test that validation can be disabled."""
        sample_config['validation']['enabled'] = False
        validator = MaskValidator(sample_config)
        
        # Even empty mask should pass when disabled
        empty_mask = np.zeros((100, 100), dtype=np.uint8)
        result = validator.validate_mask(empty_mask)
        assert result is True
    
    def test_border_rejection(self, sample_config):
        """Test border defect rejection."""
        sample_config['validation']['reject_border_defects'] = True
        sample_config['validation']['border_margin'] = 5
        validator = MaskValidator(sample_config)
        
        # Create defect touching border
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[0:20, 0:20] = 1  # Touches top-left corner
        
        result = validator.validate_mask(mask)
        assert result is False
    
    def test_preservation_with_resize(self, sample_config):
        """Test that preservation check works correctly when image is resized."""
        sample_config['validation']['check_defect_preservation'] = True
        sample_config['validation']['max_area_change_ratio'] = 0.10  # 10% threshold
        validator = MaskValidator(sample_config)
        
        # Original: 500x500 image, defect = 1000 pixels (0.4% of image)
        orig_mask = np.zeros((500, 500), dtype=np.uint8)
        orig_mask[100:110, 100:110] = 1  # 100 pixels
        orig_mask[200:240, 200:240] = 1  # 900 more pixels = 1000 total
        
        # CASE 1: After 2x resize with 5% defect growth (should PASS)
        # Image becomes 1000x1000 (4x pixels)
        # Defect should be 4000 pixels if scaled perfectly
        # With 5% growth: 4000 * 1.05 = 4200 pixels (0.42% of image)
        # Relative change: (0.42 - 0.40) / 0.40 = 5% < 10% → PASS
        aug_mask_pass = np.zeros((1000, 1000), dtype=np.uint8)
        aug_mask_pass[200:220, 200:220] = 1  # 400 pixels
        aug_mask_pass[400:480, 400:480] = 1  # 3800 more = 4200 total
        
        result = validator.validate_mask(aug_mask_pass, orig_mask)
        assert result is True, "Should pass: 5% relative change < 10% threshold"
        
        # CASE 2: After 2x resize with 15% defect loss (should FAIL)
        # Expected: 4000 pixels, Actual: 4000 * 0.85 = 3400 pixels (0.34% of image)
        # Relative change: (0.40 - 0.34) / 0.40 = 15% > 10% → FAIL
        aug_mask_fail = np.zeros((1000, 1000), dtype=np.uint8)
        aug_mask_fail[200:220, 200:220] = 1  # 400 pixels
        aug_mask_fail[400:470, 400:470] = 1  # 3000 more = 3400 total
        
        result = validator.validate_mask(aug_mask_fail, orig_mask)
        assert result is False, "Should fail: 15% relative loss > 10% threshold"
        
        # CASE 3: After 0.5x resize with proper scaling (should PASS)
        # Image becomes 250x250 (0.25x pixels)
        # Defect should be ~250 pixels if scaled perfectly
        # With 8% change: 250 * 0.92 = 230 pixels (0.368% of image)
        # Relative change: (0.40 - 0.368) / 0.40 = 8% < 10% → PASS
        aug_mask_shrink = np.zeros((250, 250), dtype=np.uint8)
        aug_mask_shrink[50:55, 50:55] = 1  # 25 pixels
        aug_mask_shrink[100:120, 100:120] = 1  # 205 more = 230 total
        
        result = validator.validate_mask(aug_mask_shrink, orig_mask)
        assert result is True, "Should pass: 8% relative change < 10% threshold"
    
    def test_length_validation_min(self, sample_config):
        """Test minimum defect length validation."""
        sample_config['validation']['min_defect_length'] = 50.0
        validator = MaskValidator(sample_config)
        
        # Create horizontal scratch (long defect) - should PASS
        mask_pass = np.zeros((100, 100), dtype=np.uint8)
        mask_pass[50:55, 20:80] = 1  # 60 pixels long (length > 50)
        
        result = validator.validate_mask(mask_pass)
        assert result is True, "Long defect should pass min length check"
        
        # Create small defect - should FAIL
        mask_fail = np.zeros((100, 100), dtype=np.uint8)
        mask_fail[50:55, 45:50] = 1  # Only 5 pixels long (length < 50)
        
        result = validator.validate_mask(mask_fail)
        assert result is False, "Short defect should fail min length check"
    
    def test_length_validation_max(self, sample_config):
        """Test maximum defect length validation."""
        sample_config['validation']['max_defect_length'] = 30.0
        validator = MaskValidator(sample_config)
        
        # Create small defect - should PASS
        mask_pass = np.zeros((100, 100), dtype=np.uint8)
        mask_pass[50:55, 45:65] = 1  # 20 pixels long (length < 30)
        
        result = validator.validate_mask(mask_pass)
        assert result is True, "Short defect should pass max length check"
        
        # Create long defect - should FAIL
        mask_fail = np.zeros((100, 100), dtype=np.uint8)
        mask_fail[50:55, 20:80] = 1  # 60 pixels long (length > 30)
        
        result = validator.validate_mask(mask_fail)
        assert result is False, "Long defect should fail max length check"
    
    def test_length_validation_angled(self, sample_config):
        """Test length calculation for angled defects."""
        sample_config['validation']['min_defect_length'] = 70.0
        validator = MaskValidator(sample_config)
        
        # Create diagonal scratch (angled defect)
        # Should measure length along major axis, not just x or y
        mask = np.zeros((100, 100), dtype=np.uint8)
        # Draw a diagonal line from (20,20) to (80,80)
        # Length should be sqrt((80-20)^2 + (80-20)^2) ≈ 84.85
        for i in range(60):
            mask[20+i:22+i, 20+i:22+i] = 1
        
        result = validator.validate_mask(mask)
        assert result is True, "Diagonal defect length should be calculated correctly"
    
    def test_per_class_length_validation(self, sample_config, sample_mask):
        """Test per-class length validation overrides."""
        # Global: no length constraint
        # T1-Scratch (class 1): min_defect_length = 30
        sample_config['class_specific'] = {
            'defect1': {
                'min_defect_length': 30.0
            }
        }
        idx_to_class = {1: 'defect1', 2: 'defect2'}
        validator = MaskValidator(sample_config, idx_to_class)
        
        # Create mask with defect1 (short) and defect2 (any length)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:25, 30:40] = 1  # defect1: 10 pixels long (< 30, should FAIL)
        mask[60:80, 60:80] = 2  # defect2: any length (should PASS, no constraint)
        
        result = validator.validate_mask(mask)
        assert result is False, "defect1 should fail min_defect_length check"
        
        # Now make defect1 longer
        mask2 = np.zeros((100, 100), dtype=np.uint8)
        mask2[20:25, 30:70] = 1  # defect1: 40 pixels long (> 30, should PASS)
        mask2[60:80, 60:80] = 2  # defect2: unchanged
        
        result = validator.validate_mask(mask2)
        assert result is True, "Both defects should pass"
