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
* max_health
    * maximum health this character can heal up to
* heal_rate
    * health to restore each turn
* speed
    * move this character every x turns (computer characters only)
* stealth
    * unused
* power
    * starting power of a character
* max_power
    * maximum power this character can heal up to
* power_restore_rate
    * power to restore each turn
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

The tileset is an image divided into 32x32 sized squares of tiled images. This is a PNG file, it should not have a transparency layer, instead all magenta #ff00ff pixels are rendered transparent. This means that you must avoid using per-pixel alpha effects. The image size must be in multiples of 32 as this helps the rendering engine determine how many columns and rows comprise the tileset.

Once you start building levels with a given tileset image, you should not add any more columns to the tileset image. This will offset the indexes and break your levels. You are free to add as many rows as you need, that is okay.

To help build your story with the proper image and animation id's, use the built-in debug command ^F2 to render two temporary png images: Use the first file, `alive_tileset_indexed.png`, to build your conf animations sections.

Once your animation config is set up, re-run ^F2 so that the second image, `alive_animations.png`, is refreshed to reflect your newly configured animations. This particular cheat sheet will help you as a reference when building levels with the map editor.

# Creating a level

1. Run Tiled and create a new map: Orientation is Orthagonal. Make size 16x16 for now, and set tile size to 32x32.
1. From the Map menu, add a New Tileset. Choose the image in your story path. Enable the transparency color and set it to #ff00ff magenta. Set the tile size to 32x32.
1. Rename the default tile layer to "map", and add an object layer named "objects". The names are not required but help you know where to put what.
1. You are now ready to create your level :]
* Place walls and doodads "map" tile layer.
* Place interactable game objects on the "objects" Object Layer.

## Object Reference

You may apply these properties to level objects for more effect.

**types**

* player
    * sets the player object on a level. this is the one required object on any level.
* ai
    * these objects you enter combat with. they also get movement turns as defined in the story file, or on the map level.
* friend
    * also get movement turns, but you don't enter into combat with these.
* door
    * nothing special here. use it anyway as future functionality will benefit from this.
* terminal
    * nothing special here. use it anyway as future functionality will benefit from this.

**extended properties**
_these are added via the Name-Value property list._

* none as of yet

## Object Interactions

Map objects can be interacted with in two ways: directly when the player walks into the object, or indirectly via a trigger. You define these interactions as custom properties for the map object in the map editor. The property name is descriptive only, and you can label it whatever suits you. The Value part is where the interaction command is defined.

All commands begin with the @-symbol, and remainder text is put into a $user variable. The structure for a command is:

    [@when] @command [@option] [$user]

Optional commands are indicated by [].

@when can be **any** of:

    @ontrigger
        occurs when object is triggered indirectly, that is a player touching this object won't activate this trigger, but another object with a properly configured command will.

    @delay=n
        occurs after n turns.

    @ifcounter=n
        this command will only trigger if the object's internal counter reaches n.

@command can be **one** of:

    @message
        display a game message stored in $user.

    @exit
        warp to the next level.

    @trigger
        trigger all objects that match $user

    @dialogue
        display a story dialogue where the dialogue key matches $user.

    @give
        give the containing object a new property equals $user.
        note: prefix commands in $user with % instead of @.

    @transmute
        change this object tile to another by GID stored in $user.
        this can be a single number one-way transmute, or a
        comma separated list of GID's to rotate between each trigger
        (assuming @repeat is specified).

    @addcounter
        add 1 to the object's internal counter.

    @clearcounter
        resets the object's internal counter to 0.

    @setattr
        alter the attributes of any objects within the containing rectangle.

@option can **any** of:

    @repeat
        repeat this interaction next time. by default commands only action once.

### Interaction Examples

A non-blocking transparent tile shows a game message as the player walks over it:

    @message @once You step through the portal

A blocking terminal tile opens a door object named "locked door":

    @trigger locked door

A blocking door tile changes to a non-blocking open door tile (GID 5) when triggered:

    @ontrigger @transmute 5

A wall switch repeatedly triggers a door on every interaction:

    @trigger @repeat locked door

And the door will repeatedly open and close itself by rotating between those two tiles:

    @ontrigger @repeat @transmute 5, 4

A more complex example: A computer shows story dialogue and unlocks a door, after which interacting with it only shows a message that the computer has locked.

    @dialogue player reads email
    @trigger locked door
    @give %message %repeat this computer is now locked

It is worth noting that the order of interactions is arbitrary, from the player perspective all actions happen at the same turn.

Also noteworthy is that interactions triggered indirectly via @ontrigger ignore calling @trigger commands themselves. This is to prevent infinite recursion. For more on this, see Recursion.

### addcounter and clearcounter example

Object counters allow you to trigger commands after an arbitrary amount of times, in any order. Consider an object with these properties:

    @repeat @addcounter
    @repeat @ifcounter=5 @message muffins for everyone!

On every interaction with this object it adds to the counter. When it reaches 5 it will announce free muffins. A more complex and realistic example can simulate needing to toggle 5 switches scattered on a map, in any order, before a computer terminal can be accessed. This is done by letting each of the switches @trigger the terminal, who then @addcounter @ontrigger. The actual command to use the terminal does a @ifcounter=n test. Naturally since counters are useless without repetition, all of the counting object's commands need the @repeat option to be of any use.

switches 1 to 5:

    @trigger that_terminal

the terminal:

    @repeat @ontrigger @addcounter
    @repeat @ifcounter=5 @clearcounter @dialogue win the cookie

The @clearcounter is used to ensure that particular command only gets actioned once, if that is your intent. You can very well omit it, in which case that trigger will get hit repeatedly on every interact if the counter is the correct value. You can also replace the clear with a @addcounter to keep on counting.

### setattr example

Usually applied to a rectangle object that has a width and height, any objects within its region, and match set filters, have their attributes altered as per the user data. The format for this command is:

    @setattr [type_filter=ai|friend|term|switch|door] [name_filter="object name"] attribute=value

A real example to make any objects called "the doctor" within the region fast and follow you:

    @setattr name_filter="the doctor" speed=1 modes=magnet

A real example to change all friend AI within the region, hostile:

    @setattr type_filter=friend type=ai

Filter objects match by type_filter (strict), or by name_filter (fuzzy). The filters are exclusive so only specify one or the other.

The rest of the command will set object attributes to the key=value pairs. More on what these attributes are in the "character stats explained" section.

Any values that contain spaces are to be quoted.

Be careful of side effects, like changing an object's type could make it fail any following @setattr commands that may rely on an object's type.

# FAQ

## The AI in my map do not move around. Are they broken?

A: For AI to take move turns they need a few things: A "type" of either "ai" or "friend", a "modes" of movement, and "speed".

These can be set either on the map level by giving these as object properties with corresponding values, or by giving it a name that matches a character definition in your story.conf.

## Why does my upgrade ability not act upon any AI?

    Your upgrade config needs the use_targeting value set True. If you have max_targets set to more than 1 then you also need to set the reach value.

## Why do doors not open or close when I trigger them from a switch?

    Make sure you give them the @ontrigger and @transmute commands. Their names must also match exactly to what the switch is triggering.

## Why do my doors open or close only once?

    Give them the @repeat command, and to the switch that trigger them too.

## Why do some of my @setattr commands work but not others?

    If you are altering an object's type then subsequent filters will not detect that object anymore, if these rely on a type_filter match. Try match on the name in these cases.