import arcpy
import os

ws = r"E:\Documents\Fleming_College\Semester_3\Script\ArcGISPro\script.gdb"
arcpy.env.workspace = ws
arcpy.env.overwriteOutput = True

# Note: The "Family Biotic Index (Value)" field must only contain numeric values, ie. no "N/A"
in_table = r"E:\Documents\Fleming_College\Semester_3\Data\Biomonitoring.csv"
in_table_basename = os.path.basename(in_table)
out_table = os.path.splitext(in_table_basename)[0]

# arcpy.conversion.ExportTable(in_table, out_table, {where_clause}, use_field_alias_as_name, {field_mapping}, {sort_field})
arcpy.conversion.ExportTable(in_table, out_table)

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
        return "N/A" """

# arcpy.management.CalculateField(in_table, field, expression, {expression_type}, {code_block}, {field_type}, {enforce_domains})
# Replace "Family_Biotic_Index__Category_" with the name of the output field, if necessary
arcpy.management.CalculateField(out_table, "Family_Biotic_Index__Category_", expression, code_block = codeblock)
