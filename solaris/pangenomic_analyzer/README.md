# Pangenomic Analyzer

The **Pangenomic Analyzer** module provides comprehensive tools for analyzing pathway completeness across multiple bacterial strains using HMM (Hidden Markov Model) profiles. It is integrated into the main Solaris CLI for seamless workflow management.

## Features

- **Complete Workflow Integration**: Works seamlessly with pathway_profiler for end-to-end analysis
- **HMM Analysis**: Advanced HMM profile searching using pyhmmer with parallel processing
- **Strain Comparison**: Create comprehensive strain × EC comparison matrices
- **Advanced Visualizations**: Heatmaps, clustering plots, and statistical dashboards
- **Flexible Analysis**: Step-by-step commands or complete workflow execution
- **Scalable Processing**: Handles large datasets (100+ strains) with intelligent optimization

## Architecture

The module follows object-oriented design with specialized classes:

- **StrainManager**: Handles strain data loading and validation
- **BatchAnalyzer**: HMM searching with EC number mapping using original optimized logic
- **PathwayAnalyzer**: Creates comparison matrices and calculates strain rankings
- **VisualizationManager**: Advanced plotting with clustering and crowding management

## Installation

The pangenomic analyzer is installed as part of the Solaris package:

```bash
pip install -e .
```

## Prerequisites

Before running pangenomic analysis, you need to generate the required files using pathway_profiler:

```bash
# Step 1: Extract EC-Pfam mappings from KEGG pathway
solaris pathway_profiler extract-ec --pathway map00720 --output pfam_ids.txt

# Step 2: Generate HMM profiles from Pfam database
solaris pathway_profiler get-profiles --input pfam_ids.txt --pfam-db /path/to/pfam --output selected_pfam.hmm
```

## Command Line Usage

### Complete Workflow (Recommended)

Run the entire pangenomic analysis pipeline:

```bash
# Complete analysis with clustering visualizations
solaris pangenomic_analyzer complete \
    --genomes-dir ./genomes \
    --hmm-file selected_pfam.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --clustered-plots
```

### Step-by-Step Workflow

For more control, run individual steps:

```bash
# Step 2: HMM Analysis (equivalent to tmp/run_comparison.py)
solaris pangenomic_analyzer step2-hmm \
    --genomes-dir ./genomes \
    --hmm-file selected_pfam.hmm \
    --pfam-ids-file pfam_ids.txt \
    --output-dir results/batch

# Step 3: Create comparison matrix (equivalent to tmp/rank_strains.py)  
solaris pangenomic_analyzer step3-matrix \
    --results-dir results/batch \
    --output-dir results \
    --clustered-plots
```

### Check Prerequisites

Validate required files and get setup guidance:

```bash
solaris pangenomic_analyzer check-prerequisites \
    --hmm-file selected_pfam.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --pathway-id map00720 \
    --pfam-db /path/to/pfam
```

## Python API Usage

### Basic Usage

```python
from solaris.pangenomic_analyzer import (
    StrainManager, BatchAnalyzer, 
    PathwayAnalyzer, VisualizationManager
)

# Initialize components
strain_manager = StrainManager()
batch_analyzer = BatchAnalyzer()
pathway_analyzer = PathwayAnalyzer()
viz_manager = VisualizationManager("plots/")

# Load strain files
strains_df = strain_manager.load_strains_from_directory("genomes/")

# Run HMM analysis with EC mapping (optimized implementation)
hmm_results = batch_analyzer.analyze_ec_numbers_from_directory(
    genomes_dir="genomes/",
    hmm_file="selected_pfam.hmm",
    pfam_ec_mapping_file="pfam_ids.txt",
    output_dir="results/batch",
    evalue_threshold=1e-5
)

# Create comparison matrix from individual strain results
comparison_matrix, strain_rankings = pathway_analyzer.create_comparison_matrix_from_files(
    results_dir="results/batch",
    output_dir="results"
)

# Generate visualizations with clustering
plot_files = viz_manager.generate_all_plots(
    strain_rankings, comparison_matrix, output_dir="plots"
)

# Advanced clustering plots (from plots_collapsed.py)
cluster_plots = viz_manager.generate_clustered_plots(
    comparison_matrix, output_dir="plots"
)
```

### Advanced Features

```python
# Rank strains by completeness with detailed metrics
detailed_rankings = pathway_analyzer.rank_strains_by_completeness_from_matrix(
    comparison_matrix_file="results/comparison_matrix.csv",
    output_file="results/strain_rankings.csv"
)

# Custom visualization with intelligent crowding management
heatmap_file = viz_manager.plot_comparison_heatmap(
    comparison_matrix, 
    max_labels=50,  # Hide labels if more than 50 strains
    cluster_strains=True
)

# Similarity analysis with hierarchical clustering
similarity_plots = viz_manager.plot_strain_clustering(
    comparison_matrix,
    method='ward',  # Clustering method
    metric='euclidean'
)
```

## Input Files

### Genome Files
- **Format**: FASTA amino acid sequences (.faa)
- **Naming**: One file per strain, named with strain identifiers
- **Location**: All files in a single directory (e.g., `genomes/`)
- **Example**: `MIT_9107_GCF_000759855.1.faa`, `MED4_GCF_000011465.1.faa`

