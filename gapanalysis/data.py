# -*- coding: utf-8 -*-
"""
A module of functions related to managing the data needed for analyses.


"""
def CheckHabitatMaps(rasters, nodata=0, Format="TIFF", pixel_type="U8", maximum=3,
                 minimum=3):
    '''
    (list) -> dictionary
    
    Returns a dictionary of lists, one for each error that the function tests for.
        It looks for tables with a count of values less than zero, raster values
        greater than 3, and rasters that have an issue with search cursors. 
        Also checks that the properties of a list of rasters, match the desired 
        properties for species models (TIFF, Albers projection, 8 bit unsigned 
        pixel type, NoDataValue = nodata). Designed for testing GAP species model output
        specifically.

        Keys:
        "WrongProjection" -- Raster has projection other than Albers.
        "WrongNoDataValue" -- Raster has nodata value other than nodata.
        "WrongPixelType" -- The pixel type isn't correct.
        "WrongFormat" -- Raster isn't the desired type.
        "WrongMinimum" -- Minimum from cell statistics is > allowable minimum.
        "WrongMaximum" -- Maximum from cell statistics is > allowable maximum.
        "BadCount" -- A pixel value has a count < or = 0.
        "CursorProblem" -- Arcpy can't create a cursor to read the attribute table so 
            the table is likely corrupt.
        "overMax" -- The table has a value > allowable maximum in it.
        "NoRows" -- A table exists, but doesn't have any rows.
        "Zeros" -- The value "0" exists in the table.
    
    Argument:
    rasters -- A list of rasters to check.
    nodata -- Designate a desired nodata value.
    Format -- The desired format (i.e., "TIFF" or "GRID") 
    maximum -- Allowable max value for the raster.
    minimum -- Allowable min value for the raster.

    Examples:
    >>> BadProperties = CheckRasters(arcpy.ListRasters())
    >>> a = BadProperties["WrongNoDataValue"]
    >>> a
    ['amwlfx.tif', 'andsax.tif']
    '''
    import arcpy, time
    
    #######################################  Initialize dictionaries for collection
    ###############################################################################
    WrongProjection = []
    WrongNoDataValue = []
    WrongPixelType = []
    WrongFormat = []
    WrongMinimum = []
    WrongMaximum = []
    noRows = []        
    badCount = []
    cursorProblem = []
    overMax = []
    zero = []

    ########################################################### Examine each raster
    ###############################################################################
    for r in rasters:
        print r
        time.sleep(.1)
        rasObj = arcpy.Raster(r)
        desObj = arcpy.Describe(rasObj)
        ######################################## Examine describe object properties
        ###########################################################################
        if desObj.spatialReference.projectionName != "Albers":
            WrongProjection.append(r)
        if desObj.format != Format:
            WrongFormat.append(r)
        if desObj.pixelType != pixel_type:
            WrongPixelType.append(r)
        if desObj.nodataValue != nodata:
            WrongNoDataValue.append(r)
        ######################################### Exmamine raster object properties
        ###########################################################################
        if rasObj.maximum > maximum:
            WrongMaximum.append(r)
        if rasObj.minimum > minimum:
            WrongMinimum.append(r)
        ########################################## Check the raster attribute table
        ###########################################################################
        try:
                # Make an indicator variable for checking whether the cursor is 
                # empty, otherwise the cursor will quietly pass tables with no rows.
                RowsOK = False                
                # Make a cursor as a test to see if there's a vat                
                cursor = arcpy.SearchCursor(rasObj)
                for c in cursor:
                    countt = c.getValue("COUNT")
                    if countt < 0 or countt == 0:
                        print r + "  - has bad counts"
                        badCount.append(rasObj.name)
                        RowsOK = True
                    elif countt > 0:
                        # Change RowsOK to True since the table has rows.                          
                        RowsOK = True
                    else:
                        pass
                    time.sleep(.1)
                    value = c.getValue("VALUE")
                    if value > maximum:
                        print r + " - has a value greater than {0}".format(maximum)
                        overMax.append(rasObj.name)
                    if value == 0:
                        print r + " - has a value equal to 0"
                        zero.append(rasObj.name)
                if RowsOK == False:
                    noRows.append(rasObj.name)
        except:
            print "No Cursor"
            cursorProblem.append(rasObj.name)
            
    return {"WrongProjection":WrongProjection, "WrongNoDataValue":WrongNoDataValue,
            "WrongPixelType":WrongPixelType, "WrongFormat":WrongFormat, 
            "WrongMinimum":WrongMinimum, "WrongMaximum":WrongMaximum, 
            "BadCount":badCount, "CursorProblem":cursorProblem, "overMax":overMax,
            "NoRows":noRows, "Zeros":zero}


def Expand_0s(rasters, CONUS_extent, from_dir, to_dir, snap_raster):
    '''
    (list, string, string, string, string) -> saved raster
    
    Copies a GAP habitat map that is in the format of values 1-3 and nodata (no zeros) 
        and with an extent defined by the species range to a full CONUS extent version
        with zero's and original values throughout. Also adds 9 pixels to the upper 
        left corner of the map if the CONUS_extent layer has them.  NOTE: This takes
        about 25 minutes to run one species.
    
    Arguments:
    rasters -- A list of rasters to check.
    CONUS_extent -- A raster with a national extent and zeros everywhere except for 
        counter cells.
    from_dir -- Where to find the habitat maps to process.
    to_dir -- Directory to work in and save output.
    snap_raster -- Location of snap raster to use.

    Examples:
    >>> gapanalysis.data.Expand_0s(rasters=arcpy.ListRasters(), 
                                   CONUS_extent="C:/gapanalysis/data/CONUS_extent",
                                   snap_raster="C:/gapanalysis/data/snap_raster", 
                                   from_dir="C:/models/"
                                   to_dir="C:/models/Expanded_0s")
    >>>
    '''
    import arcpy, datetime
    arcpy.CheckOutExtension("Spatial")
    arcpy.overwriteOutput=True
    arcpy.env.snapRaster = snap_raster
    arcpy.env.extent = CONUS_extent
    arcpy.env.workspace = to_dir
    
    for sp in rasters:
        start1 = datetime.datetime.now()
        print(sp)
        Tiff = from_dir + sp
        newTiff = to_dir + sp
        print("Copying")
        try:
            arcpy.management.CopyRaster(Tiff, newTiff,)
            print("Summing")
            newRast = arcpy.sa.CellStatistics([newTiff, CONUS_extent], "SUM", "DATA")
            print("Setting nodata value to 255")
            arcpy.management.SetRasterProperties(newRast, nodata="1 255")
            print("Saving")
            newRast.save(newTiff)
            print("Calculating statistics")
            arcpy.management.CalculateStatistics(newTiff)
            print("Building RAT")
            arcpy.management.BuildRasterAttributeTable(newTiff, overwrite=True)
            end = datetime.datetime.now()
            runtime = end - start1
            print("Total runtime: " + str(runtime))
        except Exception as e:
            print('ERROR expanding raster - {0}'.format(e))