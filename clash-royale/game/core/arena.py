import pygame
from game.settings import *

# Arena Colors
GRASS_LIGHT = (100, 200, 100)
GRASS_DARK = (80, 180, 80)
BORDER_COLOR = (100, 80, 60) # Wood/Earth tone
RIVER_COLOR = (50, 150, 255)
BRIDGE_COLOR = (160, 120, 80)

class Arena:
    def __init__(self, manager):
        self.manager = manager
        self.screen = manager.screen
        self.playable_height = manager.playable_height
        
        # Grid dimensions
        self.grid_width = GRID_WIDTH
        self.grid_height = GRID_HEIGHT
        self.tile_size = TILE_SIZE
        self.margin_x = GRID_MARGIN_X
        self.margin_y = GRID_MARGIN_Y
        
        # Calculate Geometry
        self.calculate_geometry()
        
        # Pre-render background
        self.background = self._generate_background()
        
    def calculate_geometry(self):
        """
        Calculates the rectangles for the river and bridges.
        """
        # River
        # River is typically in the middle. 
        # Let's assume it spans 2 tiles height-wise in the center.
        river_row_start = (self.grid_height // 2) - 1
        river_y = self.margin_y + river_row_start * self.tile_size
        river_height = 2 * self.tile_size
        
        self.river_rect = pygame.Rect(self.margin_x, river_y, self.grid_width * self.tile_size, river_height)
        
        # Bridges
        # Left and Right bridges.
        # Width: 3 blocks (TILE_SIZE)
        # Position: Centered on LANE_LEFT_COL and LANE_RIGHT_COL
        
        bridge_width = 3 * self.tile_size
        bridge_height = river_height + 10 # Slightly longer than river
        
        # Left Bridge
        # Center X of the lane column
        left_lane_x = self.margin_x + LANE_LEFT_COL * self.tile_size + self.tile_size // 2
        self.left_bridge_rect = pygame.Rect(left_lane_x - bridge_width//2, river_y - 5, bridge_width, bridge_height)
        
        # Right Bridge
        right_lane_x = self.margin_x + LANE_RIGHT_COL * self.tile_size + self.tile_size // 2
        self.right_bridge_rect = pygame.Rect(right_lane_x - bridge_width//2, river_y - 5, bridge_width, bridge_height)

    def _generate_background(self):
        """
        Generates the static background surface with grid, river, and bridges.
        """
        # Create surface for the full playable area
        surface = pygame.Surface((SCREEN_WIDTH, self.playable_height))
        surface.fill(DARK_GREY) # Background for margins
        
        # Draw Grid (Checkered Grass)
        # 1. Draw base layer (Light Grass) for the entire grid area
        # This ensures no gaps between light tiles
        grid_rect = pygame.Rect(self.margin_x, self.margin_y, self.grid_width * self.tile_size, self.grid_height * self.tile_size)
        pygame.draw.rect(surface, GRASS_LIGHT, grid_rect)
        
        # 2. Draw Dark Grass tiles on top
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                # Only draw dark tiles
                if (row + col) % 2 != 0:
                    x = self.margin_x + col * self.tile_size
                    y = self.margin_y + row * self.tile_size
                    pygame.draw.rect(surface, GRASS_DARK, (x, y, self.tile_size, self.tile_size))
        
        # Optional: Draw faint grid lines if needed, but user asked to remove "black grid".
        # If they meant the checkerboard itself, a solid color is safest.
        # Or maybe they want faint lines? "remove the black grid".
        # The previous implementation had alternating colors which created a "grid" look.
        # Let's stick to a solid pleasant green.
                
        # Draw River
        pygame.draw.rect(surface, RIVER_COLOR, self.river_rect)
        
        # Draw Bridges
        # Left Bridge
        pygame.draw.rect(surface, BRIDGE_COLOR, self.left_bridge_rect)
        # Wood planks details
        for i in range(5):
            y = self.left_bridge_rect.y + i * (self.left_bridge_rect.height // 5)
            pygame.draw.line(surface, (100, 70, 40), (self.left_bridge_rect.left, y), (self.left_bridge_rect.right, y), 2)

        # Right Bridge
        pygame.draw.rect(surface, BRIDGE_COLOR, self.right_bridge_rect)
        # Wood planks details
        for i in range(5):
            y = self.right_bridge_rect.y + i * (self.right_bridge_rect.height // 5)
            pygame.draw.line(surface, (100, 70, 40), (self.right_bridge_rect.left, y), (self.right_bridge_rect.right, y), 2)

        # Draw Border
        border_rect = pygame.Rect(self.margin_x - 5, self.margin_y - 5, (self.grid_width * self.tile_size) + 10, (self.grid_height * self.tile_size) + 10)
        pygame.draw.rect(surface, BORDER_COLOR, border_rect, 5)
        
        return surface

    def draw(self, surface):
        """
        Draw the arena background to the target surface.
        """
        surface.blit(self.background, (0, 0))

    def get_valid_spawn_rects(self):
        """
        Returns a list of pygame.Rects where units can be spawned.
        """
        rects = []
        
        # Base Area: Player side (below the river)
        # Start from the bottom of the river to prevent spawning in the river
        spawn_y = self.river_rect.bottom
        
        grid_pixel_width = self.grid_width * self.tile_size
        # Limit spawn area to grid bottom
        grid_bottom = self.margin_y + self.grid_height * self.tile_size
        
        rects.append(pygame.Rect(self.margin_x, spawn_y, grid_pixel_width, grid_bottom - spawn_y))
        
        # Pocket Logic
        # If a princess tower is down, we can spawn in that lane up to the King Tower
        pocket_top_tile = 8
        pocket_top_y = self.margin_y + pocket_top_tile * self.tile_size
        # Pocket extends down to the top of the river
        river_y = self.river_rect.y
        pocket_height = river_y - pocket_top_y
        pocket_width = grid_pixel_width // 2
        
        # Access towers via manager
        if not self.manager.left_tower_e.alive():
            # Left pocket
            rects.append(pygame.Rect(self.margin_x, pocket_top_y, pocket_width, pocket_height))
            
        if not self.manager.right_tower_e.alive():
            # Right pocket
            rects.append(pygame.Rect(self.margin_x + pocket_width, pocket_top_y, pocket_width, pocket_height))
            
        return rects
