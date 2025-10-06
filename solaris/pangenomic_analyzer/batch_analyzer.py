#!/usr/bin/env python3
"""
Batch Analyzer - Handle batch processing of multiple strains for pangenomic analysis.
"""

import pandas as pd
import pyhmmer
from pathlib import Path
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """
    Handles batch processing of multiple strains using HMM profiles.
    
    This class provides:
    - Batch HMM searching across multiple genome files
    - Parallel processing capabilities
    - Progress tracking and error handling
    - Result aggregation and organization
    """
    
    def __init__(self, hmm_file: str, evalue_threshold: float = 1e-5, 
                 output_dir: str = "results/batch"):
        """
        Initialize BatchAnalyzer.
        
        Args:
            hmm_file: Path to HMM profiles file
            evalue_threshold: E-value threshold for hits
            output_dir: Directory for batch results
        """
        self.hmm_file = Path(hmm_file)
        self.evalue_threshold = evalue_threshold
        self.output_dir = Path(output_dir)
        self.hmms = None
        self.results_summary = {}
        
        # Validate HMM file
        if not self.hmm_file.exists():
            raise FileNotFoundError(f"HMM file not found: {hmm_file}")
            
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_hmm_profiles(self) -> List:
        """
        Load HMM profiles from file.
        
        Returns:
            List of HMM profile objects
        """
        logger.info(f"Loading HMM profiles from {self.hmm_file}")
        
        try:
            with pyhmmer.plan7.HMMFile(str(self.hmm_file)) as hmm_file_handle:
                self.hmms = list(hmm_file_handle)
            
            logger.info(f"✓ Loaded {len(self.hmms)} HMM profiles")
            return self.hmms
            
        except Exception as e:
            logger.error(f"Error loading HMM profiles: {e}")
            raise
    
    def analyze_single_strain(self, strain_info: Dict[str, str], 
                             pfam_ec_mapping_file: Optional[str] = None) -> Dict[str, any]:
        """
        Analyze a single strain against HMM profiles.
        
        Args:
            strain_info: Dictionary with strain, file, and accession info
            pfam_ec_mapping: Optional EC-Pfam mapping data
            
        Returns:
            Dictionary with analysis results
        """
        strain = strain_info['strain']
        fasta_file = strain_info['file']
        accession = strain_info['accession']
        
        logger.info(f"Analyzing strain: {strain} ({accession})")
        
        if not Path(fasta_file).exists():
            logger.error(f"Genome file not found: {fasta_file}")
            return {"strain": strain, "error": "File not found", "hits": 0}
        
        try:
            # Load sequences
            with pyhmmer.easel.SequenceFile(fasta_file, digital=True) as seq_file:
                sequences = list(seq_file)
            
            logger.info(f"  Loaded {len(sequences)} sequences")
            
            # Run HMM search (simplified like your original code)
            all_hits = []
            
            if self.hmms is None:
                self.load_hmm_profiles()
            
            for hmm in self.hmms:
                for hits in pyhmmer.hmmsearch(hmm, sequences, cpus=0):
                    for hit in hits:
                        if hit.evalue < self.evalue_threshold:
                            all_hits.append({
                                'target': hit.name.decode(),
                                'query_hmm': hmm.name.decode(),
                                'evalue': hit.evalue,
                                'score': hit.score,
                                'bias': hit.bias
                            })
            
            # Save hits in original format (tab-separated)
            hits_file = self.output_dir / f"{strain}_{accession}_hits.txt"
            with open(hits_file, 'w') as f:
                f.write("# target_name\tquery_name\te_value\tscore\tbias\n")
                for hit in all_hits:
                    f.write(f"{hit['target']}\t{hit['query_hmm']}\t{hit['evalue']:.2e}\t"
                           f"{hit['score']:.1f}\t{hit['bias']:.1f}\n")
            
            logger.info(f"  ✓ Found {len(all_hits)} hits, saved to {hits_file}")
            
            # Analyze EC numbers if mapping file is provided
            if pfam_ec_mapping_file and Path(pfam_ec_mapping_file).exists():
                ec_results = self._analyze_ec_numbers_from_file(
                    hits_file, pfam_ec_mapping_file, strain, accession
                )
                return ec_results
            
            return {
                "strain": strain,
                "accession": accession,
                "hits": len(all_hits),
                "unique_proteins": len(set(hit['target'] for hit in all_hits)),
                "output_file": str(hits_file)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing strain {strain}: {e}")
            return {"strain": strain, "error": str(e), "hits": 0}
    
    def _analyze_ec_numbers_from_file(self, hits_file: Path, 
                                     pfam_ec_mapping_file: str, 
                                     strain: str, 
                                     accession: str) -> Dict[str, any]:
        """
        Analyze EC numbers from HMM hits using the exact original approach.
        """
        try:
            from collections import defaultdict
            
            # Load EC to Pfam mapping (exactly like original)
            ec_pfam_df = pd.read_csv(pfam_ec_mapping_file, sep='\t')
            logger.info(f"  Loaded {len(ec_pfam_df)} EC-Pfam mappings")
            
            # Load hits (exactly like original)
            hits_df = pd.read_csv(hits_file, sep='\t', comment='#',
                                 names=['target', 'query_hmm', 'evalue', 'score', 'bias'])
            
            # Parse HMM file to map NAME to Pfam ID (exactly like original)
            name_to_id = {}
            with open(self.hmm_file) as f:
                current_name = None
                for line in f:
                    if line.startswith('NAME'):
                        current_name = line.strip().split()[1]
                    elif line.startswith('ACC') and current_name:
                        acc = line.strip().split()[1]
                        pfam_id = acc.split('.')[0]
                        name_to_id[current_name] = pfam_id
                        current_name = None
            
            # Map query names to Pfam IDs (exactly like original)
            hits_df['pfam_id'] = hits_df['query_hmm'].map(name_to_id)
            
            # Get found Pfam IDs (exactly like original)
            found_pfam_ids = set(hits_df['pfam_id'].dropna().unique())
            
            # Analyze EC numbers (exactly like original)
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
            
            # Create results DataFrame (exactly like original)
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
            
            # Save EC results (exactly like original)
            ec_results_file = self.output_dir / f"{strain}_{accession}_ec_results.csv"
            results_df.to_csv(ec_results_file, index=False)
            
            # Count found ECs
            found_ecs = len([r for r in results if r['Status'] in ['FULLY_FOUND', 'PARTIALLY_FOUND']])
            
            logger.info(f"  ✓ Found {found_ecs} EC numbers with hits, saved to {ec_results_file}")
            
            return {
                "strain": strain,
                "accession": accession,
                "hits": len(hits_df),
                "unique_ecs": found_ecs,
                "ec_results_file": str(ec_results_file),
                "results_df": results_df
            }
            
        except Exception as e:
            logger.error(f"Error analyzing EC numbers for {strain}: {e}")
            import traceback
            traceback.print_exc()
            return {"strain": strain, "error": str(e), "hits": 0}
    
    def batch_analyze_strains(self, strains_df: pd.DataFrame, 
                             pfam_ec_mapping_file: Optional[str] = None,
                             max_workers: int = 4) -> List[Dict[str, any]]:
        """
        Analyze multiple strains in batch.
        
        Args:
            strains_df: DataFrame with strain information
            pfam_ec_mapping_file: Optional path to EC-Pfam mapping file
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of dictionaries with individual strain results
        """
        logger.info(f"Starting batch analysis of {len(strains_df)} strains")
        logger.info(f"Using {max_workers} parallel workers")
        logger.info(f"Output directory: {self.output_dir}")
        
        # Load HMM profiles once
        if self.hmms is None:
            self.load_hmm_profiles()
        
        start_time = time.time()
        results = []
        failed_strains = []
        
        # Process strains
        if max_workers == 1:
            # Sequential processing
            for idx, row in strains_df.iterrows():
                strain_info = {
                    'strain': row['strain'],
                    'file': row['genome_file'],
                    'accession': row['accession']
                }
                
                logger.info(f"[{idx+1}/{len(strains_df)}] Processing {strain_info['strain']}")
                result = self.analyze_single_strain(strain_info, pfam_ec_mapping_file)
                
                if 'error' in result:
                    failed_strains.append(result)
                else:
                    results.append(result)
        else:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_strain = {}
                
                for idx, row in strains_df.iterrows():
                    strain_info = {
                        'strain': row['strain'],
                        'file': row['genome_file'],
                        'accession': row['accession']
                    }
                    
                    future = executor.submit(
                        self.analyze_single_strain, strain_info, pfam_ec_mapping_file
                    )
                    future_to_strain[future] = strain_info
                
                # Collect results
                for future in as_completed(future_to_strain):
                    strain_info = future_to_strain[future]
                    
                    try:
                        result = future.result()
                        if 'error' in result:
                            failed_strains.append(result)
                        else:
                            results.append(result)
                            
                        processed = len(results) + len(failed_strains)
                        logger.info(f"[{processed}/{len(strains_df)}] Completed {strain_info['strain']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {strain_info['strain']}: {e}")
                        failed_strains.append({
                            "strain": strain_info['strain'],
                            "error": str(e),
                            "hits": 0
                        })
        
        # Calculate summary
        end_time = time.time()
        total_time = end_time - start_time
        total_hits = sum(r['hits'] for r in results)
        
        summary = {
            "total_strains": len(strains_df),
            "successful_strains": len(results),
            "failed_strains": len(failed_strains),
            "total_hits": total_hits,
            "average_hits_per_strain": total_hits / len(results) if results else 0,
            "processing_time_seconds": total_time,
            "strains_per_minute": len(strains_df) / (total_time / 60) if total_time > 0 else 0,
            "output_directory": str(self.output_dir),
            "hmm_profiles_used": len(self.hmms) if self.hmms else 0
        }
        
        # Save batch summary
        self._save_batch_summary(summary, results, failed_strains)
        
        logger.info(f"✓ Batch analysis completed in {total_time:.1f} seconds")
        logger.info(f"  Successful: {len(results)}, Failed: {len(failed_strains)}")
        logger.info(f"  Total hits: {total_hits}")
        
        # Return the individual results instead of summary for CLI compatibility
        return results
    
    def _save_batch_summary(self, summary: Dict, results: List[Dict], 
                           failed_strains: List[Dict]) -> None:
        """Save batch processing summary to files."""
        
        # Save summary JSON
        import json
        summary_file = self.output_dir / "batch_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed results
        if results:
            results_df = pd.DataFrame(results)
            results_file = self.output_dir / "batch_results.csv"
            results_df.to_csv(results_file, index=False)
        
        # Save failed strains
        if failed_strains:
            failed_df = pd.DataFrame(failed_strains)
            failed_file = self.output_dir / "failed_strains.csv"
            failed_df.to_csv(failed_file, index=False)
        
        logger.info(f"✓ Saved batch summary to {self.output_dir}")
    
    def get_batch_status(self) -> Dict[str, any]:
        """
        Get status of current batch processing.
        
        Returns:
            Dictionary with batch processing status
        """
        output_files = list(self.output_dir.glob("*_hits.csv"))
        summary_file = self.output_dir / "batch_summary.json"
        
        status = {
            "output_directory": str(self.output_dir),
            "completed_strains": len(output_files),
            "batch_summary_exists": summary_file.exists()
        }
        
        if summary_file.exists():
            import json
            with open(summary_file, 'r') as f:
                batch_summary = json.load(f)
            status.update(batch_summary)
        
        return status