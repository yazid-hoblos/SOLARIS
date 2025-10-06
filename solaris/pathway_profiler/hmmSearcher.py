#!/usr/bin/env python3
"""
HMMSearcher: Run HMM search using pyhmmer and extract hits below E-value threshold.
"""

import pyhmmer
from pathlib import Path
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class HMMHit:
    """Data class for HMM search hit"""
    target: str
    query: str
    evalue: float
    score: float
    bias: float


class HMMSearcher:
    """
    Run HMM searches using pyhmmer and manage results
    """
    
    def __init__(self, evalue_threshold: float = 1e-5, cpus: int = 0):
        """
        Initialize HMMSearcher
        
        Args:
            evalue_threshold: E-value threshold for filtering hits (default: 1e-5)
            cpus: Number of CPUs to use (0 = all available)
        """
        self.evalue_threshold = evalue_threshold
        self.cpus = cpus
        self.hmms = []
        self.sequences = []
        self.hits = []
        self.hit_ids = []
    
    def load_hmm_profiles(self, hmm_file: str) -> int:
        """
        Load HMM profiles from file
        
        Args:
            hmm_file: Path to HMM file
            
        Returns:
            Number of HMM profiles loaded
        """
        hmm_path = Path(hmm_file)
        
        if not hmm_path.exists():
            raise FileNotFoundError(f"HMM file not found: {hmm_file}")
        
        print(f"Loading HMM profiles from {hmm_file}...")
        
        try:
            with pyhmmer.plan7.HMMFile(str(hmm_path)) as hmm_file_handle:
                self.hmms = list(hmm_file_handle)
            
            print(f"✓ Loaded {len(self.hmms)} HMM profile(s)")
            
            # Display loaded HMM names
            if self.hmms:
                print(f"  HMM profiles:")
                for i, hmm in enumerate(self.hmms[:10], 1):
                    print(f"    {i}. {hmm.name.decode()}")
                if len(self.hmms) > 10:
                    print(f"    ... and {len(self.hmms) - 10} more")
            
            return len(self.hmms)
            
        except Exception as e:
            print(f"Error loading HMM profiles: {e}", file=sys.stderr)
            raise
    
    def load_sequences(self, fasta_file: str) -> int:
        """
        Load protein sequences from FASTA file
        
        Args:
            fasta_file: Path to protein FASTA file
            
        Returns:
            Number of sequences loaded
        """
        fasta_path = Path(fasta_file)
        
        if not fasta_path.exists():
            raise FileNotFoundError(f"FASTA file not found: {fasta_file}")
        
        print(f"\nLoading protein sequences from {fasta_file}...")
        
        try:
            with pyhmmer.easel.SequenceFile(str(fasta_path), digital=True) as seq_file:
                self.sequences = list(seq_file)
            
            print(f"✓ Loaded {len(self.sequences)} protein sequences")
            
            return len(self.sequences)
            
        except Exception as e:
            print(f"Error loading sequences: {e}", file=sys.stderr)
            raise
    
    def run_search(self) -> Tuple[List[str], List[HMMHit]]:
        """
        Run HMM search with loaded profiles and sequences
        
        Returns:
            Tuple of (hit_ids: list, hits: list of HMMHit objects)
        """
        if not self.hmms:
            raise ValueError("No HMM profiles loaded. Call load_hmm_profiles() first.")
        
        if not self.sequences:
            raise ValueError("No sequences loaded. Call load_sequences() first.")
        
        print(f"\nRunning hmmsearch...")
        print(f"E-value threshold: {self.evalue_threshold}")
        print(f"CPUs: {self.cpus if self.cpus > 0 else 'all available'}")
        
        hit_ids = []
        all_hits = []
        
        # Search each HMM against the sequences
        for hmm_idx, hmm in enumerate(self.hmms, 1):
            hmm_name = hmm.name.decode()
            print(f"  [{hmm_idx}/{len(self.hmms)}] Searching with HMM: {hmm_name}", end='')
            
            hit_count = 0
            
            # Run the search
            for hits in pyhmmer.hmmsearch(hmm, self.sequences, cpus=self.cpus):
                # Filter hits by E-value
                for hit in hits:
                    if hit.evalue < self.evalue_threshold:
                        target_name = hit.name.decode()
                        hit_ids.append(target_name)
                        
                        hit_obj = HMMHit(
                            target=target_name,
                            query=hmm_name,
                            evalue=hit.evalue,
                            score=hit.score,
                            bias=hit.bias
                        )
                        all_hits.append(hit_obj)
                        hit_count += 1
            
            print(f" → {hit_count} hits")
        
        print(f"\n✓ Search completed")
        print(f"✓ Found {len(hit_ids)} total hits with E-value < {self.evalue_threshold}")
        
        # Store in instance variables
        self.hit_ids = hit_ids
        self.hits = all_hits
        
        return hit_ids, all_hits
    
    def save_hits_table(self, output_file: str = 'hits_table.txt') -> str:
        """
        Save detailed hits table to file
        
        Args:
            output_file: Path to output file
            
        Returns:
            Path to output file
        """
        if not self.hits:
            print("Warning: No hits to save", file=sys.stderr)
            return output_file
        
        print(f"\nSaving detailed results to {output_file}...")
        
        try:
            with open(output_file, 'w') as f:
                # Write header
                f.write("# target_name\tquery_name\te_value\tscore\tbias\n")
                
                # Write hits
                for hit in self.hits:
                    f.write(f"{hit.target}\t{hit.query}\t{hit.evalue:.2e}\t"
                           f"{hit.score:.1f}\t{hit.bias:.1f}\n")
            
            print(f"✓ Saved {len(self.hits)} hits to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error saving hits table: {e}", file=sys.stderr)
            raise
    
    def save_unique_ids(self, output_file: str = 'unique_hits_ids.txt') -> str:
        """
        Save unique hit IDs to file
        
        Args:
            output_file: Path to output file
            
        Returns:
            Path to output file
        """
        if not self.hit_ids:
            print("Warning: No hit IDs to save", file=sys.stderr)
            return output_file
        
        unique_ids = sorted(set(self.hit_ids))
        
        try:
            with open(output_file, 'w') as f:
                for uid in unique_ids:
                    f.write(uid + '\n')
            
            print(f"✓ Saved {len(unique_ids)} unique IDs to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error saving unique IDs: {e}", file=sys.stderr)
            raise
    
    def save_results(self, hits_table: str = 'hits_table.txt',
                    unique_hits_file: str = 'unique_hits_ids.txt'):
        """
        Save both hits table and unique IDs
        
        Args:
            hits_table: Output file for detailed hits table
            unique_hits_file: Output file for unique IDs
        """
        self.save_hits_table(hits_table)
        self.save_unique_ids(unique_hits_file)
    
    def print_statistics(self):
        """
        Print statistics about the search results
        """
        if not self.hits:
            print("\nNo hits to report")
            return
        
        unique_ids = sorted(set(self.hit_ids))
        
        print(f"\nStatistics:")
        print(f"  Total hits: {len(self.hit_ids)}")
        print(f"  Unique proteins: {len(unique_ids)}")
        print(f"  HMM profiles searched: {len(self.hmms)}")
        
        # Count hits per HMM
        hmm_hit_counts = {}
        for hit in self.hits:
            hmm_hit_counts[hit.query] = hmm_hit_counts.get(hit.query, 0) + 1
        
        print(f"\nHits per HMM profile:")
        for hmm_name, count in sorted(hmm_hit_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {hmm_name}: {count} hits")
        if len(hmm_hit_counts) > 10:
            print(f"  ... and {len(hmm_hit_counts) - 10} more HMMs")
    
    def print_example_hits(self, n: int = 10):
        """
        Print example hits
        
        Args:
            n: Number of examples to show
        """
        if not self.hits:
            return
        
        unique_ids = sorted(set(self.hit_ids))
        
        # Show some examples
        if unique_ids:
            print(f"\nExample hits (first {min(n, len(unique_ids))}):")
            for uid in unique_ids[:n]:
                print(f"  {uid}")
            if len(unique_ids) > n:
                print(f"  ... and {len(unique_ids) - n} more")
    
    def print_top_hits(self, n: int = 10):
        """
        Print top hits by E-value
        
        Args:
            n: Number of top hits to show
        """
        if not self.hits:
            return
        
        print(f"\nTop {min(n, len(self.hits))} hits by E-value:")
        sorted_hits = sorted(self.hits, key=lambda x: x.evalue)
        
        for hit in sorted_hits[:n]:
            print(f"  {hit.target}: E={hit.evalue:.2e}, Score={hit.score:.1f} (HMM: {hit.query})")
    
    def get_statistics(self) -> Dict:
        """
        Get statistics as a dictionary
        
        Returns:
            Dictionary with statistics
        """
        unique_ids = set(self.hit_ids) if self.hit_ids else set()
        
        # Count hits per HMM
        hmm_hit_counts = {}
        for hit in self.hits:
            hmm_hit_counts[hit.query] = hmm_hit_counts.get(hit.query, 0) + 1
        
        return {
            'total_hits': len(self.hit_ids),
            'unique_proteins': len(unique_ids),
            'hmm_profiles_searched': len(self.hmms),
            'sequences_searched': len(self.sequences),
            'evalue_threshold': self.evalue_threshold,
            'hits_per_hmm': hmm_hit_counts
        }
    
    def filter_hits_by_evalue(self, new_threshold: float) -> List[HMMHit]:
        """
        Re-filter existing hits with a new E-value threshold
        
        Args:
            new_threshold: New E-value threshold
            
        Returns:
            List of filtered HMMHit objects
        """
        if not self.hits:
            return []
        
        filtered = [hit for hit in self.hits if hit.evalue < new_threshold]
        
        print(f"Filtered to {len(filtered)} hits with E-value < {new_threshold}")
        
        return filtered
    
    def run(self, hmm_file: str, fasta_file: str,
            hits_table: str = 'hits_table.txt',
            unique_hits_file: str = 'unique_hits_ids.txt') -> bool:
        """
        Complete workflow: load, search, and save results
        
        Args:
            hmm_file: Path to HMM file
            fasta_file: Path to protein FASTA file
            hits_table: Output file for detailed hits table
            unique_hits_file: Output file for unique IDs
            
        Returns:
            True if successful, False otherwise
        """
        print("="*60)
        print("HMMSearcher: HMM Profile Search")
        print("="*60)
        print(f"E-value threshold: {self.evalue_threshold}")
        print(f"CPUs: {self.cpus if self.cpus > 0 else 'all available'}")
        print("="*60)
        
        try:
            # Load HMM profiles
            self.load_hmm_profiles(hmm_file)
            
            # Load sequences
            self.load_sequences(fasta_file)
            
            # Run search
            hit_ids, all_hits = self.run_search()
            
            if not hit_ids:
                print("\n⚠ No hits found below threshold")
                return False
            
            # Save results
            self.save_results(hits_table, unique_hits_file)
            
            # Print statistics and examples
            self.print_statistics()
            self.print_example_hits()
            self.print_top_hits()
            
            print("\n✓ Done!")
            print(f"\nOutput files:")
            print(f"  - Detailed hits: {hits_table}")
            print(f"  - Unique IDs: {unique_hits_file}")
            
            return True
            
        except Exception as e:
            print(f"\nError during HMM search: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Command-line interface
    """
    if len(sys.argv) != 3:
        print("Usage: python pyhmmer_run.py <hmm_file> <fasta_file>")
        print("\nExample:")
        print("  python pyhmmer_run.py selected_pfam.hmm proteins.fasta")
        print("\nArguments:")
        print("  hmm_file   : Path to HMM profiles file")
        print("  fasta_file : Path to protein FASTA file")
        sys.exit(1)
    
    hmm_file = sys.argv[1]
    fasta_file = sys.argv[2]
    
    # Create searcher instance
    searcher = HMMSearcher(
        evalue_threshold=1e-5,
        cpus=0  # Use all available CPUs
    )
    
    # Run the complete workflow
    success = searcher.run(
        hmm_file=hmm_file,
        fasta_file=fasta_file,
        hits_table='hits_table.txt',
        unique_hits_file='unique_hits_ids.txt'
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()