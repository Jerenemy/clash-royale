import pygame
import math
from game.settings import *
from game.assets import assets
from game.entities.particles import particle_system
from game.entities.geometric_sprites import geometric_renderer
import random
import uuid

class Entity(pygame.sprite.Sprite):
    def __init__(self, game, x, y, team, network_id=None):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.team = team
        self.network_id = network_id or str(uuid.uuid4())
        self.game = game
        self.team = team
        self.image = None # Will be set by subclass
        self.rect = pygame.Rect(x, y, 30, 30) # Default rect
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        self.health = 100
        self.max_health = 100
        self.last_attack_time = 0
        self.attack_cooldown = 1.0
        self.damage = 0
        self.range = 0
        self.target = None
        
        # Animation
        self.anim_offset = pygame.math.Vector2(0, 0)
        self.anim_timer = 0
        self.is_moving = False
        self.is_attacking = False
        self.attack_anim_timer = 0
        
        # Hitbox
        self.hitbox_type = "circle" # Default
        self.radius = 15 # Default radius
        
    def get_closest_point(self, point):
        """Get the closest point on this entity's hitbox to the given point"""
        if self.hitbox_type == "circle":
            direction = point - self.pos
            if direction.length() == 0:
                return self.pos
            direction = direction.normalize()
            return self.pos + direction * self.radius
            
        elif self.hitbox_type == "rect":
            # Use floating point bounds based on pos and size/rect
            # Assuming square/centered if size is present, else use rect dimensions relative to pos
            
            w = self.rect.width
            h = self.rect.height
            if hasattr(self, 'size'):
                w = self.size
                h = self.size
                
            # Calculate float bounds
            left = self.pos.x - w / 2.0
            right = self.pos.x + w / 2.0
            top = self.pos.y - h / 2.0
            bottom = self.pos.y + h / 2.0
            
            # Clamp point to bounds
            x = max(left, min(point.x, right))
            y = max(top, min(point.y, bottom))
            return pygame.math.Vector2(x, y)
            
        return self.pos

    def get_edge_distance(self, other):
        """Calculate distance between the edges of two entities"""
        # 1. Get closest points on each other's hitboxes?
        # Not exactly. We want the distance between the shapes.
        
        if self.hitbox_type == "circle" and other.hitbox_type == "circle":
            dist = self.pos.distance_to(other.pos)
            return dist - (self.radius + other.radius)
            
        elif self.hitbox_type == "rect" and other.hitbox_type == "rect":
            # Rect-Rect distance (simplified, usually not needed for units)
            # Just use center distance minus approximation or 0 if overlapping
            if self.rect.colliderect(other.rect):
                return 0
            # This is complex for arbitrary rects, but towers don't move.
            # Let's fallback to center distance minus sizes for now if needed, 
            # but units are circles.
            return 0 # Placeholder
            
        else:
            # Circle-Rect
            circle = self if self.hitbox_type == "circle" else other
            rect_entity = other if self.hitbox_type == "circle" else self
            
            # Find closest point on Rect to Circle Center
            closest = rect_entity.get_closest_point(circle.pos)
            
            # Distance from circle center to closest point
            dist_to_closest = circle.pos.distance_to(closest)
            
            # Edge distance is dist_to_closest - circle radius
            return dist_to_closest - circle.radius

    def update_animation(self, dt):
        self.anim_timer += dt
        
        # Bobbing animation when moving
        if self.is_moving:
            bob_amount = 3
            bob_speed = 15
            self.anim_offset.y = math.sin(self.anim_timer * bob_speed) * bob_amount
        else:
            self.anim_offset.y = 0
            
        # Attack lunge animation
        if self.is_attacking:
            self.attack_anim_timer += dt
            lunge_duration = 0.2
            if self.attack_anim_timer < lunge_duration:
                # Lunge forward
                progress = self.attack_anim_timer / lunge_duration
                lunge_dist = 10
                # Calculate direction to target
                if self.target and self.target.alive():
                    direction = (self.target.pos - self.pos).normalize()
                    # Sine wave for lunge: 0 -> 1 -> 0
                    lunge_amount = math.sin(progress * math.pi) * lunge_dist
                    self.anim_offset = direction * lunge_amount
            else:
                self.is_attacking = False
                self.anim_offset = pygame.math.Vector2(0, 0)
    
    def update_sprite(self):
        """Override in subclasses to update sprite based on animation state"""
        pass

    def draw(self, surface):
        # Shadow is now handled by the sprite itself (GeometricSprite)
        # to ensure correct perspective and positioning.
        pass

        # Custom draw to include animation offset
        draw_pos = self.rect.topleft + self.anim_offset
        
        if self.image:
            surface.blit(self.image, draw_pos)
        
        self.draw_health_bar(surface, draw_pos)

    def draw_health_bar(self, surface, pos=None):
        if pos is None:
            pos = self.rect.topleft
            
        if self.health < self.max_health:
            width = self.rect.width
            height = 5
            fill = (self.health / self.max_health) * width
            pygame.draw.rect(surface, RED, (pos[0], pos[1] - 10, width, height))
            pygame.draw.rect(surface, GREEN, (pos[0], pos[1] - 10, fill, height))

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, target, damage, team, projectile_type="basic"):
        self.groups = game.all_sprites, game.projectiles
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.target = target
        self.damage = damage
        self.team = team
        self.projectile_type = projectile_type
        self.speed = 300
        self.pos = pygame.math.Vector2(x, y)
        self.rotation = 0
        
        # Create projectile image based on type
        self.create_image()
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def create_image(self):
        """Override in subclasses for custom projectile visuals"""
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLACK, (5, 5), 5)

    def update(self, dt):
        if not self.target.alive():
            self.kill()
            return
            
        target_pos = self.target.pos
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            # Calculate rotation angle
            self.rotation = math.atan2(direction.y, direction.x)
        
        self.pos += direction * self.speed * dt
        self.rect.center = self.pos
        
        # Particle Trail
        particle_system.create_projectile_trail(self.pos.x, self.pos.y, self.get_trail_color())
        
        if self.pos.distance_to(target_pos) < 10:
            self.on_hit()
            self.kill()
    
    def get_trail_color(self):
        """Override for custom trail colors"""
        return BLACK
    
    def on_hit(self):
        """Override for custom hit effects"""
        self.target.take_damage(self.damage)
        particle_system.create_explosion(self.pos.x, self.pos.y, RED if self.team == "enemy" else BLUE)
        assets.play_sound("hit")


