import math
import numpy as np
import time

class StrategyTools:
    def __init__(self, world, commands, game, simple):
        self.world = world
        self.commands = commands
        self.game = game
        self.simple = simple

    def attackwithball(self):

        x1 = self.world.venus.position[0]
        y1 = self.world.venus.position[1]
        x2 = self.world.friend.position[0]
        y2 = self.world.friend.position[1]
        x3 = self.world.enemy1.position[0]
        y3 = self.world.enemy1.position[1]
        x4 = self.world.enemy2.position[0]
        y4 = self.world.enemy2.position[1]

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
            if self.isSafe2((x1,y1),(goalx,i),robotposlist ):
                return "ATTACK_GOAL"
            i = i + 1
        i = (highy + lowy)/2
        while i > lowy:
            if self.isSafe2((x1,y1),(goalx,i),robotposlist):
                return "ATTACK_GOAL"
            i = i - 1
        if self.isSafe2((x1, y1), (x2, y2), robotposlist):
            return "ATTACK_PASS"
        # do something instead
        #print('something else')
        angle, motion_length = self.simple.calculate_angle_length_goal()
        self.commands.c(angle)
        time.sleep(3)
        i = (highy + lowy)/2
        while i < highy:
            if self.isSafe2((x1,y1),(goalx,i),robotposlist ):
                return "ATTACK_GOAL"
            i = i + 1
        i = (highy + lowy)/2
        while i > lowy:
            if self.isSafe2((x1,y1),(goalx,i),robotposlist):
                return "ATTACK_GOAL"
            i = i - 1
        if self.isSafe2((x1, y1), (x2, y2), robotposlist):
            return "ATTACK_PASS"
        self.commands.c(20)
        self.commands.x()

        # i = 0
        # while i< 5:
        #     self.commands.c(20)
        #
        #     go_x = -0.5*(-2*self.world.venus.position[0] + 2*m*(c-self.world.venus.position[1]))/(1+m**2)
        #     go_y = go_x*m + c
        #
        #
        return

    def isSafe2(self,(x1, y1), (x2, y2), robotposlist):
        rotation = 20 # todo needs adjusting!

        safe_kick = True
        for (x, y) in robotposlist:
            # determine if in y area
            if self.isinbetweenY((x1,y1),(x2,y2),(x,y)):
                # there is a robot in the area
                # find angle
                print(x1)
                angle = self.ang((x1,y1), (x,y), (x2,y2))
                print angle
                if (angle < rotation):
                    return False
            else:
                safe_kick = True
        return safe_kick

    # check if there is other robot between ball/goal and our robot
    # return True if there is something in between
    # else return false
    # USE THIS !!!!!

    def isSafe3(self, pt1, pt2, robotlist):
        for rb in robotlist:
            distance1 = self.euclideandist(pt1, rb)
            distance2 = self.euclideandist(pt2, rb)
            distance3 = self.euclideandist(pt1, pt2)

            if (abs((distance1 + distance2) - distance3) < 20):
                # Object is on the line.
                return False
        return True

    def dot(self, vectorA, vectorB):
        return vectorA[0]*vectorB[0]+vectorA[1]*vectorB[1]

    def ang(self, (x1, y1), (x2, y2), (x, y)):
        # one line is (x1, y1) to (x2, y2), second line is (x1, y1) and (x, y)
        # Get nicer vector form
        vA = [(x1-x2), (y1-y2)]
        vB = [(x1-x), (y1-y)]
        # Get dot prod
        dot_prod = self.dot(vA, vB)
        # Get magnitudes
        magA = self.dot(vA, vA)**0.5
        magB = self.dot(vB, vB)**0.5
        # Get cosine value
        if magA != 0 and magB != 0:
            cos_ = dot_prod/magA/magB
        else:
            cos_ = 1
        # Get angle in radians and then convert to degrees
        angle = math.acos(cos_)
        
        # Basically doing angle <- angle mod 360
        ang_deg = math.degrees(angle)%360

        if ang_deg-180>=0:
            # As in if statement
            return 360 - ang_deg
        else:
            return ang_deg

    # def isSafeKick(self,(x1, y1), (x2, y2), robotposlist):
    #     rotation = 0.30
    #     m = (y2 - y1) / (x2 - x1)
    #     c = y2 - m*x2
    #     print((m,c))
    #     (m1, c1 )= self.rotateline(x1, y1, x2, y2, rotation)
    #     print((m1,c1))
    #     m2, c2 = self.rotateline(x1, y1, x2, y2, -rotation*2)
    #     print((m2,c2))
    #     if (y2 - (m1 * x2) - c1) > 0:
    #         s1 = 1
    #     else:
    #         s1 = -1
    #     if (y2 - (m2 * x2) - c2) > 0:
    #         s2 = 1
    #     else:
    #         s2 = -1
    #     i = 0
    #     while i < len(robotposlist):
    #         if robotposlist[i][1] > min(y1, y2) & robotposlist[i][1] < max(y1, y2):
    #             if (robotposlist[i][1] - m1 * robotposlist[i][0] - c1) * s1 > 0:
    #                 return False
    #             if (robotposlist[i][1] - m2 * robotposlist[i][0] - c2) * s2 > 0:
    #                 return False
    #         i = i + 1
    #     return True
    #
    # def rotateline(self,x1, y1, x2, y2, rotation):
    #     # diff = np.array([x2 - x1, y2 - y1])
    #     # r = np.array([[math.cos(rotation), -math.sin(rotation)], [math.sin(rotation), math.cos(rotation)]])
    #     # mul = np.multiply(r, diff)
    #     # newarr = np.subtract(mul, np.array([x1, y1]))
    #     # newlist = newarr.tolist()
    #     # m1 = (newlist[1][1] - y1) / (newlist[1][0] - x1)
    #     # c1 = newlist[1][1] - m1*newlist[1][0]
    #     # return (m1,c1)
    #
    #       #POINT rotate_point(float cx,float cy,float angle,POINT p)
    #     s = math.sin(rotation);
    #     c = math.cos(rotation);
    #
    #     m2 = (y2 - y1) / (x2 - x1)
    #     c2 = y1 - m2*x1
    #
    #     x3 = x2-x1;
    #     y3 = y2 -y1;
    #
    #     xnew = (x2 * c) - (y2 * s);
    #     ynew = (y2* s) + (x2 * c);
    #     x3 = xnew + x1;
    #     y3 = ynew + y1;
    #     m1 = (y3 - y1) / (x3 - x1)
    #     c1 = y3 - m1*x3
    #
    #     return (m1,c1)
    #

    def ballwithenemy(self, enemy_no):
        #enemy_no = int(enemystr)
        if enemy_no == 1:
            enemyposition = self.world.enemy1.position
            if self.iclosertogoal2(enemyposition) or self.world.enemy2.out.value: #TODO: or enemy out of pitch -- done, test!
               # self.commands.block_goal(1)
                print('block goal enemy1')
                return "ENEMY1_BALL_TAKE_GOAL"
            else:
                #self.commands.intercept()
                print('block pass')
                return "ENEMY_BALL_TAKE_PASS"
        elif enemy_no == 2:
            enemyposition = self.world.enemy2.position
            if self.iclosertogoal2(enemyposition) or self.world.enemy1.out.value:  #TODO: or enemy out of pitch -- done, test!
                #self.commands.block_goal(2)
                print('block goal enemy2')
                return "ENEMY2_BALL_TAKE_GOAL"
            else:
                #self.commands.intercept()
                print('block pass')
                return "ENEMY_BALL_TAKE_PASS"
        else:
            print('wrong no')
        return

    def iclosertogoal2(self,enemyposition):
        linex1,liney1 = (self.world.our_goalX, self.world.our_goalmeanY)
        linex2,liney2 = enemyposition
        x1 = self.world.venus.position[0]
        y1 = self.world.venus.position[1]
        x2 = self.world.friend.position[0]
        y2 = self.world.friend.position[1]

        venusin = y1 > min(liney1,liney2) & y1 < max(liney1,liney2)
        friendin = y2 > min(liney1,liney2) & y2 < max(liney1,liney2)

        if venusin and friendin :
            midx = (linex1 + linex2) / 2
            midy = (liney1 + liney2) / 2
            adist = self.euclideandist((x1,y1),(midx,midy))
            bdist = self.euclideandist((x2,y2),(midx,midy))
            if adist>bdist:
                return True
            else:
                return False
        elif venusin:
            return True
        elif friendin:
            return False
        else:
            minvenddist = min( self.euclideandist((linex1,liney1),(x1,y1)),self.euclideandist((linex2,liney2),(x1,y1)))
            minfenddist = min( self.euclideandist((linex1,liney1),(x2,y2)),self.euclideandist((linex2,liney2),(x2,y2)))
            if minvenddist < minfenddist:
                return True
            else:
                return False

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
        if x>min(int(x1),int(x2)) and x < max(int(x1), int(x2)) and y>min(y1,y2) and y<max(y1,y2) :
            return True
        else:
            return False

    def isinbetweenY(self,(x1,y1),(x2,y2),(x,y)):
        if y>=min(y1,y2) and y<=max(y1,y2) :
            return True
        else:
            return False

    def euclideandist(self,(x1,y1),(x2,y2)):
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)

    def openball(self):
        if self.icloserball():
            #grab_ball
            #print('grab ball')
            return "FREE_BALL_YOURS"
        else:
            return self.bestpositioncase()

    def icloserball(self):
        x1 = self.world.venus.position[0]
        y1 = self.world.venus.position[1]
        x2 = self.world.friend.position[0]
        y2 = self.world.friend.position[1]
        x = self.world.ball[0]
        y = self.world.ball[1]

        d1 = self.euclideandist((x1,y1),(x,y))
        d2 = self.euclideandist((x2,y2),(x,y))

        if d1 < d2 or self.world.friend.out.value:         #TODO: or teamate out of pitch -- done, testing needed
            return True
        else:
            return False

    def bestpositioncase(self):
        x1 = self.world.venus.position[0]
        y1 = self.world.venus.position[1]
        x2 = self.world.friend.position[0]
        y2 = self.world.friend.position[1]
        x3 = self.world.enemy1.position[0]
        y3 = self.world.enemy1.position[1]
        x4 = self.world.enemy2.position[0]
        y4 = self.world.enemy2.position[1]
        x5 = self.world.their_goalX
        y5 = self.world.their_goalmeanY

        if self.isinbetweenY((x1,y1),(x5,y5),(x3,y3)) :
            if self.isinbetweenY((x1,y1),(x5,y5),(x4,y4)):
                return "FREE_BALL_BOTH_GOALSIDE"
            else:
                return "FREE_BALL_1_GOALSIDE"
        else:
            if self.isinbetweenY((x1,y1),(x5,y5),(x4,y4)):
                return "FREE_BALL_2_GOALSIDE"
            else:
                return "FREE_BALL_NONE_GOALSIDE"

    def ballwithfriend(self): # trigger on isballinrange
        x1 = self.world.venus.position[0]
        y1 = self.world.venus.position[1]
        x2 = self.world.friend.position[0]
        y2 = self.world.friend.position[1]
        x3 = self.world.enemy1.position[0]
        y3 = self.world.enemy1.position[1]
        x4 = self.world.enemy2.position[0]
        y4 = self.world.enemy2.position[1]

        robotposlist = [(x3,y3),
                        (x4,y4)]

        if self.isSafe2((x2,y2),(x1,y1),robotposlist) and self.world.friend.hasBallInRange.value:
            return "RECEIVE_BALL"
            # print('receive pass')
        else:
            return self.bestpositioncase()

    def get_pass_goal_position(self):
        pass

    def penalty_attack(self):
        self.game.grab_ball()
        self.simple.goal()
        # x1 = self.world.venus.position[0]
        # y1 = self.world.venus.position[1]
        # x2 = self.world.friend.position[0]
        # y2 = self.world.friend.position[1]
        # x3 = self.world.enemy1.position[0]
        # y3 = self.world.enemy1.position[1]
        # x4 = self.world.enemy2.position[0]
        # y4 = self.world.enemy2.position[1]
        #
        # robotposlist = [(x3,y3),
        #                 (x4,y4)]
        #
        # # todo: can we determine which enemy robot is blocking the goal? maybe pass it as argument?
        # # todo add grab ball and kick goal??
        # goalx = self.world.their_goalX
        # highy = self.world.their_goalhighY
        # lowy = self.world.their_goallowY
        #
        # i = (highy + lowy)/2
        # while i < highy:
        #     if self.isSafe2((x1,y1),(goalx,i),robotposlist ):
        #         # grab_ball then turn and kick towards the right spot at the goal
        #         return
        #     i = i + 1
        # i = (highy + lowy)/2
        # while i > lowy:
        #     if self.isSafe2((x1,y1),(goalx,i),robotposlist):
        #         # grab_ball then turn and kick towards the right spot at the goal
        #         return
        #     i = i - 1
        # return

    def penalty_defend(self, enemy_num):
        # pass number of the enemy that attacks, 1 - enemy1 or 2 - enemy2
        self.commands.block_goal(enemy_num)
        return

    def kick_off_us(self):
        self.commands.x()
        self.commands.g()
        return

    def kick_off_them(self):
        while not self.world.ball_moving.value:
            pass
        return

    def main(self):
        start = True
        x1 = self.world.venus.position[0]
        y1 = self.world.venus.position[1]
        x2 = self.world.friend.position[0]
        y2 = self.world.friend.position[1]
        x3 = self.world.enemy1.position[0]
        y3 = self.world.enemy1.position[1]
        x4 = self.world.enemy2.position[0]
        y4 = self.world.enemy2.position[1]

        last_state = "None"
        while True:

            x1 = self.world.venus.position[0]
            y1 = self.world.venus.position[1]
            x2 = self.world.friend.position[0]
            y2 = self.world.friend.position[1]
            x3 = self.world.enemy1.position[0]
            y3 = self.world.enemy1.position[1]
            x4 = self.world.enemy2.position[0]
            y4 = self.world.enemy2.position[1]
            venus = self.world.venus
            friend = self.world.friend
            enemy1 = self.world.enemy1
            enemy2 = self.world.enemy2
           # if self.commands.query_ball():
           #  print(friend.hasBallInRange.value)
           #  print(enemy1.hasBallInRange.value)
           #  print(enemy2.hasBallInRange.value)
            if self.commands.query_ball():
                state = self.attackwithball()
            elif friend.hasBallInRange.value:
                # friend has the ball
                state = self.ballwithfriend()
            elif enemy1.hasBallInRange.value:
                # enemy1 has the ball
                state = self.ballwithenemy(1)
            elif enemy2.hasBallInRange.value:
                # enemy2 has the ball
                state = self.ballwithenemy(2)
            else:
                # open ball!
                state = self.openball()
            print(state)

            #
            # if start == True:
            #     start = False
            #     self.game.start(state)
            # elif last_state == state:
            #     self.game.mid(state)
            # else:
            #     self.game.end(last_state)
            #     self.game.start(state)

    if __name__ == "__main__":
        main()

