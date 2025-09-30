from setuptools import setup, find_packages

setup(
    name='biomera',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'pyhmmer',
        'requests',
        'selenium',
        'beautifulsoup4',
        'matplotlib',
        'seaborn',
        'scipy',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'biomera=biomera.cli:main',
        ],
    },
)