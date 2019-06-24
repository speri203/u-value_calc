import csv
import sys
import os
import json
import numpy as np
from skimage import draw #Used to calculate points within a polygon

#Global variables to hold arguements/fetch data from the CSV file
filePath = ''
jsonFilePath = ''
indoor_temperature = 0.0
wind_speed = 0.0
emissivity = 0 #From CSV
atmosphere_temperature = 0 #From CSV
pixil_temperature = [] #Essentially a 2D array pixil_temperature[x][y] where x=row and y=column
u_values = []


#Check to make sure the right number of arguements are being entered into the command line
#arg1: CSV folder location
#arg2: Wind speed in MPH
#arg3: Indoor temperature in celsius
if(len(sys.argv) != 5):
    print("Invalid number of arguements. arg1: csv folder location, arg2: wind speed (mph), arg3: indoor room temperature (Celsius)")
    exit(0)

def kelvinConvert(x):
    '''
    This function will take in a celsius reading and convert it to kelvin.
    :param x: Degrees in Celsius.
    :return: Degrees in Kelvin.
    '''
    return float(x) + 273.15


def loadData():
    '''
    This function will load the global variables (filePath, indoor_temperature, wind_speed)
    with the proper inputs from the commandline.
    :return: None.
    '''
    global filePath, jsonFilePath,indoor_temperature, wind_speed
    filePath = sys.argv[1]
    jsonFilePath = sys.argv[2]
    indoor_temperature = kelvinConvert(sys.argv[3])
    wind_speed = float(sys.argv[4]) * .44704



