from setuptools import setup, find_packages

setup(
    name='solaris',
    version='0.1.0',
    description='Solaris: Toolkit for heterologous pathway transfer for metabolic engineering',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'pandas>=1.3.0',
        'pyhmmer>=0.8.0',
        'requests>=2.25.0',
        'selenium>=4.0.0',
        'beautifulsoup4>=4.9.0',
        'matplotlib>=3.3.0',
        'seaborn>=0.11.0',
        'scipy>=1.7.0',
        'numpy>=1.20.0',
        'biopython>=1.79',
        'bacdive>=1.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.900',
        ],
        'docs': [
            'sphinx>=4.0',
            'sphinx-rtd-theme>=0.5',
        ],
    },
    # Pangenomic analyzer
    entry_points={
        'console_scripts': [
            'solaris=solaris.cli:main',
            'solaris-pathway-profiler=solaris.pathway_profiler.cli:main',
            'solaris-pangenomic-analyzer=solaris.pangenomic_analyzer.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='bioinformatics genomics pathway-analysis metabolic-engineering synthetic-biology',
)