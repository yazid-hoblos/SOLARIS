#!/usr/bin/env python3
"""
CLI interface for pathway profiler tool.
"""

def setup_pathway_parser(parser):
    """Add pathway_profiler subcommands."""
    
    subparsers = parser.add_subparsers(dest='pathway_command')
    
    # Complete workflow
    workflow = subparsers.add_parser('workflow', 
                                   help='Run complete pathway analysis workflow')
    workflow.add_argument('--pathway', 
                         help='KEGG pathway ID (e.g., map00720) or search term (optional - will prompt if not provided)')
    workflow.add_argument('--module', 
                         help='KEGG module ID (e.g., M00001) for direct module extraction')
    workflow.add_argument('--genome', required=True,
                         help='Path to genome FASTA file')
    workflow.add_argument('--pfam-db', required=True,
                         help='Path to directory containing Pfam-A.hmm database file')
    workflow.add_argument('--output-dir', default='pathway_analysis_results',
                         help='Output directory for all results')
    workflow.add_argument('--evalue', type=float, default=1e-5,
                         help='E-value threshold for HMM search')
    workflow.add_argument('--visualize', action='store_true',
                         help='Generate KEGG pathway visualization')
    workflow.add_argument('--show-browser', action='store_true',
                         help='Show browser during visualization (default: headless mode)')
    workflow.add_argument('--plot', action='store_true',
                         help='Generate analysis plots and visualizations')
    workflow.add_argument('--interactive', action='store_true',
                         help='Force interactive pathway selection even if --pathway is provided')
    workflow.add_argument('--taxonomy', default='1117', #2 Bacteria
                         help='NCBI taxonomy ID for UniProt search (default: "2" for Bacteria)')
    workflow.add_argument('--reviewed-only', action='store_true',
                         help='Only retrieve reviewed (Swiss-Prot) entries from UniProt')
    
    # Extract EC
    extract = subparsers.add_parser('extract-ec', 
                                  help='Extract EC numbers from KEGG pathway')
    extract.add_argument('--pathway',
                        help='KEGG pathway ID or search term (optional - will prompt if not provided)')
    extract.add_argument('--module',
                        help='KEGG module ID (e.g., M00001) for direct module extraction')
    extract.add_argument('--output', default='pfam_ids.txt',
                        help='Output file for EC-Pfam mappings')
    extract.add_argument('--interactive', action='store_true',
                        help='Force interactive pathway selection even if --pathway is provided')
    extract.add_argument('--taxonomy', default='2',
                        help='NCBI taxonomy ID for UniProt search (default: "2" for Bacteria)')
    extract.add_argument('--reviewed-only', action='store_true',
                        help='Only retrieve reviewed (Swiss-Prot) entries from UniProt')
    
    # Get profiles
    profiles = subparsers.add_parser('get-profiles',
                                   help='Extract HMM profiles from Pfam database')
    profiles.add_argument('--input', required=True,
                         help='Input file with Pfam IDs')
    profiles.add_argument('--pfam-db', required=True,
                         help='Path to directory containing Pfam-A.hmm database file')
    profiles.add_argument('--output', default='selected_pfam.hmm',
                         help='Output HMM file')
    
    # Search
    search = subparsers.add_parser('search',
                                 help='Search genome using HMM profiles')
    search.add_argument('--hmm', required=True,
                       help='HMM profiles file')
    search.add_argument('--genome', required=True,
                       help='Genome FASTA file')
    search.add_argument('--output', default='hits.txt',
                       help='Output hits file')
    search.add_argument('--evalue', type=float, default=1e-5,
                       help='E-value threshold')
    
    # Analyze
    analyze = subparsers.add_parser('analyze',
                                  help='Analyze search results')
    analyze.add_argument('--hits', required=True,
                        help='HMM search hits file')
    analyze.add_argument('--input', required=True,
                        help='Original EC-Pfam mapping file')
    analyze.add_argument('--hmm', required=True,
                        help='HMM profiles file used for search')
    analyze.add_argument('--output-dir', default='results',
                        help='Output directory')
    
    # Visualize
    visualize = subparsers.add_parser('visualize',
                                    help='Generate KEGG pathway visualization')
    visualize.add_argument('--results', required=True,
                          help='EC results CSV file')
    visualize.add_argument('--pathway', default='map00720',
                          help='KEGG pathway ID for visualization')
    visualize.add_argument('--headless', action='store_true',
                          help='Run in headless mode')


