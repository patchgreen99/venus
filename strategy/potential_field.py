import math
import numpy as np
import cv2
from game import *

PITCH_ROWS = 480+1 #pixels
PITCH_COLS = 640+1 #pixels

POTENTIAL_GRANULARITY = 20*CENTIMETERS_TO_PIXELS #pixels
WALL_INFLUENCE = 1000 # pixels
PENALTY_BOX_INFLUENCE = 1000# pixels

'''
DEFENDING_LEFT_TOP = [(117, 114), (190, 144)]
DEFENDING_LEFT_BOT = [(169, 365), (188, 367)]
DEFENDING_RIGHT_TOP = [(457, 107), (462, 114)]
DEFENDING_RIGHT_BOT = [(460, 358), (464, 368)]
GOAL_LEFT_TOP = [(25, 114), (38, 144)]
GOAL_LEFT_BOT = [(25, 365), (37, 367)]
GOAL_RIGHT_TOP = [(594, 107), (618, 114)]
GOAL_RIGHT_BOT = [(600, 358), (620, 368)]
PITCH_TOP_RIGHT = [(594, 15), (617, 10)]
PITCH_TOP_LEFT = [(25, 13), (39, 14)]
PITCH_BOT_RIGHT = [(600, 450), (617, 464)]
PITCH_BOT_LEFT = [(25, 457), (34, 466)]
'''

