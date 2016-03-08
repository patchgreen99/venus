import math
import numpy as np
from potential_field import Potential

ROBOT_SIZE = 20
ROBOT_INFLUENCE_SIZE = 50

class Game:
    def __init__(self, world):
        self.world = world
        self.current_point = Potential.get_current_sqaure() #todo
        self.local_potential = np.zeros(5, 5)
        return

    def run(self):

        # example state
        if True:
            # as an example the potentials you wil need for any single state
            # if you don't understand ask Aseem, then ask me :)
            # All the zeros are up to you
            # first value is the gradient eg. the response of the field
            # the second value is the constant eg. the magnitude of the field

            ball_field = radial(self.world.ball, 0, 0)

            # radial - constant gradient everywhere  coming out from one single spot
            # 3 3 3 3 3 3 3
            # 3 3 2 1 2 3 3
            # 3 3 1 0 1 3 3
            # 3 3 2 1 2 3 3
            # 3 3 3 3 3 3 3

            friend_field = solid_field(self.world.friend.position, 0, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 0, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 0, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            # solid - modeled as a circle, from center 'forbidden' is unreachable and outside the influence area
            # is unreachable
            # 0 2 3 3 3 2 0
            # 1 3 9 9 9 3 1
            # 2 3 9 9 9 3 2
            # 1 3 9 9 9 3 1
            # 0 2 3 3 3 2 0

            free_up_pass_enemy1 = finite_axial(self.world.enemy1.position, self.world.friend.position, 0, 0)
            free_up_pass_enemy2 = finite_axial(self.world.enemy2.position, self.world.friend.position, 0, 0)
            free_up_goal_enemy1 = finite_axial(self.world.enemy1.position, self.world.there_goal, 0, 0)
            free_up_goal_enemy2 = finite_axial(self.world.enemy2.position, self.world.there_goal, 0, 0)

            # finite axial - field will start at start point and exist on the opposite side to the ref point and
            # continue of the pitch
            # 3 3 3 2 3 3 3
            # 3 2 1 1 1 2 3
            # 0 0 0 0 0 0 0
            # 3 2 1 1 1 2 3
            # 3 3 3 2 3 3 3

            block_pass = infinite_axial(self.world.enemy1.position, self.world.enemy2.position, 0, 0)
            block_goal_enemy1 = infinite_axial(self.world.enemy1.position, self.world.our_goal, 0, 0)
            block_goal_enemy2 = infinite_axial(self.world.enemy2.position, self.world.our_goal, 0, 0)
            bad_minima = infinite_axial(self.world.venus.position, self.world.friend.position, 0, 0)

            # infinite axial - field is only implemented between start and end points everywhere else
            # contribution is zero
            # 3 3 3 3 3 3 3
            # 1 1 1 1 1 1 1
            # 0 0 0 0 0 0 0
            # 1 1 1 1 1 1 1
            # 3 3 3 3 3 3 3

            advance = step_field(self.world.friend.position, (0, 1), 0, 0)
            catch_up = step_field(self.world.venus.position, (0, 1), 0, 0)

            # step - an infinite line drawn through the point in the first argument in the direction of the vector in
            # the second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment
            # acts like a infinite axial field over the entire pitch
            # 9 9 9 9 9 9 9
            # 9 9 9 9 9 9 9
            # 3 3 3 3 3 3 3
            # 1 1 1 1 1 1 1
            # 0 0 0 0 0 0 0

            # Constructor must always be this
            self.local_potential = Potential(self.current_point, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima)

            '''
            jules's movement method will be called here once you have you local matrix
            '''










































































    '''POTENTIALS'''

# radial - constant gradient everywhere  coming out from one single spot
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


# infinite axial - field is only implemented between start and end points everywhere else contribution is zero
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0
# 1 1 1 1 1 1 1
# 3 3 3 3 3 3 3

class infinite_axial:
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
        angle = math.atan2(self.dir_y, self.dir_x)
        rotated_point = rotate_vector(-angle, x, y)
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        if rotated_start[0] < rotated_end[0]:
            if rotated_start[0] < rotated_point[0] < rotated_end[0]:
                distance_to = abs(rotated_point[1] - rotated_start[1])
                return self.constant*math.pow(math.log(900/distance_to, math.e), self.gradient)
            else:
                return 0
        else:
            if rotated_end[0] < rotated_point[0] < rotated_start[0]:
                distance_to = abs(rotated_point[1] - rotated_start[1])
                return self.constant*math.pow(math.log(900/distance_to, math.e), self.gradient)
            else:
                return 0

# finite axial - field will start at start point and exist on the opposite side to the ref point anc continue of the pitch
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial:
    def __init__(self, (start_x, start_y), (ref_x, ref_y), g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.ref_x = ref_x
        self.ref_y = ref_y
        self.dir_x = start_x - ref_x
        self.dir_y = start_y - ref_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        angle = math.atan2(self.dir_y, self.dir_x)
        rotated_point = rotate_vector(-angle, x, y)
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            right_ref = start_field[0]
            left_ref = end_field[0]

        if start_field[0] < rotated_point[0] < end_field[0]:
            b = right_ref - rotated_point[0]
            a = left_ref - rotated_point[0]
            distance_to = abs(rotated_point[1] - start_field[1])
            return self.constant*math.pow(math.log(b + math.sqrt(b**2 + distance_to**2)/a + math.sqrt(a**2 + distance_to**2), math.e), self.gradient)
        elif right_ref <= rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-right_ref[0])**2 + (y-right_ref[1])**2), self.gradient)
        elif left_ref >= rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-left_ref[0])**2 + (y-left_ref[1])**2), self.gradient)

# solid - modeled as a circle, from center 'forbidden' is unreachable and outside the influence area is unreachable
# 0 2 3 3 3 2 0
# 1 3 9 9 9 3 1
# 2 3 9 9 9 3 2
# 1 3 9 9 9 3 1
# 0 2 3 3 3 2 0

class solid_field:
    def __init__(self, (pos_x, pos_y), g, k, forbidden, influence_area):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.gradient = g
        self.constant = k
        self.forbidden = forbidden
        self.influence_area = influence_area

    def field_at(self, x, y):
        separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
        if separation > self.forbidden:
            return self.constant/math.pow(math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2), self.gradient)
        elif separation > self.influence_area:
            return 0
        else:
            if self.constant <= 0:
                return -float("inf")
            else:
                return float("inf")

# step - an infinite line drawn through the point in the first argument in the direction of the vector in the
# second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment acts like a
# infinite axial field over the entire pitch
# 9 9 9 9 9 9 9
# 9 9 9 9 9 9 9
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0


class step_field:
    def __init__(self, (start_x, start_y), (dir_x, dir_y), g, k):
        self.pos_x = start_x
        self.pos_y = start_y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.atan2(self.dir_y, self.dir_x)
        rotated_point = rotate_vector(-angle, x, y)
        rotated_field = rotate_vector(-angle, self.pos_x, self.pos_y)
        distance_to = rotated_point[1] - rotated_field[1]
        if dot_product(step_direction, (x - self.pos_x, y - self.pos_y)) > 0: # in direction step_direction
            return self.constant*math.pow(math.log(900/distance_to, math.e), self.gradient)
        else:
            if self.constant <= 0:
                return -float("inf")
            else:
                return float("inf")

def rotate_vector(angle, x, y):
    return x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle)

def normalize((x, y)):
    return x/math.sqrt(x**2 + y**2), y/math.sqrt(x**2 + y**2)

def dot_product((ax, ay),(bx, by)):
    return ax*bx + ay*by