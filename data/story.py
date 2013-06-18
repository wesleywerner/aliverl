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
from configobj import ConfigObj

class StoryData(object):
    """
    Provides a high-level wrapper for reading game story data from story.conf.
    Each game story (aka campaing) has it's own conf.

    """

    def __init__(self, config_path):
        """
        Read config_path and prepare for action
        Will Except if the file does not exist, or is malformed.

        """

        self.conf = ConfigObj(config_path, file_error=True)

        # store the path where the story conf lives
        self.path = os.path.dirname(config_path)

    def animations(self, gid):
        """
        Return animation settings for a GID.
        """
        
        anims = self.conf['animations']
        for key, value in anims.items():
            if value.as_int('gid') == gid:
                return value

    def characters(self):
        """
        Return a list of character names as defined in the conf.
        """

        return self.conf['characters'].keys()

    def char_stats(self, name):
        """
        Returns stats defined for a character as a dictionary.
        Returns None if name not defined.

        """

        stats = self.conf['characters']
        if stats.has_key(name):
            return stats[name]

    def dialogue(self, key):
        """
        Returns dialogue words for the given key.
        """
        
        dialogues = self.conf['dialogue']
        if dialogues.has_key(key):
            return dialogues[key]

    def entry_message(self, level_number):
        """
        Return the entry message for a level, or None if empty.

        """
        
        key = self.level_key(level_number)
        if key:
            level = self.conf['levels'][key]
            if level.has_key('entry message'):
                return level['entry message']

    def level_file(self, level_number):
        """
        Returns the .tmx filename for the given level number.
        Returns None if the level number does not exist.

        """

        key = self.level_key(level_number)
        if key:
            return os.path.join(self.path, key)

    def level_key(self, level_number):
        """
        Returns the key for a level number.
        Returns None if the level does not exist.

        """
        
        # keep in mind our list is 0-based: position 0 stores level 1.
        level_keys = self.conf['levels'].keys()
        if level_number < len(level_keys):
            return level_keys[level_number - 1]

    def tile_blocks(self, gid):
        """
        Returns True if the given tile id is in our blocklist.

        """

        blocks = self.conf['blocking tiles']
        for key in blocks.keys():
            if str(gid) in blocks.as_list(key):
                return True
