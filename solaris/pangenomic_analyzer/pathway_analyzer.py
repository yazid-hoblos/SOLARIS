#!/usr/bin/env python3
"""
Pathway Analyzer - Analyze pathway completeness for pangenomic studies.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PathwayAnalyzer:
    """
    Analyzes pathway completeness across multiple strains.
    
    This class provides:
    - EC number coverage analysis
    - Pathway completeness scoring
    - Cross-strain comparison
    - Statistical analysis of pathway presence
    """
    
    def __init__(self):
        """Initialize PathwayAnalyzer."""
        self.ec_status_cache = {}
        
    def analyze_ec_coverage(self, output_dir: str, 
                           target_ecs_file: str) -> Dict[str, Dict]:
        """
        Analyze EC number coverage based on individual strain EC result files.
        This follows the original working approach from your tmp/ directory.
        
        Args:
            output_dir: Directory containing individual strain EC result files
            target_ecs_file: Path to file containing target EC numbers
            
        Returns:
            Dictionary mapping EC numbers to their status information
        """
        logger.info("Analyzing EC number coverage from individual strain results...")
        
        output_path = Path(output_dir)
        
        # Load target EC numbers
        target_ecs = []
        if target_ecs_file and Path(target_ecs_file).exists():
            with open(target_ecs_file, 'r') as f:
                for line in f:
                    ec = line.strip()
                    if ec and not ec.startswith('#'):
                        target_ecs.append(ec)
            logger.info(f"Loaded {len(target_ecs)} target EC numbers")
        else:
            # If no target file, use all EC numbers found in the results
            logger.info("No target EC file provided, will use all EC numbers found in results")
        
        # Find all EC result files
        ec_result_files = list(output_path.glob("*_ec_results.csv"))
        logger.info(f"Found {len(ec_result_files)} strain EC result files")
        
        # Initialize coverage matrix
        strain_ec_matrix = {}
        all_strains = []
        
        # Process each strain's EC results
        for ec_file in ec_result_files:
            try:
                # Extract strain info from filename (strain_accession_ec_results.csv)
                filename_parts = ec_file.stem.replace('_ec_results', '').split('_')
                if len(filename_parts) >= 2:
                    strain = filename_parts[0]
                    accession = filename_parts[1]
                    strain_key = f"{strain}_{accession}"
                else:
                    strain_key = ec_file.stem.replace('_ec_results', '')
                
                all_strains.append(strain_key)
                
                # Read EC results
                ec_df = pd.read_csv(ec_file)
                # Only count FULLY_FOUND and PARTIALLY_FOUND EC numbers
                if 'EC_number' in ec_df.columns and 'Status' in ec_df.columns:
                    found_ecs = set(ec_df[ec_df['Status'].isin(['FULLY_FOUND', 'PARTIALLY_FOUND'])]['EC_number'].unique())
                else:
                    found_ecs = set()
                
                # Initialize strain's EC status
                strain_ec_matrix[strain_key] = {}
                for ec in target_ecs:
                    if ec in found_ecs:
                        strain_ec_matrix[strain_key][ec] = 'FULLY_FOUND'
                    else:
                        strain_ec_matrix[strain_key][ec] = 'NOT_FOUND'
                
                logger.info(f"  ✓ {strain_key}: {len(found_ecs)} EC numbers found")
                
            except Exception as e:
                logger.error(f"Error processing {ec_file}: {e}")
        
        # Create summary coverage analysis
        ec_coverage = {}
        for ec in target_ecs:
            strains_with_ec = [strain for strain in all_strains 
                              if strain_ec_matrix.get(strain, {}).get(ec) == 'FULLY_FOUND']
            
            ec_coverage[ec] = {
                'status': 'FULLY_FOUND' if strains_with_ec else 'NOT_FOUND',
                'found_in_strains': strains_with_ec,
                'total_strains': len(all_strains),
                'coverage_percentage': (len(strains_with_ec) / len(all_strains) * 100) if all_strains else 0
            }
        
        logger.info(f"✓ Analyzed EC coverage for {len(all_strains)} strains and {len(target_ecs)} EC numbers")
        
        return ec_coverage
    
    def save_ec_results(self, ec_status: Dict[str, Dict], output_file: str) -> str:
        """
        Save EC analysis results to CSV file.
        
        Args:
            ec_status: EC status dictionary from analyze_ec_coverage
            output_file: Path to output CSV file
            
        Returns:
            Path to saved file
        """
        results_data = []
        
        for ec_number, data in ec_status.items():
            results_data.append({
                'EC_number': ec_number,
                'Status': data['status'],
                'Total_Pfam_domains': data['total_pfam_domains'],
                'Found_Pfam_domains': data['found_pfam_domains'],
                'Coverage_%': data['coverage_percent'],
                'Total_hits': data['total_hits'],
                'Unique_proteins_with_hits': data['unique_proteins'],
                'Best_E_value': data['best_evalue'],
                'Best_score': data['best_score'],
                'Required_Pfam_IDs': ';'.join(data['required_pfam_ids']),
                'Found_Pfam_IDs': ';'.join(data['found_pfam_ids']),
                'Missing_Pfam_IDs': ';'.join(data['missing_pfam_ids'])
            })
        
        results_df = pd.DataFrame(results_data)
        
        # Create output directory if needed
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_df.to_csv(output_path, index=False)
        logger.info(f"✓ Saved EC results to {output_path}")
        
        return str(output_path)
    
    def create_summary_report(self, ec_status: Dict[str, Dict], output_file: str) -> str:
        """
        Create a text summary report of EC analysis.
        
        Args:
            ec_status: EC status dictionary
            output_file: Path to output text file
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate statistics
        total_ecs = len(ec_status)
        fully_found = sum(1 for data in ec_status.values() if data['status'] == 'FULLY_FOUND')
        partially_found = sum(1 for data in ec_status.values() if data['status'] == 'PARTIALLY_FOUND')
        not_found = sum(1 for data in ec_status.values() if data['status'] == 'NOT_FOUND')
        
        total_hits = sum(data['total_hits'] for data in ec_status.values())
        total_proteins = sum(data['unique_proteins'] for data in ec_status.values())
        avg_coverage = sum(data['coverage_percent'] for data in ec_status.values()) / total_ecs if total_ecs > 0 else 0
        
        with open(output_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("EC NUMBER ANALYSIS SUMMARY\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Total EC numbers analyzed: {total_ecs}\n\n")
            
            f.write("STATUS DISTRIBUTION:\n")
            f.write(f"  Fully Found:     {fully_found:3d} ({fully_found/total_ecs*100:5.1f}%)\n")
            f.write(f"  Partially Found: {partially_found:3d} ({partially_found/total_ecs*100:5.1f}%)\n")
            f.write(f"  Not Found:       {not_found:3d} ({not_found/total_ecs*100:5.1f}%)\n\n")
            
            f.write("OVERALL STATISTICS:\n")
            f.write(f"  Total hits found: {total_hits}\n")
            f.write(f"  Unique proteins with hits: {total_proteins}\n")
            f.write(f"  Average coverage: {avg_coverage:.1f}%\n\n")
            
            f.write("DETAILED RESULTS BY STATUS:\n")
            f.write("-"*60 + "\n")
            
            # Group by status
            for status in ['FULLY_FOUND', 'PARTIALLY_FOUND', 'NOT_FOUND']:
                status_ecs = [(ec, data) for ec, data in ec_status.items() if data['status'] == status]
                
                if status_ecs:
                    f.write(f"\n{status.replace('_', ' ').title()} ({len(status_ecs)} ECs):\n")
                    
                    for ec, data in sorted(status_ecs, key=lambda x: x[1]['coverage_percent'], reverse=True):
                        f.write(f"  {ec}: {data['coverage_percent']:.1f}% coverage "
                               f"({data['found_pfam_domains']}/{data['total_pfam_domains']} domains, "
                               f"{data['total_hits']} hits)\n")
        
        logger.info(f"✓ Saved summary report to {output_path}")
        return str(output_path)
    
    def create_comparison_matrix(self, strain_results: Dict[str, Dict], 
                                output_file: str) -> pd.DataFrame:
        """
        Create a comparison matrix showing EC presence across strains.
        
        Args:
            strain_results: Dictionary mapping strain names to their EC status
            output_file: Path to output CSV file
            
        Returns:
            DataFrame with comparison matrix
        """
        logger.info("Creating strain comparison matrix...")
        
        # Collect all EC numbers
        all_ecs = set()
        for strain_data in strain_results.values():
            all_ecs.update(strain_data.keys())
        
        all_ecs = sorted(list(all_ecs))
        
        # Create matrix
        matrix_data = {'EC_number': all_ecs}
        
        for strain, ec_status in strain_results.items():
            strain_column = []
            
            for ec in all_ecs:
                if ec in ec_status:
                    status = ec_status[ec]['status']
                    if status == 'FULLY_FOUND':
                        value = 2
                    elif status == 'PARTIALLY_FOUND':
                        value = 1
                    else:
                        value = 0
                else:
                    value = 0
                
                strain_column.append(value)
            
            matrix_data[strain] = strain_column
        
        matrix_df = pd.DataFrame(matrix_data)
        
        # Save matrix
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matrix_df.to_csv(output_path, index=False)
        
        logger.info(f"✓ Saved comparison matrix to {output_path}")
        return matrix_df
    
    def calculate_strain_similarity(self, matrix_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate pairwise similarity between strains based on EC presence.
        
        Args:
            matrix_df: Comparison matrix from create_comparison_matrix
            
        Returns:
            DataFrame with pairwise similarity scores
        """
        strain_columns = [col for col in matrix_df.columns if col != 'EC_number']
        
        similarity_data = []
        
        for i, strain1 in enumerate(strain_columns):
            for j, strain2 in enumerate(strain_columns):
                if i <= j:  # Only calculate upper triangle + diagonal
                    vec1 = matrix_df[strain1].values
                    vec2 = matrix_df[strain2].values
                    
                    # Calculate Jaccard similarity for EC presence
                    intersection = sum(1 for a, b in zip(vec1, vec2) if a > 0 and b > 0)
                    union = sum(1 for a, b in zip(vec1, vec2) if a > 0 or b > 0)
                    
                    jaccard = intersection / union if union > 0 else 0
                    
                    # Calculate correlation
                    correlation = pd.Series(vec1).corr(pd.Series(vec2))
                    
                    similarity_data.append({
                        'Strain_1': strain1,
                        'Strain_2': strain2,
                        'Jaccard_similarity': jaccard,
                        'Correlation': correlation,
                        'Shared_ECs': intersection,
                        'Total_ECs_union': union
                    })
        
        similarity_df = pd.DataFrame(similarity_data)
        return similarity_df
    
    def rank_strains_by_completeness_from_matrix(self, matrix_df: pd.DataFrame) -> pd.DataFrame:
        """
        Rank strains by completeness using the comparison matrix.
        
        Args:
            matrix_df: Comparison matrix DataFrame
            
        Returns:
            DataFrame with strain rankings
        """
        strains = [col for col in matrix_df.columns if col != 'EC_number']
        rankings = []
        
        for strain in strains:
            strain_data = matrix_df[strain]
            total_ecs = len(strain_data)
            found_ecs = (strain_data == 2).sum()
            partial_ecs = (strain_data == 1).sum()
            not_found_ecs = (strain_data == 0).sum()
            completeness = (found_ecs + partial_ecs * 0.5) / total_ecs * 100
            
            rankings.append({
                'Strain': strain,
                'Completeness_Score': completeness,
                'Average_Coverage_%': completeness,  # Use completeness as proxy
                'Total_ECs': total_ecs,
                'Fully_Found': found_ecs,
                'Partially_Found': partial_ecs,
                'Not_Found': not_found_ecs,
                'Total_Hits': found_ecs + partial_ecs,  # Approximate
                'Unique_Proteins': found_ecs + partial_ecs,  # Approximate
                'Fully_Found_%': (found_ecs / total_ecs * 100) if total_ecs > 0 else 0
            })
        
        rankings_df = pd.DataFrame(rankings)
        rankings_df = rankings_df.sort_values('Completeness_Score', ascending=False)
        
        return rankings_df
    
    def rank_strains_by_completeness(self, strain_results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Rank strains by pathway completeness.
        
        Args:
            strain_results: Dictionary mapping strain names to their EC status
            
        Returns:
            DataFrame with strain rankings
        """
        logger.info("Ranking strains by pathway completeness...")
        
        rankings = []
        
        for strain, ec_status in strain_results.items():
            total_ecs = len(ec_status)
            fully_found = sum(1 for data in ec_status.values() if data['status'] == 'FULLY_FOUND')
            partially_found = sum(1 for data in ec_status.values() if data['status'] == 'PARTIALLY_FOUND')
            not_found = sum(1 for data in ec_status.values() if data['status'] == 'NOT_FOUND')
            
            avg_coverage = sum(data['coverage_percent'] for data in ec_status.values()) / total_ecs if total_ecs > 0 else 0
            total_hits = sum(data['total_hits'] for data in ec_status.values())
            total_proteins = sum(data['unique_proteins'] for data in ec_status.values())
            
            # Calculate composite score
            completeness_score = (fully_found * 2 + partially_found * 1) / (total_ecs * 2) * 100 if total_ecs > 0 else 0
            
            rankings.append({
                'Strain': strain,
                'Completeness_Score': completeness_score,
                'Average_Coverage_%': avg_coverage,
                'Total_ECs': total_ecs,
                'Fully_Found': fully_found,
                'Partially_Found': partially_found,
                'Not_Found': not_found,
                'Total_Hits': total_hits,
                'Unique_Proteins': total_proteins,
                'Fully_Found_%': (fully_found / total_ecs * 100) if total_ecs > 0 else 0
            })
        
        rankings_df = pd.DataFrame(rankings)
        rankings_df = rankings_df.sort_values('Completeness_Score', ascending=False)
        
        logger.info(f"✓ Ranked {len(rankings_df)} strains")
        return rankings_df
    
    def create_comparison_matrix_from_files(self, results_dir: str) -> pd.DataFrame:
        """
        Create comparison matrix from individual EC results files.
        Based on the original tmp/rank_strains.py approach.
        
        Args:
            results_dir: Directory containing *_ec_results.csv files
            
        Returns:
            DataFrame with EC numbers as rows and strains as columns
        """
        logger.info("Creating pangenome comparison matrix from EC results files...")
        
        results_path = Path(results_dir)
        
        # Find all ec_results files
        result_files = list(results_path.glob('*_ec_results.csv'))
        
        if not result_files:
            logger.error(f"No EC results files found in {results_dir}")
            raise FileNotFoundError(f"No *_ec_results.csv files found in {results_dir}")
        
        logger.info(f"Found {len(result_files)} strain results")
        
        # Load all results
        strain_data = {}
        all_ecs = set()
        
        for file in result_files:
            strain_name = file.stem.replace('_ec_results', '')
            
            try:
                df = pd.read_csv(file)
                strain_data[strain_name] = df
                all_ecs.update(df['EC_number'].unique())
                logger.debug(f"Loaded {len(df)} EC entries for {strain_name}")
            except Exception as e:
                logger.warning(f"Could not load {file}: {e}")
                continue
        
        logger.info(f"Total unique EC numbers: {len(all_ecs)}")
        
        # Build matrix
        matrix_data = []
        
        for ec in sorted(all_ecs):
            row = {'EC_number': ec}
            
            for strain_name, df in strain_data.items():
                ec_data = df[df['EC_number'] == ec]
                
                if len(ec_data) > 0:
                    status = ec_data['Status'].iloc[0]
                    if status == 'FULLY_FOUND':
                        row[strain_name] = 2  # Fully found
                    elif status == 'PARTIALLY_FOUND':
                        row[strain_name] = 1  # Partially found
                    else:
                        row[strain_name] = 0  # Not found
                else:
                    row[strain_name] = 0  # Not found
            
            matrix_data.append(row)
        
        comparison_matrix = pd.DataFrame(matrix_data)
        
        logger.info(f"✓ Created comparison matrix: {comparison_matrix.shape[0]} ECs × {len(strain_data)} strains")
        
        return comparison_matrix