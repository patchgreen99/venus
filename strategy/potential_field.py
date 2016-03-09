import math
import numpy as np

PITCH_ROWS = 480 #pixels
PITCH_COLS = 640 #pixels

POTENTIAL_GRANULARITY = 20 #pixels

DEFENDING_LEFT_TOP = [(117, 114), (190, 144)]
DEFENDING_LEFT_BOT = [(169, 365), (188, 367)]
DEFENDING_RIGHT_TOP = [(457, 107), (462, 114)]
DEFENDING_RIGHT_BOT = [(460, 358), (464, 368)]
GOAL_LEFT_TOP = [(25, 114), (38, 181)]
GOAL_LEFT_BOT = [(25, 365), (37, 304)]
GOAL_RIGHT_TOP = [(594, 107), (618, 176)]
GOAL_RIGHT_BOT = [(600, 358), (620, 297)]
PITCH_TOP_RIGHT = [(594, 15), (617, 10)]
PITCH_TOP_LEFT = [(25, 13), (39, 14)]
PITCH_BOT_RIGHT = [(600, 450), (617, 464)]
PITCH_BOT_LEFT = [(25, 457), (34, 466)]


class Potential:
        def __init__(self, last_square, last_direction, world, ball_field, friend_field, enemy1_field, enemy2_field,
                     free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1, free_up_goal_enemy2, block_pass,
                     block_goal_enemy1, block_goal_enemy2, advance, catch_up, bad_minima):

            self.world = world

            if last_square is None:
                self.last_square = (0, self.world.venus.position[0], self.world.venus.position[1])
            else:
                self.last_square = last_square

            if last_direction is None:
                self.last_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])
            else:
                self.last_direction = last_square

            self.top_wall = step_field(PITCH_TOP_LEFT[self.world.room_num], (PITCH_TOP_LEFT[self.world.room_num][0]-PITCH_TOP_RIGHT[self.world.room_num][0], PITCH_TOP_LEFT[self.world.room_num][1]-PITCH_TOP_RIGHT[self.world.room_num][1]), 0, 0)
            self.bot_wall = step_field(PITCH_BOT_LEFT[self.world.room_num], (PITCH_BOT_RIGHT[self.world.room_num][0]-PITCH_BOT_LEFT[self.world.room_num][0], PITCH_BOT_RIGHT[self.world.room_num][1]-PITCH_BOT_LEFT[self.world.room_num][1]), 0, 0)
            self.right_wall = step_field(PITCH_TOP_RIGHT[self.world.room_num], (PITCH_TOP_RIGHT[self.world.room_num][0] - PITCH_BOT_RIGHT[self.world.room_num][0], PITCH_TOP_RIGHT[self.world.room_num][1] - PITCH_BOT_RIGHT[self.world.room_num][1]), 0, 0)
            self.left_wall = step_field(PITCH_TOP_LEFT[self.world.room_num], (PITCH_BOT_LEFT[self.world.room_num][0] - PITCH_TOP_LEFT[self.world.room_num][0], PITCH_BOT_LEFT[self.world.room_num][1] - PITCH_TOP_LEFT[self.world.room_num][1]), 0, 0)

            if world.we_have_computer_goal and world.room_num == 1 or not world.we_have_computer_goal and world.room_num == 0: # there goal is on the right
                self.penalty_box_front = infinite_axial(DEFENDING_RIGHT_TOP[self.world.room_num], DEFENDING_RIGHT_BOT[self.world.room_num], 0, 0)
                self.penalty_box_top = infinite_axial(GOAL_RIGHT_TOP[self.world.room_num], DEFENDING_RIGHT_TOP[self.world.room_num], 0, 0)
                self.penalty_box_bot = infinite_axial(GOAL_RIGHT_BOT[self.world.room_num], DEFENDING_RIGHT_BOT[self.world.room_num], 0, 0)
            elif world.we_have_computer_goal and world.room_num == 0 or not world.we_have_computer_goal and world.room_num == 1: # obviously the left goal
                self.penalty_box_front = infinite_axial(DEFENDING_LEFT_TOP[self.world.room_num], DEFENDING_LEFT_BOT[self.world.room_num], 0, 0)
                self.penalty_box_top = infinite_axial(GOAL_LEFT_TOP[self.world.room_num], DEFENDING_LEFT_TOP[self.world.room_num], 0, 0)
                self.penalty_box_bot = infinite_axial(GOAL_LEFT_BOT[self.world.room_num], DEFENDING_LEFT_BOT[self.world.room_num], 0, 0)

            self.potential_list = [self.ball_field, self.friend_field, self.enemy1_field, self.enemy2_field,
                     self.free_up_pass_enemy1, self.free_up_pass_enemy2, self.free_up_goal_enemy1,
                    self.free_up_goal_enemy2, self.block_pass, self.block_goal_enemy1, self.block_goal_enemy2,
                        self.advance, self.catch_up, self.bad_minima, self.top_wall, self.bot_wall, self.right_wall,
                                self.left_wall, self.penalty_box_front, self.penalty_box_top, self.penalty_box_bot]

            self.ball_field = ball_field
            self.friend_field = friend_field
            self.enemy1_field = enemy1_field
            self.enemy2_field = enemy2_field
            self.free_up_pass_enemy1 = free_up_pass_enemy1
            self.free_up_pass_enemy2 = free_up_pass_enemy2
            self.free_up_goal_enemy1 = free_up_goal_enemy1
            self.free_up_goal_enemy2 = free_up_goal_enemy2
            self.block_pass = block_pass
            self.block_goal_enemy1 = block_goal_enemy1
            self.block_goal_enemy2 = block_goal_enemy2
            self.advance = advance
            self.catch_up = catch_up
            self.bad_minima = bad_minima

            self.local_potential = np.full((5, 5), fill_value=np.inf, dtype=np.float64)
            self.points = np.zeros((5, 5, 2))

        def build_grid(self):
            robot_pos = self.last_square
            robot_dir = self.last_direction

            #row then column

            self.local_potential[2, 2] = self.get_potential_at_square((robot_pos[0], robot_pos[1]))
            self.points[2, 2] = (robot_pos[0], robot_pos[1])

            point = (robot_pos[0]+POTENTIAL_GRANULARITY*robot_dir[0],robot_pos[1]+POTENTIAL_GRANULARITY*robot_dir[1])
            self.local_potential[1, 2] = self.get_potential_at_square(point)
            self.points[1, 2] = point

            back = rotate_vector(180, robot_dir[0], robot_dir[1])
            point = (robot_pos[0]+POTENTIAL_GRANULARITY*back[0],robot_pos[1]+POTENTIAL_GRANULARITY*back[1])
            self.local_potential[3, 2] = self.get_potential_at_square(point)
            self.points[3, 2] = point

            right = rotate_vector(-90, robot_dir[0], robot_dir[1])
            point = (robot_pos[0]+POTENTIAL_GRANULARITY*right[0],robot_pos[1]+POTENTIAL_GRANULARITY*right[1])
            self.local_potential[2, 3] = self.get_potential_at_square(point)
            self.points[2, 3] = point

            left = rotate_vector(90, robot_dir[0], robot_dir[1])
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

        def get_potential_at_square(self, (x, y)):
            potential_sum = 0
            for potential in self.potential_list:
                potential_sum = potential_sum + potential.field_at(x, y)
            return potential_sum






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

# finite axial - field will start at start point and exist on the opposite side to the ref point anc continue of
# the pitch
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
    angle = math.degrees(angle)
    return x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle)

def normalize((x, y)):
    return x/math.sqrt(x**2 + y**2), y/math.sqrt(x**2 + y**2)

def dot_product((ax, ay),(bx, by)):
    return ax*bx + ay*by