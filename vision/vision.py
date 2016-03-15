from pylab import *
from scipy.ndimage import measurements
from color_calibration import *
from strategy.world import NO_VALUE
import time

VISION_ROOT = 'vision/'

MAX_COLOR_COUNTS = {
    'red': 10,
    'blue': 2,
    'yellow': 10,
    'pink': 8,
    'green': 8,
}

COLORS = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'yellow': (0, 255, 255),
    'pink': (153, 51, 255),
    'green': (0, 255, 0),
}

HUES = {
    'blue': (80, 107),
    'yellow': (28, 39),
    'pink': (150, 175),
    'green': (41, 55),
}


VENUS = 0
TEAMMATE = 1
ENEMY_1 = 2
ENEMY_2 = 3


class Vision:
    def __init__(self, world, debug=False):
        self.last_angle = [0, 0, 0, 0]
        self.out_counter = [0, 0, 0, 0]
        self.start = 0
        self.debug = debug
        self.world = world
        self.pressed_key = None
        self.exit_key = None
        self.image = None
        self.imageHSV = None
        self.pressed_key = None
        self.colorList = ["red", "blue", "yellow", "pink", "green"]
        self.colorMedians = []
        self.counter = 0
        self.trajectory_list = [(0, 0)] * 6
        self.COLS = 640
        self.ROWS = 480

# #################################################################################################

        if self.world.room_num == 1:
            #self.color_ranges = {
            #    'red': [((0, 170, 130), (10, 255, 255)), ((175, 170, 130), (180, 255, 255))],
            #    'blue': [((85, 100, 110), (102, 230, 230))],
            #    'yellow': [((30, 120, 120), (45, 255, 255))],
            #    'pink': [((149, 130, 60), (170, 255, 255))],
            #    'green': [((47, 130, 200), (65, 255, 255))],
            #    }
            target = open('vision/color1.txt', 'r')
            self.color_ranges = eval(target.read())
            target.close()

            target = open('vision/room1.txt', 'r')
            self.brightness = int(target.readline())
            self.contrast = int(target.readline())
            self.saturation = int(target.readline())
            self.hue = int(target.readline())
            target.close()

            self.min_color_area = {
                    'red': 1000.0,
                    'blue': 1000.0,
                    'yellow': 1000.0,
                    'pink': 2000.0,
                    'green': 2000.0,
                }

            self.mtx = np.loadtxt(VISION_ROOT + "mtx1.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist1.txt")
            self.newmtx = np.loadtxt(VISION_ROOT + "newmtx1.txt")

# ################################################################################################

        elif self.world.room_num == 0:
            #self.color_ranges = {
            #    'red': [((0, 100, 100), (8, 255, 255)), ((165, 170, 130), (180, 255, 255))],
            #    'blue': [((83, 150, 160), (100, 255, 230))],
            #    'yellow': [((30, 150, 150), (37, 255, 255))],
            #    'pink': [((149, 130, 100), (175, 255, 255))],
            #    'green': [((47, 130, 200), (59, 255, 255))],
            #    }
            target = open('vision/color0.txt', 'r')
            self.color_ranges = eval(target.read())
            target.close()

            target = open('vision/room0.txt', 'r')
            self.brightness = int(target.readline())
            self.contrast = int(target.readline())
            self.saturation = int(target.readline())
            self.hue = int(target.readline())
            target.close()

            self.min_color_area = {
                    'red': 1000.0,
                    'blue': 1000.0,
                    'yellow': 1000.0,
                    'pink': 2000.0,
                    'green': 2000.0,
                }
            self.mtx = np.loadtxt(VISION_ROOT + "mtx0.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist0.txt")
            self.newmtx = np.loadtxt(VISION_ROOT + "newmtx0.txt")

