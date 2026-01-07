#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include "secrets.h"

WiFiSSLClient wifi;
HttpClient client(wifi, SERVER_ADDRESS, SERVER_PORT);

// -----------------------------
// Connect to WiFi (one-time)
// -----------------------------
void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  while (WiFi.begin(WIFI_SSID, WIFI_PASS) != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
}

void sendTemperature(float tempC) {
  String payload = "{\"temperature\": " + String(tempC, 2) + "}";

  client.beginRequest();
  client.post("/environment/temperature");
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", payload.length());
  client.beginBody();
  client.print(payload);
  client.endRequest();

  int statusCode = client.responseStatusCode();
  String response = client.responseBody();

  Serial.print("HTTP Status: ");
  Serial.println(statusCode);
  Serial.print("Response: ");
  Serial.println(response);
}


void setup() {
  Serial.begin(115200);
  while (!Serial);

  connectWiFi();

  
  sendTemperature(24.7);
}

void loop() {
  // Empty for now — this is a tester
}
