"""
This is an example of a top-level script that uses the richness module in
creating a species richness map.

The code manages a log file and writes the code that was run to the log file.

Runtime for ~150 species was 11 hours on May 5, 2023.
"""
## Define a function that writes code to the log file -------------------------
def __LogCode(content):
    print(content)
    with open(topLog, 'a') as logDoc:
        logDoc.write(content)
    logDoc.close()

## Imports and environment settings -------------------------------------------
import sys
import pandas as pd
sys.path.append("PATH/TO/GAPANALYSIS/REPOSITORY")
import gapanalysis as ga
import analysisconfig as config # a config file is necessary, contact N.M. Tarr for details
import arcpy
arcpy.env.overwriteOutput=True
import inspect

## Define variables -----------------------------------------------------------
groupName = "example" # just a phrase to identify the output
outLoc = "/WORKING/DIRECTORY/PATH" # where to saver
modelDir = "W:/USGap/Vert/Model/Output/CONUS/01/" # Path to where the gap data is stored
season = "Any" # define the seasons you are interested in (summer, winter, or any)
interval_size = 50 # the code works in batches of species, this is the batch size
topLog = outLoc + groupName + "/Log" + groupName + '.txt'
CONUS_extent = config.CONUS_extent

# Build species• list ---------------------------------------------------------
sp_df = ["bAMROx", "bKEWAx", "mAMMAx"] # a list of species codes
spp = [x + "_CONUS_01A_2001v1.tif" for x in sp_df if x is not pd.NA]
arcpy.env.workspace=outLoc

# Run the richness calculation function ---------------------------------------
Map, Table = ga.richness.MapRichness(spp=spp, groupName=groupName, 
                                      outLoc=outLoc, modelDir=modelDir,
                                      season=season, intervalSize=interval_size, 
                                      CONUSExtent=config.CONUS_extent,
                                      weight="area")

## Write this script's code to the log ----------------------------------------
codeReader= open(sys.argv[0], "r")
__LogCode("\n\n" + ("#"*67))
__LogCode("\nThe code that was run for the top-level script\n")
__LogCode("#"*67 + "\n")
for l in codeReader.readlines():
    __LogCode(l)
codeReader.close()

#  Write the function's code to the log ---------------------------------------
__LogCode("\n\n" + ("#"*67))
__LogCode("\nThe code that was run to process the richness calculation\n")
__LogCode("#"*67 + "\n")
__LogCode(inspect.getsource(ga.richness.MapRichness))