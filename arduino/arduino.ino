#include <Wire.h>
#include <SDPArduino.h>
#include <SoftwareSerial.h>
#include <SerialCommand.h>
#include <SimpleTimer.h>

#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 5
#define ROTARY_REQUEST_INTERVAL 30

#define RECEIVER_SLAVE_ADDRESS 69
#define BALL_SENSOR_ANALOG_PORT 0
#define BALL_SENSOR_SLAVE_ADDRESS 57

#define MOTOR_LEFT 0
#define MOTOR_RIGHT 1
#define MOTOR_TURN 2
#define MOTOR_KICK 3
#define MOTOR_GRAB 4

#define RESP_DONE 'D'
#define RESP_NEGATIVE 'N'
#define RESP_ERROR_COMMAND_UNKNOWN 'U'
#define RESP_ERROR_CHECKSUM 'C'
#define RESP_ERROR_JOBS_EXCEEDED 'X'

#define MAX_JOB_COUNT 20
#define JOB_MOTOR_COUNT 3

#define MAX_PARAMS 15

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
  stopMotor4
};

/* Current positions and target positions when moving motors
 * by an amount of rotary units.
 */
int positions[ROTARY_COUNT];
int targetPositions[ROTARY_COUNT];

/* Whether motors are moving in any way */
bool moving[ROTARY_COUNT];

struct Job {
  bool pause;
  int target;
  int master;
  int grab;
  int powers[JOB_MOTOR_COUNT];
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
  
  Wire.begin();
  Wire.beginTransmission(57);
  Wire.write(0x43);
  delay(100);
  Wire.write(0x18);
  delay(100);
  Wire.write(0x03);
  delay(100);
  Wire.endTransmission();
  
  sc.addCommand("M", moveTimeUnits);
  sc.addCommand("R", moveRotaryUnits);
  sc.addCommand("V", moveForever);
  sc.addCommand("J", scheduleJob);
  sc.addCommand("P", schedulePause);
  sc.addCommand("F", flushJobs);
  //sc.addCommand("Z", stopSome);
  sc.addCommand("S", stopAll);
  sc.addCommand("I", areAllStopped);
  sc.addCommand("Y", isOneStopped);
  //sc.addCommand("T", transferByte);
  sc.addCommand("H", handshake);
  sc.addCommand("A", queryBallSensor);
  sc.addDefaultHandler(unknown);
  
  timer.setInterval(ROTARY_REQUEST_INTERVAL, rotaryTimerCallback);
}


/*
void setup(){
    
  Serial.begin(112500);
  Wire.begin();
  Wire.beginTransmission(57);
  Wire.write(0x43);
  delay(100);
  Wire.write(0x18);
  delay(100);
  Wire.write(0x03);
  delay(100);
  Wire.endTransmission();
}
*/

void done() {
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
  Serial.print(RESP_DONE);
}

void loop(){
  timer.run();
  sc.readSerial();
  //queryBallSensor();
}

void stopMotor(int i) {
  motorStop(i);
  moving[i] = false;
}

void runMotor(int i, int power) {
  if (power > 0) {
    motorForward(i, power);
  } else {
    motorBackward(i, -power);
  }
  moving[i] = true;
}

/* Used to set timeouts after moving for some time units */
void stopMotor0() { stopMotor(0); }
void stopMotor1() { stopMotor(1); }
void stopMotor2() { stopMotor(2); }
void stopMotor3() { stopMotor(3); }
void stopMotor4() { stopMotor(4); }

/* Callback that stops motors after they moved for some rotary units */
void rotaryTimerCallback() {
  updateRotaryPositions();
  
  bool stopping = running && (jobs[head].pause && pauseFinished || !jobs[head].pause && finished(positions[jobs[head].master], jobs[head].target));
  bool starting = !running && count > 0 || stopping && count > 1;
  
  int next = stopping ? (head + 1) % MAX_JOB_COUNT : head;
  
  if (starting && jobs[next].pause) {
    timer.setTimeout(jobs[next].target, setPauseFinished);
  }
  
  for (int i = 0; i < JOB_MOTOR_COUNT; ++i) {
    if (starting && jobs[next].powers[i]) {
      positions[i] = 0;
      runMotor(i, jobs[next].powers[i]);
    } else if (stopping && jobs[head].powers[i]) {
      positions[i] = 0;
      stopMotor(i);
      
      // Moving motors in other direction hoping to stop them quickly
      /*if (jobs[head].powers[i] > 0) {
        motorBackward(i, 100);
      } else {
        motorForward(i, 100);
      }
      timer.setTimeout(400, stopMotorCallbacks[i]);*/
    }
  }
  
  if (starting && jobs[next].grab) {
    if (jobs[next].grab > 0) {
      runMotor(MOTOR_GRAB, 100);
    } else {
      runMotor(MOTOR_GRAB, -100);
    }
    timer.setTimeout(abs(jobs[next].grab), stopMotor4);
  }
  
  if (stopping) {
    --count;
    head = next;
  }
  
  running = running && !stopping || starting;
  
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (finished(positions[i], targetPositions[i])) {
      motorAllStop();
      for (int j = 0; j < ROTARY_COUNT; ++j) {
        moving[j] = false;
        positions[j] = 0;
        targetPositions[j] = 0;
      }
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
    done();
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
  
  done();
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
    
    runMotor(motor, power);
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
    
    runMotor(motor, power);
    
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
  
  int motor = params[p++];
  int power = params[p++];
  positions[motor] = 0;
  
  if (power > 0) {
    targetPositions[motor] = target;
  } else {
    targetPositions[motor] = -target;
  }
  
  runMotor(motor, power);

  while (p < paramCount) {
    int motor = params[p++];
    int power = params[p++];
    positions[motor] = 0;
    
    runMotor(motor, power);
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
  jobs[tail].grab = params[p++];
  
  for (int i = 0; i < JOB_MOTOR_COUNT; ++i) {
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
  
  for (int i = 0; i < JOB_MOTOR_COUNT; ++i) {
    jobs[tail].powers[i] = 0;
  }
  
  ++count;
  tail = (tail + 1) % MAX_JOB_COUNT;
}

void flushJobs() {
  if (ignore()) {
    return;
  }
  
  if (count > 1) {
    count = 1;
    tail = (head + 1) % MAX_JOB_COUNT;
  }
}

/*void stopSome() {
  if (ignore()) {
    return;
  }
  
  int p = 0;
  while (p < paramCount) {
    int motor = params[p++];
    
    stopMotor(motor);
  }
}*/

void stopAll() {
  if (ignore()) {
    return;
  }

  motorAllStop();
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    moving[i] = false;
  }
}

void areAllStopped() {
  for (int i = 0; i < ROTARY_COUNT; ++i) {
    if (moving[i]) {
      return;
    }
  }
  
  done();
}

void isOneStopped() {
  int motor = atoi(sc.next());
  
  if (moving[motor]) {
    return;
  }
  
  done();
}

/*void transferByte() {
  if (ignore()) {
    return;
  }
  
  byte value = params[0];
  Wire.beginTransmission(RECEIVER_SLAVE_ADDRESS);
  Wire.write(value);
  Wire.endTransmission();
}*/

void handshake() {
  lastSeqNo = -1;
  done();
}

void queryBallSensor() {
  Wire.requestFrom(BALL_SENSOR_SLAVE_ADDRESS, 1);
  int value = Wire.read();
  Serial.print(value > 190 ? RESP_DONE : RESP_NEGATIVE);
}

void unknown() {
  Serial.print(RESP_ERROR_COMMAND_UNKNOWN);
}
