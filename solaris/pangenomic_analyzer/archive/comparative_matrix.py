#!/usr/bin/env python3
"""
Step 4: Visualize pangenome comparison results.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

def plot_heatmap(matrix_df, output_file='results/plots/pangenome_heatmap.png'):
    """Create heatmap showing EC presence across strains."""
    
    print("Creating heatmap...")
    
    # Prepare data
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    data = matrix_df[strains].values
    
    # Create figure
    fig, ax = plt.subplots(figsize=(max(12, len(strains)*0.8), max(8, len(matrix_df)*0.15)))
    
    # Plot heatmap
    im = ax.imshow(data, aspect='auto', cmap='RdYlGn', vmin=0, vmax=2)
    
    # Set ticks
    ax.set_xticks(np.arange(len(strains)))
    ax.set_yticks(np.arange(len(matrix_df)))
    ax.set_xticklabels(strains, rotation=45, ha='right')
    ax.set_yticklabels(matrix_df['EC_number'])
    
    # Labels
    ax.set_xlabel('Strain', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('EC Number Presence Across Strains', fontsize=14, weight='bold', pad=20)
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Status', rotation=270, labelpad=20)
    cbar.set_ticks([0, 1, 2])
    cbar.set_ticklabels(['Not Found', 'Partial', 'Fully Found'])
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")


def plot_strain_completeness(matrix_df, output_file='results/plots/strain_completeness.png'):
    """Bar chart of pathway completeness per strain."""
    
    print("Creating strain completeness chart...")
    
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    
    completeness = []
    for strain in strains:
        values = matrix_df[strain].values
        fully = (values == 2).sum()
        partial = (values == 1).sum()
        absent = (values == 0).sum()
        total = len(values)
        
        completeness.append({
            'strain': strain,
            'fully_found': fully,
            'partially_found': partial,
            'not_found': absent,
            'completeness_%': (fully / total) * 100
        })
    
    df = pd.DataFrame(completeness).sort_values('completeness_%', ascending=False)
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(df))
    width = 0.8
    
    p1 = ax.bar(x, df['fully_found'], width, label='Fully Found', color='#2ecc71')
    p2 = ax.bar(x, df['partially_found'], width, bottom=df['fully_found'],
                label='Partially Found', color='#f39c12')
    p3 = ax.bar(x, df['not_found'], width,
                bottom=df['fully_found'] + df['partially_found'],
                label='Not Found', color='#e74c3c')
    
    ax.set_ylabel('Number of EC Numbers', fontsize=12, weight='bold')
    ax.set_xlabel('Strain', fontsize=12, weight='bold')
    ax.set_title('Pathway Completeness by Strain', fontsize=14, weight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df['strain'], rotation=45, ha='right')
    ax.legend()
    
    # Add percentage labels
    for i, (idx, row) in enumerate(df.iterrows()):
        total = row['fully_found'] + row['partially_found'] + row['not_found']
        ax.text(i, total + 1, f"{row['completeness_%']:.1f}%",
                ha='center', va='bottom', fontsize=9, weight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")
    
    return df


def plot_core_accessory(matrix_df, output_file='results/plots/core_accessory.png'):
    """Venn-like diagram showing core vs accessory EC numbers."""
    
    print("Creating core/accessory analysis...")
    
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    
    # Calculate presence in each EC
    matrix_df['presence_count'] = matrix_df[strains].apply(
        lambda row: (row >= 2).sum(), axis=1
    )
    
    # Categorize
    n_strains = len(strains)
    core = matrix_df[matrix_df['presence_count'] == n_strains]  # In all strains
    accessory = matrix_df[(matrix_df['presence_count'] > 0) & 
                          (matrix_df['presence_count'] < n_strains)]  # In some
    absent = matrix_df[matrix_df['presence_count'] == 0]  # In none
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie chart
    sizes = [len(core), len(accessory), len(absent)]
    labels = [f'Core\n({len(core)})', f'Accessory\n({len(accessory)})', 
              f'Absent\n({len(absent)})']
    colors = ['#3498db', '#f39c12', '#95a5a6']
    explode = (0.1, 0, 0)
    
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90, textprops={'size': 12, 'weight': 'bold'})
    ax1.set_title('Core vs Accessory vs Absent', fontsize=14, weight='bold')
    
    # Distribution histogram
    counts = matrix_df['presence_count'].value_counts().sort_index()
    ax2.bar(counts.index, counts.values, color='#3498db', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Number of Strains', fontsize=12, weight='bold')
    ax2.set_ylabel('Number of EC Numbers', fontsize=12, weight='bold')
    ax2.set_title('EC Number Distribution Across Strains', fontsize=14, weight='bold')
    ax2.set_xticks(range(n_strains + 1))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")
    
    return {'core': len(core), 'accessory': len(accessory), 'absent': len(absent)}


def plot_pairwise_similarity(matrix_df, output_file='results/plots/pairwise_similarity.png'):
    """Heatmap of pairwise strain similarity."""
    
    print("Creating pairwise similarity matrix...")
    
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    
    # Calculate Jaccard similarity between each pair
    similarity = np.zeros((len(strains), len(strains)))
    
    for i, strain1 in enumerate(strains):
        for j, strain2 in enumerate(strains):
            if i == j:
                similarity[i, j] = 1.0
            else:
                s1 = set(matrix_df[matrix_df[strain1] >= 2]['EC_number'])
                s2 = set(matrix_df[matrix_df[strain2] >= 2]['EC_number'])
                
                intersection = len(s1 & s2)
                union = len(s1 | s2)
                
                similarity[i, j] = intersection / union if union > 0 else 0
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(similarity, cmap='YlGnBu', vmin=0, vmax=1)
    
    # ax.set_xticks(np.arange(len(strains)))
    # ax.set_yticks(np.arange(len(strains)))
    # ax.set_xticklabels(strains, rotation=45, ha='right')
    # ax.set_yticklabels(strains)
    
    # Add values
    for i in range(len(strains)):
        for j in range(len(strains)):
            text = ax.text(j, i, f'{similarity[i, j]:.2f}',
                          ha='center', va='center', color='black', fontsize=8)
    
    ax.set_title('Pairwise Strain Similarity (Jaccard Index)', 
                fontsize=14, weight='bold', pad=20)
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Similarity', rotation=270, labelpad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")


def create_summary_report(matrix_df, completeness_df, core_accessory, 
                         output_file='results/pangenome_summary.txt'):
    """Create text summary report."""
    
    print("Creating summary report...")
    
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("PANGENOMIC ANALYSIS SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Species: Synechococcus elongatus\n")
        f.write(f"Number of strains analyzed: {len(strains)}\n")
        f.write(f"Number of EC numbers searched: {len(matrix_df)}\n\n")
        
        f.write("CORE/ACCESSORY/ABSENT ANALYSIS\n")
        f.write("-"*80 + "\n")
        f.write(f"Core EC numbers (in all strains): {core_accessory['core']}\n")
        f.write(f"Accessory EC numbers (in some strains): {core_accessory['accessory']}\n")
        f.write(f"Absent EC numbers (in no strains): {core_accessory['absent']}\n\n")
        
        f.write("STRAIN RANKING BY PATHWAY COMPLETENESS\n")
        f.write("-"*80 + "\n")
        for idx, row in completeness_df.iterrows():
            f.write(f"{idx+1}. {row['strain']}: {row['completeness_%']:.1f}% complete\n")
            f.write(f"   Fully found: {row['fully_found']}, "
                   f"Partial: {row['partially_found']}, "
                   f"Absent: {row['not_found']}\n\n")
        
        f.write("RECOMMENDATION\n")
        f.write("-"*80 + "\n")
        best = completeness_df.iloc[0]
        f.write(f"Best chassis candidate: {best['strain']}\n")
        f.write(f"Pathway completeness: {best['completeness_%']:.1f}%\n")
        f.write(f"Has {best['fully_found']} fully complete EC numbers\n")
    
    print(f"✓ Saved to {output_file}")


def main():
    # Create output directory
    Path('results/plots').mkdir(parents=True, exist_ok=True)
    
    # Load matrix
    matrix_df = pd.read_csv('results/pangenome_matrix.csv')
    
    print(f"Loaded matrix: {len(matrix_df)} EC numbers")
    print("="*80)
    
    # Generate all visualizations
    plot_heatmap(matrix_df)
    completeness_df = plot_strain_completeness(matrix_df)
    core_accessory = plot_core_accessory(matrix_df)
    plot_pairwise_similarity(matrix_df)
    
    # Create summary
    create_summary_report(matrix_df, completeness_df, core_accessory)
    
    print("\n" + "="*80)
    print("VISUALIZATION COMPLETE")
    print("="*80)
    print("\nGenerated files:")
    print("  - results/plots/pangenome_heatmap.png")
    print("  - results/plots/strain_completeness.png")
    print("  - results/plots/core_accessory.png")
    print("  - results/plots/pairwise_similarity.png")
    print("  - results/pangenome_summary.txt")

if __name__ == '__main__':
    main()