"""LabelMe Augmentor - Advanced data augmentation for LabelMe annotated datasets."""

from . import config, core, io, transforms, utils, validation, visualization
from .__version__ import __author__, __license__, __version__
from .core import Augmentor, DatasetProcessor

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "Augmentor",
    "DatasetProcessor",
    "config",
    "core",
    "io",
    "transforms",
    "utils",
    "validation",
    "visualization",
]
