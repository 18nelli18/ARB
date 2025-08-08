#!/usr/bin/env python3
# Alert.py

import json
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
# Chemin vers le fichier JSON à surveiller
WATCHED_FILE = Path(__file__).parent / "report.json"

# Liste des identifiants de groupes Signal (obtenus via signal-cli)
SIGNAL_GROUPS = [
    "YOUR_GROUP_ID_1",  # exemple : a1b2c3d4-5678-90ab-cdef-1234567890ab
    "YOUR_GROUP_ID_2",

]

# Numéro de téléphone enregistré dans signal-cli (+CCCNNNNNNNN)
SIGNAL_SENDER = "+33783604000"

# --- Fonction d'envoi de message via signal-cli ---
def send_to_signal(group_id: str, message: str):
    cmd = [
        "signal-cli",
        "--username", SIGNAL_SENDER,
        "send",
        "-g", group_id,
        "--message", message
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"[+] Message envoyé au groupe {group_id}")
    except subprocess.CalledProcessError as e:
        print(f"[!] Erreur en envoyant au groupe {group_id} : {e}")

# --- Fonction de formatage d'une entrée JSON ---
def format_entry(entry: dict) -> str:
    lines = [
        f"*Nouvelle mise à jour* 🆕",
        f"• *Timestamp* : {entry.get('timestamp')}",
        f"• *Type d'intervention* : {entry.get('intervention_type')}",
        f"• *Lieu* : {entry.get('location_type')} / {entry.get('other_location')}",
        f"• *Durée* : {entry.get('time_delta')}",
        f"• *Agents* : " + ", ".join(
            f"{a['count']}×{a['type']}" for a in entry.get('agents', [])
        ),
        f"• *Cibles* : {entry.get('target_count')}",
        f"• *Problème* : {entry.get('issue')}",
        f"• *Transmissions* : {entry.get('transmissions')}",
        f"• *Contact* : {entry.get('contact')}",
        f"• *À supprimer* : {len(entry.get('to_delete', []))} éléments",
    ]
    return "\n".join(lines)

# --- Gestionnaire d'événements pour watchdog ---
class ReportHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_mtime = None

    def on_modified(self, event):
        if event.src_path != str(WATCHED_FILE):
            return

        mtime = WATCHED_FILE.stat().st_mtime
        # Ne pas traiter deux fois la même modification
        if self._last_mtime is not None and mtime == self._last_mtime:
            return
        self._last_mtime = mtime

        try:
            data = json.loads(WATCHED_FILE.read_text(encoding="utf-8"))
            # Vous pouvez ici filtrer les entrées déjà traitées si besoin
            for entry in data:
                msg = format_entry(entry)
                for grp in SIGNAL_GROUPS:
                    send_to_signal(grp, msg)
        except Exception as e:
            print(f"[!] Impossible de lire/traiter {WATCHED_FILE} : {e}")

def main():
    # Initialisation de l'observer
    event_handler = ReportHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(WATCHED_FILE.parent), recursive=False)
    observer.start()
    print(f"🔍 Surveillance de {WATCHED_FILE} en cours...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
