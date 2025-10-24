#!/usr/bin/env python3
"""
CLI for Compatibility Predictor module.

Provides subcommands to run KEGG queries, BacDive filtering, and taxonomy matching
from the main `solaris` entrypoint.
"""
import argparse
import sys
from pathlib import Path


def setup_compatibility_parser(parent_parser):
    """Attach compatibility_predictor subparsers to the provided parent parser."""
    parser = parent_parser.add_parser('compatibility_predictor',
                                      help='Organism compatibility prediction tools')
    subparsers = parser.add_subparsers(dest='compat_command', help='Compatibility commands')

    # KEGG query
    kegg = subparsers.add_parser('kegg', help='Query KEGG for EC numbers')
    kegg.add_argument('--ec-file', '-e', required=True, help='File with EC numbers (one per line)')
    kegg.add_argument('--output', '-o', default='kegg_results.json', help='Output JSON file')
    kegg.add_argument('--max-species', '-s', type=int, default=3, help='Max species per EC')
    kegg.set_defaults(func=run_kegg)

    # BacDive access
    bacdive = subparsers.add_parser('bacdive', help='Query BacDive and filter organisms')
    bacdive.add_argument('--email', '-e', required=True, help='BacDive account email')
    bacdive.add_argument('--password', '-p', help='BacDive password (will prompt if not provided)')
    bacdive.add_argument('--taxonomy', '-t', help='Taxonomy search term')
    bacdive.add_argument('--temp-min', type=float, default=20.0, help='Minimum temperature')
    bacdive.add_argument('--temp-max', type=float, default=45.0, help='Maximum temperature')
    bacdive.add_argument('--output', '-o', help='Output file')
    bacdive.set_defaults(func=run_bacdive)

    # Taxonomy matching
    match = subparsers.add_parser('match', help='Match KEGG and BacDive organisms by NCBI taxid')
    match.add_argument('--kegg-file', '-k', default='kegg_results.json', help='KEGG results JSON file')
    match.add_argument('--bacdive-file', '-b', default='bacdive_results.json', help='BacDive results JSON file')
    match.add_argument('--email', '-e', required=True, help='Email for NCBI E-utilities')
    match.add_argument('--output-json', default='taxid_matches.json', help='Output JSON file')
    match.add_argument('--output-txt', default='taxid_matched_species.txt', help='Output text file')
    match.set_defaults(func=run_match)

    return parser


def run_kegg(args):
    # Import locally to avoid heavy imports at top-level
    from . import keggQuery

    kegg = keggQuery.KEGGQuery(delay=0.5, max_species=args.max_species)
    ecs = keggQuery.load_ec_numbers(args.ec_file)
    results = kegg.query_ec_numbers(ecs)
    keggQuery.save_results(results, args.output)
    print(f"Saved KEGG results to {args.output}")


def run_bacdive(args):
    from . import bacdive_access
    import sys

    # Save original sys.argv
    original_argv = sys.argv
    
    try:
        # Build new argv for the bacdive script (without solaris subcommands)
        sys.argv = [
            'bacdive_access.py',
            '--email', args.email,
            '--taxonomy', args.taxonomy,
            '--temp-min', str(args.temp_min),
            '--temp-max', str(args.temp_max),
            '--output', args.output
        ]
        
        # Add password if provided
        if args.password:
            sys.argv.extend(['--password', args.password])
        
        # Call bacdive_access main-like function if present
        if hasattr(bacdive_access, 'query_bacdive'):
            bacdive_access.query_bacdive(
                email=args.email, 
                password=args.password,
                taxonomy=args.taxonomy, 
                temp_min=args.temp_min,
                temp_max=args.temp_max,
                output=args.output
            )
        else:
            # Fallback: run as script with modified argv
            script_path = Path(bacdive_access.__file__)
            print(f"Executing BacDive script: {script_path}")
            import runpy
            runpy.run_path(str(script_path), run_name='__main__')
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


def run_match(args):
    from . import taxonomyMatcher

    kegg_data = taxonomyMatcher.load_kegg_data(args.kegg_file)
    bacdive_data = taxonomyMatcher.load_bacdive_data(args.bacdive_file)
    matcher = taxonomyMatcher.TaxonomyMatcher(email=args.email)
    results = matcher.match_with_taxids(kegg_data, bacdive_data)
    taxonomyMatcher.save_results(results, args.output_json)
    taxonomyMatcher.save_matched_list(results, args.output_txt)
    print(f"Saved matches to {args.output_json} and {args.output_txt}")


def handle_compatibility(args):
    if not hasattr(args, 'compat_command') or args.compat_command is None:
        print('Use `solaris compatibility_predictor -h` for help')
        return 1
    return args.func(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    setup_compatibility_parser(parser)
    ns = parser.parse_args()
    handle_compatibility(ns)
