#include "secrets.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFiS3.h>

#define ONE_WIRE_BUS 8  // DS18B20 data pin connected to pin D8

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

char serverAddress[] = "192.168.1.55"; // my thinkpad's IP address
int serverPort = 3001;                 // Flask port

void setup() {
  Serial.begin(9600);
  sensors.begin();

  Serial.print("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("Device IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  sensors.requestTemperatures();
  float tempF = sensors.getTempFByIndex(0);
  Serial.print("Temp: ");
  Serial.print(tempF);
  Serial.println(" °F");

  String postData = "{\"temperature\": " + String(tempF, 2) + "}";

  WiFiClient client;
  if (client.connect(serverAddress, serverPort)) {
    client.println("POST /update/temp HTTP/1.1");
    client.print("Host: ");
    client.println(serverAddress);
    client.println("Content-Type: application/json");
    client.print("Content-Length: ");
    client.println(postData.length());
    client.println();
    client.print(postData);
    client.stop();
    Serial.println("Sent to Flask!");
  } else {
    Serial.println("Failed to connect to Flask");
  }

  delay(30000); 
}
