import math

# We have moveStraight, turn , kick , ungrab , grab

# Positions and orientation to be calculated by vision
ourRobotPos = (0, 0)
teamRobotPos = (0, 0)
enemy1Pos = (0, 0)
enemy2Pos = (0, 0)
ballPos = (0, 0)
ourorientation = 0

ourPossession = False
TeamPossession = False
enemy1Posession = False
enemy2Posession = False
enemyPosession = enemy1Posession or enemy2Posession


# Constants
goalPos = (0, 100)
defenseGoalPos = (200, 100)

pixeltosditance = 0.05  # 1 pixel is 0.05 cms #random


class simple:
    def turnToPoint(self, point):
        desiredOrientation = self.calcOrientation(ourRobotPos, point)
        turn(desiredOrientation - ourOrientation)

    def calcOrientation(self, (x1, y1), (x2, y2)):
        if (x2 - x1 == 0):
            return 0
        angle = math.atan((y2 - y1) / (x2 - x1)) + (math.pi / 2)  # not 100% correct
        return (angle * 180) / math.pi

    def moveToPoint(self, point):
        self.turnToPoint(point)
        moveStraight(pixeltosditance * calcDistance(ourRobotPos, point))

    def calcDistance(self, (x1, y1), (x2, y2)):
        distance = math.sqrt((x1 - x2) ^ 2 + (y1 - y2) ^ 2)
        return distance

    def goGrab(self):
        if (enemyPosession):
            return ('cannot')
        else:
            ungrab()
            self.moveToPoint(ballPos)
            grab()

    # if(not ourPosession):
    #		goGrab()

    def kickToGoal(self):
        self.turnToPoint(goalPos)
        kick(pixeltosditance * calcDistance(ourRobotPos, Point))

# TODO : block, 360 degree overflow, conversionproblem
