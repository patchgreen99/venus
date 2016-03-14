import math
import numpy as np

class StrategyTools:
    def __init__(self, world, commands, game):
        self.world = world
        self.commands = commands
        self.game = game

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
        print('something else')
        return 'NOTHING'

    def isSafe2(self,(x1, y1), (x2, y2), robotposlist):
        #rotation = 0.30
        m = (y2 - y1) / (x2 - x1)
        c = y2 - m*x2
        for rb in robotposlist:
            if rb[1] > min(y1, y2) & rb[1] < max(y1, y2):
                if ((rb[1] - m * rb[0] - c) < 0.5) & ((rb[1] - m * rb[0] - c) > -0.5):
                    return False
        return True

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
        # enemy_no = int(enemystr)
        if enemy_no == 1:
            enemyposition = self.world.enemy1.position
            if self.iclosertogoal(enemyposition) or self.world.enemy2.out.value: #TODO: or enemy out of pitch -- done, test!
               # self.commands.block_goal(1)
                #print('block goal enemy1')
                return "ENEMY1_BALL_TAKE_GOAL"
            else:
                #self.commands.intercept()
                #print('block pass')
                return "ENEMY_BALL_TAKE_PASS"
        elif enemy_no == 2:
            enemyposition = self.world.enemy2.position
            if self.iclosertogoal(enemyposition) or self.world.enemy1.out.value:  #TODO: or enemy out of pitch -- done, test!
                #self.commands.block_goal(2)
                #print('block goal enemy2')
                return "ENEMY2_BALL_TAKE_GOAL"
            else:
                #self.commands.intercept()
                #print('block pass')
                return "ENEMY_BALL_TAKE_PASS"
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
        if x>min(int(x1),int(x2)) & x < max(int(x1), int(x2)) & y>min(y1,y2) & y<max(y1,y2) :
            return True
        else:
            return False

    def isinbetweenY(self,(x1,y1),(x2,y2),(x,y)):
        if y>min(y1,y2) & y<max(y1,y2) :
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
        x1,y1 = self.world.venus.position
        x2,y2 = self.world.friend.position
        x,y = self.world.ball

        d1 = self.euclideandist((x1,y1),(x,y))
        d2 = self.euclideandist((x2,y2),(x,y))

        if d1 < d2 or self.world.friend.out.value:         #TODO: or teamate out of pitch -- done, testing needed
            return True
        else:
            return False

    def bestpositioncase(self):
        x1,y1 = self.world.venus.position
        x2,y2 = self.world.friend.position
        x3,y3 = self.world.enemy1.position
        x4,y4 = self.world.enemy2.position
        x5,y5 = self.world.their_goalX, self.world.their_goalmeanY

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
        x1,y1 = self.world.venus.position
        x2,y2 = self.world.friend.position
        x3,y3 = self.world.enemy1.position
        x4,y4 = self.world.enemy2.position

        robotposlist = [(x3,y3),
                        (x4,y4)]


        if self.isSafeKick((x2,y2),(x1,y1),robotposlist) and self.world.friend.hasBallInRange.value
            return "RECEIVE_BALL"
            # print('receive pass')
        else:
            return self.bestpositioncase()
        # else:
        #     # change position
        #     # based on positions of all robots choose the one that will ensure a safe pass
        #     # switch relevant fields on
        #
        #     # at this point we are sure one of the enemy robots is between venus and friend
        #     # so it's mainly the position of another enemy robot that might affect us
        #
        #     # find out which robot is on the way for us to pass todo: this is not a nice way to do it, (isSafeKick function could return number of enemy as well)...
        #     robot_not_middle = self.world.enemy1
        #     if self.isSafeKick((x2,y2),(x1,y1),[(x3, y3)]):
        #         robot_not_middle = self.world.enemy2
        #
        #     elif self.isSafeKick((x2,y2),(x1,y1),[(x4, y4)]):
        #         robot_not_middle = self.world.enemy1
        #
        #     if robot_not_middle == self.world.enemy1:
        #         pass
        #         # free_up_pass_enemy2
        #         # free_up_goal_enemy1
        #
        #         # need to import game
        #         # free_up_pass_enemy2 = self.game.finite_axial_outside(self.world.enemy2.position, self.world.friend.position, 1, 10000)
        #         # free_up_goal_enemy1 = self.game.finite_axial_outside(self.world.enemy1.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
        #         # then catch_ball and score!
        #     else:
        #         pass
        #         # free_up_pass_enemy1
        #         # free_up_goal_enemy2
        #
        #         # free_up_pass_enemy1 = self.game.finite_axial_outside(self.world.enemy1.position, self.world.friend.position, 1, 10000)
        #         # free_up_goal_enemy2 = self.game.finite_axial_outside(self.world.enemy2.position, (self.world.their_goalX, self.world.their_goalmeanY), 1, 10000)
        #         # then catch_ball and score!
        #
        #     # todo: what if we can't free up goal? e.g. enemy robot is there... what if enemy robot blocks the goal too well?
        #     # we should have a strategy how to attract enemy robot out of the goal, and then attack quickly?
        #     # or just turn and kick very quickly such that their vision doesnt recongnize where our orientation verctor is pointing
        #
        #     print('move to pass position')

    def get_pass_goal_position(self):
        pass

    def penalty_attack(self):
        x1,y1 = self.world.venus.position
        x3,y3 = self.world.enemy1.position
        x4,y4 = self.world.enemy2.position

        robotposlist = [(x3,y3),
                        (x4,y4)]

        # todo: can we determine which enemy robot is blocking the goal? maybe pass it as argument?

        goalx = self.world.their_goalX
        highy = self.world.their_goalhighY
        lowy = self.world.their_goallowY

        i = (highy + lowy)/2
        while i < highy:
            if self.isSafeK2((x1,y1),(goalx,i),robotposlist ):
                # grab_ball then turn and kick towards the right spot at the goal
                return
            i = i + 1
        i = (highy + lowy)/2
        while i > lowy:
            if self.isSafe2((x1,y1),(goalx,i),robotposlist):
                # grab_ball then turn and kick towards the right spot at the goal
                return
            i = i - 1
        return

    def penalty_defend(self, enemy_num):
        # pass number of the enemy that attacks, 1 - enemy1 or 2 - enemy2
        self.commands.block_goal(enemy_num)
        return

    def main(self):
        start = True
        last_state = "None"
        while True:
            venus = self.world.venus
            friend = self.world.friend
            enemy1 = self.world.enemy1
            enemy2 = self.world.enemy2
           # if self.commands.query_ball():
            print(friend.hasBallInRange.value)
            print(enemy1.hasBallInRange.value)
            print(enemy2.hasBallInRange.value)
            if venus.hasBallInRange.value:
                # venus has the ball
             #   self.commands.g()
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

