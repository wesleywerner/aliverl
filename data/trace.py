#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see http://www.gnu.org/licenses/.

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
