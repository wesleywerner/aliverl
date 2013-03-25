import eventmanager
import aliveModel
import aliveView
import aliveController

def run():
    evManager = eventmanager.EventManager()
    engine = aliveModel.GameEngine(evManager)
    kbmousey = aliveController.KeyboardMouse(evManager)
    graphics = aliveView.GraphicalView(evManager)
    evManager.RegisterListener(engine)
    evManager.RegisterListener(kbmousey)
    evManager.RegisterListener(graphics)
    engine.run()

if __name__ == '__main__':
    run()
