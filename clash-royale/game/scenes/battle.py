import pygame
from game.core.scene import Scene
from game.core.managers import BattleManager
from game.settings import *

class BattleScene(Scene):
    def __init__(self, engine, battle_manager=None, network_controller=None):
        super().__init__(engine)
        self.network_controller = network_controller
        
        if battle_manager:
            self.game = battle_manager
        else:
            self.game = BattleManager(engine, practice_mode=True)

    def enter(self, params=None):
        # Reset game if starting fresh practice match (no controller)
        if not self.network_controller:
            self.game.reset_game()

    def handle_event(self, event):
        result = self.game.handle_event(event)
        if result == "menu":
            self.manager.pop()

    def update(self, dt):
        self.game.update(dt)
        if self.network_controller:
            self.network_controller.update(dt)

    def draw(self, screen):
        self.game.draw()
