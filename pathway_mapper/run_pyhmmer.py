#!/usr/bin/env python3
"""
Run HMM search using pyhmmer and extract hits below E-value threshold.
"""

import pyhmmer
from pathlib import Path
import sys

def run_hmmsearch_pyhmmer(hmm_file, fasta_file, evalue_threshold=1e-5):
    """
    Run hmmsearch using pyhmmer.
    
    Args:
        hmm_file: Path to HMM file
        fasta_file: Path to protein FASTA file
        evalue_threshold: E-value threshold (default: 1e-5)
    
    Returns:
        List of hit IDs and full results
    """
    print(f"Loading HMM profiles from {hmm_file}...")
    
    # Read HMM profiles
    with pyhmmer.plan7.HMMFile(hmm_file) as hmm_file_handle:
        hmms = list(hmm_file_handle)
    
    print(f"✓ Loaded {len(hmms)} HMM profile(s)")
    
    # Read protein sequences
    print(f"\nLoading protein sequences from {fasta_file}...")
    with pyhmmer.easel.SequenceFile(fasta_file, digital=True) as seq_file:
        sequences = list(seq_file)
    
    print(f"✓ Loaded {len(sequences)} protein sequences")
    
    # Run hmmsearch
    print(f"\nRunning hmmsearch...")
    print(f"E-value threshold: {evalue_threshold}")
    
    hit_ids = []
    all_hits = []
    
    # Search each HMM against the sequences
    for hmm in hmms:
        print(f"  Searching with HMM: {hmm.name.decode()}")
        
        # Run the search
        for hits in pyhmmer.hmmsearch(hmm, sequences, cpus=0):  # cpus=0 uses all available
            # Filter hits by E-value
            for hit in hits:
                if hit.evalue < evalue_threshold:
                    target_name = hit.name.decode()
                    hit_ids.append(target_name)
                    all_hits.append({
                        'target': target_name,
                        'query': hmm.name.decode(),
                        'evalue': hit.evalue,
                        'score': hit.score,
                        'bias': hit.bias
                    })
    
    print(f"\n✓ Search completed")
    print(f"✓ Found {len(hit_ids)} hits with E-value < {evalue_threshold}")
    
    return hit_ids, all_hits

def save_results(hit_ids, all_hits, hits_table='hits_table.txt', unique_hits_file='unique_hits_ids.txt'):
    """
    Save results to files.
    
    Args:
        hit_ids: List of all hit IDs
        all_hits: List of dictionaries with hit details
        hits_table: Output file for detailed hits table
        unique_hits_file: Output file for unique IDs
    """
    # Save detailed hits table
    print(f"\nSaving detailed results to {hits_table}...")
    with open(hits_table, 'w') as f:
        # Write header
        f.write("# target_name\tquery_name\te_value\tscore\tbias\n")
        
        # Write hits
        for hit in all_hits:
            f.write(f"{hit['target']}\t{hit['query']}\t{hit['evalue']:.2e}\t"
                   f"{hit['score']:.1f}\t{hit['bias']:.1f}\n")
    
    print(f"✓ Saved {len(all_hits)} hits to {hits_table}")
    
    # Save unique IDs
    unique_ids = sorted(set(hit_ids))
    
    with open(unique_hits_file, 'w') as f:
        for uid in unique_ids:
            f.write(uid + '\n')
    
    print(f"✓ Saved {len(unique_ids)} unique IDs to {unique_hits_file}")
    
    # Show statistics
    print(f"\nStatistics:")
    print(f"  Total hits: {len(hit_ids)}")
    print(f"  Unique proteins: {len(unique_ids)}")
    
    # Show some examples
    if unique_ids:
        print(f"\nExample hits (first 10):")
        for uid in unique_ids[:10]:
            print(f"  {uid}")
        if len(unique_ids) > 10:
            print(f"  ... and {len(unique_ids) - 10} more")
    
    # Show top hits by E-value
    if all_hits:
        print(f"\nTop 10 hits by E-value:")
        sorted_hits = sorted(all_hits, key=lambda x: x['evalue'])
        for hit in sorted_hits[:10]:
            print(f"  {hit['target']}: E={hit['evalue']:.2e}, Score={hit['score']:.1f} (HMM: {hit['query']})")

def main():
    if len(sys.argv) != 3:
        print("Usage: python pyhmmer_run.py <hmm_file> <fasta_file>")
        sys.exit(1)
    # Configuration
    hmm_file = sys.argv[1] 
    fasta_file = sys.argv[2]
    hits_table = 'hits_table.txt'
    unique_hits_file = 'unique_hits_ids.txt'
    evalue_threshold = 1e-5
    
    # Check if input files exist
    if not Path(hmm_file).exists():
        print(f"Error: HMM file not found: {hmm_file}", file=sys.stderr)
        sys.exit(1)
    
    if not Path(fasta_file).exists():
        print(f"Error: FASTA file not found: {fasta_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Run hmmsearch
        hit_ids, all_hits = run_hmmsearch_pyhmmer(hmm_file, fasta_file, evalue_threshold)
        
        if not hit_ids:
            print("\n⚠ No hits found below threshold")
            return
        
        # Save results
        save_results(hit_ids, all_hits, hits_table, unique_hits_file)
        
        print("\n✓ Done!")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()