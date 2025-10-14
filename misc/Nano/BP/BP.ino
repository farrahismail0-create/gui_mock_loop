                

const float vRef = 3.27;    
//const float uMin = 0.42;    // Voltage at 0 mmHg 
//const float uMax = 4.5;    // voltage at max. pressure
//const float pMax = 10.0;   // Max pressure 

void setup() {
  analogReference(EXTERNAL);  //VRef
  Serial.begin(115200);        
  pinMode(A0, INPUT);  
}

void loop() {
  int raw = analogRead(A0);                      
  float voltage = raw * (vRef / 1023.0);        
  //float pressure = (voltage - uMin) * (pMax / (uMax - uMin)); 

  // Ausgabe
  //Serial.print("Value: ");
  //Serial.println(raw);
  //Serial.print(" | voltage: ");
  Serial.println(voltage, 2);
  //Serial.print(" V | pressure: ");
  //Serial.print(pressure, 2);
  //Serial.println(" mmHg");

  delay(500);
}
