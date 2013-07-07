# Abilities

Abilities provide extra functionality for the player, they are crafted to allow new players to surive easier, and experienced or mad players to explore different playing styles.

Abilities can optionally be upgraded in version, meaning they increase in effectiveness, or they can be one-time abilities that provide a specific feature.

It is still undetermined how ability upgrades are triggered, a @upgrade action on map objects seems the most flexible.

As abilities are considered game engine material they are stronlgy familiar with the game model.

_note how there is no view related data stored here. this is all game model data, the view is responsible for deciding what to draw where._

**attributes**
````
name:
    A descriptive name also used as a unique key by the engine.

version:
    Starts at 1 and counts on each upgrade.

enabled:
    A flag that tells us if this ability can do anything.

availability:
    A list of level numbers where this ability is available as an upgrade.

passive:
    Actions on each turn. passive abilities do not take a target.

range:
    The reach this ability has.

max_targets:
    The number of targets that can be acted upon within range.

cost:
    The cost of using this ability. Passive abilities ignore this.

cooldown:
    The number of turns before this ability can be used again. Passive abilities ignore this.

````

**methods**
````
action(player, targets):
    Activates the ability and gets given the player and optionally a list of targets within the ability's range.
````

## list of passive abilities

rebuild: Restore your health to max on level warp.
code hardening: increase to your max HP.
assembly optimize: increase your speed.
echo loop: bounce any attacks back to the attacker, splitting the damage done.
map peek: peek into the node's memory map, increasing your view range.

## list of active abilities

electro static zap: zaps for ranged damage.
code freeze: immobilize nearby AI's for x turns.
ping flood: slows nearby AI.
fork bomb: deals x damage in range, and propagates via damaged AI by range.
exploit: take control of nearby AI.
deserialize: blink into a chosen direction for x distance.
