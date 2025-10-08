"""
BacDive Database Query Script - CORRECTED VERSION
Install: pip install bacdive
Register: https://api.bacdive.dsmz.de/login

Documentation: https://api.bacdive.dsmz.de/strain_fields_information
"""

import bacdive
import json


def inspect_strain_structure(strain_data, bacdive_id):
    """
    Print the structure of a strain to understand the data format.
    """
    print(f"\n{'='*60}")
    print(f"INSPECTING STRAIN {bacdive_id}")
    print(f"{'='*60}")
    
    # Print main sections
    print("\nAvailable sections:")
    for section in strain_data.keys():
        print(f"  - {section}")
    
    # Check for oxygen tolerance with correct key names
    print("\n--- Checking Oxygen Tolerance ---")
    if 'Physiology and metabolism' in strain_data:
        print("'Physiology and metabolism' section exists")
        phys_data = strain_data['Physiology and metabolism']
        print(f"Subsections: {list(phys_data.keys())}")
        
        if 'oxygen tolerance' in phys_data:
            print("Oxygen tolerance data found:")
            ox_data = phys_data['oxygen tolerance']
            print(f"  Type: {type(ox_data)}")
            if isinstance(ox_data, list):
                for i, entry in enumerate(ox_data):
                    print(f"  Entry {i}: {entry}")
            else:
                print(f"  Data: {ox_data}")
        else:
            print("No 'oxygen tolerance' subsection found")
    
    # Check for temperature with correct key names
    print("\n--- Checking Temperature ---")
    if 'Culture and growth conditions' in strain_data:
        print("'Culture and growth conditions' section exists")
        culture_data = strain_data['Culture and growth conditions']
        print(f"Subsections: {list(culture_data.keys())}")
        
        if 'culture temp' in culture_data:
            print("Temperature data found:")
            temp_data = culture_data['culture temp']
            print(f"  Type: {type(temp_data)}")
            if isinstance(temp_data, list):
                for i, entry in enumerate(temp_data):
                    print(f"  Entry {i}: {entry}")
            else:
                print(f"  Data: {temp_data}")
        else:
            print("No 'culture temp' subsection found")
    
    # Check name with correct key names
    print("\n--- Checking Name ---")
    if 'Name and taxonomic classification' in strain_data:
        name_data = strain_data['Name and taxonomic classification']
        print(f"Subsections: {list(name_data.keys())}")
        
        if 'strains' in name_data:
            strains_data = name_data['strains']
            print(f"  Strains type: {type(strains_data)}")
            if isinstance(strains_data, list):
                for i, strain_info in enumerate(strains_data):
                    print(f"  Strain {i}: {strain_info}")
                    break
            elif isinstance(strains_data, dict):
                for strain_id, strain_info in strains_data.items():
                    print(f"  Strain {strain_id}: {strain_info}")
                    break


def extract_oxygen_tolerance(strain_data):
    """Extract oxygen tolerance from strain data - CORRECTED."""
    try:
        if 'Physiology and metabolism' in strain_data:
            phys_data = strain_data['Physiology and metabolism']
            
            # Try different possible field names for oxygen tolerance
            for field_name in ['oxygen tolerance', 'oxygen_tolerance', 'oxygen tol']:
                if field_name in phys_data:
                    oxygen_data = phys_data[field_name]
                    oxygen_entries = []
                    
                    if isinstance(oxygen_data, list):
                        for entry in oxygen_data:
                            if isinstance(entry, dict):
                                # Try different field names
                                for key in ['oxygen_tol', 'oxygen tolerance', 'oxygen', 'value']:
                                    if key in entry:
                                        oxygen_entries.append(str(entry[key]))
                                        break
                            elif isinstance(entry, str):
                                oxygen_entries.append(entry)
                    elif isinstance(oxygen_data, str):
                        oxygen_entries.append(oxygen_data)
                    
                    if oxygen_entries:
                        return ', '.join(oxygen_entries)
    except Exception as e:
        pass
    return None


def extract_temperature(strain_data):
    """Extract temperature from strain data - CORRECTED."""
    try:
        if 'Culture and growth conditions' in strain_data:
            if 'culture temp' in strain_data['Culture and growth conditions']:
                # Get all temperature entries (data is a LIST)
                temp_data = strain_data['Culture and growth conditions']['culture temp']
                temp_entries = []
                
                if isinstance(temp_data, list):
                    for entry in temp_data:
                        if isinstance(entry, dict):
                            temp_info = {}
                            # Correct field names: 'temperature' and 'type'
                            if 'temperature' in entry:
                                temp_info['temp'] = entry['temperature']
                            if 'type' in entry:
                                temp_info['type'] = entry['type']
                            if temp_info:
                                temp_entries.append(temp_info)
                                
                elif isinstance(temp_data, dict):
                    temp_info = {}
                    if 'temperature' in temp_data:
                        temp_info['temp'] = temp_data['temperature']
                    if 'type' in temp_data:
                        temp_info['type'] = temp_data['type']
                    if temp_info:
                        temp_entries.append(temp_info)
                
                if temp_entries:
                    return temp_entries
    except Exception as e:
        pass
    return None


