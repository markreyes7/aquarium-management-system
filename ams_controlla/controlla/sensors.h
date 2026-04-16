#ifndef TEMP_SENSOR_H
#define TEMP_SENSOR_H

#include <OneWire.h>
#include <DallasTemperature.h>

static const int ONE_WIRE_BUS = 5;

static OneWire oneWire(ONE_WIRE_BUS);
static DallasTemperature sensors(&oneWire);

static float currentTemperatureF = -999.0;

void initTempSensor() {
  sensors.begin();
}

void updateTemperature() {
  sensors.requestTemperatures();
  currentTemperatureF = sensors.getTempFByIndex(0);
}

float getCurrentTemperatureF() {
  return currentTemperatureF;
}

#endif