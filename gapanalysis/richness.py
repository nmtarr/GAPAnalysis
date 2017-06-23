def MapRichness(spp, groupName, outLoc, modelDir, season, intervalSize, 
                CONUSExtent, weight="None"):    
    '''
    (list, str, str, str, str, int, str) -> str, str

    Creates a species richness raster for the passed species. Also includes a
      table listing all the included species. Intermediate richness rasters are
      retained. That is, the code sums the rasters but saves the running total at interval
      size; the intermediate richness rasters are retained for spot-checking. Refer to the 
      output log file for a list of species included in each intermediate raster as well 
      as the code that was run for the process.

    Returns the path to the output richness raster and the path to the species
      table.

    Arguments:
    spp -- A list of GAP species codes to include in the calculation
    groupName -- The name you wish to use to identify the output directories
        and files (e.g., 'raptors')
    outLoc -- The directory in which you wish to place output and intermediate files.
    modelDir -- The directory that holds all of the GAP habitat map .tifs needed for the 
        analysis.  This directory must contain subdirectories names "Summer", "Winter", 
        and "Any". They need to have CONUS extent and be binary, 1_BIT .tifs.
    season -- Seasonal criteris for reclassifying the output.  Choose "Summer", "Winter", 
        or "Any". "Any" will reclassify output so that any value > 0 gets reclassed to 
        "1" and is the default. 
    intervalSize -- This number specifies how often to save the running tally as grids
        are added to it one-by-one.  For example, selecting 20 will mean that the tally 
        will be saved every time the number of maps summed is a multiple of 20.
    CONUSExtent -- A raster with a national/CONUS extent, and all cells have value of 0 except 
        for a 3x3 cell square in the top left corner that has values of 1.  The spatial reference
        should be NAD_1983_Albers and cell size 30x30 m.  Also used as a snap raster.
    weight -- option to weight each species to allow less widespead species to 
        count more.  Options are "None", "percentile", and "area".  None
        is the default and will weight each species equally (1).  Percentile
        will weight with 1/proportion of species (from the list you provided, 
        which is important to note) with a pixel count below the species' 
        pixel count.  The area option will use 1/species pixel count.  

    Example:
    >>> ProcessRichness(['aagtox', 'bbaeax', 'mnarox'], 'MyRandomSpecies', 
                        outLoc='C:/GIS_Data/Richness', modelDir='C:/Data/Model/Output',
                        season="Summer", intervalSize=20, weight="None",
                        log='C:/GIS_DATA/Richness/log_MyRandomSpecies.txt')
    C:\GIS_Data\Richness\MyRandomSpecies_04_Richness\MyRandomSpecies.tif, C:\GIS_Data\Richness\MyRandomSpecies.csv
    '''    
    
    import os, datetime, arcpy, pandas as pd
    from scipy import stats
    arcpy.CheckOutExtension('SPATIAL')
    arcpy.ResetEnvironments()
    arcpy.env.overwriteOutput=True
    arcpy.env.pyramid = 'NONE'
    arcpy.env.snapRaster = CONUSExtent
    arcpy.env.rasterStatistics = "STATISTICS"
    arcpy.env.cellSize = 30
    arcpy.env.extent = CONUSExtent
    starttime = datetime.datetime.now()      
    
    # Maximum number of species to process at once
    interval = intervalSize
    # Count the number of species in the species list
    sppLength = len(spp)
    # The seasonal input directory
    modelDir = modelDir + season + "/"
    
    ############################################# create directories for the output
    ###############################################################################
    outDir = os.path.join(outLoc, groupName)   
    arcpy.env.workspace = outDir
    intDir = os.path.join(outDir, 'Richness_intermediates')
    for x in [intDir, outDir]:
        if not os.path.exists(x):
            os.makedirs(x)
    log = outDir+"/Log_{0}.txt".format(groupName)
    if not os.path.exists(log):
        logObj = open(log, "wb")
        logObj.close()
    
    ######################################## Function to write data to the log file
    ###############################################################################
    def __Log(content):
        print content
        with open(log, 'a') as logDoc:
            logDoc.write(content + '\n')
    
    ################################################ Create a dataframe for weights
    ###############################################################################  
    outTable = os.path.join(outDir, groupName + '.csv')
    if weight != "None":
        weightsDF = pd.DataFrame()
        # Record habitat area per species in the table
        for sp in spp:
            habmap = arcpy.Raster(modelDir + sp)
            rows = arcpy.SearchCursor(habmap)
            for row in rows:
                if row.getValue("VALUE") == 1:
                    count = row.getValue("COUNT")
            weightsDF.loc[sp, "cnt"] = count
        if weight == "percentile":
            weightsDF["weight"] = 100.*(stats.rankdata(weightsDF.cnt, method="average")/len(weightsDF.cnt))
        if weight == "area":
            weightsDF["weight"] = [c*1. for c in weightsDF.cnt]
        weightsDF["weighted_value"] = 1./(weightsDF.weight)
        weightsDF.to_csv(outTable)
        
    if weight == "None":
        spTable = open(outTable, "a")
        for s in spp:
            spTable.write(str(s) + ", {0}".format(str(1)) + ",\n")
        spTable.close()
    
    ###################################################### Write header to log file
    ###############################################################################
    __Log("\n" + ("#"*67))
    __Log("The results from richness processing")
    __Log("#"*67)    
    __Log(starttime.strftime("%c"))
    __Log('\nProcessing {0} species as "{1}".\n'.format(sppLength, groupName).upper())
    __Log('Season of this calculation: ' + season)
    __Log('Weighting method: ' + weight)
    __Log('Table written to {0}'.format(outTable))
    __Log('\nThe species that will be used for analysis:')
    __Log(str(spp) + '\n')
    
    #################################### Sum rasters, saving the tally periodically
    ###############################################################################    
    tally = arcpy.Raster(CONUSExtent)
    counter = 1
    __Log("Summing")
    for sp in spp:
        try:
            starttime2=datetime.datetime.now()
            __Log(sp)
            habmap = arcpy.Raster(modelDir + sp)
            counter += 1
            print(counter)
            tally_file_name = intDir + "/Intermediate_{0}.tif".format(counter)
            # Determine the weight for the species and add accordingling
            if weight == "None":
                weight = 1
                __Log("\tvalue = " + str(1))
                tally = tally + 1
            if weight != "None":
                weight = weightsDF.loc[sp, "weight"]
                # These cases would produce float data type 
                # so multiply by 1000 for integers
                __Log("\tvalue = " + str((1/weight)))
                tally = tally + (habmap/weight)
            
            if counter - 1 in range(0, 2000, interval):
                if weight == "None":
                    tally.save(tally_file_name)
                if weight != "None":
                    intermediate = arcpy.sa.Int((tally*10000) + 0.5)
                    intermediate.save(tally_file_name)
                arcpy.management.BuildRasterAttributeTable(in_raster=tally_file_name,
                                                           overwrite=False)
                __Log('\tSaved to {0}'.format(tally_file_name))
                    
            """if  counter != tally.maximum:
                __Log('\tWARNING! Invalid maximum cell value in {0}'.format(tally_file_name))"""
            __Log("\tRuntime: " + str(datetime.datetime.now() - starttime2))
        except Exception as e:
            __Log("ERROR -- {0}".format(e))
            exit()
            
    #################################### The tally at the end is the final richness
    ###############################################################################         
    try:
        richness_file_name = outDir + "/Richness.tif"
        __Log('Saving richness raster to {0}'.format(richness_file_name))
        if weight != "None":
            finalrichness = arcpy.sa.Int((tally*10000) + 0.5)
            finalrichness.save(richness_file_name)
        if weight == "None":
            tally.save(richness_file_name)
        __Log('Richness raster saved')
        __Log('Building RAT')
        arcpy.management.BuildRasterAttributeTable(in_raster=richness_file_name,
                                                   overwrite=True)
    except Exception as e:
        __Log('ERROR in final richness save -- {0}'.format(e))
    
    runtime = datetime.datetime.now() - starttime
    __Log("Total runtime was: " + str(runtime))

    return tally, outTable