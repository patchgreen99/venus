import math
import numpy as np


class StrategyTools:
    def __init__(self, world, commands):
        self.world = world
        self.commands = commands

    def attackwithball(self):

        x2,y2 = self.world.friend.position
        x1,y1 = self.world.venus.position
        x3,y3 = self.world.enemy1.position
        x4,y4 = self.world.enemy2.position

        robotposlist = [(x3,y3),
                        (x4,y4)]
        # TODO: if self.world.enemy1.out.value == False:

        goalx = self.world.their_goalX
        highy = self.world.their_goalhighY
        lowy = self.world.their_goallowY

        print(goalx,highy,lowy)
        print(self.world.enemy1.position[0],self.world.enemy1.position[1])
        i = (highy + lowy)/2
        while i < highy:
            if self.isSafeKick((x1,y1),(goalx,i),robotposlist ):
                #self.commands.goal()
                print('goal')
                return
            i = i + 1
        i = (highy + lowy)/2
        while i > lowy:
            if self.isSafeKick((x1,y1),(goalx,i),robotposlist):
                #self.commands.goal()
                print('goal')
                return
            i = i - 1
        if self.isSafeKick((x1, y1), (x2, y2), robotposlist):
            #self.commands.pass_ball()
            print('pass')
            return
        # do something instead
        print('something else')
        return

    def isSafeKick(self, (x1, y1), (x2, y2), robotposlist):
        rotation = 0.20
        m1, c1 = self.rotateline(x1, y1, x2, y2, rotation)
        m2, c2 = self.rotateline(x1, y1, x2, y2, -rotation)
        if (y2 - m1 * x2 - c1) > 0:
            s = 1
        else:
            s = -1
        i = 0
        while i < len(robotposlist):
            if robotposlist[i][1] > min(y1, y2) & robotposlist[i][1] < max(y1, y2):
                if (robotposlist[i][1] - m1 * robotposlist[i][0] - c1) * s > 0:
                    return False
                if (robotposlist[i][1] - m2 * robotposlist[i][0] - c2) * s > 0:
                    return False
            i = i + 1
        return True

    def rotateline(self, x1, y1, x2, y2, rotation):
        diff = np.array([x2 - x1, y2 - y1])
        r = np.array([[math.cos(rotation), -math.sin(rotation)], [math.sin(rotation), math.cos(rotation)]])
        mul = np.multiply(r, diff)
        newarr = np.subtract(mul, np.array([x1, y1]))
        newlist = newarr.tolist()
        m1 = (newlist[1][1] - y1) / (newlist[1][0] - x1)
        c1 = newlist[1][1] - m1*newlist[1][0]
        return (m1,c1)

    def ballwithenemy(self, enemystr):
        enemy_no = int(enemystr)
        if enemy_no == 1:
            enemyposition = self.world.enemy1.position
            if self.iclosertogoal(enemyposition): #TODO: or enemy out of pitch
                '''# TODO: make the block_goal_enemy 1 on'''
                print('block goal enemy1')
            else:
                '''# TODO: make the block_pass on'''
                print('block pass')
        elif enemy_no == 2:
            enemyposition = self.world.enemy2.position
            if self.iclosertogoal(enemyposition):  #TODO: or enemy out of pitch
                '''# TODO: make the block_goal_enemy 1 on'''
                print('block goal enemy2')
            else:
                '''# TODO: make the block_pass on'''
                print('block pass')
        else:
            print('no')
        return

    def iclosertogoal(self,enemyposition):
        linex1,liney1 = (self.world.our_goalX,self.world.our_goalmeanY)
        linex2,liney2 = enemyposition
        m = (liney2-liney1) / (linex2 -linex1)
        c = -(liney2 - m * linex2)
        a = -m

        vx,vy = self.world.venus.position
        fx,fy = self.world.friend.position

        pvx = ((vx - a*vy) - a*c)/ (a**2 + 1)
        pfx = ((fx - a*fy) - a*c)/ (a**2 + 1)

        pvy = (a*(-vx + a*vy) - c) / (a**2 + 1)
        pfy = (a*(-fx + a*fy) - c) / (a**2 + 1)

        vlinedist= abs((liney2-liney1)*vx - (linex2-linex1)*vy + (linex1*liney2) + (linex2*liney1))/self.euclideandist((linex1,liney1),(linex2,liney2))
        flinedist= abs((liney2-liney1)*fx - (linex2-linex1)*fy + (linex1*liney2) + (linex2*liney1))/self.euclideandist((linex1,liney1),(linex2,liney2))

        minvenddist = min( self.euclideandist((linex1,liney1),(vx,vy)),self.euclideandist((linex2,liney2),(vx,vy)))
        minfenddist = min( self.euclideandist((linex1,liney1),(fx,fy)),self.euclideandist((linex2,liney2),(fx,fy)))

        if self.isinbetween((linex1,liney1),(linex2,liney2),(pvx,pvy)):
            minvdist = vlinedist
        else:
            minvdist = minvenddist

        if self.isinbetween((linex1,liney1),(linex2,liney2),(pfx,pfy)):
            minfdist = flinedist
        else:
            minfdist = minfenddist
        if minvdist < minfdist:
            return True
        else:
            return False

    def isinbetween(self,(x1,y1),(x2,y2),(x,y)):
        if x>min(x1,x2) & x <max(x1,x2) & y>min(y1,y2) & y<max(y1,y2) :
            return True
        else:
            return False

    def euclideandist(self,(x1,y1),(x2,y2)):
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)

    def enemy_has_ball(self):
        # todo: what happens if one of enemy robots is not in the game?
        # todo: what if orientation vector endpoint is outside the pitch?
        # returns either (False, -1) or (True, self.world.enemyX)

        # find which enemy robot is closer to the ball
        enemy1 = self.world.enemy1.position
        enemy2 = self.world.enemy2.position
        ball = self.world.ball

        distance1 = math.sqrt((ball[0] - enemy1.position[0])**2 + (ball[1] - enemy1.position[1])**2)
        distance2 = math.sqrt((ball[0] - enemy2.position[0])**2 + (ball[1] - enemy2.position[1])**2)
        closest = enemy1
        if distance1 > distance2:
            closest = enemy2

        # 'closest' is the robot who might have the ball, let's check that
        distance_between_points = math.sqrt((closest.position[0] - closest.orientation[0])**2 + (closest.position[1] - closest.orientation[1])**2)
        # we want point that is ten pixels away from the centre towards the orientation vector endpoint
        ratio = 10.0/distance_between_points

        # then point's coordinates will be
        new_x = closest.position[0] * (1-ratio) + ratio*closest.orientation[0]
        new_y = closest.position[1] * (1-ratio) + ratio*closest.orientation[1]

        # check how far this point is from the ball
        dist_to_ball = math.sqrt((ball[0] - new_x)**2 + (ball[1] - new_y)**2)

        # return status
        if dist_to_ball < 10:
            return True, closest
        else:
            return False, -1

    def openball(self):
        if self.icloserball():
            #grab_ball
            print('grab ball')
        else:
            print('reach pass position')
            #reachpassposition
        return

    def icloserball(self):
        x1,y1 = self.world.venus.position
        x2,y2 = self.world.friend.position
        x,y = self.world.ball

        d1 = self.euclideandist((x1,y1),(x,y))
        d2 = self.euclideandist((x2,y2),(x,y))

        if d1< d2 :         #TODO: or teamate out of pitch
            return True
        else:
            return False

    def ballwithfriend(self):
        x2,y2 = self.world.friend.position
        x1,y1 = self.world.venus.position
        x3,y3 = self.world.enemy1.position
        x4,y4 = self.world.enemy2.position

        robotposlist = [(x3,y3),
                        (x4,y4)]

        if self.isSafeKick((x2,y2),(x1,y1,robotposlist)):
            #recievepass
            print('receive pass')
        else:
            #move to pass position
            print('move to pass position')



