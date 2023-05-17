import arcpy
import os
import re
import pandas as pd

###########################################################################################
##### Edit this depending on the user's computer and where they are keeping the files #####
###########################################################################################
xlsx_folder_path = r"C:\Winter2023\COLLAB\Data"
data_folder_path = r"C:\Winter2023\COLLAB\test"
ws = r"C:\Winter2023\COLLAB\test\test_fgdb.gdb"


def xlsx_sheets_to_csv(xlsx_folder_path, data_folder_path):
    '''
    This function reads the .xlsx file located at 'xlsx_folder_path' and saves each individual worksheet from that file as separate .csv files in the folder located at 'data_folder_path'
    It also does some renaming because we don't want spaces in any field names.

    # Documentation: 
    # Read Excel file - https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
    # Convert to .csv - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

    # https://stackoverflow.com/questions/71605777/how-to-convert-multiple-sheets-in-an-excel-workbook-to-csv-files-in-python

    '''
    for sheet_name, df in pd.read_excel(xlsx_folder_path, index_col=0, sheet_name=None).items():
        csv_file = os.path.join(data_folder_path, f"{sheet_name}.csv")
        df.index.name = df.index.name.replace(" ", "")  # don't let there be a space in the field name (this only does the first column of the table but that's all we need for now - for the 'Site Code' that we use for a join)
        df.to_csv(csv_file, encoding='utf-8')


##### Set up the workspace #####
arcpy.env.workspace = ws
arcpy.env.overwriteOutput = True




##### Extract .csv files from all the .xlsx files #####
files_in_xlsx_folder = os.listdir(xlsx_folder_path)
for filename in files_in_xlsx_folder:
    # skip anything in the folder that isn't a .xlsx
    if not filename.endswith(".xlsx"):
        continue  # skips to the next file in the loop
    xlsx_sheets_to_csv(xlsx_folder_path + "/" + filename, data_folder_path)


##### Load all the .csv files into arcpy tables #####
files_in_data_folder = os.listdir(data_folder_path)
for filename in files_in_data_folder:
    # skip anything in the folder that isn't a .csv
    if not filename.endswith(".csv"):
        continue  # skips to the next file in the loop

    # take the ".csv" off the filename, and then "clean" the name by removing any non-word characters
    out_table_name = os.path.splitext(filename)[0]
    clean_out_table_name = re.sub(r"[^\w]", "", out_table_name) # re = regular expression - replace any "non-word" character with "" to remove them. 
    # https://docs.python.org/3/library/re.html 

    arcpy.conversion.ExportTable(data_folder_path + "/" + filename, clean_out_table_name)  # https://pro.arcgis.com/en/pro-app/latest/tool-reference/conversion/export-table.htm


##### Special Processing for Biomonitoring Data - add Family Biotic Index Category field #####

# Replace "Family_Biotic_Index__Value_" with the name of the input field
expression = "calcCategory(float(!Family_Biotic_Index__Value_!))"
codeblock = """
def calcCategory(value):
    if value <= 3.75:
        return "Excellent"
    if value > 3.75 and value <= 4.25:
        return "Very Good"
    if value > 4.25 and value <= 5:
        return "Good"
    if value > 5 and value <= 5.75:
        return "Fair"
    if value > 5.75 and value <= 6.5:
        return "Fairly Poor"
    if value > 6.5 and value <= 7.25:
        return "Poor"
    if value > 7.25 and value <= 10:
        return "Very Poor"
    else:
        return "N/A"
"""
# Replace "Family_Biotic_Index__Category_" with the name of the output field, if necessary
arcpy.management.CalculateField("Biomonitoring", "Family_Biotic_Index__Category_", expression, code_block = codeblock)  # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/calculate-field.htm


##### Special Processing  for Coldwater Data - join with Coldwater Streams Metadata to get the location of every site #####
arcpy.management.JoinField("ColdwaterStreams", "SiteCode", "ColdwaterStreamsmetadata", "SiteCode", ["Easting", "Northing", "Watercourse"])

##### Turn the tables into feature classes #####
arcpy.management.XYTableToPoint("ColdwaterStreams", "ColdwaterStreams_points", "Easting", "Northing", coordinate_system="NAD 1983 UTM Zone 17N")
arcpy.management.XYTableToPoint("Biomonitoring", "Biomonitoring_points", "Easting", "Northing", coordinate_system="NAD 1983 UTM Zone 17N")