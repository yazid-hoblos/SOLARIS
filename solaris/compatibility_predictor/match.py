"""
Rigorous Species Matcher using NCBI Taxonomy IDs
Matches KEGG and BacDive organisms using NCBI taxonomy IDs for accurate identification.

Requirements: pip install requests

Usage: 
    python3 match.py --email your@email.com --kegg-file kegg_results.json --bacdive-file mesophiles.json
    python3 match.py -e your@email.com -k kegg_data.json -b bacdive_data.json
"""

import json
import requests
import time
import argparse
from typing import List, Dict


class TaxonomyMatcher:
    """Match species using NCBI Taxonomy IDs for rigorous identification."""
    
    def __init__(self, email="your_email@example.com"):
        """
        Initialize taxonomy matcher.
        
        Args:
            email: Your email for NCBI E-utilities (required by NCBI)
        """
        self.email = email
        self.ncbi_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.session = requests.Session()
        self.taxid_cache = {}
        self.delay = 0.35  # NCBI rate limit: 3 requests/second
    
    def get_taxid_from_kegg(self, kegg_org_code: str) -> str:
        """
        Get NCBI taxonomy ID from KEGG organism code.
        
        Args:
            kegg_org_code: KEGG organism code (e.g., 'eco', 'hsa')
        
        Returns:
            NCBI taxonomy ID or None
        """
        if kegg_org_code in self.taxid_cache:
            return self.taxid_cache[kegg_org_code]
        
        # Get genome ID from KEGG
        url = f"https://rest.kegg.jp/find/genome/{kegg_org_code}"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200 and response.text.strip():
                lines = response.text.strip().split('\n')
                if lines:
                    parts = lines[0].split('\t')
                    if len(parts) >= 1:
                        genome_id = parts[0].replace('gn:', '')
                        
                        # Get genome entry which contains taxid
                        genome_url = f"https://rest.kegg.jp/get/{genome_id}"
                        genome_resp = self.session.get(genome_url)
                        
                        if genome_resp.status_code == 200:
                            # Look for TAXONOMY line with TAX:xxxxx
                            for line in genome_resp.text.split('\n'):
                                if line.startswith('TAXONOMY'):
                                    tax_part = line.split('TAX:')
                                    if len(tax_part) > 1:
                                        taxid = tax_part[1].split()[0]
                                        self.taxid_cache[kegg_org_code] = taxid
                                        return taxid
            
            # time.sleep(0.1)
            
        except Exception as e:
            print(f"  Warning: Could not get taxid for KEGG {kegg_org_code}: {e}")
        
        return None
    
    def get_taxid_from_name(self, species_name: str) -> str:
        """
        Get NCBI taxonomy ID from species name using NCBI E-utilities.
        
        Args:
            species_name: Species name (e.g., "Escherichia coli")
        
        Returns:
            NCBI taxonomy ID or None
        """
        if species_name in self.taxid_cache:
            return self.taxid_cache[species_name]
        
        # Search NCBI taxonomy database
        url = f"{self.ncbi_base}/esearch.fcgi"
        params = {
            'db': 'taxonomy',
            'term': species_name,
            'retmode': 'json',
            'email': self.email
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'esearchresult' in data and 'idlist' in data['esearchresult']:
                id_list = data['esearchresult']['idlist']
                if id_list:
                    taxid = id_list[0]
                    self.taxid_cache[species_name] = taxid
                    time.sleep(self.delay)
                    return taxid
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Warning: Could not get taxid for '{species_name}': {e}")
        
        return None
    
    def get_taxonomy_info(self, taxid: str) -> Dict:
        """
        Get detailed taxonomy information from NCBI.
        
        Args:
            taxid: NCBI taxonomy ID
        
        Returns:
            Dictionary with taxonomy information
        """
        url = f"{self.ncbi_base}/efetch.fcgi"
        params = {
            'db': 'taxonomy',
            'id': taxid,
            'retmode': 'xml',
            'email': self.email
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            text = response.text
            info = {'taxid': taxid}
            
            # Extract scientific name
            if '<ScientificName>' in text:
                start = text.find('<ScientificName>') + len('<ScientificName>')
                end = text.find('</ScientificName>')
                info['scientific_name'] = text[start:end]
            
            # Extract rank
            if '<Rank>' in text:
                start = text.find('<Rank>') + len('<Rank>')
                end = text.find('</Rank>')
                info['rank'] = text[start:end]
            
            time.sleep(self.delay)
            return info
            
        except Exception as e:
            print(f"  Warning: Could not fetch taxonomy info for {taxid}: {e}")
            return {'taxid': taxid}
    
    def match_with_taxids(self, kegg_data: Dict, bacdive_data: List[Dict]) -> Dict:
        """
        Match KEGG and BacDive species using taxonomy IDs.
        
        Args:
            kegg_data: KEGG results dictionary
            bacdive_data: List of BacDive organism dictionaries
        
        Returns:
            Match results with taxonomy IDs
        """
        results = {
            'matches': [],
            'kegg_no_taxid': [],
            'bacdive_no_taxid': [],
            'no_match': [],
            'statistics': {}
        }
        
        print("\n" + "="*60)
        print("STEP 1: Getting taxonomy IDs for KEGG organisms")
        print("="*60)
        
        # Get taxids for KEGG organisms
        kegg_taxids = {}
        for org_code, org_data in kegg_data['all_species'].items():
            print(f"  Processing KEGG: {org_code} ({org_data['species_name']})")
            
            taxid = self.get_taxid_from_kegg(org_code)
            
            if not taxid:
                # Fallback: try by name
                taxid = self.get_taxid_from_name(org_data['species_name'])
            
            if taxid:
                kegg_taxids[taxid] = {
                    'organism_code': org_code,
                    'species_name': org_data['species_name'],
                    'source': 'kegg'
                }
                print(f"    ✓ Taxid: {taxid}")
            else:
                results['kegg_no_taxid'].append(org_data['species_name'])
                print(f"    ✗ No taxid found")
        
        print(f"\nFound taxids for {len(kegg_taxids)}/{len(kegg_data['all_species'])} KEGG organisms")
        
        print("\n" + "="*60)
        print("STEP 2: Getting taxonomy IDs for BacDive organisms")
        print("="*60)
        
        # Get taxids for BacDive organisms (from BacDive data directly!)
        bacdive_taxids = {}
        for organism in bacdive_data:
            species_name = organism.get('name', 'Unknown')
            bacdive_id = organism.get('bacdive_id', 'Unknown')
            
            print(f"  Processing BacDive: {species_name} (ID: {bacdive_id})")
            
            # Try to get taxid directly from BacDive data
            taxid = organism.get('ncbi_taxid')
            
            if taxid:
                # Convert to string
                taxid = str(taxid)
                
                if taxid not in bacdive_taxids:
                    bacdive_taxids[taxid] = []
                bacdive_taxids[taxid].append({
                    'species_name': species_name,
                    'bacdive_id': organism.get('bacdive_id'),
                    'source': 'bacdive',
                    'organism_data': organism
                })
                print(f"    ✓ Taxid from BacDive data: {taxid}")
            else:
                # Fallback: search NCBI by name
                print(f"    No taxid in BacDive data, searching NCBI...")
                taxid = self.get_taxid_from_name(species_name)
                
                if taxid:
                    if taxid not in bacdive_taxids:
                        bacdive_taxids[taxid] = []
                    bacdive_taxids[taxid].append({
                        'species_name': species_name,
                        'bacdive_id': organism.get('bacdive_id'),
                        'source': 'bacdive',
                        'organism_data': organism
                    })
                    print(f"    ✓ Taxid from NCBI search: {taxid}")
                else:
                    results['bacdive_no_taxid'].append(species_name)
                    print(f"    ✗ No taxid found")
        
        print(f"\nFound taxids for {len(bacdive_taxids)} unique species in BacDive")
        
        print("\n" + "="*60)
        print("STEP 3: Matching by taxonomy ID")
        print("="*60)
        
        # Find matches
        for taxid in kegg_taxids.keys():
            if taxid in bacdive_taxids:
                # Match found!
                kegg_info = kegg_taxids[taxid]
                bacdive_info_list = bacdive_taxids[taxid]
                
                # Get taxonomy details
                tax_info = self.get_taxonomy_info(taxid)
                
                for bacdive_info in bacdive_info_list:
                    match = {
                        'taxid': taxid,
                        'scientific_name': tax_info.get('scientific_name', 'Unknown'),
                        'rank': tax_info.get('rank', 'Unknown'),
                        'kegg_name': kegg_info['species_name'],
                        'kegg_code': kegg_info['organism_code'],
                        'bacdive_name': bacdive_info['species_name'],
                        'bacdive_id': bacdive_info['bacdive_id'],
                        'bacdive_data': bacdive_info['organism_data']
                    }
                    results['matches'].append(match)
                    print(f"  ✓ Match: {match['scientific_name']} (taxid:{taxid})")
        
        # Find KEGG organisms without BacDive match
        for taxid, kegg_info in kegg_taxids.items():
            if taxid not in bacdive_taxids:
                results['no_match'].append({
                    'taxid': taxid,
                    'species_name': kegg_info['species_name'],
                    'source': 'kegg_only'
                })
        
        # Calculate statistics
        bacdive_with_taxid = sum(1 for org in bacdive_data if org.get('ncbi_taxid'))
        
        results['statistics'] = {
            'total_kegg_organisms': len(kegg_data['all_species']),
            'kegg_with_taxid': len(kegg_taxids),
            'kegg_without_taxid': len(results['kegg_no_taxid']),
            'total_bacdive_organisms': len(bacdive_data),
            'bacdive_with_taxid_in_data': bacdive_with_taxid,
            'bacdive_unique_taxids': len(bacdive_taxids),
            'bacdive_without_taxid': len(results['bacdive_no_taxid']),
            'total_matches': len(results['matches']),
            'kegg_unmatched': len(results['no_match'])
        }
        
        return results


def load_kegg_data(filename: str) -> Dict:
    """Load KEGG results."""
    with open(filename, 'r') as f:
        return json.load(f)


def load_bacdive_data(filename: str) -> List[Dict]:
    """Load BacDive results."""
    with open(filename, 'r') as f:
        return json.load(f)


def save_results(results: Dict, output_file: str):
    """Save matching results."""
    # Remove large organism_data from matches for cleaner output
    clean_results = results.copy()
    clean_results['matches'] = []
    for match in results['matches']:
        clean_match = {k: v for k, v in match.items() if k != 'bacdive_data'}
        clean_results['matches'].append(clean_match)
    
    with open(output_file, 'w') as f:
        json.dump(clean_results, f, indent=2)
    print(f"\n✓ Results saved to {output_file}")


def save_matched_list(results: Dict, output_file: str):
    """Save simple list of matched species."""
    with open(output_file, 'w') as f:
        f.write("# Species matched using NCBI Taxonomy IDs\n")
        f.write("# Format: Taxid | Scientific Name | KEGG Code | BacDive ID\n\n")
        
        for match in results['matches']:
            f.write(f"{match['taxid']}\t{match['scientific_name']}\t"
                   f"{match['kegg_code']}\t{match['bacdive_id']}\n")
    
    print(f"✓ Matched species list saved to {output_file}")


def print_summary(results: Dict):
    """Print summary statistics."""
    stats = results['statistics']
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"KEGG organisms: {stats['total_kegg_organisms']}")
    print(f"  - With taxonomy ID: {stats['kegg_with_taxid']}")
    print(f"  - Without taxonomy ID: {stats['kegg_without_taxid']}")
    
    print(f"\nBacDive organisms: {stats['total_bacdive_organisms']}")
    print(f"  - With taxonomy ID in data: {stats['bacdive_with_taxid_in_data']}")
    print(f"  - Unique taxonomy IDs found: {stats['bacdive_unique_taxids']}")
    print(f"  - Without taxonomy ID: {stats['bacdive_without_taxid']}")
    
    print(f"\n✓ MATCHED: {stats['total_matches']} organisms")
    print(f"✗ KEGG only: {stats['kegg_unmatched']} organisms")
    
    if results['matches']:
        for match in results['matches'][:10]:
            print(f"  • {match['scientific_name']} (taxid:{match['taxid']})")
            print(f"    KEGG: {match['kegg_code']} | BacDive: {match['bacdive_id']}")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Match species using NCBI Taxonomy IDs')
    parser.add_argument('--kegg-file', '-k', default="kegg_results.json", 
                       help='KEGG results JSON file (default: kegg_results.json)')
    parser.add_argument('--bacdive-file', '-b', default="mesophiles.json",
                       help='BacDive results JSON file (default: mesophiles.json)')
    parser.add_argument('--email', '-e', required=True,
                       help='Your email address (required by NCBI E-utilities)')
    parser.add_argument('--output-json', default="taxid_matches.json",
                       help='Output JSON file (default: taxid_matches.json)')
    parser.add_argument('--output-txt', default="taxid_matched_species.txt",
                       help='Output text file (default: taxid_matched_species.txt)')
    
    args = parser.parse_args()
    
    # Configuration from arguments
    KEGG_FILE = args.kegg_file
    BACDIVE_FILE = args.bacdive_file
    OUTPUT_JSON = args.output_json
    OUTPUT_TXT = args.output_txt
    EMAIL = args.email
    
    print("="*60)
    print("RIGOROUS SPECIES MATCHING USING TAXONOMY IDs")
    print("="*60)
    print(f"KEGG file: {KEGG_FILE}")
    print(f"BacDive file: {BACDIVE_FILE}")
    print(f"Email: {EMAIL}")
    
    # Load data
    print("\nLoading data...")
    try:
        kegg_data = load_kegg_data(KEGG_FILE)
        bacdive_data = load_bacdive_data(BACDIVE_FILE)
        print(f"✓ Loaded KEGG data: {len(kegg_data['all_species'])} organisms")
        print(f"✓ Loaded BacDive data: {len(bacdive_data)} organisms")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print(f"  1. {KEGG_FILE} (from kegg.py)")
        print(f"  2. {BACDIVE_FILE} (from bacdive_access.py)")
        return
    
    # Match using taxonomy IDs
    matcher = TaxonomyMatcher(email=EMAIL)
    results = matcher.match_with_taxids(kegg_data, bacdive_data)
    
    # Save results
    save_results(results, OUTPUT_JSON)
    save_matched_list(results, OUTPUT_TXT)
    
    # Print summary
    print_summary(results)
    
    print("\n" + "="*60)
    print("✓ Taxonomy ID matching complete!")
    print("="*60)
    print("\nThese matches are RIGOROUS - same organism in both databases")
    print("based on NCBI taxonomy identifiers, not just name similarity.")


if __name__ == "__main__":
    main()