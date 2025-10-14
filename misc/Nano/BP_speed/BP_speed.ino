                

const float vRef = 3.27;    
//const float uMin = 0.42;    // Voltage at 0 mmHg 
//const float uMax = 4.5;    // voltage at max. pressure
//const float pMax = 10.0;   // Max pressure 
int toggle_pin = 7;

void setup() {
  analogReference(EXTERNAL);  //VRef
  Serial.begin(115200);        
  pinMode(A0, INPUT);  

  pinMode(toggle_pin, OUTPUT);
  digitalWrite(toggle_pin, LOW);
}

void loop() {
  int raw = analogRead(A0);                      
  float voltage = raw * (vRef / 1023.0);        
  //float pressure = (voltage - uMin) * (pMax / (uMax - uMin)); 
  //Serial.println(voltage, 2);


  int raw1 = analogRead(A0);                      
  float voltage1 = raw1 * (vRef / 1023.0);  
  // Ausgabe
  //Serial.print("Value: ");
  //Serial.println(raw);
  //Serial.print(" | voltage: ");
  Serial.println(voltage1, 2);
  
  //Serial.print(" V | pressure: ");
  //Serial.print(pressure, 2);
  //Serial.println(" mmHg");

  int raw2 = analogRead(A0);                      
  float voltage2 = raw2 * (vRef / 1023.0);        
  //float pressure = (voltage - uMin) * (pMax / (uMax - uMin)); 
  Serial.println(voltage2, 2);

  int raw3 = analogRead(A0);                      
  float voltage3 = raw3 * (vRef / 1023.0);        
  //float pressure = (voltage - uMin) * (pMax / (uMax - uMin)); 
  Serial.println(voltage3, 2);

  delay(500);
  digitalWrite(toggle_pin, !digitalRead(toggle_pin));

}
