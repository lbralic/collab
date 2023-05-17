This document describes the process of loading the data into the arcGIS pro project using the python scripts.


1. The client provides .xlsx files.  *Save this file somewhere on your computer and record the full path to the file.  We will call this `xlsx_folder_path`*.

e.g. `xlsx_folder_path` = "C:\Winter2023\Collab\Data"

Note:  The "Site Code" values in the ColdwaterStreams and ColdwaterStreams metadata sheets must match up!  In the file we were given at time of writing, they are not exactly the same and need to be manually edited.

2. Decide what folder you want your data files to be stored in.  Make a new folder for this if you need to.  *Record the full path to this folder.  We will call this `data_folder_path`*.

e.g. `data_folder_path` = "C:\Winter2023\Collab\Data"

3. Make a geodatabase (? a whole ArcGIS project?) with ???? stuff set up ???.  *Record the full path to it.  We will call this `ws` because the script will use it as the workspace.*

e.g. `ws` = "C:\Winter2023\Collab\TestFGDB.gdb"

----

With these things set up, you need to run the script.  Before running it, update the `xlsx_folder_path`, `data_folder_path`, and `ws` values at the beginning of the script, to match the values above.


Note: the script is general in the sense that data points can be added or removed and the script will handle the new data and update the file geodatabase.  It is NOT general in the type or format of data it accepts.  The different specific kinds of client data require specific processing.  For example, the coldwater streams data is provided in two csvs and an inner join needs to be performed between the tables before the data is loaded into the feature class, and the biomonitoring data requires a custom transformation on the Family Biotic Index column to convert it from a numeric score to a text category label.  

That is to say, the client can freely modify the coldwater streams data or biomonitoring data as long as they stick to the existing data format.  If they wish to add a new kind of data or change the data format, additional work on the script will need to be performed.

----

The overall pipeline is:

xlsx -> csv -> table -> processing -> feature class -> save project -> upload project to AGOL