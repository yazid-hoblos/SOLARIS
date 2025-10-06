# Pangenomic Analyzer

The **Pangenomic Analyzer** module provides comprehensive tools for analyzing pathway completeness across multiple bacterial strains using HMM (Hidden Markov Model) profiles.

## Features

- **Strain Management**: Load, filter, and batch process multiple genome files
- **HMM Analysis**: Parallel processing of protein sequences against HMM profiles
- **Pathway Analysis**: Comprehensive EC number coverage analysis and strain ranking
- **Visualization**: Rich plotting capabilities with heatmaps, statistical plots, and dashboards
- **Similarity Analysis**: Calculate pairwise strain similarities using multiple metrics

## Architecture

The module follows object-oriented design with specialized classes:

- **StrainManager**: Handles strain data loading and management
- **BatchAnalyzer**: Processes multiple strains with parallel HMM searching
- **PathwayAnalyzer**: Analyzes pathway completeness and strain comparisons
- **VisualizationManager**: Creates comprehensive visualization plots

## Installation

The pangenomic analyzer is installed as part of the Solaris package:

```bash
pip install -e .
```

## Prerequisites

Before running pangenomic analysis, generate required files using pathway_profiler:

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
# Complete analysis with visualization
solaris pangenomic_analyzer complete \
    --genomes-dir ./genomes \
    --hmm-file selected_pfam.hmm \
    --target-ecs ec_numbers.txt \
    --ec-pfam-mapping pfam_ids.txt \
    --plot \
    --parallel \
    --max-workers 4
```

### Step-by-Step Analysis

For more control over the analysis process:

```bash
# Step 1: Analyze strains and create processing batches
solaris pangenomic_analyzer strains \
    --genomes-dir ./genomes \
    --batch-size 10 \
    --strain-list target_strains.txt

# Step 2: Run HMM analysis on all strains
solaris pangenomic_analyzer hmm \
    --genomes-dir ./genomes \
    --hmm-file selected_pfam.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --parallel \
    --max-workers 4

# Step 3: Analyze pathway completeness and create visualizations
solaris pangenomic_analyzer pathways \
    --hmm-results hmm_results.csv \
    --target-ecs ec_numbers.txt \
    --plot \
    --similarity-analysis
```

### Advanced Step-by-Step Commands

For users familiar with the original tmp/ scripts:

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

# Load and filter strains
strains_df = strain_manager.load_strains("genomes/")
filtered_strains = strain_manager.filter_strains(strains_df, target_strains)

# Create batches for processing
batches = strain_manager.create_strain_batches(filtered_strains, batch_size=10)

# Run HMM analysis
results = []
for batch in batches:
    batch_results = batch_analyzer.batch_analyze_strains(
        batch, "pfam.hmm", max_workers=4
    )
    results.extend(batch_results)

# Analyze pathway completeness
ec_coverage = pathway_analyzer.analyze_ec_coverage(results, target_ecs)
comparison_matrix = pathway_analyzer.create_comparison_matrix(ec_coverage)
strain_rankings = pathway_analyzer.rank_strains_by_completeness(ec_coverage)

# Generate visualizations
plot_files = viz_manager.generate_all_plots(
    strain_rankings, comparison_matrix
)
```

### Advanced Features

```python
# Calculate strain similarity
similarity_df = pathway_analyzer.calculate_strain_similarity(ec_coverage)

# Custom visualization
heatmap_file = viz_manager.plot_pangenome_heatmap(comparison_matrix)
completeness_plot = viz_manager.plot_strain_completeness(strain_rankings)
dashboard = viz_manager.create_summary_dashboard(
    strain_rankings, comparison_matrix
)

# Strain filtering and selection
top_performers = pathway_analyzer.get_top_strains(strain_rankings, n=10)
strain_clusters = pathway_analyzer.cluster_strains_by_similarity(similarity_df)
```

## Input Files

### Genome Files
- **Format**: FASTA amino acid sequences (.faa)
- **Location**: One file per strain in a single directory
- **Naming**: Files should be named with strain identifiers
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

### Target EC Numbers
- **Format**: Plain text file
- **Content**: One EC number per line (with or without "EC:" prefix)
- **Example**:
  ```
  1.1.1.1
  2.3.1.15
  4.2.1.2
  ```

