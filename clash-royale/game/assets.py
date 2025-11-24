import pygame
import os
from game.settings import *

class AssetManager:
    def __init__(self):
        self.sounds = {}
        self.images = {}
        self.font_cache = {}
        
        # Initialize mixer if not already
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Warning: Audio could not be initialized: {e}")

    def load_sound(self, name, path):
        if name in self.sounds:
            return self.sounds[name]
            
        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                self.sounds[name] = sound
                return sound
            else:
                print(f"Warning: Sound file not found: {path}")
                return None
        except Exception as e:
            print(f"Error loading sound {name}: {e}")
            return None

    def load_image(self, name, path, size=None):
        if name in self.images:
            return self.images[name]
            
        try:
            if os.path.exists(path):
                image = pygame.image.load(path).convert_alpha()
                if size:
                    image = pygame.transform.smoothscale(image, size)
                self.images[name] = image
                return image
            else:
                print(f"Warning: Image file not found: {path}")
                return None
        except Exception as e:
            print(f"Error loading image {name}: {e}")
            return None

    def play_sound(self, name):
        if name in self.sounds and self.sounds[name]:
            try:
                self.sounds[name].play()
            except Exception:
                pass
        else:
            # Placeholder: Print to console if sound missing (debugging)
            # print(f"[Audio] Playing sound: {name}")
            pass

    def get_font(self, name, size):
        key = (name, size)
        if key in self.font_cache:
            return self.font_cache[key]
        
        font = pygame.font.SysFont(name, size)
        self.font_cache[key] = font
    def get_image(self, name):
        return self.images.get(name)

    def load_game_assets(self):
        # Load UI/Background assets
        self.load_image("arena_map", os.path.join("assets", "arena_map.png"), (SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT))
        self.load_image("loading_screen", os.path.join("assets", "loading_screen.png"), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.load_image("menu_background", os.path.join("assets", "menu_background.png"), (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Load other assets as needed
        self.load_image("card_frame", os.path.join("assets", "card_frame.png"))
        self.load_image("elixir_drop", os.path.join("assets", "elixir_drop.png"))

# Global instance
assets = AssetManager()
