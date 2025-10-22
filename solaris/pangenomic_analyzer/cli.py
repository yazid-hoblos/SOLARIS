#!/usr/bin/env python3
"""
Pangenomic Analyzer CLI - Command-line interface for pangenomic analysis.
"""

import argparse
import sys
import logging
import warnings
from pathlib import Path
from typing import List, Optional

# Suppress numpy warnings about subnormal values
warnings.filterwarnings("ignore", message="The value of the smallest subnormal.*is zero", category=UserWarning)

# Import local modules
from .strain_manager import StrainManager
from .batch_analyzer import BatchAnalyzer
from .pathway_analyzer import PathwayAnalyzer
from .visualization_manager import VisualizationManager

def setup_pangenomic_parser(parent_parser):
    """Set up the pangenomic analyzer argument parser."""
    parser = parent_parser.add_parser('pangenomic_analyzer', 
                                     help='Pangenomic analysis tools')
    
    # Global arguments
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('-o', '--output-dir', default='results',
                       help='Output directory for results (default: results)')
    
    subparsers = parser.add_subparsers(dest='pangenomic_command', 
                                      help='Available commands')
    
    # Complete analysis workflow
    complete_parser = subparsers.add_parser('complete', 
                                           help='Run complete pangenomic analysis workflow')
    complete_parser.add_argument('--genomes-dir', '--genome-dir', required=True,
                                help='Directory containing genome FASTA files')
    complete_parser.add_argument('--hmm-file', '--hmm-profiles', required=True,
                                help='HMM profiles file (.hmm)')
    complete_parser.add_argument('--ec-pfam-mapping',
                                help='EC-Pfam mapping file (pfam_ids.txt) - optional')
    complete_parser.add_argument('--target-ecs',
                                help='File with target EC numbers (optional)')
    complete_parser.add_argument('--output-dir', default='results',
                                help='Output directory (default: results)')
    complete_parser.add_argument('--plot-dir', default='plots',
                                help='Plot output directory (default: plots)')
    complete_parser.add_argument('--batch-size', type=int, default=10,
                                help='Batch size for processing (default: 10)')
    complete_parser.add_argument('--max-workers', type=int, default=4,
                                help='Maximum number of parallel workers (default: 4)')
    complete_parser.add_argument('--evalue', type=float, default=1e-5,
                                help='E-value threshold (default: 1e-5)')
    complete_parser.add_argument('--parallel', action='store_true',
                                help='Use parallel processing')
    complete_parser.add_argument('--plot', action='store_true',
                                help='Generate visualization plots')
    complete_parser.add_argument('--similarity-analysis', action='store_true',
                                help='Include strain similarity analysis')
    complete_parser.set_defaults(func=run_complete_analysis)
    
    # HMM analysis only
    hmm_parser = subparsers.add_parser('hmm-analysis', 
                                      help='Run HMM analysis only')
    hmm_parser.add_argument('--genomes-dir', '--genome-dir', required=True,
                           help='Directory containing genome FASTA files')
    hmm_parser.add_argument('--hmm-file', '--hmm-profiles', required=True,
                           help='HMM profiles file (.hmm)')
    hmm_parser.add_argument('--ec-pfam-mapping',
                           help='EC-Pfam mapping file (pfam_ids.txt) - optional')
    hmm_parser.add_argument('--output-dir', default='results',
                           help='Output directory (default: results)')
    hmm_parser.add_argument('--batch-size', type=int, default=10,
                           help='Batch size for processing (default: 10)')
    hmm_parser.add_argument('--max-workers', type=int, default=4,
                           help='Maximum number of parallel workers (default: 4)')
    hmm_parser.add_argument('--evalue', type=float, default=1e-5,
                           help='E-value threshold (default: 1e-5)')
    hmm_parser.add_argument('--parallel', action='store_true',
                           help='Use parallel processing')
    hmm_parser.set_defaults(func=run_hmm_analysis)
    
    # Pathway analysis only
    pathways_parser = subparsers.add_parser('pathway-analysis', 
                                           help='Run pathway analysis only')
    pathways_parser.add_argument('--results-dir', required=True,
                                help='Directory with HMM analysis results')
    pathways_parser.add_argument('--target-ecs',
                                help='File with target EC numbers (optional)')
    pathways_parser.add_argument('--output-dir', default='results',
                                help='Output directory (default: results)')
    pathways_parser.add_argument('--plot-dir', default='plots',
                                help='Plot output directory (default: plots)')
    pathways_parser.add_argument('--plot', action='store_true',
                                help='Generate visualization plots')
    pathways_parser.add_argument('--similarity-analysis', action='store_true',
                                help='Include strain similarity analysis')
    pathways_parser.set_defaults(func=run_pathway_analysis)


