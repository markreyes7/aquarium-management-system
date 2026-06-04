#include <WiFiS3.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include "sensors.h"
#include "topoff_controller.h"
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
unsigned long lastAutoCheckMs = 0;
const unsigned long autoCheckIntervalMs = 2000;

void setup() {
  Serial.begin(9600);
  while (!Serial) {}

  pinMode(lightPin, OUTPUT);
  digitalWrite(lightPin, LOW);
  initTopoffController(pumpPin);

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
  updateTopoffController(pumpPin);
  handleAutoSchedule();
  handleWebClient();
  updateTemperature();
}

void handleAutoSchedule() {
  if (controlMode != AUTO_MODE) {
    return;
  }

  if (millis() - lastAutoCheckMs < autoCheckIntervalMs) {
    return;
  }
  lastAutoCheckMs = millis();

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
}

void handleWebClient() {
  WiFiClient client = server.available();

  if (!client) {
    return;
  }

  Serial.println("Client connected");

  String requestLine = client.readStringUntil('\r');
  Serial.println(requestLine);

  client.flush();

  String requestPath = extractRequestPath(requestLine);

  if (requestPath == "/light/currentStatus") {
    writeJsonResponse(
      client,
      "{\"status\":\"" + String(currentLightState ? "on" : "off") + "\"}"
    );
    closeClient(client, "Returned current light status");
    return;
  }

  if (requestPath == "/light/on") {
    controlMode = MANUAL_MODE;
    currentLightState = true;
    digitalWrite(lightPin, HIGH);
    writeJsonResponse(client, "{\"ok\":true,\"status\":\"on\",\"mode\":\"manual\"}");
    closeClient(client, "MANUAL Light ON");
    return;
  }

  if (requestPath == "/light/off") {
    controlMode = MANUAL_MODE;
    currentLightState = false;
    digitalWrite(lightPin, LOW);
    writeJsonResponse(client, "{\"ok\":true,\"status\":\"off\",\"mode\":\"manual\"}");
    closeClient(client, "MANUAL Light OFF");
    return;
  }

  if (requestPath == "/light/auto") {
    controlMode = AUTO_MODE;
    writeJsonResponse(client, "{\"ok\":true,\"mode\":\"auto\"}");
    closeClient(client, "Returned to AUTO mode");
    return;
  }

  if (requestPath == "/temp") {
    writeJsonResponse(
      client,
      "{\"temperature_f\":" + String(getCurrentTemperatureF(), 2) + "}"
    );
    closeClient(client, "Returned temperature");
    return;
  }

  if (requestPath == "/topoff/status") {
    writeTopoffStatusResponse(client);
    closeClient(client, "Returned topoff status");
    return;
  }

  if (requestPath.startsWith("/topoff/run") || requestPath.startsWith("/topoff?seconds=")) {
    float seconds = extractTopoffSeconds(requestPath);

    if (!isValidTopoffSeconds(seconds)) {
      writePlainTextResponse(client, 400, "Invalid topoff seconds");
      closeClient(client, "Rejected invalid topoff request");
      return;
    }

    if (topoffState.active) {
      writePlainTextResponse(client, 409, "Topoff already running");
      closeClient(client, "Rejected overlapping topoff request");
      return;
    }

    startTopoff(pumpPin, seconds);

    Serial.print("Running topoff pump for ");
    Serial.print(seconds);
    Serial.println(" seconds");

    writeJsonResponse(
      client,
      "{\"ok\":true,\"active\":true,\"requested_seconds\":" + String(seconds, 2) + "}"
    );
    closeClient(client, "Accepted topoff request");
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

  closeClient(client, "Returned control page");
}

String extractRequestPath(const String& requestLine) {
  int firstSpace = requestLine.indexOf(' ');
  if (firstSpace == -1) {
    return "";
  }

  int secondSpace = requestLine.indexOf(' ', firstSpace + 1);
  if (secondSpace == -1) {
    return requestLine.substring(firstSpace + 1);
  }

  return requestLine.substring(firstSpace + 1, secondSpace);
}

float extractTopoffSeconds(const String& requestPath) {
  int start = requestPath.indexOf("seconds=");
  if (start == -1) {
    return -1;
  }

  start += 8;
  int end = requestPath.indexOf('&', start);
  if (end == -1) {
    end = requestPath.length();
  }

  String value = requestPath.substring(start, end);
  return value.toFloat();
}

void writeJsonResponse(WiFiClient& client, const String& payload) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.println();
  client.println(payload);
}

void writePlainTextResponse(WiFiClient& client, int statusCode, const char* message) {
  client.print("HTTP/1.1 ");
  client.print(statusCode);
  client.println(statusCode == 400 ? " Bad Request" : " Conflict");
  client.println("Content-Type: text/plain");
  client.println("Connection: close");
  client.println();
  client.println(message);
}

void writeTopoffStatusResponse(WiFiClient& client) {
  String payload = "{\"active\":";
  payload += topoffState.active ? "true" : "false";
  payload += ",\"requested_seconds\":";
  payload += String(topoffState.requestedSeconds, 2);
  payload += ",\"last_completed_seconds\":";
  payload += String(topoffState.lastCompletedSeconds, 2);
  payload += ",\"remaining_ms\":";
  payload += String(topoffRemainingMs());
  payload += "}";

  writeJsonResponse(client, payload);
}

void closeClient(WiFiClient& client, const char* message) {
  delay(3);
  client.stop();
  Serial.println(message);
  Serial.println("Client disconnected");
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
