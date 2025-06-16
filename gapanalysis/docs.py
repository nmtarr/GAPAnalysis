"""
A module of functions related to searching/manipulating text files.
"""

import os


##################################
#### Public function to write the given text to a given document.
def Write(document, text, mode='append'):
    '''
    (string, string, [string]) -> boolean

    Writes text to a document. If necessary, the function will create the
        directories and the file itself. Ensures closure of the document.

    Returns True if the function ran successfully. Otherwise, returns False.

    Arguments:
    document -- The file to which the text will be added.
    text -- The text you wish to write to the document.
    mode -- Indicates whether you wish to append or overwrite the document. The
        only valid entries are 'Append' or 'Overwrite' (capitalization is
        irrelevant). 'Append' is the default option.
        Technically, 'a' or 'o' can be entered instead.

    Examples:
    >>> Write('mydoc.txt', 'Write this test')
    True
    >>> Write('mydoc.txt', 'Write this test', 'overwrite')
    True
    '''
    try:
        # Ensure that the user enters a valid entry for the mode
        while True:
            mode = mode.lower()
            if mode == 'a':
                mode = 'append'
            elif mode == 'o':
                mode = 'overwrite'
            if mode == 'append' or mode == 'overwrite':
                break
            else:
                mode = raw_input('The second argument to the Write function should be\neither \'append\' to add to an existing document or \'overwrite\' to\nreplace/create the file.\n\nPlease enter a valid argument: ')

        modeDict = {'append':'a', 'overwrite':'w'}

        # For the next step, you must treat the document by its absolute path,
        # in case it was passed as just the document name with the working
        # directory set
        document = os.path.abspath(document)
        # If the document's directory does not exist, create it
        if not os.path.exists(os.path.dirname(document)):
            os.makedirs(os.path.dirname(document))

        # Write the content to the output document
        with open(document, modeDict[mode]) as d:
            d.write(str(text) + '\n')

        return True

    except Exception as e:
        print("Exception in function Write(): ", e)
        return False