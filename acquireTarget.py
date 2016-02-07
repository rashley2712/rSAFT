#!/usr/bin/env python3

import argparse, sys, os, re, json, subprocess
import datetime, time, math
from astropy.io import fits
import configHelper, saftClasses, generalUtils

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Moves the telescope to the target ra and dec by using a call to Astrometry.net to find error and then offset.')
	parser.add_argument('ra', type=str, help='Right ascension.')
	parser.add_argument('dec', type=str, help='Declination.')
	parser.add_argument('-u', '--updateinterval', type=float, help='Time in seconds to keep checking the folder for new data. ')
	parser.add_argument('-o', '--outputpath', type=str, help='Path for the JSON output file that is going to be used in the web page.')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	parser.add_argument('--telpath', type=str, help='Path to the "tel" binary.')
	parser.add_argument('--tmppath', type=str, help='Path to FITS files created by the camera.')
	args = parser.parse_args()
	print(args)
	
	config = configHelper.configClass("acquireTarget")
	configDefaults  = {
		"telPath": '/home/saft/src/teld/',
		"tmpPath": '/tmp',
		"latestFrameName": "/tmp/latestFrame.dat"
	}
	config.setDefaults(configDefaults)

	telPath = config.assertProperty("telPath", args.telpath)
	jsonPath = config.assertProperty("tmpPath", args.tmppath)	
	if args.save:
		config.save()
		
	radec = generalUtils.sexagesimalParts(args.ra, args.dec)
	radec = generalUtils.fromSexagesimal(args.ra, args.dec)
	print("Your target is at %3.5f, %3.5f degrees."%(radec[0], radec[1]))
	
	telCommand = ["tel"]
	telCommand.append("track")
	telCommand.append(args.ra)
	telCommand.append(args.dec)
	print ("Issuing telescope tracking command: " + str(telCommand))
	subprocess.call(telCommand)
	
	# Acquire an image
	acquireCommand = ["r_acquire.sh"]
	acquireCommand.append("andor0")
	print ("Issuing camera acquisition command: " + str(acquireCommand))
	subprocess.call(acquireCommand)
	
	frameFile = open(config.latestFrameName, "rt")
	
	fitsFilename = frameFile.readline().strip()
	print (fitsFilename)
	
	solutionOutputFile = fitsFilename + "_wcs_solution.fits"
	FITSSolutionOutputFile = fitsFilename + "_wcs_solved_image.fits"
	# Run astrometryClient
	astrometryCommand = ['astrometryClient.py']
	astrometryCommand.append("-kpadlqljoevlogqik")
	astrometryCommand.append("-u" + fitsFilename)
	astrometryCommand.append("--wcs=" + solutionOutputFile)
	astrometryCommand.append("--wcsfits=" + FITSSolutionOutputFile)
	#astrometryCommand.append("-w")
	#astrometryCommand.append("--ra=" + str(runInfo.ra))
	#astrometryCommand.append("--dec=" + str(runInfo.dec))
	#astrometryCommand.append("--radius=1")
	
	print("Running Astrometry.net command" + str(astrometryCommand))
	
	result = subprocess.call(astrometryCommand)
	
	print("Result:", result)
	

	