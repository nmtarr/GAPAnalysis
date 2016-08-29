'''
N. Tarr, 23Sept2015.

This is a script to facilitate spatial queries of the GAP species
model data.  This script provides a table that answers the question "What percentage
of each species' habitat occurs in X subset of the cells within the contiguous US?"
It compares a group of species model output rasters, to a binary raster of your choosing
that could be a reclassification of the landcover or something like a binary 30m
pixel raster of urban.

The inputs for the script are (1) a directory containing the species model grids
that you wish to assess and (2) a "subset" grid coded as "10's" and "NoData"'s.
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

import arcpy, pandas as pd, os, shutil
arcpy.CheckOutExtension("Spatial")
from datetime import datetime
pd.set_option('display.width', 1000)
print "Running"

####################   Variables to set ################################
# Directory holding species model grids.  All grids in here will be processed.
Distributions = "P:\\Proj3\\USGap\\Vert\\Model\\Output"
arcpy.env.workspace = Distributions
dists = arcpy.ListRasters()
dists = [i[0] + i[1:5].upper() + i[5:] for i in dists]

# Subset layer of interest (e.g., landcover subset, grasslands). Must be a grid
# with values 10 and NoData and have a national extent.
Subset = "P:\\Proj3\\USGap\\Analysis\\Grasslands\\data\\nawpa_grass10"

# Keyword to use in naming output file (e.g., NAWPA Grasslands)
Keyword = "NAWPAGrasslands"

ProjDir = "P:\\Proj3\\USGap\\Analysis\\Grasslands"

# Environment variables
arcpy.env.Extent = Subset
arcpy.env.snapRaster = "P:\\Proj3\\USGap\\Vert\\Model\\data\\snapgrid"

#################################################################
arcpy.env.scratchWorkspace = ProjDir + "\\ztemp"
arcpy.env.cellSize = 30
arcpy.env.overwriteOutput = True

# Make a directory for the tiles that will be made later on.
folderTile = arcpy.env.scratchWorkspace + "\\ztemp\\tiles"
try:
    shutil.rmtree(folderTile)
    os.mkdir(folderTile)
except:
    pass

# Dictionary of values
ValueMap = {0: "NonSubsetNonHab",
            10: "SubsetNonHab",
            1: "NonSubsetSummer",
            2: "NonSubsetWinter",
            3: "NonSubsetYear",
            11: "SubsetSummer",
            12: "SubsetWinter",
            13: "SubsetYear"}

# Create empty dataframe for results
colList = ValueMap.values() + ["Date", "RunTime"]
df1 = pd.DataFrame(index=dists, columns=colList).fillna(value=0)

# MAke empt list to collect rasters with negatives
negatives = []

# Potential erroneous models
problematic = []

# Potential Hawaiian models
hawaii = []

# Loop through rasters and process
for d in dists:
    arcpy.env.workspace = Distributions
    print "\n-------" + d + "-------"

    # Start time
    starttime = datetime.now()
    timestamp = starttime.strftime('%Y-%m-%d')

    try:
        # Make a cursor as a test to see if there's a vat
        cursor = arcpy.SearchCursor(d)
        print("Attribute table found")

        for c in cursor:
            sign = c.getValue("COUNT")
            if sign < 0:
                    print d + "  - has negatives"
                    negatives.append(d)
            else:
                pass

        # Get out of the loop if there was a negative value.
        if d in negatives:
            print "Grid not processed"
        else:
            print "Proceeding"

            #Add together rasters
            print "Summing grids"
            Sum = arcpy.sa.CellStatistics([d, arcpy.sa.Raster(Subset)], "SUM", "DATA")

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
            print "Processing time: " + str(delta)

            # Fillout runtime and date fields in the main DataFrame.
            df1.loc[d, "RunTime"] = str(delta)
            df1.loc[d, "Date"] = str(timestamp)


    except:
        try:
            print "No attribute table"
            #Add together rasters

            print "Summing grids"
            Sum = arcpy.sa.CellStatistics([d, arcpy.sa.Raster(Subset)], "SUM", "DATA")
            # A slower method that could be made to work: ras = arcpy.sa.Con(arcpy.sa.IsNull(d), 0, d);Sum = ras + arcpy.sa.Raster(Subset)
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

# Now that the value counts for each species have been created, calculate various
# fields of interest.
print "Calculating some fields"
df1.index.name = "tif"
df1["SummerHabTotal"] = df1["NonSubsetSummer"] + df1["SubsetSummer"] + df1["NonSubsetYear"] + df1["SubsetYear"]
df1["WinterHabTotal"] = df1["NonSubsetWinter"] + df1["SubsetWinter"] + df1["NonSubsetYear"] + df1["SubsetYear"]
df1["SubsetTotal"] = df1["SubsetNonHab"] + df1["SubsetSummer"] + df1["SubsetWinter"] + df1["SubsetYear"]
df1["PercSummerSubset"] = 100*((df1["SubsetSummer"] + df1["SubsetYear"])/df1["SummerHabTotal"])
df1["PercWinterSubset"] = 100*((df1["SubsetWinter"] + df1["SubsetYear"])/df1["WinterHabTotal"])
df1.fillna(0, inplace=True)
df1["PercSummerSubset"] = [int(round(n)) for n in df1.PercSummerSubset]
df1["PercWinterSubset"] = [int(round(n)) for n in df1.PercWinterSubset]
df1["strUC"] = [i[0] + i[1:5].upper() + i[5] for i in df1.index]
df1 = df1[[ u'strUC', u'PercSummerSubset', u'PercWinterSubset', u'NonSubsetNonHab',
            u'NonSubsetSummer', u'NonSubsetWinter', u'NonSubsetYear', u'SubsetNonHab',
            u'SubsetSummer', u'SubsetWinter', u'SubsetYear', u'Date', u'RunTime',
            u'SummerHabTotal', u'WinterHabTotal', u'SubsetTotal']]

# Remove rows for "negative" models
df1.drop(negatives, inplace=True)
df1.drop(problematic, inplace=True)
df1.drop(hawaii, inplace=True)

# Print the results in the shell, eventually add code to write to a file somewhere.
print df1.filter(["strUC", "PercSummerSubset", "PercWinterSubset"]).fillna(value=0, inplace=True)

print "Negatives: " + str(negatives)
print "Potential problems: " + str(problematic)
print "Hawaiian? " + str(hawaii)

#Write to log
log = open("P:\\Proj3\\USGap\\Scripts\\NAWPA_Grasslands\\Log for Percent in Grassland.txt", "a")
log.write("\n\n\n****************  PercentHabitatInSubset.py " + timestamp + "  **************************\n")
log.write("\nRasters with negative values: " + str(negatives) + "\n")
log.write("\nRasters skipped because problem during tiling: " + str(problematic) + "\n")
log.write("\nRasters likely skipped because hawaiian: " + str(hawaii) + "\n")
log.write("\nRasters that were processed: " + str(dists) + "\n")
log.close()

# Save results from this run in a csv file
df1.to_csv(ProjDir + "\\archive\\Percent" + Keyword + starttime.strftime('%Y-%m-%d-%H') + ".csv")

# Load the master result table
dfMas = pd.read_csv(ProjDir + "\\Percent_in_" + Keyword + "_Master.csv", index_col="tif")
dfMas.to_csv(ProjDir + "\\archive\\Percent_in_" + Keyword + "_Master" + starttime.strftime('%Y-%m-%d-%H') + ".csv", index_col="tif")

#df1 = pd.read_csv(ProjDir + "\\Percent in " + Keyword + timestamp + ".csv", index_col="tif")
# Update the master table with data from this run
dfMas.update(df1)

# Any new species wouldn't have been added to dfMas with the update, so concat those.
# Get a list of index values in df1 that aren't in dfMas
newMod = [x for x in df1.index if x not in dfMas.index]
dfNewMod = df1.reindex(newMod)
dfNewMas = pd.concat([dfMas, dfNewMod])
dfNewMas.to_csv(ProjDir + "\\Percent_in_" + Keyword + "_Master.csv", index_col="tif")

'''
