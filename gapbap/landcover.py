# -*- coding: utf-8 -*-
'''
This a place to put functions that are in development.
'''
'''
A collecton of funcions for common tasks related to land cover data.
'''
def MakeRemapList(mapUnitCodes, reclassValue):
    '''
    (list, integer) -> list of lists

    Returns a RemapValue list for use with arcpy.sa.Reclassify()

    Arguments:
    mapUnitCodes -- A list of land cover map units that you with to reclassify.
    reclassValue -- The value that you want to reclassify the mapUnitCodes that you
        are passing to.

    Example:
    >>> MakeRemap([1201, 2543, 5678, 1234], 1)
    [[1201, 1], [2543, 1], [5678, 1], [1234, 1]]
    '''
    remap = []
    for x in mapUnitCodes:
        o = []
        o.append(x)
        o.append(reclassValue)
        remap.append(o)
    return remap  
            
def ReclassLandCover(MUlist, reclassTo, keyword, workDir):
    '''
    (list) -> map
    
    Builds a national map of select systems from the GAP Landcover used in species
        modeling. Takes several hours to run.
        
    Arguments:
    MUlist -- A list of land cover map unit codes that you want to reclass.
    reclassTo -- Value to reclass the MUs in MUlist to.
    keyword -- A keyword to use for output name.  Keep to <13 characters.
    workDir -- Where to save output and intermediate files.
    '''
    import gapageconfig
    
    try:
        import arcpy
        arcpy.CheckOutExtension("Spatial")
        
        #Some environment settings  
        LCLoc = gapageconfig.land_cover + "/"
        arcpy.env.overwriteOutput = True
        arcpy.env.cellSize = "30"
        arcpy.env.snapraster = gapageconfig.snap_raster
        
        #Get list of regional land covers to reclassify, reset workspace to workdir.
        arcpy.env.workspace = LCLoc
        regions = arcpy.ListRasters()
        regions  = [r for r in regions if r in ['lcgap_gp', 'lcgap_ne', 'lcgap_nw', 'lcgap_se',
                                                'lcgap_sw', 'lcgap_um']]
        arcpy.env.workspace = workDir
        
        #Make a remap object
        remap = arcpy.sa.RemapValue(MakeRemapList(MUlist, reclassTo))
        
        #A list to append to
        MosList = []
        
        #Reclass the rest of the regions
        for lc in regions:
            grid = arcpy.sa.Raster(LCLoc + lc)
            RegReclass = arcpy.sa.Reclassify(grid, "VALUE", remap, "NODATA")
            MosList.append(RegReclass)
            RegReclass.save(workDir + "TT" + lc)
        
        #Mosaic regional reclassed land covers
        arcpy.management.MosaicToNewRaster(MosList, workDir, keyword,"", "", 
                                           "", "1", "MAXIMUM", "")
        #arcpy.management.CalculateStatistics(workDir + "\\" + keyword)
        #arcpy.management.BuildPyramids(workDir + "\\" + keyword)
    except:
        print "May not have been able to load arcpy"                                           