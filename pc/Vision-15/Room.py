import numpy as np
import cv2
from pylab import*
from scipy.ndimage import measurements
from scipy.spatial import distance
from Objects import*


Redball = Objects("Red Ball",[(0, 100, 200), (10, 200, 255)],[(170, 100, 200), (180, 200, 255)])
Blueball = Objects("Blue Ball",[(110, 100, 100), (115, 200, 200)],[(115, 100, 200), (120, 200, 200)])
#Green spot 2 per robot
#Pink spot 2 per robot
#Blue spot 2 per game
#Yellow spot 2 per game







class Room():
		

	def __init__(self,r_id):
		self.room_id=r_id
		if(self.room_id==1):
			self.mtx = np.loadtxt("mtx1.txt")
			self.dist = np.loadtxt("dist1.txt")
			self.pts1 = np.float32([[10, 2], [634, 37], [596, 478], [6, 456]])
		elif(self.room_id==2):
			self.mtx = np.loadtxt("mtx2.txt")
			self.dist = np.loadtxt("dist2.txt")
			self.pts1 = np.float32([[7, 5], [607, 4], [593, 451], [17, 450]])
		else:
			print("invalid room id")

		self.capture = cv2.VideoCapture(0)

	def vision(self):		
		c = True
		while c != 27:
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



		self.TrackObjects(Redball,imgOriginal)
                self.TrackObjects(Blueball,imgOriginal)
		



		cv2.namedWindow("Room", cv2.WINDOW_AUTOSIZE) 
    		cv2.imshow('Room',imgOriginal)
    		c = cv2.waitKey(2) & 0xFF                                               

	


	def TrackObjects(self, obj, imgOriginal):
		global l
		l = []
		
		#Image Masking		
		imgHSV = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2HSV)

		imgThreshLow = cv2.inRange(imgHSV, obj.getColL()[0], obj.getColL()[1])
		imgThreshHigh = cv2.inRange(imgHSV, obj.getColH()[0], obj.getColH()[1])

		imgThresh = cv2.add(imgThreshLow, imgThreshHigh)

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
		print "Frame"
	
############################################################################################################	 
		cluster = 1
		while(cluster < len(area)):
			i = area.argmax()
			pos = measurements.center_of_mass(z, lw, index = cluster)
			
			#obj.setPosX(int(pos[1]))
			#obj.setPosY(int(pos[0]))


			print obj.getLabel()+ " " + str(int(pos[1])) +","+ str(int(pos[0]))
			
	
			#cv2.circle(imgOriginal, (x,y), 3, (0, 255, 0), cv2.FILLED) 
			cv2.circle(imgOriginal, (int(pos[1]),int(pos[0])), 6, (0, 0, 255), 3)          
				
			#cv2.line(imgOriginal, (x,y),(0,0), (0, 255, 0), 2) # Trajectory drawn
			
			
			cluster = cluster + 1
			#area = np.delete(area, i)
############################################################################################################
	
		
	
