#!/usr/bin/env python3
"""
Solaris - Toolkit for heterologous pathway transfer for metabolic engineering
"""

import argparse
import sys
import warnings

# Suppress numpy warnings about subnormal values
warnings.filterwarnings("ignore", message="The value of the smallest subnormal.*is zero", category=UserWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

def main():
    parser = argparse.ArgumentParser(
        prog='solaris',
        description='SOLARIS: Toolkit for heterologous pathway transfer for metabolic engineering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Tools:
  pathway_profiler      EC-based pathway profiling and visualization
  pangenomic_analyzer   Comprehensive pangenomic analysis across multiple strains

For more information, visit: https://gitlab.igem.org/2025/software-tools/evry-paris-saclay/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available tools')
    
    # Pathway Profiler subcommand
    pathway_parser = subparsers.add_parser(
        'pathway_profiler',
        help='EC-based pathway profiling and visualization'
    )
    # Import pathway_profiler CLI and add its arguments
    from solaris.pathway_profiler.cli import setup_pathway_parser
    setup_pathway_parser(pathway_parser)
    
    # Pangenomic Analyzer subcommand
    pangenomic_parser = subparsers.add_parser(
        'pangenomic_analyzer', 
        help='Comprehensive pangenomic analysis across multiple strains'
    )
    # Import pangenomic_analyzer CLI and add its arguments
    from solaris.pangenomic_analyzer.cli import setup_pangenomic_parser
    setup_pangenomic_parser(pangenomic_parser)
    
    # Add other subcommands here
    # feature3_parser = subparsers.add_parser('feature3', help='...')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate feature
    if args.command == 'pathway_profiler':
        from solaris.pathway_profiler.cli import handle_pathway_mapper
        handle_pathway_mapper(args)
    
    elif args.command == 'pangenomic_analyzer':
        from solaris.pangenomic_analyzer.cli import handle_pangenomic_analyzer
        handle_pangenomic_analyzer(args)
    
    # elif args.command == 'feature3':
    #     from solaris.feature3.cli import handle_feature3
    #     handle_feature3(args)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()