class ArrowProjectile(Projectile):
    """Arrow projectile for Archers"""
    
    def __init__(self, game, x, y, target, damage, team):
        super().__init__(game, x, y, target, damage, team, "arrow")
        self.speed = 400  # Faster than basic
        
    def create_image(self):
        self.image = pygame.Surface((20, 6), pygame.SRCALPHA)
        # Arrow shaft
        pygame.draw.line(self.image, (180, 140, 100), (0, 3), (16, 3), 2)
        # Arrow head
        pygame.draw.polygon(self.image, (200, 200, 220), [
            (18, 3),
            (16, 1),
            (16, 5),
        ])
        # Feathers
        pygame.draw.line(self.image, (220, 220, 220), (2, 1), (2, 5), 1)
        
    def update(self, dt):
        # Rotate arrow to face target
        if self.target.alive():
            target_pos = self.target.pos
            direction = target_pos - self.pos
            if direction.length() > 0:
                angle = math.degrees(math.atan2(direction.y, direction.x))
                # Recreate and rotate image
                original = pygame.Surface((20, 6), pygame.SRCALPHA)
                pygame.draw.line(original, (180, 140, 100), (0, 3), (16, 3), 2)
                pygame.draw.polygon(original, (200, 200, 220), [(18, 3), (16, 1), (16, 5)])
                pygame.draw.line(original, (220, 220, 220), (2, 1), (2, 5), 1)
                self.image = pygame.transform.rotate(original, -angle)
                self.rect = self.image.get_rect(center=self.rect.center)
        
        super().update(dt)
    
    def get_trail_color(self):
        return (200, 200, 200)
    
    def on_hit(self):
        # Arrow impact
        self.target.take_damage(self.damage)
        particle_system.create_explosion(self.pos.x, self.pos.y, (220, 220, 220), count=5)
        assets.play_sound("hit")


class FireballProjectile(Projectile):
    """Fireball projectile for Baby Dragon"""
    
    def __init__(self, game, x, y, target, damage, team):
        super().__init__(game, x, y, target, damage, team, "fireball")
        self.speed = 250
        self.life_timer = 0
        
    def create_image(self):
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        # Outer fire
        pygame.draw.circle(self.image, (255, 140, 0), (8, 8), 8)
        # Inner fire
        pygame.draw.circle(self.image, (255, 200, 50), (8, 8), 5)
        # Core
        pygame.draw.circle(self.image, (255, 255, 100), (8, 8), 3)
    
    def update(self, dt):
        self.life_timer += dt
        # Pulsing animation
        scale = 1.0 + math.sin(self.life_timer * 10) * 0.2
        
        # Recreate pulsing fireball
        size = int(16 * scale)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        pygame.draw.circle(self.image, (255, 140, 0), (center, center), center)
        pygame.draw.circle(self.image, (255, 200, 50), (center, center), int(center * 0.6))
        pygame.draw.circle(self.image, (255, 255, 100), (center, center), int(center * 0.4))
        
        super().update(dt)
    
    def get_trail_color(self):
        return (255, 150, 0)
    
    def on_hit(self):
        # Explosive fireball impact
        self.target.take_damage(self.damage)
        particle_system.create_explosion(self.pos.x, self.pos.y, (255, 140, 0), count=15)
        # Additional fire particles
        for _ in range(8):
            angle = random.uniform(0, 360)
            speed = random.uniform(30, 80)
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            from game.entities.particles import Particle
            p = Particle(self.pos.x, self.pos.y, (255, 200, 50), 
                        (vel_x, vel_y), 0.4, 4, decay_rate=8)
            particle_system.particles.append(p)
        assets.play_sound("hit")


class SpearProjectile(Projectile):
    """Spear projectile for Minions"""
    
    def __init__(self, game, x, y, target, damage, team):
        super().__init__(game, x, y, target, damage, team, "spear")
        self.speed = 350
        
    def create_image(self):
        self.image = pygame.Surface((18, 4), pygame.SRCALPHA)
        # Spear shaft
        pygame.draw.line(self.image, (160, 120, 80), (0, 2), (14, 2), 2)
        # Spear tip
        pygame.draw.polygon(self.image, (180, 180, 200), [
            (17, 2),
            (14, 0),
            (14, 4),
        ])
        
    def update(self, dt):
        # Rotate spear to face target
        if self.target.alive():
            target_pos = self.target.pos
            direction = target_pos - self.pos
            if direction.length() > 0:
                angle = math.degrees(math.atan2(direction.y, direction.x))
                original = pygame.Surface((18, 4), pygame.SRCALPHA)
                pygame.draw.line(original, (160, 120, 80), (0, 2), (14, 2), 2)
                pygame.draw.polygon(original, (180, 180, 200), [(17, 2), (14, 0), (14, 4)])
                self.image = pygame.transform.rotate(original, -angle)
                self.rect = self.image.get_rect(center=self.rect.center)
        
        super().update(dt)
    
    def get_trail_color(self):
        return (140, 120, 160)
    
    def on_hit(self):
        # Spear impact
        self.target.take_damage(self.damage)
        particle_system.create_explosion(self.pos.x, self.pos.y, (160, 140, 180), count=6)
        assets.play_sound("hit")




