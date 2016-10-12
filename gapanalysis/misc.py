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
    

def CheckRasters(rasters):
    '''
    (list) -> dictionary
    
    Returns a dictionary of lists, one for each error that the function tests for.
        It looks for tables with a count of values less than zero, raster values
        greater than 3, and rasters that have an issue with search cursors. 
        Also checks that the properties of a list of rasters, match the desired 
        properties for species models (TIFF, Albers projection, 8 bit unsigned 
        pixel type, NoDataValue = 0). Designed for testing GAP species model output
        specifically.
    
        Keys:
        "WrongProjection" -- Raster has projection other than Albers.
        "WrongNoDataValue" -- Raster has nodata value other than 0.
        "WrongPixelType" -- The pixel type isn't 8 bit unsigned.
        "WrongFormat" -- Raster isn't a geotiff.
        "WrongMinimum" -- Minimum from cell statistics is > 3.
        "WrongMaximum" -- Maximum from cell statistics is > 3.
        "BadCount" -- A pixel value has a count < or = 0.
        "CursorProblem" -- Arcpy can't create a cursor to read the attribute table so 
            the table is likely corrupt.
        "OverThree" -- The table has a value > 3 in it.
        "NoRows" -- A table exists, but doesn't have any rows.
        "Zeros" -- The value "0" exists in the table.
    
    Argument:
    rasters -- A list of rasters to check.

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
    overThree = []
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
        if desObj.format != "TIFF":
            WrongFormat.append(r)
        if desObj.pixelType != "U8":
            WrongPixelType.append(r)
        if desObj.nodataValue != 0:
            WrongNoDataValue.append(r)
        ######################################### Exmamine raster object properties
        ###########################################################################
        if rasObj.maximum > 3:
            WrongMaximum.append(r)
        if rasObj.minimum > 3:
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
                    if value > 3:
                        print r + " - has a value greater than 3"
                        overThree.append(rasObj.name)
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
            "BadCount":badCount, "CursorProblem":cursorProblem, "OverThree":overThree,
            "NoRows":noRows, "Zeros":zero}