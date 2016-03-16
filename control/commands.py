import time
import multiprocessing

import numpy as np

from control.protocol import RobotProtocol
from strategy.simple import SimpleStrategy
from strategy.highstrategy import StrategyTools
from strategy.world import World
from strategy.game import Game
from vision.vision import Vision

MOTOR_LEFT = 0
MOTOR_RIGHT = 1
MOTOR_TURN = 2
MOTOR_KICK = 3
MOTOR_GRAB = 4


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

    def query_ball(self):
        a = self.protocol.query_ball()
        print("We have the ball: %s" % a)
        return a

    def start_game(self, case_no):
        #1 is when venus kicks off the game
        if case_no == 1:
            self.highstrategy.kick_off_us()
        else:
            self.highstrategy.kick_off_them()
        self.runstrategy()

    def penalty_attack(self):
        self.highstrategy.penalty_attack(self)

    def penalty_defend(self):
        self.highstrategy.penalty_defend(self)

    def runstrategy(self):
        self.highstrategy.main()

    def attackwithball(self):
        self.highstrategy.attackwithball()

    def ballwithenemy(self, no):
        self.highstrategy.ballwithenemy(int(no))

    def ballindefensearea(self):
        a= self.highstrategy.ballindefensearea()
        print(a)

    def grab_ball(self):
        self.strategy.grab_ball()

    def goal(self):
        self.strategy.goal()

    def grab_goal(self):
        self.strategy.grab_goal()

    def pass_ball(self):
        self.strategy.pass_ball()

    def catch_ball(self):
        self.strategy.catch_ball()

    def intercept(self):
        self.strategy.intercept()

    def catch_pass(self):
        self.strategy.catch_pass()

    def pw(self):
        print(self.world)

    def pot(self):
        while True:
            self.game.mid("ENEMY1_BALL_TAKE_GOAL")

    def pot1(self):
        while True:
            self.game.mid("FREE_BALL_1_GOALSIDE")

    def positionTest(self):
        print self.world.our_goalX, self.world.our_goalmeanY


    def flush(self):
        self.protocol.flush()

    def test1(self):
        self.game.local_potential = np.array([[666, 100, 666, 100, 666],
                                              [666, 100, 0, 0, 666],
                                              [666, 100, 1, 100, 666],
                                              [666, 100, 666, 100, 666],
                                              [666, 100, 666, 100, 666]], dtype=np.float64)
        self.game.points = np.arange(50).reshape((5, 5, 2))
        print self.game.move()

    def test2(self):
        # for x in range(0, 10):
        #     self.forward_right()
        self.forward_left()
        self.forward_right()
        self.pause()
        self.sharp_left()
        self.forward_left()
        self.pause()
        self.sharp_right()
        self.forward_right()

    def test3(self):
        self.forward()
        self.pause()
        self.sharp_left()

    def test4(self):
        """Test of swerving"""
        self.forward()
        self.swerve_left(200)
        self.swerve_right(200)
        self.swerve_left(200)
        self.swerve_right(200)
        self.forward()

    def stopped(self):
        self.protocol.block_until_stop()
        print("Now it has stopped")

    def turn(self, x, grab=None):
        """Turn clockwise, negative means counter-clockwise"""
        print("  Turn %d deg" % int(x))

        x = int(x)
        s = sign(x)
        x = abs(x)

        # Last calibration: 14 March

        if s > 0:  # Clockwise
            if x > 90:
                x = 1.8055555556 * x - 85.0
            else:
                x = 0.0067224213 * (x ** 2) + 0.2676702509 * x

        else:  # Counter-clockwise
            if x > 90:
                x = 1.7477777778 * x - 93.5
            else:
                x = 0.0063082437 * (x ** 2) + 0.1935483871 * x
        x = int(x)
        if x > 0:
            self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_LEFT, -100 * s),
                                                   (MOTOR_RIGHT, 100 * s),
                                                   (MOTOR_TURN, 100 * s)], self.grab_time(grab))

    def forward_forever(self):
        """Move forward forever"""
        self.protocol.move_forever([(MOTOR_LEFT, -100),
                                    (MOTOR_RIGHT, -100)])

    def backward_forever(self):
        """Move backward forever"""
        self.protocol.move_forever([(MOTOR_LEFT, 100),
                                    (MOTOR_RIGHT, 100)])

    def swerve_right(self, x):
        """Swerve right whilst moving forwards"""
        self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_TURN, 100),
                                               (MOTOR_LEFT, -100),
                                               (MOTOR_RIGHT, -100)])

    def swerve_left(self, x):
        """Swerve left whilst moving forwards"""
        self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_TURN, -100),
                                               (MOTOR_LEFT, -100),
                                               (MOTOR_RIGHT, -100)])

    def pause(self):
        """Pause between motions that immediately change motor direction"""
        #self.protocol.schedule_pause(400)

    def grab_time(self, grab):
        if grab == 'T':
            grab = True
        elif grab == 'F':
            grab = False

        if grab is None:
            return 0
        elif grab:
            return -300
        else:
            return 400

    def forward(self, grab=None):
        """Move a cell forward"""
        print("  Forward")
        self.protocol.move(80, [(MOTOR_LEFT, -100),
                                (MOTOR_RIGHT, -100)], wait=True)
        # self.protocol.schedule(90, MOTOR_LEFT, [(MOTOR_LEFT, -100),
        #                                          (MOTOR_RIGHT, -100)], self.grab_time(grab))

    def backward(self, grab=None):
        """Move a cell backward"""
        print("  Backward")
        self.protocol.move(90, [(MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, 100)], wait=True)
        # self.protocol.schedule(70, MOTOR_LEFT, [(MOTOR_LEFT, 100),
        #                                          (MOTOR_RIGHT, 100)], self.grab_time(grab))

    def forward_left(self, grab=None):
        """Move forward and to left"""
        print("  Forward left")
        self.protocol.move(150, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, -80),
                                                 (MOTOR_RIGHT, -100)], wait=True)
        #self.protocol.move(50, [(MOTOR_LEFT, -100),
        #                                        (MOTOR_RIGHT, -100)], wait=True)

        # self.protocol.schedule(170, MOTOR_TURN, [(MOTOR_TURN, -100),
        #                                          (MOTOR_LEFT, -80),
        #                                          (MOTOR_RIGHT, -100)], self.grab_time(grab))
        # self.protocol.schedule(50, MOTOR_LEFT, [(MOTOR_LEFT, -100),
        #                                         (MOTOR_RIGHT, -100)])

    def forward_right(self, grab=None):
        """Move forward and to right"""
        print("  Forward right")
        self.protocol.move(240, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -80)], wait=True)

        #self.protocol.move(50, [(MOTOR_LEFT, -100),
         #                                        (MOTOR_RIGHT, -100)], wait=True)

        # self.protocol.schedule(170, MOTOR_TURN, [(MOTOR_TURN, 100),
        #                                          (MOTOR_LEFT, -100),
        #                                          (MOTOR_RIGHT, -60)], self.grab_time(grab))
        # self.protocol.schedule(50, MOTOR_RIGHT, [(MOTOR_LEFT, -100),
        #                                          (MOTOR_RIGHT, -100)])

    def backward_left(self, grab=None):
        """Move backward and to left"""
        print("  Backward left")
        #self.protocol.move(20, [(MOTOR_LEFT, 100),
        #                                      (MOTOR_RIGHT, 100)], wait=True)
        self.protocol.move(190, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, 80),
                                                 (MOTOR_RIGHT, 100)], wait=True)
        # self.protocol.schedule(3, MOTOR_LEFT, [(MOTOR_LEFT, 100),
        #                                         (MOTOR_RIGHT, 100)], self.grab_time(grab))
        # self.protocol.schedule(190, MOTOR_TURN, [(MOTOR_TURN, 100),
        #                                          (MOTOR_LEFT, 80),
        #                                          (MOTOR_RIGHT, 100)])

    def backward_right(self, grab=None):
        """Move backward and to right"""
        print("  Backward right")
        #self.protocol.schedule(20, MOTOR_RIGHT, [(MOTOR_LEFT, 100),
        #                                       (MOTOR_RIGHT, 100)], self.grab_time(grab))

        self.protocol.move(250, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, 80)], wait=True)

        #this was commented out before changing to move:


        # self.protocol.schedule(230, MOTOR_TURN, [(MOTOR_TURN, -100),
        #                                          (MOTOR_LEFT, 100),
        #                                          (MOTOR_RIGHT, 80)])

    def sharp_left(self, grab=None):
        """Move to a cell left"""
        print("  Sharp left")
        self.c(-90)
        # self.protocol.move(12, [(MOTOR_TURN, -100),
        #                                         (MOTOR_LEFT, 100),
        #                                         (MOTOR_RIGHT, -100)], wait=True)
        self.protocol.move(80, [(MOTOR_LEFT, -100),
                                                (MOTOR_RIGHT, -100)], wait=True)
        # self.protocol.schedule(12, MOTOR_TURN, [(MOTOR_TURN, -100),
        #                                         (MOTOR_LEFT, 100),
        #                                         (MOTOR_RIGHT, -100)], self.grab_time(grab))
        # self.protocol.schedule(50, MOTOR_LEFT, [(MOTOR_LEFT, -100),
        #                                         (MOTOR_RIGHT, -100)])

    def sharp_right(self, grab=None):
        """Move to a cell right"""
        print("  Sharp right")
        self.c(90)
        # self.protocol.move(18, [(MOTOR_TURN, 100),
        #                                         (MOTOR_LEFT, -100),
        #                                         (MOTOR_RIGHT, 100)], wait=True)
        self.protocol.move(80, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)], wait=True)
        # self.protocol.schedule(18, MOTOR_TURN, [(MOTOR_TURN, 100),
        #                                         (MOTOR_LEFT, -100),
        #                                         (MOTOR_RIGHT, 100)], self.grab_time(grab))
        # self.protocol.schedule(50, MOTOR_RIGHT, [(MOTOR_LEFT, -100),
        #                                          (MOTOR_RIGHT, -100)])

    def f(self, x):
        """Move forward, negative x means backward"""
        x = int(x)
        s = sign(x)
        if x > 0:
            if x > 17:
                x = 7.5145299398 * x - 80.3832872418
            else:
                x = 0.0432484778 * (x ** 2) + 2.1632771388 * x
        else:
            x = 13.964509832 * -x - 75.2448595458
        x = int(x)
        if x > 0:
            self.protocol.move(x, [(MOTOR_LEFT, -100 * s),
                                   (MOTOR_RIGHT, -100 * s)], wait=True)

    def c(self, x):
        """Rotate clockwise, negative x means counter-clockwise"""
        x = int(x)
        s = sign(x)
        x = abs(x)

        # Last calibration: 12 March

        if x > 90:
            x = 0.9933333333 * x - 43
        else:
            x = 0.0018797292 * (x ** 2) + 0.420501791 * x
        x = int(x)

        if x > 0:
            self.protocol.move(x, [(MOTOR_LEFT, -100 * s),
                                   (MOTOR_RIGHT, 100 * s),
                                   (MOTOR_TURN, 100 * s)], wait=True)

    def k(self, x):
        """Kick"""
        x = int(x)
        # Not using rotary encoders, granularity too low
        self.protocol.move(x, [(MOTOR_KICK, 100)], time=True)

    def g(self, x=-300):
        """Grab, positive x means release"""
        x = int(x)
        # This motor does not have rotary encoders
        self.world.grabber_open = x > 0
        self.protocol.move(abs(x), [(MOTOR_GRAB, 100 * sign(x))], time=True)

    def open_wide(self):
        self.g(400)

    def open_narrow(self):
        self.g(350)

    def x(self, x):
        """Kick and release"""
        x = int(x)
        self.k(x)
        self.open_narrow()

    def s(self):
        self.protocol.stop()

    def move(self, x, y, deg):
        """Milestone 1: Move"""
        x = int(x)
        y = int(y)
        deg = int(deg)

        print("First turn, clockwise")
        self.c(90)
        time.sleep(1)

        print("Go x")
        self.f(x)
        time.sleep(1)

        print("Second turn, counterclockwise")
        self.c(-85)

        print("Go y")
        time.sleep(1)
        self.f(y)

        print("Do final turn")
        time.sleep(1)
        self.c(deg)

    def kick(self, distance):
        """Milestone 1: Kick"""
        distance = int(distance)

        # Last calibration: 12 March

        time_value = 2.3530438329 * distance + 38.5507807011
        print("Time for kicking motor: " + str(time_value))
        self.x(time_value)
        '''
        if distance == 50:
            # time = 260
            time = 242
        elif distance == 100:
            # time = 290
            time = 275  # 295?
        elif distance == 150:
            # time = 310
            time = 303
        else:
            time = 0
        self.k(time)
        '''

    def transfer(self, filename, freq_hz):
        """Milestone 1: Communications and Timing"""
        freq_hz = float(freq_hz)
        seconds = 1.0 / freq_hz
        print("Transferring file '%s' at freq %fHz, %fs" %
              (filename, freq_hz, seconds))
        with open(filename, "rb") as f:
            byte = f.read(1)
            while byte != "":
                self.protocol.transfer(byte)
                time.sleep(seconds)
                byte = f.read(1)
                # self.p.read_all()

    def reset_input(self):
        self.protocol.reset_input()

    def block_goal(self, enemy_num):
        self.strategy.block_goal(int(enemy_num))
