import math

import numpy as np

PIXEL_TO_CENTIMETERS = 0.5


class SimpleStrategy:
    def __init__(self, world, commands):
        self.world = world
        self.commands = commands

    def grab_ball(self):
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

        motion_length = np.linalg.norm(motion_vec) * PIXEL_TO_CENTIMETERS

        print("Turning " + str(angle) + " deg")
        self.commands.c(angle, wait_done=True, wait_finished=True)
        # self.commands.f(motion_length - 10.0, wait_done=True, wait_finished=True)
        # self.commands.r()
        # self.commands.f(10.0, wait_done=True, wait_finished=True)
        # self.commands.g()
