/*
  Shared ESP32 sensor-only test firmware for the finalized FYP robot.

  Reads:
  - Two front HC-SR04 ultrasonic sensors.
  - One GY-291 / ADXL345 accelerometer over I2C.

  Publishes JSON status over USB serial before motor integration.
*/

#include <Wire.h>

const unsigned long BAUD_RATE = 115200;
const unsigned long MEASURE_INTERVAL_MS = 100;
const unsigned long PULSE_TIMEOUT_US = 30000;

const int SENSOR_COUNT = 2;
const char* SENSOR_NAMES[SENSOR_COUNT] = {"front_left", "front_right"};
const int TRIG_PINS[SENSOR_COUNT] = {5, 18};
const int ECHO_PINS[SENSOR_COUNT] = {34, 35};

const int I2C_SDA_PIN = 21;
const int I2C_SCL_PIN = 22;
const uint8_t ADXL345_ADDRESS = 0x53;
const float MOTION_THRESHOLD_G = 0.08;
const float VIBRATION_DELTA_THRESHOLD_G = 0.05;
const float SHOCK_THRESHOLD_G = 1.50;

float safeDistanceCm = 25.0;
bool adxl345Available = false;
float accelXG = 0.0;
float accelYG = 0.0;
float accelZG = 0.0;
float accelMagnitudeG = 0.0;
float previousAccelMagnitudeG = 1.0;
float rollDeg = 0.0;
float pitchDeg = 0.0;
bool motionDetected = false;
bool vibrationDetected = false;
bool shockDetected = false;
unsigned long lastMeasureMs = 0;

void setup() {
  Serial.begin(BAUD_RATE);

  for (int i = 0; i < SENSOR_COUNT; i++) {
    pinMode(TRIG_PINS[i], OUTPUT);
    pinMode(ECHO_PINS[i], INPUT);
    digitalWrite(TRIG_PINS[i], LOW);
  }

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  adxl345Available = setupAdxl345();
}

void loop() {
  handleSerialCommand();

  unsigned long now = millis();
  if (now - lastMeasureMs >= MEASURE_INTERVAL_MS) {
    lastMeasureMs = now;
    publishSensorStatus();
  }
}

void handleSerialCommand() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command == "PING") {
    Serial.println("{\"status\":\"ok\",\"device\":\"esp32_sensor_hub\"}");
    return;
  }

  if (command.startsWith("THRESHOLD=")) {
    float value = command.substring(10).toFloat();
    if (value > 0.0 && value < 500.0) {
      safeDistanceCm = value;
      Serial.print("{\"status\":\"threshold_updated\",\"safe_distance_cm\":");
      Serial.print(safeDistanceCm, 1);
      Serial.println("}");
    }
  }
}

void publishSensorStatus() {
  float distances[SENSOR_COUNT];
  float minDistance = 9999.0;

  for (int i = 0; i < SENSOR_COUNT; i++) {
    distances[i] = readDistanceCm(TRIG_PINS[i], ECHO_PINS[i]);
    if (distances[i] > 0.0 && distances[i] < minDistance) {
      minDistance = distances[i];
    }
  }

  bool obstacle = minDistance < safeDistanceCm;
  if (adxl345Available) {
    adxl345Available = readAdxl345();
  }

  Serial.print("{");
  for (int i = 0; i < SENSOR_COUNT; i++) {
    Serial.print("\"");
    Serial.print(SENSOR_NAMES[i]);
    Serial.print("_cm\":");
    if (distances[i] < 0.0) {
      Serial.print("null");
    } else {
      Serial.print(distances[i], 1);
    }
    Serial.print(",");
  }

  Serial.print("\"min_cm\":");
  if (minDistance >= 9999.0) {
    Serial.print("null");
  } else {
    Serial.print(minDistance, 1);
  }
  Serial.print(",\"obstacle\":");
  Serial.print(obstacle ? "true" : "false");
  Serial.print(",\"accel_g\":");
  if (!adxl345Available) {
    Serial.print("null");
  } else {
    Serial.print("{\"x\":");
    Serial.print(accelXG, 3);
    Serial.print(",\"y\":");
    Serial.print(accelYG, 3);
    Serial.print(",\"z\":");
    Serial.print(accelZG, 3);
    Serial.print("}");
  }
  Serial.print(",\"roll_deg\":");
  Serial.print(adxl345Available ? String(rollDeg, 1) : "null");
  Serial.print(",\"pitch_deg\":");
  Serial.print(adxl345Available ? String(pitchDeg, 1) : "null");
  Serial.print(",\"motion_detected\":");
  Serial.print(motionDetected ? "true" : "false");
  Serial.print(",\"vibration_detected\":");
  Serial.print(vibrationDetected ? "true" : "false");
  Serial.print(",\"shock_detected\":");
  Serial.print(shockDetected ? "true" : "false");
  Serial.println("}");
}

float readDistanceCm(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, PULSE_TIMEOUT_US);
  if (duration == 0) {
    return -1.0;
  }

  return duration / 58.0;
}

bool setupAdxl345() {
  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(0x2D);
  Wire.write(0x08);
  if (Wire.endTransmission() != 0) {
    return false;
  }

  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(0x31);
  Wire.write(0x08);
  return Wire.endTransmission() == 0;
}

bool readAdxl345() {
  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(0x32);
  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(ADXL345_ADDRESS, (uint8_t)6) != 6) {
    return false;
  }

  int16_t rawX = (int16_t)(Wire.read() | (Wire.read() << 8));
  int16_t rawY = (int16_t)(Wire.read() | (Wire.read() << 8));
  int16_t rawZ = (int16_t)(Wire.read() | (Wire.read() << 8));

  const float scaleGPerLsb = 0.0039;
  accelXG = rawX * scaleGPerLsb;
  accelYG = rawY * scaleGPerLsb;
  accelZG = rawZ * scaleGPerLsb;

  accelMagnitudeG = sqrt(
    accelXG * accelXG + accelYG * accelYG + accelZG * accelZG
  );
  rollDeg = atan2(accelYG, accelZG) * 180.0 / PI;
  pitchDeg = atan2(
    -accelXG,
    sqrt(accelYG * accelYG + accelZG * accelZG)
  ) * 180.0 / PI;

  motionDetected = abs(accelMagnitudeG - 1.0) > MOTION_THRESHOLD_G;
  vibrationDetected =
    abs(accelMagnitudeG - previousAccelMagnitudeG) >
    VIBRATION_DELTA_THRESHOLD_G;
  shockDetected = accelMagnitudeG > SHOCK_THRESHOLD_G;
  previousAccelMagnitudeG = accelMagnitudeG;
  return true;
}
