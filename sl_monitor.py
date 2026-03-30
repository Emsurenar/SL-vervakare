import requests
import os
import re
from datetime import datetime

# =========================================================
# KONFIGURATION
# =========================================================
# Vilka linjer vill vi bevaka?
RELEVANT_LINES = ["13", "14", "17", "18", "19", "2"]
STATE_FILE = "sent_deviations.txt"

# API-nycklar (Hämtas från GitHub Secrets)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram-nycklar saknas. Skriver ut i loggen istället:")
        print(message)
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram-notis skickad.")
        else:
            print(f"Fel vid sändning till Telegram: {response.text}")
    except Exception as e:
        print(f"Kunde inte ansluta till Telegram: {e}")

def get_already_sent():
    """Läser in ID:n för störningar vi redan larmat om."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def mark_as_sent(deviation_id):
    """Sparar störnings-ID:t i textfilen så vi inte larmar om den igen."""
    with open(STATE_FILE, "a") as f:
        f.write(f"{deviation_id}\n")

def check_delays():
    print(f"Checkar SL Deviations klockan {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    already_sent = get_already_sent()
    
    url = "https://deviations.integration.sl.se/v1/messages"
    headers = {"User-Agent": "SL-Monitor/2.0 (Python)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # Undvik att krascha Actions om SL:s server tillfälligt ligger nere (502/503)
        if response.status_code != 200:
            print(f"SL API returnerade kod {response.status_code}. Pausar tills nästa körning.")
            return

        deviations = response.json()
        new_incidents = 0
        
        for dev in deviations:
            dev_id = str(dev.get("deviation_case_id", ""))
            
            # Har vi redan larmat om exakt detta ID? Hoppa över!
            if dev_id in already_sent:
                continue
                
            scope = dev.get("scope", {})
            lines_affected = []
            
            for line in scope.get("lines", []):
                designation = str(line.get("designation", ""))
                if designation in RELEVANT_LINES:
                    lines_affected.append(designation)
            
            if lines_affected:
                variants = dev.get("message_variants", [])
                sv_variant = next((v for v in variants if v.get("language") == "sv"), None)
                
                if sv_variant:
                    header = sv_variant.get("header", "Störning")
                    details = sv_variant.get("details", "")
                    
                    text_lower = (header + " " + details).lower()
                    # Larma endast om det faktiskt låter som en försening / strul (inte "ändrade tider under jul")
                    if "försen" in text_lower or "inställ" in text_lower or "stopp" in text_lower or "ur trafik" in text_lower:
                        
                        # Formatera snyggt
                        lines_str = ", ".join(sorted(set(lines_affected)))
                        icon = "[STOPP]" if "stopp" in text_lower or "inställ" in text_lower else "[VARNING]"
                        
                        # Hämta tidpunkt för när störningen skapades hos SL (som bevis)
                        created_str = dev.get("created", "")
                        if created_str:
                            # Parse dates strictly or gracefully via slicing if python < 3.11
                            # Exempelformat: 2026-03-30T08:38:49.977+02:00
                            created_time = created_str.replace("T", " ")[:16]
                        else:
                            created_time = datetime.now().strftime("%Y-%m-%d %H:%M")

                        message = (
                            f"{icon} *NY SL-STÖRNING!*\n\n"
                            f"*{header}*\n"
                            f"Berörda linjer: {lines_str}\n\n"
                            f"_{details}_\n\n"
                            f"*DITT BEVISMATERIAL TILL SL*\n"
                            f"Kopiera och klistra in detta vid din ersättningsansökan:\n"
                            f"• Officiell tidpunkt: `{created_time}`\n"
                            f"• Händelse-ID (SL): `{dev_id}`\n\n"
                            f"*SNABB-BOKA UBER (Genvägar från nuvarande plats):*\n"
                            f"• [Till Enskede Gård](https://m.uber.com/ul/?action=setPickup&dropoff[formatted_address]=Enskede%20G%C3%A5rd,%20Stockholm)\n"
                            f"• [Till Medborgarplatsen](https://m.uber.com/ul/?action=setPickup&dropoff[formatted_address]=Medborgarplatsen,%20Stockholm)\n"
                            f"• [Till Nytorget](https://m.uber.com/ul/?action=setPickup&dropoff[formatted_address]=Nytorget,%20Stockholm)\n\n"
                            f"[Ansök om ersättning hos SL](https://sl.se/kundservice/forseningsersattning)"
                        )
                        
                        send_telegram_message(message)
                        mark_as_sent(dev_id)
                        new_incidents += 1
        
        if new_incidents == 0:
            print("Inga nya incidenter på bevakade rutter.")
            
    except requests.exceptions.RequestException as e:
        print(f"Nätverksproblem mot SL: {e} - Försöker igen om 5 minuter.")
    except Exception as e:
        print(f"Okänt kodfel: {e}")

if __name__ == "__main__":
    check_delays()