def loadJSONData(filePath, jsonFilePath):
    '''
    This function firstly parses through annotated image's JSON file to pick out key objects identifited like Windows, Lamps, Heating/Cooling etc.
    Once objects have been identified their corresponding point pixels are returned. From this information we go to the CSV file and calculate u-values
    within the boundaries fetched from JSON. U values are calculated and averaged.
    :param filePath: CSV folder path
    :param jsonFilePath: JSON folder path
    :return:
    '''
    global emissivity, atmosphere_temperature, pixil_temperature
    for file in os.listdir(jsonFilePath):
        if(file.endswith(".json")):
            path = jsonFilePath + '/' + file
            with open(path) as read_file:
                data = json.load(read_file)
                for entry in data['objects']:  # Entry holds each dictionary between each description tags
                    '''
                    The layout of each dictionary is as follows
                    Windows: description, bitmap, tags, classTitle, points{exterior, interior}
                    LAMP: description, bitmap, tags, classTitle, points{exterior, interior}
                    Ground: description, bitmap, tags, classTitle, points{exterior: [], interior}
                    Door: description, bitmap, tags, classTitle, points{exterior: [], interior}
                    '''
                    if (entry['classTitle'] == 'Window'):
                        points = entry['points']
                        exterior = (points['exterior'])
                        x1 = exterior[0][0]
                        y1 = exterior[0][1]
                        x2 = exterior[1][0]
                        y2 = exterior[1][1]

                        #Need to get temperatures from csv
                        for fileName in os.listdir(filePath):
                            json_file_name = file.split(".")
                            csv_file_name = fileName.split(".")
                            if(csv_file_name[0].find(json_file_name[0]) != -1 and fileName.endswith(".csv")): #Finds similarly named json and csv files
                                #print("JSON: {} CSV: {}".format(json_file_name[0], csv_file_name[0]))
                                csv_file_path = filePath + "/" + fileName
                                with open(csv_file_path) as read_csv_file:
                                    csvData = csv.reader(read_csv_file, delimiter=',',
                                                         quotechar='|')  # Seperated by comma (hence csv)
                                    for i, data in enumerate(
                                            csvData):  # i holds the index and increments each loop while data holds cells value
                                        length = len(data)
                                        if (length == 0):  # Incase the length of a row is 0 (empty cells)
                                            continue
                                        else:
                                            index = length - 1  # Extract the last data point in the row
                                        if (i == 2):
                                            emissivity = float(data[index])
                                        if (i == 5):
                                            atmosphere = data[index]
                                            temp = atmosphere.split(" ")
                                            atmosphere_temperature = kelvinConvert(temp[0])
                                        if (i >= 10):
                                            pixil_temperature.append(data[1:])  # Pixil temperature now holds 512 indexes. Each index is a list of values for the whole row (0-511 rows)

                                # TODO: Writing back to CSV the u-values held in the list named u_value
                                total = 0
                                for x in range(x1, x2):
                                    for y in range(y1, y2):
                                        # u-value now holds the values of each pixel
                                        u_value = u_value_calculation(emissivity, atmosphere_temperature,
                                                                                  wind_speed, indoor_temperature,
                                                                                  (pixil_temperature[x][y]))
                                        u_values.append(u_value)
                                        total = total + u_value
                                        # print("x: {}, y: {}, value: {}".format(x, y, u_value))
                                #Calculate average
                                average = total / ((x2-x1) * (y2-y1))
                                print("fileName: {} Window Av. U value: {}".format(json_file_name,average))

                    if (entry['classTitle'] == 'LAMP'):
                        points = entry['points']
                        exterior = (points['exterior'])
                        x1 = exterior[0][0]
                        y1 = exterior[0][1]
                        x2 = exterior[1][0]
                        y2 = exterior[1][1]

                        # Need to get temperatures from csv
                        for fileName in os.listdir(filePath):
                            json_file_name = file.split(".")
                            csv_file_name = fileName.split(".")
                            if (csv_file_name[0].find(json_file_name[0]) != -1 and fileName.endswith(
                                    ".csv")):  # Finds similarly named json and csv files
                                # print("JSON: {} CSV: {}".format(json_file_name[0], csv_file_name[0]))
                                csv_file_path = filePath + "/" + fileName
                                with open(csv_file_path) as read_csv_file:
                                    csvData = csv.reader(read_csv_file, delimiter=',',
                                                         quotechar='|')  # Seperated by comma (hence csv)
                                    for i, data in enumerate(
                                            csvData):  # i holds the index and increments each loop while data holds cells value
                                        length = len(data)
                                        if (length == 0):  # Incase the length of a row is 0 (empty cells)
                                            continue
                                        else:
                                            index = length - 1  # Extract the last data point in the row
                                        if (i == 2):
                                            emissivity = float(data[index])
                                        if (i == 5):
                                            atmosphere = data[index]
                                            temp = atmosphere.split(" ")
                                            atmosphere_temperature = kelvinConvert(temp[0])
                                        if (i >= 10):
                                            pixil_temperature.append(data[
                                                                     1:])  # Pixil temperature now holds 512 indexes. Each index is a list of values for the whole row (0-511 rows)

                                # TODO: Writing back to CSV the u-values held in the list named u_value
                                total = 0
                                for x in range(x1, x2):
                                    for y in range(y1, y2):
                                        # u-value now holds the values of each pixel
                                        u_value = u_value_calculation(emissivity, atmosphere_temperature,
                                                                      wind_speed, indoor_temperature,
                                                                      (pixil_temperature[x][y]))
                                        u_values.append(u_value)
                                        total = total + u_value
                                        # print("x: {}, y: {}, value: {}".format(x, y, u_value))
                                # Calculate average u-value for each of the object
                                average = total / ((x2 - x1) * (y2 - y1))
                                print("fileName: {} LAMP Av. U value: {}".format(json_file_name,average))

                    if (entry['classTitle'] == 'Heating/cooling system'):
                        points = entry['points']
                        exterior = (points['exterior'])
                        x1 = exterior[0][0]
                        y1 = exterior[0][1]
                        x2 = exterior[1][0]
                        y2 = exterior[1][1]

                        # Need to get temperatures from csv
                        for fileName in os.listdir(filePath):
                            json_file_name = file.split(".")
                            csv_file_name = fileName.split(".")
                            if (csv_file_name[0].find(json_file_name[0]) != -1 and fileName.endswith(
                                    ".csv")):  # Finds similarly named json and csv files
                                # print("JSON: {} CSV: {}".format(json_file_name[0], csv_file_name[0]))
                                csv_file_path = filePath + "/" + fileName
                                with open(csv_file_path) as read_csv_file:
                                    csvData = csv.reader(read_csv_file, delimiter=',',
                                                         quotechar='|')  # Seperated by comma (hence csv)
                                    for i, data in enumerate(
                                            csvData):  # i holds the index and increments each loop while data holds cells value
                                        length = len(data)
                                        if (length == 0):  # Incase the length of a row is 0 (empty cells)
                                            continue
                                        else:
                                            index = length - 1  # Extract the last data point in the row
                                        if (i == 2):
                                            emissivity = float(data[index])
                                        if (i == 5):
                                            atmosphere = data[index]
                                            temp = atmosphere.split(" ")
                                            atmosphere_temperature = kelvinConvert(temp[0])
                                        if (i >= 10):
                                            pixil_temperature.append(data[
                                                                     1:])  # Pixel temperature now holds 512 indexes. Each index is a list of values for the whole row (0-511 rows)

                                # TODO: Writing back to CSV the u-values held in the list named u_value
                                total = 0
                                for x in range(x1, x2):
                                    for y in range(y1, y2):
                                        # u-value now holds the values of each pixel
                                        u_value = u_value_calculation(emissivity, atmosphere_temperature,
                                                                      wind_speed, indoor_temperature,
                                                                      (pixil_temperature[x][y]))
                                        u_values.append(u_value)
                                        total = total + u_value
                                        # print("x: {}, y: {}, value: {}".format(x, y, u_value))
                                # Calculate average
                                average = total / ((x2 - x1) * (y2 - y1))
                                print("fileName: {}  Heating Av. U value: {}".format(json_file_name,average))

                    if (entry['classTitle'] == 'Door'): #Doors use polygons (4 points)
                        points = entry['points']
                        exterior = (points['exterior'])
                        x1 = exterior[0][0]
                        y1 = exterior[0][1]
                        x2 = exterior[1][0]
                        y2 = exterior[1][1]
                        x3 = exterior[2][0]
                        y3 = exterior[2][1]
                        x4 = exterior[3][0]
                        y4 = exterior[3][1]

                        # Need to get temperatures from csv
                        for fileName in os.listdir(filePath):
                            json_file_name = file.split(".")
                            csv_file_name = fileName.split(".")
                            if (csv_file_name[0].find(json_file_name[0]) != -1 and fileName.endswith(
                                    ".csv")):  # Finds similarly named json and csv files
                                # print("JSON: {} CSV: {}".format(json_file_name[0], csv_file_name[0]))
                                csv_file_path = filePath + "/" + fileName
                                with open(csv_file_path) as read_csv_file:
                                    csvData = csv.reader(read_csv_file, delimiter=',',
                                                         quotechar='|')  # Seperated by comma (hence csv)
                                    for i, data in enumerate(
                                            csvData):  # i holds the index and increments each loop while data holds cells value
                                        length = len(data)
                                        if (length == 0):  # Incase the length of a row is 0 (empty cells)
                                            continue
                                        else:
                                            index = length - 1  # Extract the last data point in the row
                                        if (i == 2):
                                            emissivity = float(data[index])
                                        if (i == 5):
                                            atmosphere = data[index]
                                            temp = atmosphere.split(" ")
                                            atmosphere_temperature = kelvinConvert(temp[0])
                                        if (i >= 10):
                                            pixil_temperature.append(data[
                                                                     1:])  # Pixel temperature now holds 512 indexes. Each index is a list of values for the whole row (0-511 rows)

                                #Find all points within polygon
                                r = np.array([x1, x2, x3, x4])
                                c = np.array([y1, y2, y3, y4])
                                x_axis, y_axis = draw.polygon(r, c)

                                # TODO: Writing back to CSV the u-values held in the list named u_value
                                total = 0
                                counter = 0
                                while(counter < len(x_axis)): #Calculate u-value within the range of the polygon
                                    u_value = u_value_calculation(emissivity, atmosphere_temperature,
                                                                  wind_speed, indoor_temperature,
                                                                  (pixil_temperature[x_axis[counter]][y_axis[counter]]))
                                    u_values.append(u_value)
                                    total = total + u_value
                                    counter += 1

                                # Calculate average
                                print("u-value: {} total: {}".format(total, counter))
                                average = total / ((x3 - x1) * (y3 - y1))
                                print("fileName: {} Door Av. U value: {}".format(json_file_name,average))


