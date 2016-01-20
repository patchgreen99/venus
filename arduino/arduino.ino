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
  sc.addDefaultHandler(unknown);
}

void loop() {
  timer.run();
  sc.readSerial();
}

void move() {
  int num = atoi(sc.next());
  int direction = atoi(sc.next());
  int power = atoi(sc.next());
  int time = atoi(sc.next());
  
  if (direction) {
    motorForward(num, power);
  } else {
    motorBackward(num, power);
  }
  Serial.println("DONE");
  
  delay(time);
  motorStop(num);
}

void stop() {
  motorAllStop();
  Serial.println("DONE");
}

void unknown() {
  Serial.println("UNKNOWN");
}
