# Alive, the roguelike

Each level is a BBS computer system you visit.

Our game levels use a 32x32 tiled map. Each level fits on one screen. The dark, minimal and make use of scanlines, patterened dots and subtle glow. The main color theme is blue, with green red and yellow hilighting buttons or events.

## Object Interactions

Give map objects these properties to interact with the game. The actions match the start of the action name, you can add descriptive words after the name (like 'Foo'), you can't have two actions with the same name.

You may append an action name with the word 'once' for a one-time trigger. This applies to both walk-in actions and fingered actions.

The GID mentioned is the numbered index of the tileset image.

### Walk-in actions

_These trigger when bumping into an object._

* message <foo once> = text 
    print a message for the player.

* fingers <foo once> = target name
    process triggers on the named object.
    objects with the same name will all get fingered.
    fingered targets won't finger others (recursion prevention)

* dialogue <foo once> = key
    show a game dialogue screen with the text defined with the key in story.py.

* exit
    exit for the next level.

### Fingered target actions

_These trigger objects being fingered._

* on finger <foo once> = action
    
    * give = newpropertyname=newpropertyvalue
        give this object a new property.
    * transmute = id <,gid..n>
        change this object tile to another.
        this affects it blocking characters and similar tests.
        A comma list of gid's will rotate between each trigger.
    * addframes = gid <,gid..n>
        Add one or more frames to the object sprite's animation.
        Note this does not change the object gid, it only adds sprites.
    * killframe
        removes the last sprite animation frame.
    * replaceframes = gid <,gid..n>
        replace the sprite animation image(s) with one or more images.

* dialog <foo once> = key
    show the dialog text by key as defined in dialogs.def

### Examples

Change a locked door tile to a non blockable open door tile.

1. switch object:
    * fingers = locked door
    * message = A secret door opens
1. locked door object:
    * on finger = transmute=2

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

Stories are like campaigns the player can enjoy. They consist of multiple levels with story dialogue. Each story defines it's own tileset and character stats.

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

## Story levels

Levels are built with the [2D Tiled map editor](http://www.mapeditor.org). This is the process of creating maps to play with Alive.

### Tileset

Each map has a tileset, an image with many 32x32 sized blocks of tile images. Each level can have it's own tileset image, or share the same image. This is a PNG file, it should not have a transparency layer, instead all magenta pixels (#FF00FF) are rendered transparent. The image size _must_ be in multiples of 32.



* Place static map tiles on a Tile Layer.
* Place AI, player, doors and such on an Object Layer.



The filename must be story.py, it lives in data/stories/<your choice>/story.py.

## Story one

1. You awaken and find yourself conscious. You must find a way out of this node.
1. You find info on a term about a backup node that hosts copies of AI's. You figure you can use it to clone yourself and increase your chance of survival.
1. You encounter an AI who you ask for access to the backup node. It requests you to verify with an electronic signature. You agree to send it soon.
1. You find a series of terminals, through them you unlock a signature. You look for a secure comms node from where to send your new signature to get backup access.
1. You find the comms node and send the signature. You now have backup access.
1. After passing a series of locked doors, you find the master backup terminal. You access it and the backup starts.
1. You see a copy of yourself appear. Interacting with it reveals nothing but a dumb AI. A blinking master backup terminal shows a backup failed, anomaly detected.
