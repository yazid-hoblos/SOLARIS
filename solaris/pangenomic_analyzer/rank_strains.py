#!/usr/bin/env python3
"""
Step 3: Create pangenome comparison matrix.
"""

import pandas as pd
from pathlib import Path
import numpy as np

def create_comparison_matrix():
    """Compare EC presence across all strains."""
    
    print("Creating pangenome comparison matrix...")
    
    # Find all ec_results files
    result_files = list(Path('results/batch').glob('*_ec_results.csv'))
    
    if not result_files:
        print("No results found. Run batch analysis first.")
        return
    
    print(f"Found {len(result_files)} strain results")
    
    # Load all results
    strain_data = {}
    all_ecs = set()
    
    for file in result_files:
        strain_name = file.stem.replace('_ec_results', '')
        df = pd.read_csv(file)
        strain_data[strain_name] = df
        all_ecs.update(df['EC_number'].unique())
    
    print(f"Total unique EC numbers: {len(all_ecs)}")
    
    # Build matrix
    matrix = []
    
    for ec in sorted(all_ecs):
        row = {'EC_number': ec}
        
        for strain_name, df in strain_data.items():
            ec_data = df[df['EC_number'] == ec]
            
            if len(ec_data) > 0:
                status = ec_data['Status'].iloc[0]
                if status == 'FULLY_FOUND':
                    row[strain_name] = 2
                elif status == 'PARTIALLY_FOUND':
                    row[strain_name] = 1
                else:
                    row[strain_name] = 0
            else:
                row[strain_name] = 0
        
        matrix.append(row)
    
    matrix_df = pd.DataFrame(matrix)
    matrix_df.to_csv('results/pangenome_matrix.csv', index=False)
    
    print(f"✓ Saved to results/pangenome_matrix.csv")
    
    # Summary statistics
    print("\nSummary:")
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    
    for strain in strains:
        total = len(matrix_df)
        fully = (matrix_df[strain] == 2).sum()
        partial = (matrix_df[strain] == 1).sum()
        absent = (matrix_df[strain] == 0).sum()
        
        print(f"\n{strain}:")
        print(f"  Fully found: {fully}/{total} ({fully/total*100:.1f}%)")
        print(f"  Partial: {partial}/{total} ({partial/total*100:.1f}%)")
        print(f"  Absent: {absent}/{total} ({absent/total*100:.1f}%)")
    
    return matrix_df


def main():
    matrix_df = create_comparison_matrix()

if __name__ == '__main__':
    main()