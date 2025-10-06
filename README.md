# SOLARIS - Toolkit for Heterologous Pathway Transfer for Metabolic Engineering

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![iGEM 2025](https://img.shields.io/badge/iGEM-2025-orange.svg)](https://2025.igem.wiki/evry-paris-saclay/)

**SOLARIS** is a comprehensive bioinformatics toolkit designed for **metabolic engineering** and **synthetic biology** applications. It enables researchers to identify optimal microbial hosts for heterologous pathway implementation through advanced genomic analysis and pathway profiling.

> Developed by **Team Evry-Paris-Saclay** for iGEM 2025 - [Visit our Wiki](https://2025.igem.wiki/evry-paris-saclay/)

## 🚀 Key Features

### 🧬 **Pathway Profiler**
- **KEGG Pathway Integration**: Extract enzyme information from KEGG pathways and modules
- **UniProt Data Mining**: Retrieve protein sequences and Pfam domain annotations
- **HMM Profile Generation**: Create custom HMM profiles for pathway-specific protein families
- **Genome Screening**: Search target genomes for pathway enzymes using sensitive HMM searches
- **Interactive Visualization**: Generate pathway completion plots and enzyme distribution analysis

### 🔍 **Pangenomic Analyzer**
- **Multi-Strain Comparison**: Analyze pathway completeness across 100+ bacterial strains simultaneously
- **Advanced Clustering**: Hierarchical clustering and similarity analysis for strain selection
- **Scalable Visualization**: Intelligent plot management for large datasets with automatic crowding control
- **Strain Ranking**: Identify optimal hosts based on pathway completeness scores
- **Comprehensive Reporting**: Generate detailed analysis reports with statistical summaries

### 💰 **Product Valorization**
- **Pathway Economics**: KEGG-driven sub-pathway enumeration with energetic cost modeling
- **Route Optimization**: Rank metabolic routes by ATP usage, redox balance, and complexity
- **Pyruvate Valorization**: Convert excess pyruvate into valuable products (lactate, ethanol, etc.)
- **Bioenergetic Analysis**: Assess O₂ consumption, CO₂ release, and literature precedent
- **Visual Integration**: Highlight optimal pathways on KEGG pathway maps

### 🤖 **BIOMERA (BioProd Agent)**
- **AI-Powered Automation**: World-first bioproduction AI agent specialized in molecular biology tasks
- **Task Automation**: Automate complex biotechnology workflows for non-experts
- **Tool Integration**: Run any biotool through Docker container execution
- **Pipeline Management**: Design pathways, run analyses, and enhance molecules automatically
- **Flexible Deployment**: Local models (Ollama) or cloud-based AI services


### 🎯 **End-to-End Workflow**
- **Seamless Integration**: pathway_profiler outputs feed into pangenomic_analyzer and product_valorization
- **AI-Assisted Analysis**: BIOMERA can automate entire analysis pipelines
- **Automated Processing**: Complete pathway-to-strain-to-economics analysis
- **Flexible Usage**: Run individual modules or complete workflows based on your needs
- **Batch Processing**: Handle large genomic datasets efficiently

## 🔬 Scientific Applications

SOLARIS addresses critical challenges in **metabolic engineering**:

- **Host Selection**: Identify bacterial strains with highest native pathway completeness
- **Gap Analysis**: Determine missing enzymes needed for pathway implementation
- **Comparative Genomics**: Compare pathway presence across diverse microbial species
- **Strain Engineering**: Guide targeted genetic modifications for pathway optimization

**Use Cases:**
- 🌱 **Biofuel Production**: Find optimal hosts and economically viable pathways for renewable fuels
- 💊 **Pharmaceutical Manufacturing**: Screen for natural product biosynthesis with cost optimization
- 🧪 **Industrial Biotechnology**: Identify strains and valorize byproducts for chemical production
- 🌿 **Carbon Fixation**: Analyze CO₂ fixation pathways and pyruvate valorization strategies
- 🤖 **Automated Research**: Let AI agents handle complex multi-tool bioinformatics workflows
- 💰 **Economic Optimization**: Evaluate pathway economics and metabolite valorization potential

## 📦 Installation

### Requirements
- **Python 3.8+** (tested with Python 3.8-3.11)
- **HMMER3** (for HMM profile searching)
- **Docker** (for BIOMERA AI agent functionality)
- **Ollama** (optional, for local AI models in BIOMERA)
- **Internet connection** (for KEGG and UniProt data retrieval)

### Quick Install

```bash
# Clone the repository
git clone https://gitlab.igem.org/2025/software-tools/evry-paris-saclay.git
cd evry-paris-saclay

# Install SOLARIS and dependencies
pip install -e .

# Verify installation
solaris --help
```

### System Dependencies

**Install HMMER3 (required for HMM searching):**

```bash
# Ubuntu/Debian
sudo apt-get install hmmer

# macOS
brew install hmmer

# Conda (all platforms)
conda install -c bioconda hmmer
```

### Development Install

For developers who want to contribute:

```bash
# Install with development dependencies
pip install -e ".[dev,docs]"

# Run tests
pytest tests/

# Format code
black solaris/
flake8 solaris/
```

## 🚀 Quick Start

### Complete Workflow Example

Analyze carbon fixation pathway (Calvin cycle) across Synechococcus strains:

```bash
# Step 1: Extract pathway information from KEGG
solaris pathway_profiler extract-ec --pathway map00720 --output pfam_ids.txt

# Step 2: Generate HMM profiles for pathway enzymes
solaris pathway_profiler get-profiles \
    --input pfam_ids.txt \
    --pfam-db /path/to/pfam \
    --output selected_pfam.hmm

# Step 3: Analyze pathway completeness across all strains
solaris pangenomic_analyzer complete \
    --genomes-dir genomes/ \
    --hmm-file selected_pfam.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --clustered-plots
```

### Individual Module Usage

**Pathway Profiler - Single Genome Analysis:**
```bash
# Complete workflow for one genome
solaris pathway_profiler workflow \
    --pathway map00720 \
    --genome target_genome.faa \
    --pfam-db /path/to/pfam \
    --output-dir results/ \
    --plot
```

**Pangenomic Analyzer - Multi-Strain Comparison:**
```bash
# Compare pathway presence across multiple strains
solaris pangenomic_analyzer complete \
    --genomes-dir genomes/ \
    --hmm-file pathway_profiles.hmm \
    --ec-pfam-mapping enzyme_mapping.txt \
    --plot
```

**BIOMERA AI Agent - Automated Analysis:**
```bash
# Start the AI agent for interactive biotechnology tasks
cd biomera/
python main.py

# Or run specific tasks through the API
python api.py
```

**Product Valorization - Economic Route Analysis:**
```python
# Find and rank pyruvate valorization pathways
import solaris.product_valorization.search as search

# Analyze pyruvate valorization in carbon fixation pathway
search.visualize_best_subpathway("map00720", "C00022")  # pyruvate

# Get cost analysis for specific pathways
import solaris.product_valorization.cost as cost
pathway_cost, details = cost.subpathway_cost_relative([("R00959", 1)])
```

### Expected Output

**Analysis Results:**
- `comparison_matrix.csv` - Strain × enzyme presence/absence matrix
- `strain_rankings.csv` - Strains ranked by pathway completeness
- `pfam_ids.txt` - EC-Pfam domain mappings

**Visualizations:**
- `comparison_heatmap.png` - Pathway completeness heatmap
- `strain_dendrogram.png` - Hierarchical clustering of strains
- `completeness_distribution.png` - Pathway completeness statistics

## 📊 Example Results

```
Top 5 Strains by Pathway Completeness:
1. MIT_9107_GCF_000759855.1    - 95.2% complete (20/21 enzymes)
2. MED4_GCF_000011465.1        - 90.5% complete (19/21 enzymes) 
3. AS9601_GCF_000015645.1      - 85.7% complete (18/21 enzymes)
4. CCMP1375_GCF_000007925.1    - 81.0% complete (17/21 enzymes)
5. MIT_9123_GCF_000759935.1    - 76.2% complete (16/21 enzymes)

Average pathway completeness: 73.4%
Strains with >80% completeness: 23/122 (18.9%)
```

## 🏗️ Project Structure

```
solaris/
├── cli.py                    # Main CLI entry point
├── pathway_profiler/         # Pathway analysis module
│   ├── keggModuleDiscoverer.py   # KEGG pathway extraction
│   ├── uniprotHandler.py        # UniProt data retrieval
│   ├── pfamHandler.py           # HMM profile generation
│   ├── hmmSearcher.py           # Genome searching
│   └── mapping_analysis.py     # Results analysis
├── pangenomic_analyzer/      # Multi-strain comparison module
│   ├── strain_manager.py        # Strain data management
│   ├── batch_analyzer.py        # HMM batch processing
│   ├── pathway_analyzer.py      # Pathway completeness analysis
│   └── visualization_manager.py # Advanced plotting
├── product_valorization/     # Economic pathway analysis
│   ├── search.py                # Sub-pathway enumeration
│   ├── cost.py                  # Energetic cost modeling
│   └── demo.py                  # Usage examples
└── tests/                    # Test suite

biomera/                      # AI Agent (separate application)
├── main.py                   # Agent entry point
├── api.py                    # Web API interface
├── model/                    # AI model configurations
├── config/                   # Agent settings
└── utils/                    # Supporting utilities
```

## 🔧 Advanced Usage

### Custom Pathway Analysis

```bash
# Analyze custom enzyme list
echo -e "1.1.1.1\n2.3.1.15\n4.2.1.2" > custom_enzymes.txt

solaris pathway_profiler extract-ec \
    --pathway custom_enzymes.txt \
    --output custom_pfam_ids.txt
```

### Large Dataset Processing

```bash
# Handle 100+ strains with optimized settings
solaris pangenomic_analyzer complete \
    --genomes-dir large_dataset/ \
    --hmm-file profiles.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --parallel \
    --max-workers 8 \
    --clustered-plots
```

### Advanced Module Integration

```bash
# Economic analysis of top strains from pangenomic analysis
# 1. Find best strains
solaris pangenomic_analyzer complete --genomes-dir genomes/ --hmm-file profiles.hmm --ec-pfam-mapping pfam_ids.txt

# 2. Analyze valorization potential for excess metabolites
python -c "
import solaris.product_valorization.search as search
search.visualize_best_subpathway('map00720', 'C00022')  # pyruvate valorization
"

# 3. Use BIOMERA to automate the entire workflow
cd biomera/
python main.py
# Tell agent: 'Analyze carbon fixation pathways in Synechococcus strains and find pyruvate valorization routes'
```

### Integration with External Tools

SOLARIS outputs are compatible with:
- **R/Bioconductor** - CSV matrices for statistical analysis
- **Cytoscape** - Network analysis of strain relationships  
- **KEGG Mapper** - Enhanced pathway visualization with cost annotations
- **PhyloTree** - Phylogenetic analysis integration
- **Docker Ecosystem** - All biotools accessible through BIOMERA agent
- **Web APIs** - BIOMERA provides RESTful access to all functionalities

## 🧪 Testing and Validation

The toolkit has been validated with:
- **122 Synechococcus strains** for carbon fixation analysis
- **Multiple KEGG pathways** including biosynthesis and central metabolism
- **Various genome sizes** from 1.5 Mb to 10+ Mb
- **Cross-platform compatibility** (Linux, macOS, Windows/WSL)

Run the test suite:
```bash
pytest tests/ -v
pytest tests/test_pathway_profiler.py::test_kegg_extraction
pytest tests/test_pangenomic_analyzer.py::test_strain_comparison
```

## 📚 Documentation

- **[Pathway Profiler Guide](solaris/pathway_profiler/README.md)** - Detailed pathway analysis documentation
- **[Pangenomic Analyzer Guide](solaris/pangenomic_analyzer/README.md)** - Multi-strain comparison manual
- **[BIOMERA Agent Guide](biomera/README.md)** - AI agent setup and usage instructions  
- **[Product Valorization Guide](solaris/product_valorization/README.md)** - Economic pathway analysis manual
- **[API Reference](docs/)** - Complete API documentation
- **[Examples](examples/)** - Tutorial notebooks and sample datasets

## 🤝 Contributing

We welcome contributions from the bioinformatics and synthetic biology communities!

### Development Setup

```bash
# Fork the repository and clone
git clone https://gitlab.igem.org/YOUR_USERNAME/evry-paris-saclay.git
cd evry-paris-saclay

# Create development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[dev]"

# Run tests before making changes
pytest tests/
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Ensure** all tests pass (`pytest tests/`)
5. **Format** code (`black solaris/` and `flake8 solaris/`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** to branch (`git push origin feature/amazing-feature`)
8. **Open** a Merge Request

### Areas for Contribution

- 🧬 **New pathway databases** (BioCyc, Reactome integration)
- 🔍 **Alternative search methods** (BLAST, Diamond)
- 📊 **Advanced visualizations** (interactive plots, web interface)
- 🚀 **Performance optimizations** (parallel processing, caching)
- 🤖 **AI agent enhancements** (new tools, improved reasoning)
- 💰 **Economic modeling** (thermodynamics, toxicity, market prices)
- 🔌 **Tool integrations** (more biotools for BIOMERA)
- 📖 **Documentation** (tutorials, examples, translations)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🏆 Team Evry-Paris-Saclay 2025

**SOLARIS** was developed by Team Evry-Paris-Saclay for iGEM 2025.

### Core Development Team
- **Software Architecture & Implementation**
- **Bioinformatics Algorithm Design**  
- **User Interface & Documentation**
- **Testing & Validation**

### Acknowledgments

- **iGEM Foundation** for providing the platform and support
- **KEGG Database** for pathway information
- **UniProt Consortium** for protein sequence data
- **Pfam Database** for protein family annotations
- **HMMER Development Team** for search algorithms
- **Open Source Community** for foundational tools and libraries

### Citation

If you use SOLARIS in your research, please cite:

```
Team Evry-Paris-Saclay (2025). SOLARIS: Toolkit for Heterologous Pathway Transfer 
for Metabolic Engineering. iGEM 2025 Software Tools. 
https://gitlab.igem.org/2025/software-tools/evry-paris-saclay/
```

## 🔗 Links

- **[Team Wiki](https://2025.igem.wiki/evry-paris-saclay/)** - Project overview and results
- **[GitLab Repository](https://gitlab.igem.org/2025/software-tools/evry-paris-saclay/)** - Source code
- **[iGEM 2025](https://2025.igem.wiki/)** - International Genetically Engineered Machine competition
- **[Software & AI Village](https://villages.igem.org)** - iGEM software community

---
