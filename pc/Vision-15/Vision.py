import sys

from Room import *

if len(sys.argv) > 1:
	r = Room(int(sys.argv[1]))
	r.vision()
else:
	print("The room number is not specified. Options are: 0 or 1 (1 - furthest, 0 - closest room)")


