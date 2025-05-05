import requests
import json
import csv
from tabulate import tabulate
from datetime import datetime
import os

# Configuration
FORTIGATE_IP = "192.168.10.254"
FORTIGATE_PORT = 8443  # Change to your custom HTTPS port
API_TOKEN = "byQc5xcmzdxmm14c6j41xq9sjp48fk"  # Generate via FortiGate GUI/API
VERIFY_SSL = False  # Set to True in production if using valid cert

EXPORT_DIR = "./wifi_client_exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Construct full host URL
FORTIGATE_HOST = f"https://{FORTIGATE_IP}:{FORTIGATE_PORT}"

# Request Headers
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# API URL
url = f"{FORTIGATE_HOST}/api/v2/monitor/wifi/client?with_stats=true"

def fetch_clients():
    try:
        response = requests.get(url, headers=headers, verify=VERIFY_SSL)
        response.raise_for_status()
        data = response.json()
        # If API response is a dict, and clients are in a field like 'results' or directly in a list:
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        elif isinstance(data, list):
            return data
        else:
            print("Unexpected response structure.")
            return []
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return []


def parse_client_capabilities(clients):
    table = []
    for client in clients:
        table.append([
            client.get("hostname", "N/A"),
            client.get("mac", "N/A"),
            client.get("os", "N/A"),
            client.get("11k_capable", False),
            client.get("11v_capable", False),
            client.get("11r_capable", False),
            client.get("mimo", "N/A"),
            client.get("radio_type", "N/A"),
            f"{client.get('signal', 'N/A')} dBm",
            f"{client.get('snr', 'N/A')} dB"
        ])
    return table

def display_clients_table(table):
    headers = ["Hostname", "MAC", "OS", "802.11k", "802.11v", "802.11r", "MIMO", "Radio", "Signal", "SNR"]
    print(tabulate(table, headers=headers, tablefmt="grid"))

def parse_client_capabilities(clients):
    table = []
    for client in clients:
        if not isinstance(client, dict):
            continue
        table.append([
            client.get("hostname", "N/A"),
            client.get("mac", "N/A"),
            client.get("os", "N/A"),
            client.get("11k_capable", False),
            client.get("11v_capable", False),
            client.get("11r_capable", False),
            client.get("mimo", "N/A"),
            client.get("radio_type", "N/A"),
            f"{client.get('signal', 'N/A')} dBm",
            f"{client.get('snr', 'N/A')} dB"
        ])
    return table


def export_to_csv(table, filename):
    headers = ["Hostname", "MAC", "OS", "802.11k", "802.11v", "802.11r", "MIMO", "Radio", "Signal", "SNR"]
    csv_path = os.path.join(EXPORT_DIR, filename)
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(table)
    print(f"✅ CSV exported to: {csv_path}")

def export_to_json(data, filename):
    json_path = os.path.join(EXPORT_DIR, filename)
    with open(json_path, 'w') as file:
        json.dump(data, file, indent=2)
    print(f"✅ Raw JSON exported to: {json_path}")

def export_to_html(table, filename):
    headers = ["Hostname", "MAC", "OS", "802.11k", "802.11v", "802.11r", "MIMO", "Radio", "Signal", "SNR"]
    html = tabulate(table, headers=headers, tablefmt="html")
    html_path = os.path.join(EXPORT_DIR, filename)
    with open(html_path, 'w') as file:
        file.write(html)
    print(f"✅ HTML exported to: {html_path}")

def export_to_html_with_charts(table, capability_stats, filename):
    headers = ["Hostname", "MAC", "OS", "802.11k", "802.11v", "802.11r", "MIMO", "Radio", "Signal", "SNR"]
    table_html = tabulate(table, headers=headers, tablefmt="html")

    # Pie chart data JS
    def gen_plotly_data(title, data_dict):
        labels = list(data_dict.keys())
        values = list(data_dict.values())
        return f"""
        {{
            type: 'pie',
            name: '{title}',
            labels: {json.dumps(labels)},
            values: {json.dumps(values)},
            textinfo: 'label+percent',
            hoverinfo: 'label+value',
            hole: 0.4
        }}
        """

    charts_html = ""
    for stat_name, stat_data in capability_stats.items():
        charts_html += f"""
        <div style="width: 400px; display: inline-block;">
            <h3>{stat_name}</h3>
            <div id="{stat_name.replace(" ", "_")}_chart"></div>
            <script>
            Plotly.newPlot('{stat_name.replace(" ", "_")}_chart', [{gen_plotly_data(stat_name, stat_data)}]);
            </script>
        </div>
        """

    html_content = f"""
    <html>
    <head>
        <title>Fortinet WiFi Client Capabilities</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>Connected WiFi Clients</h1>
        {table_html}
        <h2>Client Capabilities Overview</h2>
        {charts_html}
    </body>
    </html>
    """

    html_path = os.path.join(EXPORT_DIR, filename)
    with open(html_path, 'w') as file:
        file.write(html_content)
    print(f"✅ Interactive HTML exported to: {html_path}")

from collections import Counter

def summarize_capabilities(clients):
    stats = {
        "802.11k Support": Counter(),
        "802.11v Support": Counter(),
        "802.11r Support": Counter(),
        "MIMO Mode": Counter(),
        "Radio Type": Counter()
    }
    for client in clients:
        if not isinstance(client, dict):
            continue
        stats["802.11k Support"][str(client.get("11k_capable", False))] += 1
        stats["802.11v Support"][str(client.get("11v_capable", False))] += 1
        stats["802.11r Support"][str(client.get("11r_capable", False))] += 1
        stats["MIMO Mode"][client.get("mimo", "Unknown")] += 1
        stats["Radio Type"][client.get("radio_type", "Unknown")] += 1
    return stats

if __name__ == "__main__":
    print("Fetching connected WiFi clients...\n")
    clients = fetch_clients()
    if clients:
        table = parse_client_capabilities(clients)
        stats = summarize_capabilities(clients)

        print(tabulate(table, headers="firstrow", tablefmt="grid"))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_to_csv(table, f"wifi_clients_{timestamp}.csv")
        export_to_json(clients, f"wifi_clients_raw_{timestamp}.json")
        export_to_html_with_charts(table, stats, f"wifi_clients_{timestamp}.html")
    else:
        print("No clients found or API request failed.")
