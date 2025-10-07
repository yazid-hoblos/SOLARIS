#!/usr/bin/env python3
"""
Download cyanobacteria proteomes from multiple genera
"""

import subprocess
import json
import pandas as pd
from pathlib import Path
import sys
import time
from collections import defaultdict

def search_genus_genomes(genus_name, output_dir='genomes'):
    """Search NCBI for all GCF assemblies of a genus."""
    
    print(f"  Searching: {genus_name}... ", end='', flush=True)
    
    search_cmd = [
        'datasets', 'summary', 'genome', 'taxon', genus_name,
        '--assembly-source', 'refseq',  # Only GCF
        '--as-json-lines'
    ]
    
    try:
        result = subprocess.run(search_cmd, capture_output=True, text=True, check=True, timeout=30)
        
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
                        'genus': genus_name
                    })
                except json.JSONDecodeError:
                    continue
        
        print(f"✓ {len(assemblies)} genomes")
        return assemblies
        
    except subprocess.TimeoutExpired:
        print("✗ Timeout")
        return []
    except subprocess.CalledProcessError as e:
        print("✗ Error")
        return []
    except Exception as e:
        print(f"✗ Error")
        return []


def download_proteomes_batch(assemblies, output_dir='genomes', max_downloads=None):
    """Download protein FASTA files with robust error handling."""
    
    if max_downloads:
        assemblies = assemblies[:max_downloads]
    
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
            print(f"[{idx}/{len(assemblies)}] {genus} {accession}... ✓ (exists)")
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
            # Add delay to avoid rate limiting
            if idx > 1 and idx % 10 == 0:
                time.sleep(2)  # Longer pause every 10 downloads
            elif idx > 1:
                time.sleep(0.3)
            
            # Download with timeout
            download_result = subprocess.run([
                'datasets', 'download', 'genome', 'accession', accession,
                '--include', 'protein',
                '--filename', f'{output_dir}/{accession}.zip'
            ], check=True, capture_output=True, timeout=90)
            
            # Check if download actually worked
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
                
                # Remove extraction directory
                import shutil
                shutil.rmtree(f'{output_dir}/{accession}', ignore_errors=True)
                
            else:
                raise Exception("No protein file found or file too small")
            
        except subprocess.TimeoutExpired:
            print("✗")
            failed.append({'accession': accession, 'genus': genus, 'reason': 'timeout'})
        except subprocess.CalledProcessError as e:
            print("✗")
            if e.stderr:
                error_msg = e.stderr.decode().strip()
                if 'No assemblies found' in error_msg:
                    failed.append({'accession': accession, 'genus': genus, 'reason': 'not_found'})
                elif 'rate limit' in error_msg.lower():
                    failed.append({'accession': accession, 'genus': genus, 'reason': 'rate_limit'})
                    print("  Rate limited, waiting 30 seconds...")
                    time.sleep(30)
                else:
                    failed.append({'accession': accession, 'genus': genus, 'reason': 'api_error'})
            else:
                failed.append({'accession': accession, 'genus': genus, 'reason': 'unknown_api'})
        except Exception as e:
            print("✗")
            failed.append({'accession': accession, 'genus': genus, 'reason': str(e)[:50]})
            
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
        df.to_csv(f'{output_dir}/downloaded_cyanobacteria.csv', index=False)
        print(f"\n✓ Downloaded {len(downloaded)} proteomes")
    
    if failed:
        df_failed = pd.DataFrame(failed)
        df_failed.to_csv(f'{output_dir}/failed_downloads.csv', index=False)
        print(f"✗ Failed to download {len(failed)} proteomes")
        
        # Print failure summary
        from collections import Counter
        failure_counts = Counter([f['reason'] for f in failed])
        print("\nFailure reasons:")
        for reason, count in failure_counts.items():
            print(f"  {reason}: {count}")
    
    return downloaded, failed


def main():
    output_dir = input("Enter directory name for proteomes (e.g., 'cyanobacteria_proteomes'): ").strip()
    if not output_dir:
        output_dir = 'cyanobacteria_proteomes'
    
    Path(output_dir).mkdir(exist_ok=True)
    
    print()
    print("="*80)
    print("DOWNLOADING CYANOBACTERIA PROTEOMES")
    print("="*80)
    
    # Define cyanobacteria genera to search
    genera = [
        'Prochlorococcus',
        'Synechococcus', 
        'Synechocystis',
        'Nostoc',
        'Anabaena',
        'Microcystis',
        'Trichodesmium',
        'Cyanothece',
        'Gloeobacter',
        'Thermosynechococcus'
    ]
    
    print("\n1. Searching NCBI...")
    all_assemblies = []
    genus_counts = defaultdict(int)
    
    for genus in genera:
        assemblies = search_genus_genomes(genus, output_dir)
        all_assemblies.extend(assemblies)
        genus_counts[genus] = len(assemblies)
    
    print(f"\n✓ Total genomes found: {len(all_assemblies)}")
    
    if all_assemblies:
        # Show genus distribution
        print("\nGenomes per genus:")
        genus_df = pd.DataFrame(list(genus_counts.items()), columns=['genus', 'count'])
        genus_df = genus_df.sort_values('count', ascending=False)
        print(genus_df.to_string(index=False))
        
        # Ask user for download limit
        print(f"\nFound {len(all_assemblies)} total genomes.")
        limit_input = input("Enter max downloads (or press Enter for all): ").strip()
        max_downloads = None
        if limit_input.isdigit():
            max_downloads = int(limit_input)
            print(f"Will download first {max_downloads} genomes")
        
        # Download proteomes
        downloaded, failed = download_proteomes_batch(all_assemblies, output_dir, max_downloads)
        
        if downloaded:
            print(f"\n{'='*80}")
            print("DOWNLOAD SUMMARY")
            print(f"{'='*80}")
            print(f"Successfully downloaded: {len(downloaded)} proteomes")
            print(f"Failed downloads: {len(failed)} proteomes")
            print(f"Location: {output_dir}/")
            print(f"Manifest: {output_dir}/downloaded_cyanobacteria.csv")
            
            # Show genus breakdown of downloaded
            downloaded_df = pd.DataFrame(downloaded)
            if 'genus' in downloaded_df.columns:
                genus_summary = downloaded_df['genus'].value_counts()
                print(f"\nDownloaded by genus:")
                print(genus_summary.to_string())
        else:
            print("\n❌ No proteomes were successfully downloaded!")
            print("This might be due to:")
            print("1. Network connectivity issues")
            print("2. NCBI API rate limiting")
            print("3. Missing ncbi-datasets-cli tool")
            print("4. Authentication issues")
            
            print("\nTroubleshooting:")
            print("- Check internet connection")
            print("- Install: conda install -c conda-forge ncbi-datasets-cli")
            print("- Try running: datasets --help")
            print("- Wait and try again (rate limiting)")


if __name__ == '__main__':
    main()