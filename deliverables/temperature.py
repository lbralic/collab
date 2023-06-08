# Date last updated: June 8, 2023

# Purpose:
# Processes the temperature data and uploads it to ArcGIS Online (AGOL) as a feature layer.
# The feature layer will contain a station point layer and a data table.
#   TempModel() >> Temperature data processing model
#   GDBToMap() >> Add all feature classes and tables to the map display
#   GOLUpload() >> Upload all layers and tables to AGOL

# Instructions:
#   Under "Required inputs", enter the file/folder paths
#   Under "Optional inputs", enter the name of the feature layer to be uploaded to AGOL,
#       the summary/tags/etc., and the sharing preferences.

#############################################
#####               INPUTS              #####
#############################################

############## Required inputs ##############

# >>> File/folder paths
# Path to the folder that contains the TempMonitoring Excel file
input_Temp_Table = r"C:\Data"
# Path to the output TempMonitoring folder - the folder where the csv files are placed
output_Temp_Table = r"C:\Output"
# Path to geodatabase 
ws = r"C:\Project\Project.gdb"
# Path to .aprx file 
aprx_path = r"C:\Project\Project.aprx"
# Empty output folder for the service definition drafts
outdir = r"C:\Output"

# >>> Enter the names of the excel files/ sheets if they are different  
# Change the keys (left hand side) of this dictionary to match the names of the sheets in the .xlsx file to the names of the tables (right hand side)
data_names_for_sheet_names = {
    "Coldwater Streams - metadata": "TemperatureMonitoringXYData",
    "ColdwaterStreams": "TemperatureMonitoringData"
}


############## Optional inputs ##############

# >>> Input the name of the feature layer to be uploaded to AGOL
service_name = "Kawartha Conservation Temperature Data"

# >>> Enter the summary, tags, etc. that will appear on AGOL
mysummary = "My Summary"
mytags = "My Tags"
mydescription = "My Description"
mycredits = "My Credits"
myuselimitations = "My Use Limitations"

# >>> Alter sharing preferences
# Sharing options
sharepublic = "PRIVATE"                 # Enter "PUBLIC" or "PRIVATE"
shareorg = "NO_SHARE_ORGANIZATION"      # Enter "SHARE_ORGANIZATION" or "NO_SHARE_ORGANIZATION"
sharegroup = ""                         # Enter the name of the group(s): "My Group" or ["My Group 1", "My Group 2", ...]
# AGOL folder name
foldertype = ""                         # Enter "Existing" to specify an existing folder
foldername = ""                         # Enter the existing AGOL folder name

########################################################################################


import arcpy, os, pandas as pd

# Coordinate system
coordsys = "PROJCS[\"NAD_1983_CSRS_UTM_Zone_17N\",GEOGCS[\"GCS_North_American_1983_CSRS\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-81.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]"

arcpy.env.overwriteOutput = True

# Remove layers and tables from map view
aprx = arcpy.mp.ArcGISProject(aprx_path)
maps = aprx.listMaps()
if len(maps) == 0:
    raise ValueError("       No map found!  Make sure the ArcGIS project has a map in it.")
m = maps[0] 
table_list = m.listTables()
for tbl in table_list:
    m.removeTable(tbl)
fc_list = m.listLayers()
for fc in fc_list:
    m.removeLayer(fc)
aprx.save()

#############################################
#####        HELPER FUNCTIONS           #####
#####   can be used for any data set    #####
#############################################

# Excel File Data Pre-Processing - makes .xslx file into .csvs and removes any spaces from field names.
def xlsx_sheets_to_csv(path_to_excel_file, output_folder):
    for sheet_name, df in pd.read_excel(path_to_excel_file, index_col=0, sheet_name=None).items():
        csv_file = os.path.join(output_folder, f"{sheet_name}.csv")
        # Remove spaces in field names
        df.index.name = df.index.name.replace(" ", "")  
        df.to_csv(csv_file, encoding='utf-8')

