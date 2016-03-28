import math
import time
import numpy as np

CENTIMETERS_TO_PIXELS = (300.0 / 639.0)

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
        self.commands.c(turn)
        self.commands.ee(d)
        self.commands.g()
        exit(0)

    def pass_ball(self):
        friend_pos = np.array([self.world.friend.position[0], self.world.friend.position[1]])
        angle, motion_length = self.calculate_angle_length(friend_pos)
        print("Turning " + str(angle) + " deg then kicking " + str(motion_length) + " cm")
        turn, d = self.shot_correction(angle)
        self.commands.c(turn)
        self.commands.ee(d)
        self.commands.g()
        exit(0)

    def catch_ball(self):
        print("Waiting for the ball to move")

        #while not self.world.ball_moving.value:
        #    pass

        angle, length = self.calculate_angle_length_ball()
        print("Turning " + str(angle) + " deg, releasing grabber")
        self.commands.c(angle)

        self.commands.o()
        # speed in cm per frame

        #t = time.time()

        angle, length = self.calculate_angle_length_ball()
        ball_moved = False
        vel = math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2)
        while length > 24 and (not ball_moved or vel > 5):

            print "Velocity is", vel
            if vel > 10:
                print "Ball moved above threshold"
                ball_moved = True

            angle, length = self.calculate_angle_length_ball()
            print("Ball is " + str(length))

            vel = math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2)

        print("The ball is " + str(length) + " m away, " + str(angle) + " deg")

        self.commands.g()
        #time.sleep(1)
        #self.commands.g(150)

        #angle, length = self.calculate_angle_length_ball()
        #print("The ball is " + str(length) + " m away")
        #while length > 18:
            #self.grab_ball()
            #time.sleep(1)
            #angle, length = self.calculate_angle_length_ball()
            #print("Ball is " + str(length))

    def shot_correction(self, angle):
        if -90 <= angle <= 0:
            turn = (90+angle)
            d = -1
        elif angle < -90:
            turn = -(-angle - 90)
            d = -1
        elif 0 < angle <= 90:
            turn = -(90-angle)
            d = 1
        elif angle > 90:
            turn = (angle-90)
            d = 1

        return turn, d