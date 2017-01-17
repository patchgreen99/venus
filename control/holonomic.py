import time
import multiprocessing

import numpy as np
import math

from control.protocol import RobotProtocol
from strategy.simple_holonomic import SimpleStrategy
from strategy.highstrategy import StrategyTools
from strategy.world import World
from strategy.game import Game
#from vision2.sender import *
from vision.vision import Vision

FRONT_RIGHT = 3
BACK_RIGHT = 0
BACK_LEFT = 1
FRONT_LEFT = 2
MOTOR_GRAB = 4
MOTOR_KICK = 5


def sign(x):
    return 1 if x >= 0 else -1


class Commands:
    def __init__(self):
        self.protocol = None
        self.vision_process = None
        self.world = None
        self.strategy = None
        self.highstrategy = None
        self.game = None
        print("! Remember to call:")
        print("! init <room: 0/1> <team_color: blue/yellow> <our_single_spot_color: green/pink>")
        print("! vision")
        print("! connect <device_no>")
        self.init()
        self.vision()
        self.connect()
        #self.highstrategy.main()

    def hs(self):
        self.highstrategy.main()

    def init(self, room_num=1, team_color='yellow', our_color='green', computer_goal=False):
        print("init: Room: %s, team color: %s, our single spot color: %s, computer goal: %s" %
              (room_num, team_color, our_color, computer_goal))
        self.world = World(int(room_num), team_color, our_color, computer_goal)
        self.strategy = SimpleStrategy(self.world, self)
        self.game = Game(self.world, self)
        self.highstrategy = StrategyTools(self.world, self, self.game, self.strategy)

    def connect(self, device_no='0'):
        print("connect: Connecting to RF stick")
        self.protocol = RobotProtocol('/dev/ttyACM' + device_no)

    def vision(self):
        if not self.vision_process:
            print("vision: Starting vision")
            self.vision_process = multiprocessing.Process(target=Vision, args=(self.world,))
            self.vision_process.start()

    def map(self, state, num):
        self.game.mid(state, True, num)

    def test(self, state):
        while True:
            self.game.mid(state, False)

    def move(self, direction, angle): # direction is between our orientation and where we want to go
        dir = int(direction)
        ang = int(angle)
        if dir < 0:
            d = 45 - dir
        else:
            d = -(dir - 45)

        a = -math.radians(ang)
        dir = math.radians(d)
        idea = np.array([np.cos(dir), np.sin(dir), a])
        rad = 0.1
        m = np.array([[1, 0, rad],
                      [0, -1, rad],
                      [-1, 0, rad],
                      [0, 1, rad]])

        movement = np.dot(m, idea)
        sizes = np.fabs(movement)
        factor = np.amax(sizes)
        movement = np.multiply(100.0/factor, movement)

        movement = movement.round()
        s = np.sign(movement)
        movement = s*((40*abs(movement))/100 + 60)
        self.protocol.move_forever([(0, int(movement[0])), (1, int(movement[1])), (2, int(movement[2])), (3, int(movement[3])), ])
        #self.protocol.move(20, [(0, movement[0]), (1, movement[1]), (2, movement[2]), (3, movement[3]), ], wait=True)

    def singlemove(self, direction, angle): # direction is between our orientation and where we want to go
        dir = int(direction)
        ang = int(angle)
        if dir < 0:
            d = 45 - dir
        else:
            d = -(dir - 45)

        a = -math.radians(ang)
        dir = math.radians(d)
        idea = np.array([np.cos(dir), np.sin(dir), a])
        rad = 0.1
        m = np.array([[1, 0, rad],
                      [0, -1, rad],
                      [-1, 0, rad],
                      [0, 1, rad]])

        movement = np.dot(m, idea)
        sizes = np.fabs(movement)
        factor = np.amax(sizes)
        movement = np.multiply(100.0/factor, movement)

        movement = movement.round()
        s = np.sign(movement)
        movement = s*((40*abs(movement))/100 + 60)

        awayfromwall = 1
        self.protocol.move(awayfromwall, [(0, int(movement[0])), (1, int(movement[1])), (2, int(movement[2])), (3, int(movement[3])), ], wait=True)
        #self.protocol.move(20, [(0, movement[0]), (1, movement[1]), (2, movement[2]), (3, movement[3]), ], wait=True)


    def penalty_attack(self, clockno):
        self.highstrategy.penalty_attack(clockno)

    def penalty_defend(self):
        self.highstrategy.penalty_defend()

    def runstrategy(self):
        self.highstrategy.main()

    def attackwithball(self):
        self.highstrategy.attackwithball()

    def ballwithenemy(self, no):
        self.highstrategy.ballwithenemy(int(no))

    def ballindefensearea(self):
        a= self.highstrategy.ballindefensearea()
        print(a)

    def ballwithfriend(self):
        self.highstrategy.ballwithfriend()

    def f(self, x):
        """Move forward, negative x means backward"""
        x = int(x)
        s = sign(x)
        x = abs(x)
        # Calibrated for the holonomic robot on 27 March, only forward
        x = 5.3169850194 * x - 12
        x = int(x)
        if x > 0:
            self.protocol.move(x, [(0, 100 * s), (1, -100 * s), (2, -100 * s), (3, 100 * s)], wait=True)

    def c(self, x):
        """Rotate clockwise, negative x means counter-clockwise"""
        x = int(x)
        s = sign(x)
        x = abs(x)

        # Calibrated for the holonomic robot on 30 March
        if s > 0:
            if x > 90:
                x = 0.8 * x - 37.0
            else:
                x = 0.0015306535 * (x ** 2) + 0.3025825153 * x
        else:
            if x > 90:
                x = 0.823333333 * x - 33.5
            else:
                x = 0.001206074 * (x ** 2) + 0.3634378289 * x
        x = int(x)

        if x > 0:
            self.protocol.move(x, [(0, -80 * s), (1, -80 * s), (2, -80 * s), (3, -80 * s)], wait=True)

    def s(self):
        self.protocol.stop()

    def k(self):
        # self.protocol.move(500, [(4, -100)], time=True)
        self.protocol.move_forever([(0, -100), (1, 100), (2, 100), (3, -100), ])
        time.sleep(0.5)
        self.protocol.move_forever([(0, 100), (1, -100), (2, -100), (3, 100), ])
        time.sleep(1)
        self.protocol.stop()

    def o(self):
        self.protocol.move(400, [(4, -100)], time=True, wait=True)

    def g(self):
        self.protocol.move(800, [(4, 80)], time=True, wait=True)

    def ss(self, x):
        x = int(x)
        s = sign(x)
        x = abs(x)

        if x < 90:
            return

        if x > 90:
            if s > 0:
                x = 0.0008417761 * (x ** 2) + 0.3865014241 * x - 41.5767918089
            else:
                x = 0.0013813605 * (x ** 2) + 0.1536110506 * x - 25.1058020478
            x = int(x)
            self.protocol.schedule(x, 0, [(0, -100 * s), (1, -100 * s), (2, -100 * s), (3, -100 * s)])

        self.protocol.schedule(200, 0, [(0, -100 * s), (1, -100 * s), (2, -100 * s), (3, -100 * s)], grab=-400)

        #self.protocol.move(400, [(4, -100)], time=True)

    def flush(self):
        self.protocol.flush()

    def ee(self, x):
        x = int(x)
        s = sign(x)
        self.protocol.move(500, [(4, -100)], time=True)
        self.protocol.move(200, [(0, -100 * s), (1, -100 * s), (2, -100 * s), (3, -100 * s)], wait=True)

    def w(self):
        print self.world

    def query_ball(self):
        if self.world.room_num == 0:
            threshold = 180
        else:
            threshold = 192
        a = self.protocol.query_ball(threshold)
        print("We have the ball: %s" % a)
        return a

    def pass_ball(self):
        self.strategy.pass_ball()

    def catch_ball(self):
        self.strategy.catch_ball()

    def goal(self):
        self.strategy.goal()

    def who(self):
        print "venus " + str(self.world.venus)
        print "friend " + str(self.world.friend)
        print "enemy1 " + str(self.world.enemy1)
        print "enemy2 " + str(self.world.enemy2)

        print "Who has the ball?"
        if self.world.venus.hasBallInRange[0]:
            print "0: venus"
        if self.world.friend.hasBallInRange[0]:
            print "1: friend"
        if self.world.enemy1.hasBallInRange[0]:
            print "2: enemy1"
        if self.world.enemy2.hasBallInRange[0]:
            print "3: enemy2"

    def rr(self):
        self.protocol.move_forever([(0, 70), (1, -100), (2, -70), (3, 100), ])

    def stopped(self):
        self.protocol.block_until_stop()
        print("Now it has stopped")

    def v(self):
        while True:
            #print "---"
            #print self.world.ball_velocity[0], self.world.ball_velocity[1]
            print math.sqrt(self.world.ball_velocity[0]**2 + self.world.ball_velocity[1]**2)/6.0

    def j(self):
        angle, motion_length = self.strategy.calculate_angle_length_ball()
        print angle, motion_length
        self.c(angle)

    def b(self):
        last = self.world.ball_moving[0]
        i = 0
        while True:
            this = self.world.ball_moving[0]
            if last == 0 and this == 1:
                print "\a%d Started moving" % i
                i += 1
            elif last == 1 and this == 0:
                print "\a%d Stopped moving" % i
                i += 1
            last = this

    def gg(self):
        while True:
            self.game.mid("FREE_BALL_YOURS", False)
