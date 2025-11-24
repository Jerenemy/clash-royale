import pygame
from game.core.scene import Scene
from game.settings import *
from game.scenes.battle import BattleScene
from game.scenes.builder import DeckBuilderScene
from game.scenes.matchmaking import MatchmakingScene
from game.ui.core import UIManager, Button, Label
from game.assets import assets

try:
    from game.network.client import NetworkClient
except ImportError:
    NetworkClient = None

class MainMenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.ui_manager = UIManager(engine)
        
        # Title
        self.ui_manager.add(Label(SCREEN_WIDTH//2, 100, "Clash Royale Clone", font_size=48, color=WHITE, center=True))
        
        # Buttons
        btn_w = 200
        btn_h = 50
        cx = SCREEN_WIDTH // 2 - btn_w // 2
        cy = SCREEN_HEIGHT // 2
        
        self.ui_manager.add(Button(cx, cy - 80, btn_w, btn_h, "Multiplayer", 
                           on_click=self.on_multiplayer, color=BLUE))
                           
        self.ui_manager.add(Button(cx, cy - 10, btn_w, btn_h, "Practice", 
                           on_click=self.on_practice, color=GREEN))
                           
        self.ui_manager.add(Button(cx, cy + 60, btn_w, btn_h, "Deck Builder", 
                           on_click=self.on_deck_builder, color=ORANGE))
                           
        self.ui_manager.add(Button(cx, cy + 130, btn_w, btn_h, "Quit", 
                           on_click=self.on_quit, color=RED))

    def on_multiplayer(self):
        if NetworkClient:
            self.manager.push(MatchmakingScene(self.engine))
        else:
            print("Multiplayer not available")

    def on_practice(self):
        self.manager.push(BattleScene(self.engine))

    def on_deck_builder(self):
        self.manager.push(DeckBuilderScene(self.engine))

    def on_quit(self):
        self.engine.quit()

    def handle_event(self, event):
        self.ui_manager.handle_event(event)

    def update(self, dt):
        self.ui_manager.update(dt)

    def draw(self, screen):
        # Draw background
        screen.blit(assets.get_image("menu_background"), (0, 0))
        
        # Draw UI
        self.ui_manager.draw(screen)
