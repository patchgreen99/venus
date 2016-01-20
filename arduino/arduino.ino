#include <Wire.h>
#include <SDPArduino.h>

void setup() {
  SDPsetup();
}

void loop() {
    Serial.println("Motor forward");
    motorForward(0, 100);
    delay(5000);
    motorAllStop();
}
