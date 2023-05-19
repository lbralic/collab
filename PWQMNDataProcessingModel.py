import arcpy, os, pandas as pd

# Path to raw PWQMN .xlsx file
input_PWQMN_table = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Data\2023-04-11_PWQMNdata_GISDashboard.xlsx"
# Path to workspace
ws = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Testing\PWQMN\PWQMN_test.gdb"
# Coordinate system
coordsys = "PROJCS[\"NAD_1983_CSRS_UTM_Zone_17N\",GEOGCS[\"GCS_North_American_1983_CSRS\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-81.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]"

arcpy.env.overwriteOutput = True

# PWQMN Data Processing
def PWQMNModel():
    # Convert .xlsx to .csv (inputting an .xlsx file to TableToTable causes errors)
    PWQMN_read_file = pd.read_excel(input_PWQMN_table)
    PWQMN_path = os.path.dirname(input_PWQMN_table)
    PWQMN_csv = os.path.join(PWQMN_path, "PWQMN.csv")
    PWQMN_read_file.to_csv (PWQMN_csv, index = None, header=True)

    # Import the .csv file to the gdb with the name PWQMN
    arcpy.conversion.TableToTable(PWQMN_csv, ws, "PWQMN")

    # Create TEST_CODE domain
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
    
    # Export only the records that contain the required parameters (chloride, etc.) as PWQMN_Parameters
    PWQMN_where = "TEST_CODE = 'PPUT' Or TEST_CODE = 'CLIDUR' Or TEST_CODE = 'NNOTUR' Or TEST_CODE = 'RSP ' Or TEST_CODE = 'DO' Or TEST_CODE = 'FWTEMP' Or TEST_CODE = 'CONDAM'"
    PWQMN_Select = arcpy.management.SelectLayerByAttribute(PWQMN_raw, where_clause = PWQMN_where)
    PWQMN_Parameters = os.path.join(ws, "PWQMN_Parameters")
    arcpy.conversion.ExportTable(PWQMN_Select, PWQMN_Parameters)

    # Convert all the Total Phosphorus values that are measured in milligram/L to microgram/L
    PWQMN_SelectPhos = arcpy.management.SelectLayerByAttribute(PWQMN_Parameters, where_clause="TEST_CODE = 'PPUT' And (UNITS = 'MILLIGRAM PER LITER' Or UNITS = 'mg/L')")
    arcpy.management.CalculateField(PWQMN_SelectPhos, field="Result", expression="!Result! * 1000")[0]
    arcpy.management.CalculateField(PWQMN_SelectPhos, field="UNITS", expression="'MICROGRAM PER LITER'")[0]

    # Delete repetitive/empty fields
    arcpy.management.DeleteField(PWQMN_Parameters, drop_field=["Conservation_Authority", "Watershed", "Active", "Unnamed__6", "Unnamed__7"])[0]

# Add all feature classes and tables to the map display
def GDBToMap():
    print()
    # fcs = arcpy.ListFeatureClasses()
    # for fc in fcs:
    #     arcpy.mapping.Layer(fc)
    # tables = arcpy.ListTables()
    # for table in tables:
    #     arcpy.mapping.TableView(table)

# Upload all layers and tables to ArcGIS Online
def AGOLUpload():
    print()

if __name__ == '__main__':
    # Global Environment settings
    with arcpy.EnvManager(outputCoordinateSystem = coordsys, scratchWorkspace = ws, workspace = ws):
        PWQMNModel()
        GDBToMap()
        AGOLUpload()
