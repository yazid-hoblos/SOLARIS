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

def search_ncbi_genomes_single(species_name, output_dir='genomes'):
    """Search NCBI for all GCF assemblies of a single species."""
    
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
                try:
                    data = json.loads(line)
                    assemblies.append({
                        'accession': data['accession'],
                        'organism': data.get('organism', {}).get('organism_name', 'Unknown'),
                        'strain': data.get('organism', {}).get('infraspecific_names', {}).get('strain', 'Unknown'),
                        'assembly_level': data.get('assembly_info', {}).get('assembly_level', 'Unknown'),
                        'date': data.get('assembly_info', {}).get('submission_date', 'Unknown'),
                        'genus': species_name.split()[0]  # Extract genus for grouping
                    })
                except json.JSONDecodeError:
                    continue
        
        print(f"  Searching: {species_name}... ✓ {len(assemblies)} genomes")
        return assemblies
        
    except subprocess.CalledProcessError as e:
        print(f"  Searching: {species_name}... ✗ Error")
        return []
    except Exception as e:
        print(f"  Searching: {species_name}... ✗ Error") 
        return []


def search_ncbi_genomes(species_list, output_dir='genomes'):
    """Search NCBI for all GCF assemblies of multiple species."""
    
    Path(output_dir).mkdir(exist_ok=True)
    
    print("DOWNLOADING CYANOBACTERIA PROTEOMES")
    print("="*80)
    print("\n1. Searching NCBI...")
    
    all_assemblies = []
    genus_counts = {}
    
    for species in species_list:
        assemblies = search_ncbi_genomes_single(species, output_dir)
        all_assemblies.extend(assemblies)
        
        # Count by genus
        if assemblies:
            genus = assemblies[0]['genus']
            genus_counts[genus] = genus_counts.get(genus, 0) + len(assemblies)
    
    print(f"\n✓ Total genomes found: {len(all_assemblies)}")
    
    if all_assemblies:
        # Show genus distribution
        print("\nGenomes per genus:")
        genus_df = pd.DataFrame(list(genus_counts.items()), columns=['genus', 'count'])
        genus_df = genus_df.sort_values('count', ascending=False)
        print(genus_df.to_string(index=False))
        
        # Save all assemblies
        df = pd.DataFrame(all_assemblies)
        df.to_csv(f'{output_dir}/assemblies_list.csv', index=False)
    
    return all_assemblies


def download_proteomes(assemblies, output_dir='genomes'):
    """Download protein FASTA files with better error handling."""
    
    print(f"\n2. Downloading {len(assemblies)} proteomes...")
    print("="*80)
    
    downloaded = []
    failed = []
    
    for idx, assembly in enumerate(assemblies, 1):
        accession = assembly['accession']
        strain = assembly['strain'].replace('/', '_').replace(' ', '_')
        genus = assembly.get('genus', assembly.get('organism', 'Unknown').split()[0])
        
        # Check if already downloaded
        existing_files = list(Path(output_dir).glob(f'*{accession}*.faa'))
        if existing_files:
            print(f"[{idx}/{len(assemblies)}] {genus} {accession}... ✓")
            downloaded.append({
                'accession': accession,
                'strain': strain,
                'file': str(existing_files[0]),
                'organism': assembly['organism'],
                'genus': genus
            })
            continue
        
        print(f"[{idx}/{len(assemblies)}] {genus} {accession}... ", end='', flush=True)
        
        try:
            # Add small delay to avoid rate limiting
            if idx > 1:
                time.sleep(0.1)
            
            # Download with timeout
            subprocess.run([
                'datasets', 'download', 'genome', 'accession', accession,
                '--include', 'protein',
                '--filename', f'{output_dir}/{accession}.zip'
            ], check=True, capture_output=True, timeout=90)
            
            # Check if download worked
            zip_path = Path(f'{output_dir}/{accession}.zip')
            if not zip_path.exists() or zip_path.stat().st_size < 1000:
                raise Exception("Download failed or file too small")
            
            # Unzip
            subprocess.run(['unzip', '-q', '-o', f'{output_dir}/{accession}.zip',
                          '-d', f'{output_dir}/{accession}'], check=True, timeout=30)
            
            # Find protein file
            protein_files = list(Path(f'{output_dir}/{accession}').rglob('protein.faa'))
            
            if protein_files and protein_files[0].stat().st_size > 1000:
                new_name = f'{output_dir}/{strain}_{accession}.faa'
                protein_files[0].rename(new_name)
                print("✓")
                
                downloaded.append({
                    'accession': accession,
                    'strain': strain,
                    'file': new_name,
                    'organism': assembly['organism'],
                    'genus': genus
                })
                
                # Clean up
                zip_path.unlink(missing_ok=True)
                import shutil
                shutil.rmtree(f'{output_dir}/{accession}', ignore_errors=True)
                
            else:
                raise Exception("No protein file found")
            
        except subprocess.TimeoutExpired:
            print("✗")
            failed.append({'accession': accession, 'genus': genus, 'reason': 'timeout'})
        except subprocess.CalledProcessError as e:
            print("✗")
            stderr = e.stderr.decode() if e.stderr else ""
            if 'rate limit' in stderr.lower():
                failed.append({'accession': accession, 'genus': genus, 'reason': 'rate_limit'})
                time.sleep(10)  # Wait for rate limit
            else:
                failed.append({'accession': accession, 'genus': genus, 'reason': 'api_error'})
        except Exception as e:
            print("✗")
            failed.append({'accession': accession, 'genus': genus, 'reason': str(e)[:30]})
            
        # Clean up failed downloads
        try:
            Path(f'{output_dir}/{accession}.zip').unlink(missing_ok=True)
            import shutil
            shutil.rmtree(f'{output_dir}/{accession}', ignore_errors=True)
        except:
            pass
    
    # Save results
    if downloaded:
        df = pd.DataFrame(downloaded)
        df.to_csv(f'{output_dir}/downloaded_strains.csv', index=False)
        print(f"\n✓ Downloaded {len(downloaded)} proteomes")
    
    if failed:
        df_failed = pd.DataFrame(failed)
        df_failed.to_csv(f'{output_dir}/failed_downloads.csv', index=False)
        print(f"✗ Failed to download {len(failed)} proteomes")
        
        # Show failure summary
        from collections import Counter
        failure_counts = Counter([f['reason'] for f in failed])
        print("\nFailure reasons:")
        for reason, count in failure_counts.items():
            print(f"  {reason}: {count}")
    
    return downloaded


