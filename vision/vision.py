import cv2
from pylab import *
from scipy.ndimage import measurements
from scipy.spatial import distance

from strategy.world import NO_VALUE

VISION_ROOT = 'vision/'
KNOWN_ANGLE = 225
COLOR_RANGES = {
    'red': [((0, 170, 130), (8, 255, 255)), ((175, 170, 130), (180, 255, 255))],
    'blue': [((83, 110, 150), (99, 230, 230))],
    'yellow': [((30, 150, 150), (37, 255, 255))],
    'pink': [((149, 130, 60), (175, 255, 255))],
    'green': [((50, 130, 200), (60, 255, 255))],
}

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
    'red': 2000.0,
    'blue': 3000.0,
    'yellow': 2000.0,
    'pink': 2000.0,
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
        self.trajectory_list = [(0, 0)]*5
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
        self.capture.set(cv2.CAP_PROP_BRIGHTNESS, .5)
        self.capture.set(cv2.CAP_PROP_CONTRAST, .5)
        self.capture.set(cv2.CAP_PROP_SATURATION, .5)
        self.capture.set(cv2.CAP_PROP_HUE, .5)

        while self.pressed_key != 27:
            self.frame()
        cv2.destroyAllWindows()
        return

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

        circles = {}
        for color_name, color_ranges in COLOR_RANGES.iteritems():
            circles[color_name] = self.TrackCircle(color_name, color_ranges, imgOriginal)

        # draws circles spotted
        if self.debug:
            print '----------'
        for color_name, positions in circles.iteritems():
            if self.debug:
                print 'Detected ' + color_name + ' : ' + str(len(positions))
            for x, y in positions:
                cv2.circle(imgOriginal, (int(x), int(y)), 8, COLORS[color_name], 1)

            # save balls trajectory
            if color_name == 'red':
                for x, y in positions:
                    self.trajectory_list.append((x, y))
                    self.trajectory_list.pop(0)

        # draw balls trajectory
        delta_x = x-self.trajectory_list[0][0]
        if abs(delta_x) > 2:
            future_x = x + 100*delta_x
            m = (y-self.trajectory_list[0][1])/(x-self.trajectory_list[0][0])
            future_y = (future_x-self.trajectory_list[0][0])*m + self.trajectory_list[0][1]
            cv2.line(imgOriginal, (int(x), int(y)), (int(future_x), int(future_y)), COLORS['red'], 1)

        self.getRobots(circles)
        self.getBall(circles)

        for robot_id, robot in enumerate([self.world.venus, self.world.friend, self.world.enemy1, self.world.enemy2]):
            if robot.position[0] != NO_VALUE:
                cv2.rectangle(imgOriginal, (robot.position[0] - 20, robot.position[1] - 20),
                              (robot.position[0] + 20, robot.position[1] + 20), (0, 0, 0))
                cv2.line(imgOriginal, (robot.position[0], robot.position[1]),
                         (int(robot.position[0] + robot.orientation[0] * 50.0),
                          int(robot.position[1] + robot.orientation[1] * 50.0)),
                         (0, 0, 0))
                cv2.putText(imgOriginal, str(robot_id), (robot.position[0], robot.position[1]),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 0))

        cv2.namedWindow("Room", cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Room', imgOriginal)
        self.pressed_key = cv2.waitKey(2) & 0xFF

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
            print("There are no robots!")
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
                centerPointOfInterest2 = cpoint
                # print "center point interest ", (midpointxcoord, midpointycoord)
                # print "center pioint ", cpoint

        centerPointOfInterest = (midpointxcoord, midpointycoord)
        # slopeHorizontalLine = 0.0
        # centerPointOfInterest2 = (mid2x,mid2y)
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

    def TrackCircle(self, color_name, color_ranges, imgOriginal):
        positions = []

        # Image Masking
        imgHSV = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2HSV)

        if len(color_ranges) == 2:
            imgThreshLow = cv2.inRange(imgHSV, color_ranges[0][0], color_ranges[0][1])
            imgThreshHigh = cv2.inRange(imgHSV, color_ranges[1][0], color_ranges[1][1])
            imgThresh = cv2.add(imgThreshLow, imgThreshHigh)
        else:
            imgThresh = cv2.inRange(imgHSV, color_ranges[0][0], color_ranges[0][1])

        imgThresh = cv2.GaussianBlur(imgThresh, (3, 3), 2)  # blur

        # imgThresh = cv2.dilate(imgThresh, np.ones((5, 5), np.uint8))  # close image (dilate, then erode)
        # imgThresh = cv2.erode(imgThresh, np.ones((5, 5), np.uint8))  # closing "closes" (i.e. fills in) foreground gaps

        cv2.namedWindow(color_name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(color_name, imgThresh)

        # intRows, intColumns = imgThresh.shape

        z = imgThresh

        # Label the clusters
        lw, num = measurements.label(z)

        # Calculate areas
        area = measurements.sum(z, lw, xrange(1, num + 1))

        relevant_indices = area.argsort()[-MAX_COLOR_COUNTS[color_name]:]

        for index in relevant_indices:
            if area[index] > MIN_COLOR_AREA[color_name]:
                y, x = measurements.center_of_mass(z, lw, index=index + 1)
                positions.append((x, y))

        '''
        cluster = 1
        while cluster < len(area):
            y, x = measurements.center_of_mass(z, lw, index=cluster)

            # if self.debug:
            #    print obj.label + " " + str(int(pos[1])) +","+ str(int(pos[0]))

            positions.append((x, y))

            # cv2.circle(imgOriginal, (x,y), 3, (0, 255, 0), cv2.FILLED)

            # cv2.line(imgOriginal, (x,y),(0,0), (0, 255, 0), 2) # Trajectory drawn


            cluster = cluster + 1
            # area = np.delete(area, i)
        '''

        return positions
