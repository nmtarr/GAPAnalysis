
AOI_Name = "hasForest"
workDir = "T:/temp/overlay/" + AOI_Name
AOI_layer = "T:/temp/LCreclass/hasForest2/hasForest2.tif"
mapLoc = "P:/Proj3/USGap/Vert/Model/Output/Conus/"
log = workDir + "_log.txt"

#@@@@@@@@@@@@@@@@@$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%%%%%
#def PercentInAOI(AOI_Name, workDir, AOI_Layer, mapLoc, log)
'''
N. Tarr, 23Sept2015.

This is a script to facilitate spatial queries of the GAP species
model data.  This script provides a table that answers the question "What percentage
of each species' habitat occurs in X subset of the cells within the contiguous US?"
It compares a group of species model output rasters, to a binary raster of your choosing
that could be a reclassification of the landcover or something like a binary 30m
pixel raster of urban.

The inputs for the script are (1) a directory containing the species model grids
that you wish to assess and (2) a "AOI" grid coded as "10's" and "NoData"'s.
If other values are used, the script will need to be edited.

Arc's inability to build VAT's for grids with counts over 2 billion
are problematic for this task, so I had to code in tiling of the rasters where a VAT
is built for each tile, copied to a DataFrame, and then all DataFrames are combined
with Pandas.

Some grids have negative values that don't cause any error but give erroneous results.
There is therefore, a step that tests for that so that grids with negative counts aren't
processed and are listed instead.

Initial tests of this script found inconsistent results during the processing of
tiles from splitraster_management.  The solution was to overwrite the attribute table
for each tile before processing.

Some notes from each run are recorded in a processing log at the end of the run.
The log stores the list of models with tiling problems or negative values in the
species distribution grid.
'''

############################################################## Imports and settings
###################################################################################
import arcpy, pandas as pd, os
from datetime import datetime
arcpy.CheckOutExtension("Spatial")
arcpy.env.Extent = AOI_layer  #???????????????????????????
arcpy.env.snapRaster = "P:\\Proj3\\USGap\\Vert\\Model\\data\\snapgrid"
arcpy.env.scratchWorkspace = workDir + "\\ztemp"
arcpy.env.cellSize = 30
arcpy.env.overwriteOutput = True
pd.set_option('display.width', 1000)

############################################# Function to write data to the log file
####################################################################################
def __Log(content):
    print content
    with open(log, 'a') as logDoc:
        logDoc.write(content + '\n')    

####################################################### Make a dictionary of values
###################################################################################
ValueMap = {0: "NonAOINonHab",
            10: "AOINonHab",
            1: "NonAOISummer",
            2: "NonAOIWinter",
            3: "NonAOIYear",
            11: "AOISummer",
            12: "AOIWinter",
            13: "AOIYear"}
            
################################# Create the working directory if it doesn't exist
###################################################################################
if not os.path.exists(workDir):
    os.makedirs(workDir)
# Create a directory for the tiles that will be made later on.    
folderTile = arcpy.env.scratchWorkspace + "\\ztemp\\tiles"
if not os.path.exists(folderTile):
    os.makedirs(folderTile)
    
#################################### Get a list of species model outputs to process
###################################################################################
arcpy.env.workspace = mapLoc
dists = arcpy.ListRasters()
dists = [i[0] + i[1:5].upper() + i[5:] for i in dists]  #$$$$$$$$$$$$$$$$$$$$$$

############################################### Initialize some lists and dataframe
###################################################################################
# Create empty dataframe for results
colList = ValueMap.values() + ["Date", "RunTime"]
df1 = pd.DataFrame(index=dists, columns=colList).fillna(value=0)
# Make empty list to collect rasters with negatives
negatives = []
# Potential erroneous models
problematic = []
# Potential Hawaiian models
hawaii = []

