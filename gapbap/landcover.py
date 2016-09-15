'''
A collecton of funcions for common tasks related to land cover data.
'''
          
def ReclassLandCover(MUlist, reclassTo, keyword, workDir, lcDir, log):
    '''
    (list) -> raster object, saved map.
    
    Builds a national map of select systems from the GAP Landcover used in species
        modeling. Takes several hours to run.
        
    Arguments:
    MUlist -- A list of land cover map unit codes that you want to reclass.
    reclassTo -- Value to reclass the MUs in MUlist to.
    keyword -- A keyword to use for output name.  Keep to <13 characters.
    workDir -- Where to save output and intermediate files.
    lcDir -- Where to find the regional landcover rasters.  The landcover rasters must 
        be named 'lcgap_gp', 'lcgap_ne', 'lcgap_nw', 'lcgap_se', 'lcgap_sw',
        and 'lcgap_um'.
    log -- Path and name of log file to save print statements, errors, and code to.
    '''
    #################################################### Things to import and check out
    ###################################################################################    
    import arcpy, datetime, os
    arcpy.CheckOutExtension("Spatial")
    
    ########################################################## Some environment settings
    ####################################################################################  
    LCLoc = lcDir + "/"
    arcpy.env.overwriteOutput = True
    starttime = datetime.datetime.now()   
        
    ######### Get list of regional land covers to reclassify, reset workspace to workdir
    ####################################################################################
    arcpy.env.workspace = LCLoc
    regions = arcpy.ListRasters()
    regions  = [r for r in regions if r in ['lcgap_gp', 'lcgap_ne', 'lcgap_nw', 
                                            'lcgap_se', 'lcgap_sw', 'lcgap_um']]
    arcpy.env.workspace = workDir
    
    ################################################# Create directories for the output
    ###################################################################################
    outDir = os.path.join(workDir, keyword)
    if not os.path.exists(outDir):
        os.makedirs(outDir)
            
    ############################################# Function to write data to the log file
    ####################################################################################
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
        
    ################################################################ Reclass the regions
    ####################################################################################
    MosList = []
    for lc in regions:
        grid = arcpy.sa.Raster(LCLoc + lc)
        try:
            RegReclass = arcpy.sa.Reclassify(grid, "VALUE", remap, "NODATA")
        except Exception as e:
            __Log("ERROR reclassifying regional land cover - {0}".format(e))
            
        MosList.append(RegReclass)
        try:
            RegReclass.save(workDir + "rc" + lc)
        except Exception as e:
            __Log("ERROR saving regional land cover - {0}".format(e))
            
    ############################################## Mosaic regional reclassed land covers
    ####################################################################################
    arcpy.management.MosaicToNewRaster(MosList, workDir, keyword,"", "", 
                                       "", "1", "MAXIMUM", "")
                                       
    ###################################################### Build pyramids and statistics
    ####################################################################################                                   
    try:
        arcpy.management.BuildPyramidsandStatistics(workDir + "\\" + keyword)
    except Exception as e:
        __Log("ERROR building pyramids and statistics - {0}".format(e))
        
    ########################################################### Write closer to log file
    ####################################################################################
    endtime = datetime.datetime.now()
    runtime = endtime - starttime  
    __Log('\nProcessing time was {0}'.format(runtime))
        
    ##################################### Return raster object of reclassed national map
    ####################################################################################  
    reclassed = arcpy.Raster(workDir + "\\" + keyword)
    return reclassed
                                