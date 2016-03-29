import math
import time
import numpy as np

CENTIMETERS_TO_PIXELS = (300.0 / 639.0)
PITCH_ROWS = 480 #pixels
PITCH_COLS = 640 #pixels

def sign(x):
    return 1 if x >= 0 else -1

class SimpleStrategy:
    def __init__(self, world, commands):
        self.world = world
        self.commands = commands

    def calculate_angle_length_ball(self):
        return self.calculate_angle_length(np.array([self.world.ball[0], self.world.ball[1]]))

    def calculate_angle_length_goal(self):
        # computer goal
        return self.calculate_angle_length(np.array([self.world.their_goalX, self.world.their_goalmeanY]))

    def calculate_angle_length(self, pos):

        robot_pos = np.array([self.world.venus.position[0], self.world.venus.position[1]])
        orientation_vec = np.array([self.world.venus.orientation[0], self.world.venus.orientation[1]])
        motion_vec = pos - robot_pos

        cross_product = np.cross(orientation_vec, motion_vec)
        dot_product = np.dot(orientation_vec, motion_vec)
        if dot_product >= 0:  # in front of the robot
            angle = math.degrees(
                math.asin(cross_product / (np.linalg.norm(motion_vec) * np.linalg.norm(orientation_vec))))
        else:
            temp_angle = math.degrees(
                math.asin(cross_product / (np.linalg.norm(motion_vec) * np.linalg.norm(orientation_vec))))
            if temp_angle >= 0:
                angle = 180 - temp_angle
            else:
                angle = -(180 + temp_angle)

        motion_length = np.linalg.norm(motion_vec) * CENTIMETERS_TO_PIXELS

        return angle, motion_length
    '''
    def approach(self, angle, motion_length):
        print("Turning " + str(angle) + " deg then going " + str(motion_length) + " cm")
        self.commands.c(angle)
        #time.sleep(.4)
        self.commands.f(motion_length)
        #time.sleep(.4)

    def grab_ball(self):

        angle, motion_length = self.calculate_angle_length_ball()

        while motion_length > 80:
            self.approach(angle, 40)
            angle, motion_length = self.calculate_angle_length_ball()

        time.sleep(1)
        angle, motion_length = self.calculate_angle_length_ball()
        if motion_length > 30:
            motion_length -= 30
        else:
            motion_length = 0
        print("LAST BEFORE LAST: turning " + str(angle) + " deg, going " + str(motion_length) + " cm")
        self.approach(angle, motion_length)

        time.sleep(1)
        angle, motion_length = self.calculate_angle_length_ball()
        print("LAST: Turning " + str(angle) + " deg")
        self.commands.c(angle)

        self.commands.open_wide()
        time.sleep(.4)

        print("LAST: Going " + str(motion_length) + " cm")

        motion_length -= 8 #12 #13
        if motion_length < 5:
            motion_length = 5

        self.commands.f(motion_length)
        self.commands.g()
        time.sleep(1)
    '''
    def goal(self):
        angle, motion_length = self.calculate_angle_length_goal()
        turn, d = self.shot_correction(angle)
        print "Turning %d deg" % turn
        self.commands.c(turn)
        self.commands.g()
        time.sleep(.1)
        self.commands.ee(d)
        self.commands.g()

    def pass_ball(self):
        friend_pos = np.array([self.world.friend.position[0], self.world.friend.position[1]])
        angle, motion_length = self.calculate_angle_length(friend_pos)
        print("Turning " + str(angle) + " deg then kicking " + str(motion_length) + " cm")
        turn, d = self.shot_correction(angle)
        self.commands.c(turn)
        self.commands.ee(d)
        self.commands.g()
        #exit(0)

    def catch_ball(self):
        print("Waiting for the ball to move")
        angle, length = self.calculate_angle_length(self.world.friend.position)
        print("Turning " + str(angle) + " deg, releasing grabber")
        self.commands.c(angle)

        self.commands.o()
        # speed in cm per frame
        #t = time.time()

        angle, length = self.calculate_angle_length(self.world.friend.position)
        vel = math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2)/6.0

        already_fast = False

        print "Velocity %d " % vel
        while length > 24:
            angle, length = self.calculate_angle_length_ball()
            print("Ball is " + str(vel))
            vel = math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2)/6.0
            if vel > 3.5:
                already_fast = True

            if vel < 3.5 and already_fast:
                break

        print("The ball is " + str(length) + " m away, " + str(angle) + " deg")

        self.commands.g()

    def shot_correction(self, angle):

        one_correction = 43
        two_correction = 60

        if self.world.room_num == 0 and self.world.we_have_computer_goal or self.world.room_num == 1 and not self.world.we_have_computer_goal:
            if PITCH_ROWS/4.0 <= self.world.venus.position[1] < PITCH_ROWS/2.0: # TOP#
                print "1TOP"
                print angle
                correction = 60
                if angle < 0:
                    turn = -(180 - angle + correction)
                else:
                    turn = -(-angle + 180 + correction)
                d = -1
            elif PITCH_ROWS/2.0 <= self.world.venus.position[1] < 3.0*PITCH_ROWS/4.0:
                print "1BOTTOM"
                print angle
                correction = 65
                if angle < 0:
                    turn = 180 + angle + correction
                else:
                    turn = angle + 180 + correction
                d = 1
            elif self.world.venus.position[1] < PITCH_ROWS/4.0: # TOP#
                print "2TOP"
                print angle
                correction = 80
                if angle < 0:
                    turn = 180 + angle + correction
                else:
                    turn = angle + 180 + correction
                d = 1
            elif 3.0*PITCH_ROWS/4.0 <= self.world.venus.position[1]:
                print "2BOTTOM"
                print angle
                correction = 70
                if angle < 0:
                    turn = -(180 - angle + correction)
                else:
                    turn = -(-angle + 180 + correction)
                d = -1

        else:
            '''
            if self.world.venus.position[1] < PITCH_ROWS/2.0: # TOP#
                print "3TOP"
                print angle
                correction = two_correction
                if angle < 0:
                    turn = 180 + angle + correction
                else:
                    turn = angle + 180 + correction
                d = 1
            else:
                print "3BOTTOM"
                print angle
                correction = one_correction
                if angle < 0:
                    turn = -(180 - angle + correction)
                else:
                    turn = -(-angle + 180 + correction)
                d = -1
            '''

        return turn, d