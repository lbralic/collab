# PWQMNModel() >> PWQMN data processing model
# GDBToMap() >> Add all feature classes and tables to the map display
# AGOLUpload() >> Upload all layers and tables to ArcGIS Online

import arcpy, os

# Path to raw PWQMN .xlsx file
input_PWQMN_table = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Data\2023-04-11_PWQMNdata_GISDashboard.xlsx"
# Path to workspace
ws = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Testing\PWQMN\PWQMN_test.gdb"
# Path to .aprx file
aprx_path = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Testing\PWQMN\PWQMN_test.aprx"
# Output folder for the service definition drafts
outdir = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Script\Output"

# Coordinate system
coordsys = "PROJCS[\"NAD_1983_CSRS_UTM_Zone_17N\",GEOGCS[\"GCS_North_American_1983_CSRS\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-81.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]"

arcpy.env.overwriteOutput = True

# PWQMN Data Processing
def PWQMNModel():
    print(">> Processing the PWQMN data...")

    # Import the Excel file to the gdb with the name PWQMN
    #Parameters: arcpy.conversion.ExcelToTable(Input_Excel_File, Output_Table, {Sheet}, {field_names_row}, {cell_range})
    arcpy.conversion.ExcelToTable(input_PWQMN_table, "PWQMN")

    # Create a TEST_CODE domain
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
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="DO", code_description="Dissolved Oxygen")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="FWTEMP", code_description="Temperature")[0]
        arcpy.management.AddCodedValueToDomain(ws, domainname, code="CONDAM", code_description="Conductivity")[0]

    PWQMN_raw = os.path.join(ws, "PWQMN")
    # Assign Domain To Field
    arcpy.management.AssignDomainToField(PWQMN_raw, field_name="TEST_CODE", domain_name="TESTCODE_domain")[0]

    # Populate the TEST_CODE records that contain null values
    PWQMN_SelectNull = arcpy.management.SelectLayerByAttribute(PWQMN_raw, where_clause="TEST_CODE IS NULL And DESCRIPTION LIKE '%Nitrate%'")
    arcpy.management.CalculateField(PWQMN_SelectNull, field="TEST_CODE", expression="'NNOTUR'")[0]

    # Some of the Result records contain "<" signs, which causes the field to be interpreted as a text field
    # This causes issues when calculating averages in the ArcGIS Online Dashboard
    # Create a new Double field
    arcpy.management.AddField(PWQMN_raw, "Result_", "DOUBLE")
    # Populate the new field
    arcpy.management.CalculateField(PWQMN_raw, field="Result_", expression="!Result!")

    # Export only the records that contain the required parameters (chloride, etc.) as PWQMN_Data
    PWQMN_where = "TEST_CODE = 'PPUT' Or TEST_CODE = 'CLIDUR' Or TEST_CODE = 'NNOTUR' Or TEST_CODE = 'RSP ' Or TEST_CODE = 'DO' Or TEST_CODE = 'FWTEMP' Or TEST_CODE = 'CONDAM'"
    PWQMN_Select = arcpy.management.SelectLayerByAttribute(PWQMN_raw, where_clause = PWQMN_where)
    PWQMN_Data = os.path.join(ws, "PWQMN_Data")
    arcpy.conversion.ExportTable(PWQMN_Select, PWQMN_Data)

    # Convert all the Total Phosphorus values that are measured in milligram/L to microgram/L
    PWQMN_SelectPhos = arcpy.management.SelectLayerByAttribute(PWQMN_Data, where_clause="TEST_CODE = 'PPUT' And (UNITS = 'MILLIGRAM PER LITER' Or UNITS = 'mg/L')")
    arcpy.management.CalculateField(PWQMN_SelectPhos, field="Result", expression="!Result! * 1000")[0]
    arcpy.management.CalculateField(PWQMN_SelectPhos, field="UNITS", expression="'MICROGRAM PER LITER'")[0]

    # Delete repetitive/empty fields
    arcpy.management.DeleteField(PWQMN_Data, drop_field=["Conservation_Authority", "Watershed", "Active", "Unnamed__6", "Unnamed__7", "Result"])[0]

# Add all feature classes and tables to the map display
def GDBToMap():
    print(">> Adding data to map...")
    aprx = arcpy.mp.ArcGISProject(aprx_path)
    m = aprx.listMaps()[0]          # Enter the name of the map if there are multiple, ie. aprx.listMaps("MapName")[0]
    list_layers = m.listLayers("PWQMN_Stations")
    if len(list_layers) == 0:
        fcs = arcpy.ListFeatureClasses()
        for fc in fcs:
            desc_fc = arcpy.Describe(fc)
            fc_name = desc_fc.baseName
            arcpy.management.MakeFeatureLayer(fc, fc_name)
            lyr_name = "{}.lyrx".format(fc_name)
            arcpy.management.SaveToLayerFile(fc_name, lyr_name)
            lyr_path = os.path.join(os.path.dirname(ws), lyr_name)
            lyr = arcpy.mp.LayerFile(lyr_path)
            m.addLayer(lyr)
    tables = arcpy.ListTables()
    for table in tables:
        desc_table = arcpy.Describe(table)
        name_table = desc_table.baseName
        # Only add PWQMN_Data to the map view
        if name_table == "PWQMN_Data":
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
    service_name = "Kawartha Conservation PWQMN Data"          # Name of the feature layer to be uploaded to AGOL
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

    # Create Service Definition Draft file
    # Parameters: exportToSDDraft(out_sddraft)
    sddraft.exportToSDDraft(sddraft_output_filename)

    # Stage Service
    print("Start Staging")
    # Parameters: arcpy.server.StageService(in_service_definition_draft, out_service_definition, {staging_version})
    arcpy.server.StageService(sddraft_output_filename, sd_output_filename)

    # Share to portal
    # Documentation: https://pro.arcgis.com/en/pro-app/latest/tool-reference/server/upload-service-definition.htm
    inOverride = "OVERRIDE_DEFINITION"
    # Sharing options
    inSharePublic = "PUBLIC"                 # Enter "PUBLIC" or "PRIVATE"
    inShareOrg = "NO_SHARE_ORGANIZATION"      # Enter "SHARE_ORGANIZATION" or "NO_SHARE_ORGANIZATION"
    inShareGroup = "Kawartha Conservation Collaborative Project"                         # Enter the name of the group(s): in_groups or [in_groups,...]
    # AGOL folder name
    inFolderType = "Existing"                         # Enter "Existing" to specify an existing folder
    inFolderName = "Collab"                         # Enter the existing AGOL folder name
    print("Start Uploading")
    # Parameters: arcpy.server.UploadServiceDefinition(in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type}, {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
    arcpy.server.UploadServiceDefinition(sd_output_filename, server_type, "", "", inFolderType, inFolderName, "", inOverride, "", inSharePublic, inShareOrg, inShareGroup)

    print("Finish Publishing")

    # Delete tables from the map view
    table_list = m.listTables()
    for tbl in table_list:
        m.removeTable(tbl)
    aprx.save()

if __name__ == '__main__':
    # Global Environment settings
    with arcpy.EnvManager(outputCoordinateSystem = coordsys, scratchWorkspace = ws, workspace = ws):
        PWQMNModel()
        GDBToMap()
        AGOLUpload()
