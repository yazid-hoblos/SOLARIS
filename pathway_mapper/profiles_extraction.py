#!/usr/bin/env python3
"""
Extract Pfam versions using grep and fetch HMM profiles using hmmfetch.
"""

import csv
import subprocess
import sys
from pathlib import Path

def extract_pfam_versions_with_grep(pfam_path, pfam_ids):
    """
    Use grep to extract version numbers for given Pfam IDs from Pfam-A.hmm file.
    Much faster than reading the file in Python.
    
    Args:
        pfam_hmm_file: Path to Pfam-A.hmm file
        pfam_ids: Set of Pfam IDs to search for
    
    Returns:
        Dictionary mapping Pfam IDs to their versions
    """
    pfam_hmm_file = Path(pfam_path) / 'Pfam-A.hmm'
    pfam_versions = {}
    
    print(f"Using grep to search for {len(pfam_ids)} Pfam IDs...")
    
    for pfam_id in pfam_ids:
        try:
            # Run grep -F for exact string matching
            result = subprocess.run(
                ['grep', '-F', pfam_id, pfam_hmm_file],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse the output to find ACC lines
            for line in result.stdout.splitlines():
                if line.startswith('ACC'):
                    # Extract the version from "ACC   PF00106.31"
                    acc_field = line.strip().split()[1]
                    if acc_field.startswith(pfam_id):
                        pfam_versions[pfam_id] = acc_field
                        break
            
        except Exception as e:
            print(f"Warning: Error grepping for {pfam_id}: {e}", file=sys.stderr)
    
    return pfam_versions

def fetch_hmms(pfam_path, versions_file, output_hmm_file):
    """
    Use hmmfetch to extract HMM profiles based on version file.
    
    Args:
        pfam_hmm_file: Path to Pfam-A.hmm file
        versions_file: File containing Pfam IDs with versions (one per line)
        output_hmm_file: Output file for fetched HMMs
    """
    pfam_hmm_file = Path(pfam_path) / 'Pfam-A.hmm'
    try:
        print(f"\nRunning hmmfetch to extract HMM profiles...")
        print(f"Command: hmmfetch -f {pfam_hmm_file} {versions_file} > {output_hmm_file}")
        
        with open(output_hmm_file, 'w') as outfile:
            result = subprocess.run(
                ['hmmfetch', '-f', pfam_hmm_file, versions_file],
                stdout=outfile,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        print(f"✓ HMM profiles successfully written to {output_hmm_file}")
        
        # Show file size
        size = Path(output_hmm_file).stat().st_size
        print(f"  Output file size: {size:,} bytes")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running hmmfetch: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: hmmfetch not found. Make sure HMMER is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: python profiles_extraction.py <pfam_ids_file> <pfam_path>")
        sys.exit(1)
    
    # Configuration
    pfam_ids_file = sys.argv[1] 
    pfam_path = sys.argv[2]
    versions_file = 'pfam_versions.txt'
    output_hmm_file = 'selected_pfam.hmm'
    
    # Read unique Pfam IDs from input file
    print(f"Reading Pfam IDs from {pfam_ids_file}...")
    pfam_ids = set()
    with open(pfam_ids_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            pfam_ids.add(row['Pfam_ID'])
    
    print(f"Found {len(pfam_ids)} unique Pfam IDs")
    
    # Extract versions using grep
    pfam_versions = extract_pfam_versions_with_grep(pfam_path, pfam_ids)
    
    # Report results
    print(f"\nFound versions for {len(pfam_versions)}/{len(pfam_ids)} Pfam IDs")
        
    with open(versions_file, 'w') as vf:
        for pfam_id in sorted(pfam_ids):
            if pfam_id in pfam_versions:
                vf.write(f"{pfam_versions[pfam_id]}\n")
                
    # Check for missing IDs
    missing = pfam_ids - set(pfam_versions.keys())
    if missing:
        print(f"\n⚠ Warning: No version found for {len(missing)} Pfam IDs:")
        for pfam_id in sorted(missing):
            print(f"  {pfam_id}")
    
    # Run hmmfetch if we have versions
    if pfam_versions:
        fetch_hmms(pfam_path, versions_file, output_hmm_file)
    else:
        print("\n⚠ No Pfam versions found. Skipping hmmfetch step.")
    
    print("\n✓ Done!")

if __name__ == '__main__':
    main()