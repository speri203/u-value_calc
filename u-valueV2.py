'''
This script is meant to estimate u_values a set of 4 equations. This script is meant to go through a JSON file holding coordinates
of annotated objects found within a thermal picture. Once objects have been found their coordinates are noted down and checked for
pixel thermal value found within a similarly named CSV file (ex. DJI_0000.jpg.json and DJI_0000.csv). Averages are calculated for these
objects and returned to the screen. This script is meant to be autonomous, meaning the folder containing the JSON files and the folder
containing CSV files are needed to be passed in and the script will go through all files in the specified directories. This script has
FIVE commandline arguements. The script is exected as follows "python3 u-valueV2.py [JSON directory] [CSV directory] [indoor_temp] [outdoor_temp] [wind_speed]"
Units are in Kelvin and m/s. NOTE: THIS SCRIPT IS NOT OPTOMIZED FULLY. EACH TIME AN OBJECT IS FOUND WITHIN JSON FILE THE CSV FILE IS OPENED TO FIND THE LOCATION
TO CALCULATE U-VALUE. THE CSV FILE CAN BE OPEN MANY MANY TIMES PER JSON FILE. A SOLUTION WHERE THE CSV FILE NEEDS TO BE OPENED ONLY ONCE PER IMAGE WOULD BE BENEFICIAL
'''

import os
import csv
import sys
import json
import numpy as np
from skimage import draw #Used to calculate points within a polygon
import cmath

#Global variables to hold data that is mutual to whole test dataset
#Essentially arguements taken in by commandline and are similar for all images within directory
wind_speed = 0
inside_temperature = 0
outside_temperature = 0
csvFilePath = ''
jsonFilePath = ''

def kelvinConvert(x):
    '''
    This function will take in a celsius reading and convert it to kelvin.
    :param x: Degrees in Celsius.
    :return: Degrees in Kelvin.
    '''
    return float(x) + 273.15

def loadData():
    '''
    Function will go through the command line arguements and load data into global variables
    argv[1] = JSON file path
    argv[2] = CSV file path
    argv[3] = Inside temperature in C
    argv[4] = Outside temperature in C
    argv[5] = wind speed in mph
    '''
    global jsonFilePath, csvFilePath, inside_temperature, outside_temperature, wind_speed

    jsonFilePath = sys.argv[1]
    csvFilePath = sys.argv[2]
    inside_temperature = sys.argv[3]
    outside_temperature = sys.argv[4]
    wind_speed = float(sys.argv[5]) * .44704