def extract_name(strain_data):
    """Extract organism name - CORRECTED."""
    try:
        if 'Name and taxonomic classification' in strain_data:
            # Field name has spaces: 'full scientific name'
            if 'full scientific name' in strain_data['Name and taxonomic classification']:
                return strain_data['Name and taxonomic classification']['full scientific name']
    except:
        pass
    return 'Unknown'


def extract_bacdive_id(strain_data):
    """Extract BacDive ID."""
    try:
        if 'General' in strain_data:
            return strain_data['General'].get('BacDive-ID')
    except:
        pass
    return None


def extract_ncbi_taxid(strain_data):
    """Extract NCBI taxonomy ID from BacDive strain data."""
    try:
        # Location 1: General section (preferred - species level)
        if 'General' in strain_data:
            if 'NCBI tax id' in strain_data['General']:
                print(strain_data['General']['NCBI tax id'])
                tax_info = strain_data['General']['NCBI tax id']
                if isinstance(tax_info, dict) and 'NCBI tax id' in tax_info:
                    taxid = tax_info['NCBI tax id']
                    return str(taxid)
                elif isinstance(tax_info, list):
                    for entry in tax_info:
                        if isinstance(entry, dict) and entry['Matching level'] == 'strain':
                            taxid = entry['NCBI tax id']
                            return str(taxid)
        
        # Location 2: Sequence information - 16S sequences
        if 'Sequence information' in strain_data:
            seq_info = strain_data['Sequence information']
            
            if '16S sequences' in seq_info:
                seqs = seq_info['16S sequences']
                if isinstance(seqs, list) and seqs:
                    for seq in seqs:
                        if 'NCBI tax ID' in seq:
                            return str(seq['NCBI tax ID'])
            
            # Location 3: Genome sequences
            if 'genome sequences' in seq_info:
                genomes = seq_info['genome sequences']
                if isinstance(genomes, list) and genomes:
                    for genome in genomes:
                        if 'NCBI tax ID' in genome:
                            return str(genome['NCBI tax ID'])
    except:
        pass
    return None


def filter_by_oxygen_tolerance(client, taxonomy_query, oxygen_types=['aerobe'], max_strains=100):
    """
    Search and filter organisms by oxygen tolerance.
    """
    print(f"Searching for: {taxonomy_query}")
    count = client.search(taxonomy=taxonomy_query)
    print(f"Found {count} strains")
    
    if count == 0:
        return []
    
    matching_organisms = []
    processed = 0
    
    print(f"Retrieving and filtering strains (max {max_strains})...")
    for strain in client.retrieve():
        processed += 1
        
        if processed > max_strains:
            print(f"Reached limit of {max_strains} strains")
            break
        
        if processed % 50 == 0:
            print(f"  Processed {processed} strains, found {len(matching_organisms)} matches...")
        
        try:
            oxygen_info = extract_oxygen_tolerance(strain)
            
            if oxygen_info:
                # Check if any of the desired oxygen types match
                for otype in oxygen_types:
                    if otype.lower() in oxygen_info.lower():
                        matching_organisms.append({
                            'bacdive_id': extract_bacdive_id(strain),
                            'ncbi_taxid': extract_ncbi_taxid(strain),
                            'name': extract_name(strain),
                            'oxygen_tolerance': oxygen_info,
                            'strain_data': strain
                        })
                        break
        except Exception as e:
            continue
    
    print(f"Processed {processed} strains total")
    return matching_organisms


