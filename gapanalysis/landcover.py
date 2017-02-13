'''
A collecton of funcions for common tasks related to land cover data.
'''
          
def ReclassLandCover(MUlist, reclassTo, keyword, workDir, lcDir, lcVersion, log):
    '''
    (list, string, string, string, string, string, string) -> raster object, saved map.
    
    Builds a national map of select systems from the GAP Landcover used in species
        modeling. Takes several minutes to run.
        
    Arguments:
    MUlist -- A list of land cover map unit codes that you want to reclass.
    reclassTo -- Value to reclass the MUs in MUlist to.
    keyword -- A keyword to use for output name.  Keep to <13 characters.
    workDir -- Where to save output and intermediate files.
    lcDir -- Where to find the regional landcover rasters.  The landcover rasters must 
        be named 'lcgap_gp', 'lcgap_ne', 'lcgap_nw', 'lcgap_se', 'lcgap_sw',
        and 'lcgap_um'.
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
    if not os.path.exists(workDir):
        os.makedirs(workDir)
            
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
        
    ################################################################ Reclass the regions
    ####################################################################################
    MosList = []
    for lc in regions:
        __Log("Reclassifying {0}".format(lc))
        grid = arcpy.sa.Raster(LCLoc + lc)
        try:
            RegReclass = arcpy.sa.Reclassify(grid, "VALUE", remap, "NODATA")
        except Exception as e:
            __Log("ERROR reclassifying regional land cover - {0}".format(e))
            
        MosList.append(RegReclass)
        '''
        try:
            RegReclass.save(workDir + "rc" + lc)
        except Exception as e:
            __Log("ERROR saving regional land cover - {0}".format(e))
        '''
            
    ############################################## Mosaic regional reclassed land covers
    ####################################################################################
    try:
        __Log("Mosaicking reclassified regional outputs")
        arcpy.management.MosaicToNewRaster(input_rasters=MosList, output_location=workDir, 
                                           raster_dataset_name_with_extension=keyword + ".tif",
                                           pixel_type="8_BIT_UNSIGNED", cellsize=30, 
                                           number_of_bands=1, mosaic_method="MAXIMUM")
    except Exception as e:
        __Log("ERROR mosaicing regions - {0}".format(e))
                                       
    ############################## Build a RAT, pyramid, and statistics; set nodata to 0
    ####################################################################################                                   
    try:
        mosaic = arcpy.Raster(workDir + keyword + ".tif")
        __Log("Changing nodata value to 0")
        arcpy.management.SetRasterProperties(in_raster=mosaic, nodata="1 0") 
        __Log("Attempting to build pyramids and statistics")
        arcpy.management.CalculateStatistics(mosaic)
        __Log("Building a new RAT")
        arcpy.management.BuildRasterAttributeTable(mosaic)
        __Log("Setting cells with value 255 to nodata")
        mosaic2 = arcpy.sa.SetNull(mosaic, mosaic, "VALUE = 255")
        __Log("Saving setnulled raster")
        mosaic2.save(workDir + keyword + ".tif")
    except Exception as e:
        __Log("ERROR building RAT, pyramids, or statistics - {0}".format(e))
        
    ########################################################### Write closer to log file
    ####################################################################################
    endtime = datetime.datetime.now()
    runtime = endtime - starttime  
    __Log('\nProcessing time was {0}'.format(runtime))
        
    ##################################### Return raster object of reclassed national map
    ####################################################################################  
    reclassed = arcpy.Raster(workDir + keyword + ".tif")
    return reclassed
                                