import cv2
from pylab import *
from scipy.ndimage import measurements
from scipy.spatial import distance

from strategy.world import NO_VALUE

VISION_ROOT = 'vision/'

COLOR_RANGES = {
    'red': ((0, 170, 130), (8, 255, 255)),
    'blue': ((78, 100, 110), (102, 230, 230)),
    'yellow': ((30, 150, 150), (37, 255, 255)),
    'pink': ((149, 130, 60), (175, 255, 255)),
    'green': ((47, 130, 200), (59, 255, 255)),
}

COLOR_AVERAGES = np.array(COLOR_RANGES.values()).mean(1)


MAX_COLOR_COUNTS = {
    'red': 1,
    'blue': 10,
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

MIN_COLOR_AREA = {
    'red': 6000.0,
    'blue': 1000.0,
    'yellow': 2000.0,
    'pink': 6000.0,
    'green': 2000.0,
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
        self.image = None
        self.trajectory_list = [(0, 0)] * 6
        if self.world.room_num == 1:
            self.mtx = np.loadtxt(VISION_ROOT + "mtx1.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist1.txt")
            self.pts1 = np.float32([[33, 12], [609, 16], [607, 475], [22, 462]])
            # self.pts1 = np.float32([[10, 2], [634, 37], [596, 478], [6, 456]])
        elif self.world.room_num == 0:
            self.mtx = np.loadtxt(VISION_ROOT + "mtx2.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist2.txt")
            self.pts1 = np.float32([[33, 12], [609, 16], [607, 475], [22, 462]])
            # self.pts1 = np.float32([[7, 5], [607, 4], [593, 451], [17, 450]])
        else:
            print("invalid room id")

        self.capture = cv2.VideoCapture(0)

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 440)

        self.capture.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        self.capture.set(cv2.CAP_PROP_CONTRAST, 0.5)
        self.capture.set(cv2.CAP_PROP_SATURATION, 0.5)
        self.capture.set(cv2.CAP_PROP_HUE, 0.5)

        # Only need to create windows at the beginning
        cv2.namedWindow("Mask")
        cv2.namedWindow("Room")

        while self.pressed_key != 27:
            self.frame()

        cv2.destroyAllWindows()

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

        self.image = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2HSV)

        mask = None
        for begin, end in COLOR_RANGES.itervalues():
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

        circles = {color_name: [] for color_name in COLOR_RANGES}
        for center_index in center_indices:
            center = centers[center_index]
            color = None
            for color_name, (begin, end) in COLOR_RANGES.iteritems():
                if cv2.inRange(np.array([[self.image[center]]]), begin, end):
                    color = color_name
            #if color is None:
            #    color = COLOR_RANGES.keys()[np.linalg.norm(COLOR_AVERAGES - self.image[center], axis=1).argmin()]
            if color is not None and len(circles[color]) < MAX_COLOR_COUNTS[color] and areas[center_index] > MIN_COLOR_AREA[color]:
                circles[color].append((center[1], center[0]))

        # draws circles spotted
        for color_name, positions in circles.iteritems():
            for x, y in positions:
                cv2.circle(imgOriginal, (int(x), int(y)), 8, COLORS[color_name], 1)

            # save balls trajectory
            if color_name == 'red':
                for x, y in positions:
                    self.trajectory_list.append((x, y))
                    self.trajectory_list.pop(0)

        # draw balls trajectory
        delta_x = self.trajectory_list[len(self.trajectory_list) - 1][0] - self.trajectory_list[0][0]
        if abs(delta_x) > 2:
            self.world.ball_moving.value = True
            future_x = self.trajectory_list[len(self.trajectory_list) - 1][0] + 2.0 * delta_x
            m = (self.trajectory_list[len(self.trajectory_list) - 1][1] - self.trajectory_list[0][1]) / float(delta_x)
            future_y = (future_x - self.trajectory_list[0][0]) * m + self.trajectory_list[0][1]
            self.world.future_ball[0] = int(future_x)
            self.world.future_ball[1] = int(future_y)
            cv2.line(imgOriginal, (int(self.trajectory_list[len(self.trajectory_list) - 1][0])
                                   , int(self.trajectory_list[len(self.trajectory_list) - 1][1]))
                     , (int(future_x), int(future_y)), COLORS['red'], 1)
        else:
            self.world.ball_moving.value = False

        self.getRobots(circles)
        self.getBall(circles)

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
    def getBall(self, circles):
        if len(circles['red']) == 0:
            self.world.ball[0] = NO_VALUE
            self.world.ball[1] = NO_VALUE
        else:
            self.world.ball[0] = int(circles['red'][0][0])
            self.world.ball[1] = int(circles['red'][0][1])

    def getRobots(self, circles):
        greenPoints = circles["green"]
        pinkPoints = circles["pink"]
        bluePoints = circles["blue"]
        yellowPoints = circles["yellow"]
        if greenPoints and pinkPoints:
            greenandpink = np.concatenate((greenPoints, pinkPoints))
        elif not greenPoints and pinkPoints:
            greenandpink = np.array(pinkPoints)
        elif not pinkPoints and pinkPoints:
            greenandpink = np.array(greenPoints)
        else:
            return
        self.detected_robots = [False] * 4
        for ypoint in yellowPoints:
            distances = distance.cdist(greenandpink, [ypoint]).flatten()
            greenandpink_indices = np.argsort(distances)
            if distances[greenandpink_indices[:1]] < 20:
                greenandpink_tuples = [(greenandpink[i], 'green' if i < len(greenPoints) else 'pink') for i in
                                       greenandpink_indices[:4]]
                orientation = self.getorientation(ypoint, greenandpink_tuples)
                rid = self.getid(greenandpink_tuples, 'yellow')
                self.save_robot(ypoint, orientation, rid)
        for bpoint in bluePoints:
            distances = distance.cdist(greenandpink, [bpoint]).flatten()
            greenandpink_indices = np.argsort(distances)
            if distances[greenandpink_indices[:1]] < 20:
                greenandpink_tuples = [(greenandpink[i], 'green' if i < len(greenPoints) else 'pink') for i in
                                       greenandpink_indices[:4]]
                orientation = self.getorientation(bpoint, greenandpink_tuples)
                rid = self.getid(greenandpink_tuples, 'blue')
                self.save_robot(bpoint, orientation, rid)
        for robot_id, is_detected in enumerate(self.detected_robots):
            if not is_detected:
                robot = [self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2][robot_id]
                robot.position[0] = NO_VALUE
                robot.position[1] = NO_VALUE
                robot.orientation.value = NO_VALUE

    def save_robot(self, position, orientation, robot_id):
        self.detected_robots[robot_id] = True
        robot = [self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2][robot_id]
        robot.position[0] = int(position[0])
        robot.position[1] = int(position[1])
        rad = math.radians(orientation)
        robot.orientation[0] = sin(rad)
        robot.orientation[1] = cos(rad)

    def getid(self, greenandpink, tcolor):
        if tcolor == self.world.team_color:
            greencount = 0
            pinkcount = 0
            for gnppoint in greenandpink:
                if gnppoint[1] == 'green':
                    greencount = greencount + 1
                else:
                    pinkcount = pinkcount + 1
            if greencount == 3:
                return 1
            else:
                return 0
        else:
            greencount = 0
            pinkcount = 0
            for gnppoint in greenandpink:
                if gnppoint[1] == 'green':
                    greencount = greencount + 1
                else:
                    pinkcount = pinkcount + 1
            if greencount == 3:
                return 3
            else:
                return 2
                # TODO:

    def getorientation(self, cpoint, greenandpink):
        greenList = []
        pinkList = []
        savedi = 0
        savedj = 0
        midpointxcoord = 0
        midpointycoord = 0
        mid2x = 0
        mid2y = 0
        centerPointOfInterest2 = cpoint
        for (coordinate, color) in greenandpink:
            if (color == "green"):
                greenList.append(coordinate)
            if (color == "pink"):
                pinkList.append(coordinate)
        if (len(greenList)) == 3:
            isolatedPoint = []
            for (coordinate, color) in greenandpink:
                if (color == "pink"):
                    isolatedPoint.append(coordinate)
            if isolatedPoint:
                distances = distance.cdist(isolatedPoint, greenList)
                smallestdist = distances[0][0]
                for i in range(len(distances)):
                    for j in range(len(distances[i])):
                        if (distances[i][j] != 0 and distances[i][j] < smallestdist):
                            smallestdist = distances[i][j]
                            savedi = i
                            savedj = j
                # del greenList[savedj]
                mid2x = (pinkList[0][0] + greenList[savedj][0]) / 2.0
                mid2y = (pinkList[0][1] + greenList[savedj][1]) / 2.0
                del greenList[savedj]
                midpointxcoord = (greenList[0][0] + greenList[1][0]) / 2.0
                midpointycoord = (greenList[0][1] + greenList[1][1]) / 2.0
                centerPointOfInterest2 = (mid2x, mid2y)

        elif (len(pinkList)) == 3:
            isolatedPoint = []
            for (coordinate, color) in greenandpink:
                if (color == "green"):
                    isolatedPoint.append(coordinate)
            if isolatedPoint:
                distances = distance.cdist(isolatedPoint, pinkList)
                smallestdist = distances[0][0]
                for i in range(len(distances)):
                    for j in range(len(distances[i])):
                        if (distances[i][j] != 0 and distances[i][j] < smallestdist):
                            smallestdist = distances[i][j]
                            savedi = i
                            savedj = j
                mid2x = (greenList[0][0] + pinkList[savedj][0]) / 2.0
                mid2y = (greenList[0][1] + pinkList[savedj][1]) / 2.0
                del pinkList[savedj]
                midpointxcoord = (pinkList[0][0] + pinkList[1][0]) / 2.0
                midpointycoord = (pinkList[0][1] + pinkList[1][1]) / 2.0
                # centerPointOfInterest2 = cpoint
                # print "center point interest ", (midpointxcoord, midpointycoord)
                # print "center pioint ", cpoint

        centerPointOfInterest = (midpointxcoord, midpointycoord)
        # slopeHorizontalLine = 0.0
        centerPointOfInterest2 = (mid2x, mid2y)
        if (centerPointOfInterest[0] == cpoint[0]):
            return 270
        else:
            slopeDirection = self.findslope(centerPointOfInterest, centerPointOfInterest2)
        # print "slopeDirection " , slopeDirection
        (numerator, denominator) = slopeDirection
        # print numerator
        angle = math.atan2(denominator, numerator)
        angle = math.degrees(angle)
        # if (angle &lt; 0):
        #    return -angle
        # elif (angle &gt; 0):
        #    return 180 + (180-angle)
        return angle

    def findslope(self, point1, point2):
        numerator = point1[1] - point2[1]
        denominator = point1[0] - point2[0]  # sometimes it's not a point?? like [292. 292.]
        ans = (numerator, denominator)
        return ans
