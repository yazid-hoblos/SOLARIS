#!/usr/bin/env python3
"""
Step 1: Download all GCF genomes of a species from NCBI
"""

import subprocess
import json
import pandas as pd
from pathlib import Path
import sys
import time

def search_ncbi_genomes(species_name, output_dir='genomes'):
    """Search NCBI for all GCF assemblies of a species."""
    
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"Searching NCBI for: {species_name} (RefSeq/GCF only)")
    print("="*80)
    
    search_cmd = [
        'datasets', 'summary', 'genome', 'taxon', species_name,
        '--assembly-source', 'refseq',  # Only GCF
        '--as-json-lines'
    ]
    
    try:
        result = subprocess.run(search_cmd, capture_output=True, text=True, check=True)
        
        assemblies = []
        for line in result.stdout.strip().split('\n'):
            if line:
                data = json.loads(line)
                assemblies.append({
                    'accession': data['accession'],
                    'organism': data.get('organism', {}).get('organism_name', 'Unknown'),
                    'strain': data.get('organism', {}).get('infraspecific_names', {}).get('strain', 'Unknown'),
                    'assembly_level': data.get('assembly_info', {}).get('assembly_level', 'Unknown'),
                    'date': data.get('assembly_info', {}).get('submission_date', 'Unknown')
                })
        
        print(f"✓ Found {len(assemblies)} RefSeq assemblies")
        
        df = pd.DataFrame(assemblies)
        df.to_csv(f'{output_dir}/assemblies_list.csv', index=False)
        
        return assemblies
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("Install: conda install -c conda-forge ncbi-datasets-cli")
        return []


def download_proteomes(assemblies, output_dir='genomes'):
    """Download protein FASTA files."""
    
    print(f"\nDownloading {len(assemblies)} proteomes...")
    print("="*80)
    
    downloaded = []
    
    for idx, assembly in enumerate(assemblies, 1):
        accession = assembly['accession']
        strain = assembly['strain'].replace('/', '_').replace(' ', '_')
        
        print(f"\n[{idx}/{len(assemblies)}] {accession} - {strain}")
        
        try:
            # Download
            subprocess.run([
                'datasets', 'download', 'genome', 'accession', accession,
                '--include', 'protein',
                '--filename', f'{output_dir}/{accession}.zip'
            ], check=True, capture_output=True)
            
            # Unzip
            subprocess.run(['unzip', '-q', '-o', f'{output_dir}/{accession}.zip',
                          '-d', f'{output_dir}/{accession}'], check=True)
            
            # Find protein file
            protein_files = list(Path(f'{output_dir}/{accession}').rglob('protein.faa'))
            
            if protein_files:
                new_name = f'{output_dir}/{strain}_{accession}.faa'
                protein_files[0].rename(new_name)
                print(f"  ✓ {new_name}")
                
                downloaded.append({
                    'accession': accession,
                    'strain': strain,
                    'file': new_name,
                    'organism': assembly['organism']
                })
            
            Path(f'{output_dir}/{accession}.zip').unlink()
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    if downloaded:
        df = pd.DataFrame(downloaded)
        df.to_csv(f'{output_dir}/downloaded_strains.csv', index=False)
        print(f"\n✓ Downloaded {len(downloaded)} proteomes")
    
    return downloaded


def main():
    # species = "Synechococcus elongatus"
    species = "Prochlorococcus marinus"
    
    assemblies = search_ncbi_genomes(species)
    
    if assemblies:
        print(f"\nAssembly levels:")
        print(pd.DataFrame(assemblies)['assembly_level'].value_counts())
        
        downloaded = download_proteomes(assemblies)
        
        if downloaded:
            print(f"\n{'='*80}")
            print("FILES READY FOR ANALYSIS")
            print(f"{'='*80}")
            print(f"Location: genomes/")
            print(f"Manifest: genomes/downloaded_strains.csv")

if __name__ == '__main__':
    main()