#!/usr/bin/env python

import argparse, sys, os, re
import datetime, time
import numpy
import ppgplot
import generalUtils, configHelper
import saftClasses
from astropy.io import fits

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


if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Reduces SAFT data as it is accumulating in the output directory.')
	parser.add_argument('targetstring', type=str, help='Initial string defining the files to look for eg "WD1145-" will search for files called "WD1145-[nnnnnn].fits"')
	parser.add_argument('-s', '--searchpath', type=str, help='Folder where the data files can be found.')
	parser.add_argument('-u', '--updateinterval', type=float, help='Time in seconds to keep checking the folder for new data. ')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	args = parser.parse_args()
	print args
	
	config = configHelper.configClass("liveSAFTReduce")

	if args.save:
		config.save()
	
	if args.searchpath==None: searchPath = "."
	else: searchPath = args.searchpath
	
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
	
	hdulist = fits.open(frameFilename)
	frame = saftClasses.frameObject()
	frame.initFromFITS(hdulist)
	frameCounter+=1
	
	imageData =  hdulist[0].data
	hdulist.close()
	
	(height, width) = numpy.shape(imageData)
	
	""" Set up the PGPLOT windows """
	imagePlot = {}
	imagePlot['pgplotHandle'] = ppgplot.pgopen('/xs')
	ppgplot.pgpap(8, 1)
	ppgplot.pgenv(0., width,0., height, 1, -2)
	imagePlot['pgPlotTransform'] = [0, 1, 0, 0, 0, 1]
	
	boostedImage = generalUtils.percentiles(imageData, 20, 99)
	ppgplot.pggray(boostedImage, 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
	
	if numFrames == 1: sys.exit()
	
	# Catch up on all frames found so far
	for index in range(1, numFrames):
		hdulist = fits.open(fileList[index])
		frame = saftClasses.frameObject(index = frameCounter)
		frame.initFromFITS(hdulist)
		frameCounter+=1		
		hdulist.close()
		ppgplot.pggray(frame.boostedImage(), 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
		print frame.__str__(long=True)
	
	try:
		while True:
			time.sleep(updateInterval)
			newFiles = checkForNewFiles()
			for f in newFiles:
				fileList.append(f)
				hdulist = fits.open(f)
				frame = saftClasses.frameObject(index = frameCounter)
				frame.initFromFITS(hdulist)
				frameCounter+=1		
				hdulist.close()
			
				ppgplot.pggray(frame.boostedImage(), 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
			
	except KeyboardInterrupt:
		ppgplot.pgclos()
	
	
	
