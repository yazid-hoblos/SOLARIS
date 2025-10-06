#!/usr/bin/env python3
"""
PfamHandler: Extract Pfam versions and fetch HMM profiles using grep and hmmfetch.
"""

import csv
import subprocess
import sys
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple


class PfamHandler:
    """
    Handle Pfam domain extraction and HMM profile fetching
    """
    
    def __init__(self, pfam_path: str):
        """
        Initialize PfamHandler
        
        Args:
            pfam_path: Path to directory containing Pfam-A.hmm file
        """
        self.pfam_path = Path(pfam_path)
        self.pfam_hmm_file = self.pfam_path / 'Pfam-A.hmm'
        self.pfam_versions = {}
        
        # Verify Pfam-A.hmm file exists
        if not self.pfam_hmm_file.exists():
            raise FileNotFoundError(f"Pfam-A.hmm not found at {self.pfam_hmm_file}")
        
        # Verify hmmfetch is available
        if not self._check_hmmfetch_available():
            print("Warning: hmmfetch not found in PATH. HMM extraction will fail.", file=sys.stderr)
    
    def _check_hmmfetch_available(self) -> bool:
        """
        Check if hmmfetch is available in the system PATH
        
        Returns:
            True if hmmfetch is available, False otherwise
        """
        try:
            subprocess.run(
                ['hmmfetch', '-h'],
                capture_output=True,
                check=False
            )
            return True
        except FileNotFoundError:
            return False
    
    def read_pfam_ids_from_file(self, pfam_ids_file: str, 
                                 column_name: str = 'Pfam_ID',
                                 delimiter: str = '\t') -> Set[str]:
        """
        Read unique Pfam IDs from a TSV/CSV file
        
        Args:
            pfam_ids_file: Path to file containing Pfam IDs
            column_name: Name of column containing Pfam IDs
            delimiter: Column delimiter (default: tab)
            
        Returns:
            Set of unique Pfam IDs
        """
        pfam_ids = set()
        
        try:
            print(f"Reading Pfam IDs from {pfam_ids_file}...")
            
            with open(pfam_ids_file, 'r') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                
                if column_name not in reader.fieldnames:
                    raise ValueError(f"Column '{column_name}' not found. Available columns: {reader.fieldnames}")
                
                for row in reader:
                    pfam_id = row.get(column_name, '').strip()
                    if pfam_id and pfam_id != "No Pfam":
                        pfam_ids.add(pfam_id)
            
            print(f"Found {len(pfam_ids)} unique Pfam IDs")
            return pfam_ids
            
        except FileNotFoundError:
            print(f"Error: File '{pfam_ids_file}' not found", file=sys.stderr)
            return set()
        except Exception as e:
            print(f"Error reading Pfam IDs: {e}", file=sys.stderr)
            return set()
    
    def extract_pfam_versions_with_grep(self, pfam_ids: Set[str]) -> Dict[str, str]:
        """
        Use optimized grep to extract version numbers for given Pfam IDs from Pfam-A.hmm file.
        Uses a single grep call with pattern file for maximum efficiency.
        
        Args:
            pfam_ids: Set of Pfam IDs to search for
        
        Returns:
            Dictionary mapping Pfam IDs to their versions (e.g., {'PF00106': 'PF00106.31'})
        """
        pfam_versions = {}
        
        print(f"\nUsing optimized grep to search for {len(pfam_ids)} Pfam IDs...")
        
        try:
            # Create a temporary pattern file for grep -f (much faster than multiple greps)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patterns', delete=False) as pattern_file:
                # Write all Pfam IDs to pattern file, one per line
                for pfam_id in pfam_ids:
                    pattern_file.write(f"^ACC.*{pfam_id}\\..*\n")
                pattern_file_path = pattern_file.name
            
            try:
                # Single grep call using pattern file - much faster!
                # -E: extended regex, -f: pattern file, --line-buffered: for large files
                result = subprocess.run(
                    ['grep', '-E', '-f', pattern_file_path, str(self.pfam_hmm_file)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Parse all ACC lines at once
                for line in result.stdout.splitlines():
                    if line.startswith('ACC'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            acc_field = parts[1]  # e.g., "PF00106.31"
                            # Extract base Pfam ID (before the dot)
                            pfam_base = acc_field.split('.')[0]
                            if pfam_base in pfam_ids:
                                pfam_versions[pfam_base] = acc_field
                
            finally:
                # Clean up temporary file
                import os
                try:
                    os.unlink(pattern_file_path)
                except:
                    pass
                
        except Exception as e:
            print(f"\nWarning: Optimized grep failed, falling back to individual searches: {e}")
            # Fallback to original method if optimized version fails
            return self._extract_pfam_versions_fallback(pfam_ids)
        
        print(f"Found versions for {len(pfam_versions)}/{len(pfam_ids)} Pfam IDs")
        
        # Store in instance variable
        self.pfam_versions = pfam_versions
        
        return pfam_versions
    
    def _extract_pfam_versions_fallback(self, pfam_ids: Set[str]) -> Dict[str, str]:
        """
        Fallback method using individual grep calls (original implementation)
        
        Args:
            pfam_ids: Set of Pfam IDs to search for
        
        Returns:
            Dictionary mapping Pfam IDs to their versions
        """
        pfam_versions = {}
        
        print("Using fallback individual grep searches...")
        
        for i, pfam_id in enumerate(pfam_ids, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(pfam_ids)} Pfam IDs...", end='\r')
            
            try:
                # Run grep -F for exact string matching
                result = subprocess.run(
                    ['grep', '-F', f'ACC   {pfam_id}.', str(self.pfam_hmm_file)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Parse the first matching ACC line
                for line in result.stdout.splitlines():
                    if line.startswith('ACC'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            acc_field = parts[1]
                            if acc_field.startswith(pfam_id + '.'):
                                pfam_versions[pfam_id] = acc_field
                                break
                
            except Exception as e:
                print(f"\nWarning: Error grepping for {pfam_id}: {e}", file=sys.stderr)
        
        return pfam_versions
    
    def save_versions_to_file(self, output_file: str = 'pfam_versions.txt',
                             pfam_ids: Optional[Set[str]] = None) -> str:
        """
        Save Pfam versions to a file (one per line)
        
        Args:
            output_file: Path to output file
            pfam_ids: Optional set of Pfam IDs to include (uses all if None)
            
        Returns:
            Path to the created file
        """
        if not self.pfam_versions:
            print("Warning: No Pfam versions to save", file=sys.stderr)
            return output_file
        
        # Determine which IDs to save
        ids_to_save = pfam_ids if pfam_ids else set(self.pfam_versions.keys())
        
        try:
            with open(output_file, 'w') as f:
                for pfam_id in sorted(ids_to_save):
                    if pfam_id in self.pfam_versions:
                        f.write(f"{self.pfam_versions[pfam_id]}\n")
            
            print(f"✓ Saved {len([p for p in ids_to_save if p in self.pfam_versions])} versions to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error saving versions to file: {e}", file=sys.stderr)
            return output_file
    
    def fetch_hmms(self, versions_file: str, output_hmm_file: str = 'selected_pfam.hmm') -> bool:
        """
        Use hmmfetch to extract HMM profiles based on version file.
        
        Args:
            versions_file: File containing Pfam IDs with versions (one per line)
            output_hmm_file: Output file for fetched HMMs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nRunning hmmfetch to extract HMM profiles...")
            print(f"Command: hmmfetch -f {self.pfam_hmm_file} {versions_file} > {output_hmm_file}")
            
            with open(output_hmm_file, 'w') as outfile:
                result = subprocess.run(
                    ['hmmfetch', '-f', str(self.pfam_hmm_file), versions_file],
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
            
            print(f"✓ HMM profiles successfully written to {output_hmm_file}")
            
            # Show file size
            size = Path(output_hmm_file).stat().st_size
            print(f"  Output file size: {size:,} bytes")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running hmmfetch: {e}", file=sys.stderr)
            if e.stderr:
                print(f"stderr: {e.stderr}", file=sys.stderr)
            return False
            
        except FileNotFoundError:
            print("Error: hmmfetch not found. Make sure HMMER is installed and in your PATH.", file=sys.stderr)
            return False
            
        except Exception as e:
            print(f"Unexpected error during HMM fetching: {e}", file=sys.stderr)
            return False
    
    def get_missing_pfam_ids(self, pfam_ids: Set[str]) -> Set[str]:
        """
        Get Pfam IDs that were searched but not found
        
        Args:
            pfam_ids: Original set of Pfam IDs
            
        Returns:
            Set of Pfam IDs without versions
        """
        return pfam_ids - set(self.pfam_versions.keys())
    
    def print_missing_report(self, pfam_ids: Set[str]):
        """
        Print a report of missing Pfam IDs
        
        Args:
            pfam_ids: Original set of Pfam IDs
        """
        missing = self.get_missing_pfam_ids(pfam_ids)
        
        if missing:
            print(f"\n⚠ Warning: No version found for {len(missing)} Pfam IDs:")
            for pfam_id in sorted(missing):
                print(f"  {pfam_id}")
        else:
            print(f"\n✓ All {len(pfam_ids)} Pfam IDs found!")
    
    def run(self, pfam_ids_file: str, 
            versions_file: str = 'pfam_versions.txt',
            output_hmm_file: str = 'selected_pfam.hmm',
            column_name: str = 'Pfam_ID') -> Tuple[bool, Dict[str, str]]:
        """
        Complete workflow: read Pfam IDs, extract versions, and fetch HMMs
        
        Args:
            pfam_ids_file: Path to file containing Pfam IDs
            versions_file: Output file for versions
            output_hmm_file: Output file for HMM profiles
            column_name: Column name containing Pfam IDs
            
        Returns:
            Tuple of (success: bool, pfam_versions: dict)
        """
        print("="*60)
        print("PfamHandler: Extract and Fetch HMM Profiles")
        print("="*60)
        print(f"Pfam path: {self.pfam_path}")
        print(f"Pfam HMM file: {self.pfam_hmm_file}")
        print("="*60)
        
        # Step 1: Read Pfam IDs
        pfam_ids = self.read_pfam_ids_from_file(pfam_ids_file, column_name=column_name)
        
        if not pfam_ids:
            print("Error: No Pfam IDs found")
            return False, {}
        
        # Step 2: Extract versions
        pfam_versions = self.extract_pfam_versions_with_grep(pfam_ids)
        
        if not pfam_versions:
            print("\n⚠ No Pfam versions found. Cannot proceed with HMM extraction.")
            return False, {}
        
        # Step 3: Save versions to file
        self.save_versions_to_file(versions_file, pfam_ids)
        
        # Step 4: Print missing report
        self.print_missing_report(pfam_ids)
        
        # Step 5: Fetch HMMs
        success = self.fetch_hmms(versions_file, output_hmm_file)
        
        if success:
            print("\n✓ Done!")
            print(f"\nOutput files:")
            print(f"  - Versions: {versions_file}")
            print(f"  - HMM profiles: {output_hmm_file}")
        else:
            print("\n✗ HMM extraction failed")
        
        return success, pfam_versions
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the extraction
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_versions_found': len(self.pfam_versions),
            'pfam_hmm_file_exists': self.pfam_hmm_file.exists(),
            'hmmfetch_available': self._check_hmmfetch_available()
        }


def main():
    """
    Command-line interface
    """
    if len(sys.argv) != 3:
        print("Usage: python profiles_extraction.py <pfam_ids_file> <pfam_path>")
        print("\nExample:")
        print("  python profiles_extraction.py uniprot_output.tsv /path/to/pfam")
        print("\nArguments:")
        print("  pfam_ids_file : TSV file with a 'Pfam_ID' column")
        print("  pfam_path     : Directory containing Pfam-A.hmm file")
        sys.exit(1)
    
    pfam_ids_file = sys.argv[1]
    pfam_path = sys.argv[2]
    
    try:
        # Create handler
        handler = PfamHandler(pfam_path)
        
        # Run the complete workflow
        success, versions = handler.run(
            pfam_ids_file=pfam_ids_file,
            versions_file='pfam_versions.txt',
            output_hmm_file='selected_pfam.hmm',
            column_name='Pfam_ID'
        )
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()