################################################## Loop through rasters and process
###################################################################################
for d in dists[:3]:
    __Log("\n-------" + d + "-------")
    
    ############################################## Get start time and set workspace
    arcpy.env.workspace = workDir
    starttime = datetime.now()
    timestamp = starttime.strftime('%Y-%m-%d')

    #Add together rasters
    print "Summing grids"
    Sum = arcpy.sa.CellStatistics([arcpy.Raster(mapLoc + d), arcpy.sa.Raster(AOI_layer)],
                                   "SUM", "DATA")

    # Make empty dataframe
    df2 = pd.DataFrame(index=[0, 1, 2, 3, 10, 11, 12, 13],
                    columns=["COUNT"]).fillna(value=0)

    # Make cursor for the Sum grid
    rows = arcpy.SearchCursor(Sum)
    for r in rows:
        df2.loc[r.getValue("VALUE"), "COUNT"] = r.getValue("COUNT")

    # Do some table manipulation to prep for the next step.
    df2["Categ"] = [ValueMap[x] for x in df2.index]
    df2.set_index("Categ", drop=True, inplace=True)

    # Fill out the species' entries in the main DataFrame using the one just created.
    indx = df2.index
    for x in indx:
        df1.loc[d, x] = int(df2.ix[x])

    # Get end time and time it took to run the species.
    endtime = datetime.now()
    delta = endtime - starttime
    __Log("Processing time: " + str(delta))

    # Fillout runtime and date fields in the main DataFrame.
    df1.loc[d, "RunTime"] = str(delta)
    df1.loc[d, "Date"] = str(timestamp)

    '''
    except:
        try:
            print "No attribute table"
            #Add together rasters

            print "Summing grids"
            Sum = arcpy.sa.CellStatistics([d, arcpy.sa.Raster(AOI_layer)], "SUM", "DATA")
            # A slower method that could be made to work: ras = arcpy.sa.Con(arcpy.sa.IsNull(d), 0, d);Sum = ras + arcpy.sa.Raster(AOI)
            #Sum.save(arcpy.env.scratchWorkspace + "\\T_" + d)
            #Sum = arcpy.sa.Con(arcpy.sa.IsNull(d), 0, d)

            #Delete any old tiles left in the directory from previous iteration
            print "Cleaning tile workspace"
            arcpy.env.workspace = folderTile
            olTiles = arcpy.ListRasters()
            for o in olTiles:
                try:
                    arcpy.Delete_management(o)
                except:
                    print "An old tile may not have been deleted"
                    print o

            # In order to deal with rasters having counts over 2 billion
            # split raster into tiles -> build attribute table -> read vat -> add together vat's
            print "Splitting summed raster"
            arcpy.SplitRaster_management(Sum, arcpy.env.scratchWorkspace + "\\ztemp\\tiles",
                                        d + "_", "NUMBER_OF_TILES", "TIFF", "#", "7 7",
                                        "#", "0", "PIXELS", "#", "#")
            tiles = arcpy.ListRasters(wild_card=d + "*")

            # Make an empty DataFrame that will be updated with each iteration of the
            # next loop.
            df2 = pd.DataFrame(index=[0, 1, 2, 3, 10, 11, 12, 13],
                            columns=["COUNT"]).fillna(value=0)

            # Loop through tiles and for each one, fill out a DataFrame equivalent of it's
            # VAT.  Then add (combine) with the DataFrame df2 to keep a running total.
            for tile in tiles:
                try:
                    arcpy.BuildRasterAttributeTable_management(tile, overwrite=True) # !!! This step necessary or else the sum of tile's will be incorrect !!!
                    RCount = arcpy.GetCount_management(tile)
                    RCount = int(RCount.getOutput(0))
                    if RCount != 0:
                        rows = arcpy.SearchCursor(tile)
                        for r in rows:
                            df3 = pd.DataFrame(index=[0, 1, 2, 3, 10, 11, 12, 13],
                                            columns=["COUNT"]).fillna(value=0)
                            df3.loc[r.getValue("VALUE"), "COUNT"] = r.getValue("COUNT")
                            df2 = df2.add(df3)
                    else:
                        problematic.append(d)
                        print tile
                except:
                    problematic.append(d)
                    print "Caution!!! " + tile # Enter code to verify that it's a 100% NoData situation that landed here?

            # Do some table manipulation to prep for the next step.
            print "Cleaning up tiles and munging tables"
            df2["Categ"] = [ValueMap[x] for x in df2.index]
            df2.set_index("Categ", drop=True, inplace=True)

            # Fill out the species' entries in the main DataFrame using the one just created.
            indx = df2.index
            for x in indx:
                df1.loc[d, x] = int(df2.ix[x])

            # Delete tiles so that they aren't mistakenly used in the next iteration or run.
            for tile in tiles:
                arcpy.Delete_management(tile)

            # Get end time and time it took to run the species.
            endtime = datetime.now()
            delta = endtime - starttime
            print "Processing time: " + str(delta)

            # Fillout runtime and date fields in the main DataFrame.
            df1.loc[d, "RunTime"] = str(delta)
            df1.loc[d, "Date"] = str(timestamp)
        except:
            print "Hawaiian?"
            hawaii.append(d)
        '''

