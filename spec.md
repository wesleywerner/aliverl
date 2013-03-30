# Alive, the roguelike

# Game level

Each level is a BBS computer system you visit.

Our game levels use a 32x32 tiled map. Each level fits on one screen. The dark, minimal and make use of scanlines, patterened dots and subtle glow. The main color theme is blue, with green red and yellow hilighting buttons or events.

## Level tiles



* Walls
* Gates
* Terminals. Tile attributes handle these events:
    * Trigger doors with a challenge roll.
    * Display story related messages.
* Exit leads to the next level.
* Code bank to upgrade your abilities. One-shot per level.

## Tiled map editor notes

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


# Gameplay

## Object Interactions

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

# Characters

The player and enemy bots are all characters. Their stats are defined
in ai.def by the tileset tile_id.

If current_turn % speed == 0 then we can move her.
Same goes for heal rates.

NPC types:

* ICE, 1/1
    these guys guard each level. They patrol the level searching for
    intruders. They 



# CODE

Using the Tiled map editor, by adding the 'blocks' bit to a tile's properties makes walls in game. The objects layer items will always block a player. Theyy also call back so we known what is happening.

So adding a map object with the property "action_transmute" with a value to the new tile_id. We can test for this on object collision callbacks. Transmorgify! Thus we can open a closed door. Transmute drops away after the first time.

The "action_finger" allows a tile to point to another tile to action instead, who can transmorg. We use the target's name as the value -- map objects have name & type properties -- Now we open doors with switches.

We can have both actions on the same object, effectively expiring and fingering an accomplice. Chainload a few and instant bridge or flooding.

It becomes a npc (ambush) or item (rewards) spawner. 

# Game stories

Stories are like campaigns the player can enjoy. They consist of multiple levels with story dialogue. Each story defines it's own tileset and character stat definitions.

A story lives in the directory "./data/stories/<your choice>/", and the story file is named "story.py"

## Story definition example

A story file defines a campaign the player can play. It lists the levels involved, dialogue the player can read, and some more.

Story files use valid python syntax.

~~~python
    # the title of this story
    title = 'in the beginning...'
    
    # list of levels to play
    levels = ['level1.tmx', 'level3.tmx', 'level3.tmx', ...]

    # define npc and player stats. (lowercase keys please)
    stats = {
        "player": {
                "attack": 1,
                "health": 4,
                "maxhealth": 4,
                "healrate": 4,
                "speed": 2,
                "stealth": 0,
                "mana": 0,
                "maxmana": 5,
                "manarate": 6
                },
        "enemy": {
                "attack": 1,
                "health": 2,
                "maxhealth": 2,
                "healrate": 2,
                "speed": 2,
                "stealth": 0,
                "mana": 5,
                "maxmana": 5,
                "manarate": 2,
                "mode": "patrol"
                }
            }
~~~

The filename must be story.py, it lives in data/stories/<your choice>/story.py.

## Story one

1. You awaken and find yourself conscious. You must find a way out of this node.
1. You find info on a term about a backup node that hosts copies of AI's. You figure you can use it to clone yourself and increase your chance of survival.
1. You encounter an AI who you ask for access to the backup node. It requests you to verify with an electronic signature. You agree to send it soon.
1. You find a series of terminals, through them you unlock a signature. You look for a secure comms node from where to send your new signature to get backup access.
1. You find the comms node and send the signature. You now have backup access.
1. After passing a series of locked doors, you find the master backup terminal. You access it and the backup starts.
1. You see a copy of yourself appear. Interacting with it reveals nothing but a dumb AI. A blinking master backup terminal shows a backup failed, anomaly detected.