# Add the specified feature classes and tables to the map display 
# e.g. GDBToMap(["TemperatureMonitoringPoints"], ["TemperatureMonitoringData", "AnotherTable"])
def GDBToMap(fcs, tables):
    print(">> Adding data to map...")
    # Add stations (point layer)
    print("       Adding stations")
    for fc in fcs:
        arcpy.management.MakeFeatureLayer(fc, fc)
        lyr_name = "{}.lyrx".format(fc)
        arcpy.management.SaveToLayerFile(fc, lyr_name)
        lyr_path = os.path.join(os.path.dirname(ws), lyr_name)
        lyr = arcpy.mp.LayerFile(lyr_path)
        m.addLayer(lyr)
    # Add data (table)
    print("       Adding table")
    for table in tables:
        table_path = os.path.join(ws, table)
        addTab = arcpy.mp.Table(table_path)
        m.addTable(addTab)
        aprx.save()

# Upload all layers and tables to ArcGIS Online
def AGOLUpload(service_name):  # service_name is the name of the feature layer to be uploaded to AGOL
    print(">> Uploading to ArcGIS Online...")
    # Source: 
    # https://pro.arcgis.com/en/pro-app/latest/arcpy/sharing/featuresharingdraft-class.htm
    # https://pro.arcgis.com/en/pro-app/latest/tool-reference/server/stage-service.htm

    # Set output file names
    sddraft_filename = service_name + ".sddraft"
    sddraft_output_filename = os.path.join(outdir, sddraft_filename)
    sd_filename = service_name + ".sd"
    sd_output_filename = os.path.join(outdir, sd_filename)

    # Delete existing files
    print("       Deleting existing files...")
    if os.path.exists(sddraft_output_filename):
        os.remove(sddraft_output_filename)
    if os.path.exists(sd_output_filename):
        os.remove(sd_output_filename)

    # Reference layers to publish
    lyr_list = []               # List layers and tables
    lyrs = m.listLayers()       # List layers
    tables = m.listTables()     # List tables
    count_lyrs = len(lyrs)
    for x in range(count_lyrs):
        lyr_list.append(lyrs[x])
    count_tables = len(tables)
    for x in range(count_tables):
        lyr_list.append(tables[x])

    # Create FeatureSharingDraft and enable overwriting
    server_type = "HOSTING_SERVER"
    # Parameters: getWebLayerSharingDraft(server_type, service_type, service_name, {layers_and_tables})
    sddraft = m.getWebLayerSharingDraft(server_type, "FEATURE", service_name, lyr_list)
    sddraft.summary = mysummary
    sddraft.tags = mytags
    sddraft.description = mydescription
    sddraft.credits = mycredits
    sddraft.useLimitations = myuselimitations
    sddraft.overwriteExistingService = True

    # Create Service Definition Draft file
    # Parameters: exportToSDDraft(out_sddraft)
    sddraft.exportToSDDraft(sddraft_output_filename)

    # Stage Service
    print("       Start Staging")
    # Parameters: arcpy.server.StageService(in_service_definition_draft, out_service_definition, {staging_version})
    arcpy.server.StageService(sddraft_output_filename, sd_output_filename)

    # Share to portal
    # Documentation: https://pro.arcgis.com/en/pro-app/latest/tool-reference/server/upload-service-definition.htm
    inOverride = "OVERRIDE_DEFINITION"
    # Sharing options
    inSharePublic = sharepublic
    inShareOrg = shareorg
    inShareGroup = sharegroup
    # AGOL folder name
    inFolderType = foldertype
    inFolderName = foldername

    print(">> Start Uploading")
    # Parameters: arcpy.server.UploadServiceDefinition(in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type}, {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
    arcpy.server.UploadServiceDefinition(sd_output_filename, server_type, "", "", inFolderType, inFolderName, "", inOverride, "", inSharePublic, inShareOrg, inShareGroup)

    print(">> Finish Publishing")

    # Delete tables and layers from the map view
    table_list = m.listTables()
    for tbl in table_list:
        m.removeTable(tbl)
    fc_list = m.listLayers()
    for fc in fc_list:
        m.removeLayer(fc)
    aprx.save()


#############################################
#####     DATA-SPECIFIC FUNCTIONS       #####
#####     for coldwater temp data       #####
#############################################

