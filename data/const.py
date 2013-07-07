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

# list of upgrade abilities
UPGRADE_REBUILD = 'rebuild'
UPGRADE_CODE_HARDENING = 'code hardening'
UPGRADE_ASSEMBLY_OPTIMIZE = 'assembly optimize'
UPGRADE_ECHO_LOOP = 'echo loop'
UPGRADE_MAP_PEEK = 'map peek'
UPGRADE_ZAP = 'electro static zap'
UPGRADE_CODE_FREEZE = 'code freeze'
UPGRADE_PING_FLOOD = 'ping flood'
UPGRADE_FORK_BOMB = 'fork bomb'
UPGRADE_EXPLOIT = 'process exploit'
UPGRADE_DESERIALIZE = 'deserialize'

# define upgrade ability lookup
UPGRADES = [
    {
    'name': UPGRADE_REBUILD,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_CODE_HARDENING,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_ASSEMBLY_OPTIMIZE,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_ECHO_LOOP,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_MAP_PEEK,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_ZAP,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_CODE_FREEZE,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_PING_FLOOD,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_FORK_BOMB,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_EXPLOIT,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_DESERIALIZE,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
    {
    'name': None,
    'version': 0,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'cooldown': 0,
    },
]

# state machine constants
STATE_INTRO = 1
STATE_MENU = 2
STATE_HELP = 3
STATE_ABOUT = 4
STATE_PLAY = 5
STATE_DIALOG = 6
STATE_GAMEOVER = 7
STATE_CRASH = 8

# tile id of seen fog overlay
FOG_GID = 16

# tile id of unseen tiles
UNSEEN_GID = 24

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
