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

# Frames per second
FPS = 30

# state machine constants
STATE_INTRO = 1
STATE_MENU = 2
STATE_HELP = 3
STATE_ABOUT = 4
STATE_PLAY = 5
STATE_DIALOG = 6
STATE_LEVEL_FAIL = 7
STATE_INFO_HOME = 8
STATE_INFO_UPGRADES = 9
STATE_INFO_WINS = 10
STATE_CRASH = 42

# tile id of seen fog overlay
FOG_GID = 34

# tile id of unseen tiles
UNSEEN_GID = 51

# number of player positions to keep as a scent.
PLAYER_SCENT_LEN = 5

# let us hope this won't get shown too often.
CRASH_MESSAGE = ("I am sorry to report that Alive has crashed :(",
            "The error has been logged to errors.log",
            "",
            "You are welcome to try and continue if possible but depending",
            "what went wrong, you might experience some",
            "side affects.",
            "",
            "If you are reading this in a terminal, then I guess you",
            "can't continue.",
            "",
            "Press Escape to quit, or Enter to try continue.",
            )