def main():
    import argparse
    
    SPECIES_LIST = [
    # Marine picocyanobacteria
    "Prochlorococcus marinus",
    "Synechococcus sp.",
    
    # Model freshwater strains
    "Synechocystis sp. PCC 6803",
    "Synechococcus elongatus",
    
    # Nitrogen-fixing (heterocystous)
    "Nostoc sp.",
    "Nostoc punctiforme",
    "Anabaena sp.",
    "Anabaena variabilis",
    "Nostoc sp. PCC 7120",
    "Cylindrospermopsis raciborskii",
    "Calothrix sp.",
    "Fischerella sp.",
    
    # Bloom-forming/toxic
    "Microcystis aeruginosa",
    "Planktothrix agardhii",
    "Dolichospermum sp.",
    "Aphanizomenon flos-aquae",
    
    # Marine nitrogen-fixers
    "Trichodesmium erythraeum",
    "Crocosphaera watsonii",
    "Richelia intracellularis",
    
    # Thermophiles
    "Thermosynechococcus elongatus",
    "Synechococcus lividus",
    
    # Unicellular nitrogen-fixers
    "Cyanothece sp.",
    
    # Primitive/early-diverging
    "Gloeobacter violaceus",
    "Gloeobacter kilaueensis",
    
    # Filamentous non-heterocystous
    "Arthrospira platensis",
    "Leptolyngbya sp.",
    "Oscillatoria sp.",
    "Phormidium sp.",
    
    # Other important genera
    "Acaryochloris marina",
    "Pleurocapsa sp.",
    "Chroococcidiopsis sp.",]
    
    parser = argparse.ArgumentParser(description='Download cyanobacteria genomes from NCBI')
    parser.add_argument('--species', '-s', help='Single species to download (overrides default list)')
    parser.add_argument('--output-dir', '-o', default='genomes', help='Output directory (default: genomes)')
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    
    if args.species:
        SPECIES_LIST = [args.species]
    else:
        print("No species provided. Using default cyanobacteria list.")
        print("To specify a species, use the --species/-s argument.")
        print("You can also specify an output directory with --output-dir/-o.")
        print()
    
    assemblies = search_ncbi_genomes(SPECIES_LIST, output_dir)
    
    if assemblies:
        print(f"\nAssembly levels:")
        assembly_df = pd.DataFrame(assemblies)
        print(assembly_df['assembly_level'].value_counts())
        
        # Ask for download limit
        print(f"\nFound {len(assemblies)} total genomes.")
        limit_input = input("Enter max downloads (or press Enter for all): ").strip()
        if limit_input.isdigit():
            max_downloads = int(limit_input)
            assemblies = assemblies[:max_downloads]
            print(f"Will download first {max_downloads} genomes")
        
        downloaded = download_proteomes(assemblies, output_dir)
        
        if downloaded:
            print(f"\n{'='*80}")
            print("FILES READY FOR ANALYSIS")
            print(f"{'='*80}")
            print(f"Location: {output_dir}/")
            print(f"Manifest: {output_dir}/downloaded_strains.csv")
            
            # Show genus breakdown
            downloaded_df = pd.DataFrame(downloaded)
            if 'genus' in downloaded_df.columns:
                genus_summary = downloaded_df['genus'].value_counts()
                print(f"\nDownloaded by genus:")
                print(genus_summary.to_string())
        else:
            print("\n❌ No proteomes downloaded successfully!")
            print("Check failed_downloads.csv for details")

if __name__ == '__main__':
    main()