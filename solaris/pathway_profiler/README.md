# 🧬 Solaris Pathway Profiler - Complete Workflow Guide

## 🚀 Overview

The Solaris Pathway Profiler is a comprehensive tool for analyzing metabolic pathway completeness in genomes using EC number profiling. It combines KEGG pathway data, UniProt protein information, Pfam domain analysis, and HMM searching to determine which enzymes are present in your target organism.

## 📊 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
                           🧬 SOLARIS PATHWAY PROFILER WORKFLOW                      
└─────────────────────────────────────────────────────────────────────────────────────┘

INPUT FILES                     WORKFLOW STEPS                        OUTPUT FILES
                                                                      
 📋 Pathway ID                1️⃣  PATHWAY SELECTION                 
 or Search Term                • Interactive search                  
                               • Direct ID input                      
                               • KEGG API queries                     
                                         |                          
                                         v                          
                               2️⃣  EC NUMBER EXTRACTION              
                               • Parse KEGG pathways/modules         
                               • Extract enzyme codes                 
                               • Validate EC numbers                  
                                         |                            
                                         v                           
                               3️⃣  UNIPROT DATA RETRIEVAL              📊 ec_results.csv    
                               • Query UniProt API                                
                               • Get protein information                          
 🗄️ Pfam-A.hmm                 • Map EC → Pfam domains                 📋 ec_summary.txt  
   Database                              |                                          
                                         v                                             
                               4️⃣  HMM PROFILE EXTRACTION              📈 detailed_hits.csv     
                               • Read Pfam IDs from mapping                    
                               • Extract HMM profiles                 
                               • Create custom HMM database             🎨 Colored      
                                         |                                 Pathway URL  
                                         v                           
 🧬 Target                     5️⃣  GENOME SEARCH                    
   Genome.faa                  • Load HMM profiles & sequences
                               • Run pyhmmer search
                               • Filter by E-value threshold
                                         |
                                         v
                               6️⃣  ANALYSIS & REPORTING
                               • Map hits to EC numbers
                               • Determine pathway completeness
                               • Generate status reports
                               Status: FULLY_FOUND 🟢
                                      PARTIALLY_FOUND 🟡
                                      NOT_FOUND 🔴
                                         |
                                         v
                               7️⃣  VISUALIZATION (Optional)
                               • Generate KEGG pathway maps
                               • Color-code enzyme presence
                               • Create interactive pathway

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 KEY FEATURES                                         
├─────────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ Single command workflow    📊 Comprehensive analysis    🎨 Interactive visualize 
│ 🔍 Interactive pathway search 🧬 Multi-genome support     📋 Detailed reporting    
│ 🚀 Fast HMM searching        🎯 E-value filtering        🌐 KEGG integration      
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## ⚡ Quick Start - Complete Workflow

Run the entire analysis pipeline with a single command:

```bash
# Complete workflow - all steps automated
solaris pathway-profiler workflow \
    --pathway "map00720" \
    --genome "/path/to/genome.faa" \
    --pfam-db "/path/to/Pfam-A.hmm" \
    --output-dir "my_analysis_results" \
    --evalue 1e-5 \
    --visualize 
    --plot

# Interactive pathway selection with search terms (default)
solaris pathway-profiler workflow \
    --pathway "carbon fixation" \
    --genome "/path/to/genome.faa" \
    --pfam-db "/path/to/Pfam-A.hmm" \
    --interactive \ 
    --visualize
```

## 🔄 Workflow Steps

The complete workflow performs these steps automatically:

1. **🔍 Extract EC numbers** from the specified KEGG pathway or module
   - Connects to KEGG API to retrieve pathway information
   - Extracts all EC numbers associated with the pathway
   - Supports both direct pathway IDs and interactive search

2. **🧬 Get protein information** from UniProt database
   - Retrieves protein names and functions for each EC number
   - Maps EC numbers to associated Pfam domains
   - Creates comprehensive EC-to-Pfam mapping file

3. **📊 Extract HMM profiles** from Pfam database
   - Uses `hmmfetch` to extract relevant HMM profiles
   - Creates custom HMM database with only required domains
   - Optimizes search performance

4. **🔎 Search genome** using HMM profiles
   - Uses `pyhmmer` for fast, parallel HMM searching
   - Applies E-value threshold filtering
   - Identifies potential enzyme homologs in the target genome

5. **📈 Analyze results** and determine pathway completeness
   - Maps HMM hits back to original EC numbers
   - Categorizes each EC as FULLY_FOUND, PARTIALLY_FOUND, or NOT_FOUND
   - Generates comprehensive analysis reports

