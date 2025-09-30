#!/usr/bin/env python3
"""
Analyze hmmsearch results and link back to EC numbers and pathways.
Creates summary reports and visualizations.
"""

import csv
import pandas as pd
from pathlib import Path
from collections import defaultdict
import sys

def load_pfam_ec_mapping(pfam_ids_file):
    """
    Load the original mapping of EC numbers to Pfam IDs.
    
    Args:
        pfam_ids_file: CSV file with EC_number, UniProt_ID, Protein_Name, Pfam_ID columns
    
    Returns:
        DataFrame with EC to Pfam mappings
    """
    print(f"Loading EC number to Pfam mapping from {pfam_ids_file}...")
    df = pd.read_csv(pfam_ids_file, sep='\t')
    print(f"✓ Loaded {len(df)} entries")
    return df


def load_hmm_hits(hits_table_file):
    """
    Load hmmsearch results.
    
    Args:
        hits_table_file: Tabular output from hmmsearch
    
    Returns:
        DataFrame with hits
    """
    print(f"Loading HMM search hits from {hits_table_file}...")
    
    hits = []
    with open(hits_table_file) as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split()
            if len(parts) >= 5:
                hits.append({
                    'target': parts[0],
                    'query_hmm': parts[1],  # Query HMM name
                    'evalue': float(parts[2]),
                    'score': float(parts[3])
                })
    
    df = pd.DataFrame(hits)
    print(f"✓ Loaded {len(df)} hits")
    return df


def parse_hmm_file(hmm_file):
    """
    Parse HMM file to create mapping from NAME to Pfam ID (from ACC).
    
    Args:
        hmm_file: Path to HMM file
    
    Returns:
        Dictionary mapping HMM NAME to Pfam ID
    """
    print(f"Parsing HMM file to map NAMEs to Pfam IDs...")
    name_to_id = {}
    
    with open(hmm_file) as f:
        current_name = None
        for line in f:
            if line.startswith('NAME'):
                current_name = line.strip().split()[1]
            elif line.startswith('ACC') and current_name:
                acc = line.strip().split()[1]
                pfam_id = acc.split('.')[0]  # Remove version number
                name_to_id[current_name] = pfam_id
                current_name = None
    
    print(f"✓ Mapped {len(name_to_id)} HMM names to Pfam IDs")
    return name_to_id


def analyze_results(ec_pfam_df, hits_df, name_to_id):
    """
    Analyze which EC numbers were found in the organism.
    
    Args:
        ec_pfam_df: DataFrame with EC to Pfam mappings
        hits_df: DataFrame with HMM hits
        name_to_id: Dictionary mapping HMM NAME to Pfam ID
    
    Returns:
        Dictionary with analysis results
    """
    print("\nAnalyzing results...")
    
    # Map query_hmm names to Pfam IDs
    hits_df['pfam_id'] = hits_df['query_hmm'].map(name_to_id)
    
    # Get unique Pfam IDs that had hits
    found_pfam_ids = set(hits_df['pfam_id'].dropna().unique())
    
    print(f"Found {len(found_pfam_ids)} unique Pfam domains with hits")

    # Map back to EC numbers
    ec_status = defaultdict(lambda: {
        'searched': set(),
        'found': set(),
        'not_found': set(),
        'protein_names': set(),
        'hit_count': 0,
        'hit_proteins': set()
    })
    
    # Process all EC numbers that were searched
    for _, row in ec_pfam_df.iterrows():
        ec = row['EC_number']
        pfam_id = row['Pfam_ID']
        protein_name = row['Protein_Name']
        
        ec_status[ec]['searched'].add(pfam_id)
        ec_status[ec]['protein_names'].add(protein_name)
        
        if pfam_id in found_pfam_ids:
            ec_status[ec]['found'].add(pfam_id)
            # Count hits for this Pfam
            pfam_hits = hits_df[hits_df['pfam_id'] == pfam_id]
            hit_count = len(pfam_hits)
            ec_status[ec]['hit_count'] += hit_count
            # Get protein IDs
            hit_proteins = set(pfam_hits['target'])
            ec_status[ec]['hit_proteins'].update(hit_proteins)
        else:
            ec_status[ec]['not_found'].add(pfam_id)
    
    return ec_status, found_pfam_ids


