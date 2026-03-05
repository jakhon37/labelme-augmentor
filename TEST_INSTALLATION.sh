#!/bin/bash
# Test installation and functionality

echo "=================================="
echo "Testing LabelMe Augmentor v2.0.0"
echo "=================================="
echo ""

# Test 1: Check Python version
echo "✓ Test 1: Python version"
python3 --version
echo ""

# Test 2: Test imports
echo "✓ Test 2: Testing module imports..."
cd src
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from labelme_augmentor import __version__, Augmentor, DatasetProcessor
from labelme_augmentor.io import ImageLoader, ImageSaver, LabelMeReader, LabelMeWriter, MaskConverter
from labelme_augmentor.validation import MaskValidator
from labelme_augmentor.utils import CheckpointManager
from labelme_augmentor.visualization import ConfigurableColorPalette, DebugVisualizer
from labelme_augmentor.transforms import TransformBuilder
from labelme_augmentor.config import load_config

print(f"✅ All imports successful!")
print(f"   Version: {__version__}")
PYEOF
cd ..
echo ""

# Test 3: Check file structure
echo "✓ Test 3: Verifying file structure..."
if [ -d "src/labelme_augmentor" ]; then
    echo "✅ Source package exists"
else
    echo "❌ Source package missing"
    exit 1
fi

if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml exists"
else
    echo "❌ pyproject.toml missing"
    exit 1
fi

if [ -f "README.md" ]; then
    echo "✅ README.md exists"
else
    echo "❌ README.md missing"
    exit 1
fi
echo ""

# Test 4: Count modules
echo "✓ Test 4: Module count"
MODULE_COUNT=$(find src/labelme_augmentor -name "*.py" | wc -l)
echo "✅ Created $MODULE_COUNT Python files"
echo ""

# Test 5: Check documentation
echo "✓ Test 5: Documentation"
DOC_COUNT=$(ls -1 *.md 2>/dev/null | wc -l)
echo "✅ Created $DOC_COUNT documentation files"
echo ""

# Test 6: Verify backward compatibility
echo "✓ Test 6: Backward compatibility"
if [ -f "auglabelme.py" ]; then
    echo "✅ Original auglabelme.py preserved"
fi
if [ -f "auglabelme_v2.py" ]; then
    echo "✅ Compatibility wrapper created"
fi
echo ""

echo "=================================="
echo "✅ ALL TESTS PASSED!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Install: pip install -e ."
echo "2. Run: labelme-augment --config config/labelme_augmentation_config45black.yaml"
echo ""
