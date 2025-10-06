#!/usr/bin/env python3
"""
Create visualizations for EC number and Pfam domain search results.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
import sys
import warnings

# Suppress numpy warnings about subnormal values
warnings.filterwarnings("ignore", message="The value of the smallest subnormal.*is zero", category=UserWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

def load_results():
    """Load analysis results."""
    if len(sys.argv) < 3:
        print("Usage: python plot_findings.py <ec_results.csv> <detailed_hits.csv>")
        exit(1)
    ec_results = sys.argv[1] 
    detailed_hits = sys.argv[2]
    print("Loading results...")
    ec_results = pd.read_csv(ec_results)
    detailed_hits = pd.read_csv(detailed_hits)
    print(f"✓ Loaded {len(ec_results)} EC numbers and {len(detailed_hits)} hits")
    return ec_results, detailed_hits


def plot_ec_status_overview(ec_results, output_file='plots/01_ec_status_overview.png'):
    """Create a pie chart showing EC number status distribution."""
    print(f"Creating EC status overview: {output_file}")
    
    status_counts = ec_results['Status'].value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = {
        'FULLY_FOUND': '#2ecc71',
        'PARTIALLY_FOUND': '#f39c12',
        'NOT_FOUND': '#e74c3c'
    }
    
    plot_colors = [colors.get(status, '#95a5a6') for status in status_counts.index]
    
    wedges, texts, autotexts = ax.pie(
        status_counts.values,
        labels=[s.replace('_', ' ').title() for s in status_counts.index],
        autopct='%1.1f%%',
        startangle=90,
        colors=plot_colors,
        textprops={'size': 12, 'weight': 'bold'}
    )
    
    # Make percentage text white
    for autotext in autotexts:
        autotext.set_color('white')
    
    ax.set_title('EC Number Detection Status', fontsize=16, weight='bold', pad=20)
    
    # Add legend with counts
    legend_labels = [f"{status.replace('_', ' ').title()}: {count}" 
                     for status, count in status_counts.items()]
    ax.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1))
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_pfam_coverage(ec_results, output_file='plots/02_pfam_coverage.png'):
    """Create a bar chart showing Pfam domain coverage for each EC number."""
    print(f"Creating Pfam coverage plot: {output_file}")
    
    # Calculate coverage percentage
    ec_results['Coverage_%'] = (ec_results['Found_Pfam_domains'] / 
                                 ec_results['Total_Pfam_domains'] * 100)
    
    # Sort by coverage
    ec_sorted = ec_results.sort_values('Coverage_%', ascending=True)
    
    fig, ax = plt.subplots(figsize=(12, max(8, len(ec_results) * 0.3)))
    
    # Color bars by status
    colors = []
    for status in ec_sorted['Status']:
        if status == 'FULLY_FOUND':
            colors.append('#2ecc71')
        elif status == 'PARTIALLY_FOUND':
            colors.append('#f39c12')
        else:
            colors.append('#e74c3c')
    
    bars = ax.barh(range(len(ec_sorted)), ec_sorted['Coverage_%'], color=colors)
    
    ax.set_yticks(range(len(ec_sorted)))
    ax.set_yticklabels(ec_sorted['EC_number'], fontsize=10)
    ax.set_xlabel('Pfam Domain Coverage (%)', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('Pfam Domain Coverage by EC Number', fontsize=14, weight='bold', pad=20)
    ax.set_xlim(0, 105)
    
    # Add percentage labels on bars
    for i, (bar, coverage, found, total) in enumerate(zip(bars, ec_sorted['Coverage_%'], 
                                                           ec_sorted['Found_Pfam_domains'],
                                                           ec_sorted['Total_Pfam_domains'])):
        width = bar.get_width()
        label = f'{coverage:.0f}% ({found}/{total})'
        ax.text(width + 2, bar.get_y() + bar.get_height()/2, label,
                va='center', fontsize=9)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', label='Fully Found'),
        Patch(facecolor='#f39c12', label='Partially Found'),
        Patch(facecolor='#e74c3c', label='Not Found')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_hits_distribution(ec_results, output_file='plots/03_hits_distribution.png'):
    """Create a bar chart showing number of hits per EC number."""
    print(f"Creating hits distribution plot: {output_file}")
    
    # Filter to only EC numbers with hits
    ec_with_hits = ec_results[ec_results['Total_hits'] > 0].copy()
    
    if len(ec_with_hits) == 0:
        print("⚠ No EC numbers with hits, skipping plot")
        return
    
    ec_with_hits = ec_with_hits.sort_values('Total_hits', ascending=True)
    
    fig, ax = plt.subplots(figsize=(12, max(6, len(ec_with_hits) * 0.3)))
    
    bars = ax.barh(range(len(ec_with_hits)), ec_with_hits['Total_hits'], 
                   color='#3498db', alpha=0.8)
    
    ax.set_yticks(range(len(ec_with_hits)))
    ax.set_yticklabels(ec_with_hits['EC_number'], fontsize=10)
    ax.set_xlabel('Number of Hits', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('Total Hits per EC Number', fontsize=14, weight='bold', pad=20)
    
    # Add value labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + max(ec_with_hits['Total_hits']) * 0.01, 
                bar.get_y() + bar.get_height()/2,
                f'{int(width)}',
                va='center', fontsize=9)
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_unique_proteins(ec_results, output_file='plots/04_unique_proteins.png'):
    """Create a bar chart showing unique proteins per EC number."""
    print(f"Creating unique proteins plot: {output_file}")
    
    # Filter to only EC numbers with hits
    ec_with_hits = ec_results[ec_results['Unique_proteins_with_hits'] > 0].copy()
    
    if len(ec_with_hits) == 0:
        print("⚠ No EC numbers with hits, skipping plot")
        return
    
    ec_with_hits = ec_with_hits.sort_values('Unique_proteins_with_hits', ascending=True)
    
    fig, ax = plt.subplots(figsize=(12, max(6, len(ec_with_hits) * 0.3)))
    
    bars = ax.barh(range(len(ec_with_hits)), ec_with_hits['Unique_proteins_with_hits'], 
                   color='#9b59b6', alpha=0.8)
    
    ax.set_yticks(range(len(ec_with_hits)))
    ax.set_yticklabels(ec_with_hits['EC_number'], fontsize=10)
    ax.set_xlabel('Number of Unique Proteins', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('Unique Proteins with Hits per EC Number', fontsize=14, weight='bold', pad=20)
    
    # Add value labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + max(ec_with_hits['Unique_proteins_with_hits']) * 0.01, 
                bar.get_y() + bar.get_height()/2,
                f'{int(width)}',
                va='center', fontsize=9)
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_evalue_distribution(detailed_hits, output_file='plots/05_evalue_distribution.png'):
    """Create a histogram of E-value distribution."""
    print(f"Creating E-value distribution plot: {output_file}")
    
    if len(detailed_hits) == 0:
        print("⚠ No hits to plot, skipping")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Log-scale histogram
    log_evalues = -np.log10(detailed_hits['evalue'])
    ax1.hist(log_evalues, bins=50, color='#3498db', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('-log10(E-value)', fontsize=11, weight='bold')
    ax1.set_ylabel('Count', fontsize=11, weight='bold')
    ax1.set_title('E-value Distribution (Log Scale)', fontsize=12, weight='bold')
    ax1.axvline(x=5, color='red', linestyle='--', linewidth=2, label='E=1e-5 threshold')
    ax1.legend()
    
    # Box plot by EC number
    if 'EC_number' in detailed_hits.columns:
        ec_with_enough_hits = detailed_hits.groupby('EC_number').filter(lambda x: len(x) >= 3)
        
        if len(ec_with_enough_hits) > 0:
            ec_order = (ec_with_enough_hits.groupby('EC_number')['evalue']
                       .median().sort_values().index)
            
            ec_log_evalues = ec_with_enough_hits.copy()
            ec_log_evalues['log_evalue'] = -np.log10(ec_log_evalues['evalue'])
            
            sns.boxplot(data=ec_log_evalues, y='EC_number', x='log_evalue', 
                       order=ec_order, ax=ax2, hue='EC_number', palette='Set2', legend=False)
            ax2.set_xlabel('-log10(E-value)', fontsize=11, weight='bold')
            ax2.set_ylabel('EC Number', fontsize=11, weight='bold')
            ax2.set_title('E-value Distribution by EC Number', fontsize=12, weight='bold')
        else:
            ax2.text(0.5, 0.5, 'Not enough hits per EC\nfor box plot', 
                    ha='center', va='center', transform=ax2.transAxes, fontsize=12)
            ax2.set_xticks([])
            ax2.set_yticks([])
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_score_distribution(detailed_hits, output_file='plots/06_score_distribution.png'):
    """Create a scatter plot of scores vs E-values."""
    print(f"Creating score distribution plot: {output_file}")
    
    if len(detailed_hits) == 0:
        print("⚠ No hits to plot, skipping")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color by EC number if available
    if 'EC_number' in detailed_hits.columns:
        ec_numbers = detailed_hits['EC_number'].unique()
        colors = plt.cm.tab20(np.linspace(0, 1, len(ec_numbers)))
        color_map = dict(zip(ec_numbers, colors))
        
        for ec in ec_numbers:
            ec_data = detailed_hits[detailed_hits['EC_number'] == ec]
            ax.scatter(ec_data['score'], -np.log10(ec_data['evalue']), 
                      label=ec, alpha=0.6, s=50, color=color_map[ec])
        
        # Add legend if not too many EC numbers
        if len(ec_numbers) <= 15:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                     title='EC Number', fontsize=8)
    else:
        ax.scatter(detailed_hits['score'], -np.log10(detailed_hits['evalue']), 
                  alpha=0.6, s=50, color='#3498db')
    
    ax.set_xlabel('Score', fontsize=12, weight='bold')
    ax.set_ylabel('-log10(E-value)', fontsize=12, weight='bold')
    ax.set_title('Hit Score vs E-value', fontsize=14, weight='bold', pad=20)
    ax.axhline(y=5, color='red', linestyle='--', linewidth=2, alpha=0.5, label='E=1e-5')
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_pfam_heatmap(ec_results, detailed_hits, output_file='plots/07_pfam_heatmap.png'):
    """Create a heatmap showing which Pfam domains were found for each EC number."""
    print(f"Creating Pfam heatmap: {output_file}")
    
    if 'Pfam_ID' not in detailed_hits.columns or len(detailed_hits) == 0:
        print("⚠ Not enough data for heatmap, skipping")
        return
    
    # Create a pivot table: EC numbers vs Pfam IDs
    # Count number of hits for each combination
    pivot_data = detailed_hits.groupby(['EC_number', 'Pfam_ID']).size().reset_index(name='count')
    heatmap_data = pivot_data.pivot(index='EC_number', columns='Pfam_ID', values='count').fillna(0)
    
    if heatmap_data.empty or heatmap_data.shape[0] == 0:
        print("⚠ Not enough data for heatmap, skipping")
        return
    
    fig, ax = plt.subplots(figsize=(max(10, len(heatmap_data.columns) * 0.5), 
                                     max(8, len(heatmap_data.index) * 0.4)))
    
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                cbar_kws={'label': 'Number of Hits'}, ax=ax, linewidths=0.5)
    
    ax.set_xlabel('Pfam Domain', fontsize=12, weight='bold')
    ax.set_ylabel('EC Number', fontsize=12, weight='bold')
    ax.set_title('Pfam Domain Hits Heatmap', fontsize=14, weight='bold', pad=20)
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def create_summary_figure(ec_results, output_file='plots/00_summary_dashboard.png'):
    """Create a summary dashboard with multiple subplots."""
    print(f"Creating summary dashboard: {output_file}")
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Status pie chart
    ax1 = fig.add_subplot(gs[0, 0])
    status_counts = ec_results['Status'].value_counts()
    colors_map = {'FULLY_FOUND': '#2ecc71', 'PARTIALLY_FOUND': '#f39c12', 'NOT_FOUND': '#e74c3c'}
    plot_colors = [colors_map.get(s, '#95a5a6') for s in status_counts.index]
    ax1.pie(status_counts.values, labels=[s.replace('_', ' ').title() for s in status_counts.index],
            autopct='%1.1f%%', colors=plot_colors, startangle=90)
    ax1.set_title('EC Status Distribution', fontsize=11, weight='bold')
    
    # 2. Coverage histogram
    ax2 = fig.add_subplot(gs[0, 1:])
    ec_results['Coverage_%'] = (ec_results['Found_Pfam_domains'] / 
                                 ec_results['Total_Pfam_domains'] * 100)
    ax2.hist(ec_results['Coverage_%'], bins=20, color='#3498db', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Coverage (%)', fontsize=10)
    ax2.set_ylabel('Count', fontsize=10)
    ax2.set_title('Pfam Domain Coverage Distribution', fontsize=11, weight='bold')
    ax2.axvline(x=100, color='green', linestyle='--', linewidth=2, label='100% coverage')
    ax2.legend()
    
    # 3. Top EC numbers by hits
    ax3 = fig.add_subplot(gs[1, :])
    top_ec = ec_results.nlargest(10, 'Total_hits')
    bars = ax3.barh(range(len(top_ec)), top_ec['Total_hits'], color='#e74c3c', alpha=0.7)
    ax3.set_yticks(range(len(top_ec)))
    ax3.set_yticklabels(top_ec['EC_number'], fontsize=9)
    ax3.set_xlabel('Total Hits', fontsize=10)
    ax3.set_title('Top 10 EC Numbers by Hit Count', fontsize=11, weight='bold')
    for bar in bars:
        width = bar.get_width()
        ax3.text(width, bar.get_y() + bar.get_height()/2, f'{int(width)}',
                va='center', ha='left', fontsize=8)
    
    # 4. Summary statistics
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')
    
    stats_text = f"""
    SUMMARY STATISTICS
    
    Total EC Numbers Searched: {len(ec_results)}
    Fully Found: {len(ec_results[ec_results['Status'] == 'FULLY_FOUND'])}
    Partially Found: {len(ec_results[ec_results['Status'] == 'PARTIALLY_FOUND'])}
    Not Found: {len(ec_results[ec_results['Status'] == 'NOT_FOUND'])}
    
    Total Hits: {ec_results['Total_hits'].sum()}
    Unique Proteins with Hits: {ec_results['Unique_proteins_with_hits'].sum()}
    Average Coverage: {ec_results['Coverage_%'].mean():.1f}%
    """
    
    ax4.text(0.5, 0.5, stats_text, ha='center', va='center', 
            fontsize=12, family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    fig.suptitle('EC Number Search Results - Summary Dashboard', 
                fontsize=16, weight='bold', y=0.98)
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_pathway_completeness_radar(ec_results, output_file='plots/08_pathway_completeness.png'):
    """Create a radar chart showing pathway completeness metrics."""
    print(f"Creating pathway completeness radar: {output_file}")
    
    if len(ec_results) == 0:
        print("⚠ No data for radar chart, skipping")
        return
    
    # Calculate metrics
    total_ecs = len(ec_results)
    fully_found = len(ec_results[ec_results['Status'] == 'FULLY_FOUND'])
    partially_found = len(ec_results[ec_results['Status'] == 'PARTIALLY_FOUND'])
    avg_coverage = ec_results['Coverage_%'].mean()
    total_hits = ec_results['Total_hits'].sum()
    unique_proteins = ec_results['Unique_proteins_with_hits'].sum()
    
    # Normalize metrics to 0-100 scale
    metrics = {
        'Fully Detected\n(%)': (fully_found / total_ecs) * 100,
        'Partially Detected\n(%)': ((fully_found + partially_found) / total_ecs) * 100,
        'Avg Coverage\n(%)': avg_coverage,
        'Hit Density\n(hits/EC)': min((total_hits / total_ecs) / 10 * 100, 100),  # Scale by 10
        'Protein Diversity\n(proteins/EC)': min((unique_proteins / total_ecs) / 5 * 100, 100)  # Scale by 5
    }
    
    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    values = list(metrics.values())
    labels = list(metrics.keys())
    
    # Close the plot
    angles += angles[:1]
    values += values[:1]
    
    ax.plot(angles, values, 'o-', linewidth=2, color='#2ecc71', alpha=0.8)
    ax.fill(angles, values, alpha=0.25, color='#2ecc71')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])
    ax.grid(True)
    
    ax.set_title('Pathway Analysis Completeness Profile', fontsize=14, weight='bold', pad=30)
    
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_hit_quality_analysis(detailed_hits, output_file='plots/09_hit_quality.png'):
    """Create a comprehensive hit quality analysis with multiple subplots."""
    print(f"Creating hit quality analysis: {output_file}")
    
    if len(detailed_hits) == 0:
        print("⚠ No hits for quality analysis, skipping")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Hit Quality Analysis', fontsize=16, weight='bold')
    
    # 1. Score vs Coverage scatter
    if 'score' in detailed_hits.columns and 'alignment_coverage' in detailed_hits.columns:
        ax1.scatter(detailed_hits['score'], detailed_hits['alignment_coverage'], 
                   alpha=0.6, s=30, c='#3498db')
        ax1.set_xlabel('Hit Score', fontsize=11, weight='bold')
        ax1.set_ylabel('Alignment Coverage', fontsize=11, weight='bold')
        ax1.set_title('Score vs Alignment Coverage', fontsize=12, weight='bold')
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, 'Alignment coverage\ndata not available', 
                ha='center', va='center', transform=ax1.transAxes, fontsize=12)
    
    # 2. Hit length distribution
    if 'hit_length' in detailed_hits.columns:
        ax2.hist(detailed_hits['hit_length'], bins=30, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Hit Length (amino acids)', fontsize=11, weight='bold')
        ax2.set_ylabel('Count', fontsize=11, weight='bold')
        ax2.set_title('Hit Length Distribution', fontsize=12, weight='bold')
        ax2.axvline(detailed_hits['hit_length'].median(), color='orange', 
                   linestyle='--', linewidth=2, label=f"Median: {detailed_hits['hit_length'].median():.0f}")
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, 'Hit length\ndata not available', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
    
    # 3. E-value vs Score correlation
    if 'score' in detailed_hits.columns:
        ax3.scatter(detailed_hits['score'], -np.log10(detailed_hits['evalue']), 
                   alpha=0.6, s=30, c='#9b59b6')
        ax3.set_xlabel('Hit Score', fontsize=11, weight='bold')
        ax3.set_ylabel('-log10(E-value)', fontsize=11, weight='bold')
        ax3.set_title('Score vs E-value Correlation', fontsize=12, weight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Add correlation coefficient
        corr = np.corrcoef(detailed_hits['score'], -np.log10(detailed_hits['evalue']))[0, 1]
        ax3.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax3.transAxes, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 4. Top performing Pfam domains
    if 'Pfam_ID' in detailed_hits.columns:
        pfam_performance = detailed_hits.groupby('Pfam_ID').agg({
            'score': 'mean',
            'evalue': lambda x: -np.log10(x).mean()
        }).round(2)
        pfam_performance = pfam_performance.sort_values('score', ascending=False).head(10)
        
        bars = ax4.barh(range(len(pfam_performance)), pfam_performance['score'], 
                       color='#f39c12', alpha=0.8)
        ax4.set_yticks(range(len(pfam_performance)))
        ax4.set_yticklabels(pfam_performance.index, fontsize=9)
        ax4.set_xlabel('Average Score', fontsize=11, weight='bold')
        ax4.set_title('Top 10 Pfam Domains by Score', fontsize=12, weight='bold')
        
        # Add score labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax4.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{width:.1f}', va='center', fontsize=8)
    else:
        ax4.text(0.5, 0.5, 'Pfam ID\ndata not available', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def plot_comparative_analysis(ec_results, output_file='plots/10_comparative_analysis.png'):
    """Create comparative analysis plots showing relationships between metrics."""
    print(f"Creating comparative analysis: {output_file}")
    
    if len(ec_results) == 0:
        print("⚠ No data for comparative analysis, skipping")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Comparative Metrics Analysis', fontsize=16, weight='bold')
    
    # 1. Coverage vs Hits scatter
    colors = ['#2ecc71' if s == 'FULLY_FOUND' else '#f39c12' if s == 'PARTIALLY_FOUND' else '#e74c3c' 
              for s in ec_results['Status']]
    
    scatter = ax1.scatter(ec_results['Coverage_%'], ec_results['Total_hits'], 
                         c=colors, alpha=0.7, s=60)
    ax1.set_xlabel('Pfam Domain Coverage (%)', fontsize=11, weight='bold')
    ax1.set_ylabel('Total Hits', fontsize=11, weight='bold')
    ax1.set_title('Coverage vs Hit Count', fontsize=12, weight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    if len(ec_results) > 3:
        z = np.polyfit(ec_results['Coverage_%'], ec_results['Total_hits'], 1)
        p = np.poly1d(z)
        ax1.plot(ec_results['Coverage_%'], p(ec_results['Coverage_%']), 'r--', alpha=0.8)
    
    # 2. Domain complexity (Total domains vs Found domains)
    ax2.scatter(ec_results['Total_Pfam_domains'], ec_results['Found_Pfam_domains'], 
               c=colors, alpha=0.7, s=60)
    ax2.plot([0, ec_results['Total_Pfam_domains'].max()], 
             [0, ec_results['Total_Pfam_domains'].max()], 'r--', alpha=0.5, label='Perfect match')
    ax2.set_xlabel('Total Pfam Domains', fontsize=11, weight='bold')
    ax2.set_ylabel('Found Pfam Domains', fontsize=11, weight='bold')
    ax2.set_title('Domain Detection Efficiency', fontsize=12, weight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. EC number complexity distribution
    complexity_bins = [(1, 'Simple (1 domain)'), (2, 'Moderate (2 domains)'), 
                      (3, 'Complex (3 domains)'), (float('inf'), 'Very Complex (4+ domains)')]
    
    complexity_counts = []
    complexity_labels = []
    prev_val = 0
    
    for val, label in complexity_bins:
        if val == float('inf'):
            count = len(ec_results[ec_results['Total_Pfam_domains'] > prev_val])
        else:
            count = len(ec_results[ec_results['Total_Pfam_domains'] == val])
        complexity_counts.append(count)
        complexity_labels.append(f"{label}\n({count} ECs)")
        prev_val = val
    
    wedges, texts, autotexts = ax3.pie(complexity_counts, labels=complexity_labels, 
                                      autopct='%1.1f%%', startangle=90,
                                      colors=['#3498db', '#f39c12', '#e74c3c', '#9b59b6'])
    ax3.set_title('EC Number Complexity Distribution', fontsize=12, weight='bold')
    
    # 4. Performance matrix
    performance_data = ec_results.groupby('Status').agg({
        'Coverage_%': 'mean',
        'Total_hits': 'mean',
        'Unique_proteins_with_hits': 'mean'
    }).round(1)
    
    # Create a heatmap-style visualization
    metrics = ['Coverage_%', 'Total_hits', 'Unique_proteins_with_hits']
    statuses = performance_data.index.tolist()
    
    # Normalize data for heatmap (0-1 scale)
    normalized_data = performance_data.copy()
    for col in metrics:
        max_val = performance_data[col].max()
        if max_val > 0:
            normalized_data[col] = performance_data[col] / max_val
    
    im = ax4.imshow(normalized_data.T, cmap='RdYlGn', aspect='auto')
    ax4.set_xticks(range(len(statuses)))
    ax4.set_xticklabels([s.replace('_', ' ').title() for s in statuses], rotation=45)
    ax4.set_yticks(range(len(metrics)))
    ax4.set_yticklabels(['Avg Coverage (%)', 'Avg Hits', 'Avg Proteins'])
    ax4.set_title('Performance by Status', fontsize=12, weight='bold')
    
    # Add text annotations
    for i in range(len(metrics)):
        for j in range(len(statuses)):
            ax4.text(j, i, f'{performance_data.iloc[j, i]}', 
                    ha='center', va='center', fontsize=10, weight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"✓ Saved to {output_file}")


def main():
    # Create output directory
    Path('plots').mkdir(exist_ok=True)
    
    try:
        # Load results
        ec_results, detailed_hits = load_results()
        
        # Generate all plots
        print("\nGenerating visualizations...")
        print("=" * 80)
        
        create_summary_figure(ec_results)
        plot_ec_status_overview(ec_results)
        plot_pfam_coverage(ec_results)
        plot_hits_distribution(ec_results)
        plot_unique_proteins(ec_results)
        plot_evalue_distribution(detailed_hits)
        plot_score_distribution(detailed_hits)
        plot_pfam_heatmap(ec_results, detailed_hits)
        plot_pathway_completeness_radar(ec_results)
        plot_hit_quality_analysis(detailed_hits)
        plot_comparative_analysis(ec_results)
        
        print("\n" + "=" * 80)
        print("✓ All visualizations generated successfully!")
        print("\nOutput files in 'plots/' directory:")
        print("  00_summary_dashboard.png - Overview dashboard")
        print("  01_ec_status_overview.png - EC status pie chart")
        print("  02_pfam_coverage.png - Pfam domain coverage")
        print("  03_hits_distribution.png - Hits per EC number")
        print("  04_unique_proteins.png - Unique proteins per EC")
        print("  05_evalue_distribution.png - E-value distributions")
        print("  06_score_distribution.png - Score vs E-value scatter")
        print("  07_pfam_heatmap.png - Pfam domain heatmap")
        print("  08_pathway_completeness.png - Pathway completeness radar")
        print("  09_hit_quality.png - Hit quality analysis")
        print("  10_comparative_analysis.png - Comparative metrics analysis")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()