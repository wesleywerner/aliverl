# How to build a story for Alive

This doc will show you how to build a story for the game. It is a work in progress. If you have questions pop by were we live: https://github.com/wesleywerner/aliverl

**What is a GID?**

The game tileset is an image composed of many square pictures. Starting at top left and moving right (like how you would read a book), the first tile is #1, the second #1, and so forth. These are the Graphic ID's of the tiles, also known as a GID.

# Story definition format

Stories are campaigns the player can enjoy. They consist of multiple levels, character stats, story dialogue and more. A story lives in `./data/stories/<STORY_NAME>/story.conf`.

**Story template**

````
[ info ]

# the title of this story
title = cookie madness

# and some descriptive for this story
description = the AI's bake some binary cookies

[ levels ]
# Define the levels that make up this story. The order they appear here is the
# same order they will get played in. The name matches the map filename.
# You can define as many levels here as your heart wishes.

    [[ level1.tmx ]]
    # entry messages are shown as floating popups when you enter the level.

    entry message = You smell cookies...

[ blocking tiles ]
# This is a list of GID's that will block any player or AI character from moving onto it.
# This applies to both map tile layers, and object layers.
# You can place them all on one line too, I like to separate them for easier reading.

walls = 1, 2, 3, 4
doors = 33, 34, 35
terminals = 41, 42, 43
player = 97
npcs = 105, 113

[ characters ]
# Map objects that match these by name, will inherit the attributes defined here.
# We can quickly build levels by simply giving map object one of these names.
# The meaning of these values are explained below.

    [[ player ]]
    attack = 1
    health = 4
    maxhealth = 4
    healrate = 4
    speed = 2
    stealth = 0
    mana = 0
    maxmana = 5
    manarate = 6
    modes =

    [[ cookie thief ]]
    attack = 0
    health = 2
    maxhealth = 2
    healrate = 2
    speed = 4
    stealth = 0
    mana = 5
    maxmana = 5
    manarate = 2
    modes = random

[ animations ]
# This section tells the game engine which map objects to animate.
# The names are not used and only for your benefit, and they must be unique.
# The meaning of these values are explained below.

    [[ flashing blue terminal ]]
    gid = 41
    frames = 41, 42
    fps = 0.2
    loop = -1

    [[ idle green terminal ]]
    gid = 43
    frames = 43, 44
    fps = 0.3
    loop = -1

[ dialogue ]
# When the player interacts with computer terminals (or any object with a certain
# action associated with it), you can have dialogue appear to the player.
# Keep in mind that all dialogue defined here is available across all levels in
# your story. So to make things easier we name them accordingly.

    [[ act 1 access mainframe ]]
    # I chose "act 1" for my first level dialogues, followed by a memorable action
    # name (this same name will get assigned to a map object action).
    # You may name it whatever you please.

        [[[ screen 1 ]]]
        # Dialogues can have multiple screens too, shown one after the other
        # as the user keys through them. Each screen can have a different
        # font color. The type sets which image and effects are used in this
        # screen. At the moment we only have 'story' and 'terminal', and they
        # both look the same. the datas is the words you want to appear, tripple
        # quoted so that they can span multiple lines.
        type = story
        color = text
        datas = """
                You mix the cookie batter, some of it spill on the floor.
                """

        [[[ screen 2 ]]]
        type = story
        color = text
        datas = """
                You reach for a towel, but it is missing!
                """

        [[[ screen 3 ]]]
        type = story
        color = player
        datas = """
                Who stole my towel?!
                """
````

# character stats explained

You may have many level objects that share the same name, and hence share these same stats. Any missing values will sanely default to idle, non hostile behaviour.

* attack
    * damage dealt to and opponent's health during a combat turn
* health
    * starting health of a character
    * if this drops to zero the character dies
* maxhealth
    * maximum health this character can heal up to
* healrate
    * heal 1 point of health every x turns
* speed
    * move this character every x turns (computer characters only)
* stealth
    * unused
* mana
    * starting mana of a character
* maxmana
    * maximum mana this character can heal up to
* manarate
    * heal 1 point of mana every x turns
* modes
    * a list of computer controlled movement behaviours
        * random: moves in random directions.
        * magnet: moves towards the player while in sight.
        * updown: patrols up and down, turning around when blocked.
        * leftright: patrols left and right, turning around when blocked.
        * sniffer: follows the player's scent if on the trail.

