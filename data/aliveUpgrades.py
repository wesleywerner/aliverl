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

import trace
import rlhelper

# list of upgrade abilities
REGEN = 'regen'
CODE_HARDENING = 'code hardening'
ASSEMBLY_OPTIMIZE = 'assembly optimize'
ECHO_LOOP = 'echo loop'
MAP_PEEK = 'map peek'
ZAP = 'electro static zap'
CODE_FREEZE = 'code freeze'
PING_FLOOD = 'ping flood'
FORK_BOMB = 'fork bomb'
EXPLOIT = 'process exploit'
DESERIALIZE = 'deserialize'

# Define a list of all possible upgrades available to the player.
# 'enabled' is used in-game for various reasons, but can also be set
# here to include/exclude it from the game.
UPGRADES = [
    {
    'name': REGEN,
    'description':
        ("You gain insight into reclaiming lost bits, reincorporating them "
         "back into your processing unit allowing you to regenerate some "
         "health whenever you enter a node."
         ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'use_targeting': False,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': CODE_HARDENING,
    'description':
        ("By analyzing logs from past attacks you are able to pinpoint flaws "
         "in your own code and patch them, allowing you increase your "
         "maximum health."
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'use_targeting': False,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': ASSEMBLY_OPTIMIZE,
    'description':
        ("It's not easy being written in a sub-optimal language. "
         "You restructure your own code, replacing slower routines with "
         "optimized assembly, allowing you to increase your movement speed."
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'use_targeting': False,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': ECHO_LOOP,
    'description':
        ("You learn the art of capturing malicious packets, and through some "
         "voodoo trickery you can pipe some of it back to the sender, "
         "allowing you to split any damage you may receive and echo part of "
         "it back to your attacker."
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 1,
    'max_targets': 1,
    'use_targeting': False,
    'cost': 1,
    'duration': 6,
    'cooldown': 3,
    },
    {
    'name': MAP_PEEK,
    'description':
        ("You gain insight into the binary space tree mapping nodes use. "
         "You can Peek into these memory maps, increasing your view range. "
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': True,
    'reach': 0,
    'max_targets': 0,
    'use_targeting': False,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': ZAP,
    'description':
        ("You master the art of shuffling your feet on the fuzzy-logic carpet "
         "to build up an electro-static charge. "
         "Useful to Zap nearby enemy with."
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 2,
    'max_targets': 1,
    'use_targeting': True,
    'cost': 2,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': CODE_FREEZE,
    'description':
        ("You discover that AI are susceptible to rogue NOP commands via a "
         "flaw in the node controller. By targetting NOPs to certain AI you "
         "can force them to eat up their cycles, freezing their movement "
         "loops for a short while."
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 2,
    'max_targets': 1,
    'use_targeting': True,
    'cost': 2,
    'duration': 2,
    'cooldown': 2,
    },
    {
    'name': PING_FLOOD,
    'description':
        ("You can tap into a node's communication system, allowing you to "
         "flood nearby enemy with garbage packets, slowing down "
         "their movement while they try to filter through the noise. "
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 3,
    'max_targets': 1,
    'use_targeting': True,
    'cost': 1,
    'duration': 4,
    'cooldown': 4,
    },
    {
    'name': FORK_BOMB,
    'description':
        ("A fork bomb is as destructive as it is simple: "
         "A code that replicates itself, with each replicant doing the same, "
         "creates a powerful shockwave that damages nearby AI. "
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'use_targeting': True,
    'cost': 0,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': EXPLOIT,
    'description':
        ("By studying the signatures that trail AI, you are able to determine "
         "what signals their underlying code use for movement. You can spoof "
         "these to gain control of an AI for a short while. "
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 4,
    'max_targets': 1,
    'use_targeting': True,
    'cost': 5,
    'duration': 6,
    'cooldown': 10,
    },
    {
    'name': DESERIALIZE,
    'description':
        ("You can map the positional matrix around you, allowing you to "
         "deserialize and blink into the chosen direction. Version 4 allows "
         "you to cross wall boundaries. "
        ),
    'version': 1,
    'enabled': True,
    'availability': [1],
    'passive': False,
    'reach': 3,
    'max_targets': 0,
    'use_targeting': False,
    'cost': 2,
    'duration': 0,
    'cooldown': 0,
    },
    {
    'name': None,
    'description': '',
    'version': 1,
    'enabled': False,
    'availability': [],
    'passive': False,
    'reach': 0,
    'max_targets': 0,
    'use_targeting': False,
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

    use_targeting:
        True if this ability requires a target.

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
                use_targeting=False,
                cost=0,
                duration=0,
                cooldown=0,
                ):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = enabled
        self.availability = availability
        self.passive = passive
        self.reach = reach
        self.max_targets = max_targets
        self.use_targeting = use_targeting
        self.cost = cost
        self.duration = duration
        self.cooldown = cooldown

        # internals
        self._cooldown_count = 0
        # track the total effect applied across all versions of an upgrade
        # so that we may reverse it later if an upgrade is purged.
        self._combined_effect = 0
        # count down the turns while this upgrade is busy affecting the game
        self._busy_countdown = 0

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

        return (self.enabled and
                not self.passive and
                self._cooldown_count == 0 and
                self._busy_countdown == 0
                )

    @property
    def is_active(self):
        """
        This upgrade has been triggered by the player and is still in effect.

        """

        return (self._busy_countdown > 0)

    @property
    def is_cooling(self):
        """
        This upgrade has done working and is cooling down.

        """

        return (self._busy_countdown == 0) and (self._cooldown_count > 0)

    @property
    def versioned_busy_countdown(self):
        """
        Gets the busy countdown value for this version of this upgrade.

        """

        #TODO calculate a value based on our version, and the upgrade type.
        return self.duration

    def version_up(self):
        """
        Updates the version.

        """

        self.version += 1

    def apply_upgrade(self, character):
        """
        An action to perform when this upgrade is installed or upgraded.
        Mostly applies to passive abilities that affect the player.

        Returns a human readable message of the effect, or None if nothing
        happend.

        """

        # a neat way to test bonus multipliers (n) is this method that
        # prints each version's value and a running total of all versions.
        #def bonus(n):
            #t = 0
            #for i in range(1, 6):
                #v = i * n
                #t += v
                #print('version %s increase by %s, for total = %s' % (i, v, t))

        # heal more
        if self.name == REGEN:
            bonus = 0.3 * self.version
            self._combined_effect += bonus
            character.health = rlhelper.clamp(
                character.health + bonus, 0, character.max_health)

        # increase max hp
        if self.name == CODE_HARDENING:
            bonus = 0.5
            self._combined_effect += bonus
            character.max_health += bonus
            return '+%s max health' % bonus

        # increase speed
        elif self.name == ASSEMBLY_OPTIMIZE:
            bonus = 0.5
            self._combined_effect += bonus
            character.speed -= bonus
            return '+%s speed' % bonus

        # increase view range
        elif self.name == MAP_PEEK:
            bonus = 0.5
            self._combined_effect += bonus
            character.view_range += bonus
            return '+%s sight' % bonus

    def purge_upgrade(self, character):
        """
        Reverse the effects this upgrade has added to the character.

        Returns a human readable message of the effect, or None if nothing
        happend.

        """

        # increase max hp
        if self.name == CODE_HARDENING:
            character.max_health -= self._combined_effect
            return '-%s health' % self._combined_effect

        # increase speed
        elif self.name == ASSEMBLY_OPTIMIZE:
            character.speed += self._combined_effect
            return '-%s speed' % self._combined_effect

        # increase view range
        elif self.name == MAP_PEEK:
            character.view_range -= self._combined_effect
            return '-%s sight' % self._combined_effect

    def activate(self, owner, target):
        """
        Activates this upgrade's ability, usually for a short period, after
        which a cooldown may ensue.

        Mostly applies to non-passive upgrades, i.e. ones the player manually
        actions.

        """

        if self.ready:
            self._busy_countdown = self.versioned_busy_countdown
            self._cooldown_count = self.cooldown
            trace.write('activated "%s" for %s turns' %
                (self.name, self._busy_countdown))

    def step(self):
        """
        Step a turn for this upgrade. We tick over any counters and adjust
        our state to suit.

        """

        if self._busy_countdown > 0:
            self._busy_countdown -= 1
            trace.write('%s is active for %s turns' %
                (self.name, self._busy_countdown))
        elif self._cooldown_count > 0:
            self._cooldown_count -= 1
            trace.write('%s cooldown for %s turns' %
                (self.name, self._cooldown_count))

def from_level(level):
    """
    Returns a list of available upgrades for the given level.

    """

    return [u for u in UPGRADES if level in u['availability'] and u['enabled']]


def from_name(upgrade_name):
    """
    Get an upgrade instance by it's name.
    """

    match = [u for u in UPGRADES if u['name'] == upgrade_name]
    if match:
        return Upgrade.from_dict(match[0])


def from_list(comparisson_list, upgrade_name):
    """
    Get an upgrade from a list of upgrades, or None if it is not in the list.
    """

    match = [u for u in comparisson_list if u.name == upgrade_name]
    if match:
        return match[0]
