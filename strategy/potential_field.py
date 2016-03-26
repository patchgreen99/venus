import math
import numpy as np
import cv2
import potentials as g
import matplotlib.pyplot as plt
from pylab import *

PITCH_ROWS = 480+1 #pixels
PITCH_COLS = 640+1 #pixels

CENTIMETERS_TO_PIXELS = (300.0 / 640.0)
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

            self.top_wall = g.step_field(self.world.pitch_top_left, (self.world.pitch_top_right[0]-self.world.pitch_top_left[0], self.world.pitch_top_right[1]-self.world.pitch_top_left[1]), WALL_INFLUENCE, 1, 10) # best with 3 5
            self.bot_wall = g.step_field(self.world.pitch_bot_left, (self.world.pitch_bot_left[0]-self.world.pitch_bot_right[0], self.world.pitch_bot_left[1]-self.world.pitch_bot_right[1]), WALL_INFLUENCE, 1, 10)
            self.right_wall = g.step_field(self.world.pitch_top_right, (self.world.pitch_bot_right[0] - self.world.pitch_top_right[0], self.world.pitch_bot_right[1] - self.world.pitch_top_right[1]), WALL_INFLUENCE, 1, 10)
            self.left_wall = g.step_field(self.world.pitch_top_left, (self.world.pitch_top_left[0] - self.world.pitch_bot_left[0], self.world.pitch_top_left[1] - self.world.pitch_bot_left[1]), WALL_INFLUENCE, 1, 10)

            # use 1, 100
            if world.we_have_computer_goal and world.room_num == 1 or not world.we_have_computer_goal and world.room_num == 0: # there goal is on the right
                self.penalty_box_front = g.step_field_inside(self.world.defending_right_top, self.world.defending_right_bot, (self.world.defending_right_bot[0]-self.world.defending_right_top[0], self.world.defending_right_bot[1]-self.world.defending_right_top[1]), PENALTY_BOX_INFLUENCE, 1, 10) # 2, 500
                self.penalty_box_top = g.infinite_axial_inside((self.world.goal_right_top[0], self.world.defending_right_top[1]), self.world.defending_right_top, PENALTY_BOX_INFLUENCE, 1, 10)
                self.penalty_box_bot = g.infinite_axial_inside((self.world.goal_right_bot[0], self.world.defending_right_bot[1]), self.world.defending_right_bot, PENALTY_BOX_INFLUENCE, 1, 10)
            elif world.we_have_computer_goal and world.room_num == 0 or not world.we_have_computer_goal and world.room_num == 1: # obviously the left goal
                self.penalty_box_front = g.step_field_inside(self.world.defending_left_top, self.world.defending_left_bot, (self.world.defending_left_top[0]-self.world.defending_left_bot[0], self.world.defending_left_top[1]-self.world.defending_left_bot[1]), PENALTY_BOX_INFLUENCE, 1, 10)
                self.penalty_box_top = g.infinite_axial_inside((self.world.goal_left_top[0], self.world.defending_left_top[1]), self.world.defending_left_top, PENALTY_BOX_INFLUENCE, 1, 10)
                self.penalty_box_bot = g.infinite_axial_inside((self.world.goal_left_bot[0], self.world.defending_left_bot[1]), self.world.defending_left_bot, PENALTY_BOX_INFLUENCE, 1, 10)

            self.potential_list = potentials + [self.top_wall, self.bot_wall, self.right_wall, self.left_wall, self.penalty_box_bot, self.penalty_box_top, self.penalty_box_front]

            #self.potential_list = [self.ball_field]

            #self.local_potential = np.full((5, 5), fill_value=np.inf, dtype=np.float64)
            self.local_potential = np.zeros((5, 5), dtype=np.float64)
            self.points = np.zeros((5, 5, 2))
            self.heat_map = np.zeros((PITCH_ROWS, PITCH_COLS))


        def nothing(self, x):
            pass

        def map(self):
            heat_map = self.get_heat_map()
            x = np.arange(PITCH_COLS)
            y = np.arange(PITCH_ROWS)
            dx = np.zeros((PITCH_ROWS, PITCH_COLS))
            dy = np.zeros((PITCH_ROWS, PITCH_COLS))

            X, Y = np.meshgrid(x, y)

            fig, ax = plt.subplots()
            heatmap = ax.pcolor(X, Y, heat_map, vmin=-20, vmax=20)
            fig.colorbar(heatmap, ax=ax, shrink=0.9)
            #ax.invert_yaxis()
            #ax.xaxis.tick_top()
            #fig.show() #boom

            for p in self.potential_list:
                dx, dy = p.add_force(dx, dy)

            for x in range(0, PITCH_COLS):
                for y in range(0, PITCH_ROWS):
                    compx = dx[y,x]
                    compy = dy[y,x]
                    dx[y,x] /= math.sqrt(compx**2 + compy**2)
                    dy[y,x] /= math.sqrt(compx**2 + compy**2)
                    dx[y,x] *= 2
                    dy[y,x] *= 2

            #fig, ax = plt.subplots()
            # M = np.hypot(U[::20, ::20], -V[::20, ::20])
            plt.quiver(X[::15, ::15], Y[::15, ::15], dx[::15, ::15], -dy[::15, ::15], headwidth=5)
            #plt.colorbar()
            plt.axis([-10, PITCH_COLS+10, -10, PITCH_ROWS+10])
            ax.invert_yaxis()
            ax.xaxis.tick_top()

            fig.show()

        def build_field(self):
            for potential in self.potential_list:
                potential.add_field(self.local_potential)

        def get_force(self):
            return self.build_force()

        def build_force(self):
            dx, dy = 0, 0
            for potential in self.potential_list:
                tempx, tempy = potential.force_at(self.world.venus.position[0], self.world.venus.position[1])
                dx += tempx
                dy += tempy
                print potential
                print dx
            return dx, dy

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
