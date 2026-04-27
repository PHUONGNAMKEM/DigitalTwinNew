import mqtt from "mqtt";

const brokerUrl = "wss://2c2795488b39467aa8abc09b3e44185e.s1.eu.hivemq.cloud:8884/mqtt";
const options = {
    username: "iot_device",
    password: "iot_device123ACB",
    reconnectPeriod: 0,
    clean: true,
    connectTimeout: 10000,
};

console.log("JS MQTT Test - Correct broker URL");
console.log("Broker:", brokerUrl);

const client = mqtt.connect(brokerUrl, options);

client.on("connect", () => {
    console.log("[OK] JavaScript connected!");
    client.end();
    process.exit(0);
});

client.on("error", (err) => {
    console.log("[FAIL]", err.message);
    client.end();
    process.exit(1);
});

setTimeout(() => { console.log("[FAIL] Timeout"); client.end(); process.exit(1); }, 10000);