class Tower(Entity):
    def __init__(self, game, x, y, type, team, network_id=None):
        super().__init__(game, x, y, team, network_id)
        self.game.towers.add(self)
        stats = TOWER_STATS[type]
        self.type = type
        self.health = stats["health"]
        self.max_health = stats["health"]
        self.damage = stats["damage"]
        self.range = stats["range"]
        self.attack_cooldown = 1.0 / stats["attack_speed"]
        self.size = stats["size"]
        
        # Hitbox properties
        self.hitbox_type = "rect"
        # Radius is not used for collision, but maybe for some calculations?
        self.radius = self.size / 2 
        
        # King Tower starts inactive
        self.active = True
        if self.type == "king":
            self.active = False
        
        if self.type == "king":
            self.active = False
        
        # Use geometric sprites instead of PNG assets
        sprite_key = "king_tower" if self.type == "king" else "princess_tower"
        self.image = geometric_renderer.get_sprite(sprite_key, team, 0)
        
        if not self.image:
            # Extreme fallback
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            color = BLUE if team == "player" else RED
            self.image.fill(color)
            
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        
        # Explicit Hitbox Rect (Base footprint)
        # This is separate from self.rect which might include height/perspective
        self.hitbox_rect = pygame.Rect(0, 0, self.size, self.size)
        self.hitbox_rect.center = (x, y)
        
        # Targeting
        self.unit_type = "ground"  # Towers are ground structures
        self.target_type = "both"  # Towers can target both air and ground
        
        self.pending_attack = False

    def think(self, dt):
        """Phase 1: Logic and Targeting"""
        if self.active:
            # Target Locking
            if not self.target or not self.target.alive():
                self.find_target()
            elif self.pos.distance_to(self.target.pos) > self.range + 0.001:
                self.find_target()
                
            self.pending_attack = False
            if self.target and self.last_attack_time >= self.attack_cooldown:
                self.pending_attack = True

    def update(self, dt):
        """Phase 2: State Update"""
        self.update_animation(dt) # Update animation state
        self.last_attack_time += dt
        
        if self.pending_attack:
            self.attack()

    def take_damage(self, amount):
        super().take_damage(amount)
        if self.health <= 0:
            particle_system.create_rubble(self.pos.x, self.pos.y)
            assets.play_sound("tower_destroy")
            
        if self.type == "king" and not self.active:
            self.active = True

    def find_target(self):
        closest_dist = self.range + 0.001 # Epsilon
        self.target = None
        
        # Target units
        # Iterate deterministically if possible, or use tie-breaker
        targets = self.game.units
        
        best_target = None
        min_dist = self.range + 0.001 # Epsilon
        
        for target in targets:
            if target.team != self.team and target.alive():
                dist = self.pos.distance_to(target.pos)
                
                if dist <= min_dist:
                    # If significantly closer, take it
                    if dist < min_dist - 0.1:
                        min_dist = dist
                        best_target = target
                    # If roughly equal (within epsilon), tie-break using network_id
                    elif dist < min_dist + 0.1:
                        # If we already have a best target, compare IDs
                        if best_target:
                            # Prefer lower ID for stability
                            if getattr(target, 'network_id', '') < getattr(best_target, 'network_id', ''):
                                min_dist = dist
                                best_target = target
                        else:
                            min_dist = dist
                            best_target = target
                            
        self.target = best_target

    def attack(self):
        if self.target:
            Projectile(self.game, self.pos.x, self.pos.y, self.target, self.damage, self.team)
            self.last_attack_time = 0
            
    def draw_health_bar(self, surface, pos=None):
        # Always draw health bar for towers, even at full health
        # if self.health >= self.max_health:
        #    return
            
        # Use global constants
        bar_width = HEALTH_BAR_WIDTH
        bar_height = HEALTH_BAR_HEIGHT
        
        # Position: "below the top"
        # Let's say 1/3 down from the top of the rect
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top + (self.rect.height // 3)
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Fill
        fill_width = int((self.health / self.max_health) * bar_width)
        color = BLUE if self.team == "player" else RED
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # HP Text
        font_small = pygame.font.SysFont("Arial", 14, bold=True)
        hp_text = font_small.render(f"{int(self.health)}", True, WHITE)
        hp_shadow = font_small.render(f"{int(self.health)}", True, BLACK)
        
        text_x = self.rect.centerx - hp_text.get_width() // 2
        
        if self.type == "princess":
            if self.team == "player":
                # Ally: Text BELOW bar
                text_y = bar_y + bar_height + 2
            else:
                # Enemy: Text ABOVE bar
                text_y = bar_y - hp_text.get_height() - 2
        else:
            # King Tower: Keep symmetric/standard (Text on top?)
            # User said "keep the king tower labeling the same"
            # Previous logic had text above for player, below for enemy? 
            # Actually, previous logic in managers.py was:
            # Enemy King: Above (rect.top - 15)
            # Player King: Above (rect.top - 12)
            # Let's put it above the bar for both for visibility, or match the princess style?
            # "keep the king tower labeling the same. just keep the labeling symmetric"
            # Let's put text above the bar for King Tower to be safe/standard.
            text_y = bar_y - hp_text.get_height() - 2
            
        # Draw shadow then text
        surface.blit(hp_shadow, (text_x + 1, text_y + 1))
        surface.blit(hp_text, (text_x, text_y))

    def take_damage(self, amount):
        super().take_damage(amount)
        if self.type == "king" and not self.active:
            self.active = True

class Unit(Entity):
    def __init__(self, game, x, y, type, team, network_id=None):
        super().__init__(game, x, y, team, network_id)
        self.game.units.add(self)
        stats = UNIT_STATS[type]
        self.health = stats["health"]
        self.max_health = stats["health"]
        self.damage = stats["damage"]
        self.speed = stats["speed"]
        self.range = stats["range"]
        self.attack_cooldown = 1.0 / stats["attack_speed"]
        self.cost = stats["cost"]
        
        self.cost = stats["cost"]
        self.cost = stats["cost"]
        self.size = stats.get("size", 20) # Default size if not specified
        self.radius = self.size / 2
        self.mass = stats.get("mass", 10) # Default mass
        
        # Unit type and targeting
        self.unit_type = stats.get("unit_type", "ground")
        self.target_type = stats.get("target_type", "both")
        self.target_preference = stats.get("target_preference", "any")
        
        # Use geometric sprites
        self.unit_type_name = type  # Store for rendering
        self.image = geometric_renderer.get_sprite(type, team, 0)
        
        if not self.image:
            # Fallback
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
            self.image.fill(stats["color"])
            
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        
        self.deploy_timer = 0.0 # Instant deployment
        self.state = "active"
        self.image.set_alpha(255)
        
        # Initial facing based on team
        # Player units move UP (270), Enemy units move DOWN (90)
        if self.team == "player":
            self.facing_angle = 270
            self.facing_direction = "up"
        else:
            self.facing_angle = 90
            self.facing_direction = "down"
            
        self.flip_x = False
        
        self.last_move_dir = pygame.math.Vector2(0, 0) # Initialize last move dir
        
        # Target locking properties
        # Ensure sight range is larger than attack range so we chase targets that move out of range
        self.sight_range = max(250, self.range * 1.5) 
        self.nudged = False # Flag to trigger retargeting on collision
        
        # New Targeting Logic: Only lock after attacking
        self.locked_target = False
        self.retarget_timer = 0 # Deterministic start
        
        # Two-Phase Update State
        self.pending_move = pygame.math.Vector2(0, 0)
        self.pending_attack = False
        self.pending_pushes = [] # List of (unit, vector)
        
    def update_sprite(self):
        sprite_key = self.unit_type_name
        
        # Pass precise angle if available, otherwise fallback to legacy direction
        direction_arg = getattr(self, 'facing_angle', 0)
        
        # Calculate animation phase (0-1) based on timer
        self.animation_phase = (self.anim_timer % 1.0)
        
        self.image = geometric_renderer.get_sprite(
            sprite_key, 
            self.team, 
            self.animation_phase,
            direction_arg
        )
        
        # No need to flip_x manually if we are using 360 rotation, 
        # but for legacy sprites or if rotation fails, we might keep it.
        # However, our new renderer handles rotation.
        # If we are using legacy sprites (e.g. buildings), they might ignore angle.
        if self.flip_x and isinstance(direction_arg, str): # Only flip if using legacy string direction
             self.image = pygame.transform.flip(self.image, True, False)
             
        self.rect = self.image.get_rect(center=self.pos)

    def think(self, dt):
        """Phase 1: Logic and Targeting"""
        if self.state == "deploying":
            return

        # Target Locking: Only find new target if current is invalid, out of range, or we were nudged
        should_retarget = False
        
        if not self.target or not self.target.alive():
            should_retarget = True
            self.locked_target = False # Reset lock
        elif self.pos.distance_to(self.target.pos) > self.sight_range: # Target moved out of chase range
             should_retarget = True
             self.locked_target = False # Reset lock
        elif self.nudged: # We were pushed/nudged, so re-evaluate target
             should_retarget = True
             self.locked_target = False # Reset lock
        
        # Periodic check for closer targets if NOT locked
        if not should_retarget and self.target and not self.locked_target:
            self.retarget_timer -= dt
            if self.retarget_timer <= 0:
                self.retarget_timer = 0.2 # Check 5 times a second
                
                # Check if there is a significantly closer target
                old_target = self.target
                self.find_target()
                # If target changed, great.
        
        # Reset nudged flag immediately after checking
        self.nudged = False
             
        if should_retarget:
            self.find_target()
            
        # DECISION: Attack or Move?
        self.pending_attack = False
        self.pending_move = pygame.math.Vector2(0, 0)
        self.pending_pushes = []
        
        if self.target:
            # Use edge-to-edge distance for range check
            dist = self.get_edge_distance(self.target)
            if dist <= self.range + 0.001: # Add epsilon
                if self.last_attack_time >= self.attack_cooldown:
                    self.pending_attack = True
            else:
                self.pending_move, self.pending_pushes = self.calculate_movement(dt)
        else:
            # Move towards enemy king tower if no target
            if self.team == "player":
                target_pos = self.game.king_tower_e.pos
            else:
                target_pos = self.game.king_tower_p.pos
            
            direction = target_pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize()
            self.pending_move = direction * self.speed * dt

    def update(self, dt):
        """Phase 2: Movement and State Update"""
        self.update_animation(dt)
        self.update_sprite() # Update sprite based on animation and direction
        if self.state == "deploying":
            self.deploy_timer -= dt
            if self.deploy_timer <= 0:
                self.state = "active"
                self.image.set_alpha(255)
            return

        self.last_attack_time += dt
        self.is_moving = False # Reset moving state
        
        # Execute Pending Actions
        if self.pending_attack:
            self.attack()
            self.last_attack_time = 0
            self.locked_target = True # LOCK ON after attacking!
        
        # Apply Pushes to OTHERS
        for unit, push_vector in self.pending_pushes:
            if unit.alive():
                unit.pos += push_vector
                unit.rect.center = unit.pos
                unit.nudged = True
        
        if self.pending_move.length_squared() > 0:
            self.pos += self.pending_move
            self.rect.center = self.pos
            self.is_moving = True
            
            # Update facing direction based on movement
            if self.pending_move.length() > 0:
                self.update_facing_direction(self.pending_move.normalize())

    def update_facing_direction(self, direction_vector):
        if direction_vector.length() > 0:
            # atan2 returns angle from X axis (Right=0, Down=90, Left=180/-180, Up=-90)
            angle = math.degrees(math.atan2(direction_vector.y, direction_vector.x))
            self.facing_angle = angle % 360
            
            # Legacy direction for compatibility or logic
            if abs(direction_vector.x) > abs(direction_vector.y):
                self.facing_direction = "side"
                self.flip_x = direction_vector.x < 0
            elif direction_vector.y < 0:
                self.facing_direction = "up"
            else:
                self.facing_direction = "down"
            
    def find_target(self):
        closest_dist = 200 # Aggro range
        self.target = None
        
        # Determine potential targets based on preference
        targets = []
        if self.target_preference == "building":
            # Only target towers (and buildings if we had them)
            targets = list(self.game.towers)
            # Buildings usually have infinite aggro range (map wide), 
            # but let's stick to aggro range first, then fallback to global
        else:
            # Default: Prioritize units, then towers
            targets = list(self.game.units) + list(self.game.towers)
            
        # Sort targets deterministically by network_id
        targets.sort(key=lambda t: str(getattr(t, 'network_id', '') or id(t)))
        
        closest = None
            
        for target in targets:
            if target.team != self.team and target.alive():
                # Check targeting compatibility
                if not self.can_target(target):
                    continue
                    
                # Use edge-to-edge distance for aggro check
                dist = self.get_edge_distance(target)
                
                if dist < closest_dist:
                    closest_dist = dist
                    closest = target # Assign to the temporary variable
        
        if closest:
            self.target = closest
        else:
            self.target = None # Corrected from Nonetarget
        
        # If no unit/tower in aggro range, target nearest tower globally
        if not self.target:
            closest_dist = float('inf')
            # Sort towers deterministically
            sorted_towers = sorted(self.game.towers, key=lambda t: getattr(t, 'network_id', '') or id(t))
            for target in sorted_towers:
                if target.team != self.team and target.alive():
                    if not self.can_target(target):
                        continue
                    # Use edge-to-edge distance
                    dist = self.get_edge_distance(target)
                    if dist < closest_dist:
                        closest_dist = dist
                        self.target = target

    def can_target(self, target):
        """Check if this unit can target the given entity based on air/ground rules"""
        target_unit_type = getattr(target, 'unit_type', 'ground')
        
        if self.target_type == "both":
            return True
        elif self.target_type == "ground":
            return target_unit_type == "ground"
        elif self.target_type == "air":
            return target_unit_type == "air"
        return True

    def calculate_movement(self, dt):
        if not self.target:
            return pygame.math.Vector2(0, 0)
            
        target_pos = self.target.pos
        
        # If target is a tower (Rect), aim for the closest point on the rect, not the center
        if getattr(self.target, 'hitbox_type', 'circle') == "rect":
            target_pos = self.target.get_closest_point(self.pos)
        
        # Pathfinding: Check if we need to cross the river
        river_rect = self.game.arena.river_rect
        river_y = river_rect.centery
        
        # Check if on opposite sides
        if (self.pos.y < river_y and target_pos.y > river_y) or \
           (self.pos.y > river_y and target_pos.y < river_y):
            
            # Find nearest bridge
            bridge_y = river_y
            # Use tile-based coordinates for robustness
            left_bridge_x = GRID_MARGIN_X + LANE_LEFT_COL * TILE_SIZE + TILE_SIZE // 2
            right_bridge_x = GRID_MARGIN_X + LANE_RIGHT_COL * TILE_SIZE + TILE_SIZE // 2
            
            dist_left = abs(self.pos.x - left_bridge_x)
            dist_right = abs(self.pos.x - right_bridge_x)
            
            # Tie-breaking for symmetry
            if abs(dist_left - dist_right) < 1.0: # Roughly equal
                # Player team prefers Right, Enemy team prefers Left
                # This ensures that mirrored units pick the SAME physical bridge
                # (Host Right = Client Left)
                if self.team == "player":
                    bridge_target = pygame.math.Vector2(right_bridge_x, bridge_y)
                else:
                    bridge_target = pygame.math.Vector2(left_bridge_x, bridge_y)
            elif dist_left < dist_right:
                bridge_target = pygame.math.Vector2(left_bridge_x, bridge_y)
            else:
                bridge_target = pygame.math.Vector2(right_bridge_x, bridge_y)
            
            bridge_x = bridge_target.x
            
            # Target the bridge at the river's vertical center
            bridge_target = pygame.math.Vector2(bridge_x, river_rect.centery)
            
            # Check if we are aligned with the bridge (X-axis)
            on_bridge_x = abs(self.pos.x - bridge_x) < (3 * TILE_SIZE / 2) # Within bridge width
            
            if not on_bridge_x:
                # Move towards bridge X, but stay clear of river Y
                if self.pos.y > river_rect.centery: # Below river
                    target_pos = pygame.math.Vector2(bridge_x, river_rect.bottom + 10)
                else: # Above river
                    target_pos = pygame.math.Vector2(bridge_x, river_rect.top - 10)
            else:
                # We are aligned with bridge X, now we can cross
                target_pos = bridge_target
            
            # If we are close to the bridge center (on it), we can proceed to final target?
            # Only if we are past the river or deep enough on the bridge.
            # If distance to bridge center is small (e.g. < river_height/2), we are on it.
            if self.pos.distance_to(bridge_target) < river_rect.height / 2 + 5:
                # We are on the bridge!
                # Now we can aim for the final target, BUT we must stay on the bridge until we clear the river.
                # If we aim for final target now, we might walk off the side of the bridge.
                
                # Determine which way we want to go based on our FINAL target
                final_target_y = self.target.pos.y if self.target else (0 if self.team == "player" else self.game.playable_height)
                
                # So, if we are on the bridge, we should aim for the EXIT of the bridge.
                if final_target_y < river_rect.centery: # Target is ABOVE river (Player going up)
                    target_pos = pygame.math.Vector2(bridge_x, river_rect.top - 10)
                else: # Target is BELOW river (Enemy going down)
                    target_pos = pygame.math.Vector2(bridge_x, river_rect.bottom + 10)
                    
                # If we are already close to the exit, THEN we can aim for the real target.
                if self.pos.distance_to(target_pos) < 10:
                    target_pos = self.target.pos # Restore original target

        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        
        # Pushing Mechanic
        pushes = []
        separation = pygame.math.Vector2(0, 0)
        
        # 1. Unit Collision
        # Iterate deterministically to ensure sync
        # Sort by network_id to ensure consistent order across clients
        sorted_units = sorted(self.game.units, key=lambda u: getattr(u, 'network_id', '') or id(u))
        
        for unit in sorted_units:
            if unit != self and unit.alive():
                # Ground units collide with ground units (Hard Collision)
                if self.unit_type == "ground" and getattr(unit, 'unit_type', 'ground') == "ground":
                    collision_radius = (self.size / 2) + (getattr(unit, 'size', 20) / 2)
                    dist = self.pos.distance_to(unit.pos)
                    
                    if dist < collision_radius:
                        self.nudged = True # Collision is a nudge
                        
                        if dist < 0.001:
                            # Exact overlap, push in random direction or fixed direction based on ID
                            # Use IDs to be deterministic
                            my_id = getattr(self, 'network_id', '') or str(id(self))
                            other_id = getattr(unit, 'network_id', '') or str(id(unit))
                            if my_id > other_id:
                                normal = pygame.math.Vector2(1, 0)
                            else:
                                normal = pygame.math.Vector2(-1, 0)
                        else:
                            normal = self.pos - unit.pos
                            if normal.length() > 0:
                                normal = normal.normalize()
                            
                        # Slide: Remove velocity component towards unit
                        dot = direction.dot(normal)
                        
                        # Pushing Mechanic
                        is_pushing = False
                        if dot < 0:
                            # Check if we are hitting them squarely (centered)
                            # dot is direction.dot(normal). normal points FROM unit TO self.
                            # If we are moving towards unit, dot < 0.
                            # If we are hitting center (rear-ending), dot ~ -1.
                            is_centered = dot < PUSH_ALIGNMENT_THRESHOLD
                            
                            if is_centered:
                                other_dir = getattr(unit, 'last_move_dir', pygame.math.Vector2(0,0))
                                
                                # Check alignment (same direction)
                                is_aligned = False
                                if other_dir.length_squared() > 0.01:
                                    # If they are moving, must be moving roughly in the same direction
                                    if direction.dot(other_dir) > 0.5:
                                        is_aligned = True
                                else:
                                    # If they are stopped, we can push them if we are centered
                                    is_aligned = True
                                    
                                if is_aligned:
                                    if self.mass >= getattr(unit, 'mass', 10):
                                        # We are heavy enough to push
                                        is_pushing = True
                                    
                        if is_pushing:
                            # Push the other unit!
                            # push_vector = direction * self.speed * dt # Don't use full speed, use relative?
                            # Actually, just push them out of overlap or along direction
                            
                            overlap = collision_radius - dist
                            push_dir = direction
                            if push_dir.length() == 0:
                                push_dir = normal * -1 
                                
                            # Apply push
                            # Use PUSH_INTENSITY to control how "snappy" the push is
                            push_amount = overlap * PUSH_INTENSITY
                            
                            # Calculate push vector for the OTHER unit
                            push_vector = push_dir * (push_amount + 0.1)
                            
                            # Queue the push
                            pushes.append((unit, push_vector))
                            
                            self.nudged = True 
                        else:
                            # Standard Hard Collision (Slide/Stop)
                            if dot < 0:
                                direction = direction - normal * dot
                            
                            # Push out: Add strong outward component
                            direction += normal * 0.8 
                        
                        if direction.length() > 0:
                            direction = direction.normalize()
                                
                # Air units separate softly (Soft Collision)
                elif self.unit_type == "air" and getattr(unit, 'unit_type', 'ground') == "air":
                     dist = self.pos.distance_to(unit.pos)
                     if dist < 20: # Too close
                        if dist < 0.001:
                            # Exact overlap
                            my_id = getattr(self, 'network_id', '') or str(id(self))
                            other_id = getattr(unit, 'network_id', '') or str(id(unit))
                            if my_id > other_id:
                                diff = pygame.math.Vector2(1, 0)
                            else:
                                diff = pygame.math.Vector2(-1, 0)
                        else:
                            diff = self.pos - unit.pos
                            if diff.length() > 0:
                                diff = diff.normalize()
                        
                        separation += diff / (dist + 0.1) # Avoid div by zero

        if separation.length() > 0:
            if separation.length() > 0.5: # Significant separation force implies nudging
                self.nudged = True
            direction += separation * 1.5 # Weight separation
            if direction.length() > 0:
                direction = direction.normalize()

        # 2. Tower Collision (Hard Constraint / Slide)
        # Iterate deterministically
        sorted_towers = sorted(self.game.towers, key=lambda t: getattr(t, 'network_id', '') or id(t))
        
        for tower in sorted_towers:
            if tower.alive():
                # Tower collision radius (approx size/2) + Unit radius (approx 10)
                collision_radius = (tower.size / 2) + 10
                dist = self.pos.distance_to(tower.pos)
                
                if dist < collision_radius:
                    self.nudged = True # Collision with tower is a nudge
                    normal = self.pos - tower.pos
                    if normal.length() > 0:
                        normal = normal.normalize()
                        
                        # Slide: Remove velocity component towards tower
                        dot = direction.dot(normal)
                        if dot < 0:
                            direction = direction - normal * dot
                        
                        # Push out: Add strong outward component to ensure we don't stay inside
                        direction += normal * 0.5
                        
                        if direction.length() > 0:
                            direction = direction.normalize()
        
        return direction * self.speed * dt, pushes

    def attack(self):
        if self.target:
            self.is_attacking = True
            self.attack_anim_timer = 0
            assets.play_sound("attack")
            
            # Melee units hit instantly with custom effects
            if self.range < 60: # Melee
                self.target.take_damage(self.damage)
                
                
                # Custom melee hit effects based on unit type
                if self.unit_type_name == "knight":
                    # Knight: Blue/yellow slash effect
                    slash_color = (100, 150, 255) if self.team == "player" else (255, 100, 100)
                    particle_system.create_explosion(self.target.pos.x, self.target.pos.y, 
                                                     slash_color, count=8)
                    # Sword clang particles
                    for _ in range(4):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(40, 80)
                        rad = math.radians(angle)
                        vel_x = math.cos(rad) * speed
                        vel_y = math.sin(rad) * speed
                        from game.entities.particles import Particle
                        p = Particle(self.target.pos.x, self.target.pos.y, 
                                   (255, 255, 150), (vel_x, vel_y), 0.3, 3, decay_rate=10)
                        particle_system.particles.append(p)
                        
                elif self.unit_type_name == "skeleton_army":
                    # Skeleton: Bone fragments
                    for _ in range(6):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(30, 70)
                        rad = math.radians(angle)
                        vel_x = math.cos(rad) * speed
                        vel_y = math.sin(rad) * speed
                        from game.entities.particles import Particle
                        p = Particle(self.target.pos.x, self.target.pos.y, 
                                   (240, 240, 230), (vel_x, vel_y), 0.4, 2, decay_rate=5)
                        particle_system.particles.append(p)
                else:
                    # Default melee effect
                    particle_system.create_explosion(self.target.pos.x, self.target.pos.y, 
                                                     RED if self.team == "player" else BLUE, count=5)
            else:
                # Ranged units spawn custom projectiles
                if self.unit_type_name == "archer":
                    ArrowProjectile(self.game, self.pos.x, self.pos.y, 
                                   self.target, self.damage, self.team)
                elif self.unit_type_name == "baby_dragon":
                    FireballProjectile(self.game, self.pos.x, self.pos.y, 
                                      self.target, self.damage, self.team)
                elif self.unit_type_name == "minions":
                    SpearProjectile(self.game, self.pos.x, self.pos.y, 
                                   self.target, self.damage, self.team)
                else:
                    # Default projectile
                    Projectile(self.game, self.pos.x, self.pos.y, 
                             self.target, self.damage, self.team)
                             
            self.last_attack_time = 0

class FlyingUnit(Unit):
    """Flying units that can fly over the river without needing bridges"""
    
    def __init__(self, game, x, y, type, team, network_id=None):
        super().__init__(game, x, y, type, team, network_id)
        # Flying units always have unit_type "air"
        self.unit_type = "air"
        
    def move_towards_target(self, dt):
        """Override to fly directly without river pathfinding"""
        if not self.target:
            return
            
        target_pos = self.target.pos
        
        # No river pathfinding - fly directly!
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        
        # Collision/Separation (still avoid other units)
        separation = pygame.math.Vector2(0, 0)
        for unit in self.game.units:
            if unit != self and unit.alive():
                dist = self.pos.distance_to(unit.pos)
                if dist < 20: # Too close
                    diff = self.pos - unit.pos
                    if diff.length() > 0:
                        diff = diff.normalize()
                        separation += diff / dist # Weighted by distance
        
        if separation.length() > 0:
            direction += separation * 1.5 # Weight separation
            if direction.length() > 0:
                direction = direction.normalize()
        
        self.pos += direction * self.speed * dt
        self.rect.center = self.pos
        self.is_moving = True
        
    def draw(self, surface):
        """Add shadow effect for flying units"""
        # Draw shadow
        shadow_offset = 5
        shadow_pos = (self.rect.centerx + shadow_offset, self.rect.centery + shadow_offset)
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, 60))
        surface.blit(shadow_surface, (shadow_pos[0] - self.rect.width//2, shadow_pos[1] - self.rect.height//2))
        
        # Draw unit normally
        draw_pos = self.rect.topleft + self.anim_offset
        surface.blit(self.image, draw_pos)
        self.draw_health_bar(surface, draw_pos)


class Spell(pygame.sprite.Sprite):
    """Base class for spell cards"""
    
    def __init__(self, game, x, y, spell_type, team):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.team = team
        self.spell_type = spell_type
        
        stats = SPELL_STATS[spell_type]
        self.damage = stats["damage"]
        self.radius = stats["radius"]
        self.duration = stats["duration"]
        self.color = stats["color"]
        
        self.pos = pygame.math.Vector2(x, y)
        self.timer = 0
        self.has_dealt_damage = False
        
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
    def deal_damage(self):
        """Deal damage to all enemy entities in radius"""
        if self.has_dealt_damage:
            return
            
        self.has_dealt_damage = True
        
        # Check all units
        for unit in self.game.units:
            if unit.team != self.team:
                dist = self.pos.distance_to(unit.pos)
                if dist <= self.radius:
                    unit.take_damage(self.damage)
                    particle_system.create_explosion(unit.rect.centerx, unit.rect.centery, RED, count=10)
        
        # Check all towers
        for tower in self.game.towers:
            if tower.team != self.team:
                dist = self.pos.distance_to(tower.pos)
                if dist <= self.radius:
                    tower.take_damage(self.damage)
                    particle_system.create_explosion(tower.rect.centerx, tower.rect.centery, RED, count=10)


class FireballSpell(Spell):
    """Fireball: Flies from King Tower to target, then explodes"""
    
    def __init__(self, game, x, y, team):
        super().__init__(game, x, y, "fireball", team)
        
        # Start position (King Tower)
        if team == "player":
            start_pos = game.king_tower_p.rect.center
        else:
            start_pos = game.king_tower_e.rect.center
            
        self.current_pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(x, y)
        
        # Flight physics
        self.total_dist = self.current_pos.distance_to(self.target_pos)
        self.speed = 600
        self.flight_time = self.total_dist / self.speed
        self.flight_timer = 0
        
        # Visuals
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 140, 0), (15, 15), 15)
        pygame.draw.circle(self.image, (255, 200, 50), (15, 15), 10)
        self.rect = self.image.get_rect(center=start_pos)
        
        self.state = "flying" # flying, exploding
        self.explosion_timer = 0
        self.explosion_duration = 0.5
        
        assets.play_sound("spell") # Launch sound

    def update(self, dt):
        if self.state == "flying":
            self.flight_timer += dt
            progress = self.flight_timer / self.flight_time
            
            if progress >= 1.0:
                self.state = "exploding"
                self.deal_damage()
                assets.play_sound("hit") # Explosion sound
                
                # Create big explosion particles
                particle_system.create_explosion(self.target_pos.x, self.target_pos.y, (255, 100, 0), count=30)
                return
                
            # Parabolic arc height
            height = math.sin(progress * math.pi) * 100
            
            # Lerp position
            self.current_pos = self.current_pos.lerp(self.target_pos, min(progress + dt * 2, 1.0)) # slightly faster lerp? no, just use progress
            # Actually lerp properly
            start = pygame.math.Vector2(self.game.king_tower_p.rect.center if self.team == "player" else self.game.king_tower_e.rect.center)
            flat_pos = start.lerp(self.target_pos, progress)
            
            # Apply height to Y (visual only) - wait, Y is down. So subtract height.
            draw_pos = pygame.math.Vector2(flat_pos.x, flat_pos.y - height)
            
            self.rect.center = draw_pos
            
            # Trail particles
            if random.random() < 0.5:
                particle_system.create_projectile_trail(draw_pos.x, draw_pos.y, (255, 100, 0))
                
        elif self.state == "exploding":
            self.explosion_timer += dt
            
            # Expanding explosion ring
            radius = int(self.radius * (self.explosion_timer / self.explosion_duration))
            self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (*self.color, 128), (radius, radius), radius)
            self.rect = self.image.get_rect(center=self.target_pos)
            
            if self.explosion_timer >= self.explosion_duration:
                self.kill()


