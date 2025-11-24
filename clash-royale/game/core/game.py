import pygame
from game.settings import *
from game.entities.sprites import *
from game.assets import assets
from game.entities.particles import particle_system
from game.entities.geometric_sprites import geometric_renderer

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.all_sprites = pygame.sprite.Group()
        self.towers = pygame.sprite.Group()
        self.units = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        
        self.elixir = 5
        self.elixir_timer = 0
        
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.hud_height = 180
        self.playable_height = SCREEN_HEIGHT - self.hud_height
        
        self.setup_arena()
        
        # Deck System
        # 8 cards: 4 Knights, 4 Archers for now
        self.deck = ["knight", "archer", "knight", "archer", "knight", "archer", "knight", "archer"]
        import random
        random.shuffle(self.deck)
        
        self.hand = []
        for _ in range(4):
            self.hand.append(self.deck.pop(0))
            
        self.next_card = self.deck.pop(0)
        
        self.card_rects = {}
        self.dragging_card = None # Index in hand
        self.drag_pos = None
        
        self.enemy_spawn_timer = 0

    def setup_arena(self):
        # Setup towers
        # Player (Bottom)
        # Adjust positions to fit in playable area
        self.king_tower_p = Tower(self, SCREEN_WIDTH//2, self.playable_height - 80, "king", "player")
        self.left_tower_p = Tower(self, 80, self.playable_height - 150, "princess", "player")
        self.right_tower_p = Tower(self, SCREEN_WIDTH - 80, self.playable_height - 150, "princess", "player")
        
        # Enemy (Top)
        self.king_tower_e = Tower(self, SCREEN_WIDTH//2, 80, "king", "enemy")
        self.left_tower_e = Tower(self, 80, 150, "princess", "enemy")
        self.right_tower_e = Tower(self, SCREEN_WIDTH - 80, 150, "princess", "enemy")
        
        self.game_over = False
        self.winner = None

    def get_mouse_pos(self):
        x, y = pygame.mouse.get_pos()
        return (int((x - self.offset_x) / self.scale), int((y - self.offset_y) / self.scale))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.game_over:
                self.reset_game()
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.get_mouse_pos()
            if event.button == 1: # Left click
                # Check if clicked on a card
                for i, rect in self.card_rects.items():
                    if rect.collidepoint(pos):
                        self.dragging_card = i # Store index
                        self.drag_pos = pos
                        return

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_card is not None:
                self.drag_pos = self.get_mouse_pos()
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_card is not None:
                pos = self.get_mouse_pos()
                
                # Check valid spawn
                valid_spawn = False
                for rect in self.get_valid_spawn_rects():
                    if rect.collidepoint(pos):
                        valid_spawn = True
                        break
                
                if valid_spawn:
                    card_name = self.hand[self.dragging_card]
                    cost = UNIT_STATS[card_name]["cost"]
                    if self.elixir >= cost:
                        Unit(self, pos[0], pos[1], card_name, "player")
                        assets.play_sound("spawn")
                        particle_system.create_spawn_poof(pos[0], pos[1])
                        self.elixir -= cost
                        
                        # Cycle card
                        self.hand.pop(self.dragging_card)
                        self.hand.insert(self.dragging_card, self.next_card)
                        self.deck.append(card_name)
                        self.next_card = self.deck.pop(0)
                
                self.dragging_card = None
                self.drag_pos = None

    def get_valid_spawn_rects(self):
        rects = []
        # Default: Player side
        rects.append(pygame.Rect(0, self.playable_height//2, SCREEN_WIDTH, self.playable_height//2))
        
        # Pocket Logic
        # If left enemy tower dead, add left pocket
        if not self.left_tower_e.alive():
            rects.append(pygame.Rect(0, 0, SCREEN_WIDTH//2, self.playable_height//2))
            
        # If right enemy tower dead, add right pocket
        if not self.right_tower_e.alive():
            rects.append(pygame.Rect(SCREEN_WIDTH//2, 0, SCREEN_WIDTH//2, self.playable_height//2))
            
        return rects

    def update(self, dt):
        if self.game_over:
            return

        # Elixir regeneration
        self.elixir_timer += dt
        if self.elixir_timer >= ELIXIR_REGEN_RATE:
            if self.elixir < MAX_ELIXIR:
                self.elixir += 1
            self.elixir_timer = 0
            
        # Enemy Spawner (Simple AI)
        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= 5.0: # Spawn every 5 seconds
            import random
            lane = random.choice([80, SCREEN_WIDTH - 80])
            unit_type = random.choice(["knight", "archer"])
            Unit(self, lane, 250, unit_type, "enemy")
            self.enemy_spawn_timer = 0
            
        self.all_sprites.update(dt)
        particle_system.update(dt)
        
        # Check Princess Towers to activate King
        if not self.left_tower_p.alive() or not self.right_tower_p.alive():
            self.king_tower_p.active = True
        if not self.left_tower_e.alive() or not self.right_tower_e.alive():
            self.king_tower_e.active = True
            
        self.check_game_over()
        
    def check_game_over(self):
        if self.king_tower_p.health <= 0:
            self.game_over = True
            self.winner = "Enemy"
            assets.play_sound("game_over")
        elif self.king_tower_e.health <= 0:
            self.game_over = True
            self.winner = "Player"
            assets.play_sound("game_over")
            
    def reset_game(self):
        self.all_sprites.empty()
        self.towers.empty()
        self.units.empty()
        self.projectiles.empty()
        self.elixir = 5
        self.setup_arena()
        self.game_over = False
        self.winner = None
        
        # Reset Deck
        self.deck = ["knight", "archer", "knight", "archer", "knight", "archer", "knight", "archer"]
        import random
        random.shuffle(self.deck)
        self.hand = []
        for _ in range(4):
            self.hand.append(self.deck.pop(0))
        self.next_card = self.deck.pop(0)
        
    def draw(self):
        # Draw Arena Background (River, Bridges)
        river_y = self.playable_height // 2
        pygame.draw.rect(self.screen, RIVER_BLUE, (0, river_y - 20, SCREEN_WIDTH, 40))
        pygame.draw.rect(self.screen, BRIDGE_BROWN, (60, river_y - 25, 40, 50)) # Left Bridge
        pygame.draw.rect(self.screen, BRIDGE_BROWN, (SCREEN_WIDTH - 100, river_y - 25, 40, 50)) # Right Bridge
        
        # Draw Spawn Zones if dragging
        if self.dragging_card is not None:
            for rect in self.get_valid_spawn_rects():
                s = pygame.Surface((rect.width, rect.height))
                s.set_alpha(50)
                s.fill(GREEN)
                self.screen.blit(s, (rect.x, rect.y))
        
        self.all_sprites.draw(self.screen)
        particle_system.draw(self.screen)
        
        for sprite in self.all_sprites:
            if hasattr(sprite, 'draw_health_bar'):
                sprite.draw_health_bar(self.screen)
        
        # Draw HUD
        self.draw_hud()
        
    def draw_hud(self):
        # Background for HUD
        hud_rect = pygame.Rect(0, self.playable_height, SCREEN_WIDTH, self.hud_height)
        pygame.draw.rect(self.screen, (50, 50, 50), hud_rect)
        pygame.draw.line(self.screen, BLACK, (0, self.playable_height), (SCREEN_WIDTH, self.playable_height), 3)
        
        # Elixir Bar
        bar_width = 300
        bar_height = 20
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = self.playable_height + 10
        
        # Background
        pygame.draw.rect(self.screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        
        # Fill
        fill_width = int((self.elixir / MAX_ELIXIR) * bar_width)
        pygame.draw.rect(self.screen, (200, 0, 255), (bar_x, bar_y, fill_width, bar_height), border_radius=10)
        
        # Segments
        for i in range(1, MAX_ELIXIR):
            x = bar_x + (i / MAX_ELIXIR) * bar_width
            pygame.draw.line(self.screen, (100, 100, 100), (x, bar_y), (x, bar_y + bar_height))
            
        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)
        
        # Text
        font = pygame.font.SysFont("Arial", 16, bold=True)
        text = font.render(f"{int(self.elixir)}", True, WHITE)
        self.screen.blit(text, (bar_x - 25, bar_y))
        
        # Draw Hand
        self.card_rects = {}
        card_width = 70
        card_height = 90
        card_spacing = 15
        total_width = 4 * card_width + 3 * card_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        card_y = bar_y + 35
        
        for i, card_name in enumerate(self.hand):
            rect = pygame.Rect(start_x + i * (card_width + card_spacing), card_y, card_width, card_height)
            
            # If dragging this card, draw it faded
            if self.dragging_card == i:
                s = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                s.fill((200, 200, 200, 50))
                self.screen.blit(s, rect)
                pygame.draw.rect(self.screen, LIGHT_GREY, rect, 2, border_radius=5)
            else:
                self._draw_card_icon(rect, card_name)
                
                # Check affordability
                cost = UNIT_STATS.get(card_name, {}).get("cost", 0)
                if card_name in SPELL_STATS:
                    cost = SPELL_STATS[card_name]["cost"]
                    
                if self.elixir < cost:
                    # Darken if can't afford
                    s = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 150))
                    self.screen.blit(s, rect)
            
            self.card_rects[i] = rect
            
        # Next Card
        next_rect = pygame.Rect(SCREEN_WIDTH - 60, card_y + 10, 40, 55)
        
        # Label above
        label_font = pygame.font.SysFont("Arial", 12)
        label_text = label_font.render("Next", True, WHITE)
        label_rect = label_text.get_rect(center=(next_rect.centerx, next_rect.y - 10))
        self.screen.blit(label_text, label_rect)
        
        if self.next_card:
            self._draw_card_icon(next_rect, self.next_card, small=True)

    def _draw_card_icon(self, rect, card_name, small=False):
        is_spell = card_name in SPELL_STATS
        
        # Background
        if is_spell:
            bg_color = (180, 100, 200)
            border_color = (140, 60, 160)
        else:
            bg_color = (255, 220, 150)
            border_color = (200, 170, 100)
            
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
        
        # Icon
        if not is_spell:
            icon_size = (rect.width - 8, rect.height - 25) if not small else (rect.width - 4, rect.height - 4)
            icon = geometric_renderer.get_card_icon(card_name, icon_size)
            icon_x = rect.x + (rect.width - icon.get_width()) // 2
            icon_y = rect.y + 5
            if small:
                icon_y = rect.y + (rect.height - icon.get_height()) // 2
            self.screen.blit(icon, (icon_x, icon_y))
            
        # Cost (if not small)
        if not small:
            cost = SPELL_STATS[card_name]["cost"] if is_spell else UNIT_STATS[card_name]["cost"]
            pygame.draw.circle(self.screen, (255, 100, 200), (rect.right - 10, rect.y + 10), 8)
            pygame.draw.circle(self.screen, BLACK, (rect.right - 10, rect.y + 10), 8, 1)
            
            font = pygame.font.SysFont("Arial", 12, bold=True)
            text = font.render(str(cost), True, WHITE)
            self.screen.blit(text, (rect.right - 10 - text.get_width()//2, rect.y + 3))
            
            # Name
            name_parts = card_name.split('_')
            display_name = name_parts[0][:4].upper()
            name_font = pygame.font.SysFont("Arial", 10, bold=True)
            name_text = name_font.render(display_name, True, BLACK)
            self.screen.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.bottom - 15))

        if self.game_over:
            # Dim screen
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(128)
            s.fill(BLACK)
            self.screen.blit(s, (0,0))
            
            font_big = pygame.font.SysFont("Arial", 64)
            text = font_big.render(f"{self.winner} Wins!", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(text, rect)
            
            font_small = pygame.font.SysFont("Arial", 32)
            text_restart = font_small.render("Press R to Restart", True, WHITE)
            rect_restart = text_restart.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            self.screen.blit(text_restart, rect_restart)
            
        # Draw Dragged Card
        if self.dragging_card is not None and self.drag_pos:
            card_name = self.hand[self.dragging_card]
            color = UNIT_STATS[card_name]["color"]
            pygame.draw.circle(self.screen, color, self.drag_pos, 10)
            # Draw range circle
            range_val = UNIT_STATS[card_name]["range"]
            pygame.draw.circle(self.screen, WHITE, self.drag_pos, range_val, 1)
