TRACE = True

def write(text):
    """ Writes trace output if enabled. """
    if TRACE:
        print('* %s' % (text, ))

def error(text):
    """ Writes error output. """
    print('\n# ERR: ' + text)
