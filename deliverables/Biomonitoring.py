# BMModel() >> Biomonitoring data processing model
# GDBToMap() >> Add all feature classes and tables to the map display
# AGOLUpload() >> Upload all layers and tables to ArcGIS Online

# Required edits
#   Under "Required Edit 1": Enter data/workspace paths

# Optional edits
#   Under "Optional Edit 1": Enter the summary, tags, etc. that will appear on AGOL
#   Under "Optional Edit 2": Alter the sharing preferences

import arcpy, os, pandas as pd

##########################################
# >>> Required Edit 1: Input paths
# Path to raw Biomonitoring .xlsx file
input_BM_table = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Data\Biomonitoring Data for Dashboard)-June2,2023.xlsx"
# Path to geodatabase
ws = r"C:\Users\Lucija\Desktop\Deliverables\Project\Project.gdb"
# Path to .aprx file
aprx_path = r"C:\Users\Lucija\Desktop\Deliverables\Project\Project.aprx"
# Empty output folder for the service definition drafts
outdir = r"C:\Users\Lucija\Desktop\Deliverables\Output"
##########################################

# Coordinate system
coordsys = "PROJCS[\"NAD_1983_CSRS_UTM_Zone_17N\",GEOGCS[\"GCS_North_American_1983_CSRS\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-81.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]"

arcpy.env.overwriteOutput = True

def BioModel():
    print(">> Processing the Biomonitoring data...")

    # Importing data:
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
    df.columns = df.columns.str.replace(r'\W+', '', regex=True) # delete non-word character
    df.to_csv(csvfilepath, encoding='utf-8-sig')
    # copy the csv file to geodatabase
    arcpy.conversion.ExportTable(csvfilepath, csvname)

    # Biomonitoring stations:
    # Convert the table to a point feature class
    BM_Stations = "Biomonitoring_Stations"
    arcpy.management.XYTableToPoint(csvname, BM_Stations, "Easting", "Northing", "", coordsys)
    # Delete duplicate site codes
    arcpy.management.DeleteIdentical(BM_Stations, "Site_Code")
    # Only keep the fields that contain the basic station information
    field_list = arcpy.ListFields(BM_Stations)
    field_list_delete = []
    for field in field_list:
        if field.baseName != "OBJECTID" and field.baseName != "Shape" and field.baseName != "Watercourse" and field.baseName != "Site_Code" and field.baseName != "Site_Type":
            field_list_delete.append(field.baseName)
    arcpy.management.DeleteField(BM_Stations, drop_field=field_list_delete)

    # Domains:
    # Create coded domain
    desc_ws = arcpy.Describe(ws)
    desc_domains = desc_ws.domains
    # Assign domain name
    domainname_FBI = "FBIndexCat"
    domainname_SO="SenOrgCat"
    infield_SO="Sensitive_Organisms_Category"
    infield_FBI="Family_Biotic_Index_Category"
    # coded value dictionary
    domDict_SO={"A":"Above Average", "B":"Below Average"}
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

    # Add new field(Family Biotic Index Value), type DOUBLE 
    arcpy.AddField_management(csvname, "FamilyBioticIndex_Value", "DOUBLE", field_length = 20)
    arcpy.management.CalculateField(csvname, "FamilyBioticIndex_Value", "!Family_Biotic_Index_Value!")
    # delete original field **
    arcpy.management.DeleteField(csvname, "Family_Biotic_Index_Value")

    # Attribute Rules
    arcpy.management.AddGlobalIDs(csvname)
    # Add attribute rule(CALCULATION) for Family Biotic Index
    name = "FBI_calculateRuleCategory"
    script_expression = 'return When($feature.FamilyBioticIndex_Value >=0 && $feature.FamilyBioticIndex_Value <= 3.75, "Excellent", $feature.FamilyBioticIndex_Value <= 4.25, "Very Good", $feature.FamilyBioticIndex_Value <= 5, "Good", $feature.FamilyBioticIndex_Value <= 5.75, "Fair", $feature.FamilyBioticIndex_Value <= 6.5, "Fairly Poor", $feature.FamilyBioticIndex_Value <= 7.25, "Poor", $feature.FamilyBioticIndex_Value <= 10, "Very Poor", "Not Available");'
    triggering_events = "INSERT;UPDATE"
    description = "Populate Catogory Based on Value"
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name, "CALCULATION", script_expression, "EDITABLE", triggering_events, "", "", description, "", infield_FBI)

    # Add attribute rule(CALCULATION) for sensitive organism
    name3 = "SO_calculateRuleCategory"
    script_expression3 = 'return When($feature.Sensitive_Organisms_ >= 20.9, "Above Average", $feature.Sensitive_Organisms_ < 20.9, "Below Average", "Not Available");'
    triggering_events = "INSERT;UPDATE"
    description = "Populate Catogory Based on Value"
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name3, "CALCULATION", script_expression3, "EDITABLE", triggering_events, "", "", description, "", infield_SO)

    # Add attribute rule(CONSTRAINT) for Family Biotic Index
    name2 = "FBConstraintRule"
    script_expression2 = '$feature.FamilyBioticIndex_Value >= 0  && $feature.FamilyBioticIndex_Value <= 10'
    triggering_events = "INSERT;UPDATE"
    description = "Constraint rule, prevent value out of range: Family Biotic Index Value range from 0 to 10"
    subtype = "ALL"
    error_number = 2001
    error_message = "Invalid Family Biotic Index Value. Must be greater than or equal to 0; or less than or equal to 10."
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name2, "CONSTRAINT", script_expression2, "EDITABLE", triggering_events, error_number, error_message, description, subtype)

    # Add attribute rule(CONSTRAINT) for sensitive organism
    name4 = "SOConstraintRule"
    script_expression4 = '$feature.Sensitive_Organisms_ >= 0 && $feature.Sensitive_Organisms_ <= 100'
    triggering_events = "INSERT;UPDATE"
    description = "Constraint rule, prevent value out of range: 0-100"
    subtype = "ALL"
    error_number2 = 2002
    error_message2 = "Invalid Sensitive Organism Value. Must be greater than or equal to 0; or less than and equal to 100."
    # Run the AddAttributeRule tool
    arcpy.management.AddAttributeRule(csvname, name4, "CONSTRAINT", script_expression4, "EDITABLE", triggering_events, error_number2, error_message2, description, subtype)

