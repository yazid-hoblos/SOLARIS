"""
KEGG EC Number Query Script
Queries KEGG database for EC numbers and extracts associated genes and species.

Input: Text file with one EC number per line (e.g., ec_numbers.txt)
Output: JSON file with EC numbers, genes, and species information

Install: pip install requests
KEGG REST API: https://rest.kegg.jp/
"""

import requests
import json
import time
from typing import List, Dict, Set
from collections import defaultdict
import sys


class KEGGQuery:
    """Query KEGG database for EC numbers, genes, and organisms."""
    
    BASE_URL = "https://rest.kegg.jp"
    
    def __init__(self, delay=0.5):
        """
        Initialize KEGG query client.
        
        Args:
            delay: Delay between API requests in seconds (be nice to KEGG!)
        """
        self.delay = delay
        self.session = requests.Session()
        self.organism_cache = {}  # Cache organism info to reduce API calls
        self._load_organism_list()
    
    def _load_organism_list(self):
        """Load the complete organism list from KEGG once at initialization."""
        print("Loading KEGG organism list...")
        url = f"{self.BASE_URL}/list/organism"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse organism list
            # Format: T_number\torg_code\tSpecies name\tPhylogeny
            for line in response.text.strip().split('\n'):
                parts = line.split('\t')
                if len(parts) >= 3:
                    t_number = parts[0]
                    org_code = parts[1]
                    species_name = parts[2]
                    
                    # Clean up species name (remove strain info in parentheses if needed)
                    # e.g., "Homo sapiens (human)" -> "Homo sapiens"
                    clean_name = species_name.split('(')[0].strip()
                    
                    self.organism_cache[org_code] = {
                        'organism_code': org_code,
                        't_number': t_number,
                        'full_name': species_name,
                        'species_name': clean_name
                    }
            
            print(f"  Loaded {len(self.organism_cache)} organisms")
            
        except requests.exceptions.RequestException as e:
            print(f"  Warning: Could not load organism list: {e}")
            print("  Will fetch organism info individually as needed")
    
    def get_ec_info(self, ec_number: str) -> Dict:
        """
        Get information about an EC number.
        
        Args:
            ec_number: EC number (e.g., '1.1.1.1')
        
        Returns:
            Dictionary with EC information including genes
        """
        url = f"{self.BASE_URL}/get/ec:{ec_number}"
        
        try:
            response = self.session.get(url)
            
            # Check if EC exists
            if response.status_code == 404:
                print(f"  Warning: EC {ec_number} not found in KEGG database")
                return {
                    'ec_number': ec_number, 
                    'error': 'Not found in KEGG',
                    'exists': False
                }
            
            response.raise_for_status()
            
            # Parse the response
            data = response.text
            info = {
                'ec_number': ec_number, 
                'raw_data': data,
                'exists': True
            }
            
            # Extract enzyme name
            for line in data.split('\n'):
                if line.startswith('NAME'):
                    info['name'] = line.replace('NAME', '').strip()
                    break
            
            # Extract genes from the GENES section
            info['genes'] = self._parse_genes_from_ec_entry(data)
            
            return info
            
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching EC {ec_number}: {e}")
            return {
                'ec_number': ec_number, 
                'error': str(e),
                'exists': False
            }
    
    def _parse_genes_from_ec_entry(self, ec_data: str) -> List[str]:
        """
        Parse genes from the GENES section of an EC entry.
        
        Args:
            ec_data: Raw text from EC entry
        
        Returns:
            List of gene IDs (e.g., ['hsa:124', 'ptr:461394'])
        """
        genes = []
        in_genes_section = False
        
        for line in ec_data.split('\n'):
            # Check if we're entering the GENES section
            if line.startswith('GENES'):
                in_genes_section = True
                # Process the first line of GENES
                line = line.replace('GENES', '').strip()
            
            # Check if we've left the GENES section
            elif in_genes_section and line and not line.startswith(' '):
                # We've reached a new section
                break
            
            # Parse genes if we're in the GENES section
            if in_genes_section and line.strip():
                # Format: ORG: gene1(name1) gene2(name2) gene3 ...
                # Example: HSA: 124(ADH1A) 125(ADH1B) 999
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    org_code = parts[0].strip().lower()
                    genes_str = parts[1].strip()
                    
                    # Extract all gene IDs (with or without names)
                    import re
                    # Split by whitespace to get individual gene entries
                    gene_entries = genes_str.split()
                    
                    for entry in gene_entries:
                        # Extract gene ID (everything before '(' if present, otherwise the whole string)
                        gene_id = entry.split('(')[0]
                        
                        # Skip if it's not a valid gene ID (e.g., empty or just parentheses)
                        if gene_id and not gene_id.startswith('('):
                            genes.append(f"{org_code}:{gene_id}")
        
        return genes
    
    def get_genes_for_ec(self, ec_number: str) -> List[str]:
        """
        Get all genes associated with an EC number.
        NOTE: This method is now deprecated - genes are parsed from EC entry directly.
        
        Args:
            ec_number: EC number (e.g., '1.1.1.1')
        
        Returns:
            List of gene IDs (e.g., ['hsa:124', 'eco:b0002'])
        """
        # Genes are now extracted from the EC entry itself
        # This method is kept for backward compatibility
        return []
    
    def get_organism_from_gene(self, gene_id: str) -> Dict:
        """
        Extract organism information from gene ID.
        
        Args:
            gene_id: Gene ID (e.g., 'eco:b0002')
        
        Returns:
            Dictionary with organism code and gene
        """
        # Gene IDs are formatted as 'organism_code:gene_name'
        if ':' in gene_id:
            org_code, gene_name = gene_id.split(':', 1)
            return {
                'organism_code': org_code,
                'gene_id': gene_id,
                'gene_name': gene_name
            }
        return {'organism_code': 'unknown', 'gene_id': gene_id}
    
    def get_organism_info(self, org_code: str) -> Dict:
        """
        Get full organism information from organism code.
        Uses cached organism list loaded at initialization.
        
        Args:
            org_code: KEGG organism code (e.g., 'eco' for E. coli)
        
        Returns:
            Dictionary with organism details
        """
        # Check cache first
        if org_code in self.organism_cache:
            return self.organism_cache[org_code]
        
        # If not in cache, return the code as the name
        print(f"    Warning: Organism {org_code} not found in KEGG organism list")
        return {
            'organism_code': org_code,
            't_number': 'unknown',
            'full_name': org_code,
            'species_name': org_code
        }
    
    def query_ec_numbers(self, ec_numbers: List[str]) -> Dict:
        """
        Query multiple EC numbers and collect all associated species.
        
        Args:
            ec_numbers: List of EC numbers
        
        Returns:
            Dictionary with results
        """
        results = {
            'ec_data': {},
            'all_species': {},
            'species_to_ec': defaultdict(list),
            'summary': {}
        }
        
        print(f"Querying {len(ec_numbers)} EC numbers...")
        
        for i, ec_number in enumerate(ec_numbers, 1):
            print(f"\n[{i}/{len(ec_numbers)}] Processing EC {ec_number}...")
            
            # Get EC info with genes parsed from the entry
            print(f"  Fetching EC entry...")
            ec_info = self.get_ec_info(ec_number)
            time.sleep(self.delay)
            
            # Skip if EC doesn't exist
            if not ec_info.get('exists', False):
                results['ec_data'][ec_number] = {
                    'ec_info': ec_info,
                    'genes': [],
                    'organisms': {},
                    'organism_count': 0
                }
                continue
            
            # Show EC name if available
            if 'name' in ec_info:
                print(f"  Name: {ec_info['name']}")
            
            # Get genes from the EC entry
            genes = ec_info.get('genes', [])
            
            if len(genes) == 0:
                print(f"  ⚠ No genes found in GENES section")
            else:
                print(f"  Found {len(genes)} genes")
            
            # Extract organisms from genes
            organisms = {}
            org_codes = set()
            
            for gene_id in genes:
                org_info = self.get_organism_from_gene(gene_id)
                org_code = org_info['organism_code']
                org_codes.add(org_code)
                
                if org_code not in organisms:
                    organisms[org_code] = {
                        'organism_code': org_code,
                        'genes': []
                    }
                organisms[org_code]['genes'].append(gene_id)
            
            # Get full organism information (use cached data)
            if org_codes:
                print(f"  Found {len(org_codes)} unique organisms")
                # Limit to first 3 organisms to reduce processing time
                limited_org_codes = list(org_codes)[:3]
                if len(org_codes) > 3:
                    print(f"  Limiting to first 3 organisms to reduce processing time")
                for org_code in limited_org_codes:
                    if org_code not in results['all_species']:
                        org_details = self.get_organism_info(org_code)
                        results['all_species'][org_code] = org_details
                    
                    # Link species to EC numbers
                    species_name = results['all_species'][org_code]['species_name']
                    results['species_to_ec'][species_name].append(ec_number)
            
            # Store results for this EC number
            results['ec_data'][ec_number] = {
                'ec_info': ec_info,
                'genes': genes,
                'organisms': organisms,
                'organism_count': len(org_codes)
            }
        
        # Generate summary
        valid_ec_count = sum(1 for ec in results['ec_data'].values() 
                           if ec['ec_info'].get('exists', False))
        ec_with_genes = sum(1 for ec in results['ec_data'].values() 
                          if len(ec['genes']) > 0)
        
        # Create species list with actual names (not codes)
        species_names = sorted([
            org_data['species_name'] 
            for org_data in results['all_species'].values()
        ])
        
        results['summary'] = {
            'total_ec_numbers': len(ec_numbers),
            'valid_ec_numbers': valid_ec_count,
            'invalid_ec_numbers': len(ec_numbers) - valid_ec_count,
            'ec_with_genes': ec_with_genes,
            'ec_without_genes': valid_ec_count - ec_with_genes,
            'total_genes': sum(len(ec['genes']) for ec in results['ec_data'].values()),
            'total_unique_species': len(results['all_species']),
            'species_list': species_names,
            'organism_codes': sorted(results['all_species'].keys())
        }
        
        return results


