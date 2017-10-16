# Simply run this module (no inputs or modifications needed) to update the help
# files for all of the gappack modules.
#

import sys, pydoc, os

#Where's the package located?
sys.path.append('')
import gapanalysis as ga

helpDir = '/GAPAnalysis/docs/documentation'
if not os.path.exists(helpDir):
    os.makedirs(helpDir)

for mod in ga.__all__:
    s = pydoc.plain(pydoc.render_doc('gapanalysis.' + mod))
    ga.docs.Write(os.path.join(helpDir, 'Help_' + mod + '.txt'), s, 'o')