def parseJSON(jsonFilePath):
    '''
    This go through each json file within the folder passed and look for specific tags to identify objects
    that were annotated prehand. This function will then extract points to identify edges of these objects
    From there these values are passed to the CSV function to actually calculate the u-value and average it
    for those objects
    :param jsonFilePath: Path to the folder that holds json files.
    NOTE!!!!!!! JSON FILE CONTAINS COORDINATES IN Y,X FORM NOT X,Y
    '''
    for jsonFile in os.listdir(jsonFilePath): #get the names of all files within the directory
        if(jsonFile.endswith(".json")): #makeing sure file ends in .json extension
            #Add filename to the filepath
            path = jsonFilePath + '/' + jsonFile
            with open(path) as read_json: #read_json holds the object of the file
                data = json.load(read_json)
                for entry in data['objects']:  # Entry holds each dictionary between each description tags
                    if(entry['classTitle'] == 'Window'):
                        points = entry['points'] #Fetch the points attribute
                        exterior = (points['exterior']) #Y and X are swapped within the json file
                        y1 = exterior[0][0]
                        x1 = exterior[0][1]
                        y2 = exterior[1][0]
                        x2 = exterior[1][1]
                        csvFileName = jsonFile.split('.')

                        #Check to see if csv file exists
                        for csvFiles in os.listdir(csvFilePath):
                            csvFiles = csvFiles.split('.')
                            if(csvFiles[0] ==csvFileName[0]):
                                average_u_value = parseCSVRectangle(csvFilePath, csvFileName[0], x1, y1, x2, y2)
                                print("Window Av. {} | Eq1: {} | Eq2: {} | Eq3: {} | File: {}".format(average_u_value[0],average_u_value[1].real,average_u_value[2].real ,average_u_value[3].real, jsonFile))
                            else:
                                continue
                    if (entry['classTitle'] == 'LAMP'):
                        points = entry['points']  # Fetch the points attribute
                        exterior = (points['exterior'])  # Y and X are swapped within the json file
                        y1 = exterior[0][0]
                        x1 = exterior[0][1]
                        y2 = exterior[1][0]
                        x2 = exterior[1][1]
                        csvFileName = jsonFile.split('.')

                            # Check to see if csv file exists
                        for csvFiles in os.listdir(csvFilePath):
                            csvFiles = csvFiles.split('.')
                            if (csvFiles[0] == csvFileName[0]):
                                average_u_value = parseCSVRectangle(csvFilePath, csvFileName[0], x1, y1, x2, y2)
                                print("LAMP Av. {} | Eq1: {} | Eq2: {} | Eq3: {} | File: {}".format(average_u_value[0], average_u_value[1].real, average_u_value[2].real, average_u_value[3].real, jsonFile))
                            else:
                                continue

                    if (entry['classTitle'] == 'Door'):
                        points = entry['points']  # Fetch the points attribute
                        exterior = (points['exterior'])  # Y and X are swapped within the json file
                        y1 = exterior[0][0]
                        x1 = exterior[0][1]
                        y2 = exterior[1][0]
                        x2 = exterior[1][1]
                        y3 = exterior[2][0]
                        x3 = exterior[2][1]
                        y4 = exterior[3][0]
                        x4 = exterior[3][1]
                        csvFileName = jsonFile.split('.')

                        # Find all points within polygon
                        r = np.array([y1, y2, y3, y4])
                        c = np.array([x1, x2, x3, x4])
                        x_axis, y_axis = draw.polygon(r, c) # Y_AXIS HOLDS X VALUES AND X_AXIS HOLDS Y VALUES

                        # Check to see if csv file exists
                        for csvFiles in os.listdir(csvFilePath):
                            csvFiles = csvFiles.split('.')
                            if (csvFiles[0] == csvFileName[0]):
                                average_u_value = parseCSVPolygon(csvFilePath, csvFileName[0], x_axis, y_axis) # Y_AXIS HOLDS X VALUES AND X_AXIS HOLDS Y VALUES
                                print("Door Av. {} | Eq1:{} | Eq2: {} | Eq3: {} | File: {}".format(average_u_value[0],average_u_value[1].real, average_u_value[2].real,
                                                                                         average_u_value[3].real, jsonFile))
                            else:
                                continue
                        #print("File: {} x: {} y: {} x:{} y:{}".format(jsonFile, x1, y1, x2, y2))

