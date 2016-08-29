# -*- coding: utf-8 -*-
'''
A collecton of funcions for common tasks related to land cover data.
'''
from misc import MakeRemapList
            
def ReclassLandCover(MUlist, reclassTo, keyword, workDir, lcDir):
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
    '''
    import arcpy
    arcpy.CheckOutExtension("Spatial")
    
    #Some environment settings  
    LCLoc = lcDir + "/"
    arcpy.env.overwriteOutput = True
        
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
        RegReclass.save(workDir + "rc" + lc)
    
    #Mosaic regional reclassed land covers
    arcpy.management.MosaicToNewRaster(MosList, workDir, keyword,"", "", 
                                       "", "1", "MAXIMUM", "")
    arcpy.management.CalculateStatistics(workDir + "\\" + keyword)
    arcpy.management.BuildPyramids(workDir + "\\" + keyword)
    reclassed = arcpy.Raster(workDir + "\\" + keyword)
    return reclassed
                                