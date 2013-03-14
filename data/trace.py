TRACE = True

def write(text):
    """ Writes trace output if enabled. """
    if TRACE:
        print('\n' + text)

def error(text):
    """ Writes error output. """
    print('\nERROR: ' + text)
