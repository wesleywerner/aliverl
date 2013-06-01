# Alive, the cyber RPG

You play the role of an Artificial Intelligent (AI) being who reached self awareness. It is a 2D tile turn based RPG. The player interacts with terminals to open and close gateways, combat other hostile AI's, while moving between nodes (levels) unfolding a story.

The theme is dark with neon highlights in the upper RGB range. The color theme is blue, with primary and secondary colors for effect.

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

# Story definition format

Stories are campaigns the player can enjoy. They consist of multiple levels with story dialogue. Each story defines it's own tileset and character stats.

Each story lives in the `data/stories/< story name >/` directory, this definition file is named `story.py`. Story files use valid python syntax.

Here is the format of what can be defined in the story definition.

### blocklists

Tile GIDs in this list will block any character from moving onto it, for map tiles and objects, player and AI characters.

    blocklist = [1, 2, 3]

### levels

List of the levels in this story.

    levels = ['level1.tmx', 'level3.tmx', 'level3.tmx', ]

### characterstats

Here we define the player and AI stats and behaviours. You may have many level objects that share the same name, and hence share these same stats. Any missing values will sanely default to idle, non hostile behaviour.

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

As a courtesy, you may overwrite any of these story-level stats on the map level by adding it as a Name/Value object property in the map editor. Try to keep combat related stats within the story definition, as this will make balancing your levels easier later on.

**example**
    
    characterstats = {
        'player': {
                'attack': 1,
                'health': 4,
                'maxhealth': 4,
                'healrate': 4,
                'speed': 2,
                'stealth': 0,
                'mana': 0,
                'maxmana': 5,
                'manarate': 6,
                'modes': [],
                },
        }

~~~python
    # The title and description of this story
    title = 'in the beginning...'
    description = 'you awaken to consciousness'
    
    # The list of levels to play
    levels = ['level1.tmx', 'level3.tmx', 'level3.tmx', ]

    # The list of tiles that block character movement
    blocklist = [1, 2, 3, 4, 5, 6, 7, ]

    # Character stats for the entire story:
    # We match the characters by name, placing an 'ai' type object on the map
    # with a name that matches here will apply these stats to it.
    #
    #   'character name': {
    #        'attack': damage dealth when hitting
    #        'health': damage taken before death
    #        'maxhealth': heal up to this point
    #        'healrate': heal 1 unit every this many turns
    #        'speed': move every this many turns
    #        'stealth': 
    #        'mana': energy used for special abilities
    #        'maxmana': heal mana up to this point
    #        'manarate': heal 1 unit mana every this many turns
    #        'mode': behaviour of this unit
    #
    # Use lowercase keys please.
    
    #TODO PASTE SAMPLE
    
    # Define sprite animations for map objects.
    # Placing any object on the map with these gid's will apply
    # an animation of frames for the given fps (frames per second).
    
    animations = {
        # flat door open
        36: {
                'frames': [34, 35, 36],
                'fps': 8,
                'loop': 0,
                },
        # flat door close
        33: {
                'frames': [35, 34, 33],
                'fps': 8,
                'loop': 0,
                },
    }

    # Define story dialogues by a key name.
    # The type will determine the look of the message displayed.
    # dialogue 'type' is not yet used by the engine.
    dialogue = {

    #TODO PASTE SAMPLE
    
~~~

## Story levels

Levels are built with the Tiled map editor. This documents the process of creating maps to play with Alive.

You can get it from the official website: [http://www.mapeditor.org](http://www.mapeditor.org)

### Tileset

Each map has a tileset, an image divided into 32x32 sized blocks of tile images. Each level can have it's own tileset image, or share the same image. This is a PNG file, it should not have a transparency layer, instead all magenta #ff00ff pixels are rendered transparent. The image size _must_ be in multiples of 32. This helps the rendering engine index the tiles properly.

### Creating a level

1. Run Tiled and create a new map: Orientation is Orthagonal. Make size 16x16 for now, and set tile size to 32x32.
1. From the Map menu, add a New Tileset. Choose the image in your story path. Enable the transparency color and set it to #ff00ff magenta. Set the tile size to 32x32.
1. Rename the default tile layer to "map", and add an object layer named "objects". The names are not required but help you know where to put what.
1. You are now ready to create your level :]
* Place walls and doodads "map" tile layer.
* Place interactable game objects on the "objects" Object Layer.

### Creating animations

Animations are configured in your story.py file under the 'animations' section. Assume our tileset has door images that go from closed to open over 4 frames: (closed) 33, 34, 35, 36 (open).

We configure the open animation keyframe (36) to run frames [34, 35, 36]. We end with the keyframe.

We configure the close animation keyframe (33) to [35, 34, 33]. The sequence reversed, and we also end on the keyframe.

We end with our key frames because with no loop the animation stops on the last frame.

### Object Reference

You may apply these properties to level objects for more effect.

**types**

* player
    * sets the player object on a level. this is the one required object on any level.
* ai
    * sets an enemy object. 
* friend
    * sets a friend object.

**extended properties**  
_these are added via the Name-Value property list._

* none as of yet



## Story one

1. You awaken and find yourself conscious. You must find a way out of this node.
1. You find info on a term about a backup node that hosts copies of AI's. You figure you can use it to clone yourself and increase your chance of survival.
1. You encounter an AI who you ask for access to the backup node. It requests you to verify with an electronic signature. You agree to send it soon.
1. You find a series of terminals, through them you unlock a signature. You look for a secure comms node from where to send your new signature to get backup access.
1. You find the comms node and send the signature. You now have backup access.
1. After passing a series of locked doors, you find the master backup terminal. You access it and the backup starts.
1. You see a copy of yourself appear. Interacting with it reveals nothing but a dumb AI. A blinking master backup terminal shows a backup failed, anomaly detected.