def loadCSVData(filePath):
    '''
    This function will take the go through each file ending in .csv within the folder and gather the emissivity and atmosphere temperature.
    Then once we hit the cells related to the pixel temperatures, the values are read and saved into the pixil_temperature list.
    :param filePath: Path to the folder containing .csv files
    :return: None.
    '''
    global emissivity, atmosphere_temperature, pixil_temperature, wind_speed
    for file in os.listdir(filePath): #going through each file in the directory passed
        if(file.endswith(".csv")): #Check to ignore all non-csv files
            path = filePath + "/" + file
            with open(path) as csvFile:
                csvData = csv.reader(csvFile, delimiter=',', quotechar='|') #Seperated by comma (hence csv)
                for i, data in enumerate(csvData): #i holds the index and increments each loop while data holds cells value
                    length = len(data)
                    if (length == 0):  # Incase the length of a row is 0 (empty cells)
                        continue
                    else:
                        index = length - 1  # Extract the last data point in the row
                    if (i == 2):
                        emissivity = float(data[index])
                    if (i == 5):
                        atmosphere = data[index]
                        temp = atmosphere.split(" ")
                        atmosphere_temperature = kelvinConvert(temp[0])
                    if (i >= 10):
                        pixil_temperature.append(data[1:])  #Pixel temperature now holds 512 indexes. Each index is a list of values for the whole row (0-511 rows)

            #Iterating through each pixel and calculating u-values

            #TODO: Writing back to CSV the u-values held in the list named u_value
            for x in range(512):
                for y in range(640):
                    # u-value now holds the values of each pixel
                    u_value = u_value_calculation(emissivity, atmosphere_temperature, wind_speed, indoor_temperature, (pixil_temperature[x][y]))
                    u_values.append(u_value)
                    #print("x: {}, y: {}, value: {}".format(x, y, u_value))

            for z in enumerate(u_values):
                 print(z)

def u_value_calculation(emissivity, atmosphere, wind_speed, indoor_temperature, pixil_temperature):
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
    Ev = emissivity
    sigma = 5.67 #Constant
    Tw = kelvinConvert(pixil_temperature)
    Tout = atmosphere
    v = wind_speed
    Tin = indoor_temperature

    numerator = Ev * (sigma * (((Tw/100)**4) - ((Tout/100) ** 4))) + 3.805 * (v * (Tw - Tout))
    denominator = Tin - Tout

    return(numerator/denominator)

def main():

    loadData()
    loadJSONData(filePath, jsonFilePath)

if __name__ == "__main__":
    main()
