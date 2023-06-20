# Date last updated: June 8, 2023

# Purpose:
# Processes the Biomonitoring data and uploads it to ArcGIS Online (AGOL) as a feature layer.
# The feature layer will contain a station point layer and a data table.
#   BioModel() >> Biomonitoring data processing model
#   GDBToMap() >> Add all feature classes and tables to the map display
#   GOLUpload() >> Upload all layers and tables to AGOL

# Instructions:
#   Under "Required inputs", enter the file/folder paths.
#   Under "Optional inputs", enter the name of the feature layer to be uploaded to AGOL,
#       the summary/tags/etc., and the sharing preferences.

#############################################
#####               INPUTS              #####
#############################################

############## Required inputs ##############

# >>> File/folder paths
# Path to Biomonitoring .xlsx file
input_BM_table = r"C:\Data\Biomonitoring Data for Dashboard)-June2,2023.xlsx"
# Path to geodatabase
ws = r"C:\Project\Project.gdb"
# Path to .aprx file
aprx_path = r"C:\Project\Project.aprx"
# Empty output folder for the service definition drafts
outdir = r"C:\Output"


############## Optional inputs ##############

# >>> Input the name of the feature layer to be uploaded to AGOL
service_name = "Kawartha Conservation Biomonitoring Data"

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

# >>> Enter the URLS for the site photos {Site_Code : URL}
StationList = {"ASD01" : "https://fleming.maps.arcgis.com/home/item.html?id=fd7803f0164a4a7aa3d32a249dadd2d6",
              "BMI_PR-001" : "https://fleming.maps.arcgis.com/home/item.html?id=2956d805298349d6a60634ba0b5f6047",
              "CC1" : "https://fleming.maps.arcgis.com/home/item.html?id=e63f5ffddc3f45d7bb8d96543db4a2c4",
              "CRL1" : "https://fleming.maps.arcgis.com/home/item.html?id=760c792e709f4ad1ba70569bc483b33f",
              "DIST01" : "https://fleming.maps.arcgis.com/home/item.html?id=fa763fd84f17416fa078a9171f40e91b",
              "FEN01" : "https://fleming.maps.arcgis.com/home/item.html?id=82e9a95598544fea9b1d8fdd45141877",
              "JC2" : "https://fleming.maps.arcgis.com/home/item.html?id=d5bb9198e0524c57b33375cd13287f35",
              "KENREID01" : "https://fleming.maps.arcgis.com/home/item.html?id=03c43a512af84bc7adba60a86cc5da7a",
              "OME01" : "https://fleming.maps.arcgis.com/home/item.html?id=bc55c67d9683455d8998c8cefd46e43d",
              "PL234-22" : "https://fleming.maps.arcgis.com/home/item.html?id=d1efe0cc5b744264bcbb5d77462dbb45",
              "PLMP-01" : "https://fleming.maps.arcgis.com/home/item.html?id=deaa59f6cd7a4324a94a9caaaf741afc",
              "SIN01" : "https://fleming.maps.arcgis.com/home/item.html?id=19e010dd7b60450e96c0ef732bffbd95",
              "SUC02" : "https://fleming.maps.arcgis.com/home/item.html?id=112a7451740342c382643613e5e64463",
              "UEC6" : "https://fleming.maps.arcgis.com/home/item.html?id=0ff553ef18cc43b9855054912e128ab4",
              "URB-020" : "https://fleming.maps.arcgis.com/home/item.html?id=df7f7b68cb52431c9390467daad0e6a7",
              "URB-030" : "https://fleming.maps.arcgis.com/home/item.html?id=3f279459e04640958d96f1262ad85d10",
              "URB-088" : "https://fleming.maps.arcgis.com/home/item.html?id=ba293352e117499782cf19571357b77d",
              }


########################################################################################


import arcpy, os, pandas as pd

# Coordinate system
coordsys = "PROJCS[\"NAD_1983_CSRS_UTM_Zone_17N\",GEOGCS[\"GCS_North_American_1983_CSRS\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-81.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]"

arcpy.env.overwriteOutput = True

# Remove layers and tables from map view
print(">> Removing existing layers from map view...")
aprx = arcpy.mp.ArcGISProject(aprx_path)
m = aprx.listMaps()[0] 
table_list = m.listTables()
for tbl in table_list:
    m.removeTable(tbl)
fc_list = m.listLayers()
for fc in fc_list:
    m.removeLayer(fc)
aprx.save()

