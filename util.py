# Procedure for setting keys
def set_value(array,key,value):
	# Set key to value
	array[key]=value

def clamp(val, minVal, maxVal): 
	# This function constrains a value such that it is always within or equal to the minimum and maximum bounds. 

	val = min( max(val, minVal), maxVal) 
	# This line first finds the larger of the val or the minVal, and then compares that to the maxVal, taking the smaller. This ensures 
	# that the result you get will be the maxVal if val is higher than it, the minVal if val is lower than it, or the val itself if it's 
	# between the two. 

	return val 
	# returns the clamped value 
