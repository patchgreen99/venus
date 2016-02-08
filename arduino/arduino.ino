#include <Wire.h>
#include <SDPArduino.h>
#include <SoftwareSerial.h>
#include <SerialCommand.h>
#include <SimpleTimer.h>

#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 5
#define ROTARY_REQUEST_INTERVAL 30

#define MOTOR_LEFT 0
#define MOTOR_RIGHT 1
#define MOTOR_TURN 2
#define MOTOR_KICK 3
#define MOTOR_GRAB 4

SerialCommand sc;
SimpleTimer timer;

/* Callbacks to stop nth motor so that we would be able to
 * simply create timeouts for each single motor.
 */
timer_callback stopMotorCallbacks[] = {
  stopMotor0,
  stopMotor1,
  stopMotor2,
  stopMotor3,
  stopMotor4,
  stopMotor5
};

/* Current positions and target positions when moving motors
 * by an amount of rotary units.
 */
int positions[ROTARY_COUNT] = {0};
int targetPositions[ROTARY_COUNT] = {0};


void setup() {
  SDPsetup();
  
  sc.addCommand("M", moveTimeUnits);
  sc.addCommand("R", moveRotaryUnits);
  sc.addCommand("S", stop);
  sc.addCommand("T", transferByte);
  sc.addDefaultHandler(unknown);
  
  timer.setInterval(ROTARY_REQUEST_INTERVAL, rotaryTimerCallback);
}

void loop() {
  timer.run();
  sc.readSerial();
}


/* Used to set timeouts after moving for some time units */
void stopMotor0() { motorStop(0); }
void stopMotor1() { motorStop(1); }
void stopMotor2() { motorStop(2); }
void stopMotor3() { motorStop(3); }
void stopMotor4() { motorStop(4); }
void stopMotor5() { motorStop(5); }
void notifyFinished() { Serial.print('F'); }

/* Callback that stops motors after they moved for some rotary units */
void rotaryTimerCallback() {
  // Request motor position deltas from rotary slave board
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT);
  
  // Update the recorded motor positions
  for (int i = 0; i < ROTARY_COUNT; i++) {
    positions[i] += (int8_t) Wire.read();  // Must cast to signed 8-bit type
  }
  
  bool motorWasStopped = false;
  bool allMotorsAreStopped = true;
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (targetPositions[i] > 0 && positions[i] >= targetPositions[i] ||
        targetPositions[i] < 0 && positions[i] <= targetPositions[i]) {
      motorStop(i);
      positions[i] = 0;
      targetPositions[i] = 0;
      motorWasStopped = true;
    } else if (targetPositions[i]) {
      allMotorsAreStopped = false;
    }
  }
  
  // Acknowledgement that the motion is finished
  if (motorWasStopped && allMotorsAreStopped) {
    Serial.print('F');
  }
}

void moveTimeUnits() {
  Serial.print('D');

  int time = atoi(sc.next()); 
  int count = atoi(sc.next());
  int power[ROTARY_COUNT] = {0};
  
  if (time <= 0) {
    return;
  }

  for (int i = 0; i < count; ++i) {
    int motor = atoi(sc.next());
    power[motor] = atoi(sc.next());
    
    if (power[motor] > 0) {
      motorForward(motor, power[motor]);
    } else {
      motorBackward(motor, -power[motor]);
    }
    
    timer.setTimeout(time, stopMotorCallbacks[motor]);
  }

  // Acknowledgement that the motion is finished
  timer.setTimeout(time, notifyFinished);
}

void moveRotaryUnits() {
  Serial.print('D');

  int target = atoi(sc.next());
  int count = atoi(sc.next());
  int power[ROTARY_COUNT] = {0};
  
  if (target <= 0) {
    return;
  }

  for (int i = 0; i < count; ++i) {
    int motor = atoi(sc.next());
    power[motor] = atoi(sc.next());
    positions[motor] = 0;
    
    if (power[motor] > 0) {
      targetPositions[motor] = target;
      motorForward(motor, power[motor]);
    } else {
      targetPositions[motor] = -target;
      motorBackward(motor, -power[motor]);
    }
  }
}

void stop() {
  Serial.print('D');

  motorAllStop();
}

void transferByte() {
  byte value = atoi(sc.next());
  Wire.beginTransmission(69);
  Wire.write(value);
  Wire.endTransmission();
  
  Serial.print('D');
}

void unknown() {
  Serial.print('U');
}
