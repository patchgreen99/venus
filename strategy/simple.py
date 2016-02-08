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
        motion_vec = robot_pos - ball_pos
        motion_abs_angle = math.degrees(math.atan2(motion_vec[1], motion_vec[0])) + 90.0
        motion_rel_angle = self.world.venus.orientation.value - motion_abs_angle
        motion_length = np.linalg.norm(motion_vec) * PIXEL_TO_CENTIMETERS

        self.commands.c(motion_rel_angle, wait_done=True, wait_finished=True)
        self.commands.f(motion_length - 10.0, wait_done=True, wait_finished=True)
        self.commands.r()
        self.commands.f(10.0, wait_done=True, wait_finished=True)
        self.commands.g()