As a courtesy, you may overwrite any of these story-level stats on the map itself by adding it as a Name/Value object property on the map object. Try to keep combat related stats within the story definition, as this will make balancing your levels easier later on.

# animations explained

````
    [[ descriptive name only ]]
    gid = 42
    frames = 42, 43, 44, 43
    fps = 0.3
    loop = -1
````

These consist of a sequence of gid's and a few other values that determine how animations are displayed. Only object layers can animate, not tile layers.

All map objects with the `gid` value 42 will match animate rule above.

`frames` define which tiles is apart of the animation. Usually `frames` start with the same value given in `gid` although it does not have to. In this example we use the same tile twice (43) to create a ping-pong loop animation.

`fps` set how many frames to show per second. An animation with 3 frames, running at 3 fps, will take 1 second to complete.

`loop` indicates how many times to loop the animation. -1 will loop forever, 0 will run the animation once and stop, and any other postive value will loop that many times.

_Note: When using object triggers to `transmorgify` one object into another, the new object will inherit and play it's new animations immediately._

# Building maps

Maps are built with the Tiled map editor. You can get it from the official website: [http://www.mapeditor.org](http://www.mapeditor.org).

**Important:** _Set your Tiled Preferences to "store layer data" as `Base 64 (zlib compressed)`. This is the format we expect to read the map data._

# Tileset

Each map has a tileset, an image divided into 32x32 sized blocks of tile images. Each level can have it's own tileset image, or share the same image. This is a PNG file, it should not have a transparency layer, instead all magenta #ff00ff pixels are rendered transparent. The image size _must_ be in multiples of 32. This helps the rendering engine index the tiles properly.

# Creating a level

1. Run Tiled and create a new map: Orientation is Orthagonal. Make size 16x16 for now, and set tile size to 32x32.
1. From the Map menu, add a New Tileset. Choose the image in your story path. Enable the transparency color and set it to #ff00ff magenta. Set the tile size to 32x32.
1. Rename the default tile layer to "map", and add an object layer named "objects". The names are not required but help you know where to put what.
1. You are now ready to create your level :]
* Place walls and doodads "map" tile layer.
* Place interactable game objects on the "objects" Object Layer.

### Object Reference

You may apply these properties to level objects for more effect.

**types**

* player
    * sets the player object on a level. this is the one required object on any level.
* ai
* friend
* door
* terminal

**extended properties**
_these are added via the Name-Value property list._

* none as of yet


## Object Interactions

Give map objects these properties to interact with the game. The actions match the start of the action name, you can add descriptive words after the name (like 'Foo'), you can't have two actions with the same name.

You may append an action name with the word 'once' for a one-time trigger. This applies to both walk-in actions and fingered actions.

Actions take the form of ** < action > **: _< value >_.

The GID mentioned is the numbered index of the tileset image.

### Walk-in actions

_These trigger when bumping into an object._

* **message <foo once>**: _text_
    print a message for the player.

* **fingers <foo once>**: _target name_
    process triggers on the named object.
    objects with the same name will all get fingered.
    fingered targets won't finger others (recursion prevention)

* **dialogue <foo once>**: _dialogue key_
    show a game dialogue screen with the text defined with the key in story.py.

* **exit**
    exit for the next level.

### Fingered target actions

_These trigger objects being fingered._

* on finger <foo once>: action

    * **give**: _newpropertyname=newpropertyvalue_
        give this object a new property.
    * **transmute**: _gid <,gid..n>_
        change this object tile to another.
        this affects it blocking characters and similar tests.
        a comma list of GID's will rotate between each trigger (opening or closing doors).

* **dialogue** _<foo once>_: dialogue key
    show a dialog screen by key, as defined in the game story definition.

### Examples

Change a locked door tile to a non blockable open door tile.

1. "switch actions":
    * **fingers**: _locked door_
    * **message**: _A secret door opens_
1. "locked door actions"
    * **on finger**: _transmute=2_

Unlock a terminal with another, the former will then show a storyline when accessed.

1. "terminal 1 actions":
    * **fingers**: _locked terminal_
    * **message**: _The other terminal unlocks_
1. "locked terminal actions":
    * **on finger**: _give=dialogue=foo storyline_

