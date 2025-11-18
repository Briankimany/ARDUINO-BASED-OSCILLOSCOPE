/* 
A program that samples voltage and scales them 
to deduce the voltage and current in a circuit 
*/

float maxVoltage = 5.0;
float RSHUNT = 1;

float channelGains[] = {920.0, 115.0, 14.40 , 1.8};
const int START_CHANNEL = 0;
float currentGain = channelGains[START_CHANNEL];

const float correctionFactor = 1.0;
const float maxMappingValue = 1024.0;
float voltageSensitivity =  maxVoltage /maxMappingValue ;

const int CHANNEL_MSB_PIN = 11;
const int CHANNEL_MID_PIN = 10;
const int CHANNEL_LSB_PIN = 9;
const int ANALOG_READ_PIN = A4;
const int ACTIVE_LOW_ENABLE_MUX_PIN = 12;
const int MEASUREMENT_TRIGGER_PIN = 2;
const int SIGNALTYPEPIN = 8; // A high corrensponds to a dc signal and a low to an ac signal.

const int MAX_CHANNEL = 4;
const float RANGE_MAX_VOLTAGE = 2.3;
const float RANGE_MIN_VOLTAGE = 0.23;

const unsigned long SETTLING_TIME = 1; // in microseconds, since multiplexter used has a propagation of 12nS.
int measurementCount =0;


double calculateCurrentSensitivity(float currentGain) {
  return (maxVoltage / maxMappingValue) / (currentGain * RSHUNT);
}

float scaleVoltage(int value) {
  return maxVoltage * value / (maxMappingValue * correctionFactor);
}

float calculateCurrent(float ivPlus, float ivMinus, bool second) {
  if (second) {
    float scaledPD = scaleVoltage(ivPlus - ivMinus) * 1000;
    //Serial.print("Scaled PD: "); Serial.print(scaledPD); Serial.println(" mV");
    return scaleVoltage(ivPlus - ivMinus) / (currentGain * RSHUNT);
  }
  return scaleVoltage(ivPlus - ivMinus) / RSHUNT;
}

float calculateVoltage(float vPlus, float vMinus) {
  return scaleVoltage(vPlus - vMinus);
}

void writeAddress(int high, int pinNumber) {
  digitalWrite(pinNumber, high ? HIGH : LOW);
}

void setInputChannel(int number) {   
  writeAddress((number >> 2) & 1, CHANNEL_MSB_PIN);
  writeAddress((number >> 1) & 1, CHANNEL_MID_PIN);
  writeAddress(number & 1, CHANNEL_LSB_PIN);
}   

int autoSetRange() {
  float voltage;
  
   for (int currentChannel = 0; currentChannel < MAX_CHANNEL; currentChannel++) {
    setInputChannel(currentChannel);
    delayMicroseconds(SETTLING_TIME);

    voltage = scaleVoltage(analogRead(ANALOG_READ_PIN));
    double channelSensitivity = calculateCurrentSensitivity(channelGains[currentChannel]) * 1e6;
    
    if (voltage <= RANGE_MAX_VOLTAGE && voltage >= RANGE_MIN_VOLTAGE) {
      return currentChannel;
    }

    if (voltage >= RANGE_MAX_VOLTAGE) {
      continue;
    }
    
    if (voltage <= RANGE_MIN_VOLTAGE) {
      break;
    
    }
  
  }

  return -1;
}



void setup() {
  Serial.begin(9600);

  pinMode(MEASUREMENT_TRIGGER_PIN, INPUT_PULLUP);
  pinMode(SIGNALTYPEPIN, INPUT_PULLUP); // Default to measuring dc signals. 

  for (int i = 9; i <= 12; i++) {
    pinMode(i, OUTPUT);
  }

  digitalWrite(ACTIVE_LOW_ENABLE_MUX_PIN, LOW);
  setInputChannel(START_CHANNEL);

}

void loop() {

  int threshold = digitalRead(SIGNALTYPEPIN) ? 2 : 10;

  if (measurementCount == threshold) {
      
      while (digitalRead(MEASUREMENT_TRIGGER_PIN)) {
          measurementCount = 0;
      }
  }


  bool rangeFound =true;

  static double currentSensitivity = calculateCurrentSensitivity(currentGain) * 1e6;

  float scaledVoltage2 = scaleVoltage(analogRead(A4)) * 1000;


  if (scaledVoltage2 > RANGE_MAX_VOLTAGE * 1000 || scaledVoltage2 < RANGE_MIN_VOLTAGE * 1000) {
    int currentChannel = autoSetRange();
    if (currentChannel >=0) {
      currentGain = channelGains[currentChannel];
      currentSensitivity = calculateCurrentSensitivity(currentGain) * 1e6;
      float scaledVoltage2 = scaleVoltage(analogRead(A4)) * 1000;
   
    } else {
      rangeFound=false;
    }
  }

  float vPlus = scaleVoltage(analogRead(A1));
  float vMinus = scaleVoltage(analogRead(A0));
  float ivPlus = scaleVoltage(analogRead(A2));
  float ivMinus = scaleVoltage(analogRead(A3));

  float measuredCurrent = calculateCurrent(analogRead(A2), analogRead(A3), false) * 1000;
  float measuredCurrent2 = calculateCurrent(analogRead(A4), 0, true) * 1000;
  float measuredVoltage = calculateVoltage(analogRead(A1), analogRead(A0)) * 1000;


  float measuredCurrentPrecision = voltageSensitivity /  calculateVoltage(analogRead(A2), analogRead(A3));
  float measuredCurrentPrecision2 =  voltageSensitivity / (scaledVoltage2/1000) ;
  float measuredVoltagePrecision =  voltageSensitivity / (measuredVoltage/1000) ;
 

  // Serial.print("Voltage: " + String(measuredVoltage, 3) + " mV | Accuracy: " + String(max(0,  1-measuredVoltagePrecision) * 100, 6) + "%");
  // Serial.println();
  // Serial.print("Current (Method 1): " + String(measuredCurrent, 3) + " mA | Accuracy: " + String(max(0,   1- measuredCurrentPrecision) * 100, 6) + "%");
  // Serial.println();
  // if (rangeFound){
  //   Serial.print("Current (Method 2): " + String(measuredCurrent2, 3) + " mA | Accuracy: " + String(max(0,  1- measuredCurrentPrecision2) * 100, 6) + "%");
  //   Serial.println();
  // }
  Serial.print(" Serial  <<  Voltage = " +String(measuredVoltage /1000 , 4));
  Serial.println("        Current[A] = "+String(measuredCurrent2/1000 , 4));
  measurementCount++;
}




