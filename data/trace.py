TRACE = True


def write(text):
    """
    Writes a message to stdout.
    """
    if TRACE:
        if type(text) is list:
            text = str.join('* ', text)
        if len(text) > 0:
            print('* %s' % (text, ))


def error(text):
    """
    Writes error output.
    """
    if type(text) is str:
        print('\n# ERR: ' + text)
    else:
        print(text)


def log_crash(error_message):
    """
    Log the crash to text file.
    """

    import datetime
    log = open('error.log', 'wt')
    log.write('ALIVE CRASH LOG - ' + datetime.datetime.now().strftime('%c'))
    log.write('\n' + str(error_message))
    log.close()
