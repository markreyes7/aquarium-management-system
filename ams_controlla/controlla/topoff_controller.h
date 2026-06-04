#ifndef TOPOFF_CONTROLLER_H
#define TOPOFF_CONTROLLER_H

struct TopoffState {
  bool active;
  unsigned long startedAtMs;
  unsigned long durationMs;
  float requestedSeconds;
  float lastCompletedSeconds;
};

static TopoffState topoffState = {false, 0, 0, 0.0, 0.0};

static const float MIN_TOP_OFF_SECONDS = 1.0;
static const float MAX_TOP_OFF_SECONDS = 5.0;

void initTopoffController(int pumpPin) {
  pinMode(pumpPin, OUTPUT);
  digitalWrite(pumpPin, LOW);
}

bool isValidTopoffSeconds(float seconds) {
  return seconds >= MIN_TOP_OFF_SECONDS && seconds <= MAX_TOP_OFF_SECONDS;
}

bool startTopoff(int pumpPin, float seconds) {
  if (topoffState.active || !isValidTopoffSeconds(seconds)) {
    return false;
  }

  topoffState.active = true;
  topoffState.startedAtMs = millis();
  topoffState.durationMs = (unsigned long)(seconds * 1000.0);
  topoffState.requestedSeconds = seconds;

  digitalWrite(pumpPin, HIGH);
  return true;
}

void updateTopoffController(int pumpPin) {
  if (!topoffState.active) {
    return;
  }

  if (millis() - topoffState.startedAtMs < topoffState.durationMs) {
    return;
  }

  digitalWrite(pumpPin, LOW);
  topoffState.active = false;
  topoffState.lastCompletedSeconds = topoffState.requestedSeconds;
}

unsigned long topoffRemainingMs() {
  if (!topoffState.active) {
    return 0;
  }

  unsigned long elapsedMs = millis() - topoffState.startedAtMs;
  if (elapsedMs >= topoffState.durationMs) {
    return 0;
  }

  return topoffState.durationMs - elapsedMs;
}

#endif