def parseCSVRectangle(csvFilePath, fileName, x1, y1, x2, y2):
    '''
    Parses though CSV file looking for rectangle marked objects and finds the average u-value of the object
    :param csvFilePath: Path to the directory holding csv files
    :param fileName: Name of the csv file
    :param x1: X Coord
    :param y1: Y Coord
    :param x2: X Coord
    :param y2: Y Coord
    :return: Returns the average u value for the object
    '''
    emissivity = 0
    pixel_temperature = []
    average = 0
    average2 = 0
    average_u_values = []
    total2 = 0
    total3 = 0
    total4 = 0
    total = 0

    fileName += ".csv"
    path = csvFilePath + '/' + fileName
    with open(path) as read_csv:
        csvData = csv.reader(read_csv, delimiter=',', quotechar='|')  # Seperated by comma (hence csv)
        for i, data in enumerate(csvData):  # i holds the index and increments each loop while data holds cells value
            length = len(data)
            if (length == 0):  # Incase the length of a row is 0 (empty cells)
                continue
            else:
                index = length - 1  # Extract the last data point in the row
            if (i == 2):
                emissivity = float(data[index])
                #print(emissivity)
            if (i >= 10):
                pixel_temperature.append(data[1:])  # Pixel temperature now holds 512 indexes. Each index

    for x in range(x1, x2): #JSON file has x and y flipped for exterior points
        for y in range(y1, y2):
            u = u_value_calculation(emissivity, pixel_temperature[x][y])
            u2 = u_value_estimation_eq1(emissivity, pixel_temperature[x][y])
            u3 = u_value_estimation_eq2(emissivity, pixel_temperature[x][y])
            u4 = u_value_estimation_eq3(emissivity, pixel_temperature[x][y])
            total += u
            total2 += u2
            total3 += u3
            total4 += u4
            #print("x: {} y: {} u: {}".format(x, y, u))
    average = total / ((x2-x1)*(y2-y1))
    average2 = total2 / ((x2-x1)*(y2-y1))
    average3 = total3 / ((x2-x1)*(y2-y1))
    average4 = total4 / ((x2-x1)*(y2-y1))
    average_u_values.append(average)
    average_u_values.append(average2)
    average_u_values.append(average3)
    average_u_values.append(average4)

    return average_u_values #TODO: UPDATE THE RETURNED VARIABLE TO BE A LIST OF AVERAGES AND NOT JUST ONE VARIABLE

def parseCSVPolygon(csvFilePath, fileName, x, y):
    '''
    Parses though CSV file looking for rectangle marked objects and finds the average u-value of the object
    :param csvFilePath: Path to the directory holding csv files
    :param fileName: Name of the csv file
    :param Y: Holds the X coordinates
    :param X: holds the Y coordinates
    :return: Returns the average u value for the object
    '''
    emissivity = 0
    pixel_temperature = []
    average = 0
    total = 0
    total2 = 0 #For u_value_eq1 function
    total3 = 0
    total4 = 0
    average_values_list = []

    fileName += ".csv"
    path = csvFilePath + '/' + fileName
    with open(path) as read_csv:
        csvData = csv.reader(read_csv, delimiter=',', quotechar='|')  # Seperated by comma (hence csv)
        for i, data in enumerate(csvData):  # i holds the index and increments each loop while data holds cells value
            length = len(data)
            if (length == 0):  # Incase the length of a row is 0 (empty cells)
                continue
            else:
                index = length - 1  # Extract the last data point in the row
            if (i == 2):
                emissivity = float(data[index])
                #print(emissivity)
            if (i >= 10):
                pixel_temperature.append(data[1:])  # Pixel temperature now holds 512 indexes. Each index

    #TODO: Figure out how to calculate the doors u-value (or Polygons)
    for item in range(len(y)):
        total += u_value_calculation(emissivity, pixel_temperature[y[item]][x[item]]) #In the JSON order is y,x not x,y
        total2 += u_value_estimation_eq1(emissivity, pixel_temperature[y[item]][x[item]]) #In the JSON order is y,x not x,y
        total3 += u_value_estimation_eq2(emissivity, pixel_temperature[y[item]][x[item]])
        total4 += u_value_estimation_eq3(emissivity,pixel_temperature[y[item]][x[item]])
    average = total / (len(x) * len(y))
    average_values_list.append(average)
    average = total2 / (len(x) * len(y))
    average_values_list.append(average)
    average = total3 / (len(x) * len(y))
    average_values_list.append(average)
    average = total4 /(len(x) * len(y))
    average_values_list.append(average)

    return average_values_list

