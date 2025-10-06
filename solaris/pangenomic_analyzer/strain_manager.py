#!/usr/bin/env python3
"""
Strain Manager - Handle strain data loading and management for pangenomic analysis.
"""

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrainManager:
    """
    Manages strain data loading, validation, and organization for pangenomic analysis.
    
    This class handles:
    - Loading strain metadata from CSV files
    - Validating genome file paths
    - Organizing strain information for batch processing
    - Filtering strains by various criteria
    """
    
    def __init__(self, strain_file: Optional[str] = None):
        """
        Initialize StrainManager.
        
        Args:
            strain_file: Path to CSV file containing strain information
        """
        self.strain_file = strain_file
        self.strains_df = None
        self.validated_strains = None
        
    def load_strains(self, input_path: Optional[str] = None, 
                     required_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load strain information from CSV file or discover from directory.
        
        Args:
            input_path: Path to strain CSV file or directory containing .faa files
            required_columns: List of required column names
            
        Returns:
            DataFrame with strain information
            
        Raises:
            FileNotFoundError: If input path doesn't exist
            ValueError: If required columns are missing or no .faa files found
        """
        file_path = input_path or self.strain_file
        
        if not file_path:
            raise ValueError("No input path specified")
            
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Input path not found: {file_path}")
            
        logger.info(f"Loading strain data from {file_path}")
        
        try:
            # Check if it's a directory or file
            if path_obj.is_dir():
                # Auto-discover .faa files in directory
                self.strains_df = self._discover_strains_from_directory(path_obj)
            else:
                # Load from CSV file
                self.strains_df = pd.read_csv(file_path)
            
            logger.info(f"✓ Loaded {len(self.strains_df)} strains")
            
            # Validate required columns
            default_required = ['strain', 'genome_file']
            columns_to_check = required_columns or default_required
            
            missing_columns = [col for col in columns_to_check 
                             if col not in self.strains_df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
                
            return self.strains_df
            
        except Exception as e:
            logger.error(f"Error loading strain file: {e}")
            raise
    
    def _discover_strains_from_directory(self, genome_dir: Path) -> pd.DataFrame:
        """
        Discover strain files from a directory containing .faa files.
        
        Args:
            genome_dir: Directory containing genome files
            
        Returns:
            DataFrame with strain information
        """
        logger.info(f"Discovering .faa files in {genome_dir}")
        
        # Find all .faa files
        faa_files = list(genome_dir.glob("*.faa"))
        
        if not faa_files:
            raise ValueError(f"No .faa files found in {genome_dir}")
        
        strains_data = []
        for faa_file in faa_files:
            # Extract strain name from filename
            strain_name = faa_file.stem
            
            # Handle common filename patterns like "strain_GCF_123456.faa"
            if '_GCF_' in strain_name:
                parts = strain_name.split('_GCF_')
                strain_name = parts[0]
                accession = f"GCF_{parts[1]}"
            elif '_GCA_' in strain_name:
                parts = strain_name.split('_GCA_')
                strain_name = parts[0]
                accession = f"GCA_{parts[1]}"
            else:
                accession = strain_name
            
            strains_data.append({
                'strain': strain_name,
                'genome_file': str(faa_file.absolute()),
                'accession': accession
            })
        
        logger.info(f"✓ Discovered {len(strains_data)} .faa files")
        
        return pd.DataFrame(strains_data)
    
    def validate_genome_files(self, genome_dir: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate that genome files exist for all strains.
        
        Args:
            genome_dir: Base directory for genome files (optional)
            
        Returns:
            Tuple of (validated_strains_df, missing_files_list)
        """
        if self.strains_df is None:
            raise ValueError("No strain data loaded. Call load_strains() first.")
            
        logger.info("Validating genome files...")
        
        validated_strains = []
        missing_files = []
        
        for idx, row in self.strains_df.iterrows():
            strain = row['strain']
            file_path = row['file']
            
            # Adjust path if genome_dir is provided
            if genome_dir:
                file_path = Path(genome_dir) / Path(file_path).name
            else:
                file_path = Path(file_path)
                
            if file_path.exists():
                validated_strains.append({
                    'strain': strain,
                    'file': str(file_path),
                    'accession': row['accession'],
                    'file_size': file_path.stat().st_size
                })
            else:
                missing_files.append(f"{strain}: {file_path}")
                
        self.validated_strains = pd.DataFrame(validated_strains)
        
        logger.info(f"✓ Validated {len(self.validated_strains)} strains")
        if missing_files:
            logger.warning(f"⚠ Missing {len(missing_files)} genome files")
            
        return self.validated_strains, missing_files
    
    def filter_strains(self, criteria: Dict[str, any]) -> pd.DataFrame:
        """
        Filter strains based on various criteria.
        
        Args:
            criteria: Dictionary of filter criteria
                     e.g., {'min_file_size': 1000000, 'accession_pattern': 'GCF_*'}
                     
        Returns:
            Filtered DataFrame
        """
        if self.validated_strains is None:
            logger.warning("No validated strains available. Using original strain data.")
            df_to_filter = self.strains_df
        else:
            df_to_filter = self.validated_strains
            
        if df_to_filter is None:
            raise ValueError("No strain data available for filtering")
            
        filtered_df = df_to_filter.copy()
        
        # Apply filters
        if 'min_file_size' in criteria and 'file_size' in filtered_df.columns:
            min_size = criteria['min_file_size']
            filtered_df = filtered_df[filtered_df['file_size'] >= min_size]
            logger.info(f"Filtered by minimum file size ({min_size} bytes): {len(filtered_df)} strains")
            
        if 'accession_pattern' in criteria:
            pattern = criteria['accession_pattern']
            filtered_df = filtered_df[filtered_df['accession'].str.contains(pattern, na=False)]
            logger.info(f"Filtered by accession pattern '{pattern}': {len(filtered_df)} strains")
            
        if 'strain_list' in criteria:
            strain_list = criteria['strain_list']
            filtered_df = filtered_df[filtered_df['strain'].isin(strain_list)]
            logger.info(f"Filtered by strain list: {len(filtered_df)} strains")
            
        return filtered_df
    
    def get_strain_summary(self) -> Dict[str, any]:
        """
        Get summary statistics about loaded strains.
        
        Returns:
            Dictionary with summary information
        """
        if self.strains_df is None:
            return {"error": "No strain data loaded"}
            
        summary = {
            "total_strains": len(self.strains_df),
            "validated_strains": len(self.validated_strains) if self.validated_strains is not None else 0,
            "unique_accessions": self.strains_df['accession'].nunique(),
            "columns": list(self.strains_df.columns)
        }
        
        if self.validated_strains is not None and 'file_size' in self.validated_strains.columns:
            summary.update({
                "avg_file_size_mb": self.validated_strains['file_size'].mean() / (1024 * 1024),
                "total_data_size_gb": self.validated_strains['file_size'].sum() / (1024 * 1024 * 1024)
            })
            
        return summary
    
    def save_validated_strains(self, output_file: str) -> str:
        """
        Save validated strain information to CSV file.
        
        Args:
            output_file: Path to output CSV file
            
        Returns:
            Path to saved file
        """
        if self.validated_strains is None:
            raise ValueError("No validated strains available. Run validate_genome_files() first.")
            
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.validated_strains.to_csv(output_path, index=False)
        logger.info(f"✓ Saved validated strains to {output_path}")
        
        return str(output_path)
    
    def create_strain_batches(self, batch_size: int = 10) -> List[pd.DataFrame]:
        """
        Split strains into batches for parallel processing.
        
        Args:
            batch_size: Number of strains per batch
            
        Returns:
            List of DataFrames, each containing a batch of strains
        """
        df_to_batch = self.validated_strains if self.validated_strains is not None else self.strains_df
        
        if df_to_batch is None:
            raise ValueError("No strain data available for batching")
            
        batches = []
        for i in range(0, len(df_to_batch), batch_size):
            batch = df_to_batch.iloc[i:i + batch_size].copy()
            batches.append(batch)
            
        logger.info(f"Created {len(batches)} batches of ~{batch_size} strains each")
        return batches