# A module of functions related to managing the data needed for analyses.

def CheckHabMaps(rasters, nodata=0, Format="TIFF", pixel_type="U2", maximum=3,
                 minimum=3, zero=False):
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
    zero -- True or False on whether to check for the existence of 0 values in the table.
    

    Examples:
    >>> BadProperties = CheckHabMaps(arcpy.ListRasters())
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
        print(r)
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
                        print(r + "  - has bad counts")
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
                        print(r + " - has a value greater than {0}".format(maximum))
                        overMax.append(rasObj.name)
                    if zero == True:
                        if value == 0:
                            print(r + " - has a value equal to 0")
                            zero.append(rasObj.name)
                if RowsOK == False:
                    noRows.append(rasObj.name)
        except:
            print("No Cursor")
            cursorProblem.append(rasObj.name)
            
    return {"WrongProjection":WrongProjection, "WrongNoDataValue":WrongNoDataValue,
            "WrongPixelType":WrongPixelType, "WrongFormat":WrongFormat, 
            "WrongMinimum":WrongMinimum, "WrongMaximum":WrongMaximum, 
            "BadCount":badCount, "CursorProblem":cursorProblem, "overMax":overMax,
            "NoRows":noRows, "Zeros":zero}

# def Make01Seasonal(rasters, seasons, from_dir, to_dir, CONUS_extent, 
#                    log="P:/Proj3/USGap/Vert/Model/Output/CONUS/log.txt"):
#     '''
#     (list, list, string, string, raster) -> saved rasters
    
#     Copies a GAP habitat map that is in the format of values 1-3 and nodata (no zeros) 
#         and with an extent defined by the species range to a full CONUS extent version
#         with zero's and 1's throughout. A raster is saved for each season in "Summer", 
#         "Winter", or "Any" directory.  Also adds 9 pixels to the upper left corner of 
#         the map if the conus raster has them.  Runtime for 1 species creating each season
#         is around 2 hours.  Consider 
        
#     Arguments:
#     rasters -- A list of rasters to copy.
#     seasons -- A list of seasons create rasters for.
#     from_dir -- Directory to copy rasters from.
#     to_dir -- Directory to create seasonal subdirectories into and save to.
#     log -- The log file to record progress to.
#     CONUS_extent -- A full continental extent raster (30m, albers), composed entirely of
#         zeros and counter pixels with value "1" in the top left corner if desired.  This
#         layer is used for setting the extent, snapgrid, and adding the counter pixels.
    
#     Examples:
#     >>> gapanalysis.data.MakeSeasonalBinary(rasters=arcpy.ListRasters(),
#                                             seasons=["any", "Summer", "w"],
#                                             from_dir="C:/data/maps/"
#                                             to_dir="C:/data/Output/",
#                                             CONUS_extent="C:/data/conus_ext_cnt",
#                                             log="P:/Proj3/USGap/Vert/Model/Output/Conus/log.txt")
#     >>>
#     '''
#     ################################################### import packages, set environments
#     #####################################################################################
#     import arcpy, os, datetime
#     arcpy.ResetEnvironments()
#     arcpy.CheckOutExtension("Spatial")
#     arcpy.env.overwriteOutput=True
#     arcpy.env.snapRaster = CONUS_extent
#     arcpy.env.pyramid = 'PYRAMIDS'
#     arcpy.env.rasterStatistics = "STATISTICS"
#     arcpy.env.cellSize = 30
#     arcpy.env.scratchworkspace = to_dir
#     arcpy.env.extent = CONUS_extent
#     arcpy.env.workspace = to_dir
    
#     ################################################### create directories for the output
#     #####################################################################################
#     summerDir = os.path.join(to_dir, 'Summer') 
#     winterDir = os.path.join(to_dir,'Winter')
#     anyDir = os.path.join(to_dir, 'Any')
#     for x in [summerDir, winterDir, anyDir]:
#         if not os.path.exists(x):
#             os.makedirs(x)
#     logg = open(log, "a")
#     logg.close()
    