def handle_pathway_mapper(args):
    """Handle pathway_mapper commands."""
    import os
    from pathlib import Path
    
    if args.pathway_command == 'workflow':
        run_complete_workflow(args)
    
    elif args.pathway_command == 'extract-ec':
        from .keggModuleDiscoverer import KEGGModuleDiscoverer
        from .uniprotHandler import UniProtHandler
        
        # Initialize tools
        discoverer = KEGGModuleDiscoverer(delay=0.1)
        uniprot_handler = UniProtHandler(taxonomy_id=args.taxonomy, reviewed_only=args.reviewed_only)
        
        # Handle pathway/module extraction
        if args.module:
            # Direct module ID provided
            entity_id = args.module
            if not entity_id.startswith('M'):
                entity_id = f'M{entity_id}'
            results = discoverer.extract_module_components(entity_id)
        elif args.interactive or not args.pathway:
            entity_result = discoverer.interactive_pathway_search()
            if not entity_result:
                print("No pathway selected. Exiting.")
                return
            # Extract the ID and type from the tuple (entity_id, entity_type)
            if isinstance(entity_result, tuple):
                entity_id, entity_type = entity_result
            else:
                entity_id = entity_result
                entity_type = 'pathway'  # default assumption
            
            # Handle modules and pathways differently
            if entity_type == 'module' or entity_id.startswith('M'):
                results = discoverer.extract_module_components(entity_id)
            else:
                results = discoverer.interactive_module_selection(entity_id)
        else:
            # Direct pathway ID provided
            entity_id = args.pathway
            # Add map prefix if not present
            if not entity_id.startswith(('map', 'ko')):
                entity_id = f'map{entity_id}'
            
            # For pathways, use interactive module selection to avoid extracting ALL EC numbers
            results = discoverer.interactive_module_selection(entity_id)
        
        if results and 'ec_numbers' in results:
            # Get UniProt data for EC numbers
            ec_data = uniprot_handler.process_ec_list(list(results['ec_numbers']))
            uniprot_handler.save_to_csv(ec_data, args.output)
            print(f"✓ Saved EC-Pfam mapping to {args.output}")
        else:
            print("No EC numbers found.")
    
    elif args.pathway_command == 'get-profiles':
        from .pfamHandler import PfamHandler
        pfam_handler = PfamHandler(args.pfam_db)
        success, pfam_versions = pfam_handler.run(args.input, output_hmm_file=args.output)
        if success:
            print(f"✅ HMM profiles extracted to {args.output}")
        else:
            print("❌ Failed to extract HMM profiles")
    
    elif args.pathway_command == 'search':
        from .hmmSearcher import HMMSearcher
        searcher = HMMSearcher(evalue_threshold=args.evalue)
        searcher.load_hmm_profiles(args.hmm)
        searcher.load_sequences(args.genome)
        searcher.run_search()
        searcher.save_hits_table(args.output)
        print(f"✅ Search results saved to {args.output}")
    
    elif args.pathway_command == 'analyze':
        from .mapping_analysis import (load_pfam_ec_mapping, load_hmm_hits, 
                                     parse_hmm_file, analyze_results,
                                     create_summary_report, create_csv_report,
                                     create_detailed_hits_report)
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Load data
        ec_pfam_df = load_pfam_ec_mapping(args.input)
        hits_df = load_hmm_hits(args.hits)
        name_to_id = parse_hmm_file(args.hmm)
        
        # Analyze
        ec_status, found_pfam_ids = analyze_results(ec_pfam_df, hits_df, name_to_id)
        
        # Generate reports
        create_summary_report(ec_status, str(output_dir / 'ec_summary.txt'))
        results_df = create_csv_report(ec_status, str(output_dir / 'ec_results.csv'))
        create_detailed_hits_report(ec_pfam_df, hits_df, str(output_dir / 'detailed_hits.csv'))
        
        print(f"✅ Analysis complete. Results saved to {output_dir}")
    
    elif args.pathway_command == 'visualize':
        from .kegg_visualization import main as viz_main
        import sys
        old_argv = sys.argv
        sys.argv = ['visualize', '--ec_file', args.results]
        if args.headless:
            sys.argv.append('--headless')
        try:
            viz_main()
        finally:
            sys.argv = old_argv


