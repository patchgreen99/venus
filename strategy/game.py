import math
import time
import numpy as np
import potentials as P

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
        self.current_force = None
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
    def start(self, state, num):
        if state == "FREE_BALL_YOURS":
            pass
        elif state == "ATTACK_PASS":
            pass
        elif state == "ATTACK_GOAL":
            pass
        elif state == "RECEIVE_PASS":
            pass
        elif state == "BLOCK_BALL":
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
    def mid(self, state, sim, num):
        if state == "FREE_BALL_YOURS":

            # ON
            #####################################

            ball_field = P.radial(self.world.ball, 1, -200)# -5

            friend_field = P.solid_field(self.world.friend.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)


            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead

            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, advance, catch_up] #todo add advance and catch up
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)


            # MOTION
            #######################################
            if sim is False:
                angle, motion_length = self.calculate_angle_length_ball()
                #print "moving = " + str(self.world.ball_moving[0])
                if motion_length < 40 and potential.get_potential() < -0.7:
                    self.world.sensor = True
                    self.world.undistort[0] = 1
                    print("HAS BALL IN RANGE")
                    self.commands.s()
                    time.sleep(.5)
                    angle, motion_length = self.calculate_angle_length_ball()
                    self.commands.o()
                    self.commands.c(angle)

                    angle, motion_length = self.calculate_angle_length_ball()

                    if PITCH_COLS/4.0 <= self.world.venus.position[0] <= 3.0*PITCH_COLS/4.0:
                        #print "FIX A"
                        fix = 7
                    else:
                        #print "FIX B"
                        fix = 2
                    self.commands.f(motion_length - fix)  # todo hack
                    self.commands.g()
                    time.sleep(.5)
                    # todo need to implement considering objects
                    #if self.commands.query_ball() or self.commands.query_ball():
                    #    print("It thinks it has the ball")
                    #    #exit(0)
                else:
                    self.current_force = potential.get_force()
                    #print self.current_force
                    bearing = self.calculate_angle(self.current_force)
                    #print bearing
                    self.commands.move(bearing, 0)
                    #self.local_potential, self.points = potential.get_local_potential()

            ########################################

            # TESTING
            ########################################
            else:
                potential.map(num)

            ########################################

            ###########################################################################################################################################

        elif state == "FREE_BALL_2_GOALSIDE":

            # ON
            #####################################

            friend_field = P.solid_field(self.world.friend.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), POSITION_INFLUENCE_RANGE, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), POSITION_INFLUENCE_RANGE, 1, 0)

            if self.world.enemy1.out[0] == 0:
                free_up_pass_enemy1 = P.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_pass_enemy1 = P.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 0)

            if self.world.enemy2.out[0] == 0:
                free_up_goal_enemy2 = P.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_goal_enemy2 = P.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 0)
            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [friend_field, enemy1_field, enemy2_field, free_up_pass_enemy1, free_up_goal_enemy2, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if sim is False:
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)

            ########################################

            # TESTING
            ########################################
            else:
                potential.map(num)
            ########################################

            ###########################################################################################################################################

        elif state == "FREE_BALL_1_GOALSIDE":

            # ON
            #####################################

            friend_field = P.solid_field(self.world.friend.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            if self.world.enemy2.out[0] == 0:
                free_up_pass_enemy2 = P.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_pass_enemy2 = P.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 0)

            if self.world.enemy1.out[0] == 0:
                free_up_goal_enemy1 = P.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_goal_enemy1 = P.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 0)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potential = [friend_field, enemy1_field, enemy2_field, free_up_pass_enemy2, free_up_goal_enemy1,advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potential)

            # MOTION
            #######################################
            if sim is False:
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)

            ########################################

            # TESTING
            ########################################
            else:
                potential.map()
            ########################################

            ###########################################################################################################################################

        elif state == "FREE_BALL_BOTH_GOALSIDE":

            # ON
            #####################################

            friend_field = P.solid_field(self.world.friend.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            if self.world.enemy2.out[0] == 0:
                free_up_goal_enemy2 = P.finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_goal_enemy2 = P.finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 0)

            if self.world.enemy1.out[0] == 0:
                free_up_goal_enemy1 = P.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_goal_enemy1 = P.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), POSITION_INFLUENCE_RANGE, 1.3, 2.5)

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
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)

            ########################################

            # TESTING
            ########################################
            else:
                potential.map()

            ########################################
            ###########################################################################################################################################

        elif state == "FREE_BALL_NONE_GOALSIDE":

            # ON
            #####################################

            friend_field = P.solid_field(self.world.friend.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 15, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            if self.world.enemy1.out[0] == 0:
                free_up_pass_enemy1 = P.finite_axial_outside(self.world.enemy2.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_pass_enemy1 = P.finite_axial_outside(self.world.enemy2.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 0)

            if self.world.enemy2.out[0] == 0:
                free_up_pass_enemy2 = P.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 2.5)
            else:
                free_up_pass_enemy2 = P.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, POSITION_INFLUENCE_RANGE, 1.3, 0)

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
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
            ########################################

            # TESTING
            ########################################
            else:
                potential.map()

            ########################################

            ###########################################################################################################################################

        elif state == "ENEMY1_BALL_TAKE_GOAL":

            # ON
            #####################################
            ball_field = P.radial(self.world.ball, 1, 0)

            friend_field = P.solid_field(self.world.friend.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            block_goal_enemy1 = P.finite_axial_inside(self.world.enemy1.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -5)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_goal_enemy1, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################
            if not sim and potential.get_potential() > -30:
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
                print "velocity is " + str(math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2))

            ########################################

            # TESTING
            ########################################
            elif sim:
                potential.map(num)
            ########################################
            elif (self.world.enemy1.hasBallInRange[0] == 0 and self.world.enemy2.hasBallInRange[0] == 0) or self.world.ball_moving[0] == 1:
                ball_field = P.radial(self.world.ball, 1, -100)
                potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_goal_enemy1, advance, catch_up]
                potential = Potential(self.current_point, self.current_direction, self.world, potentials)
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
            else:
                self.world.undistort[0] = 1
                self.commands.s()
                self.commands.o()
                angle, length = self.calculate_angle_length_ball()
                self.commands.c(angle)
            ###########################################################################################################################################

        elif state == "ENEMY2_BALL_TAKE_GOAL":

            # ON
            #####################################
            ball_field = P.radial(self.world.ball, 1, 0)

            friend_field = P.solid_field(self.world.friend.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            block_goal_enemy2 = P.finite_axial_inside(self.world.enemy2.position, (self.world.our_goalX,self.world.our_goalmeanY), 1, -5)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_goal_enemy2,  advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)


            # MOTION
            #######################################

            if not sim and potential.get_potential() > -30:
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
                print "velocity is " + str(math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2))
            ########################################

            # TESTING
            ########################################
            elif sim:
                potential.map(num)

            ########################################
            elif (self.world.enemy1.hasBallInRange[0] == 0 and self.world.enemy2.hasBallInRange[0] == 0) or self.world.ball_moving[0] == 1:
                ball_field = P.radial(self.world.ball, 1, -100)
                potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_goal_enemy2,  advance, catch_up]
                potential = Potential(self.current_point, self.current_direction, self.world, potentials)
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
            else:
                self.world.undistort[0] = 1
                self.commands.s()
                self.commands.o()
                angle, length = self.calculate_angle_length_ball()
                self.commands.c(angle)

            ###########################################################################################################################################

        elif state == "ENEMY_BALL_TAKE_PASS":

            # ON
            #####################################
            ball_field = P.radial(self.world.ball, 1, 0)

            friend_field = P.solid_field(self.world.friend.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy1_field = P.solid_field(self.world.enemy1.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)
            enemy2_field = P.solid_field(self.world.enemy2.position, 1, 60, ROBOT_SIZE, ROBOT_INFLUENCE_SIZE)

            advance = P.step_field(self.world.friend.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)
            catch_up = P.step_field(self.world.venus.position, rotate_vector(-90, get_play_direction(self.world)[0], get_play_direction(self.world)[1]), 2000, 1, 0)

            block_pass = P.finite_axial_inside(self.world.enemy1.position, self.world.enemy2.position, 1, -5)

            # BUILD FIELD AND NEXT POSITION AND DIRECTIONS
            ####################################
            # todo too reliant on vision, must pick what to use for look ahead
            self.current_point = (self.world.venus.position[0], self.world.venus.position[1])
            self.current_direction = (self.world.venus.orientation[0], self.world.venus.orientation[1])

            potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_pass, advance, catch_up]
            potential = Potential(self.current_point, self.current_direction, self.world, potentials)

            # MOTION
            #######################################

            if not sim and potential.get_potential() > -30:
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
                print "velocity is " + str(math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2))
            ########################################

            # TESTING
            ########################################
            elif sim:
                potential.map()
            ########################################
            elif (self.world.enemy1.hasBallInRange[0] == 0 and self.world.enemy2.hasBallInRange[0] == 0) or self.world.ball_moving[0] == 1:
                ball_field = P.radial(self.world.ball, 1, -100)
                potentials = [ball_field, friend_field, enemy1_field, enemy2_field, block_pass, advance, catch_up]
                potential = Potential(self.current_point, self.current_direction, self.world, potentials)
                self.current_force = potential.get_force()
                #print self.current_force
                bearing = self.calculate_angle(self.current_force)
                #print bearing
                self.commands.move(bearing, 0)
            else:
                self.world.undistort[0] = 1
                self.commands.s()
                self.commands.o()
                angle, length = self.calculate_angle_length_ball()
                self.commands.c(angle)

            ###########################################################################################################################################

       ##############################################################################################

        elif state == "ATTACK_PASS":
            self.world.kicked = True
            self.world.undistort[0] = 1
            # pass ball to the friend, when attacking
            self.commands.pass_ball()

            ###########################################################################################################################################

        elif state == "ATTACK_GOAL":
            self.world.kicked = True
            self.world.undistort[0] = 1
            # you're in the good position to score
            self.commands.goal()

            ###########################################################################################################################################

        elif state == "RECEIVE_PASS":
            self.world.sensor = True
            self.world.undistort[0] = 1
            # you should be in the good position to catch the ball
            self.commands.catch_ball()


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

    def calculate_angle(self, motion_vec):
        orientation_vec = np.array([self.world.venus.orientation[0], self.world.venus.orientation[1]])
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

        return angle

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
