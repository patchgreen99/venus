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

    def ballwithenemy(self, enemy_no):
        # enemy_no = int(enemystr)
        if enemy_no == 1:
            enemyposition = self.world.enemy1.position
            if self.iclosertogoal(enemyposition) or self.world.enemy1.out: #TODO: or enemy out of pitch -- done, test!
                '''# TODO: make the block_goal_enemy 1 on'''
                print('block goal enemy1')
            else:
                '''# TODO: make the block_pass on'''
                print('block pass')
        elif enemy_no == 2:
            enemyposition = self.world.enemy2.position
            if self.iclosertogoal(enemyposition) or self.world.enemy2.out:  #TODO: or enemy out of pitch -- done, test!
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

        if d1 < d2 or self.world.friend.out:         #TODO: or teamate out of pitch -- done, testing needed
            return True
        else:
            return False

    def ballwithfriend(self): # trigger on isballinrange
        x2,y2 = self.world.friend.position
        x1,y1 = self.world.venus.position
        x3,y3 = self.world.enemy1.position
        x4,y4 = self.world.enemy2.position

        robotposlist = [(x3,y3),
                        (x4,y4)]

        if self.isSafeKick((x2,y2),(x1,y1,robotposlist)) and self.world.friend.hasBallInRange:
            #recievepass
            print('receive pass')
        else:
            # change position
            # based on positions of all robots choose the one that will ensure a safe pass
            # switch relevant fields on

            # at this point we are sure one of the enemy robots is between venus and friend
            # so it's mainly the position of another enemy robot that might affect us

            # find out which robot is on the way for us to pass todo: this is not a nice way to do it, also it (isSafeKick function) might not even work...
            robot_not_middle = self.world.enemy1
            if self.isSafeKick((x2,y2),(x1,y1,[(x3, y3)])):
                robot_not_middle = self.world.enemy2

            elif self.isSafeKick((x2,y2),(x1,y1,[(x4, y4)])):
                robot_not_middle = self.world.enemy1

            if robot_not_middle == self.world.enemy1:
                pass
                # free_up_pass_enemy2
                # free_up_goal_enemy1
            else:
                pass
                # free_up_pass_enemy1
                # free_up_goal_enemy2

            print('move to pass position')

    def get_pass_goal_position(self):
        pass

    def main(self):
        venus = self.world.venus
        friend = self.world.friend
        enemy1 = self.world.enemy1
        enemy2 = self.world.enemy2
        if self.commands.query_ball():
            # venus has the ball
            self.commands.g()
            self.attackwithball()

        elif friend.hasBallInRange:
            # friend has the ball
            self.ballwithfriend()
        elif enemy1.hasBallInRange:
            # enemy1 has the ball
            self.ballwithenemy(1)
        elif enemy2.hasBallInRange:
            # enemy2 has the ball
            self.ballwithenemy(2)
        else:
            # open ball!
            self.openball()
    if __name__ == "__main__":
        main()

