const int sensorPin = A0;
const uint8_t sensorID = 0b01; // sensor 2 (binary 01)

void setup() {
  Serial.begin(115200, SERIAL_6N1);
  analogReference(EXTERNAL);
  pinMode(sensorPin, INPUT);
}

void loop() {
  uint16_t pressure = analogRead(sensorPin);  // 10-bit value (0–1023)

  // Ensure pressure is within 10-bit range (safety)
  pressure = pressure & 0x03FF;

  uint8_t byte1 = (pressure >> 4) & 0b00111111;  // [P9 P8 P7 P6 P5 P4]  ← high 6 bits of pressure
  uint8_t byte2 = ((pressure & 0b1111) << 2) | (sensorID & 0b11); // [P3 P2 P1 P0 S1 S0]  ← low 4 pressure bits + 2-bit sensor ID

  // Send as two 6-bit bytes (within 8-bit containers, only 6 bits used)
  Serial.write(byte1); // first byte: P9–P4
  Serial.write(byte2); // second byte: P3–P0 + sensor ID

  delay(100); // Control sample rate
}