# Temperature Monitoring Data Processing
#  data_names_for_sheet_names is a dictionary where the keys are the names of the .csv files (which are named the same as the sheets in the .xslx files) and the values are the names we assign to the data
def TempModel(data_names_for_sheet_names):
    print(">> Processing the Temperature Monitoring data...")
    
    ##### Extract .csv files from all the .xlsx files #####
    files_in_xlsx_folder = os.listdir(input_Temp_Table)
    print("       Processing the Excel table") 
    for filename in files_in_xlsx_folder:
        # skip anything in the folder that isn't a .xlsx
        if filename.endswith(".xlsx") == False:
            continue  # skips to the next file in the loop
        xlsx_sheets_to_csv(input_Temp_Table + "/" + filename, output_Temp_Table)

    print("       The .xlsx files have been converted to .csv files.")
    
    ##### Load all the .csv files into arcpy tables #####
    files_in_data_folder = os.listdir(output_Temp_Table)
    for filename in files_in_data_folder:
        # take the ".csv" off the filename, and then get our name for that sheet's data
        sheet_name = os.path.splitext(filename)[0]
        # skip anything in the folder that isn't a .csv
        if (filename.endswith(".csv") == False) or (sheet_name not in list(data_names_for_sheet_names.keys())):
            continue  # skips to the next file in the loop
        
        out_table_name = data_names_for_sheet_names[sheet_name]

        arcpy.conversion.ExportTable(output_Temp_Table + "/" + filename, out_table_name)  
        print("       Created table " + out_table_name)

    #### Add a field for the date and calculate it using the Row Labels and Year Fields 
    arcpy.management.AddField("TemperatureMonitoringData", "Date", "DATE")
    arcpy.management.AddField("TemperatureMonitoringData", "textDate", "TEXT")

    expression_coldwater_date = "calcDate(!Row_Labels!, !Year!)"
    codeblock_coldwater_date = """
def calcDate(month, year):
    monthDictionary = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    dateString = str(int(year)) + "/" + monthDictionary[month] + "/01 12:00:00"
    return dateString
    """

    expression_coldwater_textDate = "calcDate(!Row_Labels!, !Year!)"
    codeblock_coldwater_textDate = """
def calcDate(month, year):
    dateString = month + " " + str(int(year))
    return dateString
"""

    #### Calculate the new date field 
    arcpy.management.CalculateField("TemperatureMonitoringData", "Date", expression_coldwater_date, code_block = codeblock_coldwater_date)
    arcpy.management.CalculateField("TemperatureMonitoringData", "textDate", expression_coldwater_textDate, code_block = codeblock_coldwater_textDate)

    #### Delete the unnecessary fields in TemperatureMonitoringData
    arcpy.management.DeleteField("TemperatureMonitoringData", ["Year","Row_Labels"], "DELETE_FIELDS")


    #### Create the Point Class
    arcpy.management.XYTableToPoint("TemperatureMonitoringXYData", "TemperatureMonitoringPoints", "Easting", "Northing", coordinate_system="NAD 1983 UTM Zone 17N")
    print("       The feature class TemperatureMonitoringPoints has been updated.")


    #### Create a Relationship Class 
    # Parameters: arcpy.management.CreateRelationshipClass(point_table, data_table, name_of_relationshipClass, "Composite", data_table_name, points_name, "FORWARD", "ONE_TO_MANY", "NONE", "the_common_field_SiteCode", "the_common_field")
    arcpy.management.CreateRelationshipClass("TemperatureMonitoringPoints", "TemperatureMonitoringData", "TemperatureMonitoringPoints_TemperatureMonitoringData", "Composite", "TemperatureMonitoringData", "TemperatureMonitoringPoints", "FORWARD", "ONE_TO_MANY", "NONE", "SiteCode", "SiteCode")

    print("       The relationship class has been updated.")


if __name__ == '__main__':
    # Global Environment settings
    with arcpy.EnvManager(outputCoordinateSystem = coordsys, scratchWorkspace = ws, workspace = ws):
        TempModel(data_names_for_sheet_names)
        GDBToMap(["TemperatureMonitoringPoints"], ["TemperatureMonitoringData"])
        AGOLUpload(service_name)