def handle_pangenomic_analyzer(args):
    """Handle pangenomic analyzer commands."""
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)


def run_complete_analysis(args) -> int:
    """
    Run complete pangenomic analysis workflow.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting complete pangenomic analysis workflow...")
        
        # Initialize managers
        strain_manager = StrainManager()
        batch_output_dir = str(Path(args.output_dir) / "batch")
        batch_analyzer = BatchAnalyzer(args.hmm_file, output_dir=batch_output_dir)
        pathway_analyzer = PathwayAnalyzer()
        visualization_manager = VisualizationManager(args.plot_dir)
        
        # Step 1: Load and filter strains
        logger.info("Step 1: Loading and filtering strains...")
        all_strains = strain_manager.load_strains(args.genomes_dir)
        
        if args.strain_list:
            target_strains = []
            with open(args.strain_list, 'r') as f:
                target_strains = [line.strip() for line in f if line.strip()]
            strains_df = strain_manager.filter_strains(all_strains, target_strains)
            # Update the strain manager's internal state with filtered data
            strain_manager.strains_df = strains_df
        else:
            strains_df = all_strains
        
        logger.info(f"Selected {len(strains_df)} strains for analysis")
        
        # Step 2: Prepare batches
        logger.info("Step 2: Preparing strain batches...")
        batches = strain_manager.create_strain_batches(args.batch_size)
        logger.info(f"Created {len(batches)} batches for processing")
        
        # Step 3: Run HMM analysis
        logger.info("Step 3: Running HMM analysis on all strains...")
        all_results = []
        
        for i, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {i}/{len(batches)} ({len(batch)} strains)...")
            
            if args.parallel:
                # batch is already a DataFrame
                batch_results = batch_analyzer.batch_analyze_strains(
                    batch, pfam_ec_mapping_file=args.ec_pfam_mapping, max_workers=args.max_workers
                )
            else:
                batch_results = []
                # Convert DataFrame rows to dictionaries for single strain processing
                for _, row in batch.iterrows():
                    strain_data = {
                        'strain': row['strain'],
                        'file': row['genome_file'],  # Use 'file' key as expected by analyze_single_strain
                        'accession': row['accession']
                    }
                    result = batch_analyzer.analyze_single_strain(strain_data, args.ec_pfam_mapping)
                    batch_results.append(result)
            
            all_results.extend(batch_results)
        
        logger.info(f"Completed HMM analysis for all {len(all_results)} strains")
        
        # Step 4: Analyze pathway completeness
        logger.info("Step 4: Analyzing pathway completeness...")
        ec_coverage = pathway_analyzer.analyze_ec_coverage(batch_output_dir, args.target_ecs)
        
        # Step 5: Save results
        logger.info("Step 5: Saving analysis results...")
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        comparison_matrix = pathway_analyzer.create_comparison_matrix_from_files(batch_output_dir)
        
        # Save comparison matrix
        matrix_file = output_dir / "comparison_matrix.csv"
        comparison_matrix.to_csv(matrix_file, index=False)
        logger.info(f"✓ Comparison matrix saved to {matrix_file}")
        
        strain_rankings = pathway_analyzer.rank_strains_by_completeness_from_matrix(comparison_matrix)
        
        # Save main results
        comparison_matrix.to_csv(output_dir / "comparison_matrix.csv", index=False)
        strain_rankings.to_csv(output_dir / "strain_rankings.csv", index=False)
        
        # Save detailed results
        import pandas as pd
        detailed_results = pd.DataFrame(all_results)
        detailed_results.to_csv(output_dir / "detailed_hmm_results.csv", index=False)
        
        logger.info(f"✓ Results saved to {output_dir}/")
        
        # Step 6: Generate visualizations
        if args.plot:
            logger.info("Step 6: Generating visualizations...")
            
            # Generate similarity analysis if requested
            similarity_df = None
            if args.similarity_analysis:
                similarity_df = pathway_analyzer.calculate_strain_similarity(ec_coverage)
                similarity_df.to_csv(output_dir / "strain_similarity.csv", index=False)
            
            # Generate all plots
            plot_files = visualization_manager.generate_all_plots(
                strain_rankings, comparison_matrix, similarity_df
            )
            
            logger.info(f"✓ Generated {len(plot_files)} visualization plots")
            for plot_file in plot_files:
                logger.info(f"  - {plot_file}")
        
        logger.info("✅ Complete pangenomic analysis workflow finished successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error in complete analysis workflow: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_strain_analysis(args) -> int:
    """
    Analyze strains and create batches.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Running strain analysis...")
        
        strain_manager = StrainManager()
        
        # Load strains
        strains_df = strain_manager.load_strains(args.genomes_dir)
        logger.info(f"Loaded {len(strains_df)} strains")
        
        # Filter if needed
        if args.strain_list:
            target_strains = []
            with open(args.strain_list, 'r') as f:
                target_strains = [line.strip() for line in f if line.strip()]
            strains_df = strain_manager.filter_strains(strains_df, target_strains)
            logger.info(f"Filtered to {len(strains_df)} target strains")
        
        # Create batches
        batches = strain_manager.create_strain_batches(strains_df, args.batch_size)
        logger.info(f"Created {len(batches)} batches")
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        strains_df.to_csv(output_dir / "strain_analysis.csv", index=False)
        
        # Save batch information
        batch_info = []
        for i, batch in enumerate(batches):
            for strain_data in batch:
                batch_info.append({
                    'batch_id': i + 1,
                    'strain': strain_data['strain'],
                    'genome_file': strain_data['genome_file']
                })
        
        import pandas as pd
        batch_df = pd.DataFrame(batch_info)
        batch_df.to_csv(output_dir / "batch_information.csv", index=False)
        
        logger.info(f"✓ Strain analysis results saved to {output_dir}/")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error in strain analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_hmm_analysis(args) -> int:
    """
    Run HMM analysis on specified strains.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Running HMM analysis...")
        
        batch_analyzer = BatchAnalyzer(args.hmm_file)
        
        # Load target strains
        strain_manager = StrainManager()
        strains_df = strain_manager.load_strains(args.genomes_dir)
        
        if args.strain_list:
            target_strains = []
            with open(args.strain_list, 'r') as f:
                target_strains = [line.strip() for line in f if line.strip()]
            strains_df = strain_manager.filter_strains(strains_df, target_strains)
        
        # Create strain data format
        strain_data_list = []
        for _, row in strains_df.iterrows():
            strain_data_list.append({
                'strain': row['strain'],
                'genome_file': row['genome_file']
            })
        
        # Run analysis
        if args.parallel:
            # Convert to DataFrame format expected by batch_analyzer
            import pandas as pd
            strains_df = pd.DataFrame(strain_data_list)
            results = batch_analyzer.batch_analyze_strains(
                strains_df, pfam_ec_mapping_file=args.ec_pfam_mapping, max_workers=args.max_workers
            )
        else:
            results = []
            for strain_data in strain_data_list:
                result = batch_analyzer.analyze_single_strain(strain_data, args.ec_pfam_mapping)
                results.append(result)
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import pandas as pd
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_dir / "hmm_analysis_results.csv", index=False)
        
        logger.info(f"✓ HMM analysis completed for {len(results)} strains")
        logger.info(f"✓ Results saved to {output_dir}/hmm_analysis_results.csv")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error in HMM analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_pathway_analysis(args) -> int:
    """
    Run pathway completeness analysis.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Running pathway analysis...")
        
        pathway_analyzer = PathwayAnalyzer()
        
        # Load HMM results
        import pandas as pd
        hmm_results_df = pd.read_csv(args.hmm_results)
        hmm_results = hmm_results_df.to_dict('records')
        
        # Analyze EC coverage
        ec_coverage = pathway_analyzer.analyze_ec_coverage(hmm_results, args.target_ecs)
        
        # Create matrices and rankings
        comparison_matrix = pathway_analyzer.create_comparison_matrix(ec_coverage)
        strain_rankings = pathway_analyzer.rank_strains_by_completeness(ec_coverage)
        
        # Generate similarity analysis if requested
        similarity_df = None
        if args.similarity_analysis:
            similarity_df = pathway_analyzer.calculate_strain_similarity(ec_coverage)
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        comparison_matrix.to_csv(output_dir / "comparison_matrix.csv", index=False)
        strain_rankings.to_csv(output_dir / "strain_rankings.csv", index=False)
        
        if similarity_df is not None:
            similarity_df.to_csv(output_dir / "strain_similarity.csv", index=False)
        
        # Generate plots if requested
        if args.plot:
            visualization_manager = VisualizationManager(args.plot_dir)
            plot_files = visualization_manager.generate_all_plots(
                strain_rankings, comparison_matrix, similarity_df
            )
            
            logger.info(f"✓ Generated {len(plot_files)} visualization plots")
        
        logger.info(f"✓ Pathway analysis completed")
        logger.info(f"✓ Results saved to {output_dir}/")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error in pathway analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def setup_pangenomic_parser(parser):
    """Setup parser for pangenomic analyzer when called from main CLI."""
    
    # Global arguments
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('-o', '--output-dir', default='results',
                       help='Output directory for results (default: results)')
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest='subcommand', help='Available commands')
    
    # Complete workflow command
    complete_parser = subparsers.add_parser('complete', 
                                          help='Run complete pangenomic analysis workflow')
    complete_parser.add_argument('--genomes-dir', required=True,
                               help='Directory containing genome files (.faa)')
    complete_parser.add_argument('--hmm-file', required=True,
                               help='Path to HMM profile file')
    complete_parser.add_argument('--target-ecs', required=True,
                               help='File containing target EC numbers (one per line)')
    complete_parser.add_argument('--ec-pfam-mapping', required=True,
                               help='Path to EC-Pfam mapping file (tab-separated)')
    complete_parser.add_argument('--strain-list',
                               help='File containing target strain names (one per line)')
    complete_parser.add_argument('--batch-size', type=int, default=10,
                               help='Number of strains per batch (default: 10)')
    complete_parser.add_argument('--parallel', action='store_true',
                               help='Enable parallel processing')
    complete_parser.add_argument('--max-workers', type=int, default=4,
                               help='Maximum number of parallel workers (default: 4)')
    complete_parser.add_argument('--plot', action='store_true',
                               help='Generate visualization plots')
    complete_parser.add_argument('--plot-dir', default='results/plots',
                               help='Directory for saving plots (default: results/plots)')
    complete_parser.add_argument('--similarity-analysis', action='store_true',
                               help='Include strain similarity analysis')
    complete_parser.set_defaults(func=run_complete_analysis)
    
    # Strain analysis command
    strains_parser = subparsers.add_parser('strains',
                                         help='Analyze strains and create batches')
    strains_parser.add_argument('--genomes-dir', required=True,
                              help='Directory containing genome files (.faa)')
    strains_parser.add_argument('--strain-list',
                              help='File containing target strain names (one per line)')
    strains_parser.add_argument('--batch-size', type=int, default=10,
                              help='Number of strains per batch (default: 10)')
    strains_parser.set_defaults(func=run_strain_analysis)
    
    # HMM analysis command
    hmm_parser = subparsers.add_parser('hmm',
                                     help='Run HMM analysis on strains')
    hmm_parser.add_argument('--genomes-dir', required=True,
                          help='Directory containing genome files (.faa)')
    hmm_parser.add_argument('--hmm-file', required=True,
                          help='Path to HMM profile file')
    hmm_parser.add_argument('--ec-pfam-mapping',
                          help='Path to EC-Pfam mapping file (tab-separated)')
    hmm_parser.add_argument('--strain-list',
                          help='File containing target strain names (one per line)')
    hmm_parser.add_argument('--parallel', action='store_true',
                          help='Enable parallel processing')
    hmm_parser.add_argument('--max-workers', type=int, default=4,
                          help='Maximum number of parallel workers (default: 4)')
    hmm_parser.set_defaults(func=run_hmm_analysis)
    
    # Pathway analysis command
    pathways_parser = subparsers.add_parser('pathways',
                                          help='Analyze pathway completeness')
    pathways_parser.add_argument('--hmm-results', required=True,
                               help='CSV file with HMM analysis results')
    pathways_parser.add_argument('--target-ecs', required=True,
                               help='File containing target EC numbers (one per line)')
    pathways_parser.add_argument('--plot', action='store_true',
                               help='Generate visualization plots')
    pathways_parser.add_argument('--plot-dir', default='results/plots',
                               help='Directory for saving plots (default: results/plots)')
    pathways_parser.add_argument('--similarity-analysis', action='store_true',
                               help='Include strain similarity analysis')
    pathways_parser.set_defaults(func=run_pathway_analysis)