# Now that the value counts for each species have been created, calculate various
# fields of interest.
print "Calculating some fields"
df1.index.name = "tif"
df1["SummerHabTotal"] = df1["NonAOISummer"] + df1["AOISummer"] + df1["NonAOIYear"] + df1["AOIYear"]
df1["WinterHabTotal"] = df1["NonAOIWinter"] + df1["AOIWinter"] + df1["NonAOIYear"] + df1["AOIYear"]
df1["AOITotal"] = df1["AOINonHab"] + df1["AOISummer"] + df1["AOIWinter"] + df1["AOIYear"]
df1["PercSummerAOI"] = 100*((df1["AOISummer"] + df1["AOIYear"])/df1["SummerHabTotal"])
df1["PercWinterAOI"] = 100*((df1["AOIWinter"] + df1["AOIYear"])/df1["WinterHabTotal"])
df1.fillna(0, inplace=True)
df1["PercSummerAOI"] = [int(round(n)) for n in df1.PercSummerAOI]
df1["PercWinterAOI"] = [int(round(n)) for n in df1.PercWinterAOI]
df1["strUC"] = [i[0] + i[1:5].upper() + i[5] for i in df1.index]
df1 = df1[[ u'strUC', u'PercSummerAOI', u'PercWinterAOI', u'NonAOINonHab',
            u'NonAOISummer', u'NonAOIWinter', u'NonAOIYear', u'AOINonHab',
            u'AOISummer', u'AOIWinter', u'AOIYear', u'Date', u'RunTime',
            u'SummerHabTotal', u'WinterHabTotal', u'AOITotal']]
'''
# Remove rows for "negative" models
df1.drop(negatives, inplace=True)
df1.drop(problematic, inplace=True)
df1.drop(hawaii, inplace=True)
'''
# Print the results in the shell, eventually add code to write to a file somewhere.
print df1.filter(["strUC", "PercSummerAOI", "PercWinterAOI"]).fillna(value=0, inplace=True)

print "Negatives: " + str(negatives)
print "Potential problems: " + str(problematic)
print "Hawaiian? " + str(hawaii)

__Log("\n\n\n****************  PercentHabitatInAOI " + timestamp + "  **************************\n")
__Log("\nRasters with negative values: " + str(negatives) + "\n")
__Log("\nRasters skipped because problem during tiling: " + str(problematic) + "\n")
__Log("\nRasters likely skipped because hawaiian: " + str(hawaii) + "\n")
__Log("\nRasters that were processed: " + str(dists) + "\n")

# Save results from this run in a csv file
df1.to_csv(workDir + "\\archive\\Percent" + AOI_Name + starttime.strftime('%Y-%m-%d-%H') + ".csv")

# Load the master result table
dfMas = pd.read_csv(workDir + "\\Percent_in_" + AOI_Name + "_Master.csv", index_col="tif")
dfMas.to_csv(workDir + "\\archive\\Percent_in_" + AOI_Name + "_Master" + starttime.strftime('%Y-%m-%d-%H') + ".csv", index_col="tif")

#df1 = pd.read_csv(workDir + "\\Percent in " + AOI_Name + timestamp + ".csv", index_col="tif")
# Update the master table with data from this run
dfMas.update(df1)

# Any new species wouldn't have been added to dfMas with the update, so concat those.
# Get a list of index values in df1 that aren't in dfMas
newMod = [x for x in df1.index if x not in dfMas.index]
dfNewMod = df1.reindex(newMod)
dfNewMas = pd.concat([dfMas, dfNewMod])
dfNewMas.to_csv(workDir + "\\Percent_in_" + AOI_Name + "_Master.csv", index_col="tif")
