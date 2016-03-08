import math
import numpy as np
from potential_field import Potential

ROBOT_SIZE = 20

class Game:
    def __init__(self, world):
        self.world = world
        self.current_point = (0,0) #todo in the potential array not in the world !!!!!!!!!!!!!
        self.local_potential = np.zeros(5, 5)
        return

    def run(self):

        if True:
            # as an example the potentials you wil need for any single state
            # if you don't understand ask Aseem, then ask me :)
            # All the zeros are up to you
            # first value is the gradient eg. the response of the field
            # the second value is the constant eg. the magnitude of the field

            ball_field = radial(self.world.ball, 0, 0)
            friend_field = solid_field(self.world.friend.position, 0, 0)
            enemy1_field = solid_field(self.world.enemy1.position, 0, 0)
            enemy2_field = solid_field(self.world.enemy2.position, 0, 0)
            free_up_pass_enemy1 = finite_axial(self.world.enemy1.position, self.world.friend.position, 0, 0)
            free_up_pass_enemy2 = finite_axial(self.world.enemy2.position, self.world.friend.position, 0, 0)
            free_up_goal_enemy1 = finite_axial(self.world.enemy1.position, self.world.there_goal, 0, 0)
            free_up_goal_enemy2 = finite_axial(self.world.enemy2.position, self.world.there_goal, 0, 0)
            block_pass = infinite_axial(self.world.enemy1.position, self.world.enemy2.position, 0, 0)
            block_goal_enemy1 = infinite_axial(self.world.enemy1.position, self.world.there_our, 0, 0)
            block_goal_enemy2 = infinite_axial(self.world.enemy2.position, self.world.there_our, 0, 0)
            dont_copy_friend_enemy1 = infinite_axial(self.world.friend.position, self.world.enemy1.position, 0, 0)
            dont_copy_friend_enemy2 = infinite_axial(self.world.friend.position, self.world.enemy2.position, 0, 0)
            advance = step_field(self.world.friend.position, 0, 0)
            catch_up = step_field(self.world.venus.position, 0, 0)
            bad_minima = infinite_axial(self.world.venus.position, self.world.friend.position, 0, 0)

            self.local_potential = Potential(self.current_point, ball_field, friend_field, enemy1_field, enemy2_field, free_up_pass_enemy1,
                                             free_up_pass_enemy2, free_up_goal_enemy1, free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2, dont_copy_friend_enemy1,
                                             dont_copy_friend_enemy2, advance, catch_up,bad_minima)

            '''
            jules's movement method will be called here once you have you local matrix
            '''





'''Add here a very cool state machine'''



















'''POTENTIALS'''

# radial
# 3 3 3 3 3 3 3
# 3 3 2 1 2 3 3
# 3 3 1 0 1 3 3
# 3 3 2 1 2 3 3
# 3 3 3 3 3 3 3

class radial:
    def __init__(self, (pos_x, pos_y), g, k):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        return self.constant/math.pow(math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2), self.gradient)


# infinite axial
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0
# 1 1 1 1 1 1 1
# 3 3 3 3 3 3 3

class infinite_axial:
    def __init__(self, (start_x, start_y), (end_x, end_y), g, k):
        self.pos_x = start_x
        self.pos_y = start_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        # pure genius, if you don't like it speak to patrick
        angle = math.atan2(self.dir_y, self.dir_x)
        rotated_point = rotate_vector(-angle, x, y)
        rotated_field = rotate_vector(-angle, self.pos_x, self.pos_y)
        distance_to = abs(rotated_point[1] - rotated_field[1])
        return self.constant*math.pow(math.log(900/distance_to, math.e), self.gradient)

# finite axial
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial:
    def __init__(self, (start_x, start_y), (end_x, end_y), g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        # pure genius, if you don't like it speak to patrick
        angle = math.atan2(self.dir_y, self.dir_x)
        rotated_point = rotate_vector(-angle, x, y)
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)
        if start_field[0] < end_field[0]:
            left_ref = start_field
            right_ref = end_field
        else:
            left_ref = end_field
            right_ref = start_field
        distance_to = abs(rotated_point[1] - start_field[1])

        if left_ref < rotated_point[0] < right_ref: # within
            b = abs(right_ref[0] - rotated_point[0])
            a = abs(left_ref[0] - rotated_point[0])
            return self.constant*math.pow(math.log(b + math.sqrt(b**2 + distance_to**2)/a + math.sqrt(a**2 + distance_to**2), math.e), self.gradient)
        elif right_ref < rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-right_ref[0])**2 + (y-right_ref[1])**2), self.gradient)
        elif left_ref > rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-left_ref[0])**2 + (y-left_ref[1])**2), self.gradient)

# solid
# 0 2 3 3 3 2 0
# 1 3 9 9 9 3 1
# 2 3 9 9 9 3 2
# 1 3 9 9 9 3 1
# 0 2 3 3 3 2 0

class solid_field:
    def __init__(self, (pos_x, pos_y), g, k):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        seperation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
        if seperation > ROBOT_SIZE:
            return self.constant/math.pow(math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2), self.gradient)
        else:
            return float("inf")

# step
# 9 9 9 9 9 9 9
# 9 9 9 9 9 9 9
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0


class step_field:
    def __init__(self, (start_x, start_y), g, k):
        end_x, end_y = 0, 0 #todo (0,0) dependent on direction of play
        self.pos_x = start_x
        self.pos_y = start_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        # pure genius, if you don't like it speak to patrick
        angle = math.atan2(self.dir_y, self.dir_x)
        rotated_point = rotate_vector(-angle, x, y)
        rotated_field = rotate_vector(-angle, self.pos_x, self.pos_y)
        distance_to = rotated_point[1] - rotated_field[1]
        if distance_to < 0:
            return float("inf")
        else:
            return self.constant*math.pow(math.log(900/distance_to, math.e), self.gradient)


def rotate_vector(angle, x, y):
    return x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle)
