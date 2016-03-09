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
#define RESP_ERROR_CHECKSUM 'C'
#define RESP_ERROR_JOBS_EXCEEDED 'X'

#define MAX_JOB_COUNT 10

#define MAX_PARAMS 30

SerialCommand sc;
SimpleTimer timer;

/* Values for repeated message checking */
int lastSeqNo = -1;

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

struct Job {
  bool pause;
  int target;
  int master;
  int powers[ROTARY_COUNT];
};

Job jobs[MAX_JOB_COUNT];
bool running;
bool pauseFinished;
int head;
int tail;
int count;

int params[MAX_PARAMS];
int paramCount;

void setup() {
  SDPsetup();
  
  sc.addCommand("M", moveTimeUnits);
  sc.addCommand("R", moveRotaryUnits);
  sc.addCommand("V", moveForever);
  sc.addCommand("J", scheduleJob);
  sc.addCommand("P", schedulePause);
  sc.addCommand("Z", stopSome);
  sc.addCommand("S", stopAll);
  sc.addCommand("I", areAllStopped);
  sc.addCommand("Y", isOneStopped);
  sc.addCommand("T", transferByte);
  sc.addCommand("H", handshake);
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
  updateRotaryPositions();
  
  bool stopping = running && (jobs[head].pause && pauseFinished || !jobs[head].pause && finished(positions[jobs[head].master], jobs[head].target));
  bool starting = !running && count > 0 || stopping && count > 1;
  
  int next = stopping ? (head + 1) % MAX_JOB_COUNT : head;
  
  if (starting && jobs[next].pause) {
    timer.setTimeout(jobs[next].target, setPauseFinished);
  }
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (starting && jobs[next].powers[i]) {
      positions[i] = 0;
      if (jobs[next].powers[i] > 0) {
        motorForward(i, jobs[next].powers[i]);
      } else {
        motorBackward(i, -jobs[next].powers[i]);
      }
    } else if (stopping && jobs[head].powers[i]) {
      positions[i] = 0;
      motorStop(i);
      
      // Moving motors in other direction hoping to stop them quickly
      /*if (jobs[head].powers[i] > 0) {
        motorBackward(i, 100);
      } else {
        motorForward(i, 100);
      }
      timer.setTimeout(400, stopMotorCallbacks[i]);*/
    }
  }
  
  if (stopping) {
    --count;
    head = next;
  }
  
  running = running && !stopping || starting;
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (finished(positions[i], targetPositions[i])) {
      motorStop(i);
      positions[i] = 0;
      targetPositions[i] = 0;
    }
  }
}

void setPauseFinished() {
  pauseFinished = true;
}

void updateRotaryPositions() {
  // Request motor position deltas from rotary slave board
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT);
  
  // Update the recorded motor positions
  for (int i = 0; i < ROTARY_COUNT; i++) {
    positions[i] += (int8_t) Wire.read();  // Must cast to signed 8-bit type
  }
}

bool finished(int position, int targetPosition) {
  return targetPosition > 0 && position >= targetPosition ||
         targetPosition < 0 && position <= targetPosition;
}

/* Returns true if the command should be ignored in case
 * it is a duplicate command or bad checksum */
bool ignore() {  
  int seqNo = atoi(sc.next());
  if (seqNo == lastSeqNo) {
    return true;
  }
  
  int checksum = atoi(sc.next());
  
  int sum = 0;
  paramCount = 0;
  while (char *token = sc.next()) {
    params[paramCount] = atoi(token);
    sum += abs(params[paramCount]);
    ++paramCount;
  }
  if (checksum != sum) {
    Serial.print(RESP_ERROR_CHECKSUM);
    return true;
  }
  
  Serial.print(RESP_DONE);
  lastSeqNo = seqNo;
  return false;
}

void moveForever() {
  if (ignore()) {
    return;
  }
  
  int i = 0;
  while (i < paramCount) {
    int motor = params[i++];
    int power = params[i++];
    
    if (power > 0) {
      motorForward(motor, power);
    } else {
      motorBackward(motor, -power);
    }
  }
}

void moveTimeUnits() {
  if (ignore()) {
    return;
  }
  
  int p = 0;
  int time = params[p++];

  while (p < paramCount) {
    int motor = params[p++];
    int power = params[p++];
    
    if (power > 0) {
      motorForward(motor, power);
    } else {
      motorBackward(motor, -power);
    }
    
    moving[motor] = true;
    
    // Use timeout to make moveTimeUnits non-blocking
    timer.setTimeout(time, stopMotorCallbacks[motor]);
  }
}

void moveRotaryUnits() {
  if (ignore()) {
    return;
  }
  
  int p = 0;
  int target = params[p++];

  while (p < paramCount) {
    int motor = params[p++];
    int power = params[p++];
    positions[motor] = 0;
    
    if (power > 0) {
      targetPositions[motor] = target;
      motorForward(motor, power);
    } else {
      targetPositions[motor] = -target;
      motorBackward(motor, -power);
    }
  }
}

void scheduleJob() {
  if (count == MAX_JOB_COUNT) {
    // No more space in the job queue
    Serial.print(RESP_ERROR_JOBS_EXCEEDED);
    return;
  }
  
  if (ignore()) {
    return;
  }
  
  int p = 0;
  jobs[tail].pause = false;
  jobs[tail].target = params[p++];
  jobs[tail].master = params[p++];
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    jobs[tail].powers[i] = 0;
  }
  
  while (p < paramCount) {
    int motor = params[p++];
    jobs[tail].powers[motor] = params[p++];
  }
  
  if (jobs[tail].powers[jobs[tail].master] < 0) {
    jobs[tail].target *= -1;
  }
  
  ++count;
  tail = (tail + 1) % MAX_JOB_COUNT;
}

void schedulePause() {
  if (count == MAX_JOB_COUNT) {
    // No more space in the job queue
    Serial.print(RESP_ERROR_JOBS_EXCEEDED);
    return;
  }
  
  if (ignore()) {
    return;
  }
  
  jobs[tail].pause = true;
  jobs[tail].target = params[0];
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    jobs[tail].powers[i] = 0;
  }
  
  ++count;
  tail = (tail + 1) % MAX_JOB_COUNT;
}

void stopSome() {
  if (ignore()) {
    return;
  }
  
  int p = 0;
  while (p < paramCount) {
    int motor = params[p++];
    
    motorStop(motor);
  }
}

void stopAll() {
  if (ignore()) {
    return;
  }
  
  motorAllStop();
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
  
  byte value = params[0];
  Wire.beginTransmission(69);
  Wire.write(value);
  Wire.endTransmission();
}

void handshake() {
  lastSeqNo = -1;
  Serial.print(RESP_DONE);
}

void unknown() {
  Serial.print(RESP_UNKNOWN);
}
