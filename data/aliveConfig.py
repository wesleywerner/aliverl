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

import os
from configobj4 import ConfigObj


class AliveConfig(object):
    """
    Provides a high-level wrapper for reading game config.

    """

    def __init__(self):
        """
        Read config_path and prepare for action
        Will Except if the file does not exist, or is malformed.

        """

        self.conf = ConfigObj('alive.conf', file_error=True)

    def story_list(self):
        """
        Get the list of stories available to play.
        Returns a list of (name, description)
        """

        return [(k, v['description']) for k, v in self.conf['stories'].items()]

if __name__ == '__main__':
    test = AliveConfig()
    print(test.story_list())
    for name, desc in test.story_list():
        print(name + ': ' + desc)