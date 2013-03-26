# Table of contents

[TOC]

# The purpose of this document

Implement the MVC design pattern for a 2D graphical RPG Roguelike game.
By decoupling the view, controller and model and using an event manager to
communicate between them, we make the code more maintainable and allow us to
implement other neat controllers like:

* a View for graphic on mobile devices.
* a Controller for touch-screens.

_For more on MVC patters see References below_

## Versions

This document is a work in progress and incomplete.

1. 2013/03: drafting

# The coupling

Here we see how our our model pieces are connected:

                 +------------+
                 |    Model   |
      >---->---->+------------+<----<----<
      |          .            .          |
      ^          .            .          ^
      |          +------------+          |
      ^          |   Events   |          ^
      |          +------------+          |
      ^          .            .          ^
      |          .            .          |
      ^          .            .          ^
      +------------+        +------------+
      |    View    |        | Controller |
      +------------+        +------------+

* Model
    * job: stores game map, player and npc data, game settings. Everything data.
    * is not aware of what Views or Controllers are looking at it.
    * can post and listen for events.
* View
    * job: draws on screen what the model represents.
    * is strongly aware of the model and it's values.
    * can post and listen for events.
* Controller
    * job: taking keyboard and mouse input and posts matching events.
    * is strongly aware of the model and it's values.
    * can post and listen for events.
* Events
    * job: coordinates messages between listeners.

This shows that even if the Controller does not know anything about the player's
health, what level we are on, it still only catches key presses and sends out
events to match.

Nor does the View care how the player is controlling our game. 
The View only cares about showing on screen the current model state.
Since the View also listens to posted events, it will pick up mouse clicks and
key presses that integrate into it's widgets.

# Game states

The model is host to multiple game states, like:

* playing
    * The game is in play.
    * Controls react to the playtime context.
* dialogue
    * The screen shows game storyline.
    * The game is not running.
    * Controls only respond to the dialog context.
* menus
    * The user can select a profile to play or continue play.
    * The user can select to view the settings or other pages.
    * The game is not running. 
    * Controls only respond to the menu context.
* settings
    * The user can toggle audio or music.
    * The game is not running.
    * Controls only respond to the settings context.
* intro
    * Shows opening screen.
* help
    * Display a game help overlay.

Since our View and Controller has strong links to the Model, both can look at
the Model state, and decide what user keys to process, and what to draw.

That is their domain, and their job.

## State implementation

Using a state machine to track these game states allows us interesting tricks otherwise difficult to do.

### What is a state machine?

It is a fancy name for "a list of values, Last one In is First one Out." LIFO.

Think of it like a stack of dinner plates.

              ===     <- we have a green plate on the table
            #######   <- our wooden breakfast table

You can peek() at what the topmost plate is, we see it is green, so we draw and react to events that mean "our game is busy playing". 

When we push() a red plate on top of the stack, we draw and do things that mean "the game is now paused". 

              ===     <- we now see a red plate on top of the stack
              ===     ... green plate
            #######   ... table

To unpause, we simply pop() the top most plate off the stack, and we can now see the green plate again. Our game carries on playing.

### Why would we do this?

Because this allows us to easily unwind the stack to escape from game menus, options, dialogue screens and so forth.

All our View needs to do, is draw whatever the current stack item says.
All our Controller needs to do, is handle input for the current stack item.

We can use this to show game dialogue for more than one screen. Consider this:

              ===     ... dialogue text #1
              ===     ... dialogue text #2
              ===     ... dialogue text #3
              ===     ... green plate
            #######   ... table

The View draws the dialogue text #1, and when the user presses the "anykey" we pop the stack and suddenly the View draws text #2. Neat. 

The Controller knows it's a dialogue mode and knows to pop the stack on the "anykey" press. 

Press enough keys, pop enough plates, we move through the storyline and get back to the game.

# Restructuring

Existing code files will be restructured.
(_slanted files await refactoring_)

**MODEL**: aliveModel.py

* _game.py_
* _character.py_
* _objects.py_
* states.py
* _stats.py_
* _combat.py_
* _bump.py_
* _level.py_
* _messages.py_

**VIEW**: aliveView.py

* resources.py
* _trace.py_
* _ui.py_
* _color.py_
* _helper.py_
* _audio.py_

**CONTROLLER**: aliveController.py

* _input.py_

**OTHER**:

* alive.py
    * binds the mvc objects together
* eventmanager.py
    * pygame provides an event manager but we implement our own so it is not coupled to pygame.

# License

    Copyright (C) 2013 Wesley Werner

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.
If not, see [http://www.gnu.org/licenses/](http://www.gnu.org/licenses/).

# Contact
You may contact me at [wez@[anti-spam]darknet.co.za](mailto:wez@[anti-spam]darknet.co.za)

# References

* [http://ootips.org/mvc-pattern.html](http://ootips.org/mvc-pattern.html): A nice MVC paradigm. Here I replaced the weakly-typed references with our event manager.
* [http://ezide.com/games/writing-games.html](http://ezide.com/games/writing-games.html): touches on a basic implementation which this document started from. It expands the model to include networking support, which I have omitted.