def create_summary_report(ec_status, output_file='ec_summary.txt'):
    """
    Create a text summary report of findings.
    """
    print(f"\nCreating summary report: {output_file}")
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("EC NUMBER SEARCH RESULTS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        # Categorize EC numbers
        fully_found = []
        partially_found = []
        not_found = []
        
        for ec, status in sorted(ec_status.items()):
            total_pfams = len(status['searched'])
            found_pfams = len(status['found'])
            
            if found_pfams == total_pfams:
                fully_found.append(ec)
            elif found_pfams > 0:
                partially_found.append(ec)
            else:
                not_found.append(ec)
        
        # Summary statistics
        f.write(f"OVERVIEW\n")
        f.write(f"-" * 80 + "\n")
        f.write(f"Total EC numbers searched: {len(ec_status)}\n")
        f.write(f"  ✓ Fully found (all Pfam domains present): {len(fully_found)}\n")
        f.write(f"  ◐ Partially found (some Pfam domains present): {len(partially_found)}\n")
        f.write(f"  ✗ Not found (no Pfam domains present): {len(not_found)}\n")
        f.write(f"\n")
        
        # Detailed results - FULLY FOUND
        if fully_found:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"FULLY FOUND EC NUMBERS ({len(fully_found)})\n")
            f.write(f"{'=' * 80}\n\n")
            
            for ec in fully_found:
                status = ec_status[ec]
                f.write(f"EC {ec}\n")
                f.write(f"  Protein(s): {', '.join(status['protein_names'])}\n")
                f.write(f"  Pfam domains found: {', '.join(sorted(status['found']))}\n")
                f.write(f"  Total hits: {status['hit_count']}\n")
                f.write(f"  Unique proteins with hits: {len(status['hit_proteins'])}\n")
                if status['hit_proteins']:
                    # Show first few protein IDs
                    proteins_list = sorted(status['hit_proteins'])
                    if len(proteins_list) <= 5:
                        f.write(f"  Hit proteins: {', '.join(proteins_list)}\n")
                    else:
                        f.write(f"  Hit proteins (first 5): {', '.join(proteins_list[:5])}...\n")
                f.write(f"\n")
        
        # Detailed results - PARTIALLY FOUND
        if partially_found:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"PARTIALLY FOUND EC NUMBERS ({len(partially_found)})\n")
            f.write(f"{'=' * 80}\n\n")
            
            for ec in partially_found:
                status = ec_status[ec]
                f.write(f"EC {ec}\n")
                f.write(f"  Protein(s): {', '.join(status['protein_names'])}\n")
                f.write(f"  Pfam domains FOUND: {', '.join(sorted(status['found']))}\n")
                f.write(f"  Pfam domains NOT FOUND: {', '.join(sorted(status['not_found']))}\n")
                f.write(f"  Total hits: {status['hit_count']}\n")
                f.write(f"  Unique proteins with hits: {len(status['hit_proteins'])}\n")
                if status['hit_proteins']:
                    proteins_list = sorted(status['hit_proteins'])
                    if len(proteins_list) <= 5:
                        f.write(f"  Hit proteins: {', '.join(proteins_list)}\n")
                    else:
                        f.write(f"  Hit proteins (first 5): {', '.join(proteins_list[:5])}...\n")
                f.write(f"\n")
        
        # Detailed results - NOT FOUND
        if not_found:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"NOT FOUND EC NUMBERS ({len(not_found)})\n")
            f.write(f"{'=' * 80}\n\n")
            
            for ec in not_found:
                status = ec_status[ec]
                f.write(f"EC {ec}\n")
                f.write(f"  Protein(s): {', '.join(status['protein_names'])}\n")
                f.write(f"  Pfam domains searched: {', '.join(sorted(status['searched']))}\n")
                f.write(f"\n")
    
    print(f"✓ Summary report saved to {output_file}")


