#!/usr/bin/env python3
"""
Step 4: Visualize pangenome with clustering of similar patterns.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import pdist, squareform
import sys 

def cluster_strains(matrix_df, method='ward', metric='euclidean'):
    """Cluster strains based on EC profile similarity."""
    
    print("Clustering strains by EC profile similarity...")
    
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    data = matrix_df[strains].T.values  # Transpose: strains as rows
    
    # Hierarchical clustering
    linkage_matrix = linkage(data, method=method, metric=metric)
    
    # Cut tree to get clusters
    # Use distance threshold or number of clusters
    clusters = fcluster(linkage_matrix, t=0.3, criterion='distance')
    
    # Create cluster assignments
    strain_clusters = pd.DataFrame({
        'strain': strains,
        'cluster': clusters
    })
    
    # Sort by cluster
    strain_clusters = strain_clusters.sort_values('cluster')
    
    print(f"✓ Found {len(set(clusters))} clusters")
    
    # Print cluster composition
    for cluster_id in sorted(set(clusters)):
        members = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
        print(f"  Cluster {cluster_id}: {len(members)} strain(s)")
        for member in members:
            print(f"    - {member}")
    
    return strain_clusters, linkage_matrix


def plot_clustered_heatmap(matrix_df, strain_clusters, 
                           output_file='results/plots/pangenome_clustered_heatmap.png'):
    """Heatmap with strains ordered by cluster and simplified labels."""
    
    print("\nCreating clustered heatmap...")
    
    # Reorder strains by cluster
    ordered_strains = strain_clusters['strain'].tolist()
    data = matrix_df[ordered_strains].values
    
    # Simplify strain labels to main groups
    simple_labels = []
    for strain in ordered_strains:
        # Extract genus and species/strain identifier
        parts = strain.split('_')
        
        if 'Synechococcus' in strain:
            # Get strain number (PCC 7942, etc.)
            strain_num = next((p for p in parts if p.startswith('PCC') or p.isdigit()), '')
            simple_labels.append(f'S.elongatus {strain_num}')
        elif 'Synechocystis' in strain:
            strain_num = next((p for p in parts if p.startswith('PCC') or p.isdigit()), '')
            simple_labels.append(f'Synechocystis {strain_num}')
        elif 'Prochlorococcus' in strain:
            strain_num = next((p for p in parts if any(c.isalpha() for c in p) and any(c.isdigit() for c in p)), '')
            simple_labels.append(f'Prochlorococcus {strain_num}')
        elif 'Anabaena' in strain:
            strain_num = next((p for p in parts if p.startswith('PCC') or p.isdigit()), '')
            simple_labels.append(f'Anabaena {strain_num}')
        else:
            # Fallback: first word + last meaningful part
            simple_labels.append(f'{parts[0][:12]}...')
    
    fig, ax = plt.subplots(figsize=(max(12, len(ordered_strains)*0.8), 
                                     max(8, len(matrix_df)*0.15)))
    
    im = ax.imshow(data, aspect='auto', cmap='RdYlGn', vmin=0, vmax=2)
    
    # Add cluster separators
    cluster_changes = strain_clusters['cluster'].diff().fillna(0) != 0
    change_positions = np.where(cluster_changes)[0]
    
    for pos in change_positions[1:]:
        ax.axvline(x=pos-0.5, color='black', linewidth=3)
    
    ax.set_xticks(np.arange(len(ordered_strains)))
    ax.set_yticks(np.arange(len(matrix_df)))
    ax.set_xticklabels(simple_labels, rotation=45, ha='right', fontsize=10)
    ax.set_yticklabels(matrix_df['EC_number'], fontsize=8)
    
    ax.set_xlabel('Strain (grouped by cluster)', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('Clustered EC Number Presence Across Strains', 
                fontsize=14, weight='bold', pad=20)
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Status', rotation=270, labelpad=20)
    cbar.set_ticks([0, 1, 2])
    cbar.set_ticklabels(['Not Found', 'Partial', 'Fully Found'])
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")


def plot_cluster_representatives(matrix_df, strain_clusters,
                                 output_file='results/plots/cluster_representatives.png'):
    """Show one representative per cluster with clean labels."""
    
    print("\nCreating cluster representative plot...")
    
    representatives = []
    cluster_labels = []
    
    for cluster_id in sorted(strain_clusters['cluster'].unique()):
        cluster_members = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
        rep = cluster_members[0]
        representatives.append(rep)
        
        # Extract genus name for cluster label
        genus = rep.split('_')[0]
        if len(cluster_members) == 1:
            cluster_labels.append(f"{genus}")
        else:
            cluster_labels.append(f"{genus}\ncluster\n(n={len(cluster_members)})")
    
    data = matrix_df[representatives].values
    
    fig, ax = plt.subplots(figsize=(max(10, len(representatives)*1.5), 
                                     max(8, len(matrix_df)*0.2)))
    
    im = ax.imshow(data, aspect='auto', cmap='RdYlGn', vmin=0, vmax=2)
    
    ax.set_xticks(np.arange(len(representatives)))
    ax.set_yticks(np.arange(len(matrix_df)))
    ax.set_xticklabels(cluster_labels, rotation=0, ha='center', fontsize=11)
    ax.set_yticklabels(matrix_df['EC_number'], fontsize=9)
    
    ax.set_xlabel('Cluster Representative', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('EC Profiles - Cluster Representatives Only', 
                fontsize=14, weight='bold', pad=20)
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Status', rotation=270, labelpad=20)
    cbar.set_ticks([0, 1, 2])
    cbar.set_ticklabels(['Not Found', 'Partial', 'Fully Found'])
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")

def plot_dendrogram(linkage_matrix, strain_clusters,
                   output_file='results/plots/strain_dendrogram.png'):
    """Plot dendrogram showing strain relationships."""
    
    print("\nCreating dendrogram...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    dendrogram(
        linkage_matrix,
        labels=strain_clusters['strain'].tolist(),
        ax=ax,
        leaf_rotation=90,
        leaf_font_size=10
    )
    
    ax.set_xlabel('Strain', fontsize=12, weight='bold')
    ax.set_ylabel('Distance', fontsize=12, weight='bold')
    ax.set_title('Hierarchical Clustering of Strains', 
                fontsize=14, weight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved to {output_file}")


def save_cluster_summary(strain_clusters, matrix_df, 
                        output_file='results/cluster_summary.csv'):
    """Save detailed cluster information."""
    
    print("\nCreating cluster summary...")
    
    summary = []
    
    for cluster_id in sorted(strain_clusters['cluster'].unique()):
        members = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
        
        # Calculate average completeness for this cluster
        cluster_data = matrix_df[members]
        avg_completeness = (cluster_data == 2).sum().sum() / (len(cluster_data) * len(members)) * 100
        
        summary.append({
            'cluster_id': cluster_id,
            'num_strains': len(members),
            'members': '; '.join(members),
            'avg_completeness_%': avg_completeness,
            'representative': members[0]
        })
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_file, index=False)
    
    print(f"✓ Saved to {output_file}")
    
    return summary_df


def main():
    Path('results/plots').mkdir(parents=True, exist_ok=True)
    
    pan_matrix = sys.argv[1] 
    # Load matrix
    matrix_df = pd.read_csv(pan_matrix)
    
    print(f"Loaded matrix: {len(matrix_df)} EC numbers")
    strains = [col for col in matrix_df.columns if col != 'EC_number']
    print(f"Number of strains: {len(strains)}")
    print("="*80)
    
    # Cluster strains
    strain_clusters, linkage_matrix = cluster_strains(matrix_df)
    
    # Save cluster info
    cluster_summary = save_cluster_summary(strain_clusters, matrix_df)
    
    # Generate visualizations
    plot_dendrogram(linkage_matrix, strain_clusters)
    plot_clustered_heatmap(matrix_df, strain_clusters)
    plot_cluster_representatives(matrix_df, strain_clusters)
    
    # Original plots with all strains (if not too many)
    if len(strains) <= 10:
        from comparative_matrix import (plot_strain_completeness, 
                                         plot_core_accessory, 
                                         plot_pairwise_similarity)
        plot_strain_completeness(matrix_df)
        plot_core_accessory(matrix_df)
        plot_pairwise_similarity(matrix_df)
    
    print("\n" + "="*80)
    print("CLUSTERED VISUALIZATION COMPLETE")
    print("="*80)
    print("\nCluster Summary:")
    print(cluster_summary.to_string(index=False))
    print("\nGenerated files:")
    print("  - results/cluster_summary.csv")
    print("  - results/plots/strain_dendrogram.png")
    print("  - results/plots/pangenome_clustered_heatmap.png")
    print("  - results/plots/cluster_representatives.png")

if __name__ == '__main__':
    main()