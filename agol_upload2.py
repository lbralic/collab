# Created by: Lucija Bralic, Fleming College
# Last updated: May 2023
# Purpose: Automate the upload of ArcGIS Pro layers to ArcGIS Online (AGOL)

import arcpy
import os
# import xml.dom.minidom as DOM

# Source: https://pro.arcgis.com/en/pro-app/latest/arcpy/sharing/featuresharingdraft-class.htm

username = input(">> Please enter your ArcGIS Online username: ")
password = input(">> Please enter your ArcGIS Online password: ")
# Organization URL
org_url = "https://fleming.maps.arcgis.com"
# Output folder for the service definition drafts
outdir = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Script\Output"
# Path to the .aprx file that contains the layers to be exported
aprx_path = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Script\ArcGISPro\script.aprx"

# Sign in to ArcGIS Online
arcpy.SignInToPortal(org_url, username, password)

# Set output file names
service_name = "service_draft"
sddraft_filename = service_name + ".sddraft"
sddraft_output_filename = os.path.join(outdir, sddraft_filename)
sd_filename = service_name + ".sd"
sd_output_filename = os.path.join(outdir, sd_filename)

# Reference layers to publish
aprx = arcpy.mp.ArcGISProject(aprx_path)
# aprx.save()
m = aprx.listMaps()[0]
selected_layer = m.listLayers()[0]      # List layers (ie. feature classes)
selected_layer_str = str(selected_layer)
# selected_table = m.listTables()[0]    # List tables

# Create FeatureSharingDraft
server_type = "HOSTING_SERVER"
# getWebLayerSharingDraft(server_type, service_type, service_name, {layers_and_tables})
sddraft = m.getWebLayerSharingDraft(server_type, "FEATURE", service_name, selected_layer)       # For layers and tables: [selected_layer, selected_table]

# Create Service Definition Draft file
# exportToSDDraft(out_sddraft)
sddraft.exportToSDDraft(sddraft_output_filename)

# Stage Service
print("Start Staging")
# arcpy.server.StageService(in_service_definition_draft, out_service_definition, {staging_version})
arcpy.server.StageService(sddraft_output_filename, sd_output_filename)

# Share to portal
print("Start Uploading")
# arcpy.server.UploadServiceDefinition(in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type}, {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
arcpy.server.UploadServiceDefinition(in_sd_file=sd_output_filename, in_server=server_type)

print("Finish Publishing")