def filter_by_temperature(client, taxonomy_query, min_temp=None, max_temp=None, 
                         temp_type='optimum', max_strains=100):
    """
    Filter organisms by growth temperature.
    temp_type can be: 'optimum', 'maximum', 'minimum', or None for any
    """
    print(f"Searching for: {taxonomy_query}")
    count = client.search(taxonomy=taxonomy_query)
    print(f"Found {count} strains")
    
    if count == 0:
        return []
    
    matching_organisms = []
    processed = 0
    
    print(f"Retrieving and filtering strains (max {max_strains})...")
    for strain in client.retrieve():
        processed += 1
        
        if processed > max_strains:
            print(f"Reached limit of {max_strains} strains")
            break
        
        if processed % 50 == 0:
            print(f"  Processed {processed} strains, found {len(matching_organisms)} matches...")
        
        try:
            temp_entries = extract_temperature(strain)
            
            if temp_entries:
                for temp_entry in temp_entries:
                    # Check if this entry matches our criteria
                    if temp_type and 'type' in temp_entry:
                        if temp_type.lower() not in temp_entry['type'].lower():
                            continue
                    
                    if 'temp' in temp_entry:
                        try:
                            if not '-' in str(temp_entry['temp']):  # Skip ranges for now
                                temp_value = float(temp_entry['temp'])
                            else:
                                temp_value = float(temp_entry['temp'].split('-')[0].strip())
                            
                            # Check temperature range
                            if min_temp and temp_value < min_temp:
                                continue
                            if max_temp and temp_value > max_temp:
                                continue
                            
                            # Match found
                            matching_organisms.append({
                                'bacdive_id': extract_bacdive_id(strain),
                                'ncbi_taxid': extract_ncbi_taxid(strain),
                                'name': extract_name(strain),
                                'temperature': temp_entry,
                                'strain_data': strain
                            })
                            break  # Only add once per strain
                        except (ValueError, TypeError):
                            continue
        except Exception as e:
            continue
    
    print(f"Processed {processed} strains total")
    return matching_organisms


def main():
    # Replace with your credentials
    EMAIL = "yazidhoblos4@gmail.com"
    PASSWORD = "djAyrr4XhCW@73n"
    
    print("Connecting to BacDive...")
    client = bacdive.BacdiveClient(EMAIL, PASSWORD)
    
    # # FIRST: Inspect a single strain to understand the structure
    # print("\n" + "="*60)
    # print("STEP 1: Inspecting data structure of one strain")
    # print("="*60)
    
    # # Get one strain to inspect
    # client.search(culturecolno="DSM 402")
    # for strain in client.retrieve():
    #     inspect_strain_structure(strain, "DSM 402")
    #     break
    
    # Example 1: Filter by oxygen tolerance
    print("\n" + "="*60)
    print("STEP 2: Filter by oxygen tolerance (aerobe)")
    print("="*60)
    aerobic_organisms = filter_by_oxygen_tolerance(
        client,
        taxonomy_query='Bacillus',
        oxygen_types=['aerobe'],
        max_strains=200
    )
    
    print(f"\n✓ Found {len(aerobic_organisms)} aerobic organisms")
    for org in aerobic_organisms[:10]:
        print(f"  - {org['name']}")
        print(f"    ID: {org['bacdive_id']}, O2: {org['oxygen_tolerance']}")
        if org['ncbi_taxid']:
            print(f"    NCBI TaxID: {org['ncbi_taxid']}")
        else:
            print(f"    NCBI TaxID: Not available")
    
    if aerobic_organisms:
        with open('aerobic_organisms.json', 'w') as f:
            # Don't save full strain_data to keep file smaller
            simplified = [{k: v for k, v in org.items() if k != 'strain_data'} 
                         for org in aerobic_organisms]
            json.dump(simplified, f, indent=2)
        print(f"\n✓ Saved to aerobic_organisms.json")
        
        # Count how many have taxonomy IDs
        with_taxid = sum(1 for org in aerobic_organisms if org.get('ncbi_taxid'))
        print(f"  - {with_taxid}/{len(aerobic_organisms)} organisms have NCBI taxonomy IDs")
    
    # Example 2: Filter by temperature
    print("\n" + "="*60)
    print("STEP 3: Filter by temperature (30-40°C, any type)")
    print("="*60)
    mesophiles = filter_by_temperature(
        client,
        taxonomy_query='Chloroflexus',
        min_temp=0,
        max_temp=100,
        temp_type=None,  # Accept any type (growth, optimum, etc.)
        max_strains=200
    )
    
    print(f"\n✓ Found {len(mesophiles)} mesophilic organisms (30-40°C)")
    for org in mesophiles[:10]:
        print(f"  - {org['name']}")
        print(f"    ID: {org['bacdive_id']}, Temp: {org['temperature']}")
        if org['ncbi_taxid']:
            print(f"    NCBI TaxID: {org['ncbi_taxid']}")
        else:
            print(f"    NCBI TaxID: Not available")
    
    if mesophiles:
        with open('mesophiles.json', 'w') as f:
            simplified = [{k: v for k, v in org.items() if k != 'strain_data'} 
                         for org in mesophiles]
            json.dump(simplified, f, indent=2)
        print(f"\n✓ Saved to mesophiles.json")
        
        # Count how many have taxonomy IDs
        with_taxid = sum(1 for org in mesophiles if org.get('ncbi_taxid'))
        print(f"  - {with_taxid}/{len(mesophiles)} organisms have NCBI taxonomy IDs")


if __name__ == "__main__":
    main()