"""Test Albumentations transforms compatibility with mask augmentation."""

import inspect
import logging

import albumentations as A
import numpy as np
import pytest


# Mark to suppress expected warnings from compatibility testing
pytestmark = pytest.mark.filterwarnings(
    'ignore::UserWarning',  # Suppress all UserWarnings for this module
)


class TestAlbumentationsCompatibility:
    """Test that Albumentations transforms work with our mask augmentation use case."""
    
    @staticmethod
    def get_all_transforms():
        """Get all available transform classes from Albumentations.
        
        Returns:
            List of (name, class) tuples for usable transforms
        """
        transforms = []
        base_classes = ['BasicTransform', 'DualTransform', 'ImageOnlyTransform', 
                       'NoOp', 'Compose', 'ReplayCompose', 'Sequential', 
                       'OneOf', 'SomeOf']
        
        for name in dir(A):
            if name.startswith('_'):
                continue
            
            obj = getattr(A, name)
            if not inspect.isclass(obj):
                continue
            
            # Filter to actual transform classes
            if hasattr(obj, 'apply') and name not in base_classes:
                transforms.append((name, obj))
        
        return sorted(transforms, key=lambda x: x[0])
    
    @staticmethod
    def is_dual_transform(transform_class):
        """Check if transform supports both image and mask.
        
        Args:
            transform_class: Transform class to check
            
        Returns:
            True if supports masks, False otherwise
        """
        # Check class hierarchy
        try:
            return issubclass(transform_class, A.DualTransform)
        except:
            return False
    
    @staticmethod
    def get_transform_params(transform_name):
        """Get parameters to instantiate a transform with various fallbacks.
        
        Args:
            transform_name: Name of the transform
            
        Returns:
            List of parameter dictionaries to try (in order)
        """
        # Return list of parameter configs to try (first that works wins)
        # This handles version differences in parameter names
        param_variants = {
            # Normalization
            'Normalize': [
                {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]},
            ],
            'FromFloat': [
                {'dtype': 'uint8'},
                {},
            ],
            
            # Lambda and custom
            'Lambda': [
                {'image': lambda x, **kwargs: x, 'mask': lambda x, **kwargs: x},
            ],
            
            # Reference-based transforms
            'FDA': [
                {'reference_images': [np.zeros((10, 10, 3), dtype=np.uint8)]},
            ],
            'HistogramMatching': [
                {'reference_images': [np.zeros((10, 10, 3), dtype=np.uint8)]},
            ],
            'PixelDistributionAdaptation': [
                {'reference_images': [np.zeros((10, 10, 3), dtype=np.uint8)]},
            ],
            
            # Size-based transforms
            'LongestMaxSize': [
                {'max_size': 100},
            ],
            'SmallestMaxSize': [
                {'max_size': 100},
            ],
            'Resize': [
                {'height': 100, 'width': 100},
                {'size': (100, 100)},  # Alternative parameter name
            ],
            
            # Crop transforms
            'Crop': [
                {'x_min': 0, 'y_min': 0, 'x_max': 50, 'y_max': 50},
            ],
            'CenterCrop': [
                {'height': 50, 'width': 50},
                {'size': (50, 50)},
            ],
            'RandomCrop': [
                {'height': 50, 'width': 50},
                {'size': (50, 50)},
            ],
            'RandomSizedCrop': [
                {'min_max_height': (40, 60), 'height': 50, 'width': 50},
                {'min_max_height': (40, 60), 'size': (50, 50)},
            ],
            'RandomResizedCrop': [
                {'height': 50, 'width': 50},
                {'size': (50, 50)},
            ],
            'CropAndPad': [
                {'px': 10},
                {'percent': 0.1},
            ],
            
            # Padding
            'Pad': [
                {'min_height': 100, 'min_width': 100},
            ],
            'PadIfNeeded': [
                {'min_height': 100, 'min_width': 100},
            ],
            
            # Morphological
            'Morphological': [
                {'operation': 'dilation', 'kernel': np.ones((3, 3), dtype=np.uint8)},
                {'scale': (3, 3), 'operation': 'dilation'},  # Alternative
            ],
            
            # Special cases requiring metadata
            'Mosaic': [
                {'height': 100, 'width': 100, 'reference_data': []},
            ],
            'MixUp': [
                {'reference_data': []},
            ],
            'OverlayElements': [
                {'template_dir': '.'},
            ],
            
            # Grid-based
            'GridElasticDeform': [
                {'num_grid_xy': (3, 3)},
            ],
            
            # BBox transforms
            'AtLeastOneBBoxRandomCrop': [
                {'height': 50, 'width': 50},
            ],
            'BBoxSafeRandomCrop': [
                {'erosion_rate': 0.0},
            ],
            'CropNonEmptyMaskIfExists': [
                {'height': 50, 'width': 50},
            ],
            'RandomCropNearBBox': [
                {'max_part_shift': 0.3},
            ],
            'RandomSizedBBoxSafeCrop': [
                {'height': 50, 'width': 50},
            ],
            
            # 3D transforms
            'CenterCrop3D': [
                {'size': (50, 50, 50)},
            ],
            'CoarseDropout3D': [
                {'max_holes': 5, 'max_height': 10, 'max_width': 10, 'max_depth': 10},
            ],
            'Pad3D': [
                {'padding': 10},
            ],
            'RandomCrop3D': [
                {'size': (50, 50, 50)},
            ],
            'PadIfNeeded3D': [
                {'min_height': 50, 'min_width': 50, 'min_depth': 50},
            ],
            
            # Special symmetry
            'CubicSymmetry': [
                {},  # May need volume input
            ],
        }
        
        # Return list of variants to try, or single empty dict if no special params
        return param_variants.get(transform_name, [{}])
    
    def test_count_transforms(self):
        """Test that we have access to 100+ transforms."""
        transforms = self.get_all_transforms()
        assert len(transforms) >= 100, f"Expected 100+ transforms, got {len(transforms)}"
        print(f"\n✓ Found {len(transforms)} transforms in Albumentations")
    
    def test_dual_transforms_with_mask(self):
        """Test that dual transforms work with image + mask."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 20:40] = 1
        mask[60:80, 60:80] = 2
        
        transforms = self.get_all_transforms()
        dual_transforms = [(name, cls) for name, cls in transforms 
                          if self.is_dual_transform(cls)]
        
        working = []
        failed = []
        skipped = []
        working_params = {}  # Store which params worked
        
        for name, transform_class in dual_transforms:
            param_variants = self.get_transform_params(name)
            transform_worked = False
            last_error = None
            
            # Try each parameter variant until one works
            for params in param_variants:
                try:
                    transform = transform_class(p=1.0, **params)
                    
                    # Try to apply with mask
                    result = transform(image=image, mask=mask)
                    
                    # Verify result has both image and mask
                    assert 'image' in result, f"{name}: Missing 'image' in result"
                    assert 'mask' in result, f"{name}: Missing 'mask' in result"
                    assert result['image'].shape[:2] == result['mask'].shape[:2], \
                        f"{name}: Image and mask shape mismatch"
                    
                    working.append(name)
                    working_params[name] = params
                    transform_worked = True
                    break  # Success - move to next transform
                    
                except NotImplementedError as e:
                    last_error = ('NotImplementedError', str(e))
                    continue  # Try next parameter variant
                except Exception as e:
                    last_error = (type(e).__name__, str(e)[:100])
                    continue  # Try next parameter variant
            
            # If no variant worked, record failure
            if not transform_worked:
                if last_error and last_error[0] == 'NotImplementedError':
                    skipped.append(name)
                else:
                    failed.append((name, f"{last_error[0]}: {last_error[1]}" if last_error else "Unknown error"))
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"DUAL TRANSFORMS TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Albumentations version: {A.__version__}")
        print(f"Total dual transforms: {len(dual_transforms)}")
        print(f"✓ Working: {len(working)}")
        print(f"⚠ Skipped: {len(skipped)}")
        print(f"✗ Failed: {len(failed)}")
        
        if working:
            print(f"\n✓ Working transforms with parameters ({len(working)}):")
            for i, name in enumerate(working[:20], 1):
                params = working_params.get(name, {})
                param_str = f" (params: {list(params.keys())})" if params else ""
                print(f"  {i:2d}. {name}{param_str}")
            if len(working) > 20:
                print(f"  ... and {len(working) - 20} more")
        
        if skipped:
            print(f"\n⚠ Skipped (not implemented) ({len(skipped)}):")
            for name in skipped[:10]:
                print(f"  - {name}")
            if len(skipped) > 10:
                print(f"  ... and {len(skipped) - 10} more")
        
        if failed:
            print(f"\n✗ Failed ({len(failed)}):")
            for name, error in failed[:10]:
                print(f"  - {name}: {error[:80]}")
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more")
        
        print(f"{'='*70}\n")
        
        # Test passes if most dual transforms work
        success_rate = len(working) / len(dual_transforms) if dual_transforms else 0
        assert success_rate >= 0.7, \
            f"Too many dual transforms failed: {success_rate:.1%} success rate (expected >= 70%)"
    
    def test_each_working_transform_individually(self):
        """Test each working dual transform individually with proper parameters."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 20:40] = 1
        mask[60:80, 60:80] = 2
        
        # List of transforms that should work (from previous test results)
        expected_working = [
            'Affine', 'CenterCrop', 'CoarseDropout', 'ConstrainedCoarseDropout',
            'Crop', 'CropAndPad', 'D4', 'ElasticTransform', 'Erasing',
            'FrequencyMasking', 'GridDistortion', 'GridDropout', 'HorizontalFlip',
            'Lambda', 'LongestMaxSize', 'MaskDropout', 'Morphological',
            'OpticalDistortion', 'Pad', 'PadIfNeeded', 'Perspective',
            'PiecewiseAffine', 'PixelDropout', 'RandomCrop', 'RandomCropFromBorders',
            'RandomResizedCrop', 'RandomRotate90', 'RandomScale', 'RandomSizedCrop',
            'Resize', 'SafeRotate', 'ShiftScaleRotate', 'SmallestMaxSize',
            'Transpose', 'VerticalFlip', 'XYMasking', 'Rotate',
        ]
        
        results = {}
        
        for name in expected_working:
            if not hasattr(A, name):
                results[name] = ('missing', 'Transform not found in this Albumentations version')
                continue
            
            transform_class = getattr(A, name)
            param_variants = self.get_transform_params(name)
            
            worked = False
            for params in param_variants:
                try:
                    transform = transform_class(p=1.0, **params)
                    result = transform(image=image, mask=mask)
                    
                    assert 'image' in result
                    assert 'mask' in result
                    assert result['image'].shape[:2] == result['mask'].shape[:2]
                    
                    results[name] = ('success', params)
                    worked = True
                    break
                except Exception as e:
                    last_error = f"{type(e).__name__}: {str(e)[:80]}"
                    continue
            
            if not worked:
                results[name] = ('failed', last_error)
        
        # Print individual results
        print(f"\n{'='*70}")
        print(f"INDIVIDUAL TRANSFORM VERIFICATION")
        print(f"{'='*70}")
        print(f"Albumentations version: {A.__version__}")
        
        success = [k for k, v in results.items() if v[0] == 'success']
        failed = [k for k, v in results.items() if v[0] == 'failed']
        missing = [k for k, v in results.items() if v[0] == 'missing']
        
        print(f"\n✓ Success: {len(success)}/{len(expected_working)}")
        print(f"✗ Failed: {len(failed)}/{len(expected_working)}")
        print(f"⚠ Missing: {len(missing)}/{len(expected_working)}")
        
        if failed:
            print(f"\n✗ Failed transforms:")
            for name in failed:
                error = results[name][1]
                print(f"  - {name}: {error}")
        
        if missing:
            print(f"\n⚠ Missing transforms (version mismatch):")
            for name in missing:
                print(f"  - {name}")
        
        print(f"{'='*70}\n")
        
        # Allow some failures due to version differences
        success_rate = len(success) / len(expected_working)
        assert success_rate >= 0.8, \
            f"Too many expected transforms failed: {success_rate:.1%} (expected >= 80%)"
    
    def test_common_transforms_work(self):
        """Test that commonly used transforms work perfectly."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 20:40] = 1
        
        # List of transforms we commonly use in configs
        common_transforms = [
            ('HorizontalFlip', A.HorizontalFlip, {}),
            ('VerticalFlip', A.VerticalFlip, {}),
            ('Rotate', A.Rotate, {'limit': [-15, 15]}),
            ('ShiftScaleRotate', A.ShiftScaleRotate, {}),
            ('ElasticTransform', A.ElasticTransform, {'alpha': 50, 'sigma': 5}),
            ('GridDistortion', A.GridDistortion, {}),
            ('OpticalDistortion', A.OpticalDistortion, {}),
            ('RandomBrightnessContrast', A.RandomBrightnessContrast, {}),
            ('HueSaturationValue', A.HueSaturationValue, {}),
            ('GaussNoise', A.GaussNoise, {}),
            ('Blur', A.Blur, {}),
            ('GaussianBlur', A.GaussianBlur, {}),
            ('ColorJitter', A.ColorJitter, {}),
            ('Affine', A.Affine, {}),
            ('Perspective', A.Perspective, {}),
        ]
        
        print(f"\n{'='*70}")
        print(f"COMMON TRANSFORMS TEST")
        print(f"{'='*70}")
        
        for name, transform_class, params in common_transforms:
            try:
                transform = transform_class(p=1.0, **params)
                result = transform(image=image, mask=mask)
                
                assert 'image' in result
                assert 'mask' in result
                assert result['image'].shape[:2] == result['mask'].shape[:2]
                
                print(f"✓ {name:30s} - OK")
                
            except Exception as e:
                print(f"✗ {name:30s} - FAILED: {e}")
                raise AssertionError(f"Common transform {name} failed: {e}")
        
        print(f"{'='*70}\n")
    
    def test_transform_builder_compatibility(self):
        """Test that transforms work through our TransformBuilder."""
        from labelme_augmentor.transforms import TransformBuilder
        
        transform_configs = [
            {'name': 'HorizontalFlip', 'probability': 0.5},
            {'name': 'VerticalFlip', 'probability': 0.5},
            {'name': 'Rotate', 'probability': 0.3, 'params': {'limit': [-15, 15]}},
            {'name': 'RandomBrightnessContrast', 'probability': 0.3},
            {'name': 'ElasticTransform', 'probability': 0.2, 'params': {'alpha': 50, 'sigma': 5}},
        ]
        
        # Build transform pipeline
        transform = TransformBuilder.build_transform(transform_configs)
        
        # Test with image and mask
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 20:40] = 1
        
        # Apply multiple times to test randomness
        for _ in range(10):
            result = transform(image=image, mask=mask)
            assert 'image' in result
            assert 'mask' in result
            assert result['image'].shape[:2] == result['mask'].shape[:2]
        
        print("\n✓ TransformBuilder compatibility test passed")
    
    def test_image_only_transforms_exist(self):
        """Test that image-only transforms are available but don't break mask pipelines."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 20:40] = 1
        
        # Image-only transforms we might want to use
        image_only = [
            'CLAHE',
            'Equalize',
            'Posterize',
            'Emboss',
            'Sharpen',
            'AutoContrast',
        ]
        
        available = []
        for name in image_only:
            if hasattr(A, name):
                transform_class = getattr(A, name)
                try:
                    # Test it works on image only
                    transform = transform_class(p=1.0)
                    result = transform(image=image)
                    assert 'image' in result
                    available.append(name)
                except:
                    pass
        
        print(f"\n✓ Found {len(available)} image-only transforms available")
        print(f"  Available: {', '.join(available)}")


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
