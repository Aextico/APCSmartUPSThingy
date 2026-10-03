import network
import socket
import uasyncio as asyncio
from ups import Ups
from machine import UART

ssid='IOT'
password='baranowka'
uart = UART(1, baudrate=2400, bits=8, parity=None, stop=1)
ups = Ups(uart)

async def connect():
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(ssid,password)
  while wlan.isconnected() == False:
    print("Waiting for connection")
    await asyncio.sleep(1)
  print(f"ip:{wlan.ifconfig()[0]}")
  return True

def render_html():
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>APC Smart-UPS</title>
    <style>
        body {{ font-family: sans-serif; background: #121212; color: #fff; padding: 20px; }}
        .card {{ background: #1e1e1e; padding: 20px; border-radius: 8px; max-width: 420px; }}
        button {{ background: #e53935; color: #fff; border: none; padding: 10px 14px; border-radius: 4px; cursor: pointer; }}
        button:disabled {{ background: #555; }}
        #log {{ margin-top: 12px; color: #ffeb3b; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>APC Smart-UPS</h2>
        <p>Model: <strong>{ups.model}</strong></p>
        <p>Serial Number: <strong>{ups.serial_number}</strong></p>
        <p>Battery Voltage: <strong>{ups.battery_voltage} V</strong></p>
        <p>Line Voltage: <strong>{ups.line_voltage} V</strong></p>
        <p>Load Level: <strong>{ups.load_level} %</strong></p>
        <p>Battery Level: <strong>{ups.battery_level} %</strong></p>
        <p>Status: <strong>{ups.status}</strong></p>
        <p>Internal Temperature: <strong>{ups.temperature} °C</strong></p>
        <p>Cause of transfer: <strong>{ups.cause_of_transfer}</strong></p>
        <p>Estimated Runtime: <strong>{ups.estimated_runtime} minutes</strong></p>
        <button id="btn-sim" onclick="runSim()">Simulate power loss (10s)</button>
        <div id="log"></div>
    </div>
    <script>
    async function runSim() {{
        const btn = document.getElementById('btn-sim');
        const log = document.getElementById('log');
        btn.disabled = true;
        log.innerText = "Trwa test baterii...";
        try {{
            const res = await fetch('/simulate', {{ method: 'POST' }});
            log.innerText = await res.text();
        }} catch(e) {{
            log.innerText = "Błąd żądania";
        }} finally {{
            btn.disabled = false;
        }}
    }}
    </script>
</body>
</html>"""

async def handle_client(reader, writer):
    raw_request = await reader.read(1024)
    request = raw_request.decode('utf-8', 'ignore')

    if "POST /simulate" in request:
        result = await ups.simulate_power_failure()
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n{result}"
    else:
        ups.download_status()
        ups.download_battery_voltage()
        html = render_html()
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n{html}"

    writer.write(response.encode('utf-8'))
    await writer.drain()
    await writer.wait_closed()
    
async def main():
  ups.initialize_smart_mode()
  ups.download_model()
  ups.download_serial_number()
  ups.download_battery_voltage()
  ups.download_line_voltage()
  ups.download_load_level()
  ups.download_battery_level()
  ups.download_status()
  ups.download_temperature()
  ups.download_cause_of_transfer()
  ups.download_estimated_runtime()
  
  await connect()
  server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
  while True:
        await asyncio.sleep(3600)
asyncio.run(main())
