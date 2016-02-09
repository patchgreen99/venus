import math
import time

import numpy as np

CENTIMETERS_TO_PIXELS = (300.0 / 600.0)


class SimpleStrategy:
    def __init__(self, world, commands):
        self.world = world
        self.commands = commands

    def calculate_angle_length(self):
        ball_pos = np.array([self.world.ball[0], self.world.ball[1]])
        robot_pos = np.array([self.world.venus.position[0], self.world.venus.position[1]])
        orientation_vec = np.array([self.world.venus.orientation[0], self.world.venus.orientation[1]])
        motion_vec = ball_pos - robot_pos

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
        time.sleep(0.5)
        self.commands.f(motion_length)
        time.sleep(0.5)

    def grab_ball(self):

        angle, motion_length = self.calculate_angle_length()
        while motion_length > 40.0:
            self.approach(angle, 40.0)
            angle, motion_length = self.calculate_angle_length()

        motion_length -= 30.0
        if motion_length > 0:
            self.approach(angle, motion_length)

        self.commands.r()
        time.sleep(0.5)
        self.commands.f(10.0)
        time.sleep(0.5)
        self.commands.g()
