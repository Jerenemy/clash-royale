import pygame
import sys
from game.settings import *
from game.core.scene import SceneManager

class GameEngine:
    """
    Core engine that manages the game loop, window, and scenes.
    """
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.virtual_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Clash Royale Clone")
        
        # Load assets after display is initialized
        from game.assets import assets
        assets.load_game_assets()
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Scaling variables
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.scene_manager = SceneManager(self)

    def get_mouse_pos(self):
        """Get mouse position transformed to virtual surface coordinates."""
        mx, my = pygame.mouse.get_pos()
        return int((mx - self.offset_x) / self.scale), int((my - self.offset_y) / self.scale)

    def run(self):
        """Main game loop."""
        FIXED_DT = 1.0 / 60.0
        accumulator = 0.0
        
        while self.running:
            # Get frame time
            frame_time = self.clock.tick(FPS) / 1000.0
            if frame_time > 0.25: frame_time = 0.25 # Cap frame time to avoid spiral of death
            
            accumulator += frame_time
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                else:
                    self.scene_manager.handle_event(event)
            
            # Fixed time step update
            while accumulator >= FIXED_DT:
                self.scene_manager.update(FIXED_DT)
                accumulator -= FIXED_DT
            
            # Draw (interpolated? for now just draw)
            self.virtual_surface.fill(BLACK)
            self.scene_manager.draw(self.virtual_surface)
            
            # Scale and draw to window
            scaled_w = int(SCREEN_WIDTH * self.scale)
            scaled_h = int(SCREEN_HEIGHT * self.scale)
            
            if scaled_w > 0 and scaled_h > 0:
                scaled_surface = pygame.transform.scale(self.virtual_surface, (scaled_w, scaled_h))
                self.window.fill(BLACK) # Clear borders
                self.window.blit(scaled_surface, (self.offset_x, self.offset_y))
            
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_resize(self, w, h):
        """Handle window resize."""
        self.scale = min(w / SCREEN_WIDTH, h / SCREEN_HEIGHT)
        self.offset_x = (w - SCREEN_WIDTH * self.scale) // 2
        self.offset_y = (h - SCREEN_HEIGHT * self.scale) // 2

    def quit(self):
        """Quit the game."""
        self.running = False
