#ifndef TEMP_SENSOR_H
#define TEMP_SENSOR_H

#include <OneWire.h>
#include <DallasTemperature.h>

static const int ONE_WIRE_BUS = 5;

static OneWire oneWire(ONE_WIRE_BUS);
static DallasTemperature sensors(&oneWire);

static float currentTemperatureF = -999.0;
static unsigned long lastTemperatureReadMs = 0;
static const unsigned long TEMPERATURE_READ_INTERVAL_MS = 5000;

void initTempSensor() {
  sensors.begin();
  sensors.requestTemperatures();
  currentTemperatureF = sensors.getTempFByIndex(0);
  lastTemperatureReadMs = millis();
}

void updateTemperature() {
  if (millis() - lastTemperatureReadMs < TEMPERATURE_READ_INTERVAL_MS) {
    return;
  }

  sensors.requestTemperatures();
  currentTemperatureF = sensors.getTempFByIndex(0);
  lastTemperatureReadMs = millis();
}

float getCurrentTemperatureF() {
  return currentTemperatureF;
}

#endif
