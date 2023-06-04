import arcpy, os
import pandas as pd

arcpy.env.overwriteOutput = True

# Path to geodatabase
workspace = arcpy.env.workspace = r"C:\gis\_collab\test" # change path here

# Path to .aprx file
aprx_path = r"C:\gis\_collab\test\test.aprx" # change path

# Empty output folder for the service definition drafts
outdir = r"C:\gis\_collab\test\Output" # change path

# Create file geodatabase
gdb = "Biomonitoring.gdb" 
ws = workspace + '/' + gdb
if arcpy.Exists(ws):
    arcpy.Delete_management(ws)
arcpy.management.CreateFileGDB(workspace, gdb)


# Coordinate system
coordsys = "PROJCS[\"NAD_1983_CSRS_UTM_Zone_17N\",GEOGCS[\"GCS_North_American_1983_CSRS\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-81.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]"

# Path to Biomonitoring Excel file
inputExcelFile = r"C:\gis\_collab\DATA\BioMonitoringData.xlsx" # change path here
# csv file path
csvname = os.path.basename(inputExcelFile).split(".")[0]
csvfile = os.path.join(csvname + '.csv')
csvfilepath = os.path.join(workspace+'/' + csvfile)

def BioModel():
    print(">> Processing the Biomonitoring data...")

    # Reading an excel file
    excelFile = pd.read_excel (inputExcelFile, sheet_name="Biomonitoring")

    # Converting excel file into CSV file
    excelFile.to_csv (csvfilepath, index = None, header=True)

    # Reading and Converting the output csv file into a dataframe object
    df = pd.DataFrame(pd.read_csv(csvfile))

    # Displaying the dataframe object
    df.columns=df.columns.str.replace(' ', '_') # replace space with underscore
    df.columns = df.columns.str.replace(r'\W+', '', regex=True) # delete non-word character
    df.to_csv(csvfilepath, encoding='utf-8-sig')

    # copy the csv file to geodatabase
    arcpy.conversion.ExportTable(csvfile, ws + "/" + csvname)
    # convert the csv table into point feature class
    arcpy.management.XYTableToPoint(csvfilepath, csvname, "Easting", "Northing", "", coordsys)


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


if __name__ == '__main__':
    # Global Environment settings
    with arcpy.EnvManager(outputCoordinateSystem = coordsys, scratchWorkspace = ws, workspace = ws):
        BioModel()
