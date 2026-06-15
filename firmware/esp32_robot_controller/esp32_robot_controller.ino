/*
  ESP32 robot controller for the Raspberry Pi 4 FYP prototype.

  ESP32 responsibilities:
  - Read two front HC-SR04 ultrasonic sensors.
  - Read a GY-291 / ADXL345 accelerometer over I2C.
  - Publish JSON sensor status to the Raspberry Pi 4 over USB serial.
  - Receive high-level movement commands.
  - Control four DC motors through two MX1508 dual H-bridge modules.
  - Stop on obstacle, unknown command, or command timeout.

  Hardware notes:
  - Use level shifting on each 5 V HC-SR04 Echo signal.
  - GY-291 / ADXL345 provides acceleration, roll/pitch tilt, and
    motion/vibration/shock observations.
  - MX1508 channels use two PWM-capable inputs per motor.
  - For the first prototype, the ESP32 USB port provides power, serial
    communication, and development access from the Raspberry Pi.
  - Confirm all pins and electrical ratings before physical testing.
*/

#include <Wire.h>

const unsigned long BAUD_RATE = 115200;
const unsigned long MEASURE_INTERVAL_MS = 100;
const unsigned long COMMAND_TIMEOUT_MS = 1000;
const unsigned long PULSE_TIMEOUT_US = 30000;

const int BASE_SPEED = 90;
const int TURN_SPEED = 80;
const int SEARCH_SPEED = 65;

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

struct MotorPins {
  int input1;
  int input2;
};

// Two MX1508 modules provide four two-input motor channels.
MotorPins frontLeft  = {25, 26};
MotorPins frontRight = {27, 14};
MotorPins rearLeft   = {32, 33};
MotorPins rearRight  = {16, 17};

float safeDistanceCm = 25.0;
float latestDistances[SENSOR_COUNT] = {-1.0, -1.0};
float latestMinCm = -1.0;
bool latestObstacle = false;
bool latestSensorFault = true;

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
unsigned long lastCommandMs = 0;

void setup() {
  Serial.begin(BAUD_RATE);

  for (int i = 0; i < SENSOR_COUNT; i++) {
    pinMode(TRIG_PINS[i], OUTPUT);
    pinMode(ECHO_PINS[i], INPUT);
    digitalWrite(TRIG_PINS[i], LOW);
  }

  setupMotor(frontLeft);
  setupMotor(frontRight);
  setupMotor(rearLeft);
  setupMotor(rearRight);
  stopAll();

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  adxl345Available = setupAdxl345();
  lastCommandMs = millis();
}

void loop() {
  handleSerialCommand();

  unsigned long now = millis();
  if (now - lastMeasureMs >= MEASURE_INTERVAL_MS) {
    lastMeasureMs = now;
    updateSensors();
    publishSensorStatus();
  }

  if (latestObstacle || latestSensorFault || (now - lastCommandMs > COMMAND_TIMEOUT_MS)) {
    stopAll();
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
    Serial.println("{\"status\":\"ok\",\"device\":\"esp32_robot_controller\"}");
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
    return;
  }

  executeCommand(command);
  lastCommandMs = millis();
}

void executeCommand(String command) {
  if ((latestObstacle || latestSensorFault) && command != "STOP") {
    stopAll();
    Serial.println(latestObstacle ? "ACK:STOP:OBSTACLE" : "ACK:STOP:SENSOR_FAULT");
    return;
  }

  if (command == "FWD") {
    moveForward(BASE_SPEED);
    Serial.println("ACK:FWD");
  } else if (command == "LEFT") {
    turnLeft(TURN_SPEED);
    Serial.println("ACK:LEFT");
  } else if (command == "RIGHT") {
    turnRight(TURN_SPEED);
    Serial.println("ACK:RIGHT");
  } else if (command == "SEARCH") {
    turnLeft(SEARCH_SPEED);
    Serial.println("ACK:SEARCH");
  } else {
    stopAll();
    Serial.println("ACK:STOP");
  }
}

void updateSensors() {
  float minDistance = 9999.0;

  for (int i = 0; i < SENSOR_COUNT; i++) {
    latestDistances[i] = readDistanceCm(TRIG_PINS[i], ECHO_PINS[i]);
    if (latestDistances[i] > 0.0 && latestDistances[i] < minDistance) {
      minDistance = latestDistances[i];
    }
  }

  latestMinCm = minDistance >= 9999.0 ? -1.0 : minDistance;
  latestSensorFault = latestMinCm < 0.0;
  latestObstacle = latestMinCm > 0.0 && latestMinCm < safeDistanceCm;

  if (adxl345Available) {
    adxl345Available = readAdxl345();
  }
}

void publishSensorStatus() {
  Serial.print("{");
  for (int i = 0; i < SENSOR_COUNT; i++) {
    Serial.print("\"");
    Serial.print(SENSOR_NAMES[i]);
    Serial.print("_cm\":");
    if (latestDistances[i] < 0.0) {
      Serial.print("null");
    } else {
      Serial.print(latestDistances[i], 1);
    }
    Serial.print(",");
  }

  Serial.print("\"min_cm\":");
  if (latestMinCm < 0.0) {
    Serial.print("null");
  } else {
    Serial.print(latestMinCm, 1);
  }

  Serial.print(",\"obstacle\":");
  Serial.print(latestObstacle ? "true" : "false");
  Serial.print(",\"sensor_fault\":");
  Serial.print(latestSensorFault ? "true" : "false");
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
  Wire.write(0x2D);  // POWER_CTL
  Wire.write(0x08);  // Measurement mode
  if (Wire.endTransmission() != 0) {
    return false;
  }

  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(0x31);  // DATA_FORMAT
  Wire.write(0x08);  // Full resolution, +/-2 g
  return Wire.endTransmission() == 0;
}

bool readAdxl345() {
  Wire.beginTransmission(ADXL345_ADDRESS);
  Wire.write(0x32);  // DATAX0
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

void setupMotor(MotorPins motor) {
  pinMode(motor.input1, OUTPUT);
  pinMode(motor.input2, OUTPUT);
}

void moveForward(int speedValue) {
  setMotor(frontLeft, speedValue);
  setMotor(frontRight, speedValue);
  setMotor(rearLeft, speedValue);
  setMotor(rearRight, speedValue);
}

void turnLeft(int speedValue) {
  setMotor(frontLeft, -speedValue);
  setMotor(rearLeft, -speedValue);
  setMotor(frontRight, speedValue);
  setMotor(rearRight, speedValue);
}

void turnRight(int speedValue) {
  setMotor(frontLeft, speedValue);
  setMotor(rearLeft, speedValue);
  setMotor(frontRight, -speedValue);
  setMotor(rearRight, -speedValue);
}

void stopAll() {
  setMotor(frontLeft, 0);
  setMotor(frontRight, 0);
  setMotor(rearLeft, 0);
  setMotor(rearRight, 0);
}

void setMotor(MotorPins motor, int speedValue) {
  speedValue = constrain(speedValue, -255, 255);

  if (speedValue > 0) {
    analogWrite(motor.input1, speedValue);
    analogWrite(motor.input2, 0);
  } else if (speedValue < 0) {
    analogWrite(motor.input1, 0);
    analogWrite(motor.input2, -speedValue);
  } else {
    analogWrite(motor.input1, 0);
    analogWrite(motor.input2, 0);
  }
}
