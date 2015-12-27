#!/usr/bin/env python

import argparse, sys
import datetime, time
import numpy
import ppgplot
import generalUtils, configHelper
from astropy.io import fits

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Simulates a real run on the SAFT telescope.')
	parser.add_argument('runfile', type=str, help='A text file containing the filenames of all of the images that will be output from the \'run\'.')
	parser.add_argument('-o', '--outputdir', type=str, help='Folder to use for the output of the \'run\'.')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	parser.add_argument('--plot', action="store_true", help='Show each frame in a PGPLOT window.')
	parser.add_argument('-e', '--exposuretime', type=float, help='Exposure time for the simulated exposures.')
	parser.add_argument('-r', '--readouttime', type=float, help='Readout time for the simulated exposures.')
	args = parser.parse_args()
	print args
	
	config = configHelper.configClass("simulateSAFTRun")
	configDefaults  = {
		"ExposureTime": 3.0,
		"ReadoutTime": 2.0
	}
	config.setDefaults(configDefaults)
	exposureTime = config.assertProperty("ExposureTime", args.exposuretime)
	readoutTime = config.assertProperty("ReadoutTime", args.readouttime)
	outputDir = config.assertProperty("OutputDirectory", args.outputdir)
	if args.save:
		config.save()
	
	print "Exposure time:", exposureTime
	print "Readout time:", readoutTime
	print "Output directory:", outputDir
	
	filenames = []	
	filename = args.runfile
	fileList = open(filename, 'r')
	for line in fileList:
		filenames.append(str(line.strip()))
	fileList.close()
	
	numFrames = len(filenames)
	print "There are %d frames in this run."%numFrames
	
	hdulist = fits.open(filenames[0])
	
	# print hdulist.info()
	# for card in hdulist:
		# print card.header
	#	print card.header.keys()
	#	print repr(card.header)
	
	imageData =  hdulist[0].data
	hdulist.close()
	
	(height, width) = numpy.shape(imageData)
	
	if args.plot:
		""" Set up the PGPLOT windows """
		imagePlot = {}
		imagePlot['pgplotHandle'] = ppgplot.pgopen('/xs')
		ppgplot.pgpap(8, 1)
		ppgplot.pgenv(0., width,0., height, 1, -2)
		imagePlot['pgPlotTransform'] = [0, 1, 0, 0, 0, 1]
		
		boostedImage = generalUtils.percentiles(imageData, 20, 99)
		ppgplot.pggray(boostedImage, 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
		

	for index, frameFilename in enumerate(filenames):
		hdulist = fits.open(frameFilename)
		pathlessFilename = frameFilename.split('/')[-1]
		imageData =  hdulist[0].data
		if args.plot:
			boostedImage = generalUtils.percentiles(imageData, 20, 99)
			ppgplot.pggray(boostedImage, 0, width-1, 0, height-1, 0, 255, imagePlot['pgPlotTransform'])
		outputFilename = outputDir + "/" + pathlessFilename
		hdulist.writeto(outputFilename, clobber=True)
		hdulist.close()
		sys.stdout.write("\r%d frames of %d written to: %s"%(index+1, numFrames, outputFilename))
		sys.stdout.flush()
		time.sleep(readoutTime + exposureTime)
		
	
	if args.plot: ppgplot.pgclos()
	
	
	
