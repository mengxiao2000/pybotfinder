"""
Setup script for pybotfinder
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="pybotfinder",
    version="0.2.0",
    author="Xiao MENG",
    author_email="xiaomeng7-c@my.cityu.edu.hk",
    description="微博社交机器人检测工具包 - Weibo Social Bot Detection Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mengxiao2000/pybotfinder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pybotfinder-collect=pybotfinder.cli:collect",
            "pybotfinder-extract=pybotfinder.cli:extract",
            "pybotfinder-train=pybotfinder.cli:train",
            "pybotfinder-predict=pybotfinder.cli:predict",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

