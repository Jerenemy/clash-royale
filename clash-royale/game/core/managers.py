import pygame
from game.settings import *
from game.models import Player
from game.core.registry import CardRegistry
from game.core.card import UnitCard, SpellCard
from game.entities.sprites import Unit, Tower, FlyingUnit, Spell
from game.assets import assets

class BattleManager:
    def __init__(self, engine, practice_mode=False):
        self.engine = engine
        self.screen = engine.virtual_surface
        self.practice_mode = practice_mode
        self.enemy_spawn_timer = 0
        
        # Sprite Groups
        self.all_sprites = pygame.sprite.Group()
        self.towers = pygame.sprite.Group()
        self.units = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        
        # Players - Load player deck from file
        from game.utils import load_deck
        player_deck = load_deck()
        enemy_deck = ["knight", "archer", "knight", "archer", "knight", "archer", "knight", "archer"]
        self.player = Player("player", player_deck)
        self.enemy = Player("enemy", enemy_deck)
        
        # Display settings
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.hud_height = 180
        self.playable_height = SCREEN_HEIGHT - self.hud_height
        
        # Arena System
        from game.core.arena import Arena
        self.arena = Arena(self)
        
        self.setup_arena()
        
        self.game_over = False
        self.winner = None
        
        # UI State
        self.card_rects = {}
        self.calculate_card_rects()
        self.selected_card_idx = None # Index in hand of selected card
        self.dragging_card_idx = None # Index in hand of card being dragged
        self.drag_pos = None
        
        # Tick-based Synchronization
        self.tick = 0
        self.action_queue = [] # List of (target_tick, action_type, data)
        self.latency_buffer = 10 # Ticks (approx 160ms at 60FPS)
        
    def calculate_card_rects(self):
        """
        Pre-calculate card positions based on settings.
        Layout: [Next/Emote Column] [Deck Area]
        """
        self.card_rects = {}
        
        # Dimensions
        card_w = CARD_WIDTH
        card_h = CARD_HEIGHT
        spacing = 10
        
        # Left Column (Next + Emote)
        # Positioned on the left side
        left_col_x = 10
        hud_top = self.playable_height
        
        # Emote Button (Top of left column)
        self.emote_button_rect = pygame.Rect(left_col_x, hud_top + 10, 50, 40)
        
        # Next Card (Directly under Emote Button)
        # "Right under" the emote button
        # Make it smaller than normal cards
        next_w = 50
        next_h = 70
        self.next_card_rect = pygame.Rect(left_col_x, self.emote_button_rect.bottom + 10, next_w, next_h)
        
        # Deck Area (Right of Left Column)
        # "Deck hand should be aligned right" -> To the right of the next/emote
        deck_start_x = left_col_x + 50 + 20 # 20px gap
        
        # Elixir Bar (Bottom of Deck Area)
        # User said "deck and elixir bar in a box"
        # Let's put Elixir at the bottom
        elixir_h = 20
        elixir_y = SCREEN_HEIGHT - elixir_h - 10
        
        # Deck Y
        # Above Elixir
        deck_y = elixir_y - card_h - 10
        
        # Calculate Deck Width for centering or filling
        # 4 cards
        total_deck_width = 4 * card_w + 3 * spacing
        
        # If we want to align it right, we can push it to the right edge?
        # Or just place it after the left column.
        # Let's place it after the left column but maybe centered in the remaining space?
        # Remaining width = SCREEN_WIDTH - deck_start_x
        # Center of remaining: deck_start_x + (Remaining - DeckWidth) // 2
        remaining_w = SCREEN_WIDTH - deck_start_x
        if remaining_w > total_deck_width:
            deck_x = deck_start_x + (remaining_w - total_deck_width) // 2
        else:
            deck_x = deck_start_x
            
        # Elixir Bar Rect (Matches Deck Width)
        self.elixir_bar_rect = pygame.Rect(deck_x, elixir_y, total_deck_width, elixir_h)
        
        # Card Rects
        for i in range(4):
            rect = pygame.Rect(deck_x + i * (card_w + spacing), deck_y, card_w, card_h)
            self.card_rects[i] = rect
            
        # Emote Menu Rect (Covers the deck area)
        # Should cover cards + elixir? Or just cards? 
        # "take the place of the deck hand" -> Just cards usually.
        # But let's make it cover the whole "box" (cards + elixir space) for a clean look?
        # Or just the cards row. Let's do cards row + a bit of padding.
        self.emote_menu_rect = pygame.Rect(deck_x - 5, deck_y - 5, total_deck_width + 10, card_h + 10)
        
        # Re-init emote buttons to fit the new menu rect
        self._init_emote_buttons()

        self.enemy_spawn_timer = 0
        
        # Battle Timer
        self.battle_timer = 180.0 # 3 minutes
        self.sudden_death = False
        self.sd_start_towers_p = 0
        self.sd_start_towers_e = 0
        
        # Crown tracking
        self.player_crowns = 0
        self.enemy_crowns = 0
        
        # Callbacks
        self.on_card_played = None # function(card, pos, network_ids)
        
        # Emotes
        self.show_emotes = False

    def _init_emote_buttons(self):
        emotes = ["Good luck!", "Well played!", "Wow!", "Thanks!", "Good game!", "Oops"]
        cols = 2
        rows = 3
        
        # Fit buttons into emote_menu_rect
        padding = 10
        available_w = self.emote_menu_rect.width - (padding * 2)
        available_h = self.emote_menu_rect.height - (padding * 2)
        
        btn_w = (available_w - padding) // cols
        btn_h = (available_h - padding) // rows
        
        self.emote_buttons = []
        for i, text in enumerate(emotes):
            row = i // cols
            col = i % cols
            x = self.emote_menu_rect.x + padding + col * (btn_w + padding)
            y = self.emote_menu_rect.y + padding + row * (btn_h + padding)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.emote_buttons.append({"text": text, "rect": rect})
        
        # Re-setup arena with new height (if needed later)
        # self.towers.empty()
        # self.player.towers.empty()
        # self.enemy.towers.empty()
        # self.setup_arena()

    def setup_arena(self):
        # Setup towers
        # Calculate X positions based on Lanes
        left_lane_x = GRID_MARGIN_X + LANE_LEFT_COL * TILE_SIZE + TILE_SIZE // 2
        right_lane_x = GRID_MARGIN_X + LANE_RIGHT_COL * TILE_SIZE + TILE_SIZE // 2
        
        # Player (Bottom)
        # King Tower: One level (tile) offset from bottom edge
        king_y_p = GRID_MARGIN_Y + (GRID_HEIGHT - 2) * TILE_SIZE + TILE_SIZE // 2
        self.king_tower_p = Tower(self, SCREEN_WIDTH//2, king_y_p, "king", "player")
        
        # Princess Towers: Aligned with bridges (Lanes)
        # Row 17? (GRID_HEIGHT - 5)
        princess_y_p = GRID_MARGIN_Y + (GRID_HEIGHT - 5) * TILE_SIZE + TILE_SIZE // 2
        self.left_tower_p = Tower(self, left_lane_x, princess_y_p, "princess", "player")
        self.right_tower_p = Tower(self, right_lane_x, princess_y_p, "princess", "player")
        self.player.towers.add(self.king_tower_p, self.left_tower_p, self.right_tower_p)
        
        # Enemy (Top)
        # King Tower: One level (tile) offset from top edge
        king_y_e = GRID_MARGIN_Y + 1 * TILE_SIZE + TILE_SIZE // 2
        self.king_tower_e = Tower(self, SCREEN_WIDTH//2, king_y_e, "king", "enemy")
        
        # Princess Towers: Row 4
        princess_y_e = GRID_MARGIN_Y + 4 * TILE_SIZE + TILE_SIZE // 2
        self.left_tower_e = Tower(self, left_lane_x, princess_y_e, "princess", "enemy")
        self.right_tower_e = Tower(self, right_lane_x, princess_y_e, "princess", "enemy")
        self.enemy.towers.add(self.king_tower_e, self.left_tower_e, self.right_tower_e)

    def get_mouse_pos(self):
        return self.engine.get_mouse_pos()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.game_over:
                self.reset_game()
            # Cancel selection with ESC
            if event.key == pygame.K_ESCAPE:
                self.selected_card_idx = None
                self.dragging_card_idx = None
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = self.get_mouse_pos()
                
                # Check Emote Button
                if self.emote_button_rect.collidepoint(pos):
                    self.show_emotes = not self.show_emotes
                    return True
                    
                # Check Emote Menu Interactions
                if self.show_emotes:
                    if self.emote_menu_rect.collidepoint(pos):
                        # Check buttons
                        for btn in self.emote_buttons:
                            if btn["rect"].collidepoint(pos):
                                print(f"Emote: {btn['text']}")
                                self.show_emotes = False
                                # TODO: Send emote to server/display it
                                return True
                        return True # Consumed click in menu area
                    else:
                        # Clicked outside menu (e.g. on field), close it
                        self.show_emotes = False
                        # Don't return True, allow click to pass through to field (e.g. to place unit)? 
                        # Actually, if we click outside to close, we probably shouldn't also place a unit in the same click.
                        return True
                
                # Check Card Clicks (Only if emotes are NOT showing)
                if not self.show_emotes:
                    clicked_card = False
                    for i, rect in self.card_rects.items():
                        if rect.collidepoint(pos):
                            self.selected_card_idx = i
                            self.dragging_card_idx = i
                            self.drag_pos = pos
                            clicked_card = True
                            return True
                
                # If clicked on field with a selected card
                if not self.show_emotes and not clicked_card and self.selected_card_idx is not None:
                    # Do nothing on mouse down, wait for mouse up
                    pass
            
            elif event.button == 3: # Right Click
                # Cancel selection
                self.selected_card_idx = None
                self.dragging_card_idx = None
                return True

        elif event.type == pygame.MOUSEMOTION:
            self.drag_pos = self.get_mouse_pos()
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                # If we were dragging, try to play on release
                if self.dragging_card_idx is not None:
                    pos = self.get_mouse_pos()
                    # Only try to play if we are in the playable area
                    if pos[1] < self.playable_height:
                        if self.try_play_card(pos):
                            self.selected_card_idx = None
                    
                    self.dragging_card_idx = None
                
                # If we have a selected card (click-to-play mode), try to play on release
                elif self.selected_card_idx is not None:
                    pos = self.get_mouse_pos()
                    # Only try to play if we are in the playable area
                    if pos[1] < self.playable_height:
                        if self.try_play_card(pos):
                            self.selected_card_idx = None
            
                # Check Game Over OK button
                if self.game_over:
                    pos = self.get_mouse_pos()
                    ok_rect = pygame.Rect(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 + 100, 100, 50)
                    if ok_rect.collidepoint(pos):
                        return "menu"
        return None

    def snap_to_grid(self, pos):
        """
        Snap a screen position to the center of the nearest grid tile.
        """
        x, y = pos
        
        # Adjust for margin
        grid_x = x - GRID_MARGIN_X
        grid_y = y - GRID_MARGIN_Y
        
        # Calculate tile index
        tile_col = int(grid_x // TILE_SIZE)
        tile_row = int(grid_y // TILE_SIZE)
        
        # Clamp to grid bounds
        tile_col = max(0, min(tile_col, GRID_WIDTH - 1))
        tile_row = max(0, min(tile_row, GRID_HEIGHT - 1))
        
        # Calculate center of that tile
        center_x = GRID_MARGIN_X + tile_col * TILE_SIZE + TILE_SIZE // 2
        center_y = GRID_MARGIN_Y + tile_row * TILE_SIZE + TILE_SIZE // 2
        
        return (center_x, center_y)

    def try_play_card(self, pos):
        """
        Attempt to play the currently selected card at the given position.
        Returns True if successful (or sent to server), False otherwise.
        """
        if self.selected_card_idx is None:
            return False
            
        card = self.player.hand[self.selected_card_idx]
        if not card:
            return False

        # Snap position to grid
        snapped_pos = self.snap_to_grid(pos)

        # Check if position is valid for this card
        valid_rects = self.get_valid_spawn_rects()
        # Spells can be placed anywhere
        from game.core.card import SpellCard
        if isinstance(card, SpellCard):
            pass # Valid anywhere
        else:
            # Units must be in valid spawn area
            valid = False
            for rect in valid_rects:
                if rect.collidepoint(snapped_pos):
                    valid = True
                    break
            
            if not valid:
                # Show invalid placement feedback?
                return False
                
            # Check for tower collision
            # Prevent placing units on top of towers
            for tower in self.towers:
                if tower.alive():
                    # Simple distance check or rect check
                    # Towers have size ~40-60. Units ~20-30.
                    # If distance < (tower_radius + unit_radius), it's overlapping.
                    # Let's use a safe distance of tower.size/2 + 10
                    dist = tower.pos.distance_to(pygame.math.Vector2(snapped_pos))
                    min_dist = (tower.size / 2) + 15 # 15 is approx unit radius + margin
                    if dist < min_dist:
                        return False
        
        # Check Elixir
        if self.player.elixir < card.cost:
            # Show not enough elixir feedback?
            return False
        
        # Generate network IDs here so we can send them
        import uuid
        network_ids = [str(uuid.uuid4()) for _ in range(card.count)] if hasattr(card, "count") else [str(uuid.uuid4())]
        
        # Calculate target tick for execution
        target_tick = self.tick + self.latency_buffer
        
        # Notify listener (NetworkController) to send the message
        # We do NOT play the card locally yet!
        if self.on_card_played:
            self.on_card_played(card, snapped_pos, network_ids, target_tick)
        else:
            # If no network controller (e.g. single player testing without server),
            # execute immediately (or schedule it to simulate latency?)
            # For local testing, we can just execute it at target_tick
            self.execute_play_card(card.name, snapped_pos, "player", network_ids, target_tick)
            
        return True

    def execute_play_card(self, card_name, pos, side, network_ids=None, target_tick=None):
        """
        Schedule or execute card play.
        """
        if target_tick is not None and target_tick > self.tick:
            # Schedule for future
            self.action_queue.append((target_tick, "play_card", {
                "card_name": card_name,
                "pos": pos,
                "side": side,
                "network_ids": network_ids
            }))
            self.action_queue.sort(key=lambda x: x[0]) # Keep sorted by tick
            return

        card = CardRegistry.get(card_name)
        if not card:
            return
            
        # Play the card effect
        card.play(self, pos, side, network_ids)
        
        # If it's the local player, spend elixir and cycle card
        if side == "player":
            found_idx = -1
            for i, c in enumerate(self.player.hand):
                if c and c.name == card_name:
                    found_idx = i
                    break
            
            if found_idx != -1:
                self.player.spend_elixir(card.cost)
                self.player.play_card(found_idx)
                
                # Reset selection if we just played the selected card
                if self.selected_card_idx == found_idx:
                    self.selected_card_idx = None
                    self.dragging_card_idx = None

    def spawn_card(self, card_name, pos, side, network_ids=None):
        """Deprecated: Use execute_play_card instead."""
        self.execute_play_card(card_name, pos, side, network_ids)



    def get_valid_spawn_rects(self):
        return self.arena.get_valid_spawn_rects()

    def update(self, dt):
        if self.game_over:
            return
            
        self.tick += 1
        
        # Process scheduled actions
        while self.action_queue and self.action_queue[0][0] <= self.tick:
            tick, action_type, data = self.action_queue.pop(0)
            if action_type == "play_card":
                self.execute_play_card(
                    data["card_name"], 
                    data["pos"], 
                    data["side"], 
                    data["network_ids"],
                    target_tick=None # Force immediate execution
                )

        self.player.update_elixir(dt)
        self.enemy.update_elixir(dt)
            
        # Enemy AI
        if self.practice_mode:
            self.enemy_spawn_timer += dt
            if self.enemy_spawn_timer >= 5.0:
                import random
                lane = random.choice([80, SCREEN_WIDTH - 80])
                unit_type = random.choice(["knight", "archer", "goblin", "minions"])
                # Enemy cheats infinite elixir for now
                Unit(self, lane, 250, unit_type, "enemy")
                self.enemy_spawn_timer = 0
            
        # Update sprites deterministically
        # Sort by network_id to ensure consistent order across clients and for symmetry tests
        sorted_sprites = sorted(self.all_sprites.sprites(), key=lambda s: str(getattr(s, 'network_id', '') or id(s)))
        
        # Phase 0: Prepare (Reset accumulators)
        for sprite in sorted_sprites:
            if hasattr(sprite, 'prepare_update'):
                sprite.prepare_update()
                
        # Phase 1: Think (Targeting/Logic/Physics Calc)
        for sprite in sorted_sprites:
            if hasattr(sprite, 'think'):
                sprite.think(dt)
                
        # Phase 2: Apply (Movement/Damage/Death)
        for sprite in sorted_sprites:
            if hasattr(sprite, 'apply_pending_changes'):
                sprite.apply_pending_changes()
                
        # Phase 3: Update (Animation/State)
        for sprite in sorted_sprites:
            sprite.update(dt)
        
        # Check Activations
        self.check_tower_activation()
        self.check_game_over()
        
        # Update Timer
        self.battle_timer -= dt
        if self.battle_timer <= 0:
            if not self.sudden_death:
                # Main time over, check for tie
                p_towers = len(self.player.towers)
                e_towers = len(self.enemy.towers)
                
                if p_towers == e_towers:
                    # Enter Sudden Death
                    self.sudden_death = True
                    self.battle_timer = 120.0 # 2 minutes overtime
                    self.sd_start_towers_p = p_towers
                    self.sd_start_towers_e = e_towers
                else:
                    # Game Over
                    self.game_over = True
                    self.winner = "Player" if p_towers > e_towers else "Enemy"
            else:
                # Sudden Death over - Draw (or tiebreaker logic)
                self.game_over = True
                # Simple tiebreaker: Health of lowest tower? For now, Draw.
                self.winner = "Draw"
                # Check healths for winner?
                p_health = sum(t.health for t in self.player.towers)
                e_health = sum(t.health for t in self.enemy.towers)
                if p_health > e_health: self.winner = "Player"
                elif e_health > p_health: self.winner = "Enemy"
        
    def check_tower_activation(self):
        if not self.left_tower_p.alive() or not self.right_tower_p.alive():
            self.king_tower_p.active = True
        if not self.left_tower_e.alive() or not self.right_tower_e.alive():
            self.king_tower_e.active = True

    def check_game_over(self):
        # Check for destroyed towers and update crowns
        # Player side
        if not self.king_tower_p.alive() and not self.game_over:
            self.game_over = True
            self.winner = "Enemy"
            self.enemy_crowns = 3  # King tower = automatic 3 crowns
        else:
            # Count princess towers destroyed
            destroyed_count = 0
            if not self.left_tower_p.alive():
                destroyed_count += 1
            if not self.right_tower_p.alive():
                destroyed_count += 1
            # Update enemy crowns based on destroyed player towers
            self.enemy_crowns = destroyed_count
            
        # Enemy side
        if not self.king_tower_e.alive() and not self.game_over:
            self.game_over = True
            self.winner = "Player"
            self.player_crowns = 3  # King tower = automatic 3 crowns
        else:
            # Count princess towers destroyed
            destroyed_count = 0
            if not self.left_tower_e.alive():
                destroyed_count += 1
            if not self.right_tower_e.alive():
                destroyed_count += 1
            # Update player crowns based on destroyed enemy towers
            self.player_crowns = destroyed_count
            
        if self.sudden_death and not self.game_over:
            if len(self.player.towers) < self.sd_start_towers_p:
                self.game_over = True
                self.winner = "Enemy"
            elif len(self.enemy.towers) < self.sd_start_towers_e:
                self.game_over = True
                self.winner = "Player"
            
    def reset_game(self, player_deck=None):
        self.all_sprites.empty()
        self.towers.empty()
        self.units.empty()
        self.projectiles.empty()
        
        # Load player deck from file if not provided
        if player_deck is None:
            from game.utils import load_deck
            player_deck = load_deck()
        
        default_enemy_deck = ["knight", "archer", "knight", "archer", "knight", "archer", "knight", "archer"]
        self.player = Player("player", player_deck)
        self.enemy = Player("enemy", default_enemy_deck)
        
        self.setup_arena()
        self.game_over = False
        self.winner = None
        self.battle_timer = 180.0
        self.sudden_death = False
        
        # Reset crown counters
        self.player_crowns = 0
        self.enemy_crowns = 0
        
    def draw(self):
        # Draw Arena Map via Arena class
        self.arena.draw(self.screen)
        
        # Draw Spawn Zones / Disallowed Areas
        if self.selected_card_idx is not None:
            card = self.player.hand[self.selected_card_idx]
            if card and not isinstance(card, SpellCard):
                # Draw Red Overlay on Disallowed Areas
                # Create a full screen red overlay
                overlay = pygame.Surface((SCREEN_WIDTH, self.playable_height), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 60)) # Red with alpha
                
                # Cut out valid rects (make them transparent)
                valid_rects = self.get_valid_spawn_rects()
                for rect in valid_rects:
                    overlay.fill((0, 0, 0, 0), rect)
                    
                self.screen.blit(overlay, (0, 0))
                
                # Draw Red Outline around valid rects (which effectively outlines the disallowed area boundary)
                # Actually, drawing outlines of valid rects might look weird if they overlap.
                # Instead, let's draw the grid on the valid area to show where you CAN place.
                for rect in valid_rects:
                    pygame.draw.rect(self.screen, (100, 255, 100), rect, 1)

        # Draw Grid (always visible or only when dragging?)
        # User asked for background to show tiles.
        # REMOVED explicit grid lines as per user request.
        pass
        
        # Sort sprites by Y coordinate (bottom of rect) for depth
        # We need to draw them in order
        sprites_list = list(self.all_sprites)
        sprites_list.sort(key=lambda s: s.rect.bottom)
        
        for sprite in sprites_list:
            self.screen.blit(sprite.image, sprite.rect)
        
        for sprite in self.all_sprites:
            if hasattr(sprite, 'draw_health_bar'):
                sprite.draw_health_bar(self.screen)

        # Draw tower HP labels - MOVED to Tower.draw_health_bar
        pass
        
        self.draw_hud()
        
        if self.show_emotes:
            self.draw_emote_menu()

    def draw_emote_menu(self):
        # Background
        pygame.draw.rect(self.screen, (240, 240, 240), self.emote_menu_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, self.emote_menu_rect, 2, border_radius=10)
        
        # Placeholder for King Emotes
        font_king = pygame.font.SysFont("Arial", 12)
        king_text = font_king.render("(King Emotes Placeholder)", True, GREY)
        self.screen.blit(king_text, (self.emote_menu_rect.centerx - king_text.get_width()//2, self.emote_menu_rect.y + 20))
        
        # Text Buttons
        font = pygame.font.SysFont("Arial", 16, bold=True)
        for btn in self.emote_buttons:
            # Button bg
            pygame.draw.rect(self.screen, WHITE, btn["rect"], border_radius=5)
            pygame.draw.rect(self.screen, BLACK, btn["rect"], 2, border_radius=5)
            
            # Text
            text = font.render(btn["text"], True, BLACK)
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)
        
    def draw_hud(self):
        from game.entities.geometric_sprites import geometric_renderer
        
        # Background
        hud_rect = pygame.Rect(0, self.playable_height, SCREEN_WIDTH, self.hud_height)
        pygame.draw.rect(self.screen, DARK_GREY, hud_rect)
        pygame.draw.line(self.screen, BLACK, (0, self.playable_height), (SCREEN_WIDTH, self.playable_height), 3)
        
        # 1. Elixir Bar
        bar_rect = self.elixir_bar_rect
        # Background
        pygame.draw.rect(self.screen, (30, 30, 30), bar_rect, border_radius=10)
        
        # Fill
        fill_width = int((self.player.elixir / MAX_ELIXIR) * bar_rect.width)
        fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_rect.height)
        pygame.draw.rect(self.screen, (200, 0, 255), fill_rect, border_radius=10)
        
        # Segments
        for i in range(1, MAX_ELIXIR):
            x = bar_rect.x + (i / MAX_ELIXIR) * bar_rect.width
            pygame.draw.line(self.screen, (100, 100, 100), (x, bar_rect.y), (x, bar_rect.bottom))
            
        # Border
        pygame.draw.rect(self.screen, WHITE, bar_rect, 2, border_radius=10)
        
        # Text
        font = pygame.font.SysFont("Arial", 16, bold=True)
        text = font.render(f"{int(self.player.elixir)}", True, WHITE)
        self.screen.blit(text, (bar_rect.x - 25, bar_rect.y))
        
        # 2. Cards (or Emote Menu)
        if self.show_emotes:
            self.draw_emote_menu()
        else:
            # Draw Deck Box Background (Optional, makes it look like a container)
            # deck_bg_rect = self.emote_menu_rect # Use same rect
            # pygame.draw.rect(self.screen, (40, 40, 40), deck_bg_rect, border_radius=5)
            
            for i, card in enumerate(self.player.hand):
                if i not in self.card_rects:
                    continue
                    
                rect = self.card_rects[i]
                
                # If dragging this card, draw it faded
                if self.dragging_card_idx == i:
                    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    s.fill((200, 200, 200, 50))
                    self.screen.blit(s, rect)
                    pygame.draw.rect(self.screen, LIGHT_GREY, rect, 2, border_radius=5)
                else:
                    self._draw_card_icon(rect, card.name)
                    
                    # Highlight selected card
                    if self.selected_card_idx == i:
                        pygame.draw.rect(self.screen, GOLD, rect, 4, border_radius=5)
                    
                    # Check affordability
                    if self.player.elixir < card.cost:
                        # Darken if can't afford
                        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                        s.fill((0, 0, 0, 150))
                        self.screen.blit(s, rect)
            
        # 3. Next Card
        next_rect = self.next_card_rect
        
        # Label above
        label_font = pygame.font.SysFont("Arial", 12, bold=True)
        label_text = label_font.render("Next:", True, WHITE)
        self.screen.blit(label_text, (next_rect.x, next_rect.y - 15))
        
        if self.player.next_card:
            self._draw_card_icon(next_rect, self.player.next_card.name, small=True)

        # 4. Emote Button
        pygame.draw.rect(self.screen, WHITE, self.emote_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, self.emote_button_rect, 2, border_radius=10)
        # Chat bubble icon
        bubble_rect = pygame.Rect(0, 0, 24, 18)
        bubble_rect.center = self.emote_button_rect.center
        
        pygame.draw.ellipse(self.screen, BLACK, bubble_rect, 2)
        # Tail
        pygame.draw.line(self.screen, BLACK, (bubble_rect.left + 5, bubble_rect.bottom-2), (bubble_rect.left + 2, bubble_rect.bottom + 3), 2)
        # Dots
        pygame.draw.circle(self.screen, BLACK, (bubble_rect.centerx - 6, bubble_rect.centery), 2)
        pygame.draw.circle(self.screen, BLACK, (bubble_rect.centerx, bubble_rect.centery), 2)
        pygame.draw.circle(self.screen, BLACK, (bubble_rect.centerx + 6, bubble_rect.centery), 2)
        
        # Timer
        minutes = int(self.battle_timer) // 60
        seconds = int(self.battle_timer) % 60
        timer_color = RED if self.sudden_death else WHITE
        font_timer = pygame.font.SysFont("Arial", 24)
        timer_text = font_timer.render(f"{minutes}:{seconds:02d}", True, timer_color)
        self.screen.blit(timer_text, (SCREEN_WIDTH - 80, 10))
        
        if self.sudden_death:
            sd_text = font_timer.render("SUDDEN DEATH", True, RED)
            self.screen.blit(sd_text, (SCREEN_WIDTH//2 - 70, 10))

    def _draw_card_icon(self, rect, card_name, small=False):
        from game.entities.geometric_sprites import geometric_renderer
        
        # card_name is a string here because we pass card.name in draw_hud
        # But we need stats for cost/color.
        # Let's look it up in registry or stats dicts.
        is_spell = card_name in SPELL_STATS
        
        # Use geometric renderer for everything now
        icon_size = (rect.width, rect.height)
        if small:
            icon_size = (rect.width, rect.height) # Keep size
            
        # Get icon from renderer (it handles background color and text)
        icon = geometric_renderer.get_card_icon(card_name, icon_size)
        self.screen.blit(icon, rect)
            
        # Cost (if not small)
        if not small:
            cost = SPELL_STATS[card_name]["cost"] if is_spell else UNIT_STATS[card_name]["cost"]
            pygame.draw.circle(self.screen, (255, 100, 200), (rect.right - 10, rect.y + 10), 8)
            pygame.draw.circle(self.screen, BLACK, (rect.right - 10, rect.y + 10), 8, 1)
            
            font = pygame.font.SysFont("Arial", 12, bold=True)
            text = font.render(str(cost), True, WHITE)
            self.screen.blit(text, (rect.right - 10 - text.get_width()//2, rect.y + 3))
            
            # Name - REMOVED as per request
            # name_parts = card_name.split('_')
            # display_name = name_parts[0][:4].upper()
            # name_font = pygame.font.SysFont("Arial", 10, bold=True)
            # name_text = name_font.render(display_name, True, BLACK)
            # self.screen.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.bottom - 15))

        # Game Over
        if self.game_over:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(200)
            s.fill(BLACK)
            self.screen.blit(s, (0,0))
            
            # Winner text
            font_big = pygame.font.SysFont("Arial", 48, bold=True)
            winner_color = BLUE if self.winner == "Player" else RED
            text = font_big.render(f"{self.winner} Wins!", True, winner_color)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            self.screen.blit(text, rect)
            
            # Crown display
            font_crown = pygame.font.SysFont("Arial", 36, bold=True)
            crown_y = SCREEN_HEIGHT//2 - 20
            
            # Player crowns
            player_crown_text = font_crown.render(f"👑 {self.player_crowns}", True, BLUE)
            self.screen.blit(player_crown_text, (SCREEN_WIDTH//2 - 150, crown_y))
            
            # VS
            vs_text = font_crown.render("-", True, WHITE)
            self.screen.blit(vs_text, (SCREEN_WIDTH//2 - 10, crown_y))
            
            # Enemy crowns
            enemy_crown_text = font_crown.render(f"{self.enemy_crowns} 👑", True, RED)
            self.screen.blit(enemy_crown_text, (SCREEN_WIDTH//2 + 50, crown_y))
            
            font_small = pygame.font.SysFont("Arial", 32)
            
            # OK Button
            ok_rect = pygame.Rect(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 + 100, 100, 50)
            pygame.draw.rect(self.screen, WHITE, ok_rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, ok_rect, 2, border_radius=8)
            text_ok = font_small.render("OK", True, BLACK)
            rect_ok = text_ok.get_rect(center=ok_rect.center)
            self.screen.blit(text_ok, rect_ok)
            
        # Drag Visual / Selection Visual
        # Show if dragging OR if selected and mouse is in playable area
        mouse_pos = self.get_mouse_pos()
        show_visual = False
        visual_pos = None
        
        # Drag Visual / Selection Visual
        # Show if dragging OR if selected and mouse is in playable area
        mouse_pos = self.get_mouse_pos()
        show_visual = False
        visual_pos = None
        
        # Determine active card (dragging takes precedence)
        active_idx = self.dragging_card_idx if self.dragging_card_idx is not None else self.selected_card_idx
        
        if active_idx is not None:
            # Check conditions to show visual
            is_dragging = self.dragging_card_idx is not None and self.drag_pos
            is_selected = self.selected_card_idx is not None and mouse_pos[1] < self.playable_height
            
            if is_dragging:
                visual_pos = self.drag_pos
            elif is_selected:
                visual_pos = mouse_pos
                
            if visual_pos:
                # Always show visual (either range or ghost)
                show_visual = True

        if show_visual and visual_pos:
            # Strict check: only show if in playable area
            if visual_pos[1] >= self.playable_height:
                return

            # Snap visual position to grid!
            visual_pos = self.snap_to_grid(visual_pos)

            card = self.player.hand[active_idx]
            if not card: return
            
            # Check if spell or unit (building)
            if isinstance(card, SpellCard):
                # Spell: show AOE radius
                color = card.stats["color"]
                radius = card.stats["radius"]
                pygame.draw.circle(self.screen, color, visual_pos, 10)
                pygame.draw.circle(self.screen, color, visual_pos, radius, 2)
                # Fill with semi-transparent
                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color, 50), (radius, radius), radius)
                self.screen.blit(s, (visual_pos[0] - radius, visual_pos[1] - radius))
            else:
                # Check if building
                is_building = False
                if hasattr(card, "stats") and card.stats.get("unit_type") == "building":
                    is_building = True
                    
                if is_building:
                    # Building: show range
                    color = card.stats["color"]
                    pygame.draw.circle(self.screen, color, visual_pos, 10)
                    range_val = card.stats["range"]
                    pygame.draw.circle(self.screen, WHITE, visual_pos, range_val, 1)
                else:
                    # Unit: Draw Ghost Preview
                    from game.entities.geometric_sprites import geometric_renderer
                    import math
                    from game.core.symmetry import SymmetryUtils
                    
                    # Calculate animation phase for "alive" feel
                    animation_phase = (pygame.time.get_ticks() % 1000) / 1000.0
                    
                    # Get the sprite facing UP (270) as if deployed
                    sprite = geometric_renderer.get_sprite(card.name, "player", animation_phase, 270)
                    
                    if sprite:
                        # Determine count and positions
                        count = getattr(card, "count", 1)
                        
                        positions = []
                        if count == 1:
                            positions.append(visual_pos)
                        else:
                            # Calculate swarm positions relative to visual_pos
                            radius = 30
                            for i in range(count):
                                angle = (2 * math.pi / count) * i
                                # No need to transform for player side preview (always player perspective)
                                # But we should match the spawn logic if possible. 
                                # Spawn logic uses SymmetryUtils.transform_formation_angle(angle, side)
                                # Here side is "player".
                                angle = SymmetryUtils.transform_formation_angle(angle, "player")
                                
                                offset_x = math.cos(angle) * radius
                                offset_y = math.sin(angle) * radius
                                positions.append((visual_pos[0] + offset_x, visual_pos[1] + offset_y))
                        
                        # Draw ghosts at all positions
                        for pos in positions:
                            ghost = sprite.copy()
                            rect = ghost.get_rect(center=pos)
                            self.screen.blit(ghost, rect, special_flags=pygame.BLEND_ADD)
