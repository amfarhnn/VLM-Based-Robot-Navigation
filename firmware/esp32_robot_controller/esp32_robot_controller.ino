/*
  ESP32 robot controller for the FYP project:
  Prompt Engineering for Mobile Robot Navigation.

  Role:
  - Read four ultrasonic sensors.
  - Publish JSON distance/status data over USB serial.
  - Receive high-level movement commands.
  - Drive a motor driver for four DC motors.

  The high-level controller can be a Raspberry Pi, Google Dev Board, or a
  development laptop during serial testing.

  Wiring note:
  If HC-SR04-style sensors are powered at 5 V, the Echo pins can output 5 V.
  Use a voltage divider or level shifter before connecting Echo to ESP32 GPIO.

  Pin definitions below are placeholders. Change them to match the selected
  ESP32 board and motor driver.
*/

const unsigned long BAUD_RATE = 115200;
const unsigned long MEASURE_INTERVAL_MS = 100;
const unsigned long COMMAND_TIMEOUT_MS = 1000;
const unsigned long PULSE_TIMEOUT_US = 30000;

const int BASE_SPEED = 90;
const int TURN_SPEED = 80;
const int SEARCH_SPEED = 65;

const int SENSOR_COUNT = 4;
const char* SENSOR_NAMES[SENSOR_COUNT] = {"front", "left", "right", "rear"};

const int TRIG_PINS[SENSOR_COUNT] = {5, 18, 19, 23};
const int ECHO_PINS[SENSOR_COUNT] = {34, 35, 32, 33};

struct MotorPins {
  int pwm;
  int in1;
  int in2;
};

// Placeholder motor-driver pins. Confirm safe pins for the final ESP32 board.
MotorPins frontLeft  = {25, 12, 13};
MotorPins frontRight = {26, 16, 17};
MotorPins rearLeft   = {27, 21, 22};
MotorPins rearRight  = {14, 4, 2};

float safeDistanceCm = 25.0;
float latestDistances[SENSOR_COUNT] = {-1.0, -1.0, -1.0, -1.0};
float latestMinCm = -1.0;
bool latestObstacle = false;

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
}

void loop() {
  handleSerialCommand();

  unsigned long now = millis();
  if (now - lastMeasureMs >= MEASURE_INTERVAL_MS) {
    lastMeasureMs = now;
    updateDistances();
    publishDistances();
  }

  if (latestObstacle || (now - lastCommandMs > COMMAND_TIMEOUT_MS)) {
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
  if (latestObstacle && command != "STOP") {
    stopAll();
    Serial.println("ACK:STOP:OBSTACLE");
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

void updateDistances() {
  float minDistance = 9999.0;

  for (int i = 0; i < SENSOR_COUNT; i++) {
    latestDistances[i] = readDistanceCm(TRIG_PINS[i], ECHO_PINS[i]);
    if (latestDistances[i] > 0.0 && latestDistances[i] < minDistance) {
      minDistance = latestDistances[i];
    }
  }

  latestMinCm = minDistance >= 9999.0 ? -1.0 : minDistance;
  latestObstacle = latestMinCm > 0.0 && latestMinCm < safeDistanceCm;
}

void publishDistances() {
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

void setupMotor(MotorPins motor) {
  pinMode(motor.pwm, OUTPUT);
  pinMode(motor.in1, OUTPUT);
  pinMode(motor.in2, OUTPUT);
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
    digitalWrite(motor.in1, HIGH);
    digitalWrite(motor.in2, LOW);
    analogWrite(motor.pwm, speedValue);
  } else if (speedValue < 0) {
    digitalWrite(motor.in1, LOW);
    digitalWrite(motor.in2, HIGH);
    analogWrite(motor.pwm, -speedValue);
  } else {
    digitalWrite(motor.in1, LOW);
    digitalWrite(motor.in2, LOW);
    analogWrite(motor.pwm, 0);
  }
}

