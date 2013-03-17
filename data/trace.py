TRACE = True

def write(text):
    """ Writes trace output if enabled. """
    if TRACE:
        if type(text) is list:
            text = str.join('* ', text)
        if len(text) > 0:
            print('* %s' % (text, ))

def error(text):
    """ Writes error output. """
    print('\n# ERR: ' + text)