def run_hmm_analysis(args):
    """Step 2: Run HMM analysis (like tmp/run_comparison.py)."""
    
    logger.info("🔍 Step 2: Running HMM analysis on all strains")
    logger.info(f"Genome directory: {args.genome_dir}")
    logger.info(f"HMM profiles: {args.hmm_profiles}")
    logger.info(f"Pfam-EC mapping: {args.pfam_ids_file}")
    
    try:
        # Discover genomes
        strain_manager = StrainManager()
        strains_df = strain_manager.discover_genomes(args.genome_dir)
        
        if strains_df.empty:
            logger.error("No genome files found!")
            return 1
        
        logger.info(f"✓ Found {len(strains_df)} genome files")
        
        # Initialize batch analyzer
        batch_analyzer = BatchAnalyzer(
            hmm_profiles_path=args.hmm_profiles,
            output_dir=args.output_dir,
            evalue_threshold=args.evalue
        )
        
        # Process strains
        logger.info(f"Running HMM search on {len(strains_df)} strains...")
        logger.info("="*80)
        
        results = []
        for idx, row in strains_df.iterrows():
            strain_info = {
                'strain': row['strain'],
                'file': row['genome_file'],
                'accession': row['accession']
            }
            
            logger.info(f"[{idx+1}/{len(strains_df)}] Processing {strain_info['strain']}")
            result = batch_analyzer.analyze_single_strain(strain_info, args.pfam_ids_file)
            results.append(result)
        
        logger.info("🎉 HMM analysis completed successfully!")
        logger.info(f"📊 Results summary:")
        logger.info(f"  - Analyzed {len(strains_df)} strains")
        logger.info(f"  - Results saved to {args.output_dir}/")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error in HMM analysis: {e}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return 1


