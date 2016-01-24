#include <Wire.h>
#include <SDPArduino.h>
#include <SoftwareSerial.h>
#include <SerialCommand.h>
#include <SimpleTimer.h>

SerialCommand sc;
SimpleTimer timer;

void setup() {
  SDPsetup();
  
  sc.addCommand("M", move);
  sc.addCommand("S", stop);
  sc.addCommand("T", transferByte);
  sc.addDefaultHandler(unknown);
}

void loop() {
  timer.run();
  sc.readSerial();
}

void move() {
  int time = atoi(sc.next());
  int count = atoi(sc.next());
  
  for (int i = 0; i < count; ++i) {
    int motor = atoi(sc.next());
    int power = atoi(sc.next());
    
    if (power > 0) {
      motorForward(motor, power);
    } else {
      motorBackward(motor, -power);
    }
  }
  Serial.println("DONE");
  
  delay(time);
  motorAllStop();
}

void stop() {
  motorAllStop();
  Serial.println("DONE");
}

void transferByte() {
  byte value = atoi(sc.next());
  Wire.beginTransmission(69);
  Wire.write(value);
  Wire.endTransmission();
  Serial.print("RECEIVED ");
  Serial.println(value);
}

void unknown() {
  Serial.println("UNKNOWN");
}