class Potential:
        def __init__(self, last_square, last_direction, world, potentials):

            self.world = world
            self.ball_next_square = False

            self.last_square = last_square
            self.last_direction = last_direction

            self.top_wall = step_field(self.world.pitch_top_left, (self.world.pitch_top_right[0]-self.world.pitch_top_left[0], self.world.pitch_top_right[1]-self.world.pitch_top_left[1]), WALL_INFLUENCE, 2, 20) # best with 3 5
            self.bot_wall = step_field(self.world.pitch_bot_left, (self.world.pitch_bot_left[0]-self.world.pitch_bot_right[0], self.world.pitch_bot_left[1]-self.world.pitch_bot_right[1]), WALL_INFLUENCE, 2, 20)
            self.right_wall = step_field(self.world.pitch_top_right, (self.world.pitch_bot_right[0] - self.world.pitch_top_right[0], self.world.pitch_bot_right[1] - self.world.pitch_top_right[1]), WALL_INFLUENCE, 2, 30)
            self.left_wall = step_field(self.world.pitch_top_left, (self.world.pitch_top_left[0] - self.world.pitch_bot_left[0], self.world.pitch_top_left[1] - self.world.pitch_bot_left[1]), WALL_INFLUENCE, 2, 30)

            # use 1, 100
            if world.we_have_computer_goal and world.room_num == 1 or not world.we_have_computer_goal and world.room_num == 0: # there goal is on the right
                self.penalty_box_front = step_field_inside(self.world.defending_right_top, self.world.defending_right_bot, (self.world.defending_right_bot[0]-self.world.defending_right_top[0], self.world.defending_right_bot[1]-self.world.defending_right_top[1]), PENALTY_BOX_INFLUENCE, 2, 20) # 2, 500
                self.penalty_box_top = infinite_axial_inside(self.world.goal_right_top, self.world.defending_right_top, PENALTY_BOX_INFLUENCE, 2, 20)
                self.penalty_box_bot = infinite_axial_inside(self.world.goal_right_bot, self.world.defending_right_bot, PENALTY_BOX_INFLUENCE, 2, 20)
            elif world.we_have_computer_goal and world.room_num == 0 or not world.we_have_computer_goal and world.room_num == 1: # obviously the left goal
                self.penalty_box_front = step_field_inside(self.world.defending_left_top, self.world.defending_left_bot, (self.world.defending_left_top[0]-self.world.defending_left_bot[0], self.world.defending_left_top[1]-self.world.defending_left_bot[1]), PENALTY_BOX_INFLUENCE, 2, 20)
                self.penalty_box_top = infinite_axial_inside(self.world.goal_left_top, self.world.defending_left_top, PENALTY_BOX_INFLUENCE, 2, 20)
                self.penalty_box_bot = infinite_axial_inside(self.world.goal_left_bot, self.world.defending_left_bot, PENALTY_BOX_INFLUENCE, 2, 20)

            self.potential_list = potentials + [self.top_wall, self.bot_wall, self.right_wall, self.left_wall, self.penalty_box_front, self.penalty_box_bot, self.penalty_box_top]

            #self.potential_list = [self.ball_field]

            #self.local_potential = np.full((5, 5), fill_value=np.inf, dtype=np.float64)
            self.local_potential = np.zeros((5, 5), dtype=np.float64)
            self.points = np.zeros((5, 5, 2))
            self.heat_map = np.zeros((PITCH_ROWS, PITCH_COLS))

        def nothing(self, x):
            pass

        def build_field(self):
            for potential in self.potential_list:
                potential.add_field(self.local_potential)

        def build_grid(self):
            robot_pos = self.last_square
            robot_dir = normalize(self.last_direction)

            #row then column
            forwards = rotate_vector(0, robot_dir[0], robot_dir[1])
            back = rotate_vector(180, robot_dir[0], robot_dir[1])
            right = rotate_vector(90, robot_dir[0], robot_dir[1])
            left = rotate_vector(-90, robot_dir[0], robot_dir[1])

            self.local_potential[2, 2] = self.get_potential_at_square((robot_pos[0], robot_pos[1]))
            self.points[2, 2] = (robot_pos[0], robot_pos[1])

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*forwards[0], robot_pos[1]+POTENTIAL_GRANULARITY*forwards[1])
            self.local_potential[1, 2] = self.get_potential_at_square(point)
            self.points[1, 2] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*back[0],robot_pos[1]+POTENTIAL_GRANULARITY*back[1])
            self.local_potential[3, 2] = self.get_potential_at_square(point)
            self.points[3, 2] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*right[0],robot_pos[1]+POTENTIAL_GRANULARITY*right[1])
            self.local_potential[2, 3] = self.get_potential_at_square(point)
            self.points[2, 3] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*left[0],robot_pos[1]+POTENTIAL_GRANULARITY*left[1])
            self.local_potential[2, 1] = self.get_potential_at_square(point)
            self.points[2, 1] = point

            # corner inner 3x3

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*robot_dir[0]+POTENTIAL_GRANULARITY*right[0],robot_pos[1]+POTENTIAL_GRANULARITY*robot_dir[1]+POTENTIAL_GRANULARITY*right[1])
            self.local_potential[1, 3] = self.get_potential_at_square(point)
            self.points[1, 3] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*robot_dir[0]+POTENTIAL_GRANULARITY*left[0],robot_pos[1]+POTENTIAL_GRANULARITY*robot_dir[1]+POTENTIAL_GRANULARITY*left[1])
            self.local_potential[1, 1] = self.get_potential_at_square(point)
            self.points[1, 1] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*back[0]+POTENTIAL_GRANULARITY*right[0],robot_pos[1]+POTENTIAL_GRANULARITY*back[1]+POTENTIAL_GRANULARITY*right[1])
            self.local_potential[3, 3] = self.get_potential_at_square(point)
            self.points[3, 3] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*back[0]+POTENTIAL_GRANULARITY*left[0],robot_pos[1]+POTENTIAL_GRANULARITY*back[1]+POTENTIAL_GRANULARITY*left[1])
            self.local_potential[3, 1] = self.get_potential_at_square(point)
            self.points[3, 1] = point

            # top and bottom

            point = (robot_pos[0]+2*POTENTIAL_GRANULARITY*robot_dir[0]+POTENTIAL_GRANULARITY*right[0],robot_pos[1]+2*POTENTIAL_GRANULARITY*robot_dir[1]+POTENTIAL_GRANULARITY*right[1])
            self.local_potential[0, 3] = self.get_potential_at_square(point)
            self.points[0, 3] = point

            point = (robot_pos[0]+2*POTENTIAL_GRANULARITY*robot_dir[0]+POTENTIAL_GRANULARITY*left[0],robot_pos[1]+2*POTENTIAL_GRANULARITY*robot_dir[1]+POTENTIAL_GRANULARITY*left[1])
            self.local_potential[0, 1] = self.get_potential_at_square(point)
            self.points[0, 1] = point

            point = (robot_pos[0]+2*POTENTIAL_GRANULARITY*back[0]+POTENTIAL_GRANULARITY*right[0],robot_pos[1]+2*POTENTIAL_GRANULARITY*back[1]+POTENTIAL_GRANULARITY*right[1])
            self.local_potential[4, 3] = self.get_potential_at_square(point)
            self.points[4, 3] = point

            point = (robot_pos[0]+2*POTENTIAL_GRANULARITY*back[0]+POTENTIAL_GRANULARITY*left[0],robot_pos[1]+2*POTENTIAL_GRANULARITY*back[1]+POTENTIAL_GRANULARITY*left[1])
            self.local_potential[4, 1] = self.get_potential_at_square(point)
            self.points[4, 1] = point

            # side side

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*robot_dir[0]+2*POTENTIAL_GRANULARITY*right[0],robot_pos[1]+POTENTIAL_GRANULARITY*robot_dir[1]+2*POTENTIAL_GRANULARITY*right[1])
            self.local_potential[1, 4] = self.get_potential_at_square(point)
            self.points[1, 4] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*robot_dir[0]+2*POTENTIAL_GRANULARITY*left[0],robot_pos[1]+POTENTIAL_GRANULARITY*robot_dir[1]+2*POTENTIAL_GRANULARITY*left[1])
            self.local_potential[1, 0] = self.get_potential_at_square(point)
            self.points[1, 0] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*back[0]+2*POTENTIAL_GRANULARITY*right[0],robot_pos[1]+POTENTIAL_GRANULARITY*back[1]+2*POTENTIAL_GRANULARITY*right[1])
            self.local_potential[3, 4] = self.get_potential_at_square(point)
            self.points[3, 4] = point

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*back[0]+2*POTENTIAL_GRANULARITY*left[0],robot_pos[1]+POTENTIAL_GRANULARITY*back[1]+2*POTENTIAL_GRANULARITY*left[1])
            self.local_potential[3, 0] = self.get_potential_at_square(point)
            self.points[3, 0] = point

        def get_local_potential(self):
            self.build_grid()
            return self.local_potential, self.points

        def get_heat_map(self):
            for potential in self.potential_list:
                self.heat_map = potential.add_field(self.heat_map)
            return self.heat_map

        def check_ahead(self, (x, y), (refx, refy), (xt, yt), (xb, yb), (xr, yr), (xl, yl)):
            t = (refx+POTENTIAL_GRANULARITY*xt/2, refy+POTENTIAL_GRANULARITY*yt/2)
            b = (refx+POTENTIAL_GRANULARITY*xb/2, refy+POTENTIAL_GRANULARITY*yb/2)
            r = (refx+POTENTIAL_GRANULARITY*xr/2, refy+POTENTIAL_GRANULARITY*yr/2)
            l = (refx+POTENTIAL_GRANULARITY*xl/2, refy+POTENTIAL_GRANULARITY*yl/2)
            if self.within((x, y), t, b) and self.within((x, y), r, l):
                return True
            else:
                return False

        def get_potential_at_square(self, (x, y)):
            potential_sum = 0
            for potential in self.potential_list:
                potential_sum = potential_sum + potential.field_at(x, y)
            return potential_sum

        def get_last_sqaure(self):
            return self.last_square

        def within(self, (x, y), (x1, y1), (x2, y2)):
            dir_x = x2-x1
            dir_y = y2-y1
            angle = math.degrees(math.atan2(dir_y, dir_x))
            rotated_point = rotate_vector(-angle, x, y)
            rotated_start = rotate_vector(-angle, x1, y1)
            rotated_end = rotate_vector(-angle, x2, y2)
            if rotated_start[0] > rotated_end[0]:
                right = rotated_start[0]
                left = rotated_end[0]
            else:
                left = rotated_start[0]
                right = rotated_end[0]
            return left < rotated_point[0] < right

        def get_last_direction(self):
            return self.last_direction

