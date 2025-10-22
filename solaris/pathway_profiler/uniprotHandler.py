import os
import requests
import csv
import time
import sys
from typing import List, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class ProteinEntry:
    """Data class for protein information"""
    ec_number: str
    uniprot_id: str
    protein_name: str
    pfam_id: str
    species: str


class UniProtHandler:
    """
    Extract Pfam domain information from UniProt for given EC numbers
    """
    
    UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
    UNIPROT_ENTRY = "https://rest.uniprot.org/uniprotkb/"
    
    def __init__(self, delay: float = 0.01, taxonomy_id: str = "2", reviewed_only: bool = False):
        """
        Initialize UniProt Pfam extractor
        
        Args:
            delay: Seconds to wait between API calls (be gentle on the server)
            taxonomy_id: NCBI taxonomy ID to filter results (default: "2" for Bacteria)
            reviewed_only: If True, only retrieve reviewed (Swiss-Prot) entries
        """
        self.delay = delay
        self.taxonomy_id = taxonomy_id
        self.reviewed_only = reviewed_only
        self.results_cache = {}  # Cache results to avoid repeated API calls
        
    def read_ec_numbers(self, ec_file: str) -> List[str]:
        """
        Read EC numbers from a file
        
        Args:
            ec_file: Path to file containing EC numbers (one per line)
            
        Returns:
            List of EC numbers
        """
        ec_numbers = []
        
        try:
            with open(ec_file, 'r') as f:
                for line in f:
                    # Skip comments and empty lines
                    if line.startswith('#') or not line.strip():
                        continue
                    ec_numbers.append(line.strip())
            
            print(f"📋 Loaded {len(ec_numbers)} EC numbers from {ec_file}")
            return ec_numbers
            
        except FileNotFoundError:
            print(f"❌ Error: File '{ec_file}' not found")
            return []
        except Exception as e:
            print(f"❌ Error reading EC file: {e}")
            return []
    
    def search_uniprot_by_ec(self, ec_number: str) -> List[Dict]:
        """
        Search UniProt for entries with a specific EC number
        
        Args:
            ec_number: EC number to search for
            
        Returns:
            List of UniProt entry dictionaries
        """
        # Build query
        query_parts = [f"ec:{ec_number}", f"taxonomy_id:{self.taxonomy_id}"]
        if self.reviewed_only:
            query_parts.append("reviewed:true")
        
        query = " AND ".join(query_parts)
        
        params = {
            "query": query,
            "format": "json",
            "fields": "accession,protein_name,organism_name",
        }
        
        try:
            response = requests.get(self.UNIPROT_SEARCH, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"🚨 Error searching UniProt for EC {ec_number}: {e}")
            return []
    
    def get_full_uniprot_entry(self, accession: str) -> Optional[Dict]:
        """
        Get full UniProt entry for an accession
        
        Args:
            accession: UniProt accession ID
            
        Returns:
            Full UniProt entry dictionary or None if error
        """
        try:
            response = requests.get(f"{self.UNIPROT_ENTRY}{accession}.json")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"🚨 Error fetching full entry for {accession}: {e}")
            return None
    
    def extract_pfam_domains(self, full_entry: Dict) -> List[str]:
        """
        Extract Pfam domain IDs from a full UniProt entry
        
        Args:
            full_entry: Full UniProt entry dictionary
            
        Returns:
            List of Pfam IDs
        """
        pfam_domains = []
        
        features = full_entry.get("uniProtKBCrossReferences", [])
        for feature in features:
            if feature.get("database") == "Pfam":
                pfam_id = feature.get("id")
                if pfam_id:
                    pfam_domains.append(pfam_id)
        
        return pfam_domains
    
    def process_ec_number(self, ec_number: str) -> List[ProteinEntry]:
        """
        Process a single EC number and extract all protein entries with Pfam domains
        
        Args:
            ec_number: EC number to process
            
        Returns:
            List of ProteinEntry objects
        """
        print(f"\n🔍 Processing EC {ec_number}")
        
        entries = []
        
        # Search UniProt
        results = self.search_uniprot_by_ec(ec_number)
        
        if not results:
            print(f"❌ No entries found for EC {ec_number}")
            return entries
        
        # Process each result
        for result in results[:1]:
            accession = result["primaryAccession"]
            
            # Extract protein name
            protein_name = result.get("proteinDescription", {}).get(
                "recommendedName", {}
            ).get("fullName", {}).get("value", "Unknown")
            
            # Extract species
            species = result.get("organism", {}).get("scientificName", "Unknown")
            
            print(f"✅ {accession} - {protein_name} ({species})")
            
            # Get full entry for Pfam domains
            full_entry = self.get_full_uniprot_entry(accession)
            
            if not full_entry:
                continue
            
            # Extract Pfam domains
            pfam_domains = self.extract_pfam_domains(full_entry)
            
            if pfam_domains:
                print(f"   Pfam domains found: {pfam_domains}")
                for pfam_id in pfam_domains:
                    entries.append(ProteinEntry(
                        ec_number=ec_number,
                        uniprot_id=accession,
                        protein_name=protein_name,
                        pfam_id=pfam_id,
                        species=species
                    ))
            else:
                print(f"   No Pfam domains found")
                # Still add entry with "No Pfam" marker
                entries.append(ProteinEntry(
                    ec_number=ec_number,
                    uniprot_id=accession,
                    protein_name=protein_name,
                    pfam_id="No Pfam",
                    species=species
                ))
            
            # Be gentle on the server
            time.sleep(self.delay)
        
        return entries
    
    def process_ec_list(self, ec_numbers: List[str]) -> List[ProteinEntry]:
        """
        Process a list of EC numbers
        
        Args:
            ec_numbers: List of EC numbers to process
            
        Returns:
            List of all ProteinEntry objects
        """
        all_entries = []
        
        for i, ec_number in enumerate(ec_numbers, 1):
            print(f"\n{'='*60}")
            print(f"Processing EC {i}/{len(ec_numbers)}: {ec_number}")
            print(f"{'='*60}")
            
            entries = self.process_ec_number(ec_number)
            all_entries.extend(entries)
            
            # Small delay between EC numbers
            if i < len(ec_numbers):
                time.sleep(self.delay)
        
        return all_entries
    
    def save_to_csv(self, entries: List[ProteinEntry], output_file: str):
        """
        Save protein entries to a TSV file
        
        Args:
            entries: List of ProteinEntry objects
            output_file: Path to output file
        """
        try:
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t')
                
                # Write header
                writer.writerow(["EC_number", "UniProt_ID", "Protein_Name", "Pfam_ID", "Species"])
                
                # Write data
                for entry in entries:
                    writer.writerow([
                        entry.ec_number,
                        entry.uniprot_id,
                        entry.protein_name,
                        entry.pfam_id,
                        entry.species
                    ])
            
            print(f"\n✅ Saved {len(entries)} entries to {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving to file: {e}")
    
    def run(self, ec_file: str, output_file: str):
        """
        Complete workflow: read EC numbers, process them, and save results
        
        Args:
            ec_file: Path to input file with EC numbers
            output_file: Path to output TSV file
        """
        print("="*60)
        print("UniProt Pfam Domain Extractor")
        print("="*60)
        print(f"Taxonomy ID: {self.taxonomy_id}")
        print(f"Reviewed only: {self.reviewed_only}")
        print(f"API delay: {self.delay}s")
        print("="*60)
        
        # Read EC numbers
        ec_numbers = self.read_ec_numbers(ec_file)
        
        if not ec_numbers:
            print("❌ No EC numbers to process")
            return
        
        # Process all EC numbers
        all_entries = self.process_ec_list(ec_numbers)
        
        # Save results
        if all_entries:
            self.save_to_csv(all_entries, output_file)
            
            # Print summary
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print(f"Total EC numbers processed: {len(ec_numbers)}")
            print(f"Total protein entries found: {len(all_entries)}")
            
            # Count unique Pfam domains
            unique_pfam = set(e.pfam_id for e in all_entries if e.pfam_id != "No Pfam")
            print(f"Unique Pfam domains: {len(unique_pfam)}")
            
            # Count entries without Pfam
            no_pfam_count = sum(1 for e in all_entries if e.pfam_id == "No Pfam")
            if no_pfam_count > 0:
                print(f"Entries without Pfam domains: {no_pfam_count}")
        else:
            print("\n❌ No entries found to save")
    
    def get_statistics(self, entries: List[ProteinEntry]) -> Dict:
        """
        Get statistics about the extracted data
        
        Args:
            entries: List of ProteinEntry objects
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_entries': len(entries),
            'unique_ec_numbers': len(set(e.ec_number for e in entries)),
            'unique_proteins': len(set(e.uniprot_id for e in entries)),
            'unique_pfam_domains': len(set(e.pfam_id for e in entries if e.pfam_id != "No Pfam")),
            'entries_without_pfam': sum(1 for e in entries if e.pfam_id == "No Pfam"),
            'unique_species': len(set(e.species for e in entries))
        }
        
        return stats


def main():
    """
    Command-line interface
    """
    if len(sys.argv) != 3:
        print("Usage: python access_uniprot.py <ec_file> <output_file>")
        sys.exit(1)
    
    ec_file = sys.argv[1]
    output_file = sys.argv[2]
    taxonomy_id = sys.argv[3] if len(sys.argv) > 3 else "2"  # Default to Bacteria
    reviewed_only = bool(sys.argv[4]) if len(sys.argv) > 4 else False
    
    # Create extractor instance
    extractor = UniProtHandler(
        delay=1.0,           # 1 second between requests
        taxonomy_id=taxonomy_id,
        reviewed_only=reviewed_only
    )
    
    # Run the extraction
    extractor.run(ec_file, output_file)


if __name__ == "__main__":
    main()