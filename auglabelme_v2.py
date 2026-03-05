#!/usr/bin/env python3
"""
Backward compatibility wrapper for the new modular labelme-augmentor.

This file provides the same CLI interface as the old auglabelme.py
but uses the new modular implementation underneath.

DEPRECATED: Use 'labelme-augment' CLI command instead.
"""

import sys
import warnings

# Add src to path
sys.path.insert(0, 'src')

from labelme_augmentor.cli import main

if __name__ == "__main__":
    warnings.warn(
        "auglabelme_v2.py is deprecated. Please use 'labelme-augment' command instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    main()
