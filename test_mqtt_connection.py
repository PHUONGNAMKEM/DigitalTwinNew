"""
Minimal MQTT test - try different protocol versions and direct password
"""
import ssl
import time
import os
import sys

try:
    import certifi
    ca = certifi.where()
except:
    ca = None

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

broker = "2c27954b8b39467aa8abc09b3e44185e.s1.eu.hivemq.cloud"
username = "iot_web"
password = "nam123456@IOT"

print(f"Broker: {broker}")
print(f"Username: [{username}]")
print(f"Password: [{password}]")
print()


def try_connect(label, protocol, transport, port):
    print(f"\n--- {label} ---")
    
    result = {"done": False, "ok": False, "msg": ""}
    
    def on_connect_v2(client, userdata, flags, reason_code, properties):
        result["done"] = True
        if reason_code == 0 or str(reason_code) == "Success":
            result["ok"] = True
            result["msg"] = "Connected!"
            print(f"  [OK] Connected! reason_code={reason_code}")
        else:
            result["msg"] = str(reason_code)
            print(f"  [FAIL] reason_code={reason_code}")

    def on_connect_v1(client, userdata, flags, rc):
        result["done"] = True
        if rc == 0:
            result["ok"] = True
            result["msg"] = "Connected!"
            print(f"  [OK] Connected! rc={rc}")
        else:
            result["msg"] = f"rc={rc}"
            print(f"  [FAIL] rc={rc}")
    
    try:
        if protocol == mqtt.MQTTv5:
            client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION2,
                client_id=f"test_{int(time.time())}",
                protocol=protocol,
                transport=transport,
            )
            client.on_connect = on_connect_v2
        else:
            client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION1,
                client_id=f"test_{int(time.time())}",
                protocol=protocol,
                transport=transport,
                clean_session=True,
            )
            client.on_connect = on_connect_v1
        
        if transport == "websockets":
            client.ws_set_options(path="/mqtt")
        
        if ca:
            client.tls_set(ca_certs=ca)
        else:
            client.tls_set()
        
        client.username_pw_set(username, password)
        client.connect(broker, port, 60)
        client.loop_start()
        
        for i in range(8):
            time.sleep(1)
            if result["done"]:
                break
        
        client.loop_stop()
        try:
            client.disconnect()
        except:
            pass
        
        return result["ok"], result["msg"]
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False, str(e)


results = []

# Test 1: MQTTv311 + TCP 8883
ok, msg = try_connect("MQTTv3.1.1 + TCP:8883", mqtt.MQTTv311, "tcp", 8883)
results.append(("MQTTv3.1.1 TCP:8883", ok, msg))

# Test 2: MQTTv311 + WebSocket 8884
ok, msg = try_connect("MQTTv3.1.1 + WSS:8884", mqtt.MQTTv311, "websockets", 8884)
results.append(("MQTTv3.1.1 WSS:8884", ok, msg))

# Test 3: MQTTv5 + TCP 8883
ok, msg = try_connect("MQTTv5 + TCP:8883", mqtt.MQTTv5, "tcp", 8883)
results.append(("MQTTv5 TCP:8883", ok, msg))

# Test 4: MQTTv5 + WebSocket 8884
ok, msg = try_connect("MQTTv5 + WSS:8884", mqtt.MQTTv5, "websockets", 8884)
results.append(("MQTTv5 WSS:8884", ok, msg))

print(f"\n{'='*50}")
print("RESULTS SUMMARY")
print(f"{'='*50}")
for label, ok, msg in results:
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}: {msg}")
