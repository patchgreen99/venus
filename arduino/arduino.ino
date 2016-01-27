#include <Wire.h>
#include <SDPArduino.h>
#include <SoftwareSerial.h>
#include <SerialCommand.h>
#include <SimpleTimer.h>

#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 4

#define MOTOR_LEFT 0
#define MOTOR_RIGHT 1
#define MOTOR_TURN 2
#define MOTOR_KICK 3

SerialCommand sc;
SimpleTimer timer;

int positions[ROTARY_COUNT] = {0};

void setup() {
  SDPsetup();
  
  sc.addCommand("M", moveTimeUnits);
  sc.addCommand("R", moveRotaryUnits);
  sc.addCommand("S", stop);
  sc.addCommand("T", transferByte);
  sc.addDefaultHandler(unknown);
}

void loop() {
  timer.run();
  sc.readSerial();
}

void updateMotorPositions() {
  // Request motor position deltas from rotary slave board
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT);
  
  // Update the recorded motor positions
  for (int i = 0; i < ROTARY_COUNT; i++) {
    positions[i] = (int8_t) Wire.read();  // Must cast to signed 8-bit type
  }
}

void moveTimeUnits() {
  int time = atoi(sc.next());
  int count = atoi(sc.next());
  int power[ROTARY_COUNT] = {0};

  for (int i = 0; i < count; ++i) {
    int motor = atoi(sc.next());
    power[motor] = atoi(sc.next());
    
    if (power[motor] > 0) {
      motorForward(motor, power[motor]);
    } else {
      motorBackward(motor, -power[motor]);
    }
  }
  
  delay(time);
  
  motorAllStop();
  
  Serial.println("DONE");
}

void moveRotaryUnits() {
  int target = atoi(sc.next());
  int count = atoi(sc.next());
  int power[ROTARY_COUNT] = {0};
  
  updateMotorPositions();  // Reset the counters in encoders

  for (int i = 0; i < count; ++i) {
    int motor = atoi(sc.next());
    power[motor] = atoi(sc.next());
    
    if (power[motor] > 0) {
      motorForward(motor, power[motor]);
    } else {
      motorBackward(motor, -power[motor]);
    }
  }
  
  int current[ROTARY_COUNT] = {0};
  int count_completed;
  do {
    delay(30);
    
    updateMotorPositions();
    
    count_completed = 0;
    for (int i = 0; i < ROTARY_COUNT; ++i) {
      if (power[i] > 0) {
        current[i] += positions[i];
      } else if (power[i] < 0) {
        current[i] -= positions[i];
      }
      
      if (power[i] != 0 && positions[i] >= target) {
        ++count_completed;
        motorStop(i);
      }
    }
  } while (count_completed < count);
  
  // This is the 'go to the other direction' stop trick
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (power[i] > 0) {
      motorBackward(i, 100);
    } else if (power[i] < 0) {
      motorForward(i, 100);
    }
  }
  delay(20);
  motorAllStop();
  
  Serial.println("DONE");
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
  
  Serial.println("DONE");
}

void unknown() {
  Serial.println("UNKNOWN");
}
