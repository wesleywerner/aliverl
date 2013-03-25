import eventmanager
import aliveModel
import aliveView
import aliveController

def run():
    evManager = eventmanager.EventManager()
    gamemodel = aliveModel.GameEngine(evManager)
    kbmousey = aliveController.KeyboardMouse(evManager, gamemodel)
    graphics = aliveView.GraphicalView(evManager, gamemodel)
    evManager.RegisterListener(gamemodel)
    evManager.RegisterListener(kbmousey)
    evManager.RegisterListener(graphics)
    gamemodel.run()

if __name__ == '__main__':
    run()
