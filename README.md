# Team Evry-Paris-Saclay 2025 Software Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![iGEM 2025](https://img.shields.io/badge/iGEM-2025-orange.svg)](https://2025.igem.wiki/evry-paris-saclay/)

## Description

**SOLARIS** is a comprehensive bioinformatics toolkit designed for **metabolic engineering** and **synthetic biology** applications. It enables researchers to identify optimal microbial hosts for heterologous pathway implementation through advanced genomic analysis, pathway profiling, and economic optimization.

Developed by **Team Evry-Paris-Saclay** for iGEM 2025, SOLARIS addresses critical challenges in metabolic engineering by providing integrated tools for pathway analysis, strain comparison, product valorization, and AI-assisted workflow automation. Visit our [team wiki](https://2025.igem.wiki/evry-paris-saclay/) for project context and results.

### Key Features

**🧬 Pathway Profiler** 📁 [`solaris/pathway_profiler/`](solaris/pathway_profiler/README.md)
- Extract enzyme information from KEGG pathways and modules
- Retrieve protein sequences and Pfam domain annotations from UniProt
- Generate custom HMM profiles for pathway-specific protein families
- Screen target genomes for pathway enzymes using sensitive HMM searches
- Create interactive pathway completion plots and enzyme distribution analysis

**🔍 Pangenomic Analyzer** 📁 [`solaris/pangenomic_analyzer/`](solaris/pangenomic_analyzer/README.md)
- Analyze pathway completeness across 100+ bacterial strains simultaneously
- Perform hierarchical clustering and similarity analysis for strain selection
- Generate scalable visualizations with intelligent plot management for large datasets
- Rank strains by pathway completeness scores with comprehensive reporting

**🧪 Compatibility Predictor** 📁 [`solaris/compatibility_predictor/`](solaris/compatibility_predictor/README.md)
- Extract genes associated with target EC numbers from KEGG database
- Filter candidate organisms using user-defined criteria from BacDive database
- Match organisms across databases using rigorous NCBI taxonomy ID validation
- Apply physiological filters (oxygen tolerance, temperature range, growth conditions)
- Generate compatibility reports for heterologous pathway implementation feasibility

**💰 Product Valorization** 📁 [`solaris/product_valorization/`](solaris/product_valorization/README.md)
- Enumerate sub-pathways with energetic cost modeling using KEGG data
- Rank metabolic routes by ATP usage, redox balance, and reaction complexity
- Analyze pyruvate valorization to convert excess metabolites into valuable products
- Assess O₂ consumption, CO₂ release, and literature precedent for pathway feasibility

**🤖 BIOMERA (BioProd Agent)** 📁 [`/biomera/`](biomera/README.md)
- Chatbot-style AI agent that automates SOLARIS workflows and runs Solaris commands on your behalf.
- Public chatbot UI: https://solaris-chatbot-wwd4.onrender.com/
- BIOMERA converts natural-language instructions into validated command plans, executes them in controlled executors (local sandbox or Docker), and returns both an explanation and the raw terminal output.
- For full usage, deployment notes (Docker / Render) and developer details see `biomera/README.md`.

You may refer to each of these directories for comprehensive documentation of each feature in their corresponding **README.md**.

### Background

SOLARIS addresses fundamental challenges in **strain selection** and **pathway optimization** for metabolic engineering. Traditional approaches require manual analysis of individual genomes and pathways, which is time-consuming and error-prone when working with large datasets. Our toolkit automates this process while adding economic analysis and AI-powered workflow management. Our work remains in progress.

**Differentiating Factors:**
- **Integrated workflow**: Seamless integration from pathway extraction to strain ranking to economic analysis
- **Large-scale analysis**: Tested with 122+ strains with intelligent visualization management
- **Economic modeling**: First tool to integrate bioenergetic cost analysis with pathway screening
- **AI automation**: First bioinformatics toolkit with integrated AI agent for workflow automation
- **Open source**: Fully open-source with comprehensive documentation and examples

## Installation

### Requirements

SOLARIS requires Python 3.8 or higher and has been tested on Linux, macOS, and Windows (via WSL). The following system dependencies are required:

- **Python 3.8+** (tested with Python 3.8-3.11)
- **HMMER3** (for HMM profile searching)
- **Docker** (for BIOMERA AI agent functionality)
- **Internet connection** (for KEGG and UniProt data retrieval)

Optional dependencies:
- **Ollama** (for local AI models in BIOMERA)
- **Pfam database** (download from [Pfam FTP](http://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/))

### Installation Steps

1. **Clone the repository**
```bash
git clone https://gitlab.igem.org/2025/software-tools/evry-paris-saclay.git
cd evry-paris-saclay
```

2. **Install Python dependencies**
```bash
pip install -e .
```

3. **Install HMMER3** (required for HMM searching)
```bash
# Ubuntu/Debian
sudo apt-get install hmmer

# macOS with Homebrew
brew install hmmer

# Conda (all platforms)
conda install -c bioconda hmmer
```

4. **Install Docker** (for BIOMERA AI agent)
```bash
# Follow instructions at https://docs.docker.com/engine/install/
# Ensure Docker is running and accessible
docker --version
```

5. **Set up BIOMERA** (optional, for AI agent functionality)
```bash
cd biomera/
pip install -r requirements.txt

# For local AI models, install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral
```

6. **Verify installation**
```bash
solaris --help
python -c "import solaris; print('SOLARIS installed successfully')"
```

## Usage

### Basic Usage

The simplest way to use SOLARIS is through the complete workflow command. Here's a minimal example analyzing carbon fixation pathways across Synechococcus strains:

```bash
# Complete workflow: pathway extraction → HMM generation → strain analysis
# Step 1: Extract pathway enzymes from KEGG
solaris pathway_profiler extract-ec --pathway 00720 --output pfam_ids.txt

# Step 2: Generate HMM profiles
solaris pathway_profiler get-profiles \
    --input pfam_ids.txt \
    --pfam-db /path/to/pfam \
    --output selected_pfam.hmm

# To obtain proteomes from NCBI, you may run `access_genomes.py`, or setup your own genomes directory with .faa files.
# By default, a comprehensive list of cyanobacteria strains will be downloaded to genomes/ directory if no parameters are given to `access_genomes.py`.
python access_genomes.py -s synechococcus -o synechococcus_proteomes

# Step 3: Analyze all strains
solaris pangenomic_analyzer complete \
    --genomes-dir synechoccocus_proteomes/ \
    --hmm-file selected_pfam.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --target-ecs ec_numbers.txt \
    --plot
```

**Expected Output:**
```
Analyzing 122 strains for carbon fixation pathway (map00720)...
✓ Found 21 target enzymes in pathway
✓ Generated HMM profiles for 45 Pfam domains
✓ Completed analysis for 122/122 strains
✓ Top strain: MIT_9107 (95.2% pathway completeness)
✓ Generated clustered heatmap and dendrogram plots
```

### Individual Module Examples

**1. Pathway Profiler - Single Genome Analysis**
```bash
# Complete workflow for one genome
solaris pathway_profiler workflow \
    --pathway 00720 \
    --genome target_genome.faa \
    --pfam-db /path/to/pfam \
    --output-dir results/ \
    --plot
```
Output: EC coverage analysis, pathway completion plots, enzyme distribution charts

**2. Pangenomic Analyzer - Compare Multiple Strains**
```bash
# Multi-strain comparison with clustering
solaris pangenomic_analyzer complete \
    --genomes-dir genomes/ \
    --hmm-file profiles.hmm \
    --ec-pfam-mapping pfam_ids.txt \
    --target-ecs ec_numbers.txt \
    --plot
```
Output: Strain rankings, comparison matrix, hierarchical clustering dendrograms

**3. Compatibility Predictor - Organism Matching**
```bash
# Match organisms between KEGG and BacDive databases
solaris compatibility_predictor match \
    --kegg-file kegg_organisms.json \
    --bacdive-file bacdive_data.json \
    --email your.email@example.com \
    --output matched_organisms.json
```
Output: Cross-referenced organism database with taxonomy validation and physiological compatibility scores

**4. Product Valorization - Economic Analysis**
```python
# Analyze pyruvate valorization options
import solaris.product_valorization.search as search
search.visualize_best_subpathway("map00720", "C00022")  # Opens KEGG browser
```
Output: Economic pathway ranking, KEGG pathway visualization with highlighted routes

Under development, for now you may run `demo.py`.

**5. BIOMERA AI Agent - Automated Workflow**
```bash
cd biomera/
python main.py
```
```
🤖 BIOMERA: How can I help with your bioproduction analysis?
User: Analyze carbon fixation in Synechococcus and find the best strains
🤖 BIOMERA: Running complete SOLARIS workflow...
    → Extracting KEGG pathway map00720
    → Generating HMM profiles  
    → Analyzing 122 genomes
    → Ranking strains by completeness
    ✓ Complete! Top strain: MIT_9107 (95.2%)
```

## Expected Outputs

You may refer to the `tests/` directory for an overview of the outputs of each feature:

- **`tests/pathway_analysis_results/`** - EC coverage analysis, HMM profiles, pathway completion plots, detailed hits reports generated by `pathway_profiler`
- **`tests/pangenomic_analysis_results/`** - Cross-genome analysis results with plots and detailed strain comparisons generated by `pangenomic_analyzer`
- **`tests/compatibility_analysis_results/`** - KEGG-BacDive organism matching, taxonomy validation, physiological filtering results generated by `compatibility_predictor`
- **`tests/example/`** - Complete workflow simple case example with all intermediate files and outputs
- **`tests/cyanobacteria_proteomes/`** - Sample proteome dataset for testing (.faa files excluded); you may replicate the same data by running `python solaris/pangenomic_analyzer/access_genomes.py -o cyanobacteria_proteomes`

### Advanced Usage Examples

**Custom Pathway Analysis:**
```bash
# Analyze user-defined enzyme list
echo -e "1.1.1.1\n2.3.1.15\n4.2.1.2" > my_enzymes.txt
solaris pathway_profiler extract-ec --pathway my_enzymes.txt --output custom_pfam.txt
```

**Large Dataset Processing:**
```bash
# Optimize for 200+ genomes
solaris pangenomic_analyzer complete \
    --genomes-dir massive_dataset/ \
    --parallel --max-workers 16 \
    --hmm-file profiles.hmm \
    --ec-pfam-mapping pfam_ids.txt
```

## Contributing

We welcome contributions from the bioinformatics and synthetic biology communities! SOLARIS is designed to be extensible and we encourage community involvement to expand its capabilities.

### Development Workflow

1. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** 

3. **Commit your changes** with descriptive messages
   ```bash
   git add .
   git commit -m "Add feature: brief description of what you added"
   ```

4. **Push and create a merge request**

### Areas We're Looking For Help

- **New pathway databases**: Integration with BioCyc, Reactome, MetaCyc
- **Alternative search algorithms**: BLAST, Diamond, MMseqs2 integration  
- **Enhanced visualizations**: Interactive plots, web dashboards, 3D pathway maps
- **Performance improvements**: Parallel processing, caching, memory optimization
- **AI agent capabilities**: New biotechnology tools, improved reasoning, workflow templates
- **Economic modeling**: Thermodynamic feasibility, toxicity assessment, market analysis
- **Platform support**: Windows native support, cloud deployment, containerization
- **Documentation**: Tutorials, video guides, translated documentation

## Authors and acknowledgment

### Team Evry-Paris-Saclay 2025

**SOLARIS** was developed by Team Evry-Paris-Saclay for iGEM 2025 as our contribution to advancing metabolic engineering and synthetic biology research.

### Acknowledgments

We extend our gratitude to the following contributors:

- **Georgy** - [@georgyzaouk](https://github.com/georgyzaouk)
- **Akshay** - [@crakshay1](https://github.com/crakshay1)
- **Yazid** - [@yazid-hoblos](https://github.com/yazid-hoblos)
- **Colombe** - [@colombearchambaud](https://github.com/colombearchambaud)
- **Matheo** - [@paradoxe-tech](https://github.com/paradoxe-tech)
- **Ada** - [@adaozin](https://github.com/adaozin)
- **Kenan**

### Citation

If you use SOLARIS in your research, please cite our work:

```bibtex
@software{evry_paris_saclay_2025,
  title={SOLARIS: Toolkit for Heterologous Pathway Transfer for Metabolic Engineering},
  author={Team Evry-Paris-Saclay},
  year={2025},
  organization={iGEM Foundation},
  url={https://gitlab.igem.org/2025/software-tools/evry-paris-saclay/},
  note={iGEM 2025 Software Tools Competition}
}
```

### Links

- **[Team Wiki](https://2025.igem.wiki/evry-paris-saclay/)** - Complete project documentation and results
- **[GitLab Repository](https://gitlab.igem.org/2025/software-tools/evry-paris-saclay/)** - Source code and development
- **[Software & AI Village](https://villages.igem.org)** - iGEM software community
- **[iGEM 2025](https://2025.igem.wiki/)** - International Genetically Engineered Machine competition
