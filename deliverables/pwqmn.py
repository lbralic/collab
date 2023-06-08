# Date last updated: June 8, 2023

# Purpose:
# Processes the PWQMN data and uploads it to ArcGIS Online (AGOL) as a feature layer.
# The feature layer will contain a station point layer and a data table.
#   PWQMNModel() >> PWQMN data processing model
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
# Path to PWQMN Excel file
input_PWQMN_table = r"C:\Data\2023-04-11_PWQMNdata_GISDashboard.xlsx"
# Path to geodatabase
ws = r"C:\Project\Project.gdb"
# Path to .aprx file
aprx_path = r"C:\Project\Project.aprx"
# Empty output folder for the service definition drafts
outdir = r"C:\Output"


############## Optional inputs ##############

# >>> Input the name of the feature layer to be uploaded to AGOL
service_name = "Kawartha Conservation PWQMN Data"

# >>> Enter the summary, tags, etc. that will appear on AGOL
mysummary = "My Summary"
mytags = "My Tags"
mydescription = "My Description"
mycredits = "My Credits"
myuselimitations = "My Use Limitations"

# >>> Alter sharing preferences
# Sharing options
sharepublic = "PUBLIC"                  # Enter "PUBLIC" or "PRIVATE"
shareorg = "NO_SHARE_ORGANIZATION"      # Enter "SHARE_ORGANIZATION" or "NO_SHARE_ORGANIZATION"
sharegroup = "Kawartha Conservation Collaborative Project"                         # Enter the name of the group(s): "My Group" or ["My Group 1", "My Group 2", ...]
# AGOL folder name
foldertype = "Existing"                         # Enter "Existing" to specify an existing folder
foldername = "Collab"                         # Enter the existing AGOL folder name

# >>> Enter the URLS for the site photos
StationList = {"Balsam Lake Outlet" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Blackstock Creek" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Burnt River" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Cameron Lake Outlet" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Gull River" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Mariposa Brook" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Nonquon River" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Pigeon River" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Scugog River Down" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Scugog River Up" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg",
"Sturgeon Lake Outlet" : "https://www.kawarthaconservation.com/en/images/structure/news_avatar.jpg"}

########################################################################################


import arcpy, os

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

