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
  int time = atoi(sc.next());
  int count = atoi(sc.next());
  
  for (int i = 0; i < count; ++i) {
    int motor = atoi(sc.next());
    int power = atoi(sc.next());
    Serial.println(motor);
    Serial.println(power);
    if (power > 0) {
      motorForward(motor, power);
    } else {
      motorBackward(motor, -power);
    }
  }
    Serial.println(time);
    Serial.println(count);
  Serial.println("DONE");
  
  delay(time);
  motorAllStop();
}

void stop() {
  motorAllStop();
  Serial.println("DONE");
}

void unknown() {
  Serial.println("UNKNOWN");
}