def rotate_vector(angle, x, y): # clock_wise negative
    angle = math.radians(angle)
    return x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle)

def normalize((x, y)):
    return x/math.sqrt(x**2 + y**2), y/math.sqrt(x**2 + y**2)

def dot_product((ax, ay),(bx, by)):
    return ax*bx + ay*by

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

    def add_field(self, local_potential):
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                distance_to = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
                if distance_to != 0:
                    local_potential[y, x] += self.constant/math.pow(distance_to, self.gradient)
        return local_potential


# infinite axial - field is only implemented between start and end points everywhere else contribution is zero
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0
# 1 1 1 1 1 1 1
# 3 3 3 3 3 3 3

class infinite_axial_inside:
    def __init__(self, (start_x, start_y), (end_x, end_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_point = rotate_vector(-angle, x, y)
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        if rotated_start[0] < rotated_end[0]:
            distance_to = abs(rotated_point[1] - rotated_start[1])
            if rotated_start[0] < rotated_point[0] < rotated_end[0] and distance_to < self.influence_range:
                return self.constant/math.pow(distance_to, self.gradient) #todo dividing by zero
            else:
                return 0
        else:
            distance_to = abs(rotated_point[1] - rotated_start[1])
            if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to < self.influence_range:
                return self.constant/math.pow(distance_to, self.gradient)
            else:
                return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - rotated_start[1])
                if rotated_start[0] < rotated_end[0]:
                    if rotated_start[0] < rotated_point[0] < rotated_end[0] and distance_to < self.influence_range and distance_to != 0:
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                else:
                    if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to < self.influence_range and distance_to != 0:
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)

        return local_potential

