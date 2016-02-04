import numpy as np
import cv2
from pylab import*
from scipy.ndimage import measurements
from scipy.spatial import distance


VISION_ROOT = 'vision/'
KNOWN_ANGLE = 225 
COLOR_RANGES = {
    'red':    [((0, 170, 170), (10, 255, 255)), ((170, 170, 170), (180, 255, 255))],
    'blue':   [((110, 130, 130), (120, 255, 255))],
    'yellow': [((27, 73, 240), (30, 255, 255))],
    'green':  [((50, 65, 230), (65, 255, 255))],
    'pink':  [((150, 45,180), (160, 255, 255))]
	
}

VENUS = 0
TEAMMATE = 1
ENEMY_1 = 2
ENEMY_2 = 3


class Ball:
    def __init__(self, pos):
        self.x = pos[0]
        self.y = pos[1]
    def printball(self):
	print ('BALL POSITION ' + str((self.x,self.y)))
	print('')


class Robot:
    def __init__(self, pos , orientation , rid):
      	self.pos = pos
	self.orientation = orientation
	self.rid= rid
    def printrobot(self):
	print('ROBOT ' + str(self.rid))	
	print('POSITION ' + str(self.pos))
	print('ORIENTATION ' + str(self.orientation))
	print('') 


class Room():
    def __init__(self,r_id,team_color, our_color, debug=False):
        self.debug = debug
        self.team_color = team_color
        self.our_color = our_color
        self.room_id=r_id
        if(self.room_id==1):
            self.mtx = np.loadtxt(VISION_ROOT + "mtx1.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist1.txt")
            self.pts1 = np.float32([[10, 2], [634, 37], [596, 478], [6, 456]])
        elif(self.room_id==0):
            self.mtx = np.loadtxt(VISION_ROOT + "mtx2.txt")
            self.dist = np.loadtxt(VISION_ROOT + "dist2.txt")
            self.pts1 = np.float32([[7, 5], [607, 4], [593, 451], [17, 450]])
        else:
            print("invalid room id")

        self.capture = cv2.VideoCapture(0)

    def vision(self):        
        while cv2.waitKey(1) != 27:   #patrick you mad man
            self.frame()
        cv2.destroyAllWindows()
        return


    def frame(self):
        status, frame = self.capture.read()
        h,  w = frame.shape[:2]    
        newcameramtx, roi=cv2.getOptimalNewCameraMatrix(self.mtx,self.dist,(w,h),0,(w,h))

        #These are the actual values needed to undistort:
        dst = cv2.undistort(frame, self.mtx, self.dist, None, newcameramtx)

        # crop the image
        x,y,w,h = roi
        dst = dst[y:y+h, x:x+w]

        # Apply perspective transformation
        pts2 = np.float32([[0,0],[639,0],[639,479],[0,479]])
        M = cv2.getPerspectiveTransform(self.pts1,pts2)
        imgOriginal = cv2.warpPerspective(dst,M,(639,479))
        
        circles = {}
        for color_name, color_ranges in COLOR_RANGES.iteritems():
            circles[color_name] = self.TrackCircle(color_ranges, imgOriginal)
            
        for color_name, positions in circles.iteritems():
            for x, y in positions:
                cv2.circle(imgOriginal, (int(x), int(y)), 6, (0, 0, 255), 3)
        
        robots = self.getRobots(circles)
	ball = self.getBall(circles)
	ball.printball()
	for robot in robots:
	    robot.printrobot()
	
        
        if self.debug:
            cv2.namedWindow("Room", cv2.WINDOW_AUTOSIZE) 
            cv2.imshow('Room',imgOriginal)
            cv2.waitKey(0)

    def getBall(self,circles):
	if len(circles['red']) == 0:
		return Ball((0,0))	
	pos= circles['red'][0]
	return Ball(pos)

    def getRobots(self,circles):
	robots= []
	greenPoints = circles["green"]
	pinkPoints = circles["pink"]
	bluePoints = circles["blue"]
	yellowPoints = circles["yellow"]
	greenandpink=[]
	for i in range(0, len(greenPoints)):
	    greenandpink.append((greenPoints[i],'green'))
	for i in range(0, len(pinkPoints)):
	    greenandpink.append((pinkPoints[i],'pink'))
	for ypoint in yellowPoints:
	    greenandpink.sort(key = lambda p: sqrt((ypoint[0] - p[0][0])**2 + (ypoint[1] - p[0][1])**2))
	    orientation = self.getorientation(ypoint,greenandpink[:4])
	    rid = self.getid(ypoint,greenandpink[:4],'yellow')
	    robots.append(Robot(ypoint,orientation,rid))
	for bpoint in bluePoints:
	    greenandpink.sort(key = lambda p: sqrt((bpoint[0] - p[0][0])**2 + (bpoint[1] - p[0][1])**2))
	    orientation = self.getorientation(bpoint,greenandpink[:4])
	    rid = self.getid(bpoint,greenandpink[:4],'blue')
	    robots.append(Robot(bpoint,orientation,rid))    
	return robots

    def getid(self,cpoint,greenandpink,tcolor):
        if tcolor == self.team_color:
	    greencount = 0
	    pinkcount = 0
	    for gnppoint in greenandpink:
		if gnppoint[1] == 'green' :
		    greencount = greencount+1
		else:
		    pinkcount=pinkcount+1
	    if greencount == 3:
		return 1
	    else:
		return 0
	else:
	    greencount = 0
	    pinkcount = 0
	    for gnppoint in greenandpink:
		if gnppoint[1] == 'green' :
		    greencount = greencount+1
		else:
		    pinkcount=pinkcount+1
	    if greencount == 3:
		return 3
	    else:
		return 2
