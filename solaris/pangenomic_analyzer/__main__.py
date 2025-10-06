#!/usr/bin/env python3
"""
Allow pangenomic_analyzer to be run as a module.
"""

from .cli import main

if __name__ == '__main__':
    exit(main())