### Strain List (Optional)
- **Format**: Plain text file
- **Content**: One strain name per line
- **Purpose**: Filter specific strains for analysis

## Output Files

### Analysis Results
- `comparison_matrix.csv`: Strain × EC presence/absence matrix
- `strain_rankings.csv`: Strain completeness rankings with detailed metrics
- `results/batch/*.csv`: Individual strain EC analysis results (step2-hmm output)
- `strain_similarity.csv`: Pairwise similarity metrics (if requested)

### Visualizations

**Standard Plots:**
- `comparison_heatmap.png`: EC presence/absence heatmap
- `completeness_distribution.png`: Strain completeness score distributions  
- `ec_frequency_plot.png`: EC number frequency across strains
- `top_strains_plot.png`: Top-performing strains visualization

**Advanced Clustering Plots (--clustered-plots):**
- `strain_dendrogram.png`: Hierarchical clustering dendrogram
- `clustered_heatmap.png`: Heatmap with strain and EC clustering
- `similarity_matrix.png`: Strain similarity matrix visualization
- `cluster_analysis.png`: Cluster validation and statistics

**Large Dataset Features:**
- Automatic label management for datasets with >50 strains
- Adaptive plot sizing based on data volume
- Intelligent clustering for improved readability

## Complete Workflow Overview

```
Prerequisites (pathway_profiler):
├── Extract EC-Pfam mapping from KEGG pathway
├── Generate HMM profiles from Pfam database
└── Validate required files

Pangenomic Analysis:
1. Strain Management
   ├── Load genome files from directory (.faa)
   ├── Filter by strain list (optional)
   └── Validate file formats and accessibility

2. HMM Analysis (step2-hmm)
   ├── Search proteins against HMM profiles using pyhmmer
   ├── Map Pfam hits to EC numbers using mapping file
   ├── Generate individual strain result files
   └── Process all strains with parallel support

3. Matrix Creation (step3-matrix)
   ├── Read individual strain EC results
   ├── Create strain × EC comparison matrix
   ├── Calculate completeness scores per strain
   ├── Rank strains by pathway completeness
   └── Generate strain similarity metrics

4. Advanced Visualization
   ├── Standard plots (heatmaps, distributions)
   ├── Hierarchical clustering analysis
   ├── Large dataset optimization (100+ strains)
   └── Export comprehensive results

Integration:
└── Seamless workflow with pathway_profiler for end-to-end analysis
```

## Performance Considerations

- **Large Datasets**: Successfully tested with 122+ strains - handles large datasets efficiently
- **Parallel Processing**: Use `--parallel` with `--max-workers` for faster HMM analysis
- **Visualization Scaling**: Intelligent crowding management for datasets with many strains
- **Memory Optimization**: Individual strain processing to manage memory usage
- **HMM Search**: Optimized pyhmmer implementation for fast protein domain searches

## Error Handling

The module includes comprehensive error handling:
- Input file validation
- Missing dependency checks  
- Memory and processing error recovery
- Detailed logging with timestamps

## Dependencies

Core dependencies:
- `pyhmmer`: HMM searching
- `pandas`: Data manipulation
- `matplotlib`: Plotting
- `seaborn`: Statistical visualizations
- `numpy`: Numerical computations

Optional dependencies:
- `concurrent.futures`: Parallel processing
- `pathlib`: Path handling

## Integration with pathway_profiler

The pangenomic analyzer is designed to work seamlessly with pathway_profiler:

```bash
# Complete end-to-end workflow
# 1. Extract pathway information
solaris pathway_profiler extract-ec --pathway map00720 --output pfam_ids.txt

# 2. Generate HMM profiles
solaris pathway_profiler get-profiles --input pfam_ids.txt --pfam-db /path/to/pfam --output selected_pfam.hmm

# 3. Run pangenomic analysis
solaris pangenomic_analyzer complete --genomes-dir genomes/ --hmm-file selected_pfam.hmm --target-ecs ec_numbers.txt --ec-pfam-mapping pfam_ids.txt --plot
```

## Examples and Testing

The module has been tested with:
- **122 Synechococcus strains** for carbon fixation pathway analysis (map00720)
- **Various pathway complexities** from simple to multi-enzyme pathways
- **Different visualization scenarios** with automatic optimization

For complete examples and sample datasets, see the `examples/` directory.