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
* _ui.py_
* _helper.py_
* _audio.py_

**CONTROLLER**: aliveController.py

* input.py

**OTHER**:

* alive.py
    * binds the objects together
* eventmanager.py
    * pygame provides an event manager but we implement our own so it is not coupled to pygame.
* trace.py
* color.py

