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
    evManager.RegisterListener(gamemodel)
    evManager.RegisterListener(kbmousey)
    evManager.RegisterListener(graphics)
    gamemodel.run()

if __name__ == '__main__':
    run()
