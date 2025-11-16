/* 
A program that samples voltage and scales them 
to deduce the voltage and current in a circuit 
*/

float maxVoltage = 5.0;
float RSHUNT = 0.1;

float channelGains[] = {1003.0 ,501.0 ,100.0 ,9.998 , 5015.0};
const int START_CHANNEL = 0;
float currentGain = channelGains[START_CHANNEL];

const float correctionFactor = 1.0;
const float maxMappingValue = 1024.0;

const int CHANNEL_MSB_PIN = 11;
const int CHANNEL_MID_PIN = 10;
const int CHANNEL_LSB_PIN = 9;
const int ANALOG_READ_PIN = A4;
const int ACTIVE_LOW_ENABLE_MUX_PIN = 12;
const int MEASUREMENT_TRIGGER_PIN =  2;

const int MAX_CHANNEL = 8;
const float RANGE_MAX_VOLTAGE = 4.5;
const float RANGE_MIN_VOLTAGE = 0.3;


const unsigned long SETTLING_TIME = 50;


double calculateCurrentSensitivity (float currentGain) {
  /*
  Calculates the current channel's current sensitivity .
  given by (maxVoltage / maxMappingValue)  / (CurrentGain * RSHUNT).
  */
  return  (maxVoltage / maxMappingValue) / (currentGain * RSHUNT);

}

float scaleVoltage(int value) {
  return maxVoltage * value / (maxMappingValue * correctionFactor);
}

float calculateCurrent(float ivPlus ,float ivMinus ,bool second) {
  if (second) {
    Serial.print(" Scaled pd is: ");
    Serial.println( scaleVoltage(ivPlus-ivMinus)*1000);
    return scaleVoltage(ivPlus-ivMinus) / (currentGain * RSHUNT);
  }
  return (scaleVoltage(ivPlus - ivMinus)) / RSHUNT;
}

float calculateVoltage (float vPlus, float vMinus ) {
  return scaleVoltage(vPlus - vMinus);
}

void writeAddress(int high, int pinNumber) {
  digitalWrite(pinNumber, high ? HIGH : LOW);
}

void setInputChannel(int number) {   
  writeAddress((number >> 2) & 1, CHANNEL_MSB_PIN);  // MSB
  writeAddress((number >> 1) & 1, CHANNEL_MID_PIN);
  writeAddress(number & 1, CHANNEL_LSB_PIN);         // LSB
}   

int autoSetRange() {
  float voltage;
  int currentChannel = START_CHANNEL;
  
  while (currentChannel < MAX_CHANNEL) {

    setInputChannel(currentChannel);
    delay(SETTLING_TIME);

    voltage = scaleVoltage(analogRead(ANALOG_READ_PIN));
    double channelSensitivity =  calculateCurrentSensitivity(channelGains[currentChannel]) * pow(10 ,6);

    Serial.println(currentChannel);
    Serial.print("Auto-range testing channel ");
    Serial.print(currentChannel);
    Serial.print(": ");
    Serial.print(" Sensitivity: ");
    Serial.print(channelSensitivity);
    Serial.print(" uA , ");
    Serial.print("Voltage: ");
    Serial.print(voltage);
    Serial.println("V");
    
    if (voltage < RANGE_MAX_VOLTAGE && voltage > RANGE_MIN_VOLTAGE) {
      Serial.print("Selected channel: ");
      Serial.println(currentChannel);
      return currentChannel;
    }
    
    Serial.println("Testing the next channel");
    currentChannel++;
  }
  
  Serial.println("Auto-range: Using default channel 4");
  return START_CHANNEL;
}

void setup (){
  Serial.begin(9600);
  Serial.println("Dmm running");

  pinMode(MEASUREMENT_TRIGGER_PIN ,INPUT_PULLUP);

  for (int i = 9; i <= 12; i++) {
    pinMode(i, OUTPUT);
  }
  
  digitalWrite(ACTIVE_LOW_ENABLE_MUX_PIN, LOW);
  setInputChannel(START_CHANNEL);
  
}

void loop() {

  while (digitalRead(MEASUREMENT_TRIGGER_PIN)) {}

  double static currentSensitivity = calculateCurrentSensitivity(currentGain) * pow(10 , 6);

  float  vPlus = scaleVoltage(analogRead(A1));
  float  vMinus = scaleVoltage(analogRead(A0));
  float  ivPlus = scaleVoltage(analogRead(A2));
  float  ivMinus = scaleVoltage(analogRead(A3));

  float scaledVoltage2 = scaleVoltage(analogRead(A4)) * 1000;

  if (scaledVoltage2 > RANGE_MAX_VOLTAGE *1000 || scaledVoltage2 < RANGE_MIN_VOLTAGE *1000) {

    int currentChannel = autoSetRange();
    currentGain = channelGains[currentChannel];
    currentSensitivity = calculateCurrentSensitivity(currentGain) * pow(10 , 6);

    Serial.print("Auto Adjusted the input range:");

    float scaledVoltage2 = scaleVoltage(analogRead(A4)) * 1000;

  }
    
  float measuredCurrent = calculateCurrent(analogRead(A2), analogRead(A3), false) * 1000;
  float measuredCurrent2 = calculateCurrent(analogRead(A4), 0, true) * 1000;
  
  
  Serial.print("Pin 4 analog value: ");
  Serial.println(analogRead(A4));
  Serial.print("Current sensitivity: ");
  Serial.print(currentSensitivity);
  Serial.println(" uA");

  float measuredVoltage = calculateVoltage(analogRead(A1), analogRead(A0)) * 1000;
  
  Serial.print("V+: ");
  Serial.print(vPlus);
  Serial.print(" V-: ");
  Serial.println(vMinus);
  
  Serial.print("I+: ");
  Serial.print(ivPlus);
  Serial.print(" I-: ");
  Serial.println(ivMinus);
  
  Serial.print("I2+: ");
  Serial.print(scaledVoltage2);
  Serial.print(" mV");
  Serial.print(" I2-: ");
  Serial.println(0);
  
  Serial.print("Vd = : ");
  Serial.print(measuredVoltage);
  Serial.print(" Ic: ");
  Serial.println(measuredCurrent);
  
  Serial.print("Vd2 = : ");
  Serial.print(measuredVoltage);
  Serial.print(" mV");
  Serial.print(" Ic2: ");
  Serial.println(measuredCurrent2);
  Serial.println("+++++++++");

  delay(10);
}