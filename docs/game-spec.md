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
    A descriptive name also used as a unique key by the engine.

version:
    Starts at 1 and counts on each upgrade.

enabled:
    A flag that tells us if this ability can do anything. By default this is True, but game events later on may decide to disable some of the player's upgrade abilities.

availability:
    A list of level numbers where this ability is available as an upgrade. This obsoletes the need for a max version, but only balancing the game later will give real insight on this.

passive:
    Passive upgrades Actions on each player turn. They provide ongoing features that the player can enjoy.

range:
    The reach in tile count that this ability has control over. Any characters within this range to the player is at the whims of this upgrade.

max_targets:
    The number of targets that can be acted upon within range. This value may increase for each version, at the upgrade's discretion.

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

## list of passive upgrades

_Some upgrades increase in effectiveness for each version they are upgraded._

#TODO refresh this list from aliveUpgrades.py

regen: Regenerate some health whenever you enter a node.
code hardening: Increase to your maximum health.
assembly optimize: increase your movement speed.
echo loop: Split any damage you may receive and echo part of it back to your attacker.
map peek: Peek into the node memory map increasing your view range.

## list of active upgrades

electro static zap: Zap a nearby enemy with an electro-static charge.
code freeze: Freeze the code of nearby enemy, immobilizing them for a while.
ping flood: Flood nearby enemy with garbage packets, slowing down their movement while they try to filter through the noise.
fork bomb: deals x damage in range, and propagates via damaged AI by range.
exploit: take control of nearby AI.
deserialize: blink into a chosen direction for x distance.
