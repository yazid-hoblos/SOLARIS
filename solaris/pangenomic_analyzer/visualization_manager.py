#!/usr/bin/env python3
"""
Visualization Manager - Create comprehensive visualizations for pangenomic analysis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Suppress numpy warnings about subnormal values
warnings.filterwarnings("ignore", message="The value of the smallest subnormal.*is zero", category=UserWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'


class VisualizationManager:
    """
    Creates comprehensive visualizations for pangenomic analysis results.
    
    This class provides:
    - Heatmaps showing EC presence across strains
    - Strain completeness analysis plots
    - Comparative analysis visualizations
    - Statistical distribution plots
    """
    
    def __init__(self, output_dir: str = "results/plots"):
        """
        Initialize VisualizationManager.
        
        Args:
            output_dir: Directory for saving plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def plot_pangenome_heatmap(self, matrix_df: pd.DataFrame, 
                              output_file: Optional[str] = None) -> str:
        """
        Create heatmap showing EC presence across strains.
        
        Args:
            matrix_df: Comparison matrix with EC numbers and strain data
            output_file: Custom output file path (optional)
            
        Returns:
            Path to saved plot
        """
        logger.info("Creating pangenome heatmap...")
        
        if output_file is None:
            output_file = self.output_dir / "pangenome_heatmap.png"
        else:
            output_file = Path(output_file)
        
        # Prepare data
        strains = [col for col in matrix_df.columns if col != 'EC_number']
        data = matrix_df[strains].values
        
        # Create figure with adaptive sizing
        num_strains = len(strains)
        num_ecs = len(matrix_df)
        
        # Adaptive sizing based on data dimensions
        if num_strains > 50:
            fig_width = min(50, num_strains * 0.4)  # Cap maximum width
            font_size_x = max(6, 12 - num_strains // 10)  # Smaller font for many strains
        else:
            fig_width = max(12, num_strains * 0.8)
            font_size_x = 10
            
        if num_ecs > 20:
            fig_height = min(30, num_ecs * 0.3)  # Cap maximum height
            font_size_y = max(6, 10 - num_ecs // 5)  # Smaller font for many ECs
        else:
            fig_height = max(8, num_ecs * 0.4)
            font_size_y = 8
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Create custom colormap
        colors = ['#e74c3c', '#f39c12', '#2ecc71']  # Red, Orange, Green
        cmap = plt.matplotlib.colors.ListedColormap(colors)
        
        # Plot heatmap
        im = ax.imshow(data, aspect='auto', cmap=cmap, vmin=0, vmax=2)
        
        # Set ticks and labels with adaptive spacing
        if num_strains > 50:
            # Remove x-axis labels for crowded plots - too many to read anyway
            ax.set_xticks([])
            ax.set_xlabel(f'Strains (n={num_strains}) - Labels hidden due to crowding', 
                         fontsize=12, weight='bold')
        elif num_strains > 25:
            # Show every other strain for moderately crowded plots
            step = 2
            x_indices = range(0, len(strains), step)
            ax.set_xticks(x_indices)
            ax.set_xticklabels([strains[i][:10] for i in x_indices], 
                               rotation=90, ha='center', fontsize=font_size_x)
        else:
            ax.set_xticks(np.arange(len(strains)))
            # Shorten long strain names
            short_names = [name[:15] + '...' if len(name) > 15 else name for name in strains]
            ax.set_xticklabels(short_names, rotation=45, ha='right', fontsize=font_size_x)
        
        ax.set_yticks(np.arange(len(matrix_df)))
        ax.set_yticklabels(matrix_df['EC_number'], fontsize=font_size_y)
        
        # Labels and title
        if num_strains <= 50:  # Only set simple label if not crowded
            ax.set_xlabel('Strain', fontsize=12, weight='bold')
        ax.set_ylabel('EC Number', fontsize=12, weight='bold')
        ax.set_title('EC Number Presence Across Strains', fontsize=14, weight='bold', pad=20)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Status', rotation=270, labelpad=20, fontsize=11, weight='bold')
        cbar.set_ticks([0, 1, 2])
        cbar.set_ticklabels(['Not Found', 'Partially Found', 'Fully Found'])
        
        # Add grid for better readability
        ax.set_xticks(np.arange(len(strains)) + 0.5, minor=True)
        ax.set_yticks(np.arange(len(matrix_df)) + 0.5, minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved pangenome heatmap to {output_file}")
        return str(output_file)
    
    def plot_strain_completeness(self, rankings_df: pd.DataFrame,
                                output_file: Optional[str] = None) -> str:
        """
        Create bar plot showing strain completeness rankings.
        
        Args:
            rankings_df: DataFrame with strain rankings
            output_file: Custom output file path (optional)
            
        Returns:
            Path to saved plot
        """
        logger.info("Creating strain completeness plot...")
        
        if output_file is None:
            output_file = self.output_dir / "strain_completeness.png"
        else:
            output_file = Path(output_file)
        
        # Adaptive sizing based on number of strains
        num_strains = len(rankings_df)
        
        if num_strains > 50:
            # For many strains, show only top 30 and create a separate overview
            top_strains = rankings_df.head(30)
            fig_height = max(16, min(25, num_strains * 0.4))
            fontsize_strain = max(6, 10 - num_strains // 20)
            show_labels = num_strains <= 100
        else:
            top_strains = rankings_df
            fig_height = max(12, num_strains * 0.4)
            fontsize_strain = 10
            show_labels = True
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, fig_height))
        
        # Plot 1: Completeness scores (top strains only if too many)
        colors = plt.cm.RdYlGn(top_strains['Completeness_Score'] / 100)
        bars1 = ax1.barh(range(len(top_strains)), top_strains['Completeness_Score'], 
                        color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_yticks(range(len(top_strains)))
        
        # Shorten strain names for crowded plots
        strain_labels = top_strains['Strain'].tolist()
        if num_strains > 50:
            strain_labels = [name[:20] + '...' if len(name) > 20 else name for name in strain_labels]
        
        ax1.set_yticklabels(strain_labels, fontsize=fontsize_strain)
        ax1.set_xlabel('Completeness Score (%)', fontsize=12, weight='bold')
        
        if num_strains > 50:
            ax1.set_title(f'Top {len(top_strains)} Strain Pathway Completeness Rankings (of {num_strains} total)', 
                         fontsize=14, weight='bold', pad=20)
        else:
            ax1.set_title('Strain Pathway Completeness Rankings', fontsize=14, weight='bold', pad=20)
        
        ax1.set_xlim(0, 100)
        
        # Add value labels only if not too crowded
        if show_labels and len(top_strains) <= 50:
            for i, (bar, score) in enumerate(zip(bars1, top_strains['Completeness_Score'])):
                ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                        f'{score:.1f}%', va='center', fontsize=9, weight='bold')
        
        # Plot 2: Detailed breakdown (use top strains for consistency)
        x_pos = np.arange(len(top_strains))
        width = 0.25
        
        bars2 = ax2.bar(x_pos - width, top_strains['Fully_Found'], width, 
                       label='Fully Found', color='#2ecc71', alpha=0.8)
        bars3 = ax2.bar(x_pos, top_strains['Partially_Found'], width,
                       label='Partially Found', color='#f39c12', alpha=0.8)
        bars4 = ax2.bar(x_pos + width, top_strains['Not_Found'], width,
                       label='Not Found', color='#e74c3c', alpha=0.8)
        
        ax2.set_xlabel('Strain', fontsize=12, weight='bold')
        ax2.set_ylabel('Number of EC Numbers', fontsize=12, weight='bold')
        
        if num_strains > 50:
            ax2.set_title(f'EC Number Status Distribution - Top {len(top_strains)} Strains', 
                         fontsize=14, weight='bold')
        else:
            ax2.set_title('EC Number Status Distribution by Strain', fontsize=14, weight='bold')
        ax2.set_xticks(x_pos)
        
        # Use shortened labels and adaptive spacing
        if num_strains > 80:
            # Show every nth strain for very crowded plots
            step = max(1, len(top_strains) // 30)
            ax2.set_xticks(x_pos[::step])
            ax2.set_xticklabels([strain_labels[i] for i in range(0, len(strain_labels), step)], 
                               rotation=45, ha='right', fontsize=fontsize_strain)
        else:
            ax2.set_xticklabels(strain_labels, rotation=45, ha='right', fontsize=fontsize_strain)
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved strain completeness plot to {output_file}")
        return str(output_file)
    
    def plot_similarity_analysis(self, similarity_df: pd.DataFrame,
                                output_file: Optional[str] = None) -> str:
        """
        Create plots showing strain similarity analysis.
        
        Args:
            similarity_df: DataFrame with pairwise similarity data
            output_file: Custom output file path (optional)
            
        Returns:
            Path to saved plot
        """
        logger.info("Creating similarity analysis plot...")
        
        if output_file is None:
            output_file = self.output_dir / "strain_similarity.png"
        else:
            output_file = Path(output_file)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Strain Similarity Analysis', fontsize=16, weight='bold')
        
        # Plot 1: Jaccard similarity distribution
        ax1.hist(similarity_df['Jaccard_similarity'], bins=20, color='#3498db', 
                alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Jaccard Similarity', fontsize=11, weight='bold')
        ax1.set_ylabel('Frequency', fontsize=11, weight='bold')
        ax1.set_title('Distribution of Jaccard Similarities', fontsize=12, weight='bold')
        ax1.axvline(similarity_df['Jaccard_similarity'].mean(), color='red', 
                   linestyle='--', linewidth=2, label=f"Mean: {similarity_df['Jaccard_similarity'].mean():.3f}")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Correlation vs Jaccard scatter
        ax2.scatter(similarity_df['Jaccard_similarity'], similarity_df['Correlation'],
                   alpha=0.6, color='#e74c3c')
        ax2.set_xlabel('Jaccard Similarity', fontsize=11, weight='bold')
        ax2.set_ylabel('Correlation', fontsize=11, weight='bold')
        ax2.set_title('Jaccard vs Correlation Similarity', fontsize=12, weight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(similarity_df['Jaccard_similarity'], similarity_df['Correlation'], 1)
        p = np.poly1d(z)
        ax2.plot(similarity_df['Jaccard_similarity'], p(similarity_df['Jaccard_similarity']), 
                'r--', alpha=0.8, linewidth=2)
        
        # Plot 3: Shared ECs distribution
        ax3.hist(similarity_df['Shared_ECs'], bins=15, color='#9b59b6', 
                alpha=0.7, edgecolor='black')
        ax3.set_xlabel('Number of Shared ECs', fontsize=11, weight='bold')
        ax3.set_ylabel('Frequency', fontsize=11, weight='bold')
        ax3.set_title('Distribution of Shared EC Numbers', fontsize=12, weight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Similarity heatmap (if not too many strains)
        strains = list(set(similarity_df['Strain_1'].tolist() + similarity_df['Strain_2'].tolist()))
        
        if len(strains) <= 20:  # Only create heatmap for reasonable number of strains
            similarity_matrix = pd.pivot_table(similarity_df, values='Jaccard_similarity',
                                             index='Strain_1', columns='Strain_2', fill_value=0)
            
            # Make matrix symmetric
            for i in similarity_matrix.index:
                for j in similarity_matrix.columns:
                    if pd.isna(similarity_matrix.loc[i, j]) or similarity_matrix.loc[i, j] == 0:
                        if j in similarity_matrix.index and i in similarity_matrix.columns:
                            similarity_matrix.loc[i, j] = similarity_matrix.loc[j, i]
            
            # Fill diagonal with 1s
            for strain in strains:
                if strain in similarity_matrix.index and strain in similarity_matrix.columns:
                    similarity_matrix.loc[strain, strain] = 1.0
            
            sns.heatmap(similarity_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                       ax=ax4, square=True, cbar_kws={'label': 'Jaccard Similarity'})
            ax4.set_title('Strain Similarity Matrix', fontsize=12, weight='bold')
            ax4.set_xlabel('Strain', fontsize=11, weight='bold')
            ax4.set_ylabel('Strain', fontsize=11, weight='bold')
        else:
            ax4.text(0.5, 0.5, f'Too many strains ({len(strains)}) for\nsimilarity matrix visualization',
                    ha='center', va='center', transform=ax4.transAxes, fontsize=12)
            ax4.set_title('Similarity Matrix (Too Many Strains)', fontsize=12, weight='bold')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved similarity analysis to {output_file}")
        return str(output_file)
    
    def plot_statistical_overview(self, rankings_df: pd.DataFrame,
                                 output_file: Optional[str] = None) -> str:
        """
        Create statistical overview plots.
        
        Args:
            rankings_df: DataFrame with strain rankings
            output_file: Custom output file path (optional)
            
        Returns:
            Path to saved plot
        """
        logger.info("Creating statistical overview plot...")
        
        if output_file is None:
            output_file = self.output_dir / "statistical_overview.png"
        else:
            output_file = Path(output_file)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Pangenomic Analysis - Statistical Overview', fontsize=16, weight='bold')
        
        # Plot 1: Distribution of completeness scores
        ax1.hist(rankings_df['Completeness_Score'], bins=15, color='#2ecc71', 
                alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Completeness Score (%)', fontsize=11, weight='bold')
        ax1.set_ylabel('Number of Strains', fontsize=11, weight='bold')
        ax1.set_title('Distribution of Pathway Completeness', fontsize=12, weight='bold')
        ax1.axvline(rankings_df['Completeness_Score'].mean(), color='red', 
                   linestyle='--', linewidth=2, label=f"Mean: {rankings_df['Completeness_Score'].mean():.1f}%")
        ax1.axvline(rankings_df['Completeness_Score'].median(), color='orange', 
                   linestyle='--', linewidth=2, label=f"Median: {rankings_df['Completeness_Score'].median():.1f}%")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Hits vs Proteins scatter
        ax2.scatter(rankings_df['Total_Hits'], rankings_df['Unique_Proteins'], 
                   c=rankings_df['Completeness_Score'], cmap='RdYlGn', 
                   s=60, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax2.set_xlabel('Total Hits', fontsize=11, weight='bold')
        ax2.set_ylabel('Unique Proteins', fontsize=11, weight='bold')
        ax2.set_title('Hits vs Unique Proteins (colored by completeness)', fontsize=12, weight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(ax2.collections[0], ax=ax2)
        cbar.set_label('Completeness Score (%)', rotation=270, labelpad=15)
        
        # Plot 3: Box plot of EC status distribution
        status_data = [rankings_df['Fully_Found'], rankings_df['Partially_Found'], rankings_df['Not_Found']]
        bp = ax3.boxplot(status_data, labels=['Fully Found', 'Partially Found', 'Not Found'],
                        patch_artist=True, notch=True)
        
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax3.set_ylabel('Number of EC Numbers', fontsize=11, weight='bold')
        ax3.set_title('EC Status Distribution Across Strains', fontsize=12, weight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Top and bottom performers
        n_top = min(10, len(rankings_df))
        top_strains = rankings_df.head(n_top)
        
        y_pos = np.arange(len(top_strains))
        bars = ax4.barh(y_pos, top_strains['Completeness_Score'], 
                       color=plt.cm.RdYlGn(top_strains['Completeness_Score'] / 100),
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(top_strains['Strain'], fontsize=10)
        ax4.set_xlabel('Completeness Score (%)', fontsize=11, weight='bold')
        ax4.set_title(f'Top {n_top} Performing Strains', fontsize=12, weight='bold')
        ax4.set_xlim(0, 100)
        
        # Add value labels
        for i, (bar, score) in enumerate(zip(bars, top_strains['Completeness_Score'])):
            ax4.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                    f'{score:.1f}%', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved statistical overview to {output_file}")
        return str(output_file)
    
    def create_summary_dashboard(self, rankings_df: pd.DataFrame, 
                                matrix_df: pd.DataFrame,
                                output_file: Optional[str] = None) -> str:
        """
        Create a comprehensive summary dashboard.
        
        Args:
            rankings_df: DataFrame with strain rankings
            matrix_df: Comparison matrix
            output_file: Custom output file path (optional)
            
        Returns:
            Path to saved plot
        """
        logger.info("Creating summary dashboard...")
        
        if output_file is None:
            output_file = self.output_dir / "summary_dashboard.png"
        else:
            output_file = Path(output_file)
        
        fig = plt.figure(figsize=(20, 14))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # Title
        fig.suptitle('Pangenomic Analysis Summary Dashboard', fontsize=20, weight='bold', y=0.98)
        
        # Plot 1: Overall statistics (text summary)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.axis('off')
        
        total_strains = len(rankings_df)
        total_ecs = len(matrix_df)
        avg_completeness = rankings_df['Completeness_Score'].mean()
        best_strain = rankings_df.iloc[0]
        
        stats_text = f"""
        PANGENOMIC ANALYSIS SUMMARY
        
        Total Strains Analyzed: {total_strains}
        Total EC Numbers: {total_ecs}
        Average Completeness: {avg_completeness:.1f}%
        
        Best Performing Strain:
        {best_strain['Strain']}
        Score: {best_strain['Completeness_Score']:.1f}%
        
        Total Hits: {rankings_df['Total_Hits'].sum():,}
        Unique Proteins: {rankings_df['Unique_Proteins'].sum():,}
        """
        
        ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Plot 2: Completeness distribution
        ax2 = fig.add_subplot(gs[0, 1:3])
        ax2.hist(rankings_df['Completeness_Score'], bins=15, color='#2ecc71', 
                alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Completeness Score (%)', fontweight='bold')
        ax2.set_ylabel('Number of Strains', fontweight='bold')
        ax2.set_title('Pathway Completeness Distribution', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Top performers
        ax3 = fig.add_subplot(gs[0, 3])
        top_10 = rankings_df.head(10)
        colors = plt.cm.RdYlGn(top_10['Completeness_Score'] / 100)
        bars = ax3.barh(range(len(top_10)), top_10['Completeness_Score'], color=colors)
        ax3.set_yticks(range(len(top_10)))
        ax3.set_yticklabels(top_10['Strain'], fontsize=9)
        ax3.set_xlabel('Score (%)', fontweight='bold')
        ax3.set_title('Top 10 Strains', fontweight='bold')
        
        # Plot 4: Heatmap (subset if too large)
        ax4 = fig.add_subplot(gs[1:, :2])
        
        # Show subset of data if too large
        max_display = 20
        if len(matrix_df) > max_display:
            display_matrix = matrix_df.head(max_display)
            title_suffix = f" (showing top {max_display} ECs)"
        else:
            display_matrix = matrix_df
            title_suffix = ""
        
        strains = [col for col in display_matrix.columns if col != 'EC_number']
        data = display_matrix[strains].values
        
        colors = ['#e74c3c', '#f39c12', '#2ecc71']
        cmap = plt.matplotlib.colors.ListedColormap(colors)
        
        im = ax4.imshow(data, aspect='auto', cmap=cmap, vmin=0, vmax=2)
        ax4.set_yticks(np.arange(len(display_matrix)))
        ax4.set_yticklabels(display_matrix['EC_number'], fontsize=6)
        
        # Handle x-axis labels based on number of strains
        if len(strains) > 30:
            # Remove x-axis labels for crowded summary heatmap
            ax4.set_xticks([])
            ax4.set_xlabel(f'Strains (n={len(strains)}) - Labels hidden', fontsize=10, weight='bold')
        elif len(strains) > 15:
            # Show every other strain for moderate crowding
            step = 2
            x_indices = range(0, len(strains), step)
            ax4.set_xticks(x_indices)
            ax4.set_xticklabels([strains[i][:8] for i in x_indices], rotation=90, ha='center', fontsize=7)
        else:
            # Show all strain names for small numbers
            ax4.set_xticks(np.arange(len(strains)))
            ax4.set_xticklabels([name[:10] for name in strains], rotation=45, ha='right', fontsize=8)
        
        ax4.set_title(f'EC Presence Heatmap{title_suffix}', fontweight='bold')
        
        # Plot 5: Summary statistics
        ax5 = fig.add_subplot(gs[1:, 2:])
        
        # Create stacked bar chart
        categories = ['Fully Found', 'Partially Found', 'Not Found']
        means = [rankings_df['Fully_Found'].mean(), 
                rankings_df['Partially_Found'].mean(),
                rankings_df['Not_Found'].mean()]
        
        colors_stack = ['#2ecc71', '#f39c12', '#e74c3c']
        bars = ax5.bar(categories, means, color=colors_stack, alpha=0.8, edgecolor='black')
        
        ax5.set_ylabel('Average per Strain', fontweight='bold')
        ax5.set_title('Average EC Status Distribution', fontweight='bold')
        ax5.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, value in zip(bars, means):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved summary dashboard to {output_file}")
        return str(output_file)
    
    def cluster_strains(self, matrix_df: pd.DataFrame, method: str = 'ward', 
                       metric: str = 'euclidean') -> Tuple[pd.DataFrame, np.ndarray]:
        """Cluster strains based on EC profile similarity."""
        from scipy.cluster.hierarchy import linkage, fcluster
        
        logger.info("Clustering strains by EC profile similarity...")
        
        strains = [col for col in matrix_df.columns if col != 'EC_number']
        data = matrix_df[strains].T.values  # Transpose: strains as rows
        
        # Hierarchical clustering
        linkage_matrix = linkage(data, method=method, metric=metric)
        
        # Cut tree to get clusters (use original threshold)
        clusters = fcluster(linkage_matrix, t=0.3, criterion='distance')
        
        # Create cluster assignments
        strain_clusters = pd.DataFrame({
            'strain': strains,
            'cluster': clusters
        })
        
        # Sort by cluster
        strain_clusters = strain_clusters.sort_values('cluster')
        
        logger.info(f"✓ Found {len(set(clusters))} clusters")
        
        # Log cluster composition with meaningful names
        for cluster_id in sorted(set(clusters)):
            members = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
            # Generate meaningful cluster name based on common genus/characteristics
            cluster_name = self._generate_cluster_name(members, cluster_id)
            logger.info(f"  {cluster_name}: {len(members)} strain(s)")
        
        return strain_clusters, linkage_matrix
    
    def _generate_cluster_name(self, strain_names: List[str], cluster_id: int) -> str:
        """Generate meaningful cluster names based on strain characteristics."""
        # Extract genus names
        genera = []
        for strain in strain_names:
            # Extract genus from strain name (usually first part before underscore)
            parts = strain.split('_')
            if len(parts) > 0:
                genus_candidate = parts[0]
                # Clean up common prefixes
                if genus_candidate.startswith('GCF') or genus_candidate.startswith('GCA'):
                    # Try next part if it's an accession
                    if len(parts) > 1:
                        genus_candidate = parts[1]
                genera.append(genus_candidate)
        
        # Find most common genus
        from collections import Counter
        if genera:
            genus_counts = Counter(genera)
            most_common_genus = genus_counts.most_common(1)[0][0]
            
            # Generate cluster name based on composition
            if len(set(genera)) == 1:
                # All strains from same genus
                return f"Cluster {cluster_id}: {most_common_genus} group"
            elif genus_counts[most_common_genus] > len(genera) * 0.7:
                # Predominantly one genus
                return f"Cluster {cluster_id}: {most_common_genus}-dominated"
            else:
                # Mixed genera
                top_genera = [genus for genus, count in genus_counts.most_common(2)]
                return f"Cluster {cluster_id}: {'/'.join(top_genera)} mixed"
        else:
            return f"Cluster {cluster_id}: Mixed group"
    
    def cluster_ecs(self, matrix_df: pd.DataFrame, method: str = 'ward', 
                    metric: str = 'euclidean') -> Tuple[pd.DataFrame, np.ndarray]:
        """Cluster EC numbers based on presence patterns across strains."""
        from scipy.cluster.hierarchy import linkage, fcluster
        
        logger.info("Clustering EC numbers by presence pattern...")
        
        # Use EC data directly (rows are ECs, columns are strains)
        strains = [col for col in matrix_df.columns if col != 'EC_number']
        data = matrix_df[strains].values  # ECs as rows
        
        # Hierarchical clustering
        linkage_matrix = linkage(data, method=method, metric=metric)
        
        # Cut tree to get clusters
        clusters = fcluster(linkage_matrix, t=0.3, criterion='distance')
        
        # Create cluster assignments
        ec_clusters = pd.DataFrame({
            'EC_number': matrix_df['EC_number'],
            'cluster': clusters
        })
        
        # Sort by cluster
        ec_clusters = ec_clusters.sort_values('cluster')
        
        logger.info(f"✓ Found {len(set(clusters))} EC clusters")
        
        return ec_clusters, linkage_matrix
    
    def plot_clustered_heatmap(self, matrix_df: pd.DataFrame, strain_clusters: pd.DataFrame,
                              output_file: Optional[str] = None) -> str:
        """Heatmap with seaborn clustermap for automatic hierarchical clustering."""
        if output_file is None:
            output_file = str(self.output_dir / "pangenome_clustered_heatmap.png")
        
        logger.info("Creating clustered heatmap using seaborn clustermap...")
        
        # Prepare data for clustermap
        strains = [col for col in matrix_df.columns if col != 'EC_number']
        data_matrix = matrix_df.set_index('EC_number')[strains]
        
        num_strains = len(strains)
        num_ecs = len(data_matrix)
        
        # Simplify strain labels with adaptive shortening
        simple_strain_labels = {}
        for strain in strains:
            parts = strain.split('_')
            if num_strains > 50:
                # Very short labels for crowded plots
                if len(parts) > 1:
                    simple_strain_labels[strain] = f'{parts[0][:6]}_{parts[1][:4]}'
                else:
                    simple_strain_labels[strain] = strain[:8]
            elif len(parts) > 1:
                simple_strain_labels[strain] = f'{parts[0][:8]}_{parts[1][:6]}'
            else:
                simple_strain_labels[strain] = strain[:12]
        
        # Rename columns for display
        display_data = data_matrix.copy()
        if num_strains <= 50:  # Only rename if labels will be visible
            display_data.columns = [simple_strain_labels[col] for col in display_data.columns]
        
        # Adaptive figure sizing
        if num_strains > 50:
            fig_width = min(25, num_strains * 0.3)
            font_size = max(4, 8 - num_strains // 20)
        else:
            fig_width = max(10, num_strains * 0.4)
            font_size = 8
            
        if num_ecs > 30:
            fig_height = min(20, num_ecs * 0.3)
        else:
            fig_height = max(6, num_ecs * 0.3)
        
        # Create clustered heatmap using seaborn
        plt.figure(figsize=(fig_width, fig_height))
        
        # Custom colormap
        colors = ['#e74c3c', '#f39c12', '#2ecc71']  # Red, Orange, Green
        cmap = sns.color_palette(colors, as_cmap=True)
        
        # Create clustermap with hierarchical clustering on both axes
        if num_strains > 80 or num_ecs > 50:
            # For very large datasets, hide labels to avoid crowding
            g = sns.clustermap(
                display_data,
                cmap=cmap,
                vmin=0, vmax=2,
                figsize=(fig_width, fig_height),
                cbar_kws={'label': 'Enzyme Status'},
                xticklabels=False,
                yticklabels=True if num_ecs <= 50 else False,
                linewidths=0.1,
                method='ward',
                metric='euclidean'
            )
        else:
            # For smaller datasets, show labels
            g = sns.clustermap(
                display_data,
                cmap=cmap,
                vmin=0, vmax=2,
                figsize=(fig_width, fig_height),
                cbar_kws={'label': 'Enzyme Status'},
                xticklabels=True,
                yticklabels=True,
                linewidths=0.1,
                method='ward',
                metric='euclidean'
            )
        
        # Adjust font sizes
        if num_strains <= 50:
            g.ax_heatmap.tick_params(axis='x', labelsize=font_size, rotation=45)
        g.ax_heatmap.tick_params(axis='y', labelsize=max(6, font_size))
        
        # Update colorbar labels
        cbar = g.ax_cbar
        cbar.set_yticklabels(['Not Found', 'Partial Hit', 'Complete'])
        cbar.set_ylabel('Enzyme Status', rotation=270, labelpad=20, fontweight='bold')
        
        # Set title
        g.fig.suptitle('Hierarchically Clustered EC Number Presence Across Strains', 
                      fontsize=14, fontweight='bold', y=0.98)
        
        # Add meaningful cluster annotations if not too crowded
        if num_strains <= 30 and hasattr(strain_clusters, 'cluster'):
            self._add_cluster_labels_to_clustermap(g, strain_clusters, simple_strain_labels)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved clustered heatmap to {output_file}")
        return str(output_file)
    
    def _add_cluster_labels_to_clustermap(self, g, strain_clusters: pd.DataFrame, simple_strain_labels: dict):
        """Add meaningful cluster name annotations to seaborn clustermap."""
        
        # Get the reordered column order from the clustermap
        reordered_cols = g.dendrogram_col.reordered_ind
        original_strains = list(strain_clusters['strain'])
        
        # Map positions to cluster names
        cluster_info = {}
        for i, original_idx in enumerate(reordered_cols):
            if original_idx < len(original_strains):
                strain = original_strains[original_idx]
                cluster_id = strain_clusters[strain_clusters['strain'] == strain]['cluster'].iloc[0]
                if cluster_id not in cluster_info:
                    cluster_info[cluster_id] = {'positions': [], 'strains': []}
                cluster_info[cluster_id]['positions'].append(i)
                cluster_info[cluster_id]['strains'].append(strain)
        
        # Add cluster annotations above the heatmap
        ax = g.ax_heatmap
        for cluster_id, info in cluster_info.items():
            if len(info['positions']) > 1:  # Only annotate multi-strain clusters
                cluster_center = np.mean(info['positions'])
                # Use simple cluster number for annotation
                cluster_label = f"C{cluster_id}"
                
                # Add annotation above the plot
                ax.text(cluster_center, len(ax.get_yticklabels()) + 0.5, cluster_label, 
                       ha='center', va='bottom', rotation=45, fontsize=8,
                       weight='bold', color='darkblue')
    
    def _add_cluster_annotations(self, ax, strain_clusters: pd.DataFrame, ec_clusters: pd.DataFrame,
                               num_strains: int, num_ecs: int, font_size_x: int, font_size_y: int):
        """Add meaningful cluster name annotations to the heatmap (legacy method)."""
        
        # Add strain cluster annotations (top of plot)
        if num_strains <= 50:  # Only for readable plots
            current_pos = 0
            for cluster_id in sorted(strain_clusters['cluster'].unique()):
                cluster_strains = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
                cluster_size = len(cluster_strains)
                cluster_center = current_pos + cluster_size / 2 - 0.5
                
                # Use simple cluster number for annotation
                cluster_label = f"C{cluster_id}"
                
                # Add annotation above the plot
                ax.text(cluster_center, -0.5, cluster_label, 
                       ha='center', va='top', rotation=45, fontsize=max(6, font_size_x-2),
                       weight='bold', color='darkblue')
                
                current_pos += cluster_size
        
        # Add EC cluster annotations (right side of plot)
        if num_ecs <= 30:  # Only for readable plots
            current_pos = 0
            for cluster_id in sorted(ec_clusters['cluster'].unique()):
                cluster_ecs = ec_clusters[ec_clusters['cluster'] == cluster_id]['EC_number'].tolist()
                cluster_size = len(cluster_ecs)
                cluster_center = current_pos + cluster_size / 2 - 0.5
                
                # Generate EC cluster name based on pathway function if possible
                ec_cluster_name = f"EC-C{cluster_id}"
                
                # Add annotation to the right of the plot
                ax.text(num_strains + 0.5, cluster_center, ec_cluster_name, 
                       ha='left', va='center', fontsize=max(6, font_size_y-1),
                       weight='bold', color='darkred')
                
                current_pos += cluster_size
    
    def plot_cluster_representatives(self, matrix_df: pd.DataFrame, strain_clusters: pd.DataFrame,
                                   output_file: Optional[str] = None) -> str:
        """Show one representative per cluster with meaningful cluster names."""
        if output_file is None:
            output_file = str(self.output_dir / "cluster_representatives.png")
        
        logger.info("Creating cluster representative plot with meaningful names...")
        
        representatives = []
        cluster_labels = []
        
        for cluster_id in sorted(strain_clusters['cluster'].unique()):
            cluster_members = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
            rep = cluster_members[0]  # Use first member as representative
            representatives.append(rep)
            
            # Use simple cluster numbers for x-axis labels
            cluster_labels.append(f"Cluster {cluster_id}\n(n={len(cluster_members)})")
        
        data = matrix_df[representatives].values
        
        fig, ax = plt.subplots(figsize=(max(10, len(representatives)*1.5), 
                                       max(8, len(matrix_df)*0.2)))
        
        im = ax.imshow(data, aspect='auto', cmap='RdYlGn', vmin=0, vmax=2)
        
        ax.set_xticks(np.arange(len(representatives)))
        ax.set_yticks(np.arange(len(matrix_df)))
        ax.set_xticklabels(cluster_labels, rotation=0, ha='center', fontsize=10, weight='bold')
        ax.set_yticklabels(matrix_df['EC_number'], fontsize=9)
        
        ax.set_xlabel('Cluster Representative (by phylogenetic similarity)', fontsize=12, weight='bold')
        ax.set_ylabel('EC Number', fontsize=12, weight='bold')
        ax.set_title('Pathway Profiles by Strain Cluster Representatives', 
                    fontsize=14, weight='bold', pad=20)
        
        # Add cluster separators
        for i in range(1, len(representatives)):
            ax.axvline(x=i-0.5, color='black', linewidth=1, alpha=0.5)
        
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Enzyme Status', rotation=270, labelpad=20, weight='bold')
        cbar.set_ticks([0, 1, 2])
        cbar.set_ticklabels(['Not Found', 'Partial Hit', 'Complete'])
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved cluster representatives to {output_file}")
        return str(output_file)
    
    def plot_dendrogram(self, linkage_matrix: np.ndarray, strain_clusters: pd.DataFrame,
                       output_file: Optional[str] = None) -> str:
        """Plot dendrogram showing strain relationships."""
        from scipy.cluster.hierarchy import dendrogram
        
        if output_file is None:
            output_file = str(self.output_dir / "strain_dendrogram.png")
        
        logger.info("Creating dendrogram...")
        
        num_strains = len(strain_clusters)
        fig, ax = plt.subplots(figsize=(max(12, num_strains * 0.2), 8))
        
        if num_strains > 50:
            # Hide labels for crowded dendrograms
            dendrogram(
                linkage_matrix,
                ax=ax,
                leaf_rotation=90,
                leaf_font_size=0,  # Hide labels
                no_labels=True
            )
            xlabel = f'Strains (n={num_strains}) - Labels hidden due to crowding'
        else:
            # Show labels for smaller numbers
            strain_labels = strain_clusters['strain'].tolist()
            if num_strains > 25:
                # Shorten labels for moderate numbers
                strain_labels = [name[:10] + '...' if len(name) > 10 else name for name in strain_labels]
            
            dendrogram(
                linkage_matrix,
                labels=strain_labels,
                ax=ax,
                leaf_rotation=90,
                leaf_font_size=max(6, 12 - num_strains // 5)
            )
            xlabel = 'Strain'
        
        ax.set_xlabel(xlabel, fontsize=12, weight='bold')
        ax.set_ylabel('Distance', fontsize=12, weight='bold')
        ax.set_title('Hierarchical Clustering of Strains', 
                    fontsize=14, weight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved dendrogram to {output_file}")
        return str(output_file)
    
    def save_cluster_summary(self, strain_clusters: pd.DataFrame, matrix_df: pd.DataFrame,
                           output_file: Optional[str] = None) -> pd.DataFrame:
        """Save detailed cluster information with meaningful names."""
        if output_file is None:
            output_file = str(self.output_dir / "cluster_summary.csv")
        
        logger.info("Creating cluster summary with meaningful names...")
        
        summary = []
        
        for cluster_id in sorted(strain_clusters['cluster'].unique()):
            members = strain_clusters[strain_clusters['cluster'] == cluster_id]['strain'].tolist()
            
            # Calculate average completeness for this cluster
            cluster_data = matrix_df[members]
            avg_completeness = (cluster_data == 2).sum().sum() / (len(cluster_data) * len(members)) * 100
            
            # Generate meaningful cluster name
            cluster_name = self._generate_cluster_name(members, cluster_id)
            
            # Calculate additional cluster statistics
            partial_completeness = (cluster_data == 1).sum().sum() / (len(cluster_data) * len(members)) * 100
            not_found_percent = (cluster_data == 0).sum().sum() / (len(cluster_data) * len(members)) * 100
            
            summary.append({
                'cluster_id': cluster_id,
                'cluster_name': cluster_name,
                'num_strains': len(members),
                'members': '; '.join(members),
                'avg_completeness_percent': round(avg_completeness, 2),
                'avg_partial_percent': round(partial_completeness, 2),
                'avg_not_found_percent': round(not_found_percent, 2),
                'representative': members[0],
                'dominant_genus': self._get_dominant_genus(members),
                'diversity_score': len(set([m.split('_')[0] for m in members])) / len(members)
            })
        
        summary_df = pd.DataFrame(summary)
        summary_df = summary_df.sort_values('avg_completeness_percent', ascending=False)
        summary_df.to_csv(output_file, index=False)
        
        logger.info(f"✓ Saved cluster summary with meaningful names to {output_file}")
        return summary_df
    
    def _get_dominant_genus(self, strain_names: List[str]) -> str:
        """Get the dominant genus in a cluster."""
        genera = [strain.split('_')[0] for strain in strain_names]
        from collections import Counter
        genus_counts = Counter(genera)
        return genus_counts.most_common(1)[0][0]
    
    def generate_clustered_plots(self, matrix_df: pd.DataFrame) -> List[str]:
        """Generate all clustering-related plots with bi-clustering."""
        logger.info("Generating bi-clustered visualization plots...")
        
        plot_files = []
        
        try:
            # Cluster strains and ECs
            strain_clusters, strain_linkage = self.cluster_strains(matrix_df)
            ec_clusters, ec_linkage = self.cluster_ecs(matrix_df)
            
            # Save cluster info with meaningful names
            cluster_summary = self.save_cluster_summary(strain_clusters, matrix_df)
            
            # Generate visualizations
            plot_files.append(self.plot_dendrogram(strain_linkage, strain_clusters))
            plot_files.append(self.plot_clustered_heatmap(matrix_df, strain_clusters))
            plot_files.append(self.plot_cluster_representatives(matrix_df, strain_clusters))
            
            # Add EC clustering dendrogram
            ec_dendrogram_file = str(self.output_dir / "ec_dendrogram.png")
            plot_files.append(self.plot_ec_dendrogram(ec_linkage, ec_clusters, ec_dendrogram_file))
            
            logger.info(f"✓ Generated {len(plot_files)} bi-clustered plots with meaningful naming")
            
        except Exception as e:
            logger.error(f"Error generating clustered plots: {e}")
            import traceback
            traceback.print_exc()
        
        return plot_files
    
    def plot_ec_dendrogram(self, linkage_matrix: np.ndarray, ec_clusters: pd.DataFrame,
                          output_file: str) -> str:
        """Plot dendrogram showing EC number relationships."""
        from scipy.cluster.hierarchy import dendrogram
        
        logger.info("Creating EC dendrogram...")
        
        num_ecs = len(ec_clusters)
        fig, ax = plt.subplots(figsize=(max(10, num_ecs * 0.2), 6))
        
        if num_ecs > 30:
            # Hide labels for crowded dendrograms
            dendrogram(
                linkage_matrix,
                ax=ax,
                leaf_rotation=90,
                leaf_font_size=0,
                no_labels=True
            )
            xlabel = f'EC Numbers (n={num_ecs}) - Labels hidden due to crowding'
        else:
            # Show labels for smaller numbers
            ec_labels = ec_clusters['EC_number'].tolist()
            
            dendrogram(
                linkage_matrix,
                labels=ec_labels,
                ax=ax,
                leaf_rotation=90,
                leaf_font_size=max(6, 10 - num_ecs // 5)
            )
            xlabel = 'EC Number'
        
        ax.set_xlabel(xlabel, fontsize=12, weight='bold')
        ax.set_ylabel('Distance', fontsize=12, weight='bold')
        ax.set_title('Hierarchical Clustering of EC Numbers by Presence Pattern', 
                    fontsize=14, weight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved EC dendrogram to {output_file}")
        return str(output_file)
    
    def generate_comparison_plots(self, matrix_df: pd.DataFrame) -> List[str]:
        """Generate basic comparison plots for matrix data."""
        logger.info("Generating comparison plots...")
        
        plot_files = []
        
        try:
            plot_files.append(self.plot_pangenome_heatmap(matrix_df))
            
            # Create a dummy rankings DataFrame for compatibility
            strains = [col for col in matrix_df.columns if col != 'EC_number']
            rankings_data = []
            for strain in strains:
                strain_data = matrix_df[strain]
                total_ecs = len(strain_data)
                found_ecs = (strain_data == 2).sum()
                partial_ecs = (strain_data == 1).sum()
                completeness = (found_ecs + partial_ecs * 0.5) / total_ecs * 100
                
                rankings_data.append({
                    'strain': strain,
                    'total_ecs': total_ecs,
                    'found_ecs': found_ecs,
                    'partial_ecs': partial_ecs,
                    'not_found_ecs': total_ecs - found_ecs - partial_ecs,
                    'completeness_percent': completeness
                })
            
            rankings_df = pd.DataFrame(rankings_data)
            plot_files.append(self.plot_strain_completeness(rankings_df))
            plot_files.append(self.create_summary_dashboard(rankings_df, matrix_df))
            
            logger.info(f"✓ Generated {len(plot_files)} comparison plots")
            
        except Exception as e:
            logger.error(f"Error generating comparison plots: {e}")
            import traceback
            traceback.print_exc()
        
        return plot_files
    
    def generate_all_plots(self, rankings_df: pd.DataFrame, 
                          matrix_df: pd.DataFrame,
                          similarity_df: Optional[pd.DataFrame] = None) -> List[str]:
        """
        Generate all visualization plots.
        
        Args:
            rankings_df: DataFrame with strain rankings
            matrix_df: Comparison matrix
            similarity_df: Optional similarity analysis DataFrame
            
        Returns:
            List of paths to generated plots
        """
        logger.info("Generating all visualization plots...")
        
        plot_files = []
        
        try:
            # Generate individual plots
            plot_files.append(self.create_summary_dashboard(rankings_df, matrix_df))
            plot_files.append(self.plot_pangenome_heatmap(matrix_df))
            plot_files.append(self.plot_strain_completeness(rankings_df))
            plot_files.append(self.plot_statistical_overview(rankings_df))
            
            if similarity_df is not None:
                plot_files.append(self.plot_similarity_analysis(similarity_df))
            
            # Generate clustered plots (like plots_collapsed.py)
            clustered_plots = self.generate_clustered_plots(matrix_df)
            plot_files.extend(clustered_plots)
            
            logger.info(f"✓ Generated {len(plot_files)} visualization plots (including {len(clustered_plots)} clustered plots)")
            
        except Exception as e:
            logger.error(f"Error generating plots: {e}")
            raise
        
        return plot_files