def u_value_calculation(emissivity, pixel_temperature):
    '''
    The data from the CSV is used in order to calculate the u-value. This function takes in params from the CSV and command line in order to calc
    u-values for each pixel. (This function calculates u-value pixel by pixel and not a row at a time)
    :param emissivity: Emissivity fetched from the CSV file
    :param atmosphere: Atmosphere temperature from CSV after converted to Kelvin
    :param wind_speed: Wind speed from command line converted into m/s
    :param indoor_temperature: Indoor temperature from command line converted into Kelvin
    :param pixil_temperature: pixel temperature from loadCSVData in Celsius
    :return: U-Value
    '''
    global wind_speed, outside_temperature, inside_temperature

    Ev = emissivity
    sigma = 5.67 #Constant
    Tw = kelvinConvert(pixel_temperature)
    Tout = kelvinConvert(outside_temperature)
    v = wind_speed
    Tin = kelvinConvert(inside_temperature)

    numerator = Ev * (sigma * (((Tw/100)**4) - ((Tout/100) ** 4))) + 3.8054 * (v * (Tw - Tout))
    denominator = Tin - Tout

    return(numerator/denominator)

def u_value_estimation_eq1(emissivity, pixel_temperature):
    '''
    This function is supposed to estimate the U-value using the first equation. This function will work much the same way as u_value_calculation
    and will return the u_value estimate at that pixel
    :param emissivity: Emissivity fetched from CSV
    :param pixel_temperature: Pixel temperature passed in by the parseCSVRectangle or parseCSVPolygon functions
    :return: u_value estimate for the pixel values
    '''

    global outside_temperature, inside_temperature

    E = emissivity
    sigma = 5.67
    Ts = kelvinConvert(pixel_temperature)
    Tref = kelvinConvert(outside_temperature)
    Tai = kelvinConvert(inside_temperature)
    L = 15.24 #height is 50 feet for twamley
    Ac = 1.365 * (((Ts - Tref) ** (1/4)) / L) #2 is supposed to be length of building face actually

    numerator = (4 * E * (sigma * (((Ts/100) ** 4) - ((Tref/100) ** 4))) + Ac * (Ts - Tref))
    denominator = (Tai - Tref)

    return (numerator/denominator)

def u_value_estimation_eq2(emissivity, pixel_temperatures):

    global outside_temperature, inside_temperature

    E = emissivity
    sigma = 5.67
    Ts = kelvinConvert(pixel_temperatures)
    Tref = kelvinConvert(outside_temperature)
    Tae = kelvinConvert(outside_temperature)
    Ta = kelvinConvert(outside_temperature)
    Tai = kelvinConvert(inside_temperature)
    L = 15.24  # height is 50 feet for twamley
    Ac = 1.365 * (((Ts - Tref) ** (1/4)) / L) #2 is supposed to be length of building face actually

    numerator = (4 * E * (sigma * ((Ts/100) ** 3) * ((Ts/100) - (Tref/100))) + Ac * (Ts - Tref
                                                                                     ))
    denominator = (Tai - Tae)

    return(numerator/denominator)

def u_value_estimation_eq3(emissivity, pixel_temperatures):

    global outside_temperature, inside_temperature

    E = emissivity
    sigma = 5.67
    Ts = kelvinConvert(pixel_temperatures)
    Tref = kelvinConvert(outside_temperature)
    Tae = kelvinConvert(outside_temperature)
    Ta = kelvinConvert(outside_temperature)
    Tai = kelvinConvert(inside_temperature)
    L = 15.24  # height is 50 feet for twamley
    Ac = 1.365 * (((Ts - Tref) ** (1/4)) / L) #2 is supposed to be length of building face actually
    Tm = (Ts + Tref) / 2

    numerator = (4 * E * sigma * ((Tm/100) ** 3) * ((Ts/100) - (Tref/100)) + Ac * (Ts - Tref))
    denominator = (Tai - Tae)

    return(numerator/denominator)
def main():
    loadData()
    parseJSON(jsonFilePath)
    #parseCSV(csvFilePath)

if(__name__ == '__main__'):
    main()