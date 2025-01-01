import json
import csv
import os
import logging
from datetime import datetime

# Konfiguration des Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dateinamen für die Quellen und Ergebnisse
NODE_URLS_FILE = "nodeurl.txt"
BASE_JSON_FILE = "nodes-{source}.json"
BASE_CSV_FILE = "nodes-{source}.csv"

def read_node_urls(file):
    """Liest die URLs aus der Datei nodeurl.txt."""
    if not os.path.exists(file):
        logging.error(f"Datei {file} nicht gefunden!")
        return []
    with open(file) as f:
        return [line.strip() for line in f if line.strip()]

def download_json(url, json_file):
    """Lädt die JSON-Datei herunter und speichert sie lokal."""
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        with open(json_file, 'w') as file:
            json.dump(response.json(), file, indent=4)
        logging.info(f"JSON-Datei erfolgreich heruntergeladen: {json_file}")
    else:
        logging.error(f"Fehler beim Herunterladen der JSON-Datei: {response.status_code}")

def load_existing_csv(csv_file):
    """Lädt bestehende CSV-Daten, falls vorhanden."""
    if not os.path.exists(csv_file):
        return {}
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return {row['node_id']: row for row in reader}

def extract_node_data(node):
    """Extrahiert relevante Daten aus einem Node."""
    nodeinfo = node.get('nodeinfo', {})
    addresses = nodeinfo.get('network', {}).get('addresses', [])
    ipv6 = next((addr for addr in addresses if ':' in addr), 'Keine IPv6-Adresse')
    return {
        'hostname': nodeinfo.get('hostname', 'Unbekannt'),
        'hardware_model': nodeinfo.get('hardware', {}).get('model', 'Unbekannt'),
        'node_id': nodeinfo.get('node_id', 'Unbekannt'),
        'contact': nodeinfo.get('owner', {}).get('contact', 'Unbekannt'),
        'ipv6': ipv6
    }

def save_to_csv(nodes, csv_file):
    """Speichert Node-Daten in eine CSV-Datei."""
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['hostname', 'hardware_model', 'node_id', 'contact', 'ipv6'])
        writer.writeheader()
        for node in nodes:
            writer.writerow(node)
    logging.info(f"CSV-Datei erfolgreich gespeichert: {csv_file}")

def process_nodes(json_file, csv_file):
    """Verarbeitet die Nodes und unterscheidet zwischen neu, aktualisiert und unverändert."""
    with open(json_file) as file:
        data = json.load(file)
    
    existing_nodes = load_existing_csv(csv_file)
    new_nodes = []
    updated_nodes = []
    unchanged_nodes = []
    
    for node in data.get('nodes', []):
        node_data = extract_node_data(node)
        node_id = node_data['node_id']
        
        if node_id not in existing_nodes:
            logging.info(f"Neue Node hinzugefügt: {node_data}")
            new_nodes.append(node_data)
        else:
            old_data = existing_nodes[node_id]
            if node_data != old_data:
                logging.info(f"Node aktualisiert: Alt: {old_data} -> Neu: {node_data}")
                updated_nodes.append(node_data)
            else:
                logging.info(f"Node unverändert: {node_data}")
                unchanged_nodes.append(node_data)
    
    save_to_csv(new_nodes + updated_nodes + unchanged_nodes, csv_file)

def main():
    urls = read_node_urls(NODE_URLS_FILE)
    if not urls:
        logging.error("Keine URLs gefunden!")
        return
    
    for idx, url in enumerate(urls, start=1):
        source = f"source{idx}"
        json_file = BASE_JSON_FILE.format(source=source)
        csv_file = BASE_CSV_FILE.format(source=source)
        
        download_json(url, json_file)
        process_nodes(json_file, csv_file)

if __name__ == '__main__':
    main()