#     ############################################## Function to write data to the log file
#     #####################################################################################
#     def __Log(content):
#         print(content)
#         with open(log, 'a') as logDoc:
#             logDoc.write(content + '\n')
            
#     ############################################################################  Process
#     #####################################################################################
#     for raster in rasters:
#         start1 = datetime.datetime.now()
#         date = start1.strftime('%Y,%m,%d')
#         print(raster)
#         print(str(rasters.index(raster) + 1) + " of " + str(len(rasters)))
#         rangewide = arcpy.Raster(from_dir + raster)
#         ############################################### expand, fill with zeros, and copy
#         #################################################################################
#         # Summer
#         if "Summer" in seasons or "s" in seasons or "S" in seasons or "summer" in seasons:
#             print("\tSummer")
#             try:
#                 print("\tReclassifying")
#                 summer = arcpy.sa.Con(rangewide, 1, where_clause="VALUE = 1 OR VALUE = 3")
#                 print("\tAdding 0's")            
#                 summer_0 = arcpy.sa.Con(arcpy.sa.IsNull(summer), 0, summer)
#                 print("\tAdding count pixels")            
#                 summer_cnt = summer_0 + CONUS_extent
#                 print("\tSaving")            
#                 arcpy.management.CopyRaster(in_raster=summer_cnt, 
#                                             out_rasterdataset=to_dir + "Summer/" + raster, 
#                                             pixel_type="1_BIT", 
#                                             nodata_value="")
#                 print("\tBuilding table")
#                 arcpy.management.BuildRasterAttributeTable(to_dir + "Summer/" + raster,
#                                                            overwrite=True)
#                 __Log(raster[:6] + "," + from_dir + raster + "," + summerDir + "/" + raster + "," + date)
#             except Exception as e:
#                 print(e)

#                 __Log(raster[:6] + "," + from_dir + raster + "," + summerDir + "/" + raster + "," + date + ",FAILED")
                                                         
#         # Winter
#         if "Winter" in seasons or "winter" in seasons or "W" in seasons or "w" in seasons:
#             print("\tWinter")
#             try:
#                 print("\tReclassifying")
#                 winter = arcpy.sa.Con(rangewide, 1, where_clause="VALUE = 2 OR VALUE = 3")
#                 print("\tAdding 0's")                 
#                 winter_0 = arcpy.sa.Con(arcpy.sa.IsNull(winter), 0, winter)
#                 print("\tAdding count pixels")                     
#                 winter_cnt = winter_0 + CONUS_extent
#                 print("\tSaving")            
#                 arcpy.management.CopyRaster(in_raster=winter_cnt, 
#                                             out_rasterdataset=to_dir + "Winter/" + raster, 
#                                             pixel_type="1_BIT", 
#                                             nodata_value="")
#                 print("\tBuilding table")
#                 arcpy.management.BuildRasterAttributeTable(to_dir + "Winter/" + raster,
#                                                            overwrite=True)
#                 __Log(raster[:6] + "," + from_dir + raster + "," + winterDir + "/" + raster + "," + date)
#             except Exception as e:
#                 print(e)
#                 __Log(raster[:6] + "," + from_dir + raster + "," + winterDir + "/" + raster + "," + date + ",FAILED")
                
#         # Any season
#         if "Any" in seasons or "any" in seasons or "a" in seasons or "A" in seasons:
#             print("\tAny")
#             try:
#                 print("\tReclassifying")            
#                 Any = arcpy.sa.Con(rangewide, 1, where_clause="VALUE > 0")
#                 print("\tAdding 0's")                 
#                 any_0 = arcpy.sa.Con(arcpy.sa.IsNull(Any), 0, Any)
#                 print("\tAdding count pixels")                     
#                 any_cnt = any_0 + CONUS_extent
#                 print("\tSaving")            
#                 arcpy.management.CopyRaster(in_raster=any_cnt, 
#                                             out_rasterdataset=to_dir + "Any/" + raster, 
#                                             pixel_type="1_BIT", 
#                                             nodata_value="")
#                 print("\tBuilding table")
#                 arcpy.management.BuildRasterAttributeTable(to_dir + "Any/" + raster,
#                                                            overwrite=True)
#                 __Log(raster[:6] + "," + from_dir + raster + "," + anyDir + "/" + raster + "," + date)
#             except Exception as e:
#                 print(e)
#                 __Log(raster[:6] + "," + from_dir + raster + "," + anyDir + "/" + raster + "," + date + ",FAILED")
        
