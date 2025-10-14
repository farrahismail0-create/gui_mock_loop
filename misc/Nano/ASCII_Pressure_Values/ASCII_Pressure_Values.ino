/*
  ASCII Packet Sender – Arduino to Raspberry Pi via USB Serial (115200 baud, 8N1)

  Packet Format (example):    #1.56,1.59,1.60,1.58;
  - Start marker:             '#'
  - 4 float values as voltage with 2 decimal places
  - Comma-separated
  - End marker:               ';'
  - Line ends with '\n' (from println) .....

  Packet Size Estimate:
  - ~4 characters per float × 4 values = ~16 chars
  - +3 commas + '#' + ';' = ~21 bytes per packet

  Theoretical Max Speed:
  - UART 115200 baud = ~11,520 bytes/sec
  - 11,520 ÷ 21 ≈ ~548 packets/second (ideal max)
  - Realistic: 50–200 packets/sec due to delays

  Advantages:
  - Easy to debug (human-readable in Serial Monitor)
  - Simple to log and parse on Raspberry Pi (split string)

  Disadvantages:
  - Less efficient (string overhead: digits, decimal points, commas, markers)
  - Slower than binary (larger packets)
*/

const float vRef = 3.27;    
const int sensorPin = A0;
const int toggle_pin = 7;

void setup() {
  analogReference(EXTERNAL);  // Make sure AREF is connected to 3.27V
  Serial.begin(115200);
  pinMode(sensorPin, INPUT);
  pinMode(toggle_pin, OUTPUT);
  digitalWrite(toggle_pin, LOW);
}

void loop() {
  float readings[4];
  
  for (int i = 0; i < 4; i++) {
    int raw = analogRead(sensorPin);
    readings[i] = raw * (vRef / 1023.0);
  }

  // Send all 4 values as one ASCII packet
  Serial.print("#");
  for (int i = 0; i < 4; i++) {
    Serial.print(readings[i], 2); // 2 decimal places
    if (i < 3) Serial.print(","); // comma between values
  }
  Serial.println(";");     

  // Toggle LED or pin for testing
  digitalWrite(toggle_pin, !digitalRead(toggle_pin));

  delay(100);  // adjust sampling rate as needed
}