def run_complete_workflow(args):
    """Run the complete pathway analysis workflow."""
    import os
    from pathlib import Path
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"🚀 Starting complete pathway analysis workflow")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🧬 Genome: {args.genome}")
    print(f"🔬 Pathway: {args.pathway}")
    print("=" * 60)
    
    # Step 1: Extract EC numbers from pathway
    print("\n📋 Step 1: Extracting EC numbers from KEGG pathway...")
    ec_pfam_file = output_dir / "ec_pfam_mapping.txt"
    
    from .keggModuleDiscoverer import KEGGModuleDiscoverer
    from .uniprotHandler import UniProtHandler
    
    discoverer = KEGGModuleDiscoverer(delay=0.1)
    uniprot_handler = UniProtHandler(taxonomy_id=args.taxonomy, reviewed_only=args.reviewed_only)
    
    if args.module:
        # Direct module ID provided
        entity_id = args.module
        if not entity_id.startswith('M'):
            entity_id = f'M{entity_id}'
        results = discoverer.extract_module_components(entity_id)
    elif args.interactive or not args.pathway:
        entity_result = discoverer.interactive_pathway_search()
        if not entity_result:
            print("❌ No pathway selected. Exiting.")
            return
        # Extract the ID and type from the tuple (entity_id, entity_type)
        if isinstance(entity_result, tuple):
            entity_id, entity_type = entity_result
        else:
            entity_id = entity_result
            entity_type = 'pathway'  # default assumption
        
        # Handle modules and pathways differently
        if entity_type == 'module' or entity_id.startswith('M'):
            results = discoverer.extract_module_components(entity_id)
        else:
            results = discoverer.interactive_module_selection(entity_id)
    else:
        # Direct pathway ID provided
        entity_id = args.pathway
        # Add map prefix if not present
        if not entity_id.startswith(('map', 'ko')):
            entity_id = f'map{entity_id}'
        
        # For pathways, use interactive module selection to avoid extracting ALL EC numbers
        results = discoverer.interactive_module_selection(entity_id)
    
    if not results or 'ec_numbers' not in results:
        print("❌ No EC numbers found in pathway.")
        return
    
    # Get UniProt data
    ec_data = uniprot_handler.process_ec_list(list(results['ec_numbers']))
    uniprot_handler.save_to_csv(ec_data, str(ec_pfam_file))
    print(f"✅ Saved {len(results['ec_numbers'])} EC numbers to {ec_pfam_file}")
    
    # Step 2: Extract HMM profiles
    print("\n🧪 Step 2: Extracting HMM profiles...")
    hmm_file = output_dir / "selected_pfam.hmm"
    
    from .pfamHandler import PfamHandler
    pfam_handler = PfamHandler(args.pfam_db)
    success, pfam_versions = pfam_handler.run(str(ec_pfam_file), output_hmm_file=str(hmm_file))
    if success:
        print(f"✅ HMM profiles saved to {hmm_file}")
    else:
        print("❌ Failed to extract HMM profiles")
        return
    
    # Step 3: Search genome
    print("\n🔍 Step 3: Searching genome with HMM profiles...")
    hits_file = output_dir / "hits_table.txt"
    
    from .hmmSearcher import HMMSearcher
    searcher = HMMSearcher(evalue_threshold=args.evalue)
    searcher.load_hmm_profiles(str(hmm_file))
    searcher.load_sequences(args.genome)
    searcher.run_search()
    searcher.save_hits_table(str(hits_file))
    print(f"✅ Search results saved to {hits_file}")
    
    # Step 4: Analyze results
    print("\n📊 Step 4: Analyzing results...")
    from .mapping_analysis import (load_pfam_ec_mapping, load_hmm_hits, 
                                 parse_hmm_file, analyze_results,
                                 create_summary_report, create_csv_report,
                                 create_detailed_hits_report)
    
    # Load data
    ec_pfam_df = load_pfam_ec_mapping(str(ec_pfam_file))
    hits_df = load_hmm_hits(str(hits_file))
    name_to_id = parse_hmm_file(str(hmm_file))
    
    # Analyze
    ec_status, found_pfam_ids = analyze_results(ec_pfam_df, hits_df, name_to_id)
    
    # Generate reports
    results_file = output_dir / "ec_results.csv"
    summary_file = output_dir / "ec_summary.txt"
    detailed_file = output_dir / "detailed_hits.csv"
    
    create_summary_report(ec_status, str(summary_file))
    results_df = create_csv_report(ec_status, str(results_file))
    create_detailed_hits_report(ec_pfam_df, hits_df, str(detailed_file))
    
    print(f"✅ Analysis results saved to {results_file}")
    print(f"✅ Summary report saved to {summary_file}")
    print(f"✅ Detailed hits saved to {detailed_file}")
    
    # Step 5: Visualization (optional)
    if args.visualize and results_file.exists():
        print("\n🎨 Step 5: Generating KEGG pathway visualization...")
        from .kegg_visualization import main as viz_main
        import sys
        old_argv = sys.argv
        sys.argv = ['visualize', '--ec_file', str(results_file)]
        if not args.show_browser:
            sys.argv.append('--headless')
        try:
            viz_main()
        finally:
            sys.argv = old_argv
        print("✅ Visualization complete")
    
    # Step 6: Generate plots (optional)
    if args.plot and results_file.exists() and detailed_file.exists():
        print("\n📊 Step 6: Generating analysis plots...")
        from . import plot_findings
        
        # Create plots directory in output directory
        plots_dir = output_dir / 'plots'
        plots_dir.mkdir(exist_ok=True)
        
        try:
            # Load the data
            import pandas as pd
            ec_results = pd.read_csv(str(results_file))
            detailed_hits = pd.read_csv(str(detailed_file))
            
            print(f"✓ Loaded {len(ec_results)} EC numbers and {len(detailed_hits)} hits")
            
            # Generate all plots with custom output directory
            plot_functions = [
                (plot_findings.create_summary_figure, 'summary_dashboard.png'),
                (plot_findings.plot_ec_status_overview, 'ec_status_overview.png'),
                (plot_findings.plot_pfam_coverage, 'pfam_coverage.png'),
                (plot_findings.plot_hits_distribution, 'hits_distribution.png'),
                (plot_findings.plot_unique_proteins, 'unique_proteins.png'),
                (plot_findings.plot_evalue_distribution, 'evalue_distribution.png'),
                (plot_findings.plot_score_distribution, 'score_distribution.png'),
                (plot_findings.plot_pfam_heatmap, 'pfam_heatmap.png')
            ]
            
            for plot_func, filename in plot_functions:
                try:
                    if plot_func == plot_findings.plot_pfam_heatmap:
                        plot_func(ec_results, detailed_hits, str(plots_dir / filename))
                    elif plot_func in [plot_findings.plot_evalue_distribution, plot_findings.plot_score_distribution]:
                        plot_func(detailed_hits, str(plots_dir / filename))
                    else:
                        plot_func(ec_results, str(plots_dir / filename))
                    print(f"✓ Generated {filename}")
                except Exception as e:
                    print(f"⚠ Warning: Could not generate {filename}: {e}")
            
            print(f"✅ Analysis plots saved to {plots_dir}")
            
        except Exception as e:
            print(f"❌ Failed to generate plots: {e}")
    
    print("\n🎉 Workflow completed successfully!")
    print(f"📁 All results saved in: {output_dir.absolute()}")
    print("\nGenerated files:")
    for file in output_dir.iterdir():
        if file.is_file():
            print(f"  - {file.name}")
        elif file.is_dir() and file.name == 'plots':
            print(f"  - {file.name}/ (visualization plots)")
            for plot_file in file.iterdir():
                if plot_file.is_file():
                    print(f"    - {plot_file.name}")

def _run_workflow_step(step_name, func, *args, **kwargs):
    """Helper function to run workflow steps with error handling."""
    print(f"\n{step_name}...")
    try:
        result = func(*args, **kwargs)
        print(f"✅ {step_name} completed")
        return result
    except Exception as e:
        print(f"❌ {step_name} failed: {e}")
        raise