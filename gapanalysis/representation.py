"""
Created Oct312016 by N. Tarr
Functions related to calculating the amount of species' habitat that falls within zones
of interest.
"""
def Calculate(zone_file, zone_name, zone_field, habitat_maps, speciesDir, workDir, 
              snap_raster):
    '''
    (string, string, string, list, string, string) -> pandas dataframe
    
    This function calculates the number of habitat pixels and proportion of each species'
        summer, winter, and year-round habitat that occurs in each "zone" of a raster. 
        It can be used to answer questions like "Which species have the largest 
        proportion of their habitat in forest map units?" or "How much habitat does the 
        NPS protect for each species?".  The processing creates a directory for saving 
        intermediate results including a csv file of results from the process and a log 
        file.  If the code has been run before for a different list of species, then it
        will update the previous table after saving a copy in "/Archive".  When the 
        process is run, new species are added to the existing table and existing entries
        are updated.  The result table contains a field for date run and runtime for 
        each species.  The table with all species that have been run is returned as a 
        pandas dataframe.
    
    Arguments:
    zone_file -- A raster layer of the continental U.S. with zones of interest assigned
        a unique value/code.  Must have following specs:
                a) areas of interest have numeric, integer codes
                b) 32 bit integer pixel type
                c) 30m x 30m
                d) Albers NAD83 projection
                e) 1 band
                f) GeoTiff format
                g) valid raster attribute table  
    zone_name -- A short name to use in file naming (e.g., "Pine")
    zone_field -- The field in in the zone_file to use in the process.  It must be
        an integer with unique values for each zone you are interested in. NOTE: Zero
        is not a valid value!!!
    habitat_maps -- Python list of GAP habitat maps to analyze. Needs to be a list of 
        geotiffs named like: "mSEWEx.tif".  
    speciesDir -- The directory containing the GAP habitat maps to use in the process.
    workDir -- The name of a directory to save all results, including subfolders, log file
        temp output, and final csv files.  This code builds several subfolders and files.
    snap_raster -- A 30x30m cell raster to use as a snap grid during processing.
    
    Example:
    >>>ProportionPineDF = ga.representation.Calculate(zone_file = "C:/data/Pine.tif",
                                                      zone_name = "Pine",
                                                      zone_field = "VALUE",
                                                      habitat_maps = ["mSEWEx.tif", "bAMROx.tif"]
                                                      speciesDir = "C:/data/speciesmaps/",
                                                      workDir = "C:/analyses/represenation/pine")
    '''
    ############################################################## Imports and settings
    ###################################################################################
    import arcpy, pandas as pd, os
    from datetime import datetime
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.extent = arcpy.Raster(zone_file).extent
    arcpy.env.snapRaster = snap_raster
    arcpy.env.scratchWorkspace = workDir
    arcpy.env.cellSize = 30
    arcpy.env.overwriteOutput = True
    arcpy.env.rasterStatistics = "STATISTICS"
    pd.set_option('display.width', 1000)
    
    ############################################### Function to check raster properties
    ###################################################################################
    def RasterReport(raster):
        print("----" + str(raster))
        print("\tMax: " + str(raster.maximum))
        print("\tMin: " + str(raster.minimum))
        print("\tNoDataValue: " + str(raster.noDataValue))
        desObj = arcpy.Describe(raster)
        print("\t" + str(desObj.spatialReference.projectionName))
        print("\t" + str(desObj.format))
        print("\t" + str(desObj.pixelType))
        print("\tInteger = " + str(raster.isInteger))
        print("\tHas RAT = " + str(raster.hasRAT))
        try:
            # Make an indicator variable for checking whether the cursor is 
            # empty, otherwise the cursor will quietly pass tables with no rows.
            RowsOK = False                
            # Make a cursor as a test to see if there's a vat                
            cursor = arcpy.SearchCursor(raster)
            for c in cursor:
                print("\tVALUE:COUNT")
                print "\t" + str(c.getValue("VALUE")) + ":" + str(c.getValue("COUNT"))
                countt = c.getValue("COUNT")
                if countt < 0:
                    print "\t" + raster + "  - has bad counts"
                    RowsOK = True
                elif countt > 0:
                    # Change RowsOK to True since the table has rows.                          
                    RowsOK = True
            if RowsOK == False:
                print("\tRows not OK")
        except:
            print "\tNo Cursor"
            
    ################################ Create the working directories if they don't exist
    ###################################################################################
    # Create working directory
    if not os.path.exists(workDir):
        os.makedirs(workDir)
    # Create a scratch workspace
    scratch = workDir + "/ztemp/"
    if not os.path.exists(scratch):
        os.makedirs(scratch)
    # Create directories for archiving results
    archive = workDir + "/Archive"
    if not os.path.exists(archive):
        os.makedirs(archive)
    
    ############################################ Function to write data to the log file
    ###################################################################################
    log = workDir + "/log.txt"
    def __Log(content):
        print content
        with open(log, 'a') as logDoc:
            logDoc.write(content + '\n')   
    
    starttime0 = datetime.now()
    timestamp = starttime0.strftime('%Y-%m-%d')
    __Log("\n\n\n****************  " + timestamp + "  **************************\n")
    __Log("\nRasters that were processed: " + str(habitat_maps[:]) + "\n")
    __Log("Checked for and built required directories, lists, & dataframes")
    
    ####################################################### Make a dictionary of values
    ###################################################################################
    ValueMap = {0: "NonHabitatPixels",
                1: "SummerPixels",
                2: "WinterPixels",
                3: "AllYearPixels"}
    
    ###################################### Inspect the zone raster to make sure it's OK
    ###################################################################################
    __Log("Checking zone raster properties")
    zone_file = arcpy.Raster(zone_file)
    RasterReport(zone_file)
    
    ######################################## Get list of unique values from zone raster
    ###################################################################################
    zoneCursor = arcpy.SearchCursor(zone_file)
    zoneValues = []
    for z in zoneCursor:
        zoneValues.append(z.getValue(zone_field))
    
    ################################################################# Some housekeeping
    ###################################################################################
    ### Build empty dataframe with hierarchical indexing
    colList = ValueMap.values() + ["Date", "RunTime"]
    indexSpecies = habitat_maps * len(zoneValues)
    indexSpecies.sort()
    indexList = [indexSpecies, zoneValues * len(habitat_maps)]
    df1 = pd.DataFrame(index=indexList, columns=colList).fillna(value=0)
    df1.index.names = ["GeoTiff", "Zone"]
    
    # Get out of the output folder
    arcpy.env.workspace = scratch
    
    ################################ Loop through rasters, sum species and zone rasters
    ###################################################################################
    for sp in habitat_maps:
        __Log("\n-------" + sp + "-------")
        starttime = datetime.now()
        timestamp = starttime.strftime('%Y-%m-%d')
        __Log("Copying habitat map to 32 bit, temp version")
        arcpy.management.CopyRaster(speciesDir + sp, scratch + sp, nodata_value=0, 
                                    pixel_type="32_BIT_UNSIGNED")
        __Log("Building raster object")
        spMap = arcpy.Raster(scratch + sp)
        RasterReport(spMap)
        __Log("Summing zone and species map")
        Sum = arcpy.sa.CellStatistics([spMap, zone_file * 10], "SUM", "DATA")
        __Log("Saving and checking summed raster")
        Sum.save(scratch + "tmpSum.tif")
        arcpy.management.CalculateStatistics(scratch + "tmpSum.tif")
        arcpy.management.BuildRasterAttributeTable(scratch + "tmpSum.tif", overwrite=True)
        RasterReport(arcpy.Raster(scratch + "tmpSum.tif"))
        
        ############################################## Fill out dataframes with results
        ###############################################################################
        # Make empty dataframe for species results, first build a list of index values    
        df2indexList = []
        for i in zoneValues:
            df2indexList = df2indexList + [i*10 + k for k in ValueMap.keys()]
        df2 = pd.DataFrame(index=df2indexList, columns=["COUNT"]).fillna(value=0)
        
        __Log("Reading summed raster's table, writing in a dataframe") 
        try:
            rows = arcpy.SearchCursor(Sum)
            for r in rows:
                if r.getValue("VALUE") not in df2.index:
                    __Log("ERROR!!!")
                __Log("Cursor: v{0}, c{1}".format(r.getValue("VALUE"), int(r.getValue("COUNT"))))
                df2.loc[r.getValue("VALUE"), "COUNT"] = r.getValue("COUNT")
            del(rows)
            del(r)
                
        except Exception as e:
            print("ERROR -- {0}".format(e))
            # Not doing anything will leave values set to zero in df2
    
        # Do some table manipulation to prep for the next step
        df2["Season"] = [ValueMap[int(str(x)[-1:])] for x in df2.index]
        df2["Zone"] = [int(str(l)[:-1]) for l in df2.index]
        df2.set_index(["Zone", "Season"], drop=True, inplace=True)
        # Fill out the species' entries in main DataFrame using the one just created
        # First you need a list of index values to loop on, since Dataframe is multiindexed
        df2Index = []
        for a in list(df2.index.levels[0]):
            for b in list(df2.index.levels[1]):
                df2Index.append((a,b))
        # Fill out df1 with values from df2
        for x in df2Index:
            df1.loc[(sp, x[0]), x[1]] = int(df2.loc[(x[0], x[1])])
    
        # Get end time and time it took to run the species
        endtime = datetime.now()
        delta = endtime - starttime
        __Log("Processing time: " + str(delta))
    
        # Fillout runtime and date fields in the main DataFrame
        df1.loc[sp, "RunTime"] = str(delta)
        df1.loc[sp, "Date"] = str(timestamp)
        
        # Delete intermediate files
        arcpy.management.Delete(scratch + sp)
        arcpy.management.Delete(scratch + "tmpSum.tif")
        
    ######################################## Data munging of the multispecies dataframe
    ###################################################################################
    __Log("\nCalculating some fields in multispecies dataframe")
    df3 = df1.reset_index(level=1)
    df3["strUC"] = [i[0] + i[1:5].upper() + i[5] for i in df3.index]
    df3["ZoneTotal"] = df3["NonHabitatPixels"] + df3["SummerPixels"] + df3["WinterPixels"] + df3["AllYearPixels"]
    df3["SummerPixels"] = df3.SummerPixels + df3.AllYearPixels
    df3["WinterPixels"] = df3.WinterPixels + df3.AllYearPixels
    df3["SummerPixelTotal"] = [sum(df3.loc[i]["SummerPixels"]) for i in df3.index]
    df3["WinterPixelTotal"] = [sum(df3.loc[i]["WinterPixels"]) for i in df3.index]
    df3["AllYearPixelTotal"] = [sum(df3.loc[i]["AllYearPixels"]) for i in df3.index]
    df3["PercSummer"] = 100*(df3["SummerPixels"]/df3["SummerPixelTotal"])
    df3["PercWinter"] = 100*(df3["WinterPixels"]/df3["WinterPixelTotal"])
    df3["PercYearRound"] = 100*(df3["AllYearPixels"]/df3["AllYearPixelTotal"])
    df3.fillna(0, inplace=True)
    
    # Specify the order of columns for convenience
    df3 = df3[[u'strUC', u'Zone', u'PercSummer', u'PercWinter', u'PercYearRound', 
               u'NonHabitatPixels', u'SummerPixels', u'WinterPixels', u'AllYearPixels', 
               u'ZoneTotal', u'SummerPixelTotal', u'WinterPixelTotal', u'AllYearPixelTotal', 
               u'Date', u'RunTime']]
                
    ############################################ Print the results in the shell and log
    ###################################################################################
    df3.set_index([df3.index, "Zone"], inplace=True)
    print(df3.filter(["Zone", "strUC", "PercSummer", "PercWinter", "PercYearRound"]))
    
    ######################################################### Update and save csv files
    ###################################################################################
    df3FileName = workDir + "/archive/" + zone_name + starttime.strftime('%Y-%m-%d-%H') + ".csv"
    __Log("Saving new species table to " + df3FileName)
    df3.to_csv(df3FileName, index_col=["GeoTiff", "Zone"])
    
    # Load the master result table
    masterFileName = workDir + "/Percent_in_" + zone_name + "_Master.csv"
    if os.path.exists(masterFileName):
        dfMas = pd.read_csv(masterFileName, index_col=["GeoTiff", "Zone"])
        __Log("Loaded " + masterFileName)
    else:
        dfMas = df3
    
    # Save an archive copy of master table/dataframe
    dfMas.to_csv(workDir + "/archive/" + zone_name + "_Master" + \
                starttime.strftime('%Y-%m-%d-%H') + ".csv", )
    __Log("Created " + workDir + "/archive/" + zone_name + "_Master" + \
            starttime.strftime('%Y-%m-%d-%H') + ".csv")
    
    __Log("Updating master table with new calculations")
    dfMas.update(df3)
    
    __Log("Concating species that haven't been run before")
    newMod = [x for x in df3.index if x not in dfMas.index]
    dfNewMod = df3.reindex(newMod)
    dfNewMas = pd.concat([dfMas, dfNewMod])
    dfNewMas.to_csv(masterFileName, index_col=["GeoTiff", "Zone"])
    
    ########################################################################## Clean up
    ###################################################################################
    df1 = None
    df2 = None
    df3 = None
    
    # Get end time and time it took to run all species
    endtime2 = datetime.now()
    delta2 = endtime2 - starttime0
    __Log("Total processing time: " + str(delta2))
    
    return dfMas