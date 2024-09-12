# Get-List-New-Datasets-Wards

Python code designed to be run in ArcGIS OnLine Notebook

This allows users to create a list of Electoral Ward datasets from PHE FingerTips (Open Source Data) which require updating.

It carries out the following actions in the following order  
- Connect to AGOL  
- Import Required Modules
- Create FGDB & Variables  
- Import Metadata and OldMetadata CSV files  
- Merge Both Metadata DataFrames  
- Import list of Wards  
- Merge Metadata and Ward list Data Frames
- Location of NCL wards
- Number of iterations needed
- Creation of loop to process FingerTips Data
- Initial creation of the service - GP Services
- Overwrite the existing service - All Services
- Code to delete unnecessary files
