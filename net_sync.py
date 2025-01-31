import requests
import time
import xml.etree.ElementTree as ET

# Configuration
NETLOGGER_URL = "https://www.netlogger.org/api/GetCheckins.php"
HAM_LIVE_API_BASE = "https://www.ham.live/api/admin/interactions/"
HAM_LIVE_AUTH_TOKEN = "token-go-here"  # Store securely
SERVER_NAME = "NETLOGGER2"  # Netlogger server name
NET_NAME = "OMISS%2040m%20SSB%20Net"  # The net's name
NET_ID = "6799760aacd4e2c007ecbe8e"  # The Net ID required by Ham.live
SYNC_INTERVAL = 30  # Sync every 30 seconds

# Headers for Ham.live authentication
HEADERS = {
    "Authorization": f"Bearer {HAM_LIVE_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_netlogger_data():
    """Fetch check-in data from Netlogger and save a copy to a file."""
    url = f"{NETLOGGER_URL}?ServerName={SERVER_NAME}&NetName={NET_NAME}"
    print(f"Fetching data from Netlogger: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        print("Successfully fetched data from Netlogger")
        with open("netlogger_data.xml", "w") as file:
            file.write(response.text)
        print("Saved Netlogger data to netlogger_data.xml")
        return response.text
    else:
        print(f"Error fetching Netlogger data: {response.status_code} {response.text}")
        return None

def parse_netlogger_data(xml_data):
    """Parse the XML response from Netlogger to extract check-in details."""
    check_ins = []
    try:
        root = ET.fromstring(xml_data)
        for checkin in root.findall(".//Checkin"):
            call = checkin.find("Callsign").text
            status = checkin.find("Status").text.strip() if checkin.find("Status") is not None else ""
            if status.lower() == "(c/o)":
                status = "checked out"
            else:
                status = "checked in"
            print(f"Parsed station: Callsign={call}, Status={status}")
            check_ins.append({"callsign": call, "status": status})
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
    return check_ins

def sync_to_ham_live(check_ins):
    """Send Netlogger check-in data to Ham.live with proper login/logout commands."""
    for check_in in check_ins:
        if check_in["status"].lower() == "checked in":
            command = f"i {check_in['callsign']}"
        elif check_in["status"].lower() == "checked out":
            command = f"o {check_in['callsign']}"
        else:
            print(f"Skipping unknown status for {check_in['callsign']}")
            continue

        payload = {"cmdLine": command}
        print(f"Sending command to Ham.live: {command}")
        response = requests.post(f"{HAM_LIVE_API_BASE}{NET_ID}", headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            print(f"Successfully executed {command} for {check_in['callsign']} on Ham.live")
        elif response.status_code == 401:
            print("Authentication failed: Invalid or expired token. Please check your HAM_LIVE_AUTH_TOKEN.")
        else:
            print(f"Failed to execute {command} for {check_in['callsign']}: {response.status_code} {response.text}")

def main():
    """Main loop to continuously sync data during net operation."""
    print("Starting Netlogger to Ham.live sync...")
    while True:
        print("Checking for new Netlogger data...")
        xml_data = fetch_netlogger_data()
        if xml_data:
            check_ins = parse_netlogger_data(xml_data)
            sync_to_ham_live(check_ins)
        else:
            print("No data received from Netlogger.")
        print(f"Sleeping for {SYNC_INTERVAL} seconds before next sync...")
        time.sleep(SYNC_INTERVAL)  # Wait before next sync

if __name__ == "__main__":
    main()
