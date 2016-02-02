
class Objects():

	def __init__(self, lb, cl, ch):
		self.label = lb
		self.color_range_low = cl
		self.color_range_high = ch

	def getLabel(self):
		return self.label

	def getPosX(self):
		return self.position_x

	def getPosY(self):
		return self.position_y

	def getColH(self):
		return self.color_range_high

	def getColL(self):
		return self.color_range_low

	def setPosX(self, x):
		self.position_x = x
	
	def setPosY(self,y):
		self.position_y = y



