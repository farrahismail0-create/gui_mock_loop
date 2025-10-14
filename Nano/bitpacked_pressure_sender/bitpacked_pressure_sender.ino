/*
  Binary Protocol – 2 bytes per sensor reading
  Byte format: [5 bits pressure] [2 bits sensor ID] [1 bit flag]
  - Flag = 0 → low byte (P4–P0)
  - Flag = 1 → high byte (P9–P5)
*/

const int sensorPins[3] = {A0, A1, A2};  // Sensor 1, 2, 3

//unsigned long startTime;
//unsigned long endTime;
//unsigned long time;


void setup() {
  Serial.begin(115200);  // Standard 8N1
  analogReference(EXTERNAL);

  for (int i = 0; i < 3; i++) {
    pinMode(sensorPins[i], INPUT);
  }
}

// Sends two bytes for one sensor reading
void sendSensorData(uint16_t pressure, uint8_t sensorID) {
  pressure &= 0x03FF;         // Ensure it's 10 bits
  sensorID &= 0x03;           // Max 2-bit sensor ID

  uint8_t highBits = (pressure >> 5) & 0b00011111;  // P9–P5
  uint8_t lowBits  = pressure & 0b00011111;         // P4–P0

  uint8_t lowByte  = (lowBits << 3)  | (sensorID << 1) | 0;  // flag 0 = low byte
  uint8_t highByte = (highBits << 3) | (sensorID << 1) | 1;  // flag 1 = high byte

  Serial.write(lowByte);
  Serial.write(highByte);
}

void loop() {
  
  //startTime = micros();

  // Sensor 1 (A0)
  uint16_t p0 = analogRead(sensorPins[0]);
  sendSensorData(p0, 0);  // Sensor ID = 0 (00)
  // Sensor 2 (A1)
  uint16_t p1 = analogRead(sensorPins[1]);
  sendSensorData(p1, 1);  // Sensor ID = 1 (01)
  // Sensor 3 (A2)
  uint16_t p2 = analogRead(sensorPins[2]);
  sendSensorData(p2, 2);  // Sensor ID = 2 (10)

  delay(1);
  
  //endTime = micros();

  //time = endTime - startTime;

  //Serial.print(" time: ");Serial.print(time);Serial.println(" milliseconds");

}
