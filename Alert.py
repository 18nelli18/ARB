#!/usr/bin/env python3
from pathlib import Path
import json
import time
import os
import argparse
import hashlib
import logging
from datetime import datetime, timezone
import requests

ALERT_STATE_FILE = "alert_state.json"

TEMPLATE = """\
📣 *Nouveau signalement*
🕒 {when}
📍 *Lieu*: {location_type}{location_detail}
⏱️ *Délai*: {time_delta}
👮 *Agents*: {agents}
🎯 *Personnes ciblées*: {target_count}
⚠️ *Intervention*: {intervention_type}
📌 *Issue*: {issue}
📡 *Transmissions*: {transmissions}
☎️ *Contact accepté*: {contact}
"""

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logging.warning("report.json illisible, on réessaie au prochain cycle…")
        return []

def _save_state(state_path, state):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def _load_state(state_path):
    if not Path(state_path).exists():
        return {"seen": []}
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"seen": []}

def _entry_id(entry: dict) -> str:
    # Create a stable hash for an entry, robust to ordering
    data = json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def _format_agents(entry):
    agents = entry.get("agents") or []
    if isinstance(agents, list):
        parts = []
        for a in agents:
            t = a.get("type", "agent")
            c = a.get("count")
            parts.append(f"{t}" + (f" ×{c}" if c else ""))
        return ", ".join(parts) if parts else "—"
    # fallback
    return str(agents)

def _format_location(entry):
    lt = entry.get("location_type") or entry.get("location") or "—"
    detail = ""
    # Try various keys that may contain a free-text place
    for k in ["other_location", "location_detail", "train_station", "metro_station", "bus_stop", "transport_type"]:
        v = entry.get(k)
        if v:
            detail = f" — {v}"
            break
    # Add emoji if not already present
    if isinstance(lt, str) and not lt.startswith(("🚇", "🏙️", "🚏", "🏠", "🏬", "🛤️")):
        lt = f"{lt}"
    return lt, detail

def _format_when(entry):
    ts = entry.get("timestamp")
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone().strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
    return "—"

def _build_message(entry: dict) -> str:
    location_type, location_detail = _format_location(entry)
    return TEMPLATE.format(
        when=_format_when(entry),
        location_type=location_type,
        location_detail=location_detail,
        time_delta=entry.get("time_delta", "—"),
        agents=_format_agents(entry),
        target_count=entry.get("target_count", "—"),
        intervention_type=entry.get("intervention_type", entry.get("control_type", "—")),
        issue=entry.get("issue", "—"),
        transmissions=entry.get("transmissions", entry.get("transmission", "—")),
        contact=entry.get("contact", entry.get("contact_yn", "—")),
    )

def _send_telegram(token: str, chat_id: str, text: str, preview=False, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": not preview,
        "parse_mode": parse_mode,
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def watch_and_alert(report_path: str, interval: int, token: str, chat_id: str, state_path: str):
    logging.info("Surveillance du fichier: %s", report_path)
    state = _load_state(state_path)
    seen = set(state.get("seen", []))

    # On première exécution, ne pas spammer: marquer l'existant comme vu
    existing = _load_json(report_path)
    for e in existing:
        seen.add(_entry_id(e))
    _save_state(state_path, {"seen": sorted(seen)})

    last_mtime = Path(report_path).stat().st_mtime if Path(report_path).exists() else 0.0

    while True:
        try:
            if not Path(report_path).exists():
                time.sleep(interval)
                continue

            mtime = Path(report_path).stat().st_mtime
            if mtime != last_mtime:
                # Le fichier a changé, recharger et trouver les nouvelles entrées
                entries = _load_json(report_path)
                new_entries = []
                for e in entries:
                    eid = _entry_id(e)
                    if eid not in seen:
                        new_entries.append((eid, e))
                if new_entries:
                    logging.info("→ %d nouveau(x) rapport(s) détecté(s).", len(new_entries))
                    # Envoyer dans l'ordre d'ajout
                    for eid, entry in new_entries:
                        msg = _build_message(entry)
                        try:
                            _send_telegram(token, chat_id, msg)
                            seen.add(eid)
                            _save_state(state_path, {"seen": sorted(seen)})
                            logging.info("Message envoyé.")
                        except Exception as send_err:
                            logging.exception("Échec de l'envoi Telegram: %s", send_err)
                last_mtime = mtime

            time.sleep(interval)
        except KeyboardInterrupt:
            logging.info("Arrêt demandé par l'utilisateur.")
            break
        except Exception as e:
            logging.exception("Erreur inattendue: %s", e)
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Alerte Telegram sur nouveaux rapports.")
    parser.add_argument("--file", default="report.json", help="Chemin du fichier de rapports JSON")
    parser.add_argument("--interval", type=int, default=5, help="Intervalle de vérification en secondes")
    parser.add_argument("--state", default=ALERT_STATE_FILE, help="Fichier d'état pour éviter les doublons")
    parser.add_argument("--token", default=os.getenv("TELEGRAM_BOT_TOKEN"), help="Token du bot Telegram")
    parser.add_argument("--chat-id", default=os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHANNEL_ID"),
                        help="ID du chat/canal Telegram (ex: -1001234567890 ou @mon_canal)")
    parser.add_argument("--debug", action="store_true", help="Active les logs DEBUG")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    if not args.token or not args.chat_id:
        raise SystemExit("Veuillez définir TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID (ou passer --token et --chat-id).")

    watch_and_alert(args.file, args.interval, args.token, args.chat_id, args.state)

if __name__ == "__main__":
    main()
