import requests
import os
from datetime import datetime



# Ändpunkter för vår sökning (ResRobot v2.1)
ROUTES = [
    {"from": "Tekniska högskolan (Stockholm)", "to": "Enskede gård T-bana"},
    {"from": "Tekniska högskolan (Stockholm)", "to": "Medborgarplatsen T-bana"},
    {"from": "Tekniska högskolan (Stockholm)", "to": "Nytorgsgatan (Stockholm)"}
]

DELAY_THRESHOLD = 20
STATE_FILE = "sent_deviations.txt"

# API-nycklar (Hämtas från GitHub Secrets)
API_KEY = os.getenv("SL_API_KEY") # ResRobot v2.1
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram-nycklar saknas. Testar dry-run:")
        print(message)
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Kunde inte skicka Telegram-notis: {e}")

def get_already_sent():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def mark_as_sent(incident_id):
    with open(STATE_FILE, "a") as f:
        f.write(f"{incident_id}\n")

def check_delays():
    if not API_KEY:
        print("API_KEY (ResRobot) saknas.")
        return

    print(f"Kör exakt ruttsökning klockan {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    already_sent = get_already_sent()
    new_incidents = 0

    for route in ROUTES:
        url = (
            f"https://api.resrobot.se/v2.1/trip?format=json"
            f"&accessId={API_KEY}"
            f"&originId={get_station_id(route['from'], API_KEY)}"
            f"&destId={get_station_id(route['to'], API_KEY)}"
        )
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                trips = data.get("Trip", [])
                
                for trip in trips:
                    leg_list = trip.get("LegList", {}).get("Leg", [])
                    if isinstance(leg_list, dict):
                        leg_list = [leg_list]
                    
                    if not leg_list:
                        continue
                        
                    first_leg = leg_list[0]
                    origin = first_leg.get("Origin", {})
                    
                    time_str = origin.get("time")
                    rt_time_str = origin.get("rtTime")
                    date_str = origin.get("date", datetime.now().strftime("%Y-%m-%d"))
                    
                    # Unikt ID för just denna resa
                    trip_ext_id = trip.get("extId", f"{route['from']}-{time_str}")
                    
                    if trip_ext_id in already_sent:
                        continue

                    # Kolla inställt
                    if first_leg.get("cancelled"):
                        send_telegram_alert(route, time_str, "Inställd", trip_ext_id)
                        mark_as_sent(trip_ext_id)
                        new_incidents += 1
                        continue
                        
                    # Kolla försening via exakt beräkning
                    if time_str and rt_time_str:
                        planned = datetime.strptime(time_str, "%H:%M:%S")
                        actual = datetime.strptime(rt_time_str, "%H:%M:%S")
                        
                        delay = (actual - planned).total_seconds() / 60
                        
                        if delay >= DELAY_THRESHOLD:
                            send_telegram_alert(route, time_str, f"{int(delay)} minuter sen", trip_ext_id, rt_time_str)
                            mark_as_sent(trip_ext_id)
                            new_incidents += 1
            else:
                print(f"Kunde inte hämta {route['from']} -> {route['to']} (Kod: {response.status_code})")
        except Exception as e:
            print(f"Nätverksfel vid ruttsökning: {e}")

    if new_incidents == 0:
        print("Inga nya försenade resor upptäcktes.")

def send_telegram_alert(route, time_str, status, trip_ext_id, rt_time_str=""):
    actual_info = f" | Ny tid: {rt_time_str}" if rt_time_str else ""
    created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # URL encoded destinations för Uber
    uber_dest = "Enskede%20G%C3%A5rd" if "Enskede" in route['to'] else "Medborgarplatsen" if "Medborgar" in route['to'] else "Nytorget"
    
    message = (
        f"RESA FÖRSENAD!\n\n"
        f"Rutt: {route['from']} -> {route['to']}\n"
        f"Planerad avgång: {time_str}{actual_info}\n"
        f"Status: {status}\n\n"
        f"*Bevis: *\n"
        f"• Avgång: `{time_str}` (Rutt: {route['from']} -> {route['to']})\n"
        f"• Datum/Tid uppmätt: `{created_time}`\n"
        f"• Internt Rese-ID: `{trip_ext_id}`\n\n"
        f"*SNABB-BOKA UBER (Genväg)*\n"
        f"[Boka Uber från nuvarande plats till {uber_dest}](https://m.uber.com/ul/?action=setPickup&dropoff[formatted_address]={uber_dest},%20Stockholm)\n\n"
        f"[Ansök om ersättning hos SL](https://sl.se/kundservice/forseningsersattning)"
    )
    send_telegram_message(message)

def get_station_id(station_name, api_key):
    """Söker upp stations-ID från ResRobots platssökning."""
    url = f"https://api.resrobot.se/v2.1/location.name?input={station_name}&format=json&accessId={api_key}"
    try:
        req = requests.get(url, timeout=5).json()
        stops = req.get("stopLocationOrCoordLocation", [])
        if stops:
            return stops[0].get("StopLocation", {}).get("extId")
    except:
        pass
    return ""

if __name__ == "__main__":
    check_delays()