# Add all feature classes and tables to the map display
def GDBToMap():
    print(">> Adding data to map...")
    aprx = arcpy.mp.ArcGISProject(aprx_path)
    m = aprx.listMaps()[0]
    # Add stations (point layer)
    fc = "Biomonitoring_Stations"
    arcpy.management.MakeFeatureLayer(fc, fc)
    lyr_name = "{}.lyrx".format(fc)
    arcpy.management.SaveToLayerFile(fc, lyr_name)
    lyr_path = os.path.join(os.path.dirname(ws), lyr_name)
    lyr = arcpy.mp.LayerFile(lyr_path)
    m.addLayer(lyr)
    # Add data (table)
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
    service_name = "Kawartha Conservation Biomonitoring Data test"          # Name of the feature layer to be uploaded to AGOL
    sddraft_filename = service_name + ".sddraft"
    sddraft_output_filename = os.path.join(outdir, sddraft_filename)
    sd_filename = service_name + ".sd"
    sd_output_filename = os.path.join(outdir, sd_filename)

    # Delete existing files
    print("Deleting existing files...")
    if os.path.exists(sddraft_output_filename):
        os.remove(sddraft_output_filename)
    if os.path.exists(sd_output_filename):
        os.remove(sd_output_filename)

    # Reference layers to publish
    aprx = arcpy.mp.ArcGISProject(aprx_path)
    m = aprx.listMaps()[0]      # Specify the name of the map if necessary
    lyr_list = []               # List layers and tables
    lyrs = m.listLayers()       # List layers
    tables = m.listTables()     # List tables
    count_lyrs = len(lyrs)
    for x in range(count_lyrs):
        lyr_list.append(lyrs[x])
    count_tables = len(tables)
    for x in range(count_tables):
        lyr_list.append(tables[x])

    ##########################################
    # >>> Optional Edit 1: Enter the summary, tags, etc. that will appear on AGOL
    # Create FeatureSharingDraft and enable overwriting
    server_type = "HOSTING_SERVER"
    # Parameters: getWebLayerSharingDraft(server_type, service_type, service_name, {layers_and_tables})
    sddraft = m.getWebLayerSharingDraft(server_type, "FEATURE", service_name, lyr_list)
    sddraft.summary = "My Summary"
    sddraft.tags = "My Tags"
    sddraft.description = "My Description"
    sddraft.credits = "My Credits"
    sddraft.useLimitations = "My Use Limitations"
    sddraft.overwriteExistingService = True
    ##########################################

    # Create Service Definition Draft file
    # Parameters: exportToSDDraft(out_sddraft)
    sddraft.exportToSDDraft(sddraft_output_filename)

    # Stage Service
    print("Start Staging")
    # Parameters: arcpy.server.StageService(in_service_definition_draft, out_service_definition, {staging_version})
    arcpy.server.StageService(sddraft_output_filename, sd_output_filename)

    ##########################################
    # Share to portal
    # >>> Optional Edit 2: Alter sharing preferences
    # Documentation: https://pro.arcgis.com/en/pro-app/latest/tool-reference/server/upload-service-definition.htm
    inOverride = "OVERRIDE_DEFINITION"
    # Sharing options
    inSharePublic = "PRIVATE"                 # Enter "PUBLIC" or "PRIVATE"
    inShareOrg = "NO_SHARE_ORGANIZATION"      # Enter "SHARE_ORGANIZATION" or "NO_SHARE_ORGANIZATION"
    inShareGroup = ""                         # Enter the name of the group(s): in_groups or [in_groups,...]
    # AGOL folder name
    inFolderType = "Existing"                         # Enter "Existing" to specify an existing folder
    inFolderName = "Collab"                         # Enter the existing AGOL folder name
    print("Start Uploading")
    ##########################################

    # Parameters: arcpy.server.UploadServiceDefinition(in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type}, {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
    arcpy.server.UploadServiceDefinition(sd_output_filename, server_type, "", "", inFolderType, inFolderName, "", inOverride, "", inSharePublic, inShareOrg, inShareGroup)

    print("Finish Publishing")

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
