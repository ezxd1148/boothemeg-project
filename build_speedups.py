"""
build_speedups.py — Compile the _speedups.pyx Cython module.

Usage:
    python build_speedups.py build_ext --inplace

This compiles src/backend/_speedups.pyx into a native .so/.pyd file
that can be imported by the main modules for a small CPU speed boost.

Requires: cython, a C compiler (gcc/clang/msvc)

Note: This project is I/O-bound (ADB, HTTP APIs, file I/O). Cython only
accelerates CPU computation, so real-world gains will be minimal (<1%).
This is provided for completeness — only the fingerprint hashing, schema
validation, and string parsing benefit from C compilation.
"""

from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup

HERE = Path(__file__).parent
SRC = HERE / "src" / "backend"

extensions = [
    Extension(
        "src.backend._speedups",
        [str(SRC / "_speedups.pyx")],
    ),
]

setup(
    name="bootheschedule-speedups",
    ext_modules=cythonize(
        extensions,
        language_level="3",
        annotate=True,  # generates _speedups.html showing Python/C interaction
    ),
)