def BioModel():
    print(">> Processing the Biomonitoring data...")

    # Importing data(xlsx to csv):
    print("\tConverting the Excel file to .csv")
    # csv file path
    csvname = "Biomonitoring_Data"
    csvname_ext = csvname + ".csv"
    csvfilepath = os.path.join(outdir, csvname_ext)
    # Reading an excel file
    excelFile = pd.read_excel (input_BM_table, sheet_name="Biomonitoring")
    # Converting excel file into CSV file
    excelFile.to_csv(csvfilepath, index = None, header=True)
    # Reading and Converting the output csv file into a dataframe object
    df = pd.DataFrame(pd.read_csv(csvfilepath))
    # Displaying the dataframe object
    df.columns=df.columns.str.replace(' ', '_') # replace space with underscore
    df.columns = df.columns.str.replace(r'\W+', '', regex = True) # delete non-word character
    df.to_csv(csvfilepath, encoding = 'utf-8-sig')
    # copy the csv file to geodatabase
    arcpy.conversion.ExportTable(csvfilepath, csvname)


    # Biomonitoring stations:
    print("\tCreating station points")
    # Convert the table to a point feature class
    BM_Stations = "Biomonitoring_Stations"
    arcpy.management.XYTableToPoint(csvname, BM_Stations, "Easting", "Northing", "", coordsys)
    # Delete duplicate site codes
    arcpy.management.DeleteIdentical(BM_Stations, "Site_Code")
    # Only keep the fields that contain the basic station information
    field_list = arcpy.ListFields(BM_Stations)
    field_list_delete = []
    for field in field_list:
        if field.baseName != "OBJECTID" and field.baseName != "Shape" and field.baseName != "Watercourse" and field.baseName != "Site_Code" and field.baseName != "Site_Type" and field.baseName != "Habitat_Type":
            field_list_delete.append(field.baseName)
    arcpy.management.DeleteField(BM_Stations, drop_field=field_list_delete)

    # Add photos to station points
    print("\tAdding photos")
    # Create a new text field
    arcpy.management.AddField(BM_Stations, "Photo", "TEXT")
    for station in StationList:
        station_where = "Site_Code = " + "'" + station + "'"
        BM_SelectStation = arcpy.management.SelectLayerByAttribute(BM_Stations, where_clause=station_where)
        station_calc = "'" + StationList.get(station) + "'"
        arcpy.management.CalculateField(BM_SelectStation, "Photo", station_calc)

    
    # Domains:
    print("\tCreating domains")
    # Create coded domain
    desc_ws = arcpy.Describe(ws)
    desc_domains = desc_ws.domains
    # Assign domain name
    domainname_FBI = "FBIndexCat"
    domainname_SO="SenOrgCat"
    infield_SO="Sensitive_Organisms_Category"
    infield_FBI="Family_Biotic_Index_Category"
    # coded value dictionary
    domDict_SO={"A":"Above Average", "B":"Below Average", "AVG":"Average"}
    domDict_FBI={"E":"Excellent", "VG":"Very Good", "G":"Good","F":"Fair","FP":"Fairly Poor","P":"Poor","VP":"Very Poor"}
    # Check if the domain exists
    if domainname_SO not in desc_domains:
        # Create Domain
        arcpy.management.CreateDomain(ws, domainname_SO, "Sensitive Organism Category", "TEXT", "CODED")[0]
    for code in domDict_SO:
        # Assign coded value to domain
        arcpy.management.AddCodedValueToDomain(ws, domainname_SO, code, domDict_SO[code])[0]
    # Assign domain to field    
    arcpy.AssignDomainToField_management(csvname, infield_SO, domainname_SO)[0]
    # Repeat for the second coded domain
    if domainname_FBI not in desc_domains:
        arcpy.management.CreateDomain(ws, domainname_FBI, "FamilyBioticIndex Category", "TEXT", "CODED")[0]
        for code2 in domDict_FBI:
            arcpy.management.AddCodedValueToDomain(ws, domainname_FBI, code2, domDict_FBI[code2])[0]
    arcpy.AssignDomainToField_management(csvname, infield_FBI, domainname_FBI)[0]

    # Add new field(Family Biotic Index Value), type DOUBLE. The original field is TEXT. 
    arcpy.AddField_management(csvname, "FamilyBioticIndex_Value", "DOUBLE", field_length = 20)
    arcpy.management.CalculateField(csvname, "FamilyBioticIndex_Value", "!Family_Biotic_Index_Value!")
    # delete field **
    arcpy.management.DeleteField(csvname, ["Family_Biotic_Index_Value", "Field1"])

    #**in Arcade, Null returns 0. When inserting a new row, and when FamilyBioticIndex Value field is Null, it will return 'Excellent' in the category field. An option to solve this is excluding 0 in the following calculation rule. eg. if ($feature.FamilyBioticIndex_Value > 0)
    ###Calculation rules, automate category based on value
    print("\tCreating attribute rules")
    # Create Global ID for attribute rules
    arcpy.management.AddGlobalIDs(csvname)
    # Create attribute rule(CALCULATION) for Family Biotic Index
    name = "FBI_calculateRuleCategory"
    script_expression = 'if ($feature.FamilyBioticIndex_Value >= 0 && $feature.FamilyBioticIndex_Value <= 3.75) {return "Excellent"} else if ($feature.FamilyBioticIndex_Value > 3.75 && $feature.FamilyBioticIndex_Value <= 4.25) {return "Very Good"} else if ($feature.FamilyBioticIndex_Value > 4.25 && $feature.FamilyBioticIndex_Value <= 5) {return "Good"} else if ($feature.FamilyBioticIndex_Value > 5 && $feature.FamilyBioticIndex_Value <= 5.75) {return "Fair"} else if ($feature.FamilyBioticIndex_Value > 5.75 && $feature.FamilyBioticIndex_Value <= 6.5) {return "Fairly Poor"} else if ($feature.FamilyBioticIndex_Value > 6.5 && $feature.FamilyBioticIndex_Value <= 7.25) {return "Poor"} else if ($feature.FamilyBioticIndex_Value > 7.25 && $feature.FamilyBioticIndex_Value <= 10) {return "Very Poor"} else {return null}'
    triggering_events = "INSERT;UPDATE"
    description = "Populate Catogory Based on Value"
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name, "CALCULATION", script_expression, "EDITABLE", triggering_events, "", "", description, "", infield_FBI)

    # Create attribute rule(CALCULATION) for Sensitive Organisms
    name3 = "SO_calculateRuleCategory"
    script_expression3 = 'if ($feature.Sensitive_Organisms_ > 20.9) {return "Above Average"} else if ($feature.Sensitive_Organisms_ > 0 && $feature.Sensitive_Organisms_ < 20.9 ) {return "Below Average"} else if ($feature.Sensitive_Organisms_ == 20.9 ) {return "Average"} else{return null}'
    triggering_events = "INSERT;UPDATE"
    description3 = "Populate Catogory Based on Value"
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name3, "CALCULATION", script_expression3, "EDITABLE", triggering_events, "", "", description3, "", infield_SO)
    
    ###Constraint rules, limit values to be entered
    # Create attribute rule(CONSTRAINT) for Family Biotic Index
    name2 = "FBConstraintRule"
    script_expression2 = '$feature.FamilyBioticIndex_Value >= 0  && $feature.FamilyBioticIndex_Value <= 10'
    triggering_events = "INSERT;UPDATE"
    description2 = "Constraint rule, prevent value from out of range: Family Biotic Index Value range from 0 to 10"
    subtype = "ALL"
    error_number = 2001
    error_message = "Invalid Family Biotic Index Value. Must be greater than or equal to 0; or less than or equal to 10."
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name2, "CONSTRAINT", script_expression2, "EDITABLE", triggering_events, error_number, error_message, description2, subtype)

    # Create attribute rule(CONSTRAINT) for sensitive organism
    name4 = "SOConstraintRule"
    script_expression4 = '$feature.Sensitive_Organisms_ >= 0 && $feature.Sensitive_Organisms_ <= 100'
    triggering_events = "INSERT;UPDATE"
    description4 = "Constraint rule, prevent value from out of range: 0 - 100"
    subtype = "ALL"
    error_number2 = 2002
    error_message2 = "Invalid Sensitive Organism Value. Must be greater than or equal to 0; or less than and equal to 100."
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name4, "CONSTRAINT", script_expression4, "EDITABLE", triggering_events, error_number2, error_message2, description4, subtype)

