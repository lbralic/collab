# Documentation: 
# Read Excel file - https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
# Convert to .csv - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

# https://stackoverflow.com/questions/71605777/how-to-convert-multiple-sheets-in-an-excel-workbook-to-csv-files-in-python

import pandas as pd, os

xlsx_file = r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Data\BioMonitoringTempData.xlsx"
output_dir =  r"E:\Documents\Fleming_College\Semester_3\APST62_Collab\Project\Script\Output"

for sheet_name, df in pd.read_excel(xlsx_file, index_col=0, sheet_name=None).items():
    csv_file = os.path.join(output_dir, f"{sheet_name}.csv")
    df.to_csv(csv_file, encoding='utf-8')

