#!/usr/bin/env python

import argparse, sys, os, re
import datetime, time
import numpy
import ppgplot
import generalUtils, configHelper
import saftClasses
import copy
from astropy.io import fits

from astropy.stats import median_absolute_deviation as mad
from photutils import datasets
from photutils import daofind
from photutils import aperture_photometry, CircularAperture, psf_photometry, GaussianPSF

def checkForNewFiles():
	newFiles = []
	try:
		files = os.listdir(searchPath)
	except:
		print "Could not find the directory %s. Exiting."%searchPath
		sys.exit(-1)
	for f in files:
		r = run_re.search(f)
		if (r):
			filename = r.group(0)
			if filename not in fileList:
				newFiles.append(filename)
				print "found new file", filename
	return newFiles
	
def plotSources(sources):
	ppgplot.pgsfs(2)   # Set fill style to 'outline'
	ppgplot.pgsci(3)   # Set the colour to 'green'
	for s in sources:
		x, y = s['xcentroid'], s['ycentroid']
		radius = s['sharpness']* 40.
		ppgplot.pgcirc(x,y, radius)
	



if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Reduces SAFT data as it is accumulating in the output directory.')
	parser.add_argument('targetstring', type=str, help='Initial string defining the files to look for eg "WD1145-" will search for files called "WD1145-[nnnnnn].fits"')
	parser.add_argument('-s', '--searchpath', type=str, help='Folder where the data files can be found.')
	parser.add_argument('-u', '--updateinterval', type=float, help='Time in seconds to keep checking the folder for new data. ')
	parser.add_argument('-r', '--reducedirectory', type=str, help='Reduction directory. Where to place all the output files produced during the reduction.')
	parser.add_argument('-b', '--bias', type=str, help='Use this as the bias frame')
	parser.add_argument('-f', '--flat', type=str, help='Use this as the flat (balance) frame')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	args = parser.parse_args()
	print args
	
	config = configHelper.configClass("liveSAFTReduce")
	configDefaults  = {
		"UpdateInterval": 1.0,
		"ReductionDirectory": "/home/rashley/astro/reductions",
		"SearchPath": ".",
		"BiasFrame": None,
		"FlatFrame": None
	}
	config.setDefaults(configDefaults)

	updateInterval = config.assertProperty("UpdateInterval", args.updateinterval)
	reductionDir = config.assertProperty("ReductionDirectory", args.reducedirectory)
	searchPath = config.assertProperty("SearchPath",args.searchpath)
	biasFrameFilename = config.assertProperty("BiasFrame", args.bias)
	flatFrameFilename = config.assertProperty("FlatFrame", args.flat)
	print flatFrameFilename
	if biasFrameFilename==None:	useBias = False
	else: useBias = True
	if flatFrameFilename==None:	useFlat = False
	else: useFlat = True
		
	if args.save:
		config.save()
		
	if useBias:
		biasFrame = saftClasses.frameObject()
		biasFrame.initFromFile(biasFrameFilename)
		biasFrame.frameType = "bias"
		print biasFrame.__str__(long=True)
		
	if useFlat:
		flatFrame = saftClasses.frameObject()
		flatFrame.initFromFile(flatFrameFilename)
		flatFrame.frameType = "flat"
		print flatFrame.__str__(long=True)
		
	
	targetString = args.targetstring
	
	if args.updateinterval == None:
		updateInterval = config.assertProperty("updateInterval", 1)
	else: updateInterval = args.updateinterval
	
	
	run_re = re.compile(r'%s-[0-9]{3,}.fits'%targetString)
	
	fileList = []
	fileList = checkForNewFiles()	
			
	fileList = sorted(fileList, key=lambda object: object, reverse = False)
	numFrames = len(fileList)
	print "Found %d files matching the targetString"%(numFrames)
	if numFrames == 0: sys.exit()
	
	
	frameFilename = fileList[0]
	
	
	frameCounter = 0
	
	frame = saftClasses.frameObject()
	frame.initFromFile(frameFilename)
	if useBias: frame.subtractFrame(biasFrame)
	if useFlat: frame.divideFrame(flatFrame)
	
	stackedFrame = copy.deepcopy(frame)
	frameCounter+=1
	
	(height, width) = numpy.shape(frame.imageData)
	
	""" Set up the PGPLOT windows """
	imagePlot = {}
	imagePlot['pgplotHandle'] = ppgplot.pgopen('/xs')
	ppgplot.pgpap(8, 1)
	ppgplot.pgenv(0., width,0., height, 1, -2)
	imagePlot['pgPlotTransform'] = [0, 1, 0, 0, 0, 1]
	
	
	stackedImagePlot = {}
	stackedImagePlot['pgplotHandle'] = ppgplot.pgopen('/xs')
	ppgplot.pgpap(6, 1)
	ppgplot.pgenv(0., width,0., height, 1, -2)
	stackedImagePlot['pgPlotTransform'] = [0, 1, 0, 0, 0, 1]
	
	""" Draw the latest frame """
	ppgplot.pgslct(imagePlot['pgplotHandle'])
	ppgplot.pggray(frame.boostedImage(), 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
	
	""" Draw the stacked image """
	ppgplot.pgslct(stackedImagePlot['pgplotHandle'])
	ppgplot.pggray(stackedFrame.boostedImage(), 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
	
	""" Look for sources in the stacked image """	
	bkg_sigma = 1.48 * mad(stackedFrame.imageData)
	sources = daofind(stackedFrame.imageData, fwhm=4.0, threshold=3*bkg_sigma)   
	plotSources(sources)
	for s in sources:
		print s
	
	if numFrames == 1: sys.exit()
	
	# Catch up on all frames found so far
	for index in range(1, numFrames):
		frame = saftClasses.frameObject(index = frameCounter)
		frame.initFromFile(fileList[index])
		frame.frameType = 'science'
		if useBias: frame.subtractFrame(biasFrame)
		if useFlat: frame.divideFrame(flatFrame)
		stackedFrame.addFrame(frame)
		
		frameCounter+=1	
		ppgplot.pgslct(imagePlot['pgplotHandle'])	
		ppgplot.pggray(frame.boostedImage(), 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
		plotSources(sources)
		print frame.__str__(long=True)
	
	# Now continue processing new frames as they arrive...
	try:
		while True:
			time.sleep(updateInterval)
			newFiles = checkForNewFiles()
			for f in newFiles:
				fileList.append(f)
				hdulist = fits.open(f)
				frame = saftClasses.frameObject(index = frameCounter)
				frame.initFromFITS(hdulist)
				frame.frameType = 'science'
				if useBias: frame.subtractFrame(biasFrame)
				if useFlat: frame.divideFrame(flatFrame)
				print frame.__str__(long=True)
				frameCounter+=1		
				hdulist.close()
			
				ppgplot.pggray(frame.boostedImage(), 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
				plotSources(sources)

	except KeyboardInterrupt:
		ppgplot.pgclos()
	
	
	
