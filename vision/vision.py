import cv2
from pylab import *
from scipy.ndimage import measurements

from strategy.world import NO_VALUE

VISION_ROOT = 'vision/'

MAX_COLOR_COUNTS = {
    'red': 9,
    'blue': 2,
    'yellow': 2,
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
        self.trajectory_list = [(0, 0)] * 10


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
            target.close()

            self.min_color_area = {
                    'red': 100.0,
                    'blue': 1000.0,
                    'yellow': 1000.0,
                    'pink': 2000.0,
                    'green': 2000.0,
                }
            self.mtx = np.loadtxt(VISION_ROOT + "mtx1.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist1.txt")
            self.pts1 = np.float32([[33, 12], [609, 16], [607, 475], [22, 462]])
            # self.pts1 = np.float32([[10, 2], [634, 37], [596, 478], [6, 456]])

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
            target.close()

            self.min_color_area = {
                    'red': 100.0,
                    'blue': 1000.0,
                    'yellow': 1000.0,
                    'pink': 2000.0,
                    'green': 2000.0,
                }
            self.mtx = np.loadtxt(VISION_ROOT + "mtx0.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist0.txt")
            self.pts1 = np.float32([[33, 12], [609, 16], [607, 475], [22, 462]])
            # self.pts1 = np.float32([[7, 5], [607, 4], [593, 451], [17, 450]])

# ################################################################################################

        else:
            print("invalid room id")

        self.capture = cv2.VideoCapture(0)

        cv2.namedWindow("Mask")
        cv2.namedWindow("Room")

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 440)
        cv2.createTrackbar('BRIGHTNESS', 'Room', 0, 100, self.nothing)
        cv2.createTrackbar('CONTRAST', 'Room', 0, 100, self.nothing)
        cv2.createTrackbar('CALIBRATE', 'Room', 0, 1, self.nothing)
        cv2.setTrackbarPos('BRIGHTNESS', 'Room', self.brightness)
        cv2.setTrackbarPos('CONTRAST', 'Room', self.contrast)

        self.capture.set(cv2.CAP_PROP_SATURATION, 0.6)
        self.capture.set(cv2.CAP_PROP_HUE, 0.5)


        # Only need to create windows at the beginning

        while self.pressed_key != 27:
            if self.world.room_num == 0:
                self.capture.set(cv2.CAP_PROP_BRIGHTNESS, cv2.getTrackbarPos('BRIGHTNESS', 'Room')/100.0)
                self.capture.set(cv2.CAP_PROP_CONTRAST, cv2.getTrackbarPos('CONTRAST', 'Room')/100.0)
            else:
                self.capture.set(cv2.CAP_PROP_BRIGHTNESS, cv2.getTrackbarPos('BRIGHTNESS', 'Room')/100.0)
                self.capture.set(cv2.CAP_PROP_CONTRAST, cv2.getTrackbarPos('CONTRAST', 'Room')/100.0)

            if cv2.getTrackbarPos('CALIBRATE', 'Room') == 0:
                self.frame()

            else:
                cv2.setTrackbarPos('CALIBRATE', 'Room', 0)
                self.pressed_key = None
                self.exit_key = None
                self.image = None
                self.imageHSV = None
                self.pressed_key = None
                self.counter = 0
                self.colorMedians = []
                self.snapShot(self.capture)
                cv2.namedWindow('calibrate')
                cv2.setMouseCallback('calibrate', self.on_mouse, 0)
                self.show("vision/calibrate.png")
                cv2.destroyWindow('calibrate')

                if self.world.room_num == 1:
                    target = open('vision/color1.txt', 'r')
                    self.color_ranges = eval(target.read())
                    target.close()
                elif self.world.room_num == 0:
                    target = open('vision/color0.txt', 'r')
                    self.color_ranges = eval(target.read())
                    target.close()

        if self.world.room_num == 0:
            targetFile = open("vision/room0.txt", "w")
        else:
            targetFile = open("vision/room1.txt", "w")

        targetFile.write(str(cv2.getTrackbarPos('BRIGHTNESS', 'Room')))
        targetFile.write('\n')
        targetFile.write(str(cv2.getTrackbarPos('CONTRAST', 'Room')))
        targetFile.close()
        cv2.destroyAllWindows()

    def nothing(self, x):
        pass

    def frame(self):
        status, frame = self.capture.read()
        h, w = frame.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 0, (w, h))

        # These are the actual values needed to undistort:
        dst = cv2.undistort(frame, self.mtx, self.dist, None, newcameramtx)

        # crop the image
        x, y, w, h = roi
        dst = dst[y:y + h, x:x + w]

        # Apply perspective transformation
        pts2 = np.float32([[0, 0], [639, 0], [639, 479], [0, 479]])
        M = cv2.getPerspectiveTransform(self.pts1, pts2)
        imgOriginal = cv2.warpPerspective(dst, M, (639, 479))

        imgOriginal = cv2.GaussianBlur(imgOriginal, (3, 3), 2)

        self.image = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2HSV)

        mask = None
        for ranges in self.color_ranges.itervalues():
            for begin, end in ranges:
                color_mask = cv2.inRange(self.image, begin, end)
                if mask is None:
                    mask = color_mask
                else:
                    mask += color_mask

        #mask = cv2.GaussianBlur(mask, (3, 3), 2)

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
                    if cv2.inRange(np.array([[self.image[center]]]), begin, end):
                        color = color_name
            # if color is None:
            #    color = COLOR_RANGES.keys()[np.linalg.norm(COLOR_AVERAGES - self.image[center], axis=1).argmin()]
            if color is not None and len(circles[color]) < MAX_COLOR_COUNTS[color] and areas[center_index] > \
                    self.min_color_area[color]:
                if color == 'red':
                    if 5 < center[0] < 435:
                        circles[color].append((center[1], center[0], areas[center_index], color))
                else:
                    circles[color].append((center[1], center[0], areas[center_index], color))

        # draws circles spotted doqqq
        for color_name, positions in circles.iteritems():
            for x, y, area, color in positions:
                cv2.circle(imgOriginal, (int(x), int(y)), 8, COLORS[color_name], 1)

        # draw balls trajectory
        delta_x = self.trajectory_list[len(self.trajectory_list) - 1][0] - self.trajectory_list[0][0]
        if abs(delta_x) > 10:
            self.world.ball_moving.value = True
            future_x = self.trajectory_list[len(self.trajectory_list) - 1][0] + delta_x
            m = (self.trajectory_list[len(self.trajectory_list) - 1][1] - self.trajectory_list[0][1]) / float(delta_x)
            future_y = (future_x - self.trajectory_list[0][0]) * m + self.trajectory_list[0][1]
            self.world.future_ball[0] = int(future_x)
            self.world.future_ball[1] = int(future_y)
            cv2.line(imgOriginal, (int(self.trajectory_list[len(self.trajectory_list) - 1][0]), int(self.trajectory_list[len(self.trajectory_list) - 1][1])), (int(future_x), int(future_y)), COLORS['red'], 1)
        else:
            self.world.ball_moving.value = False

        self.getRobots(circles)
        self.getBall(circles, imgOriginal)

        for robot_id, robot in enumerate([self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2]):
            if robot.position[0] != NO_VALUE:
                cv2.rectangle(imgOriginal, (robot.position[0] - 20, robot.position[1] - 20),
                              (robot.position[0] + 20, robot.position[1] + 20), self.robot_color(robot_id), 2)
                cv2.arrowedLine(imgOriginal, (robot.position[0], robot.position[1]),
                                (int(robot.position[0] + robot.orientation[0] * 50.0),
                                 int(robot.position[1] + robot.orientation[1] * 50.0)),
                                self.robot_color(robot_id), 2)
                cv2.putText(imgOriginal, str(robot_id), (robot.position[0] + 20, robot.position[1] + 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            2, self.robot_color(robot_id))

        cv2.imshow('Room', imgOriginal)
        self.pressed_key = cv2.waitKey(2) & 0xFF

    def robot_color(self, r_id):
        if r_id == 0:
            return COLORS['green']
        elif r_id == 1:
            return COLORS['yellow']
        elif r_id == 2:
            return COLORS['red']
        elif r_id == 3:
            return COLORS['red']

    # returns one ball
    def getBall(self, circles, imgOriginal):
        its_robot = False
        robot_pos = [self.world.venus.position, self.world.friend.position, self.world.enemy1.position, self.world.enemy2.position]
        if len(circles['red']) == 0:
            self.world.ball[0] = self.world.ball[0]
            self.world.ball[1] = self.world.ball[1]
        else:
            for i in range(0, len(circles['red'])-1):
                for position in robot_pos:
                    if math.sqrt((position[0]-circles['red'][i][0])**2 + (position[1]-circles['red'][i][1])**2) < 24:
                        its_robot = True
                if its_robot is False:
                    self.world.ball[0] = int(circles['red'][i][0])
                    self.world.ball[1] = int(circles['red'][i][1])
                    self.trajectory_list.append((int(circles['red'][i][0]), int(circles['red'][i][1])))
                    self.trajectory_list.pop(0)
                    break
                else:
                    self.world.ball[0] = self.world.ball[0]
                    self.world.ball[1] = self.world.ball[1]

    def getRobots(self, circles):
        self.single_angle = -150
        self.triple_angle = 45
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
            if 10 < point[1] < 430 and 10 < point[0] < 590 and pointsSorted is not None and point not in pointsUsed:  # dodgy blue stuff in top left
                pointsUsed.append(point)
                localPoints = []
                counter = 0
                if pointsSorted is not None:
                    for localPoint in pointsSorted:
                        if sqrt((point[0] - localPoint[0]) ** 2 + (point[1] - localPoint[1]) ** 2) < 25:
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
        self.venus = False
        self.friend = False
        self.enemy1 = False
        self.enemy2 = False

        for robot in robots:
            if len(robot[self.world.team_color]) > 0 and len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) > 1 or len(
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

            elif len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) > 1 and not self.venus or len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) == 1 and not self.venus:
                self.findVenus(robot)

            elif len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.our_color]) > 1 and not self.friend or len(robot[self.world.enemy_color]) == 0 and len(robot[self.world.other_color]) == 1 and not self.friend:
                self.findFriend(robot)

            elif len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) > 1 and not self.enemy1 or len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) == 1 and not self.enemy1:
                self.findEnemy1(robot)

            elif len(robot[self.world.team_color]) == 0 and len(robot[self.world.our_color]) > 1 and not self.enemy2 or len(robot[self.world.team_color]) == 0 and len(robot[self.world.other_color]) == 1 and not self.enemy2:
                self.findEnemy2(robot)

            elif len(robot[self.world.other_color]) > 1 and not self.venus and len(robot[self.world.our_color]) < 2 :
                self.findVenus(robot)

            elif len(robot[self.world.our_color]) > 1 and not self.friend and len(robot[self.world.other_color]) < 2 :
                self.findFriend(robot)

            elif len(robot[self.world.other_color]) > 1 and not self.enemy1 and len(robot[self.world.our_color]) < 2 :
                self.findEnemy1(robot)

            elif len(robot[self.world.our_color]) > 1 and not self.enemy2 and len(robot[self.world.other_color]) < 2 :
                self.findEnemy2(robot)


        if self.venus is False:
            angle = math.degrees(math.atan2(self.world.venus.orientation[0], self.world.venus.orientation[1]))
            self.save_robot((self.world.venus.position[0], self.world.venus.position[1]), angle, 0)
            self.venus = True
        if self.friend is False:
            angle = math.degrees(math.atan2(self.world.friend.orientation[0], self.world.friend.orientation[1]))
            self.save_robot((self.world.friend.position[0], self.world.friend.position[1]), angle, 1)
            self.friend = True
        if self.enemy1 is False:
            angle = math.degrees(math.atan2(self.world.enemy1.orientation[0], self.world.enemy1.orientation[1]))
            self.save_robot((self.world.enemy1.position[0], self.world.enemy1.position[1]), angle, 2)
            self.enemy1 = True
        if self.enemy2 is False:
            angle = math.degrees(math.atan2(self.world.enemy2.orientation[0], self.world.enemy2.orientation[1]))
            self.save_robot((self.world.enemy2.position[0], self.world.enemy2.position[1]), angle, 3)
            self.enemy2 = True

            # venus
            ###################################################################################################################

    def findVenus(self, robot):
        if len(robot[self.world.our_color]) == 1 and len(robot[self.world.team_color]) == 1 and abs(robot[self.world.team_color][0][0]-self.world.friend.position[0]) > 10 and abs(robot[self.world.team_color][0][1]-self.world.friend.position[1]) > 10:
            if math.sqrt((robot[self.world.team_color][0][0]-self.world.friend.position[0])**2 + (robot[self.world.team_color][0][1]-self.world.friend.position[1])**2) > 50:
                angle = self.normalize_angle(math.degrees(math.atan2(robot[self.world.our_color][0][0] - robot[self.world.team_color][0][0],
                                            robot[self.world.our_color][0][1] - robot[self.world.team_color][0][1])) + self.single_angle)
                self.save_robot((robot[self.world.team_color][0][0], robot[self.world.team_color][0][1]), angle, 0)
                self.venus = True
            else:
                angle = math.degrees(math.atan2(self.world.venus.orientation[0], self.world.venus.orientation[1]))
                self.save_robot((self.world.venus.position[0], self.world.venus.position[1]), angle, 0)
                self.venus = True

        elif len(robot[self.world.other_color]) == 3:
            dist = []
            point_1 = []
            point_2 = []
            dist.append(sqrt(
                    (robot[self.world.other_color][0][0] - robot[self.world.other_color][1][0]) ** 2 + (robot[self.world.other_color][0][1] - robot[self.world.other_color][1][1]) ** 2))
            dist.append(sqrt(
                    (robot[self.world.other_color][1][0] - robot[self.world.other_color][2][0]) ** 2 + (robot[self.world.other_color][1][1] - robot[self.world.other_color][2][1]) ** 2))
            dist.append(sqrt(
                    (robot[self.world.other_color][2][0] - robot[self.world.other_color][0][0]) ** 2 + (robot[self.world.other_color][2][1] - robot[self.world.other_color][0][1]) ** 2))
            point_1.append((robot[self.world.other_color][(dist.index(max(dist))) % 3][0] +
                            robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0)
            point_1.append((robot[self.world.other_color][(dist.index(max(dist))) % 3][1] +
                            robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0)
            point_2.append(robot[self.world.other_color][(dist.index(max(dist)) + 2) % 3][0])
            point_2.append(robot[self.world.other_color][(dist.index(max(dist)) + 2) % 3][1])
            angle = self.normalize_angle(math.degrees(math.atan2(point_2[0] - point_1[0], point_2[1] - point_1[1])) + self.triple_angle)
            center_x = (robot[self.world.other_color][(dist.index(max(dist))) % 3][0] + robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0  # add something here
            center_y = (robot[self.world.other_color][(dist.index(max(dist))) % 3][1] + robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0  # add something here

            if math.sqrt((center_x-self.world.enemy1.position[0])**2 + (center_y-self.world.enemy1.position[1])**2) > 50 or len(robot[self.world.team_color]) == 1:
                self.save_robot((center_x, center_y), angle, 0)
                self.venus = True
                # self.venus_trip = True
            else:
                angle = math.degrees(math.atan2(self.world.venus.orientation[0], self.world.venus.orientation[1]))
                self.save_robot((self.world.venus.position[0], self.world.venus.position[1]), angle, 0)
                self.venus = True
        elif len(robot[self.world.team_color]) == 1 and abs(robot[self.world.team_color][0][0]-self.world.venus.position[0]) < 10 and abs(robot[self.world.team_color][0][1]-self.world.venus.position[1]) < 10:
            angle = math.degrees(math.atan2(self.world.venus.orientation[0], self.world.venus.orientation[1]))
            self.save_robot((robot[self.world.team_color][0][0], robot[self.world.team_color][0][1]), angle, 0)
            self.venus = True
        else:
            angle = math.degrees(math.atan2(self.world.venus.orientation[0], self.world.venus.orientation[1]))
            self.save_robot((self.world.venus.position[0], self.world.venus.position[1]), angle, 0)
            self.venus = True

            # Team mate
            ####################################################################################################################

    def findFriend(self, robot):
        if len(robot[self.world.our_color]) == 1 and len(robot[self.world.team_color]) == 1 and abs(robot[self.world.team_color][0][0]-self.world.venus.position[0]) > 10 and abs(robot[self.world.team_color][0][1]-self.world.venus.position[1]) > 10:
            if math.sqrt((robot[self.world.team_color][0][0]-self.world.venus.position[0])**2 + (robot[self.world.team_color][0][1]-self.world.venus.position[1])**2) > 50:
                angle = self.normalize_angle(math.degrees(math.atan2(robot[self.world.our_color][0][0] - robot[self.world.team_color][0][0],
                                            robot[self.world.our_color][0][1] - robot[self.world.team_color][0][1])) + self.single_angle)
                self.save_robot((robot[self.world.team_color][0][0], robot[self.world.team_color][0][1]), angle, 1)
                self.friend = True
            else:
                angle = math.degrees(math.atan2(self.world.friend.orientation[0], self.world.friend.orientation[1]))
                self.save_robot((self.world.friend.position[0], self.world.friend.position[1]), angle, 1)
                self.friend = True
        elif len(robot[self.world.our_color]) == 3:
            dist = []
            point_1 = []
            point_2 = []
            dist.append(sqrt((robot[self.world.our_color][0][0] - robot[self.world.our_color][1][0]) ** 2 + (
                robot[self.world.our_color][0][1] - robot[self.world.our_color][1][1]) ** 2))

            dist.append(sqrt((robot[self.world.our_color][1][0] - robot[self.world.our_color][2][0]) ** 2 + (
                robot[self.world.our_color][1][1] - robot[self.world.our_color][2][1]) ** 2))

            dist.append(sqrt((robot[self.world.our_color][2][0] - robot[self.world.our_color][0][0]) ** 2 + (
                robot[self.world.our_color][2][1] - robot[self.world.our_color][0][1]) ** 2))
            point_1.append((robot[self.world.our_color][(dist.index(max(dist))) % 3][0] +
                            robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0)
            point_1.append((robot[self.world.our_color][(dist.index(max(dist))) % 3][1] +
                            robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0)
            point_2.append(robot[self.world.our_color][(dist.index(max(dist)) + 2) % 3][0])
            point_2.append(robot[self.world.our_color][(dist.index(max(dist)) + 2) % 3][1])
            angle = self.normalize_angle(math.degrees(math.atan2(point_2[0] - point_1[0], point_2[1] - point_1[1])) + self.triple_angle)
            center_x = (robot[self.world.our_color][(dist.index(max(dist))) % 3][0] +
                           robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0  # add something here
            center_y = (robot[self.world.our_color][(dist.index(max(dist))) % 3][1] +
                           robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0  # add something here
            if math.sqrt((center_x-self.world.enemy2.position[0])**2 + (center_y-self.world.enemy2.position[1])**2) > 50 or len(robot[self.world.team_color]) == 1:
                self.save_robot((center_x, center_y), angle, 1)
                self.friend = True
                # self.friend_trip = True
            else:
                angle = math.degrees(math.atan2(self.world.friend.orientation[0], self.world.friend.orientation[1]))
                self.save_robot((self.world.friend.position[0], self.world.friend.position[1]), angle, 1)
                self.friend = True
        elif len(robot[self.world.team_color]) == 1 and abs(robot[self.world.team_color][0][0]-self.world.friend.position[0]) < 10 and abs(robot[self.world.team_color][0][1]-self.world.friend.position[1]) < 10:
            angle = math.degrees(math.atan2(self.world.friend.orientation[0], self.world.friend.orientation[1]))
            self.save_robot((robot[self.world.team_color][0][0], robot[self.world.team_color][0][1]), angle, 1)
            self.friend = True
        else:
            angle = math.degrees(math.atan2(self.world.friend.orientation[0], self.world.friend.orientation[1]))
            self.save_robot((self.world.friend.position[0], self.world.friend.position[1]), angle, 1)
            self.friend = True

            # Enemy 1
            ######################################################################################################################

    def findEnemy1(self, robot):
        if len(robot[self.world.our_color]) == 1 and len(robot[self.world.enemy_color]) == 1 and abs(robot[self.world.enemy_color][0][0]-self.world.enemy2.position[0]) > 10 and abs(robot[self.world.enemy_color][0][1]-self.world.enemy2.position[1]) > 10:
            if math.sqrt((robot[self.world.enemy_color][0][0]-self.world.enemy2.position[0])**2 + (robot[self.world.enemy_color][0][1]-self.world.enemy2.position[1])**2) > 50:
                angle = self.normalize_angle(math.degrees(math.atan2(robot[self.world.our_color][0][0] - robot[self.world.enemy_color][0][0],
                                            robot[self.world.our_color][0][1] - robot[self.world.enemy_color][0][1])) + self.single_angle)
                self.save_robot((robot[self.world.enemy_color][0][0], robot[self.world.enemy_color][0][1]), angle, 2)
                self.enemy1 = True
            else:
                angle = math.degrees(math.atan2(self.world.enemy1.orientation[0], self.world.enemy1.orientation[1]))
                self.save_robot((self.world.enemy1.position[0], self.world.enemy1.position[1]), angle, 2)
                self.enemy1 = True
        elif len(robot[self.world.other_color]) == 3:
            dist = []
            point_1 = []
            point_2 = []
            dist.append(sqrt(
                (robot[self.world.other_color][0][0] - robot[self.world.other_color][1][0]) ** 2 + (robot[self.world.other_color][0][1] - robot[self.world.other_color][1][1]) ** 2))

            dist.append(sqrt(
                (robot[self.world.other_color][1][0] - robot[self.world.other_color][2][0]) ** 2 + (robot[self.world.other_color][1][1] - robot[self.world.other_color][2][1]) ** 2))

            dist.append(sqrt(
                (robot[self.world.other_color][2][0] - robot[self.world.other_color][0][0]) ** 2 + (robot[self.world.other_color][2][1] - robot[self.world.other_color][0][1]) ** 2))

            point_1.append((robot[self.world.other_color][(dist.index(max(dist))) % 3][0] +
                            robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0)
            point_1.append((robot[self.world.other_color][(dist.index(max(dist))) % 3][1] +
                            robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0)
            point_2.append(robot[self.world.other_color][(dist.index(max(dist)) + 2) % 3][0])
            point_2.append(robot[self.world.other_color][(dist.index(max(dist)) + 2) % 3][1])
            angle = self.normalize_angle(math.degrees(math.atan2(point_2[0] - point_1[0], point_2[1] - point_1[1])) + self.triple_angle)
            center_x = (robot[self.world.other_color][(dist.index(max(dist))) % 3][0] + robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][
                0]) / 2.0  # add something here
            center_y = (robot[self.world.other_color][(dist.index(max(dist))) % 3][1] + robot[self.world.other_color][(dist.index(max(dist)) + 1) % 3][
                1]) / 2.0  # add something here
            if math.sqrt((center_x-self.world.venus.position[0])**2 + (center_y-self.world.venus.position[1])**2) > 50 or len(robot[self.world.enemy_color]) == 1:
                self.save_robot((center_x, center_y), angle, 2)
                self.enemy1 = True
                # self.enemy1_trip = True
            else:
                angle = math.degrees(math.atan2(self.world.enemy1.orientation[0], self.world.enemy1.orientation[1]))
                self.save_robot((self.world.enemy1.position[0], self.world.enemy1.position[1]), angle, 2)
                self.enemy1 = True
        elif len(robot[self.world.enemy_color]) == 1 and abs(robot[self.world.enemy_color][0][0]-self.world.enemy1.position[0]) < 10 and abs(robot[self.world.enemy_color][0][1]-self.world.enemy1.position[1]) < 10:
            angle = math.degrees(math.atan2(self.world.enemy1.orientation[0], self.world.enemy1.orientation[1]))
            self.save_robot((robot[self.world.enemy_color][0][0], robot[self.world.enemy_color][0][1]), angle, 2)
            self.enemy1 = True
        else:
            angle = math.degrees(math.atan2(self.world.enemy1.orientation[0], self.world.enemy1.orientation[1]))
            self.save_robot((self.world.enemy1.position[0], self.world.enemy1.position[1]), angle, 2)
            self.enemy1 = True

            # enemy 2
            #######################################################################################################################

    def findEnemy2(self, robot):
        if len(robot[self.world.our_color]) == 1 and len(robot[self.world.enemy_color]) == 1:
            if math.sqrt((robot[self.world.enemy_color][0][0]-self.world.enemy1.position[0])**2 + (robot[self.world.enemy_color][0][1]-self.world.enemy1.position[1])**2) > 50:
                angle = self.normalize_angle(math.degrees(math.atan2(robot[self.world.our_color][0][0] - robot[self.world.enemy_color][0][0],
                                            robot[self.world.our_color][0][1] - robot[self.world.enemy_color][0][1])) + self.single_angle)
                self.save_robot((robot[self.world.enemy_color][0][0], robot[self.world.enemy_color][0][1]), angle, 3)
                self.enemy2 = True
            else:
                angle = math.degrees(math.atan2(self.world.enemy2.orientation[0], self.world.enemy2.orientation[1]))
                self.save_robot((self.world.enemy2.position[0], self.world.enemy2.position[1]), angle, 3)
                self.enemy2 = True
        elif len(robot[self.world.our_color]) == 3:
            dist = []
            point_1 = []
            point_2 = []
            dist.append(sqrt((robot[self.world.our_color][0][0] - robot[self.world.our_color][1][0]) ** 2 + (
                robot[self.world.our_color][0][1] - robot[self.world.our_color][1][1]) ** 2))

            dist.append(sqrt((robot[self.world.our_color][1][0] - robot[self.world.our_color][2][0]) ** 2 + (
                robot[self.world.our_color][1][1] - robot[self.world.our_color][2][1]) ** 2))

            dist.append(sqrt((robot[self.world.our_color][2][0] - robot[self.world.our_color][0][0]) ** 2 + (
                robot[self.world.our_color][2][1] - robot[self.world.our_color][0][1]) ** 2))

            point_1.append((robot[self.world.our_color][(dist.index(max(dist))) % 3][0] +
                            robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][0]) / 2.0)
            point_1.append((robot[self.world.our_color][(dist.index(max(dist))) % 3][1] +
                            robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][1]) / 2.0)
            point_2.append(robot[self.world.our_color][(dist.index(max(dist)) + 2) % 3][0])
            point_2.append(robot[self.world.our_color][(dist.index(max(dist)) + 2) % 3][1])
            angle = self.normalize_angle(math.degrees(math.atan2(point_2[0] - point_1[0], point_2[1] - point_1[1])) + self.triple_angle)
            center_x = (
                           robot[self.world.our_color][(dist.index(max(dist))) % 3][0] +
                           robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][
                               0]) / 2.0  # add something here
            center_y = (
                           robot[self.world.our_color][(dist.index(max(dist))) % 3][1] +
                           robot[self.world.our_color][(dist.index(max(dist)) + 1) % 3][
                               1]) / 2.0  # add something here
            if math.sqrt((center_x-self.world.friend.position[0])**2 + (center_y-self.world.friend.position[1])**2) > 50 or len(robot[self.world.enemy_color]) == 1:
                self.save_robot((center_x, center_y), angle, 3)
                self.enemy2 = True
                # self.enemy2_trip = True
            else:
                angle = math.degrees(math.atan2(self.world.enemy2.orientation[0], self.world.enemy2.orientation[1]))
                self.save_robot((self.world.enemy2.position[0], self.world.enemy2.position[1]), angle, 3)
                self.enemy2 = True
        elif len(robot[self.world.enemy_color]) == 1 and abs(robot[self.world.enemy_color][0][0]-self.world.enemy2.position[0]) < 10 and abs(robot[self.world.enemy_color][0][1]-self.world.enemy2.position[1]) < 10:
            angle = math.degrees(math.atan2(self.world.enemy2.orientation[0], self.world.enemy2.orientation[1]))
            self.save_robot((robot[self.world.enemy_color][0][0], robot[self.world.enemy_color][0][1]), angle, 3)
            self.enemy2 = True
        else:
            angle = math.degrees(math.atan2(self.world.enemy2.orientation[0], self.world.enemy2.orientation[1]))
            self.save_robot((self.world.enemy2.position[0], self.world.enemy2.position[1]), angle, 3)
            self.enemy2 = True

    def save_robot(self, position, orientation, robot_id):
        robot = [self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2][robot_id]
        robot.position[0] = int(position[0])
        robot.position[1] = int(position[1])
        rad = math.radians(orientation)
        robot.orientation[0] = sin(rad)
        robot.orientation[1] = cos(rad)

    def findslope(self, point1, point2):
        numerator = point1[1] - point2[1]
        denominator = point1[0] - point2[0]  # sometimes it's not a point?? like [292. 292.]
        ans = (numerator, denominator)
        return ans

    def snapShot(self, capture):
        status, frame = self.capture.read()
        h, w = frame.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 0, (w, h))

        # These are the actual values needed to undistort:
        dst = cv2.undistort(frame, self.mtx, self.dist, None, newcameramtx)

        # crop the image
        x, y, w, h = roi
        dst = dst[y:y + h, x:x + w]

        # Apply perspective transformation
        pts2 = np.float32([[0, 0], [639, 0], [639, 479], [0, 479]])
        M = cv2.getPerspectiveTransform(self.pts1, pts2)
        imgOriginal = cv2.warpPerspective(dst, M, (639, 479))

        imgOriginal = cv2.GaussianBlur(imgOriginal, (3, 3), 2)
        cv2.imwrite('vision/calibrate.png', imgOriginal)

    def on_mouse(self, event, x, y, flag, param):
        if event == cv2.EVENT_LBUTTONDBLCLK:
            pixelClicked = self.imageHSV[y][x]
            surroundingPixels = [self.imageHSV[y-1][x-1], self.imageHSV[y-1][x], self.imageHSV[y-1][x+1], self.imageHSV[y]
            [x+1], self.imageHSV[y+1][x+1], self.imageHSV[y+1][x], self.imageHSV[y+1][x-1], self.imageHSV[y][x-1], self.imageHSV[y][x]]
            hueList = []
            satList = []
            valueList = []
            for i in range(0, 9):
                hueList.append(surroundingPixels[i][0])
                satList.append(surroundingPixels[i][1])
                valueList.append(surroundingPixels[i][2])

            medianHSV = [np.median(hueList), np.median(satList), np.median(valueList)]
            print medianHSV
            if self.colorList[self.counter] == 'red':
                if 0 < medianHSV[0] < 5 or 175 < medianHSV[0] < 180:
                    self.colorMedians.append(medianHSV)
            else:
                if HUES[self.colorList[self.counter]][0] < medianHSV[0] < HUES[self.colorList[self.counter]][1]:
                    self.colorMedians.append(medianHSV)

    def show(self, filename):
        self.image = cv2.imread(filename)
        self.imageHSV = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        cv2.imshow('calibrate', self.image)
        k = 1
        while k != 27:  # Esc
            k = cv2.waitKey(100) & 0xFF
            cv2.imshow('calibrate', self.image)
            if k == 113:  # q
                hues = []
                sats = []
                values = []
                if len(self.colorMedians) > 0:   # We have clicked
                    for i in range(0, len(self.colorMedians)):
                        hues.append(self.colorMedians[i][0])
                        sats.append(self.colorMedians[i][1])
                        values.append(self.colorMedians[i][2])
                    if self.colorList[self.counter] == 'red':
                        if max(hues) <= 15:
                            hsvThres = [((min(hues), min(sats), min(values)), (max(hues), 255, 255)), self.color_ranges['red'][1]]
                        elif min(hues) >= 165:
                            hsvThres = [self.color_ranges['red'][0], ((min(hues), min(sats), min(values)), (max(hues), 255, 255))]
                        else:
                            huesLower = []
                            huesUpper = []
                            satsLower = []
                            satsUpper = []
                            valuesLower = []
                            valuesUpper = []
                            try:
                                for i in range(0, len(hues)):
                                    if hues[i] <= 100:
                                        huesLower.append(hues[i])
                                        satsLower.append(sats[i])
                                        valuesLower.append(values[i])
                                    else:
                                        huesUpper.append(hues[i])
                                        satsUpper.append(sats[i])
                                        valuesUpper.append(values[i])
                                lowerRange = ((min(huesLower), min(satsLower), min(valuesLower)), (max(huesLower), 255, 255))
                                upperRange = ((min(huesUpper), min(satsUpper), min(valuesUpper)), (max(huesUpper), 255, 255))
                                hsvThres = [lowerRange, upperRange]
                            except ValueError:
                                pass
                    else:
                        hsvThres = [((min(hues), min(sats), min(values)), (max(hues), 255, 255))]

                    self.color_ranges[self.colorList[self.counter]] = hsvThres

                self.counter += 1
                del self.colorMedians[:]
                if self.counter == 5:
                    if self.world.room_num == 1:
                        targetFile = open("vision/color1.txt", "w")
                    else:
                        targetFile = open("vision/color0.txt", "w")
                    targetFile.write(str(self.color_ranges))
                    targetFile.close()
                    break

            cv2.circle(self.image, (20, 20), 5, COLORS[self.colorList[self.counter]], 10)
            if self.counter > 4:
                if self.world.room_num == 1:
                    targetFile = open("vision/color1.txt", "w")
                else:
                    targetFile = open("vision/color0.txt", "w")
                targetFile.write(str(self.color_ranges))
                targetFile.close()

    def normalize_angle(self, angle):
        if angle > 180:
            return float(angle-360)
        elif angle < -180:
            return float(angle+360)
        else:
            return angle


