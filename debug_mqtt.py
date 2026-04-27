"""Quick Python MQTT test with corrected URL"""
import os, sys, ssl, time
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

broker = os.getenv("MQTT_BROKER")
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")

print(f"Python MQTT Test - Correct broker URL")
print(f"Broker  : {broker}")
print(f"Username: {username}")
print(f"Password: {password}")

result = {"done": False, "ok": False}

def on_connect(client, userdata, flags, reason_code, properties):
    result["done"] = True
    rc_str = str(reason_code)
    if rc_str == "Success":
        result["ok"] = True
        print(f"[OK] Python connected! reason_code={rc_str}")
    else:
        print(f"[FAIL] reason_code={rc_str}")

# Test 1: TCP 8883
print("\n--- TCP:8883 ---")
client = mqtt.Client(
    callback_api_version=CallbackAPIVersion.VERSION2,
    client_id=f"pytest_{int(time.time())}_tcp",
    transport="tcp",
    protocol=mqtt.MQTTv311,
)
client.on_connect = on_connect

try:
    import certifi
    ca = certifi.where()
except:
    ca = None

ctx = ssl.create_default_context()
if ca:
    ctx.load_verify_locations(ca)
client.tls_set_context(ctx)
client.username_pw_set(username, password)
client.connect(broker, 8883, 60)
client.loop_start()

for i in range(8):
    time.sleep(1)
    if result["done"]:
        break

client.loop_stop()
try: client.disconnect()
except: pass

if not result["ok"]:
    # Test 2: WSS 8884
    print("\n--- WSS:8884 ---")
    result = {"done": False, "ok": False}
    
    client2 = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=f"pytest_{int(time.time())}_wss",
        transport="websockets",
        protocol=mqtt.MQTTv311,
    )
    client2.on_connect = on_connect
    ctx2 = ssl.create_default_context()
    if ca:
        ctx2.load_verify_locations(ca)
    client2.tls_set_context(ctx2)
    client2.ws_set_options(path="/mqtt")
    client2.username_pw_set(username, password)
    client2.connect(broker, 8884, 60)
    client2.loop_start()
    
    for i in range(8):
        time.sleep(1)
        if result["done"]:
            break
    
    client2.loop_stop()
    try: client2.disconnect()
    except: pass

print(f"\nFinal: {'[OK] SUCCESS' if result['ok'] else '[FAIL]'}")