class ArrowsSpell(Spell):
    """Arrows: Volley of arrows raining down"""
    
    def __init__(self, game, x, y, team):
        super().__init__(game, x, y, "arrows", team)
        
        self.state = "raining"
        self.rain_duration = 0.4
        self.timer = 0
        
        # Create multiple arrow particles
        self.arrows = []
        for _ in range(20):
            # Random offset within radius
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, self.radius)
            off_x = math.cos(angle) * r
            off_y = math.sin(angle) * r
            
            # Start high up
            start_x = x + off_x + random.uniform(-20, 20)
            start_y = y + off_y - 300 # Start 300px above
            
            target_x = x + off_x
            target_y = y + off_y
            
            delay = random.uniform(0, 0.2)
            self.arrows.append({
                "start": pygame.math.Vector2(start_x, start_y),
                "target": pygame.math.Vector2(target_x, target_y),
                "current": pygame.math.Vector2(start_x, start_y),
                "delay": delay,
                "hit": False
            })
            
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        
        assets.play_sound("spell")

    def update(self, dt):
        self.timer += dt
        
        self.image.fill((0,0,0,0)) # Clear
        
        all_hit = True
        
        for arrow in self.arrows:
            if arrow["delay"] > 0:
                arrow["delay"] -= dt
                all_hit = False
                continue
                
            if arrow["hit"]:
                continue
                
            all_hit = False
            
            # Move arrow
            speed = 800
            direction = (arrow["target"] - arrow["current"])
            dist = direction.length()
            
            if dist < speed * dt:
                arrow["current"] = arrow["target"]
                arrow["hit"] = True
                # Small hit effect
                particle_system.create_explosion(arrow["target"].x, arrow["target"].y, (200, 200, 200), count=3)
            else:
                arrow["current"] += direction.normalize() * speed * dt
                
            # Draw arrow
            start = arrow["current"]
            end = start - direction.normalize() * 20
            pygame.draw.line(self.image, (160, 120, 80), start, end, 2)
            pygame.draw.line(self.image, (200, 200, 220), start, start - direction.normalize() * 5, 3) # Head
            
        if self.timer > 0.2 and not self.has_dealt_damage:
            self.deal_damage()
            assets.play_sound("hit")
            
        if all_hit and self.timer > self.rain_duration:
            self.kill()