def create_csv_report(ec_status, output_file='ec_results.csv'):
    """
    Create a CSV report for further analysis.
    """
    print(f"Creating CSV report: {output_file}")
    
    rows = []
    for ec, status in sorted(ec_status.items()):
        total_pfams = len(status['searched'])
        found_pfams = len(status['found'])
        
        if found_pfams == total_pfams:
            status_label = 'FULLY_FOUND'
        elif found_pfams > 0:
            status_label = 'PARTIALLY_FOUND'
        else:
            status_label = 'NOT_FOUND'
        
        rows.append({
            'EC_number': ec,
            'Status': status_label,
            'Protein_names': '; '.join(status['protein_names']),
            'Total_Pfam_domains': total_pfams,
            'Found_Pfam_domains': found_pfams,
            'Not_found_Pfam_domains': total_pfams - found_pfams,
            'Found_Pfams': ', '.join(sorted(status['found'])) if status['found'] else '',
            'Not_found_Pfams': ', '.join(sorted(status['not_found'])) if status['not_found'] else '',
            'Total_hits': status['hit_count'],
            'Unique_proteins_with_hits': len(status['hit_proteins']),
            'Hit_protein_IDs': '; '.join(sorted(status['hit_proteins']))
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    
    print(f"✓ CSV report saved to {output_file}")
    return df


def create_detailed_hits_report(ec_pfam_df, hits_df, output_file='detailed_hits.csv'):
    """
    Create a detailed report linking each hit back to EC numbers.
    """
    print(f"Creating detailed hits report: {output_file}")
    
    # Merge with EC information
    detailed = hits_df.merge(
        ec_pfam_df[['EC_number', 'Protein_Name', 'Pfam_ID', 'Pfam_Description']],
        left_on='pfam_id',
        right_on='Pfam_ID',
        how='left'
    )
    
    # Reorder columns
    cols = ['target', 'EC_number', 'Protein_Name', 'Pfam_ID', 'Pfam_Description', 
            'query_hmm', 'evalue', 'score']
    detailed = detailed[cols]
    
    # Sort by EC number and E-value
    detailed = detailed.sort_values(['EC_number', 'evalue'])
    
    # Save
    detailed.to_csv(output_file, index=False)
    print(f"✓ Detailed hits report saved to {output_file}")


def main():
    # Configuration
    pfam_ids_file = 'pfam_ids.txt'
    hmm_file = 'selected_pfam.hmm'
    hits_table_file = 'hits_table.txt'
    
    # Check files exist
    required_files = [pfam_ids_file, hmm_file, hits_table_file]
    for f in required_files:
        if not Path(f).exists():
            print(f"Error: Required file not found: {f}", file=sys.stderr)
            sys.exit(1)
    
    try:
        # Load data
        ec_pfam_df = load_pfam_ec_mapping(pfam_ids_file)
        hits_df = load_hmm_hits(hits_table_file)
        name_to_id = parse_hmm_file(hmm_file)
        
        # Analyze
        ec_status, found_pfam_ids = analyze_results(ec_pfam_df, hits_df, name_to_id)
        
        # Generate reports
        create_summary_report(ec_status, 'ec_summary.txt')
        results_df = create_csv_report(ec_status, 'ec_results.csv')
        create_detailed_hits_report(ec_pfam_df, hits_df, 'detailed_hits.csv')
        
        # Print quick summary to console
        print("\n" + "=" * 80)
        print("QUICK SUMMARY")
        print("=" * 80)
        print(results_df['Status'].value_counts().to_string())
        print("\nFully found EC numbers:")
        fully_found = results_df[results_df['Status'] == 'FULLY_FOUND']['EC_number'].tolist()
        for ec in fully_found:
            proteins = results_df[results_df['EC_number'] == ec]['Protein_names'].iloc[0]
            print(f"  ✓ {ec} - {proteins}")
        
        if len(fully_found) == 0:
            print("  (none)")
        
        print("\n✓ All reports generated successfully!")
        print("\nOutput files:")
        print("  - ec_summary.txt: Human-readable summary")
        print("  - ec_results.csv: Spreadsheet for analysis")
        print("  - detailed_hits.csv: All hits with EC numbers")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()