# ################################################################################################

        else:
            print("invalid room id")

        self.capture = cv2.VideoCapture(0)

        cv2.namedWindow("Mask")
        cv2.namedWindow("Room")

        ####################################################

        cv2.createTrackbar('BRIGHTNESS', 'Room', 0, 100, self.nothing)
        cv2.createTrackbar('CONTRAST', 'Room', 0, 100, self.nothing)
        cv2.createTrackbar('SATURATION', 'Room', 0, 100, self.nothing)
        cv2.createTrackbar('HUE', 'Room', 0, 100, self.nothing)
        cv2.createTrackbar('CALIBRATE', 'Room', 0, 1, self.nothing)

        cv2.setTrackbarPos('BRIGHTNESS', 'Room', self.brightness)
        cv2.setTrackbarPos('CONTRAST', 'Room', self.contrast)
        cv2.setTrackbarPos('SATURATION', 'Room', self.saturation)
        cv2.setTrackbarPos('HUE', 'Room', self.hue)

        # Only need to create windows at the beginning

        while self.pressed_key != 27:
            self.capture.set(cv2.CAP_PROP_BRIGHTNESS, cv2.getTrackbarPos('BRIGHTNESS', 'Room')/100.0)
            self.capture.set(cv2.CAP_PROP_CONTRAST, cv2.getTrackbarPos('CONTRAST', 'Room')/100.0)
            self.capture.set(cv2.CAP_PROP_SATURATION, cv2.getTrackbarPos('SATURATION', 'Room')/100.0)
            self.capture.set(cv2.CAP_PROP_HUE, cv2.getTrackbarPos('HUE', 'Room')/100.0)
            self.frame()

        if self.world.room_num == 0:
            targetFile = open("vision/room0.txt", "w")
        else:
            targetFile = open("vision/room1.txt", "w")

        targetFile.write(str(cv2.getTrackbarPos('BRIGHTNESS', 'Room')))
        targetFile.write('\n')
        targetFile.write(str(cv2.getTrackbarPos('CONTRAST', 'Room')))
        targetFile.write('\n')
        targetFile.write(str(cv2.getTrackbarPos('SATURATION', 'Room')))
        targetFile.write('\n')
        targetFile.write(str(cv2.getTrackbarPos('HUE', 'Room')))
        targetFile.close()
        cv2.destroyAllWindows()

    def nothing(self, x):
        pass

    def frame(self):
        status, frame = self.capture.read()
        imgOriginal = self.step(frame)
        #blur = imgOriginal
        blur = cv2.GaussianBlur(imgOriginal, (3, 3), 2) #todo: what values are best
