#!/usr/bin/env python3

import argparse, sys, os, re, json, subprocess
import datetime, time, math
from astropy.io import fits
import configHelper, saftClasses

	

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Moves the telescope to the target ra and dec by using a call to Astrometry.net to find error and then offset.')
	parser.add_argument('ra', type=str, help='Right ascension.')
	parser.add_argument('dec', type=str, help='Declination.')
	parser.add_argument('-u', '--updateinterval', type=float, help='Time in seconds to keep checking the folder for new data. ')
	parser.add_argument('-o', '--outputpath', type=str, help='Path for the JSON output file that is going to be used in the web page.')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	parser.add_argument('--weather', action="store_true", help='Get the weather data too.')
	parser.add_argument('-n', '--iterations', type=int, help='Terminate after "n" iterations.')
	args = parser.parse_args()
	print(args)
	
	config = configHelper.configClass("acquireTarget")
	configDefaults  = {
		"telPath": '/home/saft/src/teld/',
		"tmpPath": '/tmp'
	}
	config.setDefaults(configDefaults)

	telPath = = config.assertProperty("telPath", args.telpath)
	jsonPath = config.assertProperty("tmpPath", args.tmppath)	
	if args.save:
		config.save()

	