#!/usr/bin/env python3
"""
Download all genome assemblies for a given species from NCBI.
Uses NCBI Datasets API.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path
import sys

def search_ncbi_genomes(species_name, output_dir='genomes'):
    """
    Search and download all available genomes for a species.
    
    Args:
        species_name: e.g., "Synechococcus elongatus"
        output_dir: Directory to save genomes
    """
    
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"Searching NCBI for: {species_name}")
    print("="*80)
    
    # Step 1: Search for assemblies using NCBI Datasets
    search_cmd = [
        'datasets', 'summary', 'genome', 'taxon', species_name,
        '--as-json-lines'
    ]
    
    try:
        result = subprocess.run(search_cmd, capture_output=True, text=True, check=True)
        
        # Parse results
        assemblies = []
        for line in result.stdout.strip().split('\n'):
            if line:
                data = json.loads(line)
                if 'accession' in data:
                    assemblies.append({
                        'accession': data['accession'],
                        'organism_name': data.get('organism', {}).get('organism_name', 'Unknown'),
                        'strain': data.get('organism', {}).get('infraspecific_names', {}).get('strain', 'Unknown'),
                        'assembly_level': data.get('assembly_info', {}).get('assembly_level', 'Unknown'),
                        'submission_date': data.get('assembly_info', {}).get('submission_date', 'Unknown')
                    })
        
        print(f"✓ Found {len(assemblies)} assemblies")
        
        # Save assembly list
        df = pd.DataFrame(assemblies)
        df.to_csv(f'{output_dir}/{species_name.replace(" ", "_")}_assemblies.csv', index=False)
        
        return assemblies
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("Make sure NCBI datasets tool is installed:")
        print("  conda install -c conda-forge ncbi-datasets-cli")
        return []


def download_proteomes(assemblies, output_dir='genomes', max_strains=None):
    """
    Download protein FASTA files for selected assemblies.
    
    Args:
        assemblies: List of assembly dictionaries
        output_dir: Where to save files
        max_strains: Limit number of downloads (None = all)
    """
    
    # Filter to complete/chromosome level assemblies (higher quality)
    quality_assemblies = [a for a in assemblies 
                         if a['assembly_level'] in ['Complete Genome', 'Chromosome']]
    
    if not quality_assemblies:
        print("No high-quality assemblies found, using all available")
        quality_assemblies = assemblies
    
    # Limit if requested
    if max_strains:
        quality_assemblies = quality_assemblies[:max_strains]
    
    print(f"\nDownloading proteomes for {len(quality_assemblies)} assemblies...")
    print("="*80)
    
    downloaded = []
    
    for idx, assembly in enumerate(quality_assemblies, 1):
        accession = assembly['accession']
        strain = assembly['strain'].replace('/', '_').replace(' ', '_')
        
        print(f"\n[{idx}/{len(quality_assemblies)}] {accession} - {strain}")
        
        # Download using NCBI datasets
        download_cmd = [
            'datasets', 'download', 'genome', 'accession', accession,
            '--include', 'protein',
            '--filename', f'{output_dir}/{accession}.zip'
        ]
        
        try:
            subprocess.run(download_cmd, check=True, capture_output=True)
            
            # Unzip
            subprocess.run(['unzip', '-q', '-o', f'{output_dir}/{accession}.zip',
                          '-d', f'{output_dir}/{accession}'], check=True)
            
            # Find the protein fasta file
            protein_file = list(Path(f'{output_dir}/{accession}').rglob('protein.faa'))
            
            if protein_file:
                # Rename to something more readable
                new_name = f'{output_dir}/{accession}_{strain}.faa'
                protein_file[0].rename(new_name)
                
                print(f"  ✓ Saved to {new_name}")
                
                downloaded.append({
                    'accession': accession,
                    'strain': strain,
                    'file': new_name
                })
            
            # Clean up
            Path(f'{output_dir}/{accession}.zip').unlink()
            
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to download {accession}")
            continue
    
    print(f"\n✓ Successfully downloaded {len(downloaded)} proteomes")
    
    # Save download manifest
    if downloaded:
        df = pd.DataFrame(downloaded)
        df.to_csv(f'{output_dir}/downloaded_strains.csv', index=False)
    
    return downloaded


def main():
    species_name = "Synechococcus elongatus" 
    max_strains = 10  # Limit strains number
    
    # Search for assemblies
    assemblies = search_ncbi_genomes(species_name)
    
    if not assemblies:
        print("No assemblies found")
        return
    
    # Show summary
    print(f"\nAssembly quality distribution:")
    df = pd.DataFrame(assemblies)
    print(df['assembly_level'].value_counts())
    
    # Download proteomes
    downloaded = download_proteomes(assemblies, max_strains=max_strains)
    
    if downloaded:
        print("\n" + "="*80)
        print("DOWNLOAD COMPLETE")
        print("="*80)
        print(f"\nFiles saved in: genomes/")
        print(f"Strain list: genomes/downloaded_strains.csv")
        print(f"Assembly info: genomes/{species_name.replace(' ', '_')}_assemblies.csv")

if __name__ == '__main__':
    main()