
# GAPAnalysis
GAPAnalysis facilitates common steps in analyses of GAP habitat maps.  Users will need to have local copies of GAP habitat maps with the original file names.  

Geospatial analyses of the data may require snap grids and an extent raster.  These are included in data.zip.  conus_ext_cnt.tif is a CONUS extent raster (30m resolution) with values zero, except for 9 cells with value of 1 in the top left corner that are useful for error checking when summing lots of rasters.

So far, this package can be used to create species richness maps, calculate the overlay of individual or lists of species habitat with areas of interest, reclassification of GAP land cover map (2001) to a binary map of ecological systems of interest, and miscellaneous data management or manipulation tasks.  See the documentation folder and help files for function documentation.

Help files are available in "/docs/documentation" that list and document functions in each of the package's modules.

## Contributors
Nathan M. Tarr