class ZapSpell(Spell):
    """Zap: Instant lightning strike"""
    
    def __init__(self, game, x, y, team, network_id=None):
        super().__init__(game, x, y, "zap", team)
        self.network_id = network_id or str(uuid.uuid4()) # Ensure ID exists
        self.duration = 0.3
        self.deal_damage()
        assets.play_sound("spell")
        
        # Create lightning particles
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, self.radius)
            tx = x + math.cos(angle) * r
            ty = y + math.sin(angle) * r
            
            # Lightning bolt from sky
            start_y = y - 200
            points = []
            curr_x, curr_y = tx, start_y
            steps = 5
            for i in range(steps):
                points.append((curr_x, curr_y))
                curr_y += (ty - start_y) / steps
                curr_x += random.uniform(-10, 10)
            points.append((tx, ty))
            
            self.lightning_points = points # Store for drawing? No, just draw once or use particles
            
            # Actually, let's just use the update loop to draw a flash
            
    def update(self, dt):
        self.timer += dt
        
        # Flash effect
        if self.timer < 0.1:
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 240, 255, 100), (self.radius, self.radius), self.radius)
            self.rect = self.image.get_rect(center=self.pos)
            
            # Draw random bolts
            center = (self.radius, self.radius)
            for _ in range(3):
                angle = random.uniform(0, 2 * math.pi)
                end_x = self.radius + math.cos(angle) * self.radius
                end_y = self.radius + math.sin(angle) * self.radius
                pygame.draw.line(self.image, (100, 200, 255), center, (end_x, end_y), 2)
                
        elif self.timer >= self.duration:
            self.kill()

class FlyingUnit(Unit):
    def __init__(self, game, x, y, type, team, network_id=None):
        super().__init__(game, x, y, type, team, network_id)
        self.height = 50 # Flying height
        self.shadow_offset = 10
        
    def move_towards_target(self, dt):
        """Override to fly directly without river pathfinding"""
        if not self.target:
            return
            
        target_pos = self.target.pos
        
        # No river pathfinding - fly directly!
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        
        # Collision/Separation (still avoid other units)
        separation = pygame.math.Vector2(0, 0)
        # Sort units for deterministic iteration
        sorted_units = sorted(self.game.units, key=lambda u: getattr(u, 'network_id', '') or id(u))
        for unit in sorted_units:
            if unit != self and unit.alive() and unit.unit_type == "air":
                dist = self.pos.distance_to(unit.pos)
                if dist < 20: # Too close
                    diff = self.pos - unit.pos
                    if diff.length() > 0:
                        diff = diff.normalize()
                        separation += diff / dist # Weighted by distance
        


        if separation.length() > 0:
            direction += separation * 1.5 # Weight separation
            if direction.length() > 0:
                direction = direction.normalize()
        
        self.pos += direction * self.speed * dt
        self.rect.center = self.pos
        self.is_moving = True

