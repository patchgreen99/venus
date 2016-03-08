from multiprocessing import Array, Value
import math

NO_VALUE = -1


class Robot:
    def __init__(self):
        self.position = Array('i', [NO_VALUE, NO_VALUE])
        self.orientation = Array('d', [NO_VALUE, NO_VALUE])
        self.out = Value('b')

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

        if room_num == 1:
            if we_have_computer_goal:
                self.our_goalX = 38 # left
                self.our_goallowY = 181
                self.our_goalhighY = 304
                self.our_goalmeanY = (self.our_goalhighY + self.our_goallowY)/2
                self.their_goalX = 618 # right
                self.their_goallowY = 176
                self.their_goalhighY = 297
                self.their_goalmeanY = (self.their_goalhighY + self.their_goallowY)/2
            else:
                self.our_goalX = 618 # right
                self.our_goallowY = 176
                self.our_goalhighY = 297
                self.our_goalmeanY = (self.our_goalhighY + self.our_goallowY)/2
                self.their_goalX = 38 # right
                self.their_goallowY = 181
                self.their_goalhighY = 304
                self.their_goalmeanY = (self.their_goalhighY + self.their_goallowY)/2
        else:
            if we_have_computer_goal:
                self.our_goalX = 618 # right
                self.our_goallowY = 176
                self.our_goalhighY = 297
                self.our_goalmeanY = (self.our_goalhighY + self.our_goallowY)/2
                self.their_goalX = 38 # right
                self.their_goallowY = 181
                self.their_goalhighY = 304
                self.their_goalmeanY = (self.their_goalhighY + self.their_goallowY)/2
            else:
                self.our_goalX = 38 # left
                self.our_goallowY = 181
                self.our_goalhighY = 304
                self.our_goalmeanY = (self.our_goalhighY + self.our_goallowY)/2
                self.their_goalX = 618 # right
                self.their_goallowY = 176
                self.their_goalhighY = 297
                self.their_goalmeanY = (self.their_goalhighY + self.their_goallowY)/2

        self.ball = Array('i', [NO_VALUE, NO_VALUE]) # in pixels
        self.ball_velocity = Array('i', [NO_VALUE, NO_VALUE]) # pixels per frame
        self.ball_moving = Value('b')
        self.venus = Robot()
        self.friend = Robot()
        self.enemy1 = Robot()
        self.enemy2 = Robot()

    def __str__(self):
        return "World state: ball {} {} {}, future ball {} {}, venus {}, friend {}, enemy1 {}, enemy2 {}".format(
            self.ball[0], self.ball[1], self.ball_moving.value, self.speed[0], self.speed[1],
            self.venus, self.friend, self.enemy1, self.enemy2)

