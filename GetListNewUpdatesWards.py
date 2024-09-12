#Script created by Donald Maruta - 21 Feb 24

#Connect to AGOL
from arcgis.gis import GIS
gis = GIS("home")

#Import Required Modules
import requests, csv, os, time, shutil, arcpy, fnmatch, zipfile, glob
import pandas as pd
from arcgis.gis import GIS
from datetime import date
from pathlib import Path
from arcgis.features import FeatureLayerCollection
arcpy.env.qualifiedFieldNames = False
arcpy.env.overwriteOutput=True

#Create FGDB & Variables
arcpy.management.CreateFileGDB("/arcgis/home/CancerDashboard", "Temp")
tempFGDB = "/arcgis/home/CancerDashboard/Temp.gdb"
fldrPath = "/arcgis/home/CancerDashboard/"

#Import Metadata and OldMetadata CSV files
metadata = "/arcgis/home/CancerDashboard/Metadata.csv"
metadata_df = pd.read_csv(metadata)
oldmetadata = "/arcgis/home/CancerDashboard/OldMetadata.csv"
oldmetadata_df = pd.read_csv(oldmetadata)

#Merge Both Metadata DataFrames
combimetadata = pd.merge(oldmetadata_df, metadata_df, on="IndicatorId")
combimetadata.columns = ["IndicatorId", "OldDate", "NewDate"]

#Import list of Wards
Wardlist = "/arcgis/home/CancerDashboard/CancerMSOAWard.csv"
WardlistDF = pd.read_csv(Wardlist)
WardlistDF.columns = ["IndicatorId"]

#Merge Metadata and Ward list Data Frames
Wardmetadata = pd.merge(combimetadata, WardlistDF, on="IndicatorId")

#Location of NCL wards
NCL_Wards = "/arcgis/home/CancerDashboard/Ward2021.shp"
arcpy.env.workspace = "/arcgis/home/CancerDashboard"

#Number of iterations needed
length = len(Wardmetadata)

#Creation of loop to process FingerTips data
for i in range(length):
        
    #Check to see if data requires updating
    oldDate = Wardmetadata.loc[i, 'OldDate']
    newDate = Wardmetadata.loc[i, 'NewDate']
    if oldDate == newDate:
        continue

    #Input name of Fingertips below
    fingerTips = str(Wardmetadata.loc[i, 'IndicatorId'])
    csvfile = "Ward"+fingerTips
    
    # Maximum number of download attempts
    max_attempts = 10

    # Sleep time between retry attempts (in seconds)
    retry_delay = 30
        
    for attempt in range(max_attempts):

        #Download Files by GP Practice
        url = "https://fingertips.phe.org.uk/api/all_data/csv/for_one_indicator?indicator_id=" + fingerTips
        print(url)
        response_API = requests.get(url, timeout=3600)
        # Check if the file is correct
        if response_API.status_code == 200:
            data = response_API.text
            print("Data downloaded")

            #Save as CSV
            csvfile = "Ward"+fingerTips
            outputcsv = "/arcgis/home/CancerDashboard/Ward" + fingerTips + ".csv"
            print(outputcsv)
            open(outputcsv, "wb").write(response_API.content)
            print("Data written")
            break
                
        else:
            print("Incorrect file. Will retry")
            time.sleep(retry_delay)
    
    #Import CSV & SHP to FGDB
    shpfile = "/arcgis/home/CancerDashboard/Ward" + fingerTips + ".shp"
    WardFGDB = os.path.join(tempFGDB, csvfile)
    importFGDB = os.path.join(tempFGDB, "NCLICB_Wards")
    arcpy.conversion.ExportTable(outputcsv, WardFGDB)
    arcpy.conversion.FeatureClassToGeodatabase(NCL_Wards, tempFGDB)
    arcpy.env.workspace = tempFGDB
    fileDF = arcpy.management.AddJoin("Ward2021", "WD21CD", WardFGDB, "Area_Code")
    arcpy.conversion.ExportFeatures(fileDF, "TestFC")
    arcpy.conversion.ExportFeatures("TestFC", shpfile)
    
    #Initial creation of the service - Ward services
    path = '/arcgis/home/CancerDashboard/'
    os.chdir(path)
    
    #List of files to create ShapeFile as Zip File
    file_list = ["Ward" + fingerTips + ".shp", "Ward" + fingerTips + ".shx", "Ward" + fingerTips + ".dbf", "Ward" + fingerTips + ".prj"]
                
    #Create Zip file
    shpzip = path + csvfile + ".zip"
    with zipfile.ZipFile(shpzip, 'w') as zipF:
        for file in file_list:
            zipF.write(file, compress_type=zipfile.ZIP_DEFLATED)
            
    #Initial Publish to AGOL
    #item = gis.content.add({}, shpzip)
    #published_item = item.publish()
    #published_item.share(everyone=True)
    
    #Overwrite the existing service - All Services
    #Search for 'Ward' feature layer collection
    search_result = gis.content.search(query="Ward" + fingerTips, item_type="Feature Layer")
    feature_layer_item = search_result[0]
    feature_layer = feature_layer_item.layers[0]
    feat_id = feature_layer.properties.serviceItemId
    item = gis.content.get(feat_id)
    item_collection = FeatureLayerCollection.fromitem(item)
    #call the overwrite() method which can be accessed using the manager property
    item_collection.manager.overwrite("Ward" + fingerTips)
    item.share(everyone=True)
    update_dict = {"capabilities": "Query,Extract"}
    item_collection.manager.update_definition(update_dict)
    item.content_status="authoritative"

#Code to delete unnecessary files
arcpy.env.workspace = '/arcgis/home/CancerDashboard'

#Get a list of all subdirectories (folders) in the specified folder
folders = [f for f in os.listdir(fldrPath) if os.path.isdir(os.path.join(fldrPath, f))]

for folder in folders:
    folder = os.path.join(fldrPath, folder)
    shutil.rmtree(folder)

#List of files to preserve
files_to_preserve = ["CancerGP.csv", "CancerMSOAWard.csv", "Metadata.csv", "MSOA2011.dbf", "MSOA2011.prj", "MSOA2011.shp", "MSOA2011.shx", "MSOA2011.zip", "NCLICB_GPs.csv", "OldMetadata.csv", "Ward2021.dbf", "Ward2021.prj", "Ward2021.shp", "Ward2021.shx", "Ward2021.zip"]

# Get a list of all files in the directory
all_files = glob.glob(os.path.join(fldrPath, "*"))

# Iterate over each file
for file_path in all_files:
    # Get the file name
    file_name = os.path.basename(file_path)
    
    # Check if the file name is not in the list of files to preserve
    if file_name not in files_to_preserve:
        # Delete the file
        os.remove(file_path)
        print(f"Deleted {file_name}")

print("All files except the specified ones have been deleted.")