6. **🎨 Generate visualization** (optional) using KEGG Mapper
   - Creates colored KEGG pathway maps
   - Uses Selenium to automate KEGG Mapper website
   - Provides direct links to visualized pathways

## Individual Step Commands

You can still run each step individually if needed:

### 1. Extract EC numbers
```bash
solaris pathway-profiler extract-ec --pathway "map00720" --output "ec_pfam_mapping.txt"
```

### 2. Get HMM profiles
```bash
solaris pathway-profiler get-profiles --input "ec_pfam_mapping.txt" --pfam-db "/path/to/Pfam-A.hmm" --output "selected_pfam.hmm"
```

### 3. Search genome
```bash
solaris pathway-profiler search --hmm "selected_pfam.hmm" --genome "/path/to/genome.faa" --output "hits_table.txt" --evalue 1e-5
```

### 4. Analyze results
```bash
solaris pathway-profiler analyze --hits "hits_table.txt" --input "ec_pfam_mapping.txt" --hmm "selected_pfam.hmm" --output-dir "results"
```

### 5. Visualize (optional)
```bash
solaris pathway-profiler visualize --results "results/ec_results.csv" --headless
```

## 📁 Output Files

The workflow generates a comprehensive set of output files:

### Core Results
- **`ec_results.csv`** - 📊 **Main results file** with pathway completeness analysis
  - Status for each EC number (FULLY_FOUND, PARTIALLY_FOUND, NOT_FOUND)
  - Protein names and functions
  - Pfam domain information
  - Hit statistics and protein IDs

- **`ec_summary.txt`** - 📋 Human-readable summary report
  - Overview of pathway completeness
  - Statistics and enzyme counts
  - Easy-to-read format for quick assessment

### Intermediate Files
- **`ec_pfam_mapping.txt`** - 🔗 EC number to Pfam domain mappings
  - Links EC numbers to required Pfam domains
  - Includes protein names and UniProt information

- **`selected_pfam.hmm`** - 🧬 Custom HMM profile database
  - Contains only the HMM profiles needed for this pathway
  - Optimized for faster searching

- **`hits_table.txt`** - 🎯 Raw HMM search results
  - All significant hits with E-values and scores
  - Direct output from pyhmmer search

### Detailed Analysis
- **`detailed_hits.csv`** - 🔍 Comprehensive hit information
  - Links HMM hits back to EC numbers
  - Detailed protein and domain information
  - Useful for manual curation and validation

## ⚙️ Command Line Arguments

### 🔴 Required Arguments:

- **`--genome`** - Path to target genome file
  - Format: FASTA amino acid sequences (.faa)
  - Should contain all predicted proteins from the organism

- **`--pfam-db`** - Path to Pfam-A.hmm database file
  - Download from: http://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/
  - Must be the complete `Pfam-A.hmm` file (not compressed)

### 🟡 Optional Arguments:
- **`--output-dir`** - Output directory name (default: `"pathway_analysis_results"`)
- **`--evalue`** - E-value threshold for HMM search (default: `1e-5`)
- **`--visualize`** - Generate KEGG pathway visualization (flag)
- **`--headless`** - Run visualization without opening browser (flag)
- **`--interactive`** - Enable interactive pathway selection (flag)
- **`--plot`** - Generate descriptive plots (flag)

### 💡 Usage Tips:
- Use `--interactive` when searching with pathway names for better control
- Set `--evalue 1e-3` for more sensitive searches (more hits, potentially more false positives)
- Use `--headless` for automated pipelines or remote servers
- Specify absolute paths for `--genome` and `--pfam-db` to avoid path issues

## 💻 Usage Examples

### Example 1: 3-Hydroxypropanoate Carbon Fixation Pathway
```bash
# Analyze the 3HP/4HB carbon fixation pathway in Synechococcus
solaris pathway-profiler workflow \
    --pathway "map00720" \
    --genome "genomes/synechococcus_PCC7002.faa" \
    --pfam-db "/databases/Pfam-A.hmm" \
    --output-dir "3HP_carbon_fixation_analysis" \
    --evalue 1e-5 \
    --visualize --headless
```

### Example 2: Interactive Pathway Search
```bash
# Search and select from multiple pathways interactively
solaris pathway-profiler workflow \
    --pathway "reductive citrate cycle" \
    --genome "cyanobacteria_genome.faa" \
    --pfam-db "/home/user/databases/Pfam-A.hmm" \
    --interactive \
    --evalue 1e-3 \
    --output-dir "rTCA_analysis" \
    --visualize
```

