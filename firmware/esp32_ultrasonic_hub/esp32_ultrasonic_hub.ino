/*
  ESP32 ultrasonic sensor hub for the FYP robot.

  Role:
  - Read four ultrasonic sensors.
  - Send JSON distance/status data to the selected high-level controller over USB serial.

  Wiring note:
  If HC-SR04-style sensors are powered at 5 V, the Echo pins can output 5 V.
  Use a voltage divider or level shifter before connecting Echo to ESP32 GPIO.
*/

const unsigned long BAUD_RATE = 115200;
const unsigned long MEASURE_INTERVAL_MS = 100;
const unsigned long PULSE_TIMEOUT_US = 30000;

const int SENSOR_COUNT = 4;
const char* SENSOR_NAMES[SENSOR_COUNT] = {"front", "left", "right", "rear"};

// Example pin assignment. Change these pins to match the final wiring.
const int TRIG_PINS[SENSOR_COUNT] = {5, 18, 19, 23};
const int ECHO_PINS[SENSOR_COUNT] = {34, 35, 32, 33};

float safeDistanceCm = 25.0;
unsigned long lastMeasureMs = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  for (int i = 0; i < SENSOR_COUNT; i++) {
    pinMode(TRIG_PINS[i], OUTPUT);
    pinMode(ECHO_PINS[i], INPUT);
    digitalWrite(TRIG_PINS[i], LOW);
  }
}

void loop() {
  handleSerialCommand();

  unsigned long now = millis();
  if (now - lastMeasureMs >= MEASURE_INTERVAL_MS) {
    lastMeasureMs = now;
    publishDistances();
  }
}

void handleSerialCommand() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "PING") {
    Serial.println("{\"status\":\"ok\",\"device\":\"esp32_ultrasonic_hub\"}");
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

void publishDistances() {
  float distances[SENSOR_COUNT];
  float minDistance = 9999.0;
  bool obstacle = false;

  for (int i = 0; i < SENSOR_COUNT; i++) {
    distances[i] = readDistanceCm(TRIG_PINS[i], ECHO_PINS[i]);
    if (distances[i] > 0.0 && distances[i] < minDistance) {
      minDistance = distances[i];
    }
  }

  if (minDistance < safeDistanceCm) {
    obstacle = true;
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

  // HC-SR04 approximation: distance in cm = echo time in microseconds / 58.
  return duration / 58.0;
}
