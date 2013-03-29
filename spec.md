Alive, the roguelike spec.

MAP
============

Each level is a BBS computer system you visit.

Our game levels use a 32x32 tiled map. Each level fits on one screen.
The dark, minimal and make use of scanlines, patterened dots and subtle
glow. The main color theme is blue, with green red and yellow hilighting
buttons or events.

There are 11 wall tiles, each for the four cartesian directions, and
then for the connectors where walls join into corners or t-junctions.

### Tile types:

* Walls
* Gates
* Terminals. Tile attributes handle these events:
    + Trigger doors with a challenge roll.
    + Display story related messages.
    + 
* Backdoor leads to the next level.
* Code bank to upgrade your abilities. One-shot per level.

### Tiled map editor notes:

* Place static map tiles on a Tile Layer.
* Place AI, player, doors and such on an Object Layer.
* Set wall tiles "blocks" bit property in the Tilesets picker.
    This applies to both map tiles and Objects that use these tiles.
* Set individual Object properties:
    * name: used to target when fingering. can have duplicates.
    * type: door (always blocks), switch. 
    * fingers: also fingers_1..N. 
            points to another object to action. will action all 
            who share the same name.
    * on_finger: also on_finger_1..N. values include:
            * transmute=tile_id[, rotate_tile_id, ..N]


### Object Interactions

Give map objects these properties to interact with the game.
The action names only match the start, you can add any descriptive
words after the name (you can't have two actions with the same name).
You may also append any action name with the word 'once' for that effect.

* message=text: 
    print an in-game message.

* fingers=name: 
    action the named object. It's actions will
    process, except for other finger actions. You can finger multiple
    object with 'finger 1', 'finger that enemy', 'finger door'.
    Object that share the same name will all be fingered too.
    
* on_finger=action: 
    where action is one of:
    * give=value: give this object a new property
        This simulates a terminal that has to be fingered for it
        to work later, like a power switch or an unlock.
    * transmute=id[,id..]: change this object tile to another.
        A comma list of id's will rotate between each.
        This simulates open/closing doors.

* dialog=name: 
    show the dialog text by name as defined in dialogs.def

Examples:
    + fingers_secret_door=transmute=2
    + message=A secret door opens
    change the tile to a non blockable one, and tell the player about it.
    
    + on_finger

Characters
============

The player and enemy bots are all characters. Their stats are defined
in ai.def by the tileset tile_id.

If current_turn % speed == 0 then we can move her.
Same goes for heal rates.

NPC types:

* ICE, 1/1
    these guys guard each level. They patrol the level searching for
    intruders. They 



CODE
============

Using the Tiled map editor, by adding the 'blocks' bit to a tile's properties makes walls in game. The objects layer items will always block a player. Theyy also call back so we known what is happening.

So adding a map object with the property "action_transmute" with a value to the new tile_id. We can test for this on object collision callbacks. Transmorgify! Thus we can open a closed door. Transmute drops away after the first time.

The "action_finger" allows a tile to point to another tile to action instead, who can transmorg. We use the target's name as the value -- map objects have name & type properties -- Now we open doors with switches.

We can have both actions on the same object, effectively expiring and fingering an accomplice. Chainload a few and instant bridge or flooding.

It becomes a npc (ambush) or item (rewards) spawner. 


============
