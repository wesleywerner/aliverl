#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see http://www.gnu.org/licenses/.

import os
import eventmanager
import aliveModel
import aliveView
import aliveController


def run():
    # switch to this path to point relative paths to resources
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    evManager = eventmanager.EventManager()
    gamemodel = aliveModel.GameEngine(evManager)
    graphics = aliveView.GraphicalView(evManager, gamemodel)
    kbmousey = aliveController.KeyboardMouse(evManager, gamemodel, graphics)
    gamemodel.run()

if __name__ == '__main__':
    run()