# infinite axial - field is only implemented between start and end points everywhere else contribution is zero
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0
# 1 1 1 1 1 1 1
# 3 3 3 3 3 3 3

class infinite_axial_outside:
    def __init__(self, (start_x, start_y), (end_x, end_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_point = rotate_vector(-angle, x, y)
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        distance_to = abs(rotated_point[1] - rotated_start[1])
        if distance_to < self.influence_range:
            return self.constant/math.pow(distance_to, self.gradient)
        else:
            return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - rotated_start[1])
                if distance_to < self.influence_range and distance_to != 0:
                    local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)

        return local_potential

# # finite axial inside - field is between reference points and exists everywhere
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial_inside:
    def __init__(self, (start_x, start_y), (ref_x, ref_y), g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = ref_x
        self.end_y = ref_y
        self.dir_x = start_x - ref_x
        self.dir_y = start_y - ref_y
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_point = rotate_vector(-angle, x, y)
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        b = rotated_point[0] - right_ref
        a = rotated_point[0] - left_ref
        distance_to = rotated_point[1] - start_field[1]
        denominator = (a + math.sqrt(a**2 + distance_to**2))
        numerator = (b + math.sqrt(b**2 + distance_to**2))
        if denominator != 0 and numerator != 0:
            return self.constant*math.log(self.gradient*numerator/denominator, math.e)
        else:
            return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                b = rotated_point[0] - right_ref
                a = rotated_point[0] - left_ref
                distance_to = rotated_point[1] - start_field[1]
                denominator = (a + math.sqrt(a**2 + distance_to**2))
                numerator = (b + math.sqrt(b**2 + distance_to**2))
                if denominator != 0 and numerator != 0:
                    local_potential[y,x] += self.constant*math.log(self.gradient*numerator/denominator, math.e)

        return local_potential


# finite axial outside - field will start at start point and exist on the opposite side to the ref point anc continue of
# the pitch
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial_outside:
    def __init__(self, (start_x, start_y), (ref_x, ref_y), influence, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.ref_x = ref_x
        self.ref_y = ref_y
        self.dir_x = start_x - ref_x
        self.dir_y = start_y - ref_y
        self.gradient = g
        self.constant = k
        self.influence = influence

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_point = rotate_vector(-angle, x, y)
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        b = rotated_point[0] - right_ref
        a = rotated_point[0] - left_ref
        distance_to = rotated_point[1] - start_field[1]
        denominator = (a + math.sqrt(a**2 + distance_to**2))
        numerator = (b + math.sqrt(b**2 + distance_to**2))
        if denominator != 0 and numerator != 0:
            result =  self.constant*math.log(self.gradient*numerator/denominator, math.e)
            if result < 0:
                return 0
            else:
                return result
        else:
            return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                b = rotated_point[0] - right_ref
                a = rotated_point[0] - left_ref
                distance_to = rotated_point[1] - start_field[1]
                denominator = (a + math.sqrt(a**2 + distance_to**2))
                numerator = (b + math.sqrt(b**2 + distance_to**2))
                if denominator != 0 and numerator != 0:
                    result = self.constant*math.log(self.gradient*numerator/denominator, math.e)
                    if result >= 0:
                       local_potential[y,x] += result

        return local_potential


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
        if separation > self.influence_area:
            return 0
        elif separation > self.forbidden:
            return self.constant/math.pow(separation-self.forbidden, self.gradient)
        else:
            if self.constant <= 0:
                return -9999*self.constant
            else:
                return 9999*self.constant

    def add_field(self, local_potential):
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
                if separation > self.forbidden and separation != 0:
                    local_potential[y,x] += self.constant/math.pow(separation-self.forbidden, self.gradient)
                else:
                    if self.constant <= 0:
                        local_potential[y,x] += -9999*self.constant
                    else:
                        local_potential[y,x] += 9999*self.constant

        return local_potential

# step - an infinite line drawn through the point in the first argument in the direction of the vector in the
# second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment acts like a
# infinite axial field over the entire pitch. also must be between start and end
# 9 9 9 9 9 9 9
# 9 9 9 9 9 9 9
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0


class step_field_inside:
    def __init__(self, (start_x, start_y), (end_x, end_y), (dir_x, dir_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_point = rotate_vector(-angle, x, y)
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)
        distance_to = abs(rotated_point[1] - start_field[1])

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        if left_ref < rotated_point[0] < right_ref:
            if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                if distance_to < self.influence_range:
                    return self.constant/math.pow(distance_to, self.gradient)
                else:
                    return 0
            else:
                if self.constant <= 0:
                    return 9999*self.constant + self.constant/math.pow(distance_to, self.gradient)
                else:
                    return 9999*self.constant - self.constant/math.pow(distance_to, self.gradient)
        elif rotated_point[0] <= left_ref :
            if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                return self.constant/math.pow(math.sqrt((x-left_ref)**2 + distance_to**2), self.gradient)
            else:
                return 0
        elif rotated_point[0] >= right_ref :
            if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                return self.constant/math.pow(math.sqrt((x-right_ref)**2 + distance_to**2), self.gradient)
            else:
                return 0

    def add_field(self, local_potential):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - start_field[1])
                step = dot_product(step_direction, (x - self.start_x, y - self.start_y))
                if left_ref < rotated_point[0] < right_ref and distance_to != 0:
                    if step > 0: # in direction step_direction
                        if distance_to < self.influence_range:
                            local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                    else:
                        if self.constant <= 0:
                            local_potential[y,x] += 9999*self.constant + self.constant/math.pow(distance_to, self.gradient)
                        else:
                            local_potential[y,x] += 9999*self.constant - self.constant/math.pow(distance_to, self.gradient)
                elif rotated_point[0] <= left_ref and step > 0 and distance_to != 0:
                    local_potential[y,x] += self.constant/math.pow(math.sqrt((rotated_point[0]-left_ref)**2 + distance_to**2), self.gradient)
                elif rotated_point[0] >= right_ref and step > 0 and distance_to != 0:
                    local_potential[y,x] += self.constant/math.pow(math.sqrt((rotated_point[0]-right_ref)**2 + distance_to**2), self.gradient)

        return local_potential

# step - an infinite line drawn through the point in the first argument in the direction of the vector in the
# second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment acts like a
# infinite axial field over the entire pitch. also must be between start and end
# 9 9 9 9 9 9 9
# 9 9 9 9 9 9 9
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0


class step_field:
    def __init__(self, (start_x, start_y), (dir_x, dir_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def field_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_point = rotate_vector(-angle, x, y)
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        distance_to = abs(rotated_point[1] - start_field[1])

        if distance_to < self.influence_range:
            if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                # return self.constant*math.log(self.influence_range/math.pow(distance_to, self.gradient), math.e)
                return self.constant/math.pow(distance_to, self.gradient)
            else:
                if self.constant <= 0:
                    return -9999*self.constant
                else:
                    return 9999*self.constant
        else:
            return 0

    def add_field(self, local_potential):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):

                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - start_field[1])
                if distance_to < self.influence_range and distance_to != 0:
                    if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                    else:
                        if self.constant <= 0:
                            local_potential[y,x] += -9999*self.constant
                        else:
                            local_potential[y,x] += 9999*self.constant
        return local_potential