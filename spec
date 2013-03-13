Alive, the roguelike spec.

## MAP

Each level is a BBS computer system you visit.

Our game levels use a 32x32 tiled map. Each level fits on one screen.
The dark, minimal and make use of scanlines, patterened dots and subtle
glow. The main color theme is blue, with green red and yellow hilighting
buttons or events.

There are 11 wall tiles, each for the four cartesian directions, and
then for the connectors where walls join into corners or t-junctions.

Tile types:

* Walls
* Gates
* Terminals. Tile attributes handle these events:
    + Trigger doors with a challenge roll.
    + Display story related messages.
    + 
* Backdoor leads to the next level.
* Code bank to upgrade your abilities. One-shot per level.


## NPC's / AI's

Non Player Characters use the same  base as the player, 
allowing our hero to temporarily take control of them. 

Some AI's idle in their area, others may patrol the perimiter of the map. 
Of course any one of them will follow you if spotted or provoked.

We write their attack/health points as ATK/HP, or 1/2.

NPC types:

* ICE, 1/1
    these guys guard each level. They patrol the level searching for
    intruders. They 


## CODE

Using the Tiled map editor, by adding the 'blocks' bit to a tile's properties makes walls in game. The objects layer items will always block a player. They also call back so we known what is happening.

So adding a map object with the property "action_transmute" with a value to the new tile_id. We can test for this on object collision callbacks. Transmorgify! Thus we can open a closed door. Transmute drops away after the first time.

The "action_finger" allows a tile to point to another tile to action instead, who can transmorg. We use the target's name as the value -- map objects have name & type properties -- Now we open doors with switches.

We can have both actions on the same object, effectively expiring and fingering an accomplice. Chainload a few and instant bridge or flooding.

It becomes a npc (ambush) or item (rewards) spawner. 
