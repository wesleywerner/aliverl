# Abilities

Abilities provide extra functionality for the player, they are crafted to allow new players to surive easier, and experienced or mad players to explore different playing styles.

Abilities can optionally be upgraded in version, meaning they increase in effectiveness, or they can be one-time abilities that provide a specific feature.

It is still undetermined how ability upgrades are triggered, a @upgrade action on map objects seems the most flexible.

As abilities add coupled functionality, they are python classes. This is a level of configurability I am very happy to sacrifice for clarity, as abilities are considered game engine material.

_note how there is no view related data stored here. this is all game model data, the view is responsible for deciding what to draw where._

**attributes**
````
name:
    a descriptive name also used as a unique key by the engine.
version:
    starts at 1 and counts on each upgrade.
enabled:
    a flag that tells us if this ability can do anything.
availability:
    a list of level numbers where this ability is available as an upgrade.
passive:
    actions on each turn. passive abilities do not take a target.
requires_target:
    if True the game engine will prompt the player to select a target prior to calling this ability.

````

**methods**
````
action(player, target):
    activates the ability and gets given the player and optionally a target.
````