# Compatibility Predictor Workflow Usage

This guide provides step-by-step instructions for using the Compatibility Predictor module to identify organisms suitable for heterologous pathway implementation.

## Overview

The Compatibility Predictor workflow consists of three main steps:

1. **KEGG Analysis** (`keggQuery.py`) - Extract genes and organisms associated with target EC numbers
2. **BacDive Filtering** (`bacdive_access.py`) - Filter organisms by physiological criteria
3. **Organism Matching** (`taxonomyMatcher.py`) - Match and validate organisms between databases

## Prerequisites

- Valid BacDive account credentials (Registration at https://api.bacdive.dsmz.de/)
- Email account for NCBI API access
- Internet connection for API access

## Step 1: KEGG Analysis

Extract genes and organisms associated with your target EC numbers from the KEGG database.

### Command
```bash
python3 keggQuery.py --ec-file <ec_numbers_file> [--output <output_file>] [--max-species <number>]
```

### Parameters
- `--ec-file, -e`: Path to file containing EC numbers (one per line)
- `--output, -o`: Output JSON file (default: "kegg_results.json")
- `--max-species, -s`: Maximum number of species per EC (default: 3)

### Input File Format
Create a text file with EC numbers, one per line:
```
1.1.1.1
2.3.1.15
3.2.1.23
```

### Example Usage
```bash
# Basic usage
python3 keggQuery.py --ec-file my_ec_numbers.txt

# Custom output file and species limit
python3 keggQuery.py -e pathway_ecs.txt -o kegg_pathway_data.json -s 5

# Process single EC with detailed output
python3 keggQuery.py -e single_ec.txt -o detailed_results.json -s 10
```

### Output
Creates a JSON file containing:
- EC number mappings to genes
- Associated organism codes and names
- Gene information and pathway associations
- Limited to specified number of species per EC

And a TXT file of the identified species names.

### Sample Output Structure
```json
{
    "1.1.1.1": {
        "genes": ["adh1", "adh2"],
        "organisms": {
            "eco": "Escherichia coli",
            "bsu": "Bacillus subtilis"
        }
    }
}
```

---

## Step 2: BacDive Filtering

Filter organisms by physiological criteria using the BacDive database.

### Command
```bash
python3 bacdive_access.py --email <email> --taxonomy <taxonomy> [options]
```

### Parameters
- `--email, -e`: Your email address (required)
- `--password, -p`: BacDive password (optional - will prompt securely if not provided)
- `--taxonomy, -t`: Taxonomy search term (e.g., "Synechococcus", "Cyanobacteria")
- `--temp-min`: Minimum temperature (default: 20°C)
- `--temp-max`: Maximum temperature (default: 45°C)
- `--temp-type`: Temperature type - 'optimum', 'minimum', 'maximum' (default: 'optimum')
- `--max-strains`: Maximum strains to process (default: 200)
- `--output`: Output file prefix (default: taxonomy name)

NOTE that the code will prompt you to enter your BacDive account password to be able to access the API (so a BacDive account must be created first at https://api.bacdive.dsmz.de/).

### Example Usage
```bash
# Basic usage (password will be prompted securely)
python3 bacdive_access.py --email your@email.com --taxonomy Synechococcus

# Custom temperature range for thermophiles
python3 bacdive_access.py -e your@email.com -t Thermus --temp-min 60 --temp-max 85

# Psychrophiles with custom output
python3 bacdive_access.py -e your@email.com -t Psychrobacter --temp-min 0 --temp-max 20 --output cold_adapted

# Large-scale screening
python3 bacdive_access.py -e your@email.com -t Cyanobacteria --max-strains 500
```

### Filtering Criteria Applied
The script automatically applies two independent filters:
1. **Aerobic Filter**: Organisms with aerobic oxygen tolerance
2. **Temperature Filter**: Organisms within specified temperature range

### Output Files
- `{taxonomy}_aerobic.json`: Organisms filtered by oxygen tolerance
- `{taxonomy}_temperature.json`: Organisms filtered by temperature range
- Console output shows statistics for both filters

### Sample Console Output
```
Aerobic Filter Results:
Found 45 aerobic Synechococcus strains
Saved to: synechococcus_aerobic.json

Temperature Filter Results:
Found 32 Synechococcus strains in range 20-45°C
Saved to: synechococcus_temperature.json
```

---

## Step 3: Organism Matching

Match organisms between KEGG and BacDive databases using NCBI taxonomy validation.

### Command
```bash
python3 taxonomyMatcher.py --email <email> [--kegg-file <file>] [--bacdive-file <file>] [options]
```

### Parameters
- `--email, -e`: Your email address (required for NCBI API)
- `--kegg-file, -k`: KEGG results JSON file (default: "kegg_results.json")
- `--bacdive-file, -b`: BacDive results JSON file (default: "mesophiles.json")
- `--output-json`: Output JSON file (default: "taxid_matches.json")
- `--output-txt`: Output text file (default: "taxid_matched_species.txt")

### Example Usage
```bash
# Basic matching with default files
python3 taxonomyMatcher.py --email your@email.com

# Custom input files
python3 taxonomyMatcher.py -e your@email.com -k kegg_pathway_data.json -b synechococcus_aerobic.json

# Custom output files
python3 taxonomyMatcher.py -e your@email.com -k kegg_results.json -b cyanobacteria_temperature.json --output-json my_matches.json
```

### Matching Process
1. **Load Data**: Reads KEGG and BacDive result files
2. **Extract Taxa**: Extracts species names from both datasets
3. **NCBI Validation**: Validates species names using NCBI taxonomy database
4. **Cross-Reference**: Matches validated taxonomy IDs between datasets
5. **Generate Reports**: Creates JSON and text output files

### Output Files

#### JSON Output (`taxid_matches.json`)
```json
{
    "matches": [
        {
            "taxid": "1148",
            "species": "Synechocystis sp. PCC 6803",
            "kegg_presence": true,
            "bacdive_presence": true,
            "kegg_organisms": ["syn"],
            "bacdive_strains": ["DSM 3027", "PCC 6803"]
        }
    ],
    "summary": {
        "total_matches": 15,
        "kegg_species": 234,
        "bacdive_species": 89
    }
}
```

#### Text Output (`taxid_matched_species.txt`)
```
Matched Species Report
=====================
Total matches found: 15

1. Synechocystis sp. PCC 6803 (NCBI:1148)
   - KEGG organisms: syn
   - BacDive strains: 3

2. Synechococcus elongatus PCC 7942 (NCBI:1140)
   - KEGG organisms: syf
   - BacDive strains: 2
```

---

## Complete Workflow Example

Here's a complete example workflow for analyzing the pyruvate pathway in cyanobacteria:

### 1. Prepare EC Numbers File
```bash
# Create ec_numbers.txt
echo "1.2.1.12" > pyruvate_ecs.txt  # Glyceraldehyde-3-phosphate dehydrogenase
echo "2.7.2.3" >> pyruvate_ecs.txt  # Phosphoglycerate kinase
echo "5.4.2.11" >> pyruvate_ecs.txt # Phosphoglycerate mutase
```

### 2. Extract KEGG Data
```bash
python3 keggQuery.py --ec-file pyruvate_ecs.txt --output pyruvate_kegg.json --max-species 5
```

### 3. Filter Cyanobacteria by Growth Conditions
```bash
python3 bacdive_access.py --email your@email.com --taxonomy Synechococcus --temp-min 25 --temp-max 35 --output marine_cyano
```

### 4. Match Compatible Organisms
```bash
python3 taxonomyMatcher.py --email your@email.com --kegg-file pyruvate_kegg.json --bacdive-file marine_cyano_aerobic.json --output-json pyruvate_compatible.json
```

### 5. Analyze Results
The final output will contain organisms that:
- ✅ Have genes for your target EC numbers (from KEGG)
- ✅ Are aerobic and grow in your temperature range (from BacDive)
- ✅ Are taxonomically validated (via NCBI)

---

## Troubleshooting

### Common Issues

**1. BacDive Authentication Errors**
```bash
# Make sure credentials are correct
python3 bacdive_access.py --email your@email.com --taxonomy test
# Password will be prompted securely
```

**2. KEGG API Rate Limiting**
```bash
# Reduce max-species to avoid timeouts
python3 keggQuery.py --ec-file ecs.txt --max-species 3
```

**3. No Matches Found**
- Check that taxonomy names are spelled correctly
- Try broader taxonomy terms (e.g., "Cyanobacteria" instead of "Synechococcus")
- Verify EC numbers are valid and active in KEGG

**4. Large Dataset Processing**
```bash
# Process in smaller batches
python3 bacdive_access.py --email your@email.com --taxonomy Bacteria --max-strains 100
```

### Performance Tips

- **Limit species per EC**: Use `--max-species 3` for faster KEGG processing
- **Batch processing**: Process large taxonomy groups in smaller chunks
- **Cache results**: Save intermediate files to avoid re-running expensive API calls
- **Network stability**: Ensure stable internet connection for API access

---

## Integration with Other SOLARIS Modules

The Compatibility Predictor results can be used with other SOLARIS modules:

### With Pangenomic Analyzer
```bash
# Use matched organisms for pangenomic analysis
python3 -m solaris pangenomic_analyzer complete \
    --genomes-dir matched_genomes/ \
    --hmm-file selected_pfam.hmm \
    --ec-pfam-mapping pfam_ids.txt
```

### With Product Valorization
```bash
# Analyze economic potential of compatible organisms
python3 -m solaris product_valorization analyze \
    --organisms-file pyruvate_compatible.json \
    --pathway-data pathway_analysis.json
```

This workflow ensures you identify the most suitable organisms for your heterologous pathway implementation based on both genetic capability and physiological compatibility.