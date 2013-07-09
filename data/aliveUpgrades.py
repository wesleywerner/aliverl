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
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# See the UPGRADES section in the game-spec.md for detailed descriptions.

# list of upgrade abilities
UPGRADE_REGEN = 'regen'
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

# Define a list of all possible upgrades available to the player.
# 'enabled' is used in-game for various reasons, but can also be set
# here to include/exclude it from the game.
UPGRADES = [
    {
    'name': UPGRADE_REGEN,
    'description': """
        You gain insight into reclaiming lost bits, reincorporating them back
        into your processing unit allowing you to regenerate some health
        whenever you enter a node.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_CODE_HARDENING,
    'description': """
        By analyzing logs from past attacks you are able to pinpoint flaws
        in your own code and patch them, allowing you increase your
        maximum health.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_ASSEMBLY_OPTIMIZE,
    'description': """
        It's not easy being written in a sub-optimal language.
        You restructure your own code, replacing slower routines with
        optimized assembly, allowing you to increase your movement speed.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_ECHO_LOOP,
    'description': """
        You learn the art of capturing malicious packets, and through some
        voodoo trickery you can pipe some of it back to the sender, allowing
        you to split any damage you may receive and echo part of it
        back to your attacker.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 1,
    'max_targets': 1,
    'cost': 1,
    'duration': 4,
    'cooldown': 6,
    },
    {
    'name': UPGRADE_MAP_PEEK,
    'description': """
        You gain insight into the binary space tree mapping nodes use.
        You can Peek into these memory maps, increasing your view range.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_ZAP,
    'description': """
        You master the art of shuffling your feet on the fuzzy-logic carpet
        to build up an electro-static charge, useful to Zap nearby enemy with.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 2,
    'max_targets': 1,
    'cost': 2,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_CODE_FREEZE,
    'description': """
        You discover that AI are susceptible to rogue NOP commands via a flaw
        in the node controller. By targetting NOPs to certain AI you can
        force them to eat up their cycles, freezing their movement loops
        for a short while.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 2,
    'max_targets': 1,
    'cost': 2,
    'duration': 2,
    'cooldown': 2,
    },
    {
    'name': UPGRADE_PING_FLOOD,
    'description': """
        You can tap into a node's communication system, allowing you to
        flood nearby enemy with garbage packets, slowing down
        their movement while they try to filter through the noise.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 3,
    'max_targets': 1,
    'cost': 1,
    'duration': 4,
    'cooldown': 4,
    },
    {
    'name': UPGRADE_FORK_BOMB,
    'description': """
        A fork bomb is as destructive as it is simple:
        A code that replicates itself, with each replicant doing the same,
        creates a powerful shockwave that damages nearby AI.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': UPGRADE_EXPLOIT,
    'description': """
        By studying the signatures that trail AI, you are able to determine
        what signals their underlying code use for movement. You can spoof
        these to gain control of an AI for a short while.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 4,
    'max_targets': 1,
    'cost': 5,
    'duration': 6,
    'cooldown': 10,
    },
    {
    'name': UPGRADE_DESERIALIZE,
    'description': """
        You can map the positional matrix around you, allowing you to
        deserialize and blink into the chosen direction. Version 4 allows
        you to cross wall boundaries.
        """,
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 3,
    'max_targets': 0,
    'cost': 2,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': None,
    'description': '',
    'version': 1,
    'enabled': True,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
]


class Upgrade(object):
    """
    Represents an instance of an upgrade that adds
    functionality to a player.

    name:
        A descriptive name also used as a unique key by the engine.

    version:
        Starts at 1 and counts on each upgrade.

    enabled:
        A flag that tells us if this upgrade can do anything.

    availability:
        A list of level numbers where this upgrade is available.

    passive:
        Actions on each turn. passive abilities do not take a target.

    reach:
        The tile range this upgrade has when actioned. This includes other
        characters within the range of the player.

    max_targets:
        The number of targets that can be acted upon within range.

    cost:
        The cost of using this upgrade's ability. Passive upgrades ignore this.

    cooldown:
        The number of turns before this upgrade's ability can be used again.
        Passive upgrades ignore this.

    """

    def __init__(self,
                name=None,
                description=None,
                version=1,
                enabled=False,
                availability=[],
                passive=False,
                reach=0,
                max_targets=0,
                cost=0,
                duration=0,
                cooldown=0,
                ):
        self.name = name
        self.version = version
        self.enabled = enabled
        self.availability = availability
        self.passive = passive
        self.reach = reach
        self.max_targets = max_targets
        self.cost = cost
        self.cooldown = cooldown

        # internals
        self._cooldown_count = 0

    @classmethod
    def from_dict(cls, dictionary):
        """
        Creates an instance from the given upgrade dictionary entry
        and links the given model to an attribute of the same name.

        """

        spam = cls(**dictionary)
        #spam.model = model
        return spam

    @property
    def ready(self):
        """
        Is this upgrade is ready for action, not cooling down and enabled.

        """

        return self.enabled and self._cooldown_count == 0

    def version_up(self):
        """
        Updates the version.

        """

        self.version += 1


def get_available_upgrades(level):
    """
    Returns a list of available upgrades for the given level.

    """

    return [u for u in UPGRADES if level in u['availability'] and u['enabled']]
