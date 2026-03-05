"""Setup file for backward compatibility with older pip versions."""

from setuptools import setup

# Read version
version = {}
with open("src/labelme_augmentor/__version__.py") as f:
    exec(f.read(), version)

setup(
    name="labelme-augmentor-pro",
    version=version["__version__"],
    description="Advanced data augmentation tool for LabelMe annotated datasets",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author=version["__author__"],
    author_email=version["__email__"],
    url="https://github.com/jakhon37/labelme-augmentor",
    license=version["__license__"],
    packages=[
        "labelme_augmentor",
        "labelme_augmentor.core",
        "labelme_augmentor.io",
        "labelme_augmentor.transforms",
        "labelme_augmentor.validation",
        "labelme_augmentor.visualization",
        "labelme_augmentor.config",
        "labelme_augmentor.utils",
    ],
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
        "opencv-python>=4.5.0",
        "Pillow>=8.0.0",
        "albumentations>=1.3.0",
        "PyYAML>=5.4.0",
        "tqdm>=4.60.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "labelme-augment=labelme_augmentor.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="labelme augmentation data-augmentation computer-vision image-processing defect-detection",
)