# PWQMN Data Processing
def PWQMNModel():
    print(">> Processing the PWQMN data...")

    # Import the Excel file to the gdb with the name PWQMN
    # Parameters: arcpy.conversion.ExcelToTable(Input_Excel_File, Output_Table, {Sheet}, {field_names_row}, {cell_range})
    arcpy.conversion.ExcelToTable(input_PWQMN_table, "PWQMN")

    # Convert all site descriptions to the same case (proper case)
    PWQMN_raw = "PWQMN"
    arcpy.management.CalculateField(PWQMN_raw, field="BOW_SITE_DESC", expression="!BOW_SITE_DESC!.title()")[0]

    print("\tCreating station points")
    # Create a PWQMN_Stations feature class from the imported Excel file
    PWQMN_Stations = "PWQMN_Stations"
    # Convert the table to a point feature class
    arcpy.management.XYTableToPoint(PWQMN_raw, PWQMN_Stations, "East", "North", "", coordsys)
    # Delete duplicate site codes
    arcpy.management.DeleteIdentical(PWQMN_Stations, "Station__")
    # Only keep the fields that contain the basic station information
    field_list = arcpy.ListFields(PWQMN_Stations)
    field_list_delete = []
    for field in field_list:
        if field.baseName != "OBJECTID" and field.baseName != "Shape" and field.baseName != "Station__" and field.baseName != "BOW_SITE_DESC" and field.baseName != "SAMPLE_PT_DESC_1":
            field_list_delete.append(field.baseName)
    arcpy.management.DeleteField(PWQMN_Stations, drop_field=field_list_delete)

    # Add photos to station points
    print("\tAdding photos")
    # Create a new text field
    arcpy.management.AddField(PWQMN_raw, "Photo", "TEXT")
    for station in StationList:
        station_where = "BOW_SITE_DESC = " + "'" + station + "'"
        PWQMN_SelectStation = arcpy.management.SelectLayerByAttribute(PWQMN_Stations, where_clause=station_where)
        station_calc = "'" + StationList.get(station) + "'"
        arcpy.management.CalculateField(PWQMN_SelectStation, "Photo", station_calc)

    # Create a TEST_CODE domain
    print("\tAdding domains")
    desc_ws = arcpy.Describe(ws)
    desc_domains = desc_ws.domains
    # Check if the domain exists
    domainname = "TESTCODE_domain"
    if domainname not in desc_domains:
        # Create Domain
        arcpy.management.CreateDomain(ws, domainname, field_type="TEXT")[0]
        # Add Coded Values To Domain
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="PPUT", code_description="Total Phosphorus")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="CLIDUR", code_description="Chloride")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="NNOTUR", code_description="Nitrate")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="RSP ", code_description="Suspended Solids")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="RSP", code_description="Suspended Solids")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="DO", code_description="Dissolved Oxygen")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="FWTEMP", code_description="Temperature")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="CONDAM", code_description="Conductivity")[0]

    # Assign Domain To Field
    arcpy.management.AssignDomainToField(PWQMN_raw, field_name="TEST_CODE", domain_name="TESTCODE_domain")[0]

    print("\tCalculating fields")
    # Populate the TEST_CODE records that contain null values
    PWQMN_SelectNull = arcpy.management.SelectLayerByAttribute(PWQMN_raw, where_clause="TEST_CODE IS NULL And DESCRIPTION LIKE '%Nitrate%'")
    arcpy.management.CalculateField(PWQMN_SelectNull, field="TEST_CODE", expression="'NNOTUR'")[0]

    # Create a year field
    # Create a new short integer field
    arcpy.management.AddField(PWQMN_raw, "Year", "SHORT")
    # Populate the new field
    arcpy.management.CalculateField(PWQMN_raw, field="Year", expression="!Sample_Date!.year")

    # Create a month field
    # Create a new short integer field
    arcpy.management.AddField(PWQMN_raw, "Month", "TEXT")
    # Populate the new field
    arcpy.management.CalculateField(PWQMN_raw, field="Month", expression="!Sample_Date!.month")

    # Create Month_domain
    # Check if the domain exists
    domainname2 = "Month_domain"
    if domainname2 not in desc_domains:
        # Create Domain
        arcpy.management.CreateDomain(ws, domainname2, field_type="TEXT")[0]
        # Add Coded Values To Domain
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="1", code_description="Jan")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="2", code_description="Feb")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="3", code_description="Mar")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="4", code_description="Apr")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="5", code_description="May")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="6", code_description="June")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="7", code_description="July")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="8", code_description="Aug")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="9", code_description="Sept")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="10", code_description="Oct")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="11", code_description="Nov")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname2, code="12", code_description="Dec")[0]

    # Assign Domain To Field
    arcpy.management.AssignDomainToField(PWQMN_raw, field_name="Month", domain_name="Month_domain")[0]

    # Some of the Result records contain "<" signs, which causes the field to be interpreted as a text field
    # This causes issues when calculating averages in the ArcGIS Online Dashboard
    # Create a new Double field
    arcpy.management.AddField(PWQMN_raw, "Result_", "DOUBLE")
    # Populate the new field
    arcpy.management.CalculateField(PWQMN_raw, field="Result_", expression="!Result!")

    # Some of the Result records are equal to -9999, which skews the averages in ArcGIS Online
    # Convert -9999 values to null
    PWQMN_where2 = "Result = '-9999'"
    PWQMN_Select2 = arcpy.management.SelectLayerByAttribute(PWQMN_raw, where_clause = PWQMN_where2)
    arcpy.management.CalculateField(PWQMN_Select2, field="Result_", expression="None")

    # Export only the records that contain the required parameters (chloride, etc.) as PWQMN_Data
    PWQMN_where = "TEST_CODE = 'PPUT' Or TEST_CODE = 'CLIDUR' Or TEST_CODE = 'NNOTUR' Or TEST_CODE = 'RSP ' Or TEST_CODE = 'DO' Or TEST_CODE = 'FWTEMP' Or TEST_CODE = 'CONDAM'"
    PWQMN_Select = arcpy.management.SelectLayerByAttribute(PWQMN_raw, where_clause = PWQMN_where)
    PWQMN_Data = os.path.join(ws, "PWQMN_Data")
    arcpy.conversion.ExportTable(PWQMN_Select, PWQMN_Data)

    # Convert all the Total Phosphorus values that are measured in milligram/L to microgram/L
    PWQMN_SelectPhos = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'PPUT' And (UNITS = 'MILLIGRAM PER LITER' Or UNITS = 'mg/L')")
    arcpy.management.CalculateField(PWQMN_SelectPhos, field="Result", expression="!Result! * 1000")[0]
    arcpy.management.CalculateField(PWQMN_SelectPhos, field="UNITS", expression="'MICROGRAM PER LITER'")[0]

    # Add a pass/fail field
    arcpy.management.AddField(PWQMN_raw, "ThresholdPass", "TEXT")
    # Total Phosphorus
    PWQMN_SelectTP = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'PPUT'")
    threshold_expression_TP = "calcThresholdTP(!Result_!)"
    codeblock_TP = """
def calcThresholdTP(value):
    if value <= 30:
        return "Pass"
    if value > 30:
        return "Fail"
    else:
        return "N/A" """
    arcpy.management.CalculateField(PWQMN_SelectTP, "ThresholdPass", threshold_expression_TP, code_block = codeblock_TP)
    # Chloride
    PWQMN_SelectChlor = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'CLIDUR'")
    threshold_expression_Chlor = "calcThresholdChlor(!Result_!)"
    codeblock_Chlor = """
def calcThresholdChlor(value):
    if value <= 120:
        return "Pass"
    if value > 120:
        return "Fail"
    else:
        return "N/A" """
    arcpy.management.CalculateField(PWQMN_SelectChlor, "ThresholdPass", threshold_expression_Chlor, code_block = codeblock_Chlor)
    # Dissolved Oxygen
    PWQMN_SelectDO = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'DO'")
    threshold_expression_DO = "calcThresholdDO(!Result_!)"
    codeblock_DO = """
def calcThresholdDO(value):
    if value <= 6:
        return "Pass"
    if value > 6:
        return "Fail"
    else:
        return "N/A" """
    arcpy.management.CalculateField(PWQMN_SelectDO, "ThresholdPass", threshold_expression_DO, code_block = codeblock_DO)
    # Suspended Solids
    PWQMN_SelectSS = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'RSP '")
    threshold_expression_SS = "calcThresholdSS(!Result_!)"
    codeblock_SS = """
def calcThresholdSS(value):
    if value <= 30:
        return "Pass"
    if value > 30:
        return "Fail"
    else:
        return "N/A" """
    arcpy.management.CalculateField(PWQMN_SelectSS, "ThresholdPass", threshold_expression_SS, code_block = codeblock_SS)
    # Nitrate
    PWQMN_SelectNit = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'NNOTUR'")
    threshold_expression_Nit = "calcThresholdNit(!Result_!)"
    codeblock_Nit = """
def calcThresholdNit(value):
    if value <= 3:
        return "Pass"
    if value > 3:
        return "Fail"
    else:
        return "N/A" """
    arcpy.management.CalculateField(PWQMN_SelectNit, "ThresholdPass", threshold_expression_Nit, code_block = codeblock_Nit)
    # Delete null rows
    PWQMN_SelectNullRows = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="ThresholdPass is null")
    arcpy.management.DeleteRows(PWQMN_SelectNullRows)

    print("\tDeleting fields")
    # Delete repetitive/empty fields
    arcpy.management.DeleteField(PWQMN_Data, drop_field=["Conservation_Authority", "Watershed", "Active", "Unnamed__6", "Unnamed__7", "Result"])[0]

# Add all feature classes and tables to the map display
def GDBToMap():
    print(">> Adding data to map...")
    
    # Add stations (point layer)
    print("\tAdding layers")
    fc = "PWQMN_Stations"
    arcpy.management.MakeFeatureLayer(fc, fc)
    lyr_name = "{}.lyrx".format(fc)
    arcpy.management.SaveToLayerFile(fc, lyr_name)
    lyr_path = os.path.join(os.path.dirname(ws), lyr_name)
    lyr = arcpy.mp.LayerFile(lyr_path)
    m.addLayer(lyr)
    
    # Add data (table)
    print("\tAdding tables")
    table = "PWQMN_Data"
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
    print("\tDeleting existing files")
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
        PWQMNModel()
        GDBToMap()
        AGOLUpload()

print("Done")