#         end = datetime.datetime.now()
#         runtime = end - start1
#         print("\tTotal runtime: " + str(runtime))


# def Make0123(rasters, CONUS_extent, from_dir, to_dir, 
#              log="P:/Proj3/USGap/Vert/Model/Output/CONUS/log.txt"):
#     '''
#     (list, string, string, string, string, string) -> saved raster
    
#     Copies a GAP habitat map that is in the format of values 1-3 and nodata (no zeros) 
#         and with an extent defined by the species range to a full CONUS extent version
#         with zero's and original values throughout. Also adds 9 pixels to the upper 
#         left corner of the map if the CONUS_extent layer has them.  NOTE: This takes
#         about 25 minutes to run one species.
    
#     Arguments:
#     rasters -- A list of rasters to check.
#     CONUS_extent -- A raster with a national extent and zeros everywhere except for 
#         counter cells.  Also used as a snap raster.
#     from_dir -- Where to find the habitat maps to process.
#     to_dir -- Directory to work in and save output.  It should have a subdirectory named
#         "0123".
#     log -- Path to the log file used to keep track of habmap movement and creation.

#     Examples:
#     >>> gapanalysis.data.Expand_0s(rasters=arcpy.ListRasters(), 
#                                    CONUS_extent="C:/gapanalysis/data/CONUS_extent",
#                                    from_dir="C:/models/",
#                                    to_dir="C:/models/Output/",
#                                    log = "P:/Proj3/USGap/Vert/Model/Output/CONUS/log.txt")
#     >>>
#     '''
#     import arcpy, datetime
#     arcpy.CheckOutExtension("Spatial")
#     arcpy.overwriteOutput=True
#     arcpy.env.snapRaster = CONUS_extent
#     arcpy.env.extent = CONUS_extent
#     arcpy.env.workspace = to_dir
    
    
#     ######################################### Function to write data to the log file
#     ################################################################################
#     log = log
#     def __Log(content):
#         print(content)
#         with open(log, 'a') as logDoc:
#             logDoc.write(content + '\n')
            
#     ######################################### Expand each raster to Conus and add 0s
#     ################################################################################
#     for sp in rasters:
#         start1 = datetime.datetime.now()
#         date = start1.strftime('%Y,%m,%d')
#         print(sp)
#         Tiff = arcpy.Raster(from_dir + sp)
#         newTiff = to_dir + "0123/" + sp
#         try:
#             print("\tCon is Null")
#             ConNull = arcpy.sa.Con(arcpy.sa.IsNull(Tiff), 0, Tiff)
#             print("\tSumming")
#             newRast = ConNull + CONUS_extent
#             print("\tSaving")
#             arcpy.management.CopyRaster(newRast, newTiff, pixel_type="2_BIT", 
#                                         nodata_value="")
#             print("\tCalculating statistics")
#             arcpy.management.CalculateStatistics(newTiff)
#             print("\tBuilding RAT")
#             arcpy.management.BuildRasterAttributeTable(newTiff, overwrite=True)
#             end = datetime.datetime.now()
#             runtime = end - start1
#             print("\tTotal runtime: " + str(runtime))
#             __Log(sp[:6] + "," + from_dir + sp + "," + newTiff + "," + date)
#         except Exception as e:
#             print('ERROR expanding raster - {0}'.format(e))
#             __Log(sp[:6] + "," + from_dir + sp + "," + newTiff + "," + date + ",Failed")

