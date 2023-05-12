# v1.4 Add sharing options

# Created by: Lucija Bralic, Fleming College
# Last updated: May 2023
# Purpose: Automate the upload of ArcGIS Pro layers to ArcGIS Online (AGOL)

import arcpy
import os

# Source: 
# https://pro.arcgis.com/en/pro-app/latest/arcpy/sharing/featuresharingdraft-class.htm
# https://pro.arcgis.com/en/pro-app/latest/tool-reference/server/stage-service.htm

# Output folder for the service definition drafts
outdir = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Script\Output"
# Path to the .aprx file that contains the layers to be exported
aprx_path = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Script\ArcGISPro\script.aprx"

# Set output file names
service_name = "Biomonitoring"          # Name of the feature layer to be uploaded to AGOL
sddraft_filename = service_name + ".sddraft"
sddraft_output_filename = os.path.join(outdir, sddraft_filename)
sd_filename = service_name + ".sd"
sd_output_filename = os.path.join(outdir, sd_filename)

# Delete existing files
if os.path.exists(sddraft_output_filename):
    os.remove(sddraft_output_filename)
if os.path.exists(sd_output_filename):
    os.remove(sd_output_filename)

# Reference layers to publish
aprx = arcpy.mp.ArcGISProject(aprx_path)
m = aprx.listMaps()[0]      # Specify the name of the map if necessary
lyrs = m.listLayers()       # List layers
# tables = m.listTables()   # List tables

# Create FeatureSharingDraft and enable overwriting
server_type = "HOSTING_SERVER"
# Parameters: getWebLayerSharingDraft(server_type, service_type, service_name, {layers_and_tables})
sddraft = m.getWebLayerSharingDraft(server_type, "FEATURE", service_name, lyrs)
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
inSharePublic = "PRIVATE"                 # Enter "PUBLIC" or "PRIVATE"
inShareOrg = "NO_SHARE_ORGANIZATION"      # Enter "SHARE_ORGANIZATION" or "NO_SHARE_ORGANIZATION"
inShareGroup = ""                         # Enter the name of the group(s): in_groups or [in_groups,...]
# AGOL folder name
inFolderType = ""                         # Enter "Existing" to specify an existing folder, or "" to not specify an AGOL folder
inFolderName = ""                         # Enter the existing AGOL folder name, or "" to not specify an AGOL folder
print("Start Uploading")
# Parameters: arcpy.server.UploadServiceDefinition(in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type}, {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
arcpy.server.UploadServiceDefinition(sd_output_filename, server_type, "", "", inFolderType, inFolderName, "", inOverride, "", inSharePublic, inShareOrg, inShareGroup)

print("Finish Publishing")