def load_ec_numbers(filename: str) -> List[str]:
    """Load EC numbers from a text file (one per line)."""
    ec_numbers = []
    with open(filename, 'r') as f:
        for line in f:
            ec = line.strip()
            if ec and not ec.startswith('#'):  # Skip empty lines and comments
                ec_numbers.append(ec)
    return ec_numbers


def save_results(results: Dict, output_file: str):
    """Save results to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to {output_file}")


def save_species_list(results: Dict, output_file: str):
    """Save just the species list to a text file."""
    with open(output_file, 'w') as f:
        for species_name in sorted(results['all_species'].values(), 
                                   key=lambda x: x['species_name']):
            f.write(f"{species_name['species_name']}\n")
    print(f"✓ Species list saved to {output_file}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python kegg.py <ec_numbers.txt>")
        print("  <ec_numbers.txt>: Text file with one EC number per line")
        return
    
    # Configuration
    EC_FILE = sys.argv[1]
    OUTPUT_JSON = "kegg_results.json"  # Detailed results
    OUTPUT_SPECIES = "kegg_species.txt"  # Simple species list
    
    # Load EC numbers
    print("Loading EC numbers...")
    try:
        ec_numbers = load_ec_numbers(EC_FILE)
        print(f"Loaded {len(ec_numbers)} EC numbers")
    except FileNotFoundError:
        print(f"Error: File '{EC_FILE}' not found!")
        print("\nCreating example file...")
        return
    
    # Query KEGG
    kegg = KEGGQuery(delay=0.5)  # 0.5 second delay between requests
    results = kegg.query_ec_numbers(ec_numbers)
    
    # Save results
    save_results(results, OUTPUT_JSON)
    save_species_list(results, OUTPUT_SPECIES)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"EC numbers queried: {results['summary']['total_ec_numbers']}")
    print(f"Valid EC numbers: {results['summary']['valid_ec_numbers']}")
    print(f"  - With genes: {results['summary']['ec_with_genes']}")
    print(f"  - Without genes: {results['summary']['ec_without_genes']}")
    print(f"Invalid/Not found: {results['summary']['invalid_ec_numbers']}")
    print(f"\nTotal genes found: {results['summary']['total_genes']}")
    print(f"Unique species: {results['summary']['total_unique_species']}")
    
    # List EC numbers without genes
    no_genes_ecs = [ec for ec, data in results['ec_data'].items() 
                    if data['ec_info'].get('exists', False) and len(data['genes']) == 0]
    if no_genes_ecs:
        print(f"\n⚠ EC numbers with no genes in KEGG ({len(no_genes_ecs)}):")
        for ec in no_genes_ecs[:10]:  # Show first 10
            name = results['ec_data'][ec]['ec_info'].get('name', 'Unknown')
            print(f"  - {ec}: {name}")
        if len(no_genes_ecs) > 10:
            print(f"  ... and {len(no_genes_ecs) - 10} more")
    
    # List invalid EC numbers
    invalid_ecs = [ec for ec, data in results['ec_data'].items() 
                   if not data['ec_info'].get('exists', False)]
    if invalid_ecs:
        print(f"\n❌ EC numbers not found in KEGG ({len(invalid_ecs)}):")
        for ec in invalid_ecs:
            print(f"  - {ec}")
    
    if results['summary']['total_unique_species'] > 0:
        print("\n✓ Top 10 species by gene count:")
        
        species_gene_counts = defaultdict(int)
        for ec_data in results['ec_data'].values():
            for org_code, org_data in ec_data['organisms'].items():
                if org_code in results['all_species']:
                    species_name = results['all_species'][org_code]['species_name']
                    species_gene_counts[species_name] += len(org_data['genes'])
        
        for species, count in sorted(species_gene_counts.items(), 
                                     key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {species}: {count} genes")
    else:
        print("\n⚠ No species found. This could mean:")
        print("  - EC numbers are valid but not yet sequenced in any organism")
        print("  - EC numbers are theoretical or from non-sequenced organisms")
        print("  - Try different EC numbers with known gene sequences")


if __name__ == "__main__":
    main()