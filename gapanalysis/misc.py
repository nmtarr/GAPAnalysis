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
    
    
def PlotRAT(raster, OgiveName, DistributionName, OgiveTitle="", DistributionTitle="", 
            dropMax=False, dropZero=False,):
    '''
    (string, string, string, [boolean], [boolean]) -> saved figures
    
    Creates and saves two figures that summarize a Raster Attribute Table (RAT).  The 
        Ogive plot is a graph of value vs. cumulative frequency (count).  The 
        distribution plot is a graph of the value vs. frequency (count).
    
    Argument:
    raster -- A path to a raster with an attribute table (RAT) to summarize.
    OgiveName -- Path and filename to use for the Ogive plot name. Give a ".png" suffix.
    DistribtuionName -- Path and filename to use for the plot of value vs. count.
        Give this a ".png" suffix.
    OgiveTitle -- Title to use for the Ogive plot.
    DistributionTitle -- Title to use for the distribution plot.
    dropMax -- True or False to drop the highest value from the table.  This is useful
        when using richness rasters that included "counter pixels" in the NW corner.
    dropZero -- True or False, will the row for zero values from the table before 
        plotting.  
    
    Example:
    >>> PlotRAT(raster="T:/temp/a_richness_map.tif", OgiveName="T:/temp/Ogive.png",
                DistributionName="T:/temp/RATdist.png", dropMax=True, dropZero=True,
                OgiveTitle="All Species", DistributionTitle="All Species",)
    '''
    import arcpy, pandas as pd
    
    # Create empty dataframe
    DF0 = pd.DataFrame(index=[], columns=[])
    DF0.index.name = "value"
    
    # Use search cursor to copy RAT to dataframe
    rows = arcpy.SearchCursor(raster)
    for row in rows:
        frequency = row.getValue("COUNT")
        value = row.getValue("VALUE")
        DF0.loc[value, "freq"] = frequency
        
    # Drop max value
    if dropMax == True:
        # Drop highest value/counter
        DF0 = DF0[:-1]
    
    # Drop zeros
    if dropZero == True:
        DF0 = DF0[DF0.index > 0]
    
    # Make Ogive plot
    DF1 = DF0.copy()
    DF1["cumFreq"] = DF1.freq.cumsum()
    DF1.drop("freq", axis=1, inplace=True)
    ax = DF1.plot(kind="line", legend=False, title=OgiveTitle)
    ax.set_ylabel("cumulative frequency (# cells)")
    fig = ax.get_figure()
    fig.savefig(OgiveName)
    
    # Make distribution plot
    ax2 = DF0.plot(kind="line", legend=False, title=DistributionTitle)
    ax2.set_ylabel("frequency (# cells)")
    fig2 = ax2.get_figure()
    fig2.savefig(DistributionName)


def RasterStats(raster):
    '''
    (string) -> dictionary
    
    Creates a dictionary of measures of central tendency for a raster's values.
        Includes mean, range (as a tuple), standard deviation, and coefficient
        of variation.  Handles integer or floating point rasters.
    
    Argument:
    raster -- A path to a raster to summarize.
        
    Example:
    >>> aDict = RasterStats(raster="T:/temp/a_richness_map.tif")
    '''
    import arcpy
    # Create dictionary for results
    resultsDict = {}
    # Calculate mean value
    mean = arcpy.GetRasterProperties_management(raster, "MEAN").getOutput(0)
    resultsDict["mean"] = float(mean)
    # Calculate std
    std = arcpy.GetRasterProperties_management(raster, "STD").getOutput(0)
    resultsDict["standard_deviation"] = float(std)
    # Calculate coefficient of variation
    cv = 100*(float(std)/float(mean))
    resultsDict["coefficient_of_variation"] = cv
    # Calculate the range
    _min = float(arcpy.GetRasterProperties_management(raster, "MINIMUM").getOutput(0))
    _max = float(arcpy.GetRasterProperties_management(raster, "MAXIMUM").getOutput(0))
    _range = float(_min), float(_max)
    resultsDict["range"] = _range
    # Return result 
    return resultsDict


def RATStats(raster, percentile_list, dropMax=False, dropZero=False):
    '''
    (string, list, [boolean], [boolean]) -> dictionary
    
    Creates a dictionary of measures of variability for a Raster Attribute Table (RAT).
        Includes mean, range (as a tuple), and percentile values from the list passed.
    
    Note: Uses pd.Series.searchsorted for getting percentile values.  This is a complicated
        process that should match quantile interpolation methods during comparisons 
        with values from other tables.  It seems to behave like "interpolation="higher"" 
        in pd.quantile().
    
    Argument:
    raster -- A path to a raster with an attribute table (RAT) to summarize.
    percentile_list -- A python list of percentiles to calculate and include in the 
        dictionary that is returned.
    dropMax -- True or False to drop the highest value from the table.  This is useful
        when using richness rasters that included "counter pixels" in the NW corner.
    dropZero -- True or False, will the row for zero values from the table before 
        plotting.  
    
    Example:
    >>> aDict = RATStats(raster="T:/temp/a_richness_map.tif", 
                       percentile_list=[25, 50, 75],
                       dropMax=True, 
                       dropZero=True)
    '''
    import arcpy, pandas as pd
    # Create empty dataframe
    DF0 = pd.DataFrame(index=[], columns=[])
    # Create dictionary for results
    resultsDict = {}
    # Use search cursor to copy RAT to dataframe
    rows = arcpy.SearchCursor(raster)
    for row in rows:
        frequency = row.getValue("COUNT")
        value = row.getValue("VALUE")
        DF0.loc[value, "freq"] = frequency
    # Drop max and/or zero if specified
    if dropMax == True:
        # Drop highest value/counter
        DF0 = DF0[:-1]
    if dropZero == True:
        DF0 = DF0[DF0.index > 0]
    # Calculate mean value
    DF0.index.name = "value"
    DF0.reset_index(drop=False, inplace=True)
    DF0["countXvalue"] = DF0.value * DF0.freq
    mean = DF0.countXvalue.sum()/DF0.freq.sum()
    resultsDict["mean"] = mean
    # Calculate std
    std = arcpy.GetRasterProperties_management(raster, "STD").getOutput(0)
    resultsDict["standard_deviation"] = float(std)
    # Calculate the range
    _min = DF0.value.min()
    _max = DF0.value.max()
    _range = _min, _max
    resultsDict["range"] = _range
    # Find percentile values
    DF0.drop("countXvalue", inplace=True, axis=1)
    DF0["cumFreq"] = DF0.freq.cumsum()
    for percentile in percentile_list:
        percentile_freq = DF0.freq.sum()*(percentile/100.)
        percentile_value = DF0.loc[DF0.cumFreq.searchsorted(percentile_freq)[0], "value"]
        resultsDict[str(percentile) + "th"] = percentile_value
    # Return result 
    return resultsDict