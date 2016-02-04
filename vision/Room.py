import numpy as np
import cv2
from pylab import*
from scipy.ndimage import measurements
from scipy.spatial import distance


VISION_ROOT = 'vision/'
pattern={"yellow","pink"}
COLOR_RANGES = {
    'red':    [((0, 170, 170), (10, 255, 255)), ((170, 170, 170), (180, 255, 255))],
    'blue':   [((110, 130, 130), (120, 255, 255))],
    'yellow': [((27, 73, 240), (30, 255, 255))],
    'green':  [((50, 65, 230), (65, 255, 255))],
    'pink':  [((50, 65, 230), (65, 255, 255))],
}
teamcolors={'red'}
secondarycolors = {'blue'}
VENUS = 0
TEAMMATE = 1
ENEMY_1 = 2
ENEMY_2 = 3


class Ball:
    def __init__(self, circle):
        self.label = circle.label
        self.x = circle.x
        self.y = circle.y


class Robot:
    def __init__(self, circle1, circle2, circle3):
        self.x = (circle1[0] + circle2[0] + circle3[0]) / 3.0
        self.y = (circle1[1] + circle2[1] + circle3[1]) / 3.0
        if circle1[2]==pattern[0] and circle2[2]==circle3[2]==pattern[1]:
            self.id=1
        if circle1[2]==pattern[0] and circle2[2]!=pattern[1]:
            self.id=2
        if circle1[2]!=pattern[0] and circle2[2]==circle3[2]==pattern[1]:
            self.id=3
        if circle1[2]!=pattern[0] and circle2[2]!=pattern[1]:
            self.id=4


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
        c = True
        while c != 27:   #patrick you mad man
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
        
        print circles
        
        robots = []
        
	 # Code to classify green and pink points to a team - either the blue team or the yellow team
	
	'''
	greenPoints = circles["green"]
	pinkPoints = circles["pink"]
	bluePoints = circles["blue"]
	yellowPoints = circles["yellow"]
       
        greenPointDict = {}
	for greenPoint in greenPoints:
                distanceList = []
                bluemin = 10000
                yellowmin = 10000 
		for point in bluePoints:
	        	bluedst = distance.euclidean(greenPoint,point)
                        if (bluedst < bluemin):
                            bluemin = bluedst
                for point in yellowPoints:
	        	yellowdst = distance.euclidean(greenPoint,point)
                        if (yellowdst < yellowmin):
                            yellowmin = yellowdst
                if (bluemin < yellowmin):
                	greenPointDict[greenPoint] = "Blue Team"
                else:
                        greenPointDict[greenPoint] = "Yellow Team"
 
        pinkPointDict = {}
        for pinkPoint in pinkPoints:
                distanceList = []
                bluemin = 10000
                yellowmin = 10000 
		for point in bluePoints:
	        	bluedst = distance.euclidean(greenPoint,point)
                        if (bluedst < bluemin):
                            bluemin = bluedst
                for point in yellowPoints:
	        	yellowdst = distance.euclidean(greenPoint,point)
                        if (yellowdst < yellowmin):
                            yellowmin = yellowdst
                if (bluemin < yellowmin):
                	pinkPointDict[pinkPoint] = "Blue Team"
                else:
                        pinkPointDict[pinkPoint] = "Yellow Team"
	'''
        
        #for color1 in teamcolors:
        #    for color2 in secondarycolors:
        #        distances = distance.cdist(circles[color1], circles[color2], 'euclidean')
        #        distances.sort()
        #        print(distances)
        #        #robots.append(Robot(x, y, VENUS))
        #        a=Robot()
        
        if self.debug:
            cv2.namedWindow("Room", cv2.WINDOW_AUTOSIZE) 
            cv2.imshow('Room',imgOriginal)
            cv2.waitKey(0)
            
            

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
    
############################################################################################################     
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
############################################################################################################
        return positions
        
    
