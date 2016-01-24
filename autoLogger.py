#!/usr/bin/env python3

import argparse, sys, os, re, json, subprocess
import datetime, time, math
from astropy.io import fits
import configHelper, saftClasses

def convertDMStoRadians(dmsStr):
	""" Format for input 'DD:MM:SS.dd' """
	
	pieces = dmsStr.split(':')
		
	degrees = int(pieces[0])
	minutes = int(pieces[1])
	seconds = float(pieces[2])
	
	return (degrees + minutes/60.0 + seconds / 3600.0)/180.*math.pi
	
def getMostRecentFITSFile(searchPath):
	try:
		files = os.listdir(searchPath)
		fileList= []
		for f in files:
			extension = f.split(".")[-1]
			if "fits" in extension:
				fileObject = {}
				fileObject['name'] = f
				fileObject['date'] = os.path.getctime(searchPath + '/' + f)
				fileList.append(fileObject)
	except:
		print("Could not find the directory %s. Sorry."%searchPath)
	fileList = sorted(fileList, key=lambda file: file['date'], reverse=True)
	return fileList[0]['name']
	
				
	
def checkForNewFiles(searchPath):
	newFiles = []
	try:
		files = os.listdir(searchPath)
	except:
		print("Could not find the directory %s. Exiting."%searchPath)
		sys.exit(-1)
	for f in files:
		if f not in fileList:
			newFiles.append(f)
			# print "found new file", f
	return newFiles
	
