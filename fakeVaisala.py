#!/usr/bin/env python3

import argparse, sys, os, re, json, subprocess
import datetime, time, math, random
from astropy.io import fits
import configHelper


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
	
	parser = argparse.ArgumentParser(description='Pretends to be the Vaisala weather station and reports some faked data.')
	parser.add_argument('--save', action="store_true", help='Write the input parameters to the config file as default values.')
	args = parser.parse_args()
	
	config = configHelper.configClass("fakeVaisala")
	configDefaults  = {
		"latestTemperature": 10.5,
		"latestWindSpeed": 13.7, 
		"latestWindDirection": 128,
		"latestRelativeHumidity": 36.7,
		"latestPressure": 776.3
	}
	config.setDefaults(configDefaults)
	
	now = datetime.datetime.now()
	nowString = now.strftime("%Y-%m-%dT%H:%M:%S")
	
	config.latestWindSpeed = config.latestWindSpeed + random.gauss(0, 2)
	config.latestTemperature = config.latestTemperature + random.gauss(0, 1)
	config.latestWindDirection = config.latestWindDirection + random.gauss(0, 8)
	config.latestRelativeHumidity = config.latestRelativeHumidity + random.gauss(0, 1)
	config.latestPressure = config.latestPressure + random.gauss(0, 4)
	
	if (config.latestWindDirection) > 360: config.latestWindDirection-= 360
	if (config.latestWindDirection) < 0: config.latestWindDirection+= 360
	if (config.latestWindSpeed) < 0: config.latestWindSpeed = 0
	if (config.latestRelativeHumidity) > 100: config.latestRelativeHumidity = 100
	if (config.latestRelativeHumidity) < 0: config.latestRelativeHumidity = 0
	
	print("Data received " + nowString + "Z:")
	print("Wind Direction: %.1f °"%config.latestWindDirection)
	print("    Wind Speed: %.1f km/h"%config.latestWindSpeed)
	print("   Temperature: %.1f \u2103"%config.latestTemperature)
	print(" Rel. Humidity: %.1f %%"%config.latestRelativeHumidity)
	print("      Pressure: %.1f hPa"%config.latestPressure)
	print("   Accum. Rain: 18.8 mm")
	print("  Heater Temp.: 11.9 \u2103")
	print("Heater Voltage: 18.2 V")
	
	config.save()
	
