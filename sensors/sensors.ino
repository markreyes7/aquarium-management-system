#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFiS3.h>

#define ONE_WIRE_BUS 8  // DS18B20 data pin connected to digital pin 8

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

char WIFI_SSID[] = //wifi_name
char WIFI_PASS[] = //pass

char serverAddress[] = "localhost"; 
int serverPort = 3001;

void setup() {
  Serial.begin(9600);
  sensors.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("WiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  sensors.requestTemperatures();
  float tempF = sensors.getTempFByIndex(0);

  Serial.print("Temperature (°F): ");
  Serial.println(tempF);

  // Build JSON payload
  String postData = "{\"temperature\": " + String(tempF, 2) + "}";

  // TODO fix this.
  WiFiClient client;
  if (client.connect(serverAddress, serverPort)) {
    Serial.println("Connected to Flask server");

    client.println("POST /update/temp HTTP/1.1");
    client.print("Host: ");
    client.println(serverAddress);
    client.println("Content-Type: application/json");
    client.print("Content-Length: ");
    client.println(postData.length());
    client.println();  
    client.print(postData); 

    
    unsigned long timeout = millis();
    while (client.connected() && !client.available()) {
      if (millis() - timeout > 5000) {
        Serial.println(">>> Timeout waiting for server");
        client.stop();
        return;
      }
      delay(10);
    }

   
    while (client.available()) {
      char c = client.read();
      Serial.write(c);
    }

    client.stop();
    Serial.println("\nDisconnected from server");
  } else {
    Serial.println("Failed to connect to Flask server");
  }

  delay(5000);
}
