import math
import time

import numpy as np

CENTIMETERS_TO_PIXELS = (300.0 / 600.0)


class SimpleStrategy:
    def __init__(self, world, commands):
        self.world = world
        self.commands = commands

    def calculate_angle_length_ball(self):
        return self.calculate_angle_length(np.array([self.world.ball[0], self.world.ball[1]]))

    def calculate_angle_length_goal(self):
        # computer goal
        if self.world.venus.position[0] > 300:
            return self.calculate_angle_length(np.array([589, 221]))
        # white board goal
        else:
            return self.calculate_angle_length(np.array([8, 227]))

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

        motion_length -= 6 #12 #13
        if motion_length < 5:
            motion_length = 5

        self.commands.f(motion_length, wait=True)
        self.commands.g()
        time.sleep(1)

    def goal(self):
        angle, motion_length = self.calculate_angle_length_goal()
        self.commands.c(angle)
        self.commands.x(500)
        time.sleep(.5)
        self.commands.g()

    def grab_goal(self):
        self.grab_ball()
        self.goal()

    def pass_ball(self):
        friend_pos = np.array([self.world.friend.position[0], self.world.friend.position[1]])
        angle, motion_length = self.calculate_angle_length(friend_pos)
        print("Turning " + str(angle) + " deg then kicking " + str(motion_length) + " cm")
        self.commands.c(angle)
        time.sleep(1)
        self.commands.kick(motion_length + 50)
        self.commands.open_narrow()
        time.sleep(1)
        self.commands.g()

    def catch_ball(self):
        print("Waiting for the ball to move")

        #while not self.world.ball_moving.value:
        #    pass

        print("The ball is moving")

        angle, length = self.calculate_angle_length_ball()
        print("Turning " + str(angle) + " deg, releasing grabber")
        self.commands.c(angle)

        time.sleep(1)

        self.commands.open_wide()
        # speed in cm per frame

        angle, length = self.calculate_angle_length_ball()
        speed = math.sqrt((self.world.future_ball[0]-self.world.ball[0])**2 + (self.world.future_ball[1]-self.world.ball[1])**2)
        while length > 24:# or not self.world.ball_moving.value:
            angle, length = self.calculate_angle_length_ball()
            speed = math.sqrt((self.world.future_ball[0]-self.world.ball[0])**2 + (self.world.future_ball[1]-self.world.ball[1])**2)
            print("Ball is " + str(length))
        print("The ball is " + str(length) + " m away, " + str(angle) + " deg")

        self.commands.g()
        time.sleep(1)
        self.commands.g(150)

        time.sleep(2)

        angle, length = self.calculate_angle_length_ball()
        print("The ball is " + str(length) + " m away")
        while length > 18:
            self.grab_ball()
            time.sleep(1)
            angle, length = self.calculate_angle_length_ball()
            print("Ball is " + str(length))

    def intercept(self):
        #print("Waiting for the ball to move")

        m = float(self.world.enemy1.position[1]-self.world.enemy2.position[1]) / float(self.world.enemy1.position[0]-self.world.enemy2.position[0])
        c = self.world.enemy1.position[1] - self.world.enemy1.position[0] * m
        go_x = -0.5*(-2*self.world.venus.position[0] + 2*m*(c-self.world.venus.position[1]))/(1+m**2)
        go_y = go_x*m + c
        block_position = (go_x, go_y)
        angle, motion_length = self.calculate_angle_length(block_position)

        #while not self.world.ball_moving.value:
        #     pass

        #print("The ball is moving")

        while motion_length > 100:
            self.approach(angle, 100)
            angle, motion_length = self.calculate_angle_length(block_position)

        angle, motion_length = self.calculate_angle_length(block_position)
        self.approach(angle, motion_length)

        print("Moving to "+str(block_position))

    def block_goal(self):
        t = (self.world.enemy2.position[0]*self.world.enemy2.orientation[1] - self.world.enemy2.position[1]*self.world.enemy2.orientation[0]+
             self.world.venus.position[1]*self.world.enemy2.orientation[0] - self.world.venus.position[0]*self.world.enemy2.orientation[1])/(self.world.venus.orientation[0]*self.world.enemy2.orientation[1] - self.world.venus.orientation[1]*self.world.enemy2.orientation[0])
        go_x = t*self.world.venus.orientation[0] + self.world.venus.position[0]
        go_y = t*self.world.venus.orientation[1] + self.world.venus.position[1]

        #m = (self.world.enemy2.position[1] - (self.world.enemy2.position[1] + self.world.enemy2.orientation[1])) / (self.world.enemy2.position[0] - (self.world.enemy2.position[0] + self.world.enemy2.orientation[0]))
        #c = self.world.enemy2.position[1] - m * self.world.enemy2.position[0]

        #print(m,c)
        #go_x = -0.5*(-2*self.world.venus.position[0] + 2*m*(c-self.world.venus.position[1]))/(1+m**2)
        #go_y = go_x*m + c
        #go_x = float(self.world.venus.position[0])
        #go_y = m*go_x + c

        block_position = (go_x, go_y)
        print block_position
        angle, motion_length = self.calculate_angle_length(block_position)

        self.approach(angle, motion_length)

    def catch_pass(self):
        self.catch_ball()
        self.pass_ball()
