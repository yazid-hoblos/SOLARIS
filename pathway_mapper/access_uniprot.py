import os
import requests
import csv
import time
import sys

if len(sys.argv) != 3:
    print("Usage: python access_uniprot.py <ec_file> <output_file>")
    sys.exit(1)

ec_file = sys.argv[1]
output_file = sys.argv[2]

UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_ENTRY = "https://rest.uniprot.org/uniprotkb/"

with open(ec_file, 'r') as f:
    ec_numbers = []
    for line in f:
        if line.startswith('#') or not line.strip():
            continue
        ec_numbers.append(line.strip())

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter='\t')
    writer.writerow(["EC_number", "UniProt_ID", "Protein_Name", "Pfam_ID", "Species"])

    for ec in ec_numbers:
        print(f"\n🔍 EC {ec}")
 
        params = {
            "query": f"ec:{ec} AND taxonomy_id:1117", # 2 = Bacteria # AND reviewed:true
            "format": "json",
            "fields": "accession,protein_name,organism_name",
        }

        try:
            r = requests.get(UNIPROT_SEARCH, params=params)
            r.raise_for_status()
            results = r.json().get("results", [])

            if not results:
                print(f"❌ No reviewed entry found.")
                continue
            
            for entry in results:
                accession = entry["primaryAccession"]
                protein_name = entry.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "Unknown")
                
                # Extract species information
                species = entry.get("organism", {}).get("scientificName", "Unknown")
                
                print(f"✅ {accession} - {protein_name} ({species})")

                # Get full UniProt record to extract domains
                full_entry = requests.get(f"{UNIPROT_ENTRY}{accession}.json").json()

                features = full_entry.get("uniProtKBCrossReferences", [])
                pfam_domains = []
                for feature in features:
                    if feature.get("database") == "Pfam":
                        pfam_id = feature.get("id")
                        pfam_domains.append(pfam_id)

                        writer.writerow([ec, accession, protein_name, pfam_id, species])
                
                # If no Pfam domains found, still write a row with species info
                if not pfam_domains:
                    writer.writerow([ec, accession, protein_name, "No Pfam", species])
                    
                print(f"Pfam domains found: {pfam_domains}")
                
        except Exception as e:
            print(f"🚨 Error with EC {ec}: {e}")

        time.sleep(1)  # gentle on the server ;)