#########################################################################################################################################
        if cv2.getTrackbarPos('CALIBRATE', 'Room') == 1:

            cv2.setTrackbarPos('CALIBRATE', 'Room', 0)
            colors = ['red', 'blue', 'yellow', 'pink', 'green']
            data, R_goal, L_goal, R_defend, L_defend, pitch_corners = getColors(self.world.room_num, imgOriginal)

            for color in colors:
                if color in data.keys():
                    if color == 'red':
                        hmax = data['maroon']['min']
                        hmin = data['maroon']['max']
                        lmin = data['red']['min']
                        lmax = data['red']['max']
                        self.color_ranges[color] = [((lmin[0], lmin[1], lmin[2]), (lmax[0], lmax[1], lmax[2])),
                                                    ((hmin[0], hmin[1], hmin[2]), (hmax[0], hmax[1], hmax[2]))]
                    elif color == 'blue' and 'bright_blue' in data.keys():
                        hmax = data['blue']['min']
                        hmin = data['blue']['max']
                        lmin = data['bright_blue']['min']
                        lmax = data['bright_blue']['max']
                        self.color_ranges[color] = [((lmin[0], lmin[1], lmin[2]), (lmax[0], lmax[1], lmax[2])),
                                                    ((hmin[0], hmin[1], hmin[2]), (hmax[0], hmax[1], hmax[2]))]
                    elif color == 'blue' and 'bright_blue' not in data.keys():
                        min = data[color]['min']
                        max = data[color]['max']
                        self.color_ranges[color] = [((min[0], min[1], min[2]), (max[0], max[1], max[2]))]
                    else:
                        min = data[color]['min']
                        max = data[color]['max']
                        self.color_ranges[color] = [((min[0], min[1], min[2]), (max[0], max[1], max[2]))]
                elif 'bright_blue' in data.keys() and 'blue' not in data.keys():
                    min = data['bright_blue']['min']
                    max = data['bright_blue']['max']
                    self.color_ranges[color] = [((min[0], min[1], min[2]), (max[0], max[1], max[2]))]

            if self.world.room_num == 1:
                targetFile1 = open("vision/color1.txt", "w")
                targetFile2 = open("vision/pitch1.txt", "w")
            else:
                targetFile2 = open("vision/pitch0.txt", "w")
                targetFile1 = open("vision/color0.txt", "w")

            targetFile1.write(str(self.color_ranges))
            targetFile2.write("{'rightgoal': "+ str(R_goal) +",'leftgoal': "+ str(L_goal)+",'rightdefend': "+ str(R_defend)+",'leftdefend': "+ str(L_defend)+",'pitch': "+ str(pitch_corners)+"}")

            targetFile1.close()
            targetFile2.close()

        ##########################################################################################################################################

        else:
            hsv_image = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
            mask = None
            for ranges in self.color_ranges.itervalues():
                for begin, end in ranges:
                    color_mask = cv2.inRange(hsv_image, begin, end)
                    if mask is None:
                        mask = color_mask
                    else:
                        mask += color_mask

            cv2.imshow('Mask', mask)

            # Label the clusters
            labels, num = measurements.label(mask)

            areas = measurements.sum(mask, labels, xrange(1, num + 1))

            # All centers can be calculated in one numpy call
            centers = measurements.center_of_mass(mask, labels, xrange(1, num + 1))
            center_indices = areas.argsort()[::-1]

            circles = {color_name: [] for color_name in self.color_ranges}
            for center_index in center_indices:
                center = centers[center_index]
                color = None
                for color_name, ranges in self.color_ranges.iteritems():
                    for begin, end in ranges:
                        if cv2.inRange(np.array([[hsv_image[center]]]), begin, end):
                            color = color_name
                # if color is None:
                #    color = COLOR_RANGES.keys()[np.linalg.norm(COLOR_AVERAGES - self.image[center], axis=1).argmin()]
                if color is not None and len(circles[color]) < MAX_COLOR_COUNTS[color] and areas[center_index] > \
                        self.min_color_area[color]:
                    if color == 'red':
                        if 10 < center[1] < self.COLS - 10: #todo Danger hard coded
                            circles[color].append((center[1], center[0], areas[center_index], color))
                    elif color == 'blue':
                        if 10 < center[0] < self.COLS - 10: #todo Danger hard coded
                            circles[color].append((center[1], center[0], areas[center_index], color))
                    else:
                        circles[color].append((center[1], center[0], areas[center_index], color))

            # draws circles spotted
            for color_name, positions in circles.iteritems():
                for x, y, area, color in positions:
                    if color != 'red':
                        cv2.circle(imgOriginal, (int(x), int(y)), 8, COLORS[color_name], 1)

            self.getRobots(circles)
            self.getBall(circles)

            # Draw ball
            cv2.circle(imgOriginal, (self.world.ball[0], self.world.ball[1]), 8, COLORS['red'], 1)

            # Draw balls trajectory
            delta_x = self.trajectory_list[len(self.trajectory_list) - 1][0] - self.trajectory_list[0][0]
            if abs(delta_x) > 10:
                self.world.ball_moving.value = True
                future_x = self.trajectory_list[len(self.trajectory_list) - 1][0] + delta_x
                m = (self.trajectory_list[len(self.trajectory_list) - 1][1] - self.trajectory_list[0][1]) / float(delta_x)
                future_y = (future_x - self.trajectory_list[0][0]) * m + self.trajectory_list[0][1]
                self.world.ball_velocity[0] = (future_x - self.world.ball[0])/6.0
                self.world.ball_velocity[1] = (future_y - self.world.ball[1])/6.0
                cv2.line(imgOriginal, (int(self.trajectory_list[len(self.trajectory_list) - 1][0]), int(self.trajectory_list[len(self.trajectory_list) - 1][1])), (int(future_x), int(future_y)), COLORS['red'], 1)
            else:
                self.world.ball_moving.value = False

            # Draw robots
            for robot_id, robot in enumerate([self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2]):
                if robot.position[0] != NO_VALUE:
                    cv2.rectangle(imgOriginal, (robot.position[0] - 20, robot.position[1] - 20),
                                  (robot.position[0] + 20, robot.position[1] + 20), self.robot_color(robot_id, robot.out), 2)
                    cv2.arrowedLine(imgOriginal, (robot.position[0], robot.position[1]),
                                    (int(robot.position[0] + robot.orientation[0] * 50.0),
                                     int(robot.position[1] + robot.orientation[1] * 50.0)),
                                    self.robot_color(robot_id, robot.out), 2)
                    cv2.putText(imgOriginal, str(robot_id), (robot.position[0] + 20, robot.position[1] + 40),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                2, self.robot_color(robot_id, robot.out))
            if self.start < 10:
                self.start +=1
            self.pressed_key = cv2.waitKey(2) & 0xFF
            cv2.imshow('Room', imgOriginal)

    def robot_color(self, r_id, out):
        if out is True:
            return COLORS['blue']
        else:
            if r_id == 0:
                return COLORS['green']
            elif r_id == 1:
                return COLORS['green']
            elif r_id == 2:
                return COLORS['red']
            elif r_id == 3:
                return COLORS['red']

    # returns one ball
    def getBall(self, circles): #todo look over and test everything in here
        found = False
        robots_pos = [self.world.venus.position, self.world.friend.position, self.world.enemy1.position, self.world.enemy2.position]
        if len(circles['red']) == 0:
            self.world.ball[0] = self.world.ball[0]
            self.world.ball[1] = self.world.ball[1]
        else:
            sorted(circles, key=lambda x: x[2], reverse=True)
            for i in range(0, len(circles['red'])-1):
                its_robot = False
                for position in robots_pos:
                    if math.sqrt((position[0]-circles['red'][i][0])**2 + (position[1]-circles['red'][i][1])**2) < 25: #todo Danger hard coded
                        its_robot = True
                if not its_robot:
                    found = True
                    self.world.ball[0] = int(circles['red'][i][0])
                    self.world.ball[1] = int(circles['red'][i][1])

                    for positionIndex in range(0, len(robots_pos)):
                        position = robots_pos[positionIndex]
                        # todo Danger hard coded
                        if positionIndex == 0:
                            if math.sqrt((position[0]-circles['red'][i][0])**2 + (position[1]-circles['red'][i][1])**2) < 90: # todo: this is different!
                                self.world.venus.hasBallInRange.value = True
                            else:
                                self.world.venus.hasBallInRange.value = False
                        if positionIndex == 1:
                            if math.sqrt((position[0]-circles['red'][i][0])**2 + (position[1]-circles['red'][i][1])**2) < 45:
                                self.world.friend.hasBallInRange.value = True
                            else:
                                self.world.friend.hasBallInRange.value = False
                        if positionIndex == 2:
                            if math.sqrt((position[0]-circles['red'][i][0])**2 + (position[1]-circles['red'][i][1])**2) < 45:
                                self.world.enemy1.hasBallInRange.value = True
                            else:
                                self.world.enemy1.hasBallInRange.value = False
                        if positionIndex == 3:
                            if math.sqrt((position[0]-circles['red'][i][0])**2 + (position[1]-circles['red'][i][1])**2) < 45:
                                self.world.enemy2.hasBallInRange.value = True
                            else:
                                self.world.enemy2.hasBallInRange.value = False

                    self.trajectory_list.append((int(circles['red'][i][0]), int(circles['red'][i][1])))
                    self.trajectory_list.pop(0)
                    break
            if not found:
                flag = False
                for positionIndex in range(0,len(robots_pos)):
                    position = robots_pos[positionIndex]

                    if positionIndex == 0 and self.world.venus.hasBallInRange.value:
                        self.world.ball[0] = self.world.ball[0]
                        self.world.ball[1] = self.world.ball[1]
                        '''
                        flag = True
                        # 'closest' is the robot who might have the ball, let's check that
                        distance_between_points = math.sqrt((position[0] - self.world.venus.orientation[0])**2 + (position[1] -
                                                            self.world.venus.orientation[1])**2)
                        # we want point that is ten pixels away from the centre towards the orientation vector endpoint
                        ratio = 2.0/distance_between_points
                        # then point's coordinates will be
                        new_x = int(position[0] + 20 * (1-ratio) * self.world.venus.orientation[0])
                        new_y = int(position[1] + 20 * (1-ratio) * self.world.venus.orientation[1])
                        self.world.ball[0] = new_x
                        self.world.ball[1] = new_y
                    '''
                    if positionIndex == 1 and self.world.friend.hasBallInRange.value :
                        flag = True
                        # 'closest' is the robot who might have the ball, let's check that
                        distance_between_points = math.sqrt((position[0] - self.world.friend.orientation[0])**2 + (position[1] -
                                                             self.world.friend.orientation[1])**2)
                        # we want point that is ten pixels away from the centre towards the orientation vector endpoint
                        ratio = 2.0/distance_between_points

                        # then point's coordinates will be
                        new_x = int(position[0] + 20 * (1-ratio) * self.world.friend.orientation[0])
                        new_y = int(position[1] + 20 * (1-ratio) * self.world.friend.orientation[1])
                        self.world.ball[0] = new_x
                        self.world.ball[1] = new_y

                    if positionIndex == 2 and self.world.enemy1.hasBallInRange.value :
                        flag = True
                        # 'closest' is the robot who might have the ball, let's check that
                        distance_between_points = math.sqrt((position[0] - self.world.enemy1.orientation[0])**2 + (position[1] -
                                                             self.world.enemy1.orientation[1])**2)
                        # we want point that is ten pixels away from the centre towards the orientation vector endpoint
                        ratio = 2.0/distance_between_points

                        # then point's coordinates will be
                        new_x = int(position[0] + 20 * (1-ratio) * self.world.enemy1.orientation[0])
                        new_y = int(position[1] + 20 * (1-ratio) * self.world.enemy1.orientation[1])
                        self.world.ball[0] = new_x
                        self.world.ball[1] = new_y

                    if positionIndex == 3 and self.world.enemy2.hasBallInRange.value :
                        flag = True
                        # 'closest' is the robot who might have the ball, let's check that
                        distance_between_points = math.sqrt((position[0] - self.world.enemy2.orientation[0])**2 + (position[1] -
                                                             self.world.enemy2.orientation[1])**2)
                        # we want point that is ten pixels away from the centre towards the orientation vector endpoint
                        ratio = 2.0/distance_between_points

                        # then point's coordinates will be
                        new_x = int(position[0] + 20 * (1-ratio) * self.world.enemy2.orientation[0])
                        new_y = int(position[1] + 20 * (1-ratio) * self.world.enemy2.orientation[1])
                        self.world.ball[0] = new_x
                        self.world.ball[1] = new_y

                if not flag:
                    self.world.ball[0] = self.world.ball[0]
                    self.world.ball[1] = self.world.ball[1]

    def getRobots(self, circles):
        pointList = circles["green"] + circles["pink"] + circles["blue"] + circles["yellow"]
        pointsSorted = sorted(pointList, key=lambda x: x[2], reverse=True)
        pointsUsed = []
        robots = []
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robots.append({'pink': [], 'blue': [], 'green': [], 'yellow': []})
        robotCounter = 0
        for point in pointsSorted:
            if pointsSorted is not None and point not in pointsUsed:  #todo cropping variable
                pointsUsed.append(point)
                localPoints = []
                counter = 0
                if pointsSorted is not None:
                    for localPoint in pointsSorted:
                        if math.sqrt((point[0] - localPoint[0]) ** 2 + (point[1] - localPoint[1]) ** 2) < 30 and counter < 5:
                            counter += 1
                            localPoints.append(localPoint)
                            pointsUsed.append(localPoint)
                    if robotCounter < 8:
                        for robotPoint in localPoints:
                            if robotPoint[3] == 'pink':
                                robots[robotCounter]['pink'].append(robotPoint)
                            if robotPoint[3] == 'blue':
                                robots[robotCounter]['blue'].append(robotPoint)
                            if robotPoint[3] == 'green':
                                robots[robotCounter]['green'].append(robotPoint)
                            if robotPoint[3] == 'yellow':
                                robots[robotCounter]['yellow'].append(robotPoint)
                    robotCounter += 1
        ################################################################
        self.flag = [False, False, False, False]
        self.last_save = [0, 0, 0, 0]

        for robot in robots:
            # Best cases know all information
            if len(robot[self.world.team_color]) == 1 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) > 1 or len(
                    robot[self.world.team_color]) == 1 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) == 1:
                self.findVenus(robot)

            elif len(robot[self.world.team_color]) == 1 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) > 1 or len(
                    robot[self.world.team_color]) == 1 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) == 1:
                self.findFriend(robot)

            elif len(robot[self.world.enemy_color]) == 1 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) > 1 or len(
                    robot[self.world.enemy_color]) == 1 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) == 1:
                self.findEnemy1(robot)

            elif len(robot[self.world.enemy_color]) == 1 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) > 1 or len(
                    robot[self.world.enemy_color]) == 1 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) == 1:
                self.findEnemy2(robot)

            elif len(robot[self.world.team_color]) > 0 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) > 1 or len(
                    robot[self.world.team_color]) > 0 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) == 1:
                self.findVenus(robot)

            elif len(robot[self.world.team_color]) > 0 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) > 1 or len(
                    robot[self.world.team_color]) > 0 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) == 1:
                self.findFriend(robot)

            elif len(robot[self.world.enemy_color]) > 0 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) > 1 or len(
                    robot[self.world.enemy_color]) > 0 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) == 1:
                self.findEnemy1(robot)

            elif len(robot[self.world.enemy_color]) > 0 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) > 1 or len(
                    robot[self.world.enemy_color]) > 0 and len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) == 1:
                self.findEnemy2(robot)

            # can't see centre spot
            elif len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) > 1 and not self.flag[0] or len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) == 1 and not self.flag[0]:
                self.findVenus(robot)

            elif len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) > 1 and not self.flag[1] or len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) == 1 and not self.flag[1]:
                self.findFriend(robot)

            elif len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) > 1 and not self.flag[2] or len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) == 1 and not self.flag[2]:
                self.findEnemy1(robot)

            elif len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) > 1 and not self.flag[3] or len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) == 1 and not self.flag[3]:
                self.findEnemy2(robot)

            # looses 1 color
            elif len(robot[self.world.other_color]) > 1 and not self.flag[0] and len(robot[self.world.our_color]) < 2 :
                self.findVenus(robot)

            elif len(robot[self.world.our_color]) > 1 and not self.flag[1] and len(robot[self.world.other_color]) < 2 :
                self.findFriend(robot)

            elif len(robot[self.world.other_color]) > 1 and not self.flag[2] and len(robot[self.world.our_color]) < 2 :
                self.findEnemy1(robot)

            elif len(robot[self.world.our_color]) > 1 and not self.flag[3] and len(robot[self.world.other_color]) < 2 :
                self.findEnemy2(robot)

        # save position from last time
        if self.flag[0] is False:
            angle = math.degrees(math.atan2(self.world.venus.orientation[0], self.world.venus.orientation[1]))
            self.save_robot((self.world.venus.position[0], self.world.venus.position[1]), angle, 0)
            self.flag[0] = True
            self.out_counter[0] += 1
            if self.out_counter[0] > 100:
                self.out_counter[0] = 0
                self.world.venus.out.value = True

        if self.flag[1] is False:
            angle = math.degrees(math.atan2(self.world.friend.orientation[0], self.world.friend.orientation[1]))
            self.save_robot((self.world.friend.position[0], self.world.friend.position[1]), angle, 1)
            self.flag[1] = True
            self.out_counter[1] += 1
            if self.out_counter[1] > 100:
                self.out_counter[1] = 0
                self.world.friend.out.value = True

        if self.flag[2] is False:
            angle = math.degrees(math.atan2(self.world.enemy1.orientation[0], self.world.enemy1.orientation[1]))
            self.save_robot((self.world.enemy1.position[0], self.world.enemy1.position[1]), angle, 2)
            self.flag[2] = True
            self.out_counter[2] += 1
            if self.out_counter[2] > 100:
                self.out_counter[2] = 0
                self.world.enemy1.out.value = True

        if self.flag[3] is False:
            angle = math.degrees(math.atan2(self.world.enemy2.orientation[0], self.world.enemy2.orientation[1]))
            self.save_robot((self.world.enemy2.position[0], self.world.enemy2.position[1]), angle, 3)
            self.flag[3] = True
            self.out_counter[3] += 1
            if self.out_counter[3] > 100:
                self.out_counter[3] = 0
                self.world.enemy2.out.value = True

            # venus
            ###################################################################################################################

    def findVenus(self, robot):
        if self.last_save[0] == 0:
            if len(robot[self.world.our_color]) == 1 and len(robot[self.world.team_color]) == 1:
                if math.sqrt((robot[self.world.team_color][0][0]-self.world.friend.position[0])**2 + (robot[self.world.team_color][0][1]-self.world.friend.position[1])**2) > 50:
                    self.single_spot(robot, self.world.team_color, self.world.our_color, 0)

            if len(robot[self.world.other_color]) == 3 and not self.flag[0]:
                self.three_spot(robot, self.world.other_color, self.world.team_color, self.world.enemy1, 0)
        else:
            if len(robot[self.world.other_color]) == 3:
                self.three_spot(robot, self.world.other_color, self.world.team_color, self.world.enemy1, 0)

            if len(robot[self.world.our_color]) == 1 and len(robot[self.world.team_color]) == 1 and not self.flag[0]:
                if math.sqrt((robot[self.world.team_color][0][0]-self.world.friend.position[0])**2 + (robot[self.world.team_color][0][1]-self.world.friend.position[1])**2) > 50:
                    self.single_spot(robot, self.world.team_color, self.world.our_color, 0)

            # Team mate
            ####################################################################################################################

    def findFriend(self, robot):
        if self.last_save[1] == 0:
            if len(robot[self.world.other_color]) == 1 and len(robot[self.world.team_color]) == 1:
                if math.sqrt((robot[self.world.team_color][0][0]-self.world.venus.position[0])**2 + (robot[self.world.team_color][0][1]-self.world.venus.position[1])**2) > 50:
                    self.single_spot(robot, self.world.team_color, self.world.other_color, 1)

            if len(robot[self.world.our_color]) == 3 and not self.flag[1]:
                self.three_spot(robot, self.world.our_color, self.world.team_color, self.world.enemy2, 1)
        else:
            if len(robot[self.world.our_color]) == 3:
                self.three_spot(robot, self.world.our_color, self.world.team_color, self.world.enemy2, 1)

            if len(robot[self.world.other_color]) == 1 and len(robot[self.world.team_color]) == 1 and not self.flag[1]:
                if math.sqrt((robot[self.world.team_color][0][0]-self.world.venus.position[0])**2 + (robot[self.world.team_color][0][1]-self.world.venus.position[1])**2) > 50:
                    self.single_spot(robot, self.world.team_color, self.world.other_color, 1)


            # Enemy 1
            ######################################################################################################################

    def findEnemy1(self, robot):
        if self.last_save[2] == 0:
            if len(robot[self.world.our_color]) == 1 and len(robot[self.world.enemy_color]) == 1:
                if math.sqrt((robot[self.world.enemy_color][0][0]-self.world.enemy2.position[0])**2 + (robot[self.world.enemy_color][0][1]-self.world.enemy2.position[1])**2) > 50:
                    self.single_spot(robot, self.world.enemy_color, self.world.our_color, 2)

            if len(robot[self.world.other_color]) == 3 and not self.flag[2]:
                self.three_spot(robot, self.world.other_color, self.world.enemy_color, self.world.venus, 2)
        else:
            if len(robot[self.world.other_color]) == 3:
                self.three_spot(robot, self.world.other_color, self.world.enemy_color, self.world.venus, 2)

            if len(robot[self.world.our_color]) == 1 and len(robot[self.world.enemy_color]) == 1 and not self.flag[2]:
                if math.sqrt((robot[self.world.enemy_color][0][0]-self.world.enemy2.position[0])**2 + (robot[self.world.enemy_color][0][1]-self.world.enemy2.position[1])**2) > 50:
                    self.single_spot(robot, self.world.enemy_color, self.world.our_color, 2)


            # enemy 2
            #######################################################################################################################

    def findEnemy2(self, robot):
        if self.last_save[3] == 0:
            if len(robot[self.world.other_color]) == 1 and len(robot[self.world.enemy_color]) == 1:
                if math.sqrt((robot[self.world.enemy_color][0][0]-self.world.enemy1.position[0])**2 + (robot[self.world.enemy_color][0][1]-self.world.enemy1.position[1])**2) > 50:
                    self.single_spot(robot, self.world.enemy_color, self.world.other_color, 3)

            if len(robot[self.world.our_color]) == 3 and not self.flag[3]:
                self.three_spot(robot, self.world.our_color, self.world.enemy_color, self.world.friend, 3)
        else:
            if len(robot[self.world.our_color]) == 3:
                self.three_spot(robot, self.world.our_color, self.world.enemy_color, self.world.friend, 3)

            if len(robot[self.world.other_color]) == 1 and len(robot[self.world.enemy_color]) == 1 and not self.flag[3]:
                if math.sqrt((robot[self.world.enemy_color][0][0]-self.world.enemy1.position[0])**2 + (robot[self.world.enemy_color][0][1]-self.world.enemy1.position[1])**2) > 50:
                    self.single_spot(robot, self.world.enemy_color, self.world.other_color, 3)


            ########################################################################################################################

    def save_robot(self, position, orientation, robot_id):
        robot = [self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2][robot_id]
        if abs(orientation - self.last_angle[robot_id]) > 10 and self.start > 10:
            orientation = math.degrees(math.atan2(robot[robot_id].orientation[0], robot[robot_id].orientation[1]))
        self.last_angle[robot_id] = orientation
        robot.position[0] = int(position[0])
        robot.position[1] = int(position[1])
        rad = math.radians(orientation)
        robot.orientation[0] = math.sin(rad)
        robot.orientation[1] = math.cos(rad)

    def three_spot(self, robot, three_spot_color, center_color, similar_bot, bot_id):
        bot = [self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2][bot_id]
        dist = []
        point_1 = []
        point_2 = []
        dist.append(math.sqrt((robot[three_spot_color][0][0] - robot[three_spot_color][1][0]) ** 2 + (
            robot[three_spot_color][0][1] - robot[three_spot_color][1][1]) ** 2))

        dist.append(math.sqrt((robot[three_spot_color][1][0] - robot[three_spot_color][2][0]) ** 2 + (
            robot[three_spot_color][1][1] - robot[three_spot_color][2][1]) ** 2))

        dist.append(math.sqrt((robot[three_spot_color][2][0] - robot[three_spot_color][0][0]) ** 2 + (
            robot[three_spot_color][2][1] - robot[three_spot_color][0][1]) ** 2))

        point_1.append((robot[three_spot_color][(dist.index(max(dist))) % 3][0] +
                        robot[three_spot_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0)
        point_1.append((robot[three_spot_color][(dist.index(max(dist))) % 3][1] +
                        robot[three_spot_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0)
        point_2.append(robot[three_spot_color][(dist.index(max(dist)) + 2) % 3][0])
        point_2.append(robot[three_spot_color][(dist.index(max(dist)) + 2) % 3][1])
        angle = self.normalize_angle(math.degrees(math.atan2(point_2[0] - point_1[0], point_2[1] - point_1[1])) + 45)
        center_x = (
                       robot[three_spot_color][(dist.index(max(dist))) % 3][0] +
                       robot[three_spot_color][(dist.index(max(dist)) + 1) % 3][
                           0]) / 2.0  # add something here
        center_y = (
                       robot[three_spot_color][(dist.index(max(dist))) % 3][1] +
                       robot[three_spot_color][(dist.index(max(dist)) + 1) % 3][
                           1]) / 2.0  # add something here

        if math.sqrt((center_x-similar_bot.position[0])**2 + (center_y-similar_bot.position[1])**2) > 50:
            self.save_robot((center_x, center_y), angle, bot_id)
            bot.out.value = False
            self.flag[bot_id] = True
            self.last_save[bot_id] = 1

    def single_spot(self, robot, center_color, single_color, bot_id):
        bot = [self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2][bot_id]
        angle = self.normalize_angle(math.degrees(math.atan2(robot[single_color][0][0] - robot[center_color][0][0],
                                            robot[single_color][0][1] - robot[center_color][0][1])) - 150)
        self.save_robot((robot[center_color][0][0], robot[center_color][0][1]), angle, bot_id)
        bot.out.value = False
        self.flag[bot_id] = True
        self.last_save[bot_id] = 0

    def normalize_angle(self, angle):
        if angle > 180:
            return float(angle-360)
        elif angle < -180:
            return float(angle+360)
        else:
            return angle

    def step(self, frame):
        frame = self.undistort(frame)
        frame = self.perspective(frame)
        frame = self.translate(frame)
        frame = self.warp(frame)
        return frame

    # Scale center
    def translate(self, frame):
        if self.world.room_num == 0:
            M = np.float32([[1,0,-5],[0,1,-5]])
            return cv2.warpAffine(frame, M, (self.COLS, self.ROWS))
        else:
            return frame

    def undistort(self, frame):
        return cv2.undistort(frame, self.mtx, self.dist, None,self.newmtx)
    # Rotate
    def warp(self, frame):
        if self.world.room_num == 0:
            return frame
        else:
            M = cv2.getRotationMatrix2D((self.COLS/2, self.ROWS/2), 1, 1)
            return cv2.warpAffine(frame, M, (self.COLS, self.ROWS))

    def perspective(self, frame):

        if self.world.room_num == 0:
            return frame
        else:
            pts1 = np.float32([[5,5],[5,self.ROWS-5],[self.COLS, self.ROWS],[self.COLS,0]])
            pts2 = np.float32([[0,0],[0,self.ROWS],[self.COLS, self.ROWS],[self.COLS,0]])
            M = cv2.getPerspectiveTransform(pts1,pts2)
            dst = cv2.warpPerspective(frame, M, (self.COLS, self.ROWS))
            return dst


