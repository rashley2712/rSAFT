import numpy
import generalUtils
from astropy.io import fits

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
		self.bitmap = None
		self.filename = None
		self.index = index
		self.frameType = None     # Should be bias/flat/dark/science/balance
		
	def boostedImage(self, lower=20, upper=99):
		return generalUtils.percentiles(self.imageData, lower, upper)

	def initFromFile(self, filename):
		hdulist = fits.open(filename)
		self.initFromFITS(hdulist)
		hdulist.close()
		
	def subtractFrame(self, otherFrame):
		if (self.xBinning != otherFrame.xBinning) or (self.yBinning != otherFrame.yBinning):
			print "WARNING: Unable to subtract a frame with different binning!"
			return
		self.imageData = numpy.subtract(self.imageData, otherFrame.imageData)
		
	def initFromFITS(self, hdulist):
		card = hdulist[0]
	
		# Search for valuable metadata in the FITS headers
		for desiredParameter in self.metadata.keys():
			try:
				value = card.header[self.metadata[desiredParameter]]
			except KeyError:
				print "WARNING: Could not find the FITS header you were looking for: %s FITS: %s"%(desiredParameter, self.metadata[desiredParameter])
				value = None
			setattr(self, desiredParameter, value)
		self.imageData = hdulist[0].data
		self.xSize, self.ySize = numpy.shape(self.imageData)

	def __str__(self, long = False):
		printout = "Frame number: %d \tMJD: %f"%(self.index, self.MJD)
		if long:
			printout+= "\nBinning: (%dx%d) \tDimensions: (%dx%d)"%(self.xBinning, self.yBinning, self.xSize, self.ySize)
			
			
		return printout
