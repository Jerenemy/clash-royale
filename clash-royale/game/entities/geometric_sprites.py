"""
Geometric Sprite System
Creates beautiful, smooth sprites using geometric shapes (SVG-style)
instead of bitmap images for better performance and scalability.
"""
import pygame
import math
from game.settings import *
from game.entities.figurine_builder import FigurineBuilder

class GeometricSprite:
    """Base class for rendering entities using geometric shapes"""
    
    def __init__(self, size):
        self.size = size
        self.surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
    def render(self, team="player", animation_phase=0, direction=0):
        """
        Render the sprite to a new surface.
        team: "player" or "enemy" for color variations
        animation_phase: 0-1 float for animation cycle
        direction: angle in degrees (0=Right, 90=Down, 180=Left, 270=Up) or string ("down", etc. for legacy)
        """
        # Create a fresh surface to ensure clean transparency
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Handle legacy string directions        # Normalize direction to angle (0-360)
        if isinstance(direction, str):
            direction_map = {
                "right": 0,
                "down": 90,
                "left": 180,
                "up": 270,
                "side": 0 # Default side to right
            }
            direction = direction_map.get(direction, 90)
            
        # Draw Shadow (2D) before 3D rendering
        # Shadow is always at the bottom center (ground level)
        # We draw it directly on the surface
        center = self.size // 2
        self.draw_shadow(surface, center, center, self.size // 2)

        # Check if subclass implements render_figurine (New 3D Builder)
        # This bypasses the old rotation logic because the builder handles orientation
        if hasattr(self, 'render_figurine'):
            # 1. Measure pass
            # Create builder with no surface to measure bounds
            # We use 0,0 as center for measurement to get relative bounds
            measure_builder = FigurineBuilder(None, 0, 0, self.size, facing_angle=direction)
            self.render_figurine(measure_builder, team, animation_phase)
            
            # Calculate required size
            # We want the ground point (0,0,0) to be at the center of the final image
            # So we need to accommodate the maximum extent in any direction from the center
            max_extent_x = max(abs(measure_builder.min_x), abs(measure_builder.max_x))
            max_extent_y = max(abs(measure_builder.min_y), abs(measure_builder.max_y))
            
            # Add some padding
            padding = 4
            req_width = int(max_extent_x * 2 + padding * 2)
            req_height = int(max_extent_y * 2 + padding * 2)
            
            # Ensure at least self.size (or maybe not? self.size was arbitrary)
            # Let's ensure it's at least self.size to avoid shrinking too much
            final_width = max(self.size, req_width)
            final_height = max(self.size, req_height)
            
            # Create surface
            surface = pygame.Surface((final_width, final_height), pygame.SRCALPHA)
            
            # New center
            center_x = final_width // 2
            center_y = final_height // 2
            
            # Draw Shadow (2D) before 3D rendering
            # Shadow is always at the bottom center (ground level) -> (0,0,0) -> center of image
            # Use self.size for shadow size reference, or maybe scale it?
            # Let's keep shadow size based on self.size (base size of unit)
            self.draw_shadow(surface, center_x, center_y, self.size // 2)
            
            # 2. Render pass
            builder = FigurineBuilder(surface, center_x, center_y, self.size, facing_angle=direction)
            self.render_figurine(builder, team, animation_phase)
            return surface

        # Render top-down view
        base_surface = self.render_top_down(team, animation_phase)
        if base_surface:
            # Rotate
            # Pygame rotation is counter-clockwise, so we negate the angle
            # Our 0 is Right, Pygame 0 is Right.
            # But we want 90 to be Down. Pygame 90 is Up (counter-clockwise).
            # So we need to rotate by -direction.
            rotated_surface = pygame.transform.rotate(base_surface, -direction)
            
            # Create depth layer (darkened silhouette)
            depth_surface = rotated_surface.copy()
            
            # Darken by filling with grey with MULT blend mode
            # This multiplies the RGB values by 0.5 (128/255)
            overlay = pygame.Surface(depth_surface.get_size(), pygame.SRCALPHA)
            overlay.fill((128, 128, 128, 255)) 
            depth_surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Calculate offsets
            # Center the rotated sprite
            rect = rotated_surface.get_rect(center=(self.size // 2, self.size // 2))
            
            # Draw depth (extrusion)
            # Extrude downwards (y + 4) to simulate 3D perspective
            surface.blit(depth_surface, (rect.x, rect.y + 4))
            
            # Draw top layer
            surface.blit(rotated_surface, rect)
            
        return surface

    def render_top_down(self, team, animation_phase):
        """
        Render the sprite from a top-down perspective facing RIGHT (0 degrees).
        Override this in subclasses.
        Returns a Surface.
        """
        # Default implementation returns None, falling back to empty surface
        # Or create a placeholder
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        # Draw a simple arrow pointing right
        center = self.size // 2
        pygame.draw.polygon(s, (255, 255, 255), [
            (center + 10, center),
            (center - 10, center - 10),
            (center - 10, center + 10)
        ])
        return s

# ... (skipping to Renderer)

    def get_sprite(self, sprite_type, team="player", animation_phase=0, direction="down"):
        """Get a rendered sprite surface"""
        # Quantize angle if it's a number
        if isinstance(direction, (int, float)):
            direction = round(direction / 5) * 5
            direction = direction % 360
            
        # Simple cache key (could be expanded)
        cache_key = f"{sprite_type}_{team}_{int(animation_phase * 10)}_{direction}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        if sprite_type in self.sprites:
            surface = self.sprites[sprite_type].render(team, animation_phase, direction)
            self.cache[cache_key] = surface.copy()
            
            # Limit cache size
            if len(self.cache) > 2000: # Increased cache size for 360 views
                self.cache.clear()
                
            return self.cache[cache_key]
        return None


    def draw_circle_gradient(self, surface, center, radius, color1, color2=None):
        """Draw a circle with gradient-like effect using concentric circles"""
        if color2 is None:
            color2 = tuple(max(0, c - 40) for c in color1)
            
        steps = 8
        for i in range(steps):
            t = i / steps
            r = radius * (1 - t * 0.3)
            color = tuple(int(c1 * (1-t) + c2 * t) for c1, c2 in zip(color1, color2))
            pygame.draw.circle(surface, color, center, int(r))

    def draw_shadow(self, surface, center_x, center_y, width, height=None):
        """Draw a shadow ellipse below the unit"""
        if height is None:
            height = width // 2
        
        shadow_rect = pygame.Rect(center_x - width // 2, center_y - height // 2, width, height)
        s = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 80), (0, 0, width, height))
        surface.blit(s, shadow_rect)


class KnightSprite(GeometricSprite):
    """Geometric representation of a Knight"""
    
    def __init__(self):
        super().__init__(40)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Knight"""
        # Color scheme
        if team == "player":
            body_color = (100, 150, 255)  # Blue
            armor_color = (150, 180, 255)
            accent_color = (200, 210, 255)
        else:
            body_color = (255, 100, 100)  # Red
            armor_color = (255, 150, 150)
            accent_color = (255, 200, 200)
            
        # Body (cylinder-ish)
        builder.draw_body(body_color, 20, 16, depth=12, offset_z=0)
        
        # Head
        builder.draw_head(armor_color, 8, offset_z=10)
        builder.draw_head(accent_color, 3, offset_z=14) # Plume
        
        # Sword (Right Hand)
        # Local coords: Right is +X, Forward is +Y
        hand_x = 10
        hand_y = 0
        hand_z = 5
        
        # Draw hand
        builder.draw_head(body_color, 4, offset_x=hand_x, offset_y=hand_y, offset_z=hand_z)
        
        # Sword swing
        # Swing arc: -45 to +45 degrees relative to forward (Y axis)
        swing = math.sin(animation_phase * math.pi * 2) * 45
        rad = math.radians(swing)
        
        # Vector length 18
        # 0 deg = Forward (0, 1)
        # + deg = Right (1, 0)
        sx = math.sin(rad) * 18
        sy = math.cos(rad) * 18
        
        builder.draw_limb((200, 200, 220), (hand_x, hand_y, hand_z), (hand_x + sx, hand_y + sy, hand_z), width=3)
        
        # Shield (Left Hand)
        shield_x = -10
        shield_y = 4
        shield_z = 5
        builder.draw_rect(armor_color, 12, 8, offset_x=shield_x, offset_y=shield_y, offset_z=shield_z, border_radius=2)
        builder.draw_rect(accent_color, 12, 8, offset_x=shield_x, offset_y=shield_y, offset_z=shield_z, border_radius=2) # Outline? No, draw_rect fills.


class MiniPekkaSprite(GeometricSprite):
    """Geometric representation of Mini P.E.K.K.A"""
    
    def __init__(self):
        super().__init__(40)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Mini PEKKA"""
        # Color scheme
        if team == "player":
            metal_color = (100, 120, 140)
            eye_color = (100, 200, 255)
        else:
            metal_color = (140, 100, 100)
            eye_color = (255, 100, 100)
        
        # Body
        builder.draw_body(metal_color, 18, 14, depth=14, offset_z=0)
        
        # Head
        builder.draw_head(metal_color, 8, offset_z=14)
        
        # Eye (One glowing eye)
        builder.draw_head(eye_color, 3, offset_y=6, offset_z=14)
        
        # Horns
        builder.draw_head(metal_color, 2, offset_x=-6, offset_z=18)
        builder.draw_head(metal_color, 2, offset_x=6, offset_z=18)
        
        # Sword (Right hand)
        hand_x = 10
        hand_y = 4
        hand_z = 8
        
        # Swing
        swing = math.sin(animation_phase * math.pi * 2) * 45
        rad = math.radians(swing)
        
        sx = math.sin(rad) * 16
        sy = math.cos(rad) * 16
        
        builder.draw_limb((200, 200, 220), (hand_x, hand_y, hand_z), (hand_x + sx, hand_y + sy, hand_z), width=3)


class ArcherSprite(GeometricSprite):
    """Geometric representation of an Archer"""
    
    def __init__(self):
        super().__init__(40)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Archer"""
        # Color scheme (green/forest theme)
        if team == "player":
            hood_color = (80, 140, 80)
            accent_color = (140, 200, 140)
        else:
            hood_color = (160, 70, 70)
            accent_color = (220, 140, 140)
            
        # Hood/Cape (Triangle)
        # Local coords: X=Right, Y=Forward
        builder.draw_polygon(hood_color, [
            (-12, -8, 0),
            (-12, 8, 0),
            (4, 0, 0)
        ])
        
        # Head
        builder.draw_head(accent_color, 6, offset_z=10)
        
        # Bow
        # Arc in front (Right side, +X).
        bow_x = 8
        bow_y = 0
        bow_z = 5
        
        # Draw bow as lines
        points = []
        for i in range(11):
            t = i / 10.0
            angle = (t - 0.5) * 2.0 # -1 to 1
            bx = bow_x - abs(angle) * 4
            by = bow_y + angle * 8
            bz = bow_z
            points.append((bx, by, bz))
            
        for i in range(len(points)-1):
            builder.draw_limb((120, 80, 40), points[i], points[i+1], width=2)
            
        # Arrow
        if animation_phase > 0.5:
            offset = (animation_phase - 0.5) * 20
            # Arrow flies along X (Right)
            builder.draw_limb((200, 200, 200), (bow_x - 10 + offset, bow_y, bow_z), (bow_x + 5 + offset, bow_y, bow_z), width=1)


class TowerSprite(GeometricSprite):
    """Geometric representation of a Tower"""
    
    def __init__(self, tower_type="princess"):
        # Get size from settings
        stats = TOWER_STATS.get(tower_type, {})
        size = stats.get("size", 60)
        super().__init__(size)
        self.tower_type = tower_type
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Tower"""
        # Color scheme
        if team == "player":
            stone_color = (120, 140, 180)
            dark_stone = (80, 100, 140)
            accent_color = (100, 150, 255)
        else:
            stone_color = (180, 120, 120)
            dark_stone = (140, 80, 80)
            accent_color = (255, 100, 100)
            
        if self.tower_type == "king":
            # King Tower - Large, Square, Tall
            width = self.size
            depth = self.size
            height = TOWER_HEIGHT_KING
            
            # Main Body
            builder.draw_box(stone_color, width, depth, height, offset_z=0)
            
            # Top Platform (slightly wider)
            plat_w = width + 8
            plat_d = depth + 8
            builder.draw_box(dark_stone, plat_w, plat_d, 10, offset_z=height)
            
            # Battlements (4 corners)
            bat_size = 12
            bat_h = 12
            z_top = height + 10
            
            # Corners
            corners = [
                (-plat_w//2 + bat_size//2, -plat_d//2 + bat_size//2),
                (plat_w//2 - bat_size//2, -plat_d//2 + bat_size//2),
                (-plat_w//2 + bat_size//2, plat_d//2 - bat_size//2),
                (plat_w//2 - bat_size//2, plat_d//2 - bat_size//2)
            ]
            
            for cx, cy in corners:
                builder.draw_box(stone_color, bat_size, bat_size, bat_h, offset_x=cx, offset_y=cy, offset_z=z_top)
                
            # Central Cannon/Turret
            builder.draw_head(dark_stone, 24, offset_z=z_top + 10)
            # Cannon barrel
            builder.draw_limb((40, 40, 40), (0, 0, z_top + 16), (0, 20, z_top + 16), width=8)
            
            # King (if active? or just always visible)
            builder.draw_head(accent_color, 8, offset_z=z_top + 24)
            
        else:
            # Princess Tower - Tall, Square
            width = self.size
            depth = self.size
            height = TOWER_HEIGHT_PRINCESS
            
            # Main Body
            builder.draw_box(stone_color, width, depth, height, offset_z=0)
            
            # Top Platform
            plat_w = width + 6
            plat_d = depth + 6
            builder.draw_box(dark_stone, plat_w, plat_d, 8, offset_z=height)
            
            # Battlements
            bat_size = 10
            bat_h = 8
            z_top = height + 8
            
            corners = [
                (-plat_w//2 + bat_size//2, -plat_d//2 + bat_size//2),
                (plat_w//2 - bat_size//2, -plat_d//2 + bat_size//2),
                (-plat_w//2 + bat_size//2, plat_d//2 - bat_size//2),
                (plat_w//2 - bat_size//2, plat_d//2 - bat_size//2)
            ]
            
            for cx, cy in corners:
                builder.draw_box(stone_color, bat_size, bat_size, bat_h, offset_x=cx, offset_y=cy, offset_z=z_top)
                
            # Princess (Tiny head)
            builder.draw_head(accent_color, 6, offset_z=z_top + 6)


class BabyDragonSprite(GeometricSprite):
    """Geometric representation of a Baby Dragon (flying unit)"""
    
    def __init__(self):
        super().__init__(100)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Baby Dragon"""
        # Color scheme (orange/fire theme)
        if team == "player":
            body_color = (255, 140, 80)
            wing_color = (255, 180, 120)
        else:
            body_color = (200, 80, 80)
            wing_color = (220, 120, 120)
            
        # Flying height
        bob = math.sin(animation_phase * math.pi * 2) * 2
        fly_z = 20 + bob
        
        # Wings (flapping)
        flap = math.sin(animation_phase * math.pi * 4) * 10
        
        # Left Wing (extends to -X)
        builder.draw_polygon(wing_color, [
            (-6, 0, fly_z + 5), # Shoulder
            (-18, -5, fly_z + 10 + flap), # Tip back
            (-12, 8, fly_z + 5 + flap) # Tip front
        ])
        
        # Right Wing (extends to +X)
        builder.draw_polygon(wing_color, [
            (6, 0, fly_z + 5),
            (18, -5, fly_z + 10 + flap),
            (12, 8, fly_z + 5 + flap)
        ])
        
        # Body (oval) - elongated in Y (Forward/Back)
        # draw_body draws a cylinder/box. 
        # Let's use a custom shape or just a body.
        builder.draw_body(body_color, 14, 20, depth=12, offset_z=fly_z)
        
        # Head (Forward +Y)
        builder.draw_head(body_color, 9, offset_y=12, offset_z=fly_z + 4)
        
        # Tail (Backward -Y)
        builder.draw_polygon(body_color, [
            (0, -10, fly_z),
            (0, -22, fly_z - 2),
            (0, -12, fly_z - 4)
        ])


class MinionsSprite(GeometricSprite):
    """Geometric representation of Minions (flying swarm)"""
    
    def __init__(self):
        super().__init__(60)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Minions"""
        # Color scheme (blue flying creature)
        if team == "player":
            body_color = (100, 150, 255)
            wing_color = (150, 180, 255)
        else:
            body_color = (200, 100, 100)
            wing_color = (220, 150, 150)
            
        # 3 Minions
        offsets = [
            (0, -10, 0),
            (-8, 8, 0),
            (8, 8, 0)
        ]
        
        for i, (ox, oy, oz) in enumerate(offsets):
            # Flap offset
            flap = math.sin((animation_phase + i*0.3) * math.pi * 6) * 4
            fly_z = 20 + math.sin((animation_phase + i*0.3) * math.pi * 2) * 2
            
            # Local center for this minion
            mx, my = ox, oy
            mz = fly_z
            
            # Wings
            builder.draw_polygon(wing_color, [
                (mx - 4, my, mz),
                (mx - 12, my - 4, mz + flap),
                (mx - 4, my + 4, mz + 2)
            ])
            builder.draw_polygon(wing_color, [
                (mx + 4, my, mz),
                (mx + 12, my - 4, mz + flap),
                (mx + 4, my + 4, mz + 2)
            ])
            
            # Body
            builder.draw_head(body_color, 5, offset_x=mx, offset_y=my, offset_z=mz)
            
            # Eye
            builder.draw_head((200, 200, 200), 2, offset_x=mx, offset_y=my+3, offset_z=mz+1)


class SkeletonArmySprite(GeometricSprite):
    """Geometric representation of Skeleton (single skeleton, spawns multiple)"""
    
    def __init__(self):
        super().__init__(60)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Skeleton Army (Single Skeleton)"""
        # Color scheme (white bone)
        bone_color = (240, 240, 240)
        
        # Single Skeleton at center
        sx, sy, sz = 0, 0, 0
        
        # Ribcage (small body) - Make it thinner/smaller
        builder.draw_body(bone_color, 8, 6, depth=8, offset_x=sx, offset_y=sy, offset_z=sz)
        
        # Head
        builder.draw_head(bone_color, 5, offset_x=sx, offset_y=sy, offset_z=sz+10)
        
        # Sword (Right hand)
        hand_x = sx + 5
        hand_y = sy + 2
        hand_z = sz + 4
        
        # Swing
        swing = math.sin(animation_phase * math.pi * 2) * 45
        rad = math.radians(swing)
        
        sw_x = math.sin(rad) * 10
        sw_y = math.cos(rad) * 10
        
        builder.draw_limb((180, 180, 180), (hand_x, hand_y, hand_z), (hand_x + sw_x, hand_y + sw_y, hand_z), width=1)


class GiantSprite(GeometricSprite):
    """Geometric representation of a Giant (large melee unit)"""
    
    def __init__(self):
        super().__init__(60)  # Larger sprite
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Giant"""
        # Color scheme (brown tunic)
        if team == "player":
            tunic_color = (120, 80, 40)
            skin_color = (255, 200, 150)
        else:
            tunic_color = (120, 60, 60)
            skin_color = (255, 200, 150)
            
        # Large Body
        builder.draw_body(tunic_color, 24, 20, depth=20, offset_z=0)
        
        # Head
        builder.draw_head(skin_color, 10, offset_z=20)
        # Beard/Hair (Orange)
        builder.draw_head((200, 100, 50), 11, offset_y=-2, offset_z=20) # Slightly behind/around
        builder.draw_head(skin_color, 9, offset_y=2, offset_z=20) # Face mask? No just draw face over beard
        
        # Arms/Fists
        # Right hand
        hand_x = 14
        hand_y = 8
        hand_z = 10
        
        # Punch animation
        punch = 0
        if animation_phase > 0.5:
            punch = math.sin((animation_phase - 0.5) * math.pi * 2) * 12
            
        # Arm
        builder.draw_limb(skin_color, (10, 0, 16), (hand_x, hand_y + punch, hand_z), width=6)
        # Fist
        builder.draw_head(skin_color, 6, offset_x=hand_x, offset_y=hand_y + punch, offset_z=hand_z)
        
        # Left hand
        builder.draw_limb(skin_color, (-10, 0, 16), (-14, 8, 10), width=6)
        builder.draw_head(skin_color, 6, offset_x=-14, offset_y=8, offset_z=10)


class MusketeerSprite(GeometricSprite):
    """Geometric representation of a Musketeer"""
    
    def __init__(self):
        super().__init__(45)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Musketeer"""
        # Color scheme (blue/purple uniform)
        if team == "player":
            uniform_color = (80, 100, 180)
            helmet_color = (60, 60, 80)
            feather_color = (255, 100, 150)
        else:
            uniform_color = (180, 80, 100)
            helmet_color = (80, 60, 60)
            feather_color = (255, 100, 150)
            
        # Body
        builder.draw_body(uniform_color, 18, 14, depth=16, offset_z=0)
        
        # Head (Helmet)
        builder.draw_head(helmet_color, 9, offset_z=16)
        
        # Feather
        builder.draw_head(feather_color, 4, offset_x=-4, offset_z=20)
        
        # Musket (Long gun)
        # Held with both hands? Or just right.
        # Let's put it on right side.
        gun_color = (100, 70, 40)
        barrel_color = (50, 50, 50)
        
        # Stock start (near shoulder)
        start_x = 5
        start_y = -5
        start_z = 10
        
        # End (forward)
        end_x = 5
        end_y = 20
        end_z = 10
        
        # Draw stock
        builder.draw_limb(gun_color, (start_x, start_y, start_z), (end_x, end_y - 10, end_z), width=4)
        # Draw barrel
        builder.draw_limb(barrel_color, (end_x, end_y - 10, end_z), (end_x, end_y, end_z), width=3)
        
        # Muzzle flash
        if animation_phase > 0.7:
            builder.draw_head((255, 255, 100), 5, offset_x=end_x, offset_y=end_y+2, offset_z=end_z)


class GoblinSprite(GeometricSprite):
    """Geometric representation of a Goblin"""
    
    def __init__(self):
        super().__init__(35)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Goblin"""
        # Color scheme (green skin)
        if team == "player":
            skin_color = (100, 200, 100)
            tunic_color = (100, 150, 100)
        else:
            skin_color = (180, 100, 100)
            tunic_color = (150, 80, 80)
            
        # Sack (on back/left)
        # Local: Back-Left (-8, -6, 5)
        builder.draw_head((160, 140, 100), 8, offset_x=-8, offset_y=-6, offset_z=5)
        
        # Body
        builder.draw_body(tunic_color, 14, 14, depth=10, offset_z=0)
        
        # Head
        builder.draw_head(skin_color, 7, offset_z=10)
        
        # Ears (Triangles on side of head)
        # Left Ear
        builder.draw_polygon(skin_color, [
            (-2, 0, 14), (-8, 0, 18), (-2, -2, 12)
        ])
        # Right Ear
        builder.draw_polygon(skin_color, [
            (2, 0, 14), (8, 0, 18), (2, -2, 12)
        ])
        
        # Dagger (Right hand)
        stab = math.sin(animation_phase * math.pi * 2) * 5
        hand_x = 6
        hand_y = 4 + stab
        hand_z = 5
        
        builder.draw_limb((200, 200, 200), (hand_x, hand_y, hand_z), (hand_x + 6, hand_y + 4, hand_z), width=2)


class WizardSprite(GeometricSprite):
    """Geometric representation of a Wizard"""
    
    def __init__(self):
        super().__init__(45)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Wizard"""
        # Color scheme (blue robes)
        if team == "player":
            robe_color = (60, 80, 180)
            hood_color = (40, 60, 140)
        else:
            robe_color = (180, 60, 60)
            hood_color = (140, 40, 40)
            
        # Robes (Cone/Body)
        builder.draw_body(robe_color, 20, 16, depth=20, offset_z=0)
        
        # Head/Hood
        builder.draw_head(hood_color, 8, offset_z=18)
        
        # Hands (Casting)
        # Right hand forward
        hand_x = 10
        hand_y = 5
        hand_z = 12
        
        builder.draw_head((255, 200, 150), 4, offset_x=hand_x, offset_y=hand_y, offset_z=hand_z)
        
        # Fireball
        if animation_phase > 0.5:
            fire_size = int(math.sin(animation_phase * math.pi) * 6) + 4
            builder.draw_head((255, 100, 0), fire_size, offset_x=hand_x+2, offset_y=hand_y+2, offset_z=hand_z)
            builder.draw_head((255, 200, 0), fire_size-2, offset_x=hand_x+2, offset_y=hand_y+2, offset_z=hand_z)


class HogRiderSprite(GeometricSprite):
    """Geometric representation of a Hog Rider"""
    
    def __init__(self):
        super().__init__(55)
        
    def render_figurine(self, builder, team, animation_phase):
        """3D Figurine view of Hog Rider"""
        # Color scheme
        hog_color = (160, 120, 100)
        if team == "player":
            rider_color = (100, 60, 40)
            tunic_color = (100, 150, 255)
        else:
            rider_color = (100, 60, 40)
            tunic_color = (255, 100, 100)
            
        # Hog Body
        # Local: Forward is Y.
        builder.draw_body(hog_color, 16, 24, depth=14, offset_z=0)
        
        # Hog Head
        builder.draw_head(hog_color, 8, offset_y=14, offset_z=10)
        # Hog Ears
        builder.draw_head(hog_color, 3, offset_x=-6, offset_y=14, offset_z=14)
        builder.draw_head(hog_color, 3, offset_x=6, offset_y=14, offset_z=14)
        
        # Rider Body (on top of hog)
        builder.draw_body(tunic_color, 12, 10, depth=12, offset_z=14)
        
        # Rider Head
        builder.draw_head(rider_color, 6, offset_z=26)
        # Mohawk
        builder.draw_head((50, 50, 50), 3, offset_z=30)
        
        # Hammer (Right hand)
        hand_x = 8
        hand_y = 0
        hand_z = 20
        
        # Swing
        swing = math.sin(animation_phase * math.pi * 2) * 45
        rad = math.radians(swing)
        
        hx = math.sin(rad) * 14
        hy = math.cos(rad) * 14
        
        # Handle
        builder.draw_limb((160, 120, 80), (hand_x, hand_y, hand_z), (hand_x + hx, hand_y + hy, hand_z), width=3)
        # Head of hammer
        builder.draw_head((100, 100, 100), 6, offset_x=hand_x+hx, offset_y=hand_y+hy, offset_z=hand_z)


class BalloonSprite(GeometricSprite):
    """Geometric representation of a Balloon"""
    
    def __init__(self):
        super().__init__(80)
        
    def render_top_down(self, team, animation_phase):
        """Top-down view of Balloon facing RIGHT"""
        # Blue balloon
        balloon_color = (100, 180, 255) if team == "player" else (255, 100, 100)
        
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2
        
        # Balloon (large circle)
        pygame.draw.circle(s, balloon_color, (center, center), 20)
        # Highlight
        pygame.draw.circle(s, (255, 255, 255, 100), (center - 6, center - 6), 6)
        
        # Basket (below balloon, but in top-down view it's underneath)
        # We can draw the rim of the basket peeking out? Or maybe just the balloon is visible.
        # Let's draw the basket ropes going down.
        
        # Ropes (4 corners)
        rope_color = (160, 120, 80)
        pygame.draw.line(s, rope_color, (center - 15, center - 15), (center, center), 1)
        pygame.draw.line(s, rope_color, (center + 15, center - 15), (center, center), 1)
        pygame.draw.line(s, rope_color, (center - 15, center + 15), (center, center), 1)
        pygame.draw.line(s, rope_color, (center + 15, center + 15), (center, center), 1)
        
        # Patches on balloon
        pygame.draw.rect(s, (200, 200, 200), (center + 8, center - 10, 6, 6))
        pygame.draw.line(s, (0, 0, 0), (center + 8, center - 10), (center + 14, center - 4), 1)
        pygame.draw.line(s, (0, 0, 0), (center + 14, center - 10), (center + 8, center - 4), 1)
        
        # Skeleton Pilot (tiny head visible on side?)
        # Maybe not visible from top down if balloon is huge.
        
        return s






class FireballSprite(GeometricSprite):
    """Geometric representation of Fireball spell"""
    
    def __init__(self):
        super().__init__(50)
        
    def render(self, team="player", animation_phase=0, direction="down"):
        self.surface.fill((0, 0, 0, 0))

        
        center_x, center_y = self.size // 2, self.size // 2
        
        # Fireball core
        pygame.draw.circle(self.surface, (255, 140, 0), (center_x, center_y), 15)
        pygame.draw.circle(self.surface, (255, 200, 50), (center_x, center_y), 10)
        pygame.draw.circle(self.surface, (255, 255, 150), (center_x, center_y), 5)
        
        # Flames/Trail
        for i in range(3):
            offset_x = int(math.cos(i * 2 + animation_phase) * 5)
            offset_y = int(math.sin(i * 2 + animation_phase) * 5)
            pygame.draw.circle(self.surface, (255, 100, 0), 
                             (center_x - 10 + offset_x, center_y - 10 + offset_y), 6)
            
        return self.surface


class ArrowsSprite(GeometricSprite):
    """Geometric representation of Arrows spell"""
    
    def __init__(self):
        super().__init__(50)
        
    def render(self, team="player", animation_phase=0, direction="down"):
        self.surface.fill((0, 0, 0, 0))

        
        center_x, center_y = self.size // 2, self.size // 2
        
        # Draw 3 arrows
        offsets = [(-10, 5), (0, -5), (10, 5)]
        
        for dx, dy in offsets:
            x, y = center_x + dx, center_y + dy
            
            # Arrow shaft
            pygame.draw.line(self.surface, (160, 120, 80), (x, y - 10), (x, y + 10), 2)
            
            # Arrow head
            pygame.draw.polygon(self.surface, (200, 50, 50), [
                (x, y + 12),
                (x - 4, y + 8),
                (x + 4, y + 8),
            ])
            
            # Fletching
            pygame.draw.line(self.surface, (220, 220, 220), (x - 3, y - 10), (x - 3, y - 6), 1)
            pygame.draw.line(self.surface, (220, 220, 220), (x + 3, y - 10), (x + 3, y - 6), 1)
            
        return self.surface


class ZapSprite(GeometricSprite):
    """Geometric representation of Zap spell"""
    
    def __init__(self):
        super().__init__(50)
        
    def render(self, team="player", animation_phase=0, direction="down"):
        self.surface.fill((0, 0, 0, 0))

        
        center_x, center_y = self.size // 2, self.size // 2
        
        # Lightning bolt shape
        points = [
            (center_x + 5, center_y - 15),
            (center_x - 5, center_y),
            (center_x + 8, center_y),
            (center_x - 2, center_y + 15),
        ]
        
        # Glow
        pygame.draw.lines(self.surface, (100, 200, 255), False, points, 6)
        # Core
        pygame.draw.lines(self.surface, (200, 240, 255), False, points, 2)
        
        return self.surface



class PoisonSprite(GeometricSprite):
    """Geometric representation of Poison spell"""
    
    def __init__(self):
        super().__init__(50)
        
    def render(self, team="player", animation_phase=0, direction="down"):
        self.surface.fill((0, 0, 0, 0))

        
        center_x, center_y = self.size // 2, self.size // 2
        
        # Bubbling pool
        pygame.draw.circle(self.surface, (100, 255, 100), (center_x, center_y), 15)
        pygame.draw.circle(self.surface, (50, 200, 50), (center_x, center_y), 12)
        
        # Bubbles
        for i in range(3):
            offset_x = int(math.cos(i * 2 + animation_phase * 2) * 8)
            offset_y = int(math.sin(i * 2 + animation_phase * 2) * 8)
            size = 3 + int(math.sin(animation_phase * 5 + i) * 2)
            pygame.draw.circle(self.surface, (150, 255, 150), 
                             (center_x + offset_x, center_y + offset_y), size)
            
        # Fumes
        fume_y = center_y - 10 - int(animation_phase * 10)
        if fume_y < center_y - 20: fume_y += 10
        pygame.draw.circle(self.surface, (100, 255, 100, 100), (center_x, fume_y), 5)
            
        return self.surface


class GeometricSpriteRenderer:
    """Manages and caches geometric sprite renders"""
    
    def __init__(self):
        self.sprites = {
            "knight": KnightSprite(),
            "archer": ArcherSprite(),
            "baby_dragon": BabyDragonSprite(),
            "minions": MinionsSprite(),
            "skeleton_army": SkeletonArmySprite(),
            "giant": GiantSprite(),
            "musketeer": MusketeerSprite(),
            "goblin": GoblinSprite(),
            "goblin_gang": GoblinSprite(),  # Use same sprite for gang
            "wizard": WizardSprite(),
            "hog_rider": HogRiderSprite(),
            "balloon": BalloonSprite(),
            "mini_pekka": MiniPekkaSprite(),
            "king_tower": TowerSprite("king"),
            "princess_tower": TowerSprite("princess"),
            "fireball": FireballSprite(),
            "arrows": ArrowsSprite(),
            "zap": ZapSprite(),
            "poison": PoisonSprite(),
        }
        self.cache = {}
        self.card_icons = {}  # Cache for card icons
        
    def get_sprite(self, sprite_type, team="player", animation_phase=0, direction=0):
        """Get a rendered sprite surface"""
        # Quantize angle if it's a number
        if isinstance(direction, (int, float)):
            direction = round(direction / 5) * 5
            direction = direction % 360
            
        # Simple cache key (could be expanded)
        cache_key = f"{sprite_type}_{team}_{int(animation_phase * 10)}_{direction}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        if sprite_type in self.sprites:
            # Limit cache size BEFORE adding new item
            if len(self.cache) > 2000:
                self.cache.clear()

            surface = self.sprites[sprite_type].render(team, animation_phase, direction)
            # Convert alpha to ensure proper transparency and performance
            try:
                self.cache[cache_key] = surface.convert_alpha()
            except pygame.error:
                # Fallback if no display initialized (e.g. tests)
                self.cache[cache_key] = surface.copy()
            
            return self.cache[cache_key]
        return None



    def get_card_icon(self, card_name, size=(60, 80)):
        """Generate a card icon for deck/hand display"""
        # Check cache
        cache_key = f"icon_{card_name}_{size[0]}x{size[1]}"
        if cache_key in self.card_icons:
            return self.card_icons[cache_key]
        
        # Create card background
        icon = pygame.Surface(size, pygame.SRCALPHA)
        
        # Determine stats and rarity
        stats = None
        if card_name in UNIT_STATS:
            stats = UNIT_STATS[card_name]
        elif card_name in SPELL_STATS:
            stats = SPELL_STATS[card_name]
            
        rarity = stats.get("rarity", "common") if stats else "common"
        
        # Rarity Colors
        if rarity == "legendary":
            bg_color = RARITY_LEGENDARY
            border_color = (0, 200, 200)
        elif rarity == "epic":
            bg_color = RARITY_EPIC
            border_color = (150, 0, 200)
        elif rarity == "rare":
            bg_color = RARITY_RARE
            border_color = (200, 120, 0)
        else: # common
            bg_color = RARITY_COMMON
            border_color = (80, 120, 200)
            
        # Draw Card Shape
        if rarity == "legendary":
            # Hexagonal shape for Legendary
            w, h = size
            points = [
                (w//2, 0),          # Top center
                (w, h//4),          # Top right
                (w, 3*h//4),        # Bottom right
                (w//2, h),          # Bottom center
                (0, 3*h//4),        # Bottom left
                (0, h//4)           # Top left
            ]
            pygame.draw.polygon(icon, bg_color, points)
            pygame.draw.polygon(icon, border_color, points, 3)
            
            # Inner fill (slightly lighter/darker to show depth)
            inner_points = [
                (w//2, 4),
                (w-4, h//4 + 2),
                (w-4, 3*h//4 - 2),
                (w//2, h-4),
                (4, 3*h//4 - 2),
                (4, h//4 + 2)
            ]
            pygame.draw.polygon(icon, (255, 255, 255), inner_points) # White background for sprite
            
        else:
            # Standard Rounded Rect
            pygame.draw.rect(icon, bg_color, (0, 0, size[0], size[1]), border_radius=8)
            pygame.draw.rect(icon, border_color, (0, 0, size[0], size[1]), 3, border_radius=8)
            
            # Inner white area for sprite
            inner_rect = pygame.Rect(4, 4, size[0]-8, size[1]-8)
            pygame.draw.rect(icon, (240, 240, 240), inner_rect, border_radius=6)
        
        # Get sprite for this card
        if card_name in self.sprites:
            # Check if swarm
            count = 1
            if card_name in UNIT_STATS:
                count = UNIT_STATS[card_name]["count"]
            
            sprite_surface = self.sprites[card_name].render("player", 0)
            sprite_rect = sprite_surface.get_rect()
            
            # Available height for sprite
            avail_height = size[1] - 16 
            avail_width = size[0] - 16
            
            if count > 1:
                # Render 3 sprites in a triangle
                scale_factor = min(avail_width / (sprite_rect.width * 1.5), 
                                  avail_height / (sprite_rect.height * 1.5))
                new_size = (int(sprite_rect.width * scale_factor), 
                           int(sprite_rect.height * scale_factor))
                scaled_sprite = pygame.transform.smoothscale(sprite_surface, new_size)
                
                center_x = size[0] // 2
                center_y = size[1] // 2
                
                # Top
                icon.blit(scaled_sprite, (center_x - new_size[0]//2, center_y - new_size[1] - 2))
                # Bottom Left
                icon.blit(scaled_sprite, (center_x - new_size[0] - 2, center_y))
                # Bottom Right
                icon.blit(scaled_sprite, (center_x + 2, center_y))
                
            else:
                # Single sprite
                scale_factor = min(avail_width / sprite_rect.width, 
                                  avail_height / sprite_rect.height)
                new_size = (int(sprite_rect.width * scale_factor), 
                           int(sprite_rect.height * scale_factor))
                scaled_sprite = pygame.transform.smoothscale(sprite_surface, new_size)
                
                # Center sprite on card
                sprite_x = (size[0] - new_size[0]) // 2
                sprite_y = (size[1] - new_size[1]) // 2
                icon.blit(scaled_sprite, (sprite_x, sprite_y))
        else:
            # Fallback: just text
            font = pygame.font.SysFont("Arial", 12)
            text = font.render(card_name[:4], True, (0, 0, 0))
            text_rect = text.get_rect(center=(size[0]//2, size[1]//2))
            icon.blit(text, text_rect)
            
        # NO TEXT NAME DRAWING
        
        # Cache it
        self.card_icons[cache_key] = icon
        return icon


# Global renderer instance
geometric_renderer = GeometricSpriteRenderer()
