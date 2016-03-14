from multiprocessing import Array, Value
import math

NO_VALUE = -1


class Robot:
    def __init__(self):
        self.position = Array('i', [NO_VALUE, NO_VALUE])
        self.orientation = Array('d', [NO_VALUE, NO_VALUE])
        self.out = Value('b')
        self.hasBallInRange = Value('b')

    def __str__(self):
        return "(pos: {} {}, ori: {})".format(self.position[0], self.position[1],
                                              self.orientation[0], self.orientation[1])


class World:
    def __init__(self, room_num, team_color, our_color, we_have_computer_goal):
        self.room_num = room_num
        self.team_color = team_color  # yellow or blue
        self.our_color = our_color  # green or pink
        self.enemy_color = 'yellow' if team_color == 'blue' else 'blue'
        self.other_color = 'green' if our_color == 'pink' else 'pink'
        self.we_have_computer_goal = we_have_computer_goal

        if self.room_num == 1:
            target = open('vision/pitch1.txt', 'r')
        else:
            target = open('vision/pitch0.txt', 'r')

        data = eval(target.read())
        self.read_pitch(data)
        target.close()

        self.ball = Array('i', [NO_VALUE, NO_VALUE]) # in pixels
        self.ball_velocity = Array('d', [NO_VALUE, NO_VALUE]) # pixels per frame
        self.ball_moving = Value('b')
        self.venus = Robot()
        self.friend = Robot()
        self.enemy1 = Robot()
        self.enemy2 = Robot()
        self.grabber_open = False

    def __str__(self):
        return "World state: ball {} {} {}, future ball {} {}, venus {}, friend {}, enemy1 {}, enemy2 {}".format(
            self.ball[0], self.ball[1], self.ball_moving.value, self.speed[0], self.speed[1],
            self.venus, self.friend, self.enemy1, self.enemy2)

    def read_pitch(self, data):
        if self.we_have_computer_goal:
            self.our_goalX = (data["leftgoal"][0][0] + data["leftgoal"][1][0] + data["leftgoal"][2][0])/3.0
            ys = [data["leftgoal"][0][1] , data["leftgoal"][1][1] , data["leftgoal"][2][1]]
            ys.sort()
            self.our_goallowY = ys[0]
            self.our_goalhighY = ys[2]
            self.our_goalmeanY = ys[1]

            self.their_goalX = (data["rightgoal"][0][0] + data["rightgoal"][1][0] + data["rightgoal"][2][0])/3.0
            ys = [data["rightgoal"][0][1] , data["rightgoal"][1][1] , data["rightgoal"][2][1]]
            ys.sort()
            self.their_goallowY = ys[0]
            self.their_goalhighY = ys[2]
            self.their_goalmeanY = ys[1]

        else:
            self.our_goalX = (data["rightgoal"][0][0] + data["rightgoal"][1][0] + data["rightgoal"][2][0])/3.0
            ys = [data["rightgoal"][0][1] , data["rightgoal"][1][1] , data["rightgoal"][2][1]]
            ys.sort()
            self.our_goallowY = ys[0]
            self.our_goalhighY = ys[2]
            self.our_goalmeanY = ys[1]

            self.their_goalX = (data["leftgoal"][0][0] + data["leftgoal"][1][0] + data["leftgoal"][2][0])/3.0
            ys = [data["leftgoal"][0][1] , data["leftgoal"][1][1] , data["leftgoal"][2][1]]
            ys.sort()
            self.their_goallowY = ys[0]
            self.their_goalhighY = ys[2]
            self.their_goalmeanY = ys[1]

        # clockwise from top left
        self.goal_left_top = data["leftdefend"][0]
        self.defending_left_top = data["leftdefend"][1]
        self.defending_left_bot = data["leftdefend"][2]
        self.goal_left_bot = data["leftdefend"][3]

        self.defending_right_top = data["rightdefend"][0]
        self.defending_right_bot = data["rightdefend"][1]
        self.goal_right_top = data["rightdefend"][1]
        self.goal_right_bot = data["rightdefend"][1]

        self.pitch_top_left = data["pitch"][0]
        self.pitch_top_right = data["pitch"][1]
        self.pitch_bot_right = data["pitch"][2]
        self.pitch_bot_left = data["pitch"][3]
