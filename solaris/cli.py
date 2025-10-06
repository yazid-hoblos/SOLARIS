#!/usr/bin/env python3
"""
Solaris - Toolkit for heterologous pathway transfer for metabolic engineering
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        prog='solaris',
        description='SOLARIS: Toolkit for heterologous pathway transfer for metabolic engineering',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available tools')
    
    # Pathway Mapper subcommand
    pathway_parser = subparsers.add_parser(
        'pathway_profiler',
        help='EC-based pathway profiling and pangenomic analysis'
    )
    # Import pathway_mapper CLI and add its arguments
    from solaris.pathway_profiler.cli import setup_pathway_parser
    setup_pathway_parser(pathway_parser)
    
    # Add other subcommands here
    # feature2_parser = subparsers.add_parser('feature2', help='...')
    # feature3_parser = subparsers.add_parser('feature3', help='...')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate feature
    if args.command == 'pathway_profiler':
        from solaris.pathway_profiler.cli import handle_pathway_mapper
        handle_pathway_mapper(args)
    
    # elif args.command == 'feature2':
    #     from cyanotools.feature2.cli import handle_feature2
    #     handle_feature2(args)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()