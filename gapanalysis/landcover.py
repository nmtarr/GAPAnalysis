'''
A collecton of funcions for common tasks related to land cover data.
'''
          
def ReclassLandCover(MUlist, reclassTo, keyword, workDir, lcPath, lcVersion, log):
    '''
    (list, string, string, string, string, string, string) -> raster object, saved map.
    
    Builds a national map of select systems from the GAP Landcover used in species
        modeling. Takes several minutes to run.
        
    Arguments:
    MUlist -- A list of land cover map unit codes that you want to reclass.
    reclassTo -- Value to reclass the MUs in MUlist to.
    keyword -- A keyword to use for output name.  Keep to <13 characters.
    workDir -- Where to save output and intermediate files.
    lcPath -- Path to the national extent land cover mosaic suitable for overlay analyses
        with the models.
    lcVersion -- The version of GAP Land Cover to be reclassified.
    log -- Path and name of log file to save print statements, errors, and code to.
    '''
    #################################################### Things to import and check out
    ###################################################################################    
    import arcpy, datetime, os
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput=True
    
    ########################################################## Some environment settings
    ####################################################################################  
    arcpy.env.pyramid = "PYRAMIDS" 
    arcpy.env.rasterStatistics = "STATISTICS"
    arcpy.env.overwriteOutput = True
    starttime = datetime.datetime.now()
    arcpy.env.workspace = workDir
    
    ################################################# Create directories for the output
    ###################################################################################
    if not os.path.exists(workDir):
        os.makedirs(workDir)
            
    ############################################# Function to write data to the log file
    ####################################################################################
    log = workDir + "/{0}_log.txt".format(keyword)
    if not os.path.exists(log):
        logObj = open(log, "wb")
        logObj.close()
    def __Log(content):
        print content
        with open(log, 'a') as logDoc:
            logDoc.write(content + '\n')    
    
    ########################################################### Write header to log file
    ####################################################################################
    __Log("#"*67)
    __Log("The statements from processing")
    __Log("#"*67)    
    __Log(starttime.strftime("%c"))
    __Log('\nThis reclassification is based on GAP Land Cover version {0}.\n'.format(lcVersion))
    __Log('\nProcessing {0} systems as "{1}".\n'.format(len(MUlist), keyword).upper())
    __Log('The ecological systems used for this reclassification were:')
    __Log(str(MUlist) + '\n')
        
    ################################################################ Make a remap object
    ####################################################################################
    def MakeRemapList(mapUnitCodes, reclassValue):
        remap = []
        for x in mapUnitCodes:
            o = []
            o.append(x)
            o.append(reclassValue)
            remap.append(o)
        return remap  
    try:
        remap = arcpy.sa.RemapValue(MakeRemapList(MUlist, reclassTo))
    except Exception as e:
        __Log("ERROR making Remap List - {0}".format(e))
        
    ################################################################ Reclass the lc map
    ####################################################################################
    __Log("\tReclassifying {0}".format(lcPath))
    lcObj = arcpy.sa.Raster(lcPath)
    try:
        lcReclassObj = arcpy.sa.Reclassify(lcObj, "VALUE", remap, "NODATA")
    except Exception as e:
        __Log("ERROR reclassifying land cover")
    
    ############################## Build a RAT, pyramid, and statistics; set nodata to 0
    ####################################################################################                                   
    try:
        __Log("Attempting to calculate statistics")
        arcpy.management.CalculateStatistics(lcReclassObj, skip_existing=False)
        __Log("Building a new RAT")
        arcpy.management.BuildRasterAttributeTable(lcReclassObj, overwrite=True)
    except Exception as e:
        __Log("ERROR building RAT, pyramids, or statistics - {0}".format(e))
    
    ######################################################################## Save result
    ####################################################################################
    resultTiff = workDir + keyword + ".tif"
    try:
        print("\tSaving")
        arcpy.management.CopyRaster(lcReclassObj, resultTiff)
    except Exception as e:
        __Log("ERROR saving reclassed land cover")
        
    ########################################################### Write closer to log file
    ####################################################################################
    endtime = datetime.datetime.now()
    runtime = endtime - starttime
    __Log('\nProcessing time was {0}'.format(runtime))
        
    ##################################### Return raster object of reclassed national map
    ####################################################################################  
    reclassed = arcpy.Raster(workDir + keyword + ".tif")
    return reclassed
                                