def run_comparison_matrix(args):
    """Step 3: Create comparison matrix (like tmp/rank_strains.py)."""
    
    logger.info("📊 Step 3: Creating pangenome comparison matrix")
    logger.info(f"Results directory: {args.results_dir}")
    
    try:
        from .pathway_analyzer import PathwayAnalyzer
        
        analyzer = PathwayAnalyzer()
        
        # Create comparison matrix from individual EC results
        comparison_matrix = analyzer.create_comparison_matrix_from_files(args.results_dir)
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        matrix_file = output_dir / "comparison_matrix.csv"
        comparison_matrix.to_csv(matrix_file, index=False)
        
        logger.info(f"✓ Comparison matrix saved to {matrix_file}")
        logger.info(f"📊 Matrix dimensions: {comparison_matrix.shape}")
        
        # Generate plots if requested
        if args.plot or args.clustered_plots:
            logger.info("Generating visualizations...")
            from .visualization_manager import VisualizationManager
            
            viz_manager = VisualizationManager(str(output_dir))
            
            if args.plot:
                plot_files = viz_manager.generate_comparison_plots(comparison_matrix)
                logger.info(f"✓ Generated {len(plot_files)} standard plots")
                for plot_file in plot_files:
                    logger.info(f"  - {plot_file}")
            
            if args.clustered_plots:
                clustered_plot_files = viz_manager.generate_clustered_plots(comparison_matrix)
                logger.info(f"✓ Generated {len(clustered_plot_files)} clustered plots")
                for plot_file in clustered_plot_files:
                    logger.info(f"  - {plot_file}")
        
        logger.info("🎉 Comparison matrix analysis completed!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error creating comparison matrix: {e}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return 1


def handle_pangenomic_analyzer(args):
    """Handle pangenomic analyzer commands when called from main CLI."""
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Execute subcommand
    if args.subcommand is None:
        logger.error("No subcommand specified. Use 'solaris pangenomic_analyzer -h' for help.")
        return 1
    
    return args.func(args)


def main():
    """Main CLI entry point for standalone usage."""
    parser = argparse.ArgumentParser(
        description="Pangenomic Analyzer - Analyze pathway completeness across multiple strains",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete analysis workflow
  python -m solaris.pangenomic_analyzer complete --genomes-dir ./genomes --hmm-file pfam.hmm --target-ecs ec_numbers.txt --plot

  # Analyze strains only
  python -m solaris.pangenomic_analyzer strains --genomes-dir ./genomes --batch-size 10

  # Run HMM analysis with parallel processing
  python -m solaris.pangenomic_analyzer hmm --genomes-dir ./genomes --hmm-file pfam.hmm --parallel --max-workers 4

  # Analyze pathway completeness from existing HMM results
  python -m solaris.pangenomic_analyzer pathways --hmm-results results.csv --target-ecs ec_numbers.txt --plot
        """
    )
    
    # Setup the parser
    setup_pangenomic_parser(parser)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging level
    if hasattr(args, 'verbose') and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Execute subcommand
    if not hasattr(args, 'subcommand') or args.subcommand is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
