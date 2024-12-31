import os
import logging
import requests
import json
import csv

# Logging-Konfiguration: Logs werden sowohl in die Konsole als auch in eine Datei geschrieben
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nodes_export.log'),
        logging.StreamHandler()  # Ausgabe in die Konsole
    ]
)

# URL der JSON-Datei
URL = "https://nef05mon.karte.neanderfunk.de/data/nodes.json"
CSV_FILE = "nodes.csv"
JSON_FILE = "nodes.json"

try:
    # JSON-Datei herunterladen
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
    logging.info("JSON-Daten erfolgreich heruntergeladen.")

    # JSON-Datei speichern (immer überschreiben)
    with open(JSON_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)
    logging.info(f"JSON-Daten erfolgreich in {JSON_FILE} gespeichert.")

    # CSV-Vergleich vorbereiten
    existing_nodes = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_nodes[row['node_id']] = row
        logging.info("Vorhandene CSV-Daten geladen.")

    # CSV-Datei erstellen und schreiben
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['hostname', 'hardware_model', 'node_id', 'contact', 'ipv6_address']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Durch die Nodes iterieren und relevante Daten extrahieren
        for node in data.get('nodes', []):
            nodeinfo = node.get('nodeinfo', {})
            hostname = nodeinfo.get('hostname', 'N/A')
            hardware_model = nodeinfo.get('hardware', {}).get('model', 'N/A')
            node_id = nodeinfo.get('node_id', 'N/A')
            contact = nodeinfo.get('owner', {}).get('contact', 'N/A')
            ipv6_addresses = nodeinfo.get('network', {}).get('addresses', [])
            ipv6_address = ipv6_addresses[0] if ipv6_addresses else 'N/A'

            # Änderungen prüfen
            old_data = existing_nodes.get(node_id, {})
            if old_data != {
                'hostname': hostname,
                'hardware_model': hardware_model,
                'node_id': node_id,
                'contact': contact,
                'ipv6_address': ipv6_address
            }:
                logging.info(f"Änderung erkannt für Node-ID {node_id}")
            
            # In CSV schreiben
            writer.writerow({
                'hostname': hostname,
                'hardware_model': hardware_model,
                'node_id': node_id,
                'contact': contact,
                'ipv6_address': ipv6_address
            })
            
            # Loggen der Node-Daten (direkte Ausgabe)
            log_message = (f"Node hinzugefügt/aktualisiert: Hostname={hostname}, Hardware={hardware_model}, "
                           f"Node-ID={node_id}, Kontakt={contact}, IPv6={ipv6_address}")
            print(log_message)  # Direkte Ausgabe in die Konsole
            logging.info(log_message)

    logging.info(f"Daten wurden erfolgreich in die CSV-Datei {CSV_FILE} exportiert.")

except requests.exceptions.RequestException as e:
    logging.error(f"Fehler beim Herunterladen der JSON-Datei: {e}")
except (json.JSONDecodeError, KeyError) as e:
    logging.error(f"Fehler beim Verarbeiten der JSON-Daten: {e}")
except Exception as e:
    logging.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