# Add all feature classes and tables to the map display
def GDBToMap():
    print(">> Adding data to map...")
    print("\tAdding stations")
    # Add stations (point layer)
    fc = "Biomonitoring_Stations"
    arcpy.management.MakeFeatureLayer(fc, fc)
    lyr_name = "{}.lyrx".format(fc)
    arcpy.management.SaveToLayerFile(fc, lyr_name)
    lyr_path = os.path.join(os.path.dirname(ws), lyr_name)
    lyr = arcpy.mp.LayerFile(lyr_path)
    m.addLayer(lyr)
    # Add data (table)
    print("\tAdding table")
    table = "Biomonitoring_Data"
    table_path = os.path.join(ws, table)
    addTab = arcpy.mp.Table(table_path)
    m.addTable(addTab)
    aprx.save()

# Upload all layers and tables to ArcGIS Online
def AGOLUpload():
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
    print("\tDeleting existing files...")
    if os.path.exists(sddraft_output_filename):
        os.remove(sddraft_output_filename)
    if os.path.exists(sd_output_filename):
        os.remove(sd_output_filename)

    # Reference layers to publish
    # aprx = arcpy.mp.ArcGISProject(aprx_path)
    # m = aprx.listMaps()[0]      # Specify the name of the map if necessary
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
    print("\tStart Staging")
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
    print("\tStart Uploading")

    # Parameters: arcpy.server.UploadServiceDefinition(in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type}, {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
    arcpy.server.UploadServiceDefinition(sd_output_filename, server_type, "", "", inFolderType, inFolderName, "", inOverride, "", inSharePublic, inShareOrg, inShareGroup)

    print("\tFinish Publishing")

    # Delete tables and layers from the map view
    table_list = m.listTables()
    for tbl in table_list:
        m.removeTable(tbl)
    fc_list = m.listLayers()
    for fc in fc_list:
        m.removeLayer(fc)
    aprx.save()

if __name__ == '__main__':
    # Global Environment settings
    with arcpy.EnvManager(outputCoordinateSystem = coordsys, scratchWorkspace = ws, workspace = ws):
        BioModel()
        GDBToMap()
        AGOLUpload()
