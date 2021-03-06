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

        # to format our config nicely we indent quoted paragraphs.
        # here we secretly strip these leading spaces.
        # do this for every screen in each dialogue.
        dialogues = self.conf['dialogue']
        for dialogue_key in dialogues.keys():
            data = dialogues[dialogue_key]
            for screen in data.keys():
                #stripped = '\n'.join([s.lstrip() for s
                #                in data[screen]['datas'].split('\n')])
                # remove the first 16 characters: dialogue indent.
                stripped = '\n'.join([s[16:] for s
                                in data[screen]['datas'].split('\n')])
                data[screen]['datas'] = stripped

    def animations_by_gid(self, gid):
        """
        Return animation settings for a GID.
        """

        anims = self.conf['animations']
        for key, value in anims.items():
            if value.as_int('gid') == gid:
                return value

    def animations_by_name(self, name):
        """
        Return animation settings for a given animatino name.
        """

        anims = self.conf['animations']
        for key, value in anims.items():
            if key == name:
                return value

    def raw_animation_data(self):
        """
        Returns all animation data.
        """

        return self.conf['animations']

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

        name = name.lower()
        stats = self.conf['characters']
        for key in stats.keys():
            if key.lower() == name:
                return stats[key]

    def dialogue(self, key):
        """
        Returns dialogue words for the given key.
        """

        dialogues = self.conf['dialogue']
        if key in dialogues.keys():
            return dialogues[key]

    def entry_message(self, level_number):
        """
        Return the entry message for a level, or None if empty.

        """

        key = self.level_key(level_number)
        if key:
            level = self.conf['levels'][key]
            if 'entry message' in level.keys():
                return level['entry message']

    def level_title(self, level_number):
        """
        Return the title for a level, or None if empty.

        """

        key = self.level_key(level_number)
        if key:
            level = self.conf['levels'][key]
            if 'title' in level.keys():
                return level['title']

    def entry_dialogue(self, level_number):
        """
        Get the entry dialogue for a level, or None if empty.

        """

        key = self.level_key(level_number)
        if key:
            level = self.conf['levels'][key]
            if 'entry dialogue' in level.keys():
                return level['entry dialogue']

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
        if level_number <= len(level_keys):
            return level_keys[level_number - 1]

    def level_number(self, level_name):
        """
        Returns the number of a level by file name.
        Returns None if the file name is not in the story config.
        Level numbers are not zero based, fyi.

        """

        keys = self.conf['levels'].keys()
        if level_name in keys:
            return keys.index(level_name) + 1


    def tile_blocks(self, gid):
        """
        Returns True if the given tile id is in our blocklist.

        """

        blocks = self.conf['blocking tiles']
        for key in blocks.keys():
            if str(gid) in blocks.as_list(key):
                return True
