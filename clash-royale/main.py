import sys
# Add current directory to path so we can import game package
sys.path.append(".")

from game.core.engine import GameEngine
from game.scenes.menu import MainMenuScene

def main():
    engine = GameEngine()
    engine.scene_manager.push(MainMenuScene(engine))
    engine.run()

if __name__ == "__main__":
    main()
