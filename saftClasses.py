import numpy, os
from astropy.io import fits
from PIL import Image,ImageDraw,ImageFont


def percentiles(data, lo, hi):
    """ Returns a normalised array where lo percent of the pixels are 0 and hi percent of the pixels are 255
    """
    max = data.max()
    dataArray = data.flatten()
    pHi = numpy.percentile(dataArray, hi)
    pLo = numpy.percentile(dataArray, lo)
    range = pHi - pLo
    scale = range/255
    data = numpy.clip(data, pLo, pHi)
    data-= pLo
    data/=scale
    return data
	
def changeExtension(filename, extension):
	return os.path.splitext(filename)[0] + "." + extension 
	
def writePNG(imageArray, filename):
	""" Writes to a PNG file using the PIL library. Adds a .png extension if it isn't already there in 'filename' """
	imgData = numpy.rot90(imageArray, 3)
	imgSize = numpy.shape(imgData)
	imgLength = imgSize[0] * imgSize[1]
	testData = numpy.reshape(imgData, imgLength, order="F")
	img = Image.new("L", imgSize)
	palette = []
	for i in range(256):
		palette.extend((i, i, i)) # grey scale
		img.putpalette(palette)
	img.putdata(testData)
	outputFilename = changeExtension(filename, "png")
	print ("Writing PNG file: " + outputFilename) 
	img.save(outputFilename, "PNG", clobber=True)
	

class frameObject:
	""" This is a class of an individual frame
	"""
	
	metadata = {
		"CCDtemperature"	: "CCD-TEMP",
		"xBinning" 			: "XBINNING",
		"yBinning" 			: "YBINNING",
		"MJD"				: "MJD-OBS",
		"exposureTime"		: "EXPTIME",
		"raString"			: "RA",
		"decString"			: "DEC"
	}
	
	def __init__(self, index = 0):
		self.filename = None
		self.index = index
		self.frameType = "undefined"     # Should be bias/flat/dark/science/balance
		
	def boostedImage(self, lower=20, upper=99):
		return percentiles(self.imageData, lower, upper)

	def initFromFile(self, filename):
		hdulist = fits.open(filename)
		self.initFromFITS(hdulist)
		hdulist.close()
		
	def saveAsPNG(self, filename):
		imageArray = self.boostedImage()
		writePNG(imageArray, filename)
		
		
	def computeMedian(self):
		self.median = numpy.median(self.imageData)
		self.min = numpy.min(self.imageData)
		self.max = numpy.max(self.imageData)
		return self.median
		
	def subtractFrame(self, otherFrame):
		if (self.xBinning != otherFrame.xBinning) or (self.yBinning != otherFrame.yBinning):
			print("WARNING: Unable to subtract a frame with different binning!")
			return
		self.imageData = numpy.subtract(self.imageData, otherFrame.imageData)
		self.computeMedian()
		
	def addFrame(self, otherFrame):
		if (self.xBinning != otherFrame.xBinning) or (self.yBinning != otherFrame.yBinning):
			print("WARNING: Unable to subtract a frame with different binning!")
			return
		self.imageData = numpy.add(self.imageData, otherFrame.imageData)
		self.computeMedian()	
		
	def divideFrame(self, otherFrame):
		if (self.xBinning != otherFrame.xBinning) or (self.yBinning != otherFrame.yBinning):
			print ("WARNING: Unable to subtract a frame with different binning!")
			return
		self.imageData = numpy.divide(self.imageData, otherFrame.imageData)
		self.computeMedian()
		
	def initFromFITS(self, hdulist):
		card = hdulist[0]
	
		# Search for valuable metadata in the FITS headers
		for desiredParameter in self.metadata.keys():
			try:
				value = card.header[self.metadata[desiredParameter]]
			except KeyError:
				print("WARNING: Could not find the FITS header you were looking for: %s FITS: %s"%(desiredParameter, self.metadata[desiredParameter]))
				value = None
			setattr(self, desiredParameter, value)
		self.imageData = hdulist[0].data
		self.xSize, self.ySize = numpy.shape(self.imageData)
		self.computeMedian()

	def __str__(self, long = False):
		printout = "Frame number: %d \tMJD: %f"%(self.index, self.MJD)
		if long:
			printout+= "\nType: %s"%self.frameType
			printout+= "\nBinning: (%dx%d) \tDimensions: (%dx%d)"%(self.xBinning, self.yBinning, self.xSize, self.ySize)
			printout+= "\nMedian: %d \t Min, Max: (%.2f, %.2f)"%(self.median, self.min, self.max)
			printout+= "\n"
			
			
		return printout
