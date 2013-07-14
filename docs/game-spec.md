# Upgrades

Upgrades provide a way to add additional abilities to the player. Whenever the player is presented with an upgrade screen, they can choose to install a new upgrade, or increase the version of an existing one. These become available on a per-level basis, so there is no limit to the versions an upgrade can receive. The version number indicates the effectiveness of an upgrade's effect.

This allows new players to surive easier, and mad players to explore different playing styles.

**design notes**

1. It is still undetermined how ability upgrades are triggered, a @upgrade action on map objects seems the most flexible.
2. As Upgrades are considered game engine material they are stronlgy familiar with the game model.
3. There is no view related data stored here. This is all game model data, the view is responsible for deciding what to draw where.

**attributes**

````
name:
    A name used by the engine.

description:
    Describes what this upgrade does and how it is used.

version:
    Starts at 1 and counts on each upgrade.

enabled:
    A flag that tells us if this ability can do anything. By default this is True, but game events later on may decide to disable some of the player's upgrade abilities.

availability:
    A list of level numbers where this ability is available as an upgrade. This obsoletes the need for a max version, but only balancing the game later will give real insight on this.

passive:
    Passive upgrades Actions on each player turn. They provide ongoing features that the player can enjoy.

reach:
    The reach in tile count that this ability has control over. Any characters within this range to the player is at the whims of this upgrade.

max_targets:
    The number of targets that can be acted upon within range. This value may increase for each version, at the upgrade's discretion.

use_targeting:
    True if this ability requires a target.

cost:
    The cost of using this ability. This is synonymous to mana in fantasy game, and the player cannot Action this upgrade if they do not have enough power to pay this cost. Passive abilities ignore this.

duration:
    The number of turns that this upgrade is effect once actioned. Passive abilities ignore this.

cooldown:
    The number of turns before this ability can be used again. Passive abilities ignore this.

````

**Upgrade abilities workflow**

Passive abilities will action on each player movement turn. For the rest the player must activate (action) these abilities manually, when this happens:

1. The upgrade is marked as @active for @duration turns.
2. While active the upgrade's abilities are in effect.
3. When @duration runs out, the @cooldown period prevents the upgrade from being activated until a later turn.

## list of upgrades

    REGEN,
    "You gain insight into reclaiming lost bits, reincorporating them "
    "back into your processing unit allowing you to regenerate some "
    "health whenever you enter a node."

    CODE_HARDENING,
    "By analyzing logs from past attacks you are able to pinpoint flaws "
    "in your own code and patch them, allowing you increase your "
    "maximum health."

    ASSEMBLY_OPTIMIZE,
    "It's not easy being written in a sub-optimal language. "
    "You restructure your own code, replacing slower routines with "
    "optimized assembly, allowing you to increase your movement speed."

    ECHO_LOOP,
    "You learn the art of capturing malicious packets, and through some "
    "voodoo trickery you can pipe some of it back to the sender, "
    "allowing you to split any damage you may receive and echo part of "
    "it back to your attacker."

    MAP_PEEK,
    "You gain insight into the binary space tree mapping nodes use. "
    "You can Peek into these memory maps, increasing your view range. "

    ZAP,
    "You master the art of shuffling your feet on the fuzzy-logic carpet "
    "to build up an electro-static charge. "
    "Useful to Zap nearby enemy with."

    CODE_FREEZE,
    "You discover that AI are susceptible to rogue NOP commands via a "
    "flaw in the node controller. By targetting NOPs to certain AI you "
    "can force them to eat up their cycles, freezing their movement "
    "loops for a short while."

    PING_FLOOD,
    "You can tap into a node's communication system, allowing you to "
    "flood nearby enemy with garbage packets, slowing down "
    "their movement while they try to filter through the noise. "

    FORK_BOMB,
    "A fork bomb is as destructive as it is simple: "
    "A code that replicates itself, with each replicant doing the same, "
    "creates a powerful shockwave that damages nearby AI. "

    EXPLOIT,
    "By studying the signatures that trail AI, you are able to determine "
    "what signals their underlying code use for movement. You can spoof "
    "these to gain control of an AI for a short while. "

    DESERIALIZE,
    "You can map the positional matrix around you, allowing you to "
    "deserialize and blink into the chosen direction. Version 4 allows "
    "you to cross wall boundaries. "
