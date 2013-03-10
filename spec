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

* wall, blocks creatures.
* I/O node, opens or closes doors. A challenge roll determines success.
* Backdoor, leads to the next level.
* Code bank, upgrade your abilities. One-shot per level.


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
