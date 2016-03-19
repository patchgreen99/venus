import math
import time
import matplotlib.pyplot as plt
import numpy as np

ROBOT_SIZE = 20
ROBOT_INFLUENCE_SIZE = 1000
CENTIMETERS_TO_PIXELS = (300.0 / 640.0)
POSITION_INFLUENCE_RANGE = 1000
PITCH_ROWS = 480+1 #pixels
PITCH_COLS = 640+1 #pixels


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
        self.heat_map = None
        self.points = None
        self.current_point = None
        self.current_direction = None
        self.commands = commands
        self.moving = True
        self.moving_backwards = False
        self.ready = 0
        self.turn = 0

    ###############################################################################################################################################################
    # ENTERING STATE
    ###############################################################################################################################################################
    def start(self, state):
        if state == "FREE_BALL_YOURS":
            pass
        elif state == "ATTACK_PASS":
            pass
        elif state == "ATTACK_GOAL":
            pass
        elif state == "RECEIVE_PASS":
            pass
        elif state == "FREE_BALL_2_GOALSIDE":
            pass
        elif state == "FREE_BALL_1_GOALSIDE":
            pass
        elif state == "FREE_BALL_BOTH_GOALSIDE":
            pass
        elif state == "FREE_BALL_NONE_GOALSIDE":
            pass
        elif state == "ENEMY1_BALL_TAKE_GOAL":
            pass
        elif state == "ENEMY2_BALL_TAKE_GOAL":
            pass
        elif state == "ENEMY_BALL_TAKE_PASS":
            pass

    ################################################################################################################################################################
    # MID STATE
    ################################################################################################################################################################
    def mid(self, state, sim):
        if state == "FREE_BALL_YOURS":

            # ON
            #####################################

            ball_field = radial(self.world.ball, 1, -5)# -5

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)


            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead

            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                #todo broken badly aseem says 4 points
                if self.world.room_num == 0 and self.world.we_have_computer_goal or self.world.room_num == 1 and not self.world.we_have_computer_goal:
                    penalty_point = self.world.defending_left_bot[0]
                else:
                    penalty_point = self.world.defending_right_bot[0]

                if self.world.venus.hasBallInRange.value == 1 and not (self.world.venus.position[0] < penalty_point < self.world.ball[0] or self.world.venus.position[0] > penalty_point > self.world.ball[0]):
                    time.sleep(1)
                    angle, motion_length = self.calculate_angle_length_ball()
                    self.commands.open_wide()
                    self.commands.c(angle)
                    angle, motion_length = self.calculate_angle_length_ball()
                    self.commands.f(motion_length)
                    self.commands.g()
                    time.sleep(.6)
                    # todo need to implement considering objects
                    if self.commands.query_ball():
                        print("It thinks it has the ball")
                        return
                else:
                    self.turn, self.current_point = self.move(None)
                    self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])

            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.colorbar()
                fig.show() #boom

            ########################################

            ###########################################################################################################################################

        elif state == "FREE_BALL_2_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 1, 25, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 25, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 25, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 10, -0.4)
            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 10, -0.4)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [free_up_pass_enemy1, free_up_goal_enemy2, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])

            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################

            ###########################################################################################################################################

        elif state == "FREE_BALL_1_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1, -0.4)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1, -0.4)


            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = [friend_field, enemy1_field, enemy2_field,free_up_pass_enemy2, free_up_goal_enemy1,advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potential)

            # MOTION
            #######################################
            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])

            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################

            ###########################################################################################################################################

        elif state == "FREE_BALL_BOTH_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1, -0.4)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1, -0.4)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [friend_field, enemy1_field, enemy2_field, free_up_goal_enemy1, free_up_goal_enemy2,  advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])
            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################
            ###########################################################################################################################################

        elif state == "FREE_BALL_NONE_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1, -0.4)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1, -0.4)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [friend_field, enemy1_field, enemy2_field, free_up_pass_enemy1, free_up_pass_enemy2, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])
            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################

            ###########################################################################################################################################

        elif state == "ENEMY1_BALL_TAKE_GOAL":

            # ON
            #####################################
            ball_field = radial(self.world.ball, 1, 0)

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, 0.4)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_goal_enemy1, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])

            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################
            ###########################################################################################################################################

        elif state == "ENEMY2_BALL_TAKE_GOAL":

            # ON
            #####################################
            ball_field = radial(self.world.ball, 1, 0)

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            block_goal_enemy2 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, 0.4)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_goal_enemy2,  advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################

            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])
            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################
            ###########################################################################################################################################

        elif state == "ENEMY_BALL_TAKE_PASS":

            # ON
            #####################################
            ball_field = radial(self.world.ball, 1, 0)

            friend_field = solid_field(self.world.friend.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 1, 5, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, 0.4)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_pass, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################

            if sim is False:
                self.local_potential, self.points = potential.get_local_potential()
                self.turn, self.current_point = self.move(None)
                self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])
            ########################################

            # TESTING
            ########################################
            else:
                heat_map = potential.get_heat_map()
                x = np.arange(PITCH_COLS)
                y = np.arange(PITCH_ROWS)

                X, Y = np.meshgrid(x, y)

                intensity = np.array(heat_map)

                fig, ax = plt.subplots()
                ax.pcolor(X, Y, intensity, vmin=-1, vmax=1)
                ax.invert_yaxis()
                ax.xaxis.tick_top()
                fig.show() #boom

            ########################################

            ###########################################################################################################################################

        elif state == "ATTACK_PASS":
            # pass ball to the friend, when attacking
            self.commands.pass_ball()

            ###########################################################################################################################################

        elif state == "ATTACK_GOAL":
            # you're in the good position to score
            self.commands.goal()

            ###########################################################################################################################################

        elif state == "RECEIVE_PASS":
            # you should be in the good position to catch the ball
            self.commands.catch_ball()

    ###########################################################################################################################################################
    # EXITING STATE
    ###########################################################################################################################################################
    def exit(self, state):

        if state == "FREE_BALL_YOURS":
            pass
        elif state == "FREE_BALL_2_GOALSIDE":
            pass
        elif state == "FREE_BALL_1_GOALSIDE":
            pass
        elif state == "FREE_BALL_BOTH_GOALSIDE":
            pass
        elif state == "FREE_BALL_NONE_GOALSIDE":
            pass
        elif state == "ENEMY1_BALL_TAKE_GOAL":
            pass
        elif state == "ENEMY2_BALL_TAKE_GOAL":
            pass
        elif state == "ENEMY_BALL_TAKE_PASS":
            pass

    ############################################################################################################################################################

    ############################################################################################################################################################

    def move(self, grab=None):
        """Executes command to go to minimum potential and returns robot direction after the movement"""
        x, y = np.where(self.local_potential == self.local_potential.min())
        indices = np.array([x, y]).T.tolist()
        if [1, 4] in indices and [3, 4] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.sharp_right()
            return RIGHT, self.points[2, 3]
        elif [1, 0] in indices and [3, 0] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.sharp_left(grab)
            return LEFT, self.points[2, 1]

        elif [2, 2] in indices:
            return TOP, self.points[2, 2]
        elif [1, 2] in indices or [0, 1] in indices or [0, 3] in indices:
            if self.moving_backwards:
                self.moving_backwards = False
                self.commands.pause()
            self.commands.forward(grab)
            return TOP, self.points[1, 2]
        elif [1, 1] in indices or [1, 0] in indices:
            if self.moving_backwards:
                self.moving_backwards = False
                self.commands.pause()
            self.commands.forward_left(grab)
            return LEFT, self.points[1, 1]
        elif [1, 3] in indices or [1, 4] in indices:
            if self.moving_backwards:
                self.moving_backwards = False
                self.commands.pause()
            self.commands.forward_right(grab)
            return RIGHT, self.points[1, 3]
        elif [2, 1] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.sharp_left(grab)
            return LEFT, self.points[2, 1]
        elif [2, 3] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.sharp_right(grab)
            return RIGHT, self.points[2, 3]
        elif [3, 2] in indices or [4, 1] in indices or [4, 3] in indices:
            if not self.moving_backwards:
                self.moving_backwards = True
                self.commands.pause()
            self.commands.backward(grab)
            return TOP, self.points[3, 2]
        elif [3, 1] in indices or [3, 0] in indices:
            if not self.moving_backwards:
                self.moving_backwards = True
                self.commands.pause()
            self.commands.backward_left(grab)
            return RIGHT, self.points[3, 1]
        elif [3, 3] in indices or [3, 4] in indices:
            if not self.moving_backwards:
                self.moving_backwards = True
                self.commands.pause()
            self.commands.backward_right(grab)
            return LEFT, self.points[3, 3]

    def grab_range(self):
        refAngle = math.atan2(self.world.venus.orientation[1], self.world.venus.orientation[0])
        ballAngle, ballLength = self.calculate_angle_length_ball()
        if abs(ballLength) < 10 and abs(refAngle-ballLength) < 45:
            return True
        else:
            return False

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

    def getPerpendicular(self, start, end, point):
        angle = math.degrees(math.atan2(start[0]-end[0], start[1]-end[1]))
        rotated_point = rotate_vector(-angle, point[0], point[1])
        start_field = rotate_vector(-angle, start[0], start[1])
        end_field = rotate_vector(-angle, end[0], end[1])

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        if left_ref < rotated_point[0] < right_ref:
            return abs(rotated_point[1] - start_field[1])
        else:
            return 1000

    def grab_ball(self):

        angle, motion_length = self.calculate_angle_length_ball()

        while motion_length > 80:
            self.approach(angle, 40)
            angle, motion_length = self.calculate_angle_length_ball()

        #time.sleep(1)
        angle, motion_length = self.calculate_angle_length_ball()
        if motion_length > 30:
            motion_length -= 30
        else:
            motion_length = 0
        print("LAST BEFORE LAST: turning " + str(angle) + " deg, going " + str(motion_length) + " cm")
        self.approach(angle, motion_length)

        #time.sleep(1)
        angle, motion_length = self.calculate_angle_length_ball()
        print("LAST: Turning " + str(angle) + " deg")
        self.commands.c(angle)

        self.commands.open_wide()


        print("LAST: Going " + str(motion_length) + " cm")

        motion_length -= 8 #12 #13
        if motion_length < 5:
            motion_length = 5

        self.commands.f(motion_length)
        self.commands.g()

    def magnitude(self, (x, y)):
        return math.sqrt(x**2 + y**2)

    def dot_product(self, (ax, ay),(bx, by)):
        return ax*bx + ay*by

    def cross_product(self, (ax, ay),(bx, by)):
        return ax*by + ay*bx



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
            result = self.constant*math.log(self.gradient*numerator/denominator, math.e)
            if result >= 0:
                return result
            else:
                return 0
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


def rotate_vector(angle, x, y): # takes degrees
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

def magnitude((x, y)):
    return math.sqrt(x**2 + y**2)