### Example 3: High-Throughput Analysis
```bash
# Automated analysis for multiple pathways (using shell loop)
for pathway in "map00720" "map00190" "map00710"; do
    solaris pathway-profiler workflow \
        --pathway "$pathway" \
        --genome "my_organism.faa" \
        --pfam-db "/databases/Pfam-A.hmm" \
        --output-dir "analysis_${pathway}" \
        --headless --visualize
done
```

### Example 4: Sensitive Search
```bash
# More sensitive search with relaxed E-value threshold
solaris pathway-profiler workflow \
    --pathway "map00190" \
    --genome "draft_genome.faa" \
    --pfam-db "Pfam-A.hmm" \
    --evalue 1e-2 \
    --output-dir "oxidative_phosphorylation" \
    --visualize
```

## 🎯 Common Pathway IDs

| Pathway Name | KEGG ID | Description |
|--------------|---------|-------------|
| 3-Hydroxypropanoate bi-cycle | map00720 | Carbon fixation pathway |
| Oxidative phosphorylation | map00190 | ATP synthesis |
| Reductive citrate cycle | map00720 | rTCA carbon fixation |
| Calvin cycle | map00710 | CBB carbon fixation |
| Nitrogen metabolism | map00910 | Nitrogen processing |
| Sulfur metabolism | map00920 | Sulfur processing |

## 🛠️ Advanced Usage - Individual Steps

If you need more control, you can run each step individually:

### Step 1: Extract EC Numbers
```bash
# Extract EC numbers from a specific pathway
solaris pathway-profiler extract-ec \
    --pathway "map00720" \
    --output "ec_pfam_mapping.txt" \
    --interactive  # Optional: for pathway search
```

### Step 2: Get HMM Profiles
```bash
# Extract relevant HMM profiles from Pfam database
solaris pathway-profiler get-profiles \
    --input "ec_pfam_mapping.txt" \
    --pfam-db "/path/to/Pfam-A.hmm" \
    --output "selected_pfam.hmm"
```

### Step 3: Search Genome
```bash
# Search genome using HMM profiles
solaris pathway-profiler search \
    --hmm "selected_pfam.hmm" \
    --genome "target_genome.faa" \
    --output "hits_table.txt" \
    --evalue 1e-5
```

### Step 4: Analyze Results
```bash
# Analyze hits and generate reports
solaris pathway-profiler analyze \
    --hits "hits_table.txt" \
    --input "ec_pfam_mapping.txt" \
    --hmm "selected_pfam.hmm" \
    --output-dir "analysis_results"
```

### Step 5: Visualize Results
```bash
# Generate KEGG pathway visualization
solaris pathway-profiler visualize \
    --results "analysis_results/ec_results.csv" \
    --pathway "map00720" \
    --headless
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1 **Missing Dependencies**
```
Error: hmmfetch not found in PATH
```
**Solution**: Install HMMER tools:
```bash
# Ubuntu/Debian
sudo apt-get install hmmer

# Conda
conda install -c bioconda hmmer
```

#### 2 **Pfam Database Issues**
```
Error: Pfam-A.hmm not found
```
**Solution**: Download and prepare Pfam database:
```bash
# Download Pfam database
wget http://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz
gunzip Pfam-A.hmm.gz

# Press and index the database
hmmpress Pfam-A.hmm
```

### 📋 Prerequisites Checklist

- ✅ Python 3.8+ with required packages (`pandas`, `biopython`, `pyhmmer`, `selenium`)
- ✅ HMMER tools (`hmmfetch`, `hmmpress`) installed and in PATH
- ✅ Pfam-A.hmm database downloaded and indexed
- ✅ Firefox browser (for visualization)
- ✅ Target genome in FASTA amino acid format (.faa)

## 🎯 Result Interpretation

### EC Number Status Categories:

- **🟢 FULLY_FOUND**: All required Pfam domains detected
  - High confidence that the enzyme is present
  - Pathway step is likely functional

- **🟡 PARTIALLY_FOUND**: Some but not all required domains detected
  - Enzyme may be present but with different domain architecture
  - Manual inspection recommended

- **🔴 NOT_FOUND**: No required domains detected
  - Enzyme likely absent from the genome
  - Pathway step may be non-functional or alternative enzymes present

### Pathway Completeness Assessment:

- **>80% FULLY_FOUND**: Pathway likely complete and functional
- **60-80% FULLY_FOUND**: Pathway mostly present, some gaps may exist
- **<60% FULLY_FOUND**: Pathway likely incomplete or uses alternative enzymes
