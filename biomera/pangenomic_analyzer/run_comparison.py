#!/usr/bin/env python3
"""
Step 2: Run pathway analysis on all strains using pyhmmer.
"""

import pandas as pd
import pyhmmer
from pathlib import Path
import sys
from collections import defaultdict

def batch_hmmsearch_pyhmmer(strains_df, hmm_file='selected_pfam.hmm', evalue_threshold=1e-5):
    """Run hmmsearch using pyhmmer on all strains."""
    
    if not Path(hmm_file).exists():
        print(f"Error: {hmm_file} not found")
        sys.exit(1)
    
    Path('results/batch').mkdir(parents=True, exist_ok=True)
    
    # Load HMM profiles once
    print("Loading HMM profiles...")
    with pyhmmer.plan7.HMMFile(hmm_file) as hmm_file_handle:
        hmms = list(hmm_file_handle)
    print(f"✓ Loaded {len(hmms)} HMM profiles")
    
    print(f"\nRunning HMM search on {len(strains_df)} strains...")
    print("="*80)
    
    for idx, row in strains_df.iterrows():
        strain = row['strain']
        fasta = row['file']
        accession = row['accession']
        
        print(f"\n[{idx+1}/{len(strains_df)}] {strain} ({accession})")
        
        if not Path(fasta).exists():
            print(f"  ✗ File not found: {fasta}")
            continue
        
        try:
            # Load sequences
            with pyhmmer.easel.SequenceFile(fasta, digital=True) as seq_file:
                sequences = list(seq_file)
            
            print(f"  Loaded {len(sequences)} sequences")
            
            # Run hmmsearch
            all_hits = []
            
            for hmm in hmms:
                for hits in pyhmmer.hmmsearch(hmm, sequences, cpus=0):
                    for hit in hits:
                        if hit.evalue < evalue_threshold:
                            all_hits.append({
                                'target': hit.name.decode(),
                                'query_hmm': hmm.name.decode(),
                                'evalue': hit.evalue,
                                'score': hit.score,
                                'bias': hit.bias
                            })
            
            print(f"  ✓ Found {len(all_hits)} hits (E-value < {evalue_threshold})")
            
            # Save hits to file (hmmsearch tblout format)
            output_file = f"results/batch/{strain}_{accession}_hits.txt"
            with open(output_file, 'w') as f:
                f.write("# target_name\tquery_name\te_value\tscore\tbias\n")
                for hit in all_hits:
                    f.write(f"{hit['target']}\t{hit['query_hmm']}\t{hit['evalue']:.2e}\t"
                           f"{hit['score']:.1f}\t{hit['bias']:.1f}\n")
            
            print(f"  ✓ Saved to {output_file}")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            import traceback
            traceback.print_exc()


def analyze_single_strain(hits_file, pfam_ids_file, hmm_file, output_prefix):
    """Analyze results for a single strain."""
    
    # Load EC to Pfam mapping
    ec_pfam_df = pd.read_csv(pfam_ids_file, sep='\t')
    
    # Load hits
    hits_df = pd.read_csv(hits_file, sep='\t', comment='#',
                         names=['target', 'query_hmm', 'evalue', 'score', 'bias'])
    
    # Parse HMM file to map NAME to Pfam ID
    name_to_id = {}
    with open(hmm_file) as f:
        current_name = None
        for line in f:
            if line.startswith('NAME'):
                current_name = line.strip().split()[1]
            elif line.startswith('ACC') and current_name:
                acc = line.strip().split()[1]
                pfam_id = acc.split('.')[0]
                name_to_id[current_name] = pfam_id
                current_name = None
    
    # Map query names to Pfam IDs
    hits_df['pfam_id'] = hits_df['query_hmm'].map(name_to_id)
    
    # Get found Pfam IDs
    found_pfam_ids = set(hits_df['pfam_id'].dropna().unique())
    
    # Analyze EC numbers
    ec_status = defaultdict(lambda: {
        'searched': set(),
        'found': set(),
        'not_found': set(),
        'protein_names': set(),
        'hit_count': 0,
        'hit_proteins': set()
    })
    
    for _, row in ec_pfam_df.iterrows():
        ec = row['EC_number']
        pfam_id = row['Pfam_ID']
        protein_name = row['Protein_Name']
        
        ec_status[ec]['searched'].add(pfam_id)
        ec_status[ec]['protein_names'].add(protein_name)
        
        if pfam_id in found_pfam_ids:
            ec_status[ec]['found'].add(pfam_id)
            pfam_hits = hits_df[hits_df['pfam_id'] == pfam_id]
            ec_status[ec]['hit_count'] += len(pfam_hits)
            ec_status[ec]['hit_proteins'].update(pfam_hits['target'])
        else:
            ec_status[ec]['not_found'].add(pfam_id)
    
    # Create results DataFrame
    results = []
    for ec, status in ec_status.items():
        total_pfams = len(status['searched'])
        found_pfams = len(status['found'])
        
        if found_pfams == total_pfams:
            status_label = 'FULLY_FOUND'
        elif found_pfams > 0:
            status_label = 'PARTIALLY_FOUND'
        else:
            status_label = 'NOT_FOUND'
        
        results.append({
            'EC_number': ec,
            'Status': status_label,
            'Protein_names': '; '.join(status['protein_names']),
            'Total_Pfam_domains': total_pfams,
            'Found_Pfam_domains': found_pfams,
            'Total_hits': status['hit_count'],
            'Unique_proteins_with_hits': len(status['hit_proteins'])
        })
    
    results_df = pd.DataFrame(results)
    results_df.to_csv(f'{output_prefix}_ec_results.csv', index=False)
    
    return results_df


def analyze_all_results(strains_df, pfam_ids_file='pfam_ids.txt', hmm_file='selected_pfam.hmm'):
    """Analyze all strain results."""
    
    print(f"\nAnalyzing results for {len(strains_df)} strains...")
    print("="*80)
    
    for idx, row in strains_df.iterrows():
        strain = row['strain']
        accession = row['accession']
        
        hits_file = f"results/batch/{strain}_{accession}_hits.txt"
        
        if not Path(hits_file).exists():
            print(f"[{idx+1}/{len(strains_df)}] Skipping {strain} - no hits file")
            continue
        
        print(f"\n[{idx+1}/{len(strains_df)}] Analyzing {strain}...")
        
        try:
            results_df = analyze_single_strain(
                hits_file, 
                pfam_ids_file, 
                hmm_file,
                f"results/batch/{strain}_{accession}"
            )
            
            # Summary
            status_counts = results_df['Status'].value_counts()
            print(f"  Fully found: {status_counts.get('FULLY_FOUND', 0)}")
            print(f"  Partially found: {status_counts.get('PARTIALLY_FOUND', 0)}")
            print(f"  Not found: {status_counts.get('NOT_FOUND', 0)}")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_comparison.py <hmm_file> <pfam_ids_file>")
        sys.exit(1)
        
    # Load downloaded strains
    strains_df = pd.read_csv('genomes/downloaded_strains.csv')
    
    print(f"Found {len(strains_df)} strains to analyze")
    
    
    hmm_file = sys.argv[1] 
    pfam_ids_file = sys.argv[2]
    # Run HMM search on all using pyhmmer
    batch_hmmsearch_pyhmmer(strains_df, hmm_file)
    
    # Analyze all results
    analyze_all_results(strains_df, pfam_ids_file, hmm_file)
    
    print("\n✓ Batch analysis complete")
    print("Results in: results/batch/")

if __name__ == '__main__':
    main()