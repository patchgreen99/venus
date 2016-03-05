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

#define RESP_DONE 'D'
#define RESP_UNKNOWN 'U'

SerialCommand sc;
SimpleTimer timer;

/* Values for repeated message checking */
int lastSeqNo = -1;
bool lastDone;

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
int positions[ROTARY_COUNT];
int targetPositions[ROTARY_COUNT];

/* Whether motors are moving by an amount of time units */
bool moving[ROTARY_COUNT];

void setup() {
  SDPsetup();
  
  sc.addCommand("M", moveTimeUnits);
  sc.addCommand("R", moveRotaryUnits);
  sc.addCommand("V", moveForever);
  sc.addCommand("Z", stopSome);
  sc.addCommand("S", stopAll);
  sc.addCommand("I", areAllStopped);
  sc.addCommand("Y", isOneStopped);
  sc.addCommand("T", transferByte);
  sc.addDefaultHandler(unknown);
  
  timer.setInterval(ROTARY_REQUEST_INTERVAL, rotaryTimerCallback);
}

void loop() {
  timer.run();
  sc.readSerial();
}

/* Used to set timeouts after moving for some time units */
void stopMotor0() { motorStop(0); moving[0] = false; }
void stopMotor1() { motorStop(1); moving[1] = false; }
void stopMotor2() { motorStop(2); moving[2] = false; }
void stopMotor3() { motorStop(3); moving[3] = false; }
void stopMotor4() { motorStop(4); moving[4] = false; }
void stopMotor5() { motorStop(5); moving[5] = false; }

/* Callback that stops motors after they moved for some rotary units */
void rotaryTimerCallback() {
  // Request motor position deltas from rotary slave board
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT);
  
  // Update the recorded motor positions
  for (int i = 0; i < ROTARY_COUNT; i++) {
    positions[i] += (int8_t) Wire.read();  // Must cast to signed 8-bit type
  }
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (targetPositions[i] > 0 && positions[i] >= targetPositions[i] ||
        targetPositions[i] < 0 && positions[i] <= targetPositions[i]) {
      motorStop(i);
      positions[i] = 0;
      targetPositions[i] = 0;
    }
  }
}

/* Returns true if the command should be ignored (duplicate command) */
bool ignore() {
  int seqNo = atoi(sc.next());
  
  if (seqNo == lastSeqNo) {
    if (lastDone) {
      Serial.print(RESP_DONE);
    }
    return true;
  } else {
    lastSeqNo = seqNo;
    lastDone = false;
    return false;
  }
}

/* Inform that command is done */
void done() {
  lastDone = true;
  Serial.print(RESP_DONE);
}

void moveForever() {
  if (ignore()) {
    return;
  }
  
  while (char *ch = sc.next()) {
    int motor = atoi(ch);
    int power = atoi(sc.next());
    
    if (power > 0) {
      motorForward(motor, power);
    } else {
      motorBackward(motor, -power);
    }
  }
  
  done();
}

void moveTimeUnits() {
  if (ignore()) {
    return;
  }

  int time = atoi(sc.next());

  while (char *ch = sc.next()) {
    int motor = atoi(ch);
    int power = atoi(sc.next());
    
    if (power > 0) {
      motorForward(motor, power);
    } else {
      motorBackward(motor, -power);
    }
    
    moving[motor] = true;
    
    // Use timeout to make moveTimeUnits non-blocking
    timer.setTimeout(time, stopMotorCallbacks[motor]);
  }
  
  done();
}

void moveRotaryUnits() {
  if (ignore()) {
    return;
  }

  int target = atoi(sc.next());

  while (char *ch = sc.next()) {
    int motor = atoi(ch);
    int power = atoi(sc.next());
    positions[motor] = 0;
    
    if (power > 0) {
      targetPositions[motor] = target;
      motorForward(motor, power);
    } else {
      targetPositions[motor] = -target;
      motorBackward(motor, -power);
    }
  }
  
  done();
}

void stopSome() {
  if (ignore()) {
    return;
  }
  
  while (char *ch = sc.next()) {
    int motor = atoi(ch);
    
    motorStop(motor);
  }
  
  done();
}

void stopAll() {
  if (ignore()) {
    return;
  }
  
  motorAllStop();
  
  done();
}

void areAllStopped() {
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (targetPositions[i] || moving[i]) {
      return;
    }
  }
  
  Serial.print(RESP_DONE);
}

void isOneStopped() {
  int motor = atoi(sc.next());
  
  if (targetPositions[motor] || moving[motor]) {
    return;
  }
  
  Serial.print(RESP_DONE);
}

void transferByte() {
  if (ignore()) {
    return;
  }
  
  byte value = atoi(sc.next());
  Wire.beginTransmission(69);
  Wire.write(value);
  Wire.endTransmission();
  
  done();
}

void unknown() {
  Serial.print(RESP_UNKNOWN);
}