### HMM Profile File (from pathway_profiler)
- **Format**: HMMER3 profile file (.hmm)
- **Source**: Generated by `solaris pathway_profiler get-profiles`
- **Content**: Pfam domain profiles for target pathway
- **Example**: `selected_pfam.hmm`

### EC-Pfam Mapping File (from pathway_profiler)
- **Format**: Tab-separated values (.txt)
- **Source**: Generated by `solaris pathway_profiler extract-ec`
- **Columns**: `EC_number`, `UniProt_ID`, `Protein_Name`, `Pfam_ID`, `Species`
- **Example**: `pfam_ids.txt`

### Target EC Numbers (Optional)
- **Format**: Plain text file
- **Content**: One EC number per line (with or without "EC:" prefix)
- **Example**:
  ```
  1.1.1.1
  2.3.1.15
  4.2.1.2
  ```

## Output Files

### Analysis Results
- `comparison_matrix.csv`: Strain × EC presence/absence matrix
- `strain_rankings.csv`: Strain completeness rankings with detailed metrics
- `results/batch/*.csv`: Individual strain EC analysis results
- `strain_similarity.csv`: Pairwise similarity metrics (if requested)

### Visualizations

**Standard Plots:**
- `comparison_heatmap.png`: EC presence/absence heatmap with strain clustering
- `completeness_distribution.png`: Strain completeness score distributions
- `ec_frequency_plot.png`: EC number frequency across strains
- `top_strains_plot.png`: Top-performing strains visualization

**Advanced Clustering Plots (--clustered-plots):**
- `strain_dendrogram.png`: Hierarchical clustering dendrogram
- `clustered_heatmap.png`: Heatmap with both strain and EC clustering
- `similarity_matrix.png`: Strain similarity matrix visualization
- `cluster_analysis.png`: Cluster validation and statistics

**Large Dataset Optimizations:**
- Automatic label hiding for >50 strains
- Adaptive plot sizing based on data volume
- Intelligent clustering for readability

## Complete Workflow Overview

```
Prerequisites (pathway_profiler):
├── Extract EC-Pfam mapping from KEGG pathway
├── Generate HMM profiles from Pfam database
└── Validate files with check-prerequisites

Pangenomic Analysis:
1. HMM Analysis (Step 2)
   ├── Load genome protein sequences (.faa files)
   ├── Search against HMM profiles using pyhmmer
   ├── Map Pfam hits to EC numbers
   ├── Generate individual strain result files
   └── Process all strains in directory

2. Matrix Creation (Step 3)
   ├── Read individual strain EC results
   ├── Create strain × EC comparison matrix
   ├── Calculate completeness scores per strain
   ├── Rank strains by pathway completeness
   └── Generate strain similarity metrics

3. Visualization
   ├── Standard plots (heatmaps, distributions)
   ├── Advanced clustering plots (dendrograms, similarity)
   ├── Large dataset optimizations (label management)
   └── Export all plots and results

Integration:
└── Seamless workflow with pathway_profiler for complete analysis
```

## Performance Considerations

- **Large Datasets**: Tested with 122 strains - handles 100+ strains efficiently
- **Visualization Scaling**: Intelligent crowding management for readability
- **Memory Optimization**: Processes strains individually to manage memory usage
- **HMM Search**: Uses optimized pyhmmer implementation with original working logic
- **File I/O**: Efficient batch processing of individual strain result files

## Error Handling

The module includes comprehensive error handling:
- **Input Validation**: Checks for required files and proper formats
- **Missing Dependencies**: Validates pyhmmer, pandas, matplotlib availability
- **File Processing**: Graceful handling of missing or corrupted genome files
- **Detailed Logging**: Comprehensive logging with progress indicators
- **Prerequisite Checking**: Built-in validation of workflow requirements

## Dependencies

**Core dependencies:**
- `pyhmmer`: Fast HMM profile searching
- `pandas`: Data manipulation and CSV handling
- `matplotlib`: Base plotting functionality
- `seaborn`: Statistical visualizations and styling
- `numpy`: Numerical computations
- `scipy`: Hierarchical clustering and statistics

**System requirements:**
- Python 3.7+
- HMMER3 tools (for HMM profile generation via pathway_profiler)
- Sufficient memory for large strain datasets

## Integration with pathway_profiler

The pangenomic analyzer is designed to work seamlessly with pathway_profiler:

```bash
# Complete end-to-end workflow
# 1. Extract pathway information
solaris pathway_profiler extract-ec --pathway map00720 --output pfam_ids.txt

# 2. Generate HMM profiles  
solaris pathway_profiler get-profiles --input pfam_ids.txt --pfam-db /path/to/pfam --output selected_pfam.hmm

# 3. Run pangenomic analysis
solaris pangenomic_analyzer complete --genomes-dir genomes/ --hmm-file selected_pfam.hmm --ec-pfam-mapping pfam_ids.txt --clustered-plots
```

## Examples and Testing

The module has been tested with:
- **122 Synechococcus strains** for carbon fixation pathway analysis (map00720)
- **Various pathway sizes** from simple (few ECs) to complex (many ECs)
- **Different visualization scenarios** with automatic crowding management

For sample data and complete examples, see the `examples/` directory or test with the provided Synechococcus dataset.