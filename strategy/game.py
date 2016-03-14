import math
import time

import numpy as np

ROBOT_SIZE = 30
ROBOT_INFLUENCE_SIZE = 600
CENTIMETERS_TO_PIXELS = (300.0 / 640.0)
COLS = 640
ROWS = 480


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
        self.ready = 0
        self.turn = 0

    ###############################################################################################################################################################
    # ENTERING STATE
    ###############################################################################################################################################################
    def start(self, state):
        if state == "FREE_BALL_YOURS":
            pass
            #angle, length = self.calculate_angle_length_ball()
            #self.commands.c(angle)
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
    def mid(self, state):
        if state == "FREE_BALL_YOURS":
            start = True
            while True:

                # ON
                #####################################

                ball_field = radial(self.world.ball, 1, -5)

                friend_field = solid_field(self.world.friend.position, 4, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
                enemy1_field = solid_field(self.world.enemy1.position, 4, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
                enemy2_field = solid_field(self.world.enemy2.position, 4, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

                advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
                catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

                # OFF
                #####################################

                free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 0)
                free_up_pass_enemy2 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 0)
                free_up_goal_enemy1 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 0)
                free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 0)

                block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, 0)
                block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, 0)
                block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, 0)

                bad_minima_goal = infinite_axial_outside(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
                bad_minima_pass = infinite_axial_outside(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

                # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
                ####################################
                # todo too reliant on vision, must pick what to use for look ahead

                self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
                if self.turn != 180 or None:
                    self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

                potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                                 free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                                 free_up_goal_enemy2, block_pass,
                                                 block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

                #self.current_direction = potential.last_direction
                self.local_potential, self.points = potential.get_local_potential()

                # MOTION
                #######################################

                #self.current_direction = potential.last_direction
                self.local_potential, self.points = potential.get_local_potential()
                print self.local_potential
                if self.world.venus.hasBallInRange.value and self.ready < 1:
                    angle, length = self.calculate_angle_length_ball()
                    self.ready += 1

                    self.commands.flush()
                    self.commands.s()
                    self.grab_ball()
                    print("It thinks it has the ball")
                    return
                else:
                    if start is True:
                        start = False
                        self.turn, self.current_point = self.move_defense(None)
                    else:
                        self.turn, self.current_point = self.move_defense(None)
                    self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])
                ########################################

                time.sleep(.5)

                ###########################################################################################################################################

        elif state == "FREE_BALL_2_GOALSIDE":
            while True:
                # ON
                #####################################

                friend_field = solid_field(self.world.friend.position, 2, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
                enemy1_field = solid_field(self.world.enemy1.position, 2, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
                enemy2_field = solid_field(self.world.enemy2.position, 2, 0, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

                advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
                catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

                free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 0)
                free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 0)

                if self.world.venus.position[1] < ROWS/2:
                    pertubation = -20
                else:
                    pertubation = 20

                #todo obviously this does not want to stay on
                bad_minima_goal = infinite_axial_outside((self.world.venus.position[0], self.world.venus.position[1] + pertubation), (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
                bad_minima_pass = infinite_axial_outside((self.world.venus.position[0], self.world.venus.position[1] + pertubation), self.world.friend.position, 2000, 0, 0)

                # OFF
                #####################################

                ball_field = radial(self.world.ball, 1, 0)

                free_up_pass_enemy2 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 0)
                free_up_goal_enemy1 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 0)

                block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, 0)
                block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX, self.world.our_goalmeanY), 1, 0)
                block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX, self.world.our_goalmeanY), 1, 0)

                # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
                ####################################
                # todo too reliant on vision, must pick what to use for look ahead
                self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
                if self.turn != 180 or self.current_direction is None :
                    self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

                potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                                 free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                                 free_up_goal_enemy2, block_pass,
                                                 block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

                self.current_direction = potential.last_direction
                self.local_potential, self.points = potential.get_local_potential()

                # MOTION
                #######################################
                self.local_potential, self.points = potential.get_local_potential()
                #self.turn, self.current_point = self.move_attack()
                #self.current_direction = rotate_vector(self.turn, self.current_direction[0], self.current_direction[1])
                ########################################

                time.sleep(1)

                ###########################################################################################################################################

        elif state == "FREE_BALL_1_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

            # OFF
            #####################################

            ball_field = radial(self.world.ball, 1, -100)

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)
            block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)
            block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            if self.turn != 180:
                self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.current_direction = potential.last_direction
            self.local_potential, self.points = potential.get_local_potential()

            # MOTION
            #######################################

            ########################################

            time.sleep(.7)

            ###########################################################################################################################################

        elif state == "FREE_BALL_BOTH_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

            # OFF
            #####################################

            ball_field = radial(self.world.ball, 1, -100)

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)
            block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)
            block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            if self.turn != 180:
                self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.current_direction = potential.last_direction
            self.local_potential, self.points = potential.get_local_potential()

            # MOTION
            #######################################

            ########################################

            time.sleep(.7)

            ###########################################################################################################################################

        elif state == "FREE_BALL_NONE_GOALSIDE":

            # ON
            #####################################

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

            # OFF
            #####################################
            ball_field = radial(self.world.ball, 1, -100)

            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)
            block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)
            block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            if self.turn != 180 or self.current_direction is None:
                self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.local_potential, self.points = potential.get_local_potential()

            # MOTION
            #######################################

            ########################################


            ###########################################################################################################################################

        elif state == "ENEMY1_BALL_TAKE_GOAL":

            # ON
            #####################################
            ball_field = radial(self.world.ball, 1, -100)

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            block_goal_enemy1 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            # OFF
            #####################################

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)
            block_goal_enemy2 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            if self.turn != 180:
                self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.current_direction = potential.last_direction
            self.local_potential, self.points = potential.get_local_potential()

            # MOTION
            #######################################

            ########################################

            time.sleep(1)

            ###########################################################################################################################################

        elif state == "ENEMY2_BALL_TAKE_GOAL":

            # ON
            #####################################
            ball_field = radial(self.world.ball, 1, -100)

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            block_goal_enemy2 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            # OFF
            #####################################

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)
            block_goal_enemy1 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            if self.turn != 180:
                self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.current_direction = potential.last_direction
            self.local_potential, self.points = potential.get_local_potential()

            # MOTION
            #######################################

            ########################################

            time.sleep(.7)

            ###########################################################################################################################################

        elif state == "ENEMY_BALL_TAKE_PASS":

            # ON
            #####################################
            ball_field = radial(self.world.ball, 1, -100)

            friend_field = solid_field(self.world.friend.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = solid_field(self.world.enemy1.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = solid_field(self.world.enemy2.position, 2, 100000, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)
            catch_up = step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 0, 0)

            block_pass = finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -10000)

            # OFF
            #####################################

            free_up_pass_enemy1 = finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)
            free_up_pass_enemy2 = finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
            free_up_goal_enemy1 = finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
            free_up_goal_enemy2 = finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)

            block_goal_enemy2 = finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)
            block_goal_enemy1 = finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -10000)

            bad_minima_goal = infinite_axial(self.world.venus.position, (self.world.their_goalX, self.world.their_goalmeanY), 2000, 0, 0)
            bad_minima_pass = infinite_axial(self.world.venus.position, self.world.friend.position, 2000, 0, 0)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            if self.turn != 180:
                self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = Potential(self.current_point, self.current_direction, self.world, ball_field, friend_field, enemy1_field, enemy2_field,
                                             free_up_pass_enemy1, free_up_pass_enemy2, free_up_goal_enemy1,
                                             free_up_goal_enemy2, block_pass,
                                             block_goal_enemy1, block_goal_enemy2,  advance, catch_up, bad_minima_pass, bad_minima_goal)

            self.current_direction = potential.last_direction
            self.local_potential, self.points = potential.get_local_potential()

            # MOTION
            #######################################

            ########################################

            time.sleep(.6)

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

    def move_attack(self, grab=None):
        """Executes command to go to minimum potential and returns robot direction after the movement"""
        x, y = np.where(self.local_potential == self.local_potential.min())
        indices = np.array([x, y]).T.tolist()
        if [2, 2] in indices:
            return TOP, self.points[2, 2]
        elif [1, 2] in indices or [0, 1] in indices or [0, 3] in indices:
            self.commands.forward(grab)
            return TOP, self.points[1, 2]
        elif [1, 1] in indices or [1, 0] in indices:
            self.commands.forward_left(grab)
            return LEFT, self.points[1, 1]
        elif [1, 3] in indices or [1, 4] in indices:
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
            if self.moving:
                self.commands.pause()
            self.commands.turn(180, grab)
            return BOTTOM, self.points[2, 2]
        elif [3, 1] in indices or [3, 0] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.turn(180, grab)
            return BOTTOM, self.points[2, 2]
        elif [3, 3] in indices or [3, 4] in indices:
            if self.moving:
                self.commands.pause()
            self.commands.turn(180, grab)
            return BOTTOM, self.points[2, 2]

    def move_defense(self, grab=None):
        """Executes command to go to minimum potential and returns robot direction after the movement"""
        x, y = np.where(self.local_potential == self.local_potential.min())
        indices = np.array([x, y]).T.tolist()
        if [2, 2] in indices:
            return TOP, self.points[2, 2]
        elif [1, 2] in indices or [0, 1] in indices or [0, 3] in indices:
            self.commands.forward(grab)
            return TOP, self.points[1, 2]
        elif [1, 1] in indices or [1, 0] in indices:
            self.commands.forward_left(grab)
            return LEFT, self.points[1, 1]
        elif [1, 3] in indices or [1, 4] in indices:
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
            self.commands.backward(grab)
            return TOP, self.points[3, 2]
        elif [3, 1] in indices or [3, 0] in indices:
            self.commands.backward_left(grab)
            return RIGHT, self.points[3, 1]
        elif [3, 3] in indices or [3, 4] in indices:
            self.commands.backward_right(grab)
            return LEFT, self.points[3, 3]

    def grab_range(self):
        refAngle = math.atan2(self.world.venus.orientation[1], self.world.venus.orientation[0])
        ballAngle, ballLength = self.calculate_angle_length_ball()
        if abs(ballLength) < 25 and abs(refAngle-ballLength) < 45:
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

    def approach(self, angle, motion_length):
        print("Turning " + str(angle) + " deg then going " + str(motion_length) + " cm")
        self.commands.c(angle)
        #time.sleep(.4)
        self.commands.f(motion_length)
        #time.sleep(.4)

    def grab_ball(self):

        angle, motion_length = self.calculate_angle_length_ball()

        while motion_length > 80:
            self.approach(angle, 40)
            angle, motion_length = self.calculate_angle_length_ball()

        time.sleep(1)
        angle, motion_length = self.calculate_angle_length_ball()
        if motion_length > 30:
            motion_length -= 30
        else:
            motion_length = 0
        print("LAST BEFORE LAST: turning " + str(angle) + " deg, going " + str(motion_length) + " cm")
        self.approach(angle, motion_length)

        time.sleep(1)
        angle, motion_length = self.calculate_angle_length_ball()
        print("LAST: Turning " + str(angle) + " deg")
        self.commands.c(angle)

        self.commands.open_wide()
        time.sleep(.4)

        print("LAST: Going " + str(motion_length) + " cm")

        motion_length -= 8 #12 #13
        if motion_length < 5:
            motion_length = 5

        self.commands.f(motion_length)
        self.commands.g()
        time.sleep(1)

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
                return self.constant/math.pow(distance_to, self.gradient)
            else:
                return 0
        else:
            distance_to = abs(rotated_point[1] - rotated_start[1])
            if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to < self.influence_range:
                return self.constant/math.pow(distance_to, self.gradient)
            else:
                return 0

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
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
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
            return self.constant*math.log((b + math.sqrt(b**2 + distance_to**2))/(a + math.sqrt(a**2 + distance_to**2)), math.e)
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

        if left_ref < rotated_point[0] < right_ref:
            b = right_ref - rotated_point[0]
            a = left_ref - rotated_point[0]
            distance_to = abs(rotated_point[1] - start_field[1])
            return self.constant*math.log((b + math.sqrt(b**2 + distance_to**2))/(a + math.sqrt(a**2 + distance_to**2)), math.e) #todo no gradient
        elif right_ref <= rotated_point[0]: # outside
            return self.constant/((x-right_ref)**2 + (y-right_ref)**2)
        elif left_ref >= rotated_point[0]: # outside
            return self.constant/((x-left_ref)**2 + (y-left_ref)**2)

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
        separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)#
        if separation > self.influence_area:
            return 0
        elif separation > self.forbidden:
            return self.constant/math.pow(math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2), self.gradient)
        else:
            if self.constant <= 0:
                return -9999*self.constant
            else:
                return 9999*self.constant

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
                    return -9999*self.constant
                else:
                    return 9999*self.constant
        else:
            return 0

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
