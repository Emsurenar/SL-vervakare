import requests
import os
from datetime import datetime

# =========================================================
# KONFIGURATION
# =========================================================
# Byt ut mot de Site IDs vi vill övervaka. 
# SL Journey Planner fungerar bäst med riktiga namn på hållplatser, men ibland behövs extId.
ROUTES = [
    {"from": "Tekniska högskolan", "to": "Enskede gård"},
    {"from": "Tekniska högskolan", "to": "Medborgarplatsen"},
    {"from": "Tekniska högskolan", "to": "Nytorget"}
]

# Tröskelvärde för att skicka notis (i minuter)
DELAY_THRESHOLD = 20

# API-nycklar (Hämtas från GitHub Secrets)
API_KEY = os.getenv("SL_API_KEY") 
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    """Skickar ett meddelande via Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram-nycklar saknas.")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
        print("Telegram-notis skickad.")
    except Exception as e:
        print(f"Kunde inte skicka Telegram-notis: {e}")

def check_delays():
    """Hämtar SL-resor och kollar om det finns stora förseningar."""
    if not API_KEY:
        print("SL API_KEY saknas.")
        return

    print(f"Kör SL-koll klockan {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    delays_found = []

    for route in ROUTES:
        # Använd Trafiklabs SL Reseplanerare 3.1 eller Journey planner API V2.
        # Just nu skickar vi mot v2 (Trip-endpoint) via standard API.
        # (Behöver bytas mot ResRobot eller v3.1 om Trafiklab uppdaterat).
        # Här är ett exempelanrop för Reseplanerare 3.1:
        
        url = f"https://api.sl.se/api2/TravelplannerV3_1/trip.json?key={API_KEY}&originExtId={route['from']}&destExtId={route['to']}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                trips = data.get("Trip", [])
                
                # Reseplaneraren returnerar flera trips, vi kollar den eller de mest aktuella.
                for trip in trips:
                    leg = trip.get("LegList", {}).get("Leg", [])
                    if isinstance(leg, dict):
                        leg = [leg]
                    
                    # Kolla första benet (Leg) i resan för försening.
                    if len(leg) > 0:
                        first_leg = leg[0]
                        origin = first_leg.get("Origin", {})
                        
                        # Jämför tidtabell (time) med realtid (rtTime)
                        time_str = origin.get("time")
                        rt_time_str = origin.get("rtTime")
                        
                        if time_str and rt_time_str:
                            # Tidsformat är "HH:MM:SS"
                            planned = datetime.strptime(time_str, "%H:%M:%S")
                            actual = datetime.strptime(rt_time_str, "%H:%M:%S")
                            
                            delay = (actual - planned).total_seconds() / 60
                            
                            if delay >= DELAY_THRESHOLD:
                                delays_found.append(
                                    f"⚠️ *FÖRSENING ÖVER 20 MIN!*\n"
                                    f"Rutt: {route['from']} ➡️ {route['to']}\n"
                                    f"Planerad: {time_str} | Aktual: {rt_time_str}\n"
                                    f"Försening: {int(delay)} minuter."
                                )
                        
                        # Om inställt
                        if first_leg.get("cancelled"):
                            delays_found.append(
                                f"❌ *INSTÄLLT!*\n"
                                f"Rutt: {route['from']} ➡️ {route['to']}\n"
                                f"Tidtabell: {time_str}"
                            )
            else:
                print(f"Kunde inte hämta {route['from']} -> {route['to']} (Kod: {response.status_code})")
        except Exception as e:
            print(f"Nätverksfel: {e}")

    # Skicka resultat till Telegram 
    if delays_found:
        message = "\n\n".join(delays_found) + "\n\n[Läs om SL Förseningsersättning](https://sl.se/kundservice/forseningsersattning)"
        send_telegram_message(message)
    else:
        print("✅ Inga större förseningar hittade över 20 min.")

if __name__ == "__main__":
    check_delays()
