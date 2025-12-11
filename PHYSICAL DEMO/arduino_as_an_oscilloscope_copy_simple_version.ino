/*
A program that samples values from a circuit 
and converts their digital representations
to analog for plotting.

*/

float maxVoltage = 5000.0;
float currentRSeries = 0.5;
const float currentGain = 1003;

const float correctionFactor = 1.0;
const float maxMappingValue =  1023.0;
unsigned long SENDING_INTERVAL_MICROS =  500;


float scaleVoltage(int value) {
	return maxVoltage * value / (maxMappingValue * correctionFactor);
}

float calculateCurrent(float ivPlus ,float ivMinus ,bool second) {

  if (second) {
    // Serial.println( scaleVoltage(ivPlus-ivMinus)*1000);
    return scaleVoltage(ivPlus-ivMinus) / (currentGain * currentRSeries);
  }
  return (scaleVoltage(ivPlus - ivMinus)) / currentRSeries;
}

float calculateVoltage (float vPlus, float vMinus ) {
	// Method 1
  	return scaleVoltage(vPlus - vMinus);
}

void setup (){
  Serial.begin(57600);
}

void loop() {
	static unsigned long lastSendTime = 0;
	unsigned long now = micros();
  
	float v0 = scaleVoltage(analogRead(A0));
	float v1 = scaleVoltage(analogRead(A1));
	float v2 = scaleVoltage(analogRead(A2));
	float v3 = scaleVoltage(analogRead(A3));
 
  
	if (now - lastSendTime >= SENDING_INTERVAL_MICROS) {
		lastSendTime = now;
		
		Serial.print("V0 = ");
		Serial.print(v0, 4);
		Serial.print(" V1 = ");
		Serial.print(v1, 4); 
		Serial.print(" V2 = ");
		Serial.print(v2, 4);
		Serial.print(" V3 = ");
		Serial.print(v3, 4);
		Serial.print(" T = ");
		Serial.println(now/1000);
	}

}
