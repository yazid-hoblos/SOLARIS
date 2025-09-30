def setup_pathway_parser(parser):
    """Add pathway_mapper subcommands."""
    
    subparsers = parser.add_subparsers(dest='pathway_command')
    
    # Extract EC
    extract = subparsers.add_parser('extract-ec')
    extract.add_argument('--pathway', required=True)
    extract.add_argument('--output', default='pfam_ids.txt')
    
    # Get profiles
    profiles = subparsers.add_parser('get-profiles')
    profiles.add_argument('--input', required=True)
    profiles.add_argument('--pfam-db', required=True)
    profiles.add_argument('--output', default='selected_pfam.hmm')
    
    # Search
    search = subparsers.add_parser('search')
    search.add_argument('--hmm', required=True)
    search.add_argument('--genome', required=True)
    search.add_argument('--output', default='hits.txt')
    search.add_argument('--evalue', type=float, default=1e-5)
    
    # Analyze
    analyze = subparsers.add_parser('analyze')
    analyze.add_argument('--hits', required=True)
    analyze.add_argument('--input', required=True)
    analyze.add_argument('--output-dir', default='results')
    
    # Visualize
    visualize = subparsers.add_parser('visualize')
    visualize.add_argument('--results', required=True)
    visualize.add_argument('--pathway', default='map00720')
    visualize.add_argument('--headless', action='store_true')


def handle_pathway_mapper(args):
    """Handle pathway_mapper commands."""
    
    if args.pathway_command == 'extract-ec':
        from .extract_ec_numbers import extract_ec_from_kegg
        extract_ec_from_kegg(args.pathway, args.output)
    
    elif args.pathway_command == 'get-profiles':
        from .profiles_extraction import extract_profiles
        extract_profiles(args.input, args.pfam_db, args.output)
    
    elif args.pathway_command == 'search':
        from .run_pyhmmer import run_hmmsearch
        run_hmmsearch(args.hmm, args.genome, args.output, args.evalue)
    
    elif args.pathway_command == 'analyze':
        from .mapping_analysis import analyze_results
        analyze_results(args.hits, args.input, args.output_dir)
    
    elif args.pathway_command == 'visualize':
        from .kegg_visualization import visualize_kegg
        visualize_kegg(args.results, args.pathway, args.headless)