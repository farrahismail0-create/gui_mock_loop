/*
  Packet Format:    [0xAA][val1_L][val1_H]...[val4_H][0x55]
  - 1 Start byte:             0xAA
  - 4 analog readings (uint16_t): each sent as 2 bytes [val_L][val_H]
  - 1 End byte:               0x55

  Packet Size:
  - Start byte + (4 values × 2 bytes) + End byte = 1 + 8 + 1 = 10 bytes

  Theoretical Max Speed:
  - UART 115200 baud = ~11,520 bytes/sec
  - 11,520 ÷ 10 = ~1,152 packets/second (ideal max)
  - Realistic: ~500–1000 packets/sec (very efficient)

  Advantages:
  - only 10 bytes per packet
  - Much faster transmission speed (less bandwidth)
  - Ideal for high-frequency data streaming

  Disadvantages:
  - Not human-readable (can’t view in Serial Monitor)
  - Requires byte decoding on Raspberry Pi (e.g., struct.unpack())
*/

const int sensorPin = A0;

void setup() {
  analogReference(EXTERNAL);
  Serial.begin(115200);
  pinMode(sensorPin, INPUT);
}

void loop() {
  uint16_t values[4];
  for (int i = 0; i < 4; i++) {
    values[i] = analogRead(sensorPin);
  }

  Serial.write(0xAA); // Start byte
  for (int i = 0; i < 4; i++) {
    Serial.write(lowByte(values[i]));
    Serial.write(highByte(values[i]));
  }
  Serial.write(0x55); // End byte

  delay(100); // Sample rate control
}
