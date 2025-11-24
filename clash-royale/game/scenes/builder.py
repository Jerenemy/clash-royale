import pygame
from game.core.scene import Scene
from game.core.deck_builder import DeckBuilder
from game.utils import load_deck

class DeckBuilderScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.deck_builder = DeckBuilder(engine)

    def enter(self, params=None):
        self.deck_builder.deck = load_deck()

    def handle_event(self, event):
        result = self.deck_builder.handle_event(event)
        if result == "menu":
            self.manager.pop()

    def draw(self, screen):
        self.deck_builder.draw()

    def update(self, dt):
        self.deck_builder.update(dt)
