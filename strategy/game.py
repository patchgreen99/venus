import math
import time

import cv2
import numpy as np



ROBOT_SIZE = 20
ROBOT_INFLUENCE_SIZE = 300
CENTIMETERS_TO_PIXELS = (300.0 / 640.0)


from potential_field import Potential


# Directions robot is facing after the movement
TOP = 0
RIGHT = -90
BOTTOM = 180
LEFT = 90


class Game:
    def __init__(self, world, commands):
        self.world = world
        self.local_potential = None
        self.points = None
        self.current_point = None
        self.current_direction = None
        self.commands = commands
        self.moving = True

    def run(self):


        # example state
        while True:
            # as an example the potentials you wil need for any single state
            # if you don't understand ask Aseem, then ask me :)
            # All the zeros are up to you
            # first value is the gradient eg. the response of the field
            # the second value is the constant eg. the magnitude of the field

            ball_field = radial(self.world.ball, 1, -100)

            # radial - constant gradient everywhere  coming out from one single spot
            # 3 3 3 3 3 3 3
            # 3 3 2 1 2 3 3
            # 3 3 1 0 1 3 3
            # 3 3 2 1 2 3 3
            # 3 3 3 3 3 3 3

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            # solid - modeled as a circle, from center 'forbidden' is unreachable and outside the influence area
            # is unreachable
            # 0 2 3 3 3 2 0
            # 1 3 9 9 9 3 1
            # 2 3 9 9 9 3 2
            # 1 3 9 9 9 3 1
            # 0 2 3 3 3 2 0

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            # finite axial outside - field will start at start point and exist on the opposite side to the ref point and
            # continue of the pitch
            # 3 3 3 2 3 3 3
            # 3 2 1 1 1 2 3
            # 0 0 0 0 0 0 0
            # 3 2 1 1 1 2 3
            # 3 3 3 2 3 3 3

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)
            block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)
            block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            # finite axial inside - field is between reference points and exists everywhere
            # 3 3 3 2 3 3 3
            # 3 2 1 1 1 2 3
            # 0 0 0 0 0 0 0
            # 3 2 1 1 1 2 3
            # 3 3 3 2 3 3 3

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 0, 0)

            # infinite axial - field is only implemented between start and end points everywhere else
            # contribution is zero
            # 3 3 3 3 3 3 3
            # 1 1 1 1 1 1 1
            # 0 0 0 0 0 0 0
            # 1 1 1 1 1 1 1
            # 3 3 3 3 3 3 3

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 0, 0)

            # step - an infinite line drawn through the point in the first argument in the direction of the vector in
            # the second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment
            # acts like a infinite axial field over the entire pitch
            # 9 9 9 9 9 9 9
            # 9 9 9 9 9 9 9
            # 3 3 3 3 3 3 3
            # 1 1 1 1 1 1 1
            # 0 0 0 0 0 0 0

            # Constructor must always be this

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.current_direction = potential.last_direction
            self.local_potential, self.points = potential.get_local_potential()
            angle, length = self.calculate_angle_length_ball()
            if potential.ball_next_square and self.world.grabber_open:
                self.commands.c(angle)
            print self.local_potential[2][2]
            if not self.world.grabber_open and self.world.venus.hasBallInRange.value:
                print "Opening grabber"
                self.commands.open_wide()
            turn, self.current_point = self.move()
            if potential.ball_next_square and self.world.grabber_open:
                self.commands.g()
                exit(0)
            self.current_direction = rotate_vector(turn, self.current_direction[0], self.current_direction[1])
            time.sleep(1)

    def move(self):
        """Executes command to go to minimum potential and returns robot direction after the movement"""
        x, y = np.where(self.local_potential == self.local_potential.min())
        indices = np.array([x, y]).T.tolist()
        if [2, 2] in indices:
            return TOP, self.points[2, 2]
        elif [1, 2] in indices or [0, 1] in indices or [0, 3] in indices:
            self.commands.forward()
            return TOP, self.points[1, 2]
        elif [1, 1] in indices or [1, 0] in indices:
            self.commands.forward_left()
            return LEFT, self.points[1, 1]
        elif [1, 3] in indices or [1, 4] in indices:
            self.commands.forward_right()
            return RIGHT, self.points[1, 3]
        elif [2, 1] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.sharp_left()
            return LEFT, self.points[2, 1]
        elif [2, 3] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.sharp_right()
            return RIGHT, self.points[2, 3]
        elif [3, 2] in indices or [4, 1] in indices or [4, 3] in indices:
            self.commands.c(100)
            #self.commands.backward()
            return TOP, self.points[3, 2]
        elif [3, 1] in indices or [3, 0] in indices:
            self.commands.c(100)
            #self.commands.backward_left()
            return RIGHT, self.points[3, 1]
        elif [3, 3] in indices or [3, 4] in indices:
            self.commands.c(100)
            #self.commands.backward_right()
            return LEFT, self.points[3, 3]

    def calculate_angle_length_ball(self):
        return self.calculate_angle_length(np.array([self.world.ball[0], self.world.ball[1]]))

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
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
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

# finite axial inside - field is between reference points and exists everywhere
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial_inside:
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
        end_field = rotate_vector(-angle, self.start_x, self.start_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        if left_ref < rotated_point[0] < right_ref:
            b = right_ref - rotated_point[0]
            a = left_ref - rotated_point[0]
            distance_to = abs(rotated_point[1] - start_field[1])
            return self.constant*math.pow(math.log(b + math.sqrt(b**2 + distance_to**2)/a + math.sqrt(a**2 + distance_to**2), math.e), self.gradient)
        elif right_ref <= rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-right_ref)**2 + (y-right_ref)**2), self.gradient)
        elif left_ref >= rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-left_ref)**2 + (y-left_ref)**2), self.gradient)


# finite axial outside - field will start at start point and exist on the opposite side to the ref point anc continue of
# the pitch
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial_outside:
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
            left_ref = start_field[0]
            right_ref = end_field[0]

        if left_ref < rotated_point[0] < right_ref:
            b = right_ref - rotated_point[0]
            a = left_ref - rotated_point[0]
            distance_to = abs(rotated_point[1] - start_field[1])
            return self.constant*math.pow(math.log(b + math.sqrt(b**2 + distance_to**2)/a + math.sqrt(a**2 + distance_to**2), math.e), self.gradient)
        elif right_ref <= rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-right_ref)**2 + (y-right_ref)**2), self.gradient)
        elif left_ref >= rotated_point[0]: # outside
            return self.constant/math.pow(math.sqrt((x-left_ref)**2 + (y-left_ref)**2), self.gradient)

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
                return -9999*self.constant
            else:
                return 9999*self.constant

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
        distance_to = abs(rotated_point[1] - rotated_field[1])
        if dot_product(step_direction, (x - self.pos_x, y - self.pos_y)) > 0: # in direction step_direction
            return self.constant*math.pow(math.log(900/distance_to, math.e), self.gradient)
        else:
            if self.constant <= 0:
                return -9999*self.constant
            else:
                return 9999*self.constant

def rotate_vector(angle, x, y):
    angle = math.radians(angle)
    return x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle)

def normalize((x, y)):
    return x/math.sqrt(x**2 + y**2), y/math.sqrt(x**2 + y**2)

def dot_product((ax, ay),(bx, by)):
    return ax*bx + ay*by

def get_play_direction(world):
    if world.we_have_computer_goal and world.room_num == 1 or not world.we_have_computer_goal and world.room_num == 0:
        return 1, 0
    elif world.we_have_computer_goal and world.room_num == 0 or not world.we_have_computer_goal and world.room_num == 1:
        return -1, 0