#TODO:
    def getorientation(self, cpoint, greenandpink):
	return 0 
		
#####

    def TrackCircle(self, color_ranges, imgOriginal):
        global l
        l = []
        
        positions = []
        
        #Image Masking        
        imgHSV = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2HSV)

        if len(color_ranges) == 2:
            imgThreshLow = cv2.inRange(imgHSV, color_ranges[0][0], color_ranges[0][1])
            imgThreshHigh = cv2.inRange(imgHSV, color_ranges[1][0], color_ranges[1][1])
            imgThresh = cv2.add(imgThreshLow, imgThreshHigh)
        else:
            imgThresh = cv2.inRange(imgHSV, color_ranges[0][0], color_ranges[0][1])

        imgThresh = cv2.GaussianBlur(imgThresh, (3, 3), 2)                # blur

        imgThresh = cv2.dilate(imgThresh, np.ones((5,5),np.uint8))        # close image (dilate, then erode)
        imgThresh = cv2.erode(imgThresh, np.ones((5,5),np.uint8))         # closing "closes" (i.e. fills in) foreground gaps

        #intRows, intColumns = imgThresh.shape   
     
        z = imgThresh
             
        # Label the clusters
        lw, num = measurements.label(z)
        i = 0        
        while (i < num+1):
            l.append(i)
            i = i+1     

        # Calculate areas
        area = measurements.sum(z, lw, index = l)

        cluster = 1
        while(cluster < len(area)):
            i = area.argmax()
            y, x = measurements.center_of_mass(z, lw, index = cluster)

            #if self.debug:
            #    print obj.label + " " + str(int(pos[1])) +","+ str(int(pos[0]))
            
            positions.append((x, y))
            
            #cv2.circle(imgOriginal, (x,y), 3, (0, 255, 0), cv2.FILLED) 
                
            #cv2.line(imgOriginal, (x,y),(0,0), (0, 255, 0), 2) # Trajectory drawn
            
            
            cluster = cluster + 1
            #area = np.delete(area, i)

        return positions
        
    