def parseWeatherData(data):
	weatherObject = {}
	
	lines = data.split("\n")
	for line in lines:
		# print("Line:", line)
		if "Data received" in line:
			datetimeString = line[len("Data received")+1:-2]
			weatherDateTime = datetime.datetime.strptime(datetimeString, "%Y-%m-%dT%H:%M:%S")
			weatherObject['date'] = weatherDateTime.strftime("%Y-%m-%d")
			weatherObject['time'] = weatherDateTime.strftime("%H:%M:%S")
		try:
			# print("parts:", line.split(':'))
			valueString = (line.split(':')[1]).split(' ')[1]
		except IndexError:
			continue
		# print("ValueString:",valueString)
		if "Wind Direction" in line:
			weatherObject['WindDirection'] = float(valueString)
		if "Wind Speed" in line:
			weatherObject['WindSpeed'] = float(valueString)
		if "Temperature" in line:
			weatherObject['Temperature'] = float(valueString)
		if "Rel. Humidity" in line:
			weatherObject['RelativeHumidity'] = float(valueString)
		if "Pressure" in line:
			weatherObject['Pressure'] = float(valueString)
		if "Accum. Rain" in line:
			weatherObject['AccumulatedRain'] = float(valueString)
		if "Heater Temp." in line:
			weatherObject['HeaterTemperature'] = float(valueString)
		if "Heater Voltage" in line:
			weatherObject['HeaterVoltage'] = float(valueString)

	return weatherObject
	

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Reads the OBS_DATA folder on the 1-metre NUC and creates files for and web based log view of the night.')
	parser.add_argument('date', type=str, help='The date to create the log for.')
	parser.add_argument('--obsdata', type=str, help='Folder where the OBS_DATA can be found.')
	parser.add_argument('-u', '--updateinterval', type=float, help='Time in seconds to keep checking the folder for new data. ')
	parser.add_argument('-o', '--outputpath', type=str, help='Path for the JSON output file that is going to be used in the web page.')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	parser.add_argument('--weather', action="store_true", help='Get the weather data too.')
	parser.add_argument('-n', '--iterations', type=int, help='Terminate after "n" iterations.')
	args = parser.parse_args()
	print(args)
	
	config = configHelper.configClass("autoLogger")
	configDefaults  = {
		"OBSDATAPath": '/home/saft/OBS_DATA',
		"JSONPath": '/home/saft/www/autologger',
		"UpdateInterval": 60,
		"WeatherData": False, 
		"WeatherCommand": "vaisala"
	}
	config.setDefaults(configDefaults)

	updateInterval = config.assertProperty("UpdateInterval", args.updateinterval)
	jsonPath = config.assertProperty("JSONPath", args.outputpath)
	obsdataPath = config.assertProperty("OBSDATAPath", args.obsdata)
	weatherData = config.assertProperty("WeatherData", args.weather)
	weatherCommand = config.assertProperty("WeatherCommand", None)
	obsdataPath+= "/" + args.date
		
	if args.save:
		config.save()
		
	now = datetime.datetime.now()
	print("Running autoLogger at:", now)
	
	fileList = []
	targets = []
	
	terminate = False;
	iterationsToGo = args.iterations
	while not terminate:
	
		newFiles = checkForNewFiles(obsdataPath)
	
		for f in newFiles: fileList.append(f)
		framePattern = re.compile(".*(-|.|_)[0-9]+.(fits.gz|fit.gz|fits|fit|FIT)")
		frameSubPattern = re.compile("[A-Z,a-z,0-9]*")
		for filename in newFiles:
			r = framePattern.search(filename)
			if (r):
				rs = frameSubPattern.search(filename)
				if rs:
					targetName = rs.group(0)
					if targetName not in targets: targets.append(targetName)
		print("Targets:", targets)	
		targetList = []
		for t in targets:
			targetObject = {}
			targetObject['name'] = t
			targetObject['files'] = []
			targetObject['frames'] = []
			for f in fileList:
				framePattern = re.compile("%s-[0-9]*"%t)
				r = framePattern.search(f)
				if (r):
					match = r.group(0)
					frameNumber = int(match[len(t)+1:])
					targetObject['files'].append(f)
					targetObject['frames'].append(frameNumber)
				
			targetObject['startFrame'] = min(targetObject['frames'])
			targetObject['endFrame'] = max(targetObject['frames'])
			targetObject['numFrames'] = len(targetObject['frames'])
		
			print(targetObject['name'], targetObject['startFrame'], targetObject['endFrame'], targetObject['numFrames'])
			targetObject['files'] = sorted(targetObject['files'])
			targetObject['frames'] = sorted(targetObject['frames'])
		
			targetList.append(targetObject)
		
		for t in targetList:
			firstFrame = obsdataPath + '/' + t['files'][0]
			print("%s: Looking at the FITS headers in %s"%(t['name'], firstFrame))
			hdulist = fits.open(firstFrame)
			headers =  hdulist[0].header
			t['xbin'] = int(headers['XBINNING'])
			t['ybin'] = int(headers['YBINNING'])
			t['telescope'] = headers['TELESCOP']
			t['targetRA'] = headers['OBJRA']
			t['targetDEC'] = headers['OBJDEC']
			t['telescopeRA'] = headers['RA']
			t['telescopeDEC'] = headers['DEC']
			t['filter'] = headers['FILTER']
			t['startElevation'] = headers['ELEVATIO']
			t['startAirmass'] = 1.0/math.cos(math.pi/2.0 - convertDMStoRadians(t['startElevation']))
			t['exposureTime'] = float(headers['EXPTIME'])
			t['startMJD'] = float(headers['MJD-OBS'])
			t['focusPosition'] = headers['FOCUSPOS']
			if t['filter'] == '': t['filter'] = '--unknown--'	
			if t['telescope'] == '': t['telescope'] = '--unknown--'	
			t['xpixels'] = int(headers['NAXIS1'])
			t['ypixels'] = int(headers['NAXIS2'])
			t['obsDateTime'] = headers['DATE-OBS']
			hdulist.close()
		
			obsDateTime = datetime.datetime.strptime(t['obsDateTime'], "%Y-%m-%dT%H:%M:%S.%f")
			t['startObservationUTC'] = obsDateTime.strftime("%H:%M:%S")
		
			lastFrame = obsdataPath + '/' + t['files'][-1]
			print("%s: Looking at the FITS headers in %s"%(t['name'], lastFrame))
			hdulist = fits.open(lastFrame)
			headers =  hdulist[0].header
			t['endElevation'] = headers['ELEVATIO']
			t['endAirmass'] = 1.0/math.cos(math.pi/2.0 - convertDMStoRadians(t['endElevation']))
			t['endMJD'] = float(headers['MJD-OBS'])
			t['obsDateTime'] = headers['DATE-OBS']
			hdulist.close()
			obsDateTime = datetime.datetime.strptime(t['obsDateTime'], "%Y-%m-%dT%H:%M:%S.%f")
			t['endObservationUTC'] = obsDateTime.strftime("%H:%M:%S")
		
		
			del t['frames']
			del t['files']
		
			t['durationMinutes'] = (t['endMJD'] - t['startMJD']) * 24.*60.
		
			totalExposureTime = t['exposureTime'] * t['numFrames']
		
			t['deadTime'] = t['durationMinutes'] * 60. - totalExposureTime
			t['estimatedReadoutTime'] = t['deadTime'] / t['numFrames']
		
		for t in targetList:
			print(t['name'])
			for key in t.keys():
				print("  ", key, ":", t[key])
			
		outputfile = open(jsonPath + "/" + args.date + ".json", 'wt')
		json.dump(targetList, outputfile)
		outputfile.close()
		
		if weatherData:
			weatherResponse = subprocess.check_output(weatherCommand, shell=True)
			weatherObject = parseWeatherData(weatherResponse.decode('utf-8'))
			print("Vaisala weather data:", weatherObject)
			outputfile = open(jsonPath + "/weather.json", 'wt')
			json.dump(weatherObject, outputfile)
			outputfile.close()
	
		if iterationsToGo!= None:
			iterationsToGo-= 1
			print ("Iterations to go: ", iterationsToGo)
			if iterationsToGo==0: terminate = True
			
		print ("latest file:", getMostRecentFITSFile(obsdataPath))
		
		frame = saftClasses.frameObject(index = 0)
		frame.initFromFile(getMostRecentFITSFile(obsdataPath))
		outputPNGFilename = jsonPath + "/latestImage.png"
		frame.saveAsPNG(outputPNGFilename)
		
		
		time.sleep(updateInterval)
