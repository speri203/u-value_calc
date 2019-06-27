import os
import csv
import sys
import json
import numpy as np
from skimage import draw #Used to calculate points within a polygon

#Global variables to hold data that is mutual to whole test dataset
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
                                print("Window Av. {} {}".format(average_u_value, jsonFile))
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
                                print("LAMP Av. {}".format(average_u_value))
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
                        x_axis, y_axis = draw.polygon(r, c)

                        # Check to see if csv file exists
                        for csvFiles in os.listdir(csvFilePath):
                            csvFiles = csvFiles.split('.')
                            if (csvFiles[0] == csvFileName[0]):
                                average_u_value = parseCSVPolygon(csvFilePath, csvFileName[0], x_axis, y_axis)
                                print("Door Av. {} {}".format(average_u_value, jsonFile))
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
    total_u_value = 0
    pixel_temperature = []
    average = 0
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
            total += u
            #print("x: {} y: {} u: {}".format(x, y, u))
    average = total / ((x2-x1)*(y2-y1))
    return average

def parseCSVPolygon(csvFilePath, fileName, x, y):
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
    total_u_value = 0
    pixel_temperature = []
    average = 0
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

    #TODO: Figure out how to calculate the doors u-value (or Polygons)
    for item in range(len(y)):
        total += u_value_calculation(emissivity, pixel_temperature[y[item]][x[item]])
    average = total / (len(x) * len(y))
    return average

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

def main():
    loadData()
    parseJSON(jsonFilePath)
    #parseCSV(csvFilePath)

if(__name__ == '__main__'):
    main()