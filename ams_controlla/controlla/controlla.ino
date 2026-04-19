#include <WiFiS3.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include "sensors.h"
#include "secrets.h"

// Static IP config
IPAddress ip(192, 168, 1, 100);

WiFiServer server(80);

const int lightPin = 3;
const int pumpPin = 4;

// UDP + NTP
WiFiUDP ntpUDP;

// Pacific Daylight Time = UTC-7
// Change to -8 * 60 * 60 when Pacific Standard Time is active
NTPClient timeClient(ntpUDP, "pool.ntp.org", -7 * 60 * 60);

// Schedule
// Example: ON at 11:25, OFF at 20:30
const int onHour = 11;
const int onMinute = 25;

const int offHour = 20;
const int offMinute = 30;

// Track light state
bool currentLightState = false;

// Control modes
enum ControlMode {
  AUTO_MODE,
  MANUAL_MODE
};

ControlMode controlMode = AUTO_MODE;

void setup() {
  Serial.begin(9600);
  while (!Serial) {}

  pinMode(lightPin, OUTPUT);
  pinMode(pumpPin, OUTPUT);
  digitalWrite(lightPin, LOW);
  digitalWrite(pumpPin, LOW);

  Serial.println("Starting...");

  WiFi.config(ip);

  Serial.println("Connecting to WiFi...");
  while (WiFi.begin(WIFI_SSID, WIFI_PASS) != WL_CONNECTED) {
    Serial.println("Retrying WiFi...");
    delay(2000);
  }

  Serial.println("Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("Web server started");

  timeClient.begin();
  timeClient.setTimeOffset(-7 * 60 * 60);

  Serial.println("Syncing NTP time...");
  while (!timeClient.update()) {
    timeClient.forceUpdate();
    delay(500);
  }

  Serial.print("Initial synced time: ");
  printCurrentTime();
  initTempSensor();
}

void loop() {
  handleAutoSchedule();
  handleWebClient();
  updateTemperature();
}

void handleAutoSchedule() {
  if (controlMode != AUTO_MODE) {
    return;
  }

  timeClient.update();

  unsigned long epoch = timeClient.getEpochTime();
  if (epoch < 100000) {
    Serial.println("NTP time not synced yet");
    return;
  }

  int hour = timeClient.getHours();
  int minute = timeClient.getMinutes();

  int currentTotal = hour * 60 + minute;
  int onTotal = onHour * 60 + onMinute;
  int offTotal = offHour * 60 + offMinute;

  bool desiredState = false;

// Schedule work
  if (onTotal < offTotal) {
    desiredState = (currentTotal >= onTotal && currentTotal < offTotal);
  }

  else {
    desiredState = (currentTotal >= onTotal || currentTotal < offTotal);
  }

  Serial.println("----- AUTO CHECK -----");
  Serial.print("Time: ");
  printCurrentTime();

  Serial.print("currentTotal: ");
  Serial.println(currentTotal);

  Serial.print("onTotal: ");
  Serial.println(onTotal);

  Serial.print("offTotal: ");
  Serial.println(offTotal);

  Serial.print("desiredState: ");
  Serial.println(desiredState ? 1 : 0);

  Serial.print("currentLightState: ");
  Serial.println(currentLightState ? 1 : 0);

  if (desiredState != currentLightState) {
    currentLightState = desiredState;
    digitalWrite(lightPin, currentLightState ? HIGH : LOW);

    Serial.print("AUTO changed light to: ");
    Serial.println(currentLightState ? "ON" : "OFF");
  }
  else{
    Serial.println("Nothing to send/ not sending signal");
  }

  Serial.print("Temperature: ");
  Serial.print(getCurrentTemperatureF());
  Serial.println(" °F");

  delay(2000);
}

void handleWebClient() {
  WiFiClient client = server.available();

  if (!client) {
    return;
  }

  Serial.println("Client connected");

  String request = client.readStringUntil('\r');
  Serial.println(request);

  client.flush();

  

  if (request.indexOf("/light/currentStatus") != -1) {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: application/json");
    client.println("Connection: close");
    client.println();
    client.print("{\"status\":\"");
    client.print(currentLightState ? "on" : "off");
    client.println("\"}");

    delay(3);
    client.stop();
    Serial.println("Returned current light status");
    Serial.println("Client disconnected");
    return;
  }

  else if (request.indexOf("/light/on") != -1) {
    controlMode = MANUAL_MODE;
    currentLightState = true;
    digitalWrite(lightPin, HIGH);
    Serial.println("MANUAL Light ON");
  }
  else if (request.indexOf("/light/off") != -1) {
    controlMode = MANUAL_MODE;
    currentLightState = false;
    digitalWrite(lightPin, LOW);
    Serial.println("MANUAL Light OFF");
  }
  else if (request.indexOf("/light/auto") != -1) {
    controlMode = AUTO_MODE;
    Serial.println("Returned to AUTO mode");
  }
  else if (request.indexOf("/temp") != -1) {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: application/json");
    client.println("Connection: close");
    client.println();

    client.print("{\"temperature_f\": ");
    client.print(getCurrentTemperatureF());
    client.println("}");

    client.stop();
    return;
  }
  else if (request.indexOf("/topoff?seconds=") != -1) {
    float seconds = extractTopoffSeconds(request);

    if (seconds > 0 && seconds <= 5) {
      Serial.print("Running topoff pump for ");
      Serial.print(seconds);
      Serial.println(" seconds");

      digitalWrite(pumpPin, HIGH);
      delay((unsigned long)(seconds * 1000));
      digitalWrite(pumpPin, LOW);

      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: text/plain");
      client.println("Connection: close");
      client.println();
      client.print("Topoff completed in ");
      client.print(seconds);
      client.println(" seconds");

      delay(3);
      client.stop();
      Serial.println("Client disconnected");
      return;
    }

    client.println("HTTP/1.1 400 Bad Request");
    client.println("Content-Type: text/plain");
    client.println("Connection: close");
    client.println();
    client.println("Invalid topoff seconds");

    delay(3);
    client.stop();
    Serial.println("Client disconnected");
    return;
  }

  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/html");
  client.println("Connection: close");
  client.println();

  client.println("<!DOCTYPE html>");
  client.println("<html>");
  client.println("<head>");
  client.println("<title>Aquarium Light Control</title>");
  client.println("</head>");
  client.println("<body>");
  client.println("<h1>Aquarium Light Control</h1>");

  client.print("<p>Mode: ");
  client.print(controlMode == AUTO_MODE ? "AUTO_MODE" : "MANUAL");
  client.println("</p>");

  client.print("<p>Light State: ");
  client.print(currentLightState ? "ON" : "OFF");
  client.println("</p>");

  client.print("<p>Current Time: ");
  client.print(timeClient.getHours());
  client.print(":");
  if (timeClient.getMinutes() < 10) client.print("0");
  client.print(timeClient.getMinutes());
  client.println("</p>");

  client.println("<a href=\"/light/on\"><button>ON</button></a>");
  client.println("<a href=\"/light/off\"><button>OFF</button></a>");
  client.println("<a href=\"/light/auto\"><button>AUTO</button></a>");

  client.println("</body>");
  client.println("</html>");

  delay(3);
  client.stop();
  Serial.println("Client disconnected");
}

float extractTopoffSeconds(const String& request) {
  int start = request.indexOf("/topoff?seconds=");
  if (start == -1) {
    return -1;
  }

  start += 16;
  int end = request.indexOf(' ', start);
  if (end == -1) {
    end = request.length();
  }

  String value = request.substring(start, end);
  return value.toFloat();
}

void printCurrentTime() {
  int hour = timeClient.getHours();
  int minute = timeClient.getMinutes();

  Serial.print(hour);
  Serial.print(":");
  if (minute < 10) {
    Serial.print("0");
  }
  Serial.println(minute);
}
