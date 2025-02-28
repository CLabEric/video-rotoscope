#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="scanner-darkly",
    version="0.1.0",
    author="Edge Detection Studio",
    author_email="contact@edgedetectionstudio.com",
    description="Scanner Darkly rotoscoping effect for videos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edgedetectionstudio/scanner-darkly",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "opencv-python-headless>=4.8.0",
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
        "ffmpeg-python>=0.2.0",
        "boto3>=1.28.0",
        "tqdm>=4.66.0",
        "pyyaml>=6.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.1.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "matplotlib>=3.7.0"
        ],
    },
    entry_points={
        "console_scripts": [
            "scanner-darkly=src.main:main_cli",
        ],
    },
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
)