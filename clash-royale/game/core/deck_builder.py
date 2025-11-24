import pygame
from game.entities.geometric_sprites import geometric_renderer
from game.settings import *
from game.utils import load_deck, save_deck
from game.ui.core import UIManager, Button, Label, UIElement

class CardButton(Button):
    def __init__(self, x, y, w, h, card_name, on_click=None):
        super().__init__(x, y, w, h, "", on_click=on_click)
        self.card_name = card_name
        self.selected = False
        
    def draw(self, surface):
        # Draw card icon
        icon = geometric_renderer.get_card_icon(self.card_name, (self.rect.width, self.rect.height))
        surface.blit(icon, self.rect)
        
        # Draw border if hovered
        if self.selected:
            pygame.draw.rect(surface, (0, 255, 255), self.rect, 3, border_radius=5) # Cyan for selected
        elif self.hovered:
            pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=5)
        else:
            pygame.draw.rect(surface, BLACK, self.rect, 1, border_radius=5)

class DeckBuilder:
    def __init__(self, engine):
        self.engine = engine
        self.screen = engine.virtual_surface
        self.deck = load_deck()
        self.available_cards = sorted(list(UNIT_STATS.keys()) + list(SPELL_STATS.keys()))
        
        self.ui = UIManager(engine)
        self.selected_card = None 
        self.showing_info = False
        self.replacing_card = None 
        
        # Drag and Drop
        self.dragging_card = None 
        self.dragging_offset = (0, 0)
        self.drag_start_pos = (0, 0) 
        
        self.header_height = 80
        
        # Back Button (Fixed in Header)
        self.back_btn = Button(20, 20, 100, 40, "Back", on_click=self.on_back)
        self.ui.add(self.back_btn)
        
        # Info Screen Buttons
        self.info_action_btn = Button(0, 0, 120, 40, "Add", on_click=self.on_action)
        self.info_action_btn.visible = False
        self.ui.add(self.info_action_btn)
        
        self.info_close_btn = Button(0, 0, 120, 40, "Close", on_click=self.on_close_info)
        self.info_close_btn.visible = False
        self.ui.add(self.info_close_btn)

        # Popup Action Buttons
        self.popup_info_btn = Button(0, 0, 80, 30, "Info", font_size=18, on_click=self.on_info)
        self.popup_action_btn = Button(0, 0, 80, 30, "Add", font_size=18, on_click=self.on_action)
        self.popup_info_btn.visible = False
        self.popup_action_btn.visible = False
        self.ui.add(self.popup_info_btn)
        self.ui.add(self.popup_action_btn)

        # Title
        self.title_label = Label(SCREEN_WIDTH//2, 30, "Deck Builder", font_size=32, center=True)
        self.ui.add(self.title_label)
        
        # Initialize Buttons
        self.deck_buttons = []
        self.card_buttons = []
        self.create_buttons() # Create all button instances once
        
        self.scroll_offset = 0
        self.max_scroll = 0
        self.should_exit = False
        
        # Layout Constants
        self.card_w = 95
        self.card_h = 125
        self.spacing = 10
        self.cols = 4
        self.grid_w = self.cols * self.card_w + (self.cols - 1) * self.spacing
        self.start_x = (SCREEN_WIDTH - self.grid_w) // 2

    def create_buttons(self):
        # Create buttons for all available cards
        # We will position them dynamically in update()
        self.card_buttons = []
        for card_name in self.available_cards:
            btn = CardButton(0, 0, 95, 125, card_name,
                             on_click=lambda c=card_name: self.select_card(c))
            self.card_buttons.append(btn)
            
        # Create buttons for deck (up to 8 slots)
        # We'll manage these dynamically too, but let's create instances for the current deck
        self.update_deck_buttons()

    def on_back(self):
        if self.showing_info:
            self.showing_info = False
        elif self.replacing_card:
            self.replacing_card = None 
        else:
            save_deck(self.deck)
            self.should_exit = True

    def on_info(self):
        if self.selected_card:
            self.showing_info = True
            
    def on_close_info(self):
        self.showing_info = False

    def on_action(self):
        if not self.selected_card:
            return
            
        if self.selected_card in self.deck:
            self.remove_from_deck(self.selected_card)
        else:
            if len(self.deck) >= 8:
                self.replacing_card = self.selected_card
                self.showing_info = False 
            else:
                self.add_to_deck(self.selected_card)

    def select_card(self, card_name):
        if self.replacing_card:
            if card_name in self.deck:
                self.swap_cards(self.replacing_card, card_name)
                self.replacing_card = None
            return

        if self.selected_card == card_name:
            self.selected_card = None 
        else:
            self.selected_card = card_name

    def swap_cards(self, new_card, old_card):
        if old_card in self.deck:
            idx = self.deck.index(old_card)
            self.deck[idx] = new_card
            self.update_deck_buttons()
            save_deck(self.deck)
            self.selected_card = None

    def update_deck_buttons(self):
        self.deck_buttons = []
        for card_name in self.deck:
            btn = CardButton(0, 0, 95, 125, card_name, 
                             on_click=lambda c=card_name: self.select_card(c))
            self.deck_buttons.append(btn)

    def remove_from_deck(self, card_name):
        if card_name in self.deck:
            self.deck.remove(card_name)
            self.update_deck_buttons()
            save_deck(self.deck)
            self.selected_card = None 

    def add_to_deck(self, card_name):
        if len(self.deck) < 8 and card_name not in self.deck:
            self.deck.append(card_name)
            self.update_deck_buttons()
            save_deck(self.deck)
            self.selected_card = None 

    def handle_event(self, event):
        if self.showing_info:
            if self.ui.handle_event(event):
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.showing_info = False
            return

        if self.replacing_card:
            if self.back_btn.handle_event(event, self.engine.get_mouse_pos()):
                return
            virtual_pos = self.engine.get_mouse_pos()
            for btn in self.deck_buttons:
                if btn.handle_event(event, virtual_pos):
                    return
            return

        if self.ui.handle_event(event):
            return "menu" if self.should_exit else None

        virtual_pos = self.engine.get_mouse_pos()

        # Drag and Drop Logic
        # We need to distinguish between a Click (Select) and a Drag.
        # We use a threshold: if mouse moves > 5 pixels while down, it's a drag.
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check for potential drag start
            self.drag_candidate = None
            
            # Check deck buttons
            for btn in self.deck_buttons:
                if btn.rect.collidepoint(virtual_pos):
                    self.drag_candidate = btn
                    self.drag_start_pos = virtual_pos
                    break
            
            # Check collection buttons
            if not self.drag_candidate:
                for btn in self.card_buttons:
                    if btn.visible and btn.rect.collidepoint(virtual_pos):
                        self.drag_candidate = btn
                        self.drag_start_pos = virtual_pos
                        break

        elif event.type == pygame.MOUSEMOTION:
            if self.drag_candidate and not self.dragging_card:
                # Check threshold
                dx = virtual_pos[0] - self.drag_start_pos[0]
                dy = virtual_pos[1] - self.drag_start_pos[1]
                if (dx*dx + dy*dy) > 25: # 5 pixels squared
                    self.dragging_card = self.drag_candidate.card_name
                    self.dragging_offset = (virtual_pos[0] - self.drag_candidate.rect.x, 
                                          virtual_pos[1] - self.drag_candidate.rect.y)
                    self.drag_candidate = None # dragging started

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging_card:
                # Handle Drop
                dropped_on_deck = False
                for btn in self.deck_buttons:
                    if btn.rect.collidepoint(virtual_pos):
                        if btn.card_name != self.dragging_card:
                            self.swap_cards(self.dragging_card, btn.card_name)
                            dropped_on_deck = True
                        break
                
                if not dropped_on_deck and len(self.deck) < 8:
                    if virtual_pos[1] < self.header_height + 300: 
                         if self.dragging_card not in self.deck:
                             self.add_to_deck(self.dragging_card)

                self.dragging_card = None
                self.drag_candidate = None
                return # Consume event so buttons don't click
            
            self.drag_candidate = None

        # Scroll
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - event.y * 30))

        # Handle Clicks (if not dragging)
        # If we are dragging, we don't pass events to buttons
        if not self.dragging_card:
            for btn in self.deck_buttons:
                if btn.handle_event(event, virtual_pos):
                    return
            for btn in self.card_buttons:
                if btn.visible:
                    if btn.handle_event(event, virtual_pos):
                        return

        if self.should_exit:
            return "menu"
        return None

    def update(self, dt):
        self.ui.update(dt)
        
        # --- DYNAMIC LAYOUT CALCULATION ---
        # We calculate positions every frame to handle scrolling and deck changes correctly
        
        current_y = self.header_height + 20 - self.scroll_offset
        
        # 1. Deck Area
        # Position Deck Buttons
        for i, btn in enumerate(self.deck_buttons):
            row = i // self.cols
            col = i % self.cols
            btn.rect.x = self.start_x + col * (self.card_w + self.spacing)
            btn.rect.y = current_y + row * (self.card_h + self.spacing)
            
        # Advance Y past deck
        # 2 rows of cards + spacing
        deck_rows = 2
        deck_height = deck_rows * (self.card_h + self.spacing)
        current_y += deck_height + 10 # Extra padding
        
        # Elixir Text Position (Stored for draw)
        self.elixir_y = current_y
        current_y += 30 # Space for elixir text
        
        # Collection Label Position (Stored for draw)
        self.collection_label_y = current_y
        current_y += 40 # Space for label
        
        # 2. Collection Area
        # Filter visible buttons (not in deck)
        visible_collection_btns = [b for b in self.card_buttons if b.card_name not in self.deck]
        
        # Position Collection Buttons tightly (No gaps)
        for i, btn in enumerate(visible_collection_btns):
            row = i // self.cols
            col = i % self.cols
            btn.rect.x = self.start_x + col * (self.card_w + self.spacing)
            btn.rect.y = current_y + row * (self.card_h + self.spacing)
            
            # Visibility Check
            if btn.rect.bottom < self.header_height or btn.rect.top > SCREEN_HEIGHT:
                btn.visible = False
            else:
                btn.visible = True
                
        # Hide buttons in deck
        for btn in self.card_buttons:
            if btn.card_name in self.deck:
                btn.visible = False
                
        # Calculate Max Scroll
        # Total content height = current_y (start of collection) + collection height
        total_collection_rows = (len(visible_collection_btns) + self.cols - 1) // self.cols
        collection_height = total_collection_rows * (self.card_h + self.spacing)
        total_content_height = (current_y + self.scroll_offset) + collection_height + 100 # + padding
        # Note: current_y includes -scroll_offset, so we add it back to get absolute height
        
        self.max_scroll = max(0, total_content_height - SCREEN_HEIGHT)
        
        # --- END LAYOUT ---

        # Update Button States
        virtual_pos = self.engine.get_mouse_pos()
        
        for btn in self.deck_buttons:
            btn.selected = (btn.card_name == self.selected_card)
            btn.update(dt, virtual_pos)
            
        for btn in visible_collection_btns:
            if btn.visible:
                btn.selected = (btn.card_name == self.selected_card)
                btn.update(dt, virtual_pos)

        # Info Screen Logic
        if self.showing_info:
            self.popup_info_btn.visible = False
            self.popup_action_btn.visible = False
            self.info_action_btn.visible = True
            self.info_close_btn.visible = True
            
            box_w, box_h = 500, 600
            box_x = (SCREEN_WIDTH - box_w) // 2
            box_y = (SCREEN_HEIGHT - box_h) // 2
            btn_y = box_y + 210
            center_x = SCREEN_WIDTH // 2
            self.info_action_btn.rect.x = center_x - 130
            self.info_action_btn.rect.y = btn_y
            self.info_close_btn.rect.x = center_x + 10
            self.info_close_btn.rect.y = btn_y
            
            if self.selected_card in self.deck:
                self.info_action_btn.text = "Remove"
                self.info_action_btn.color = (200, 50, 50)
            else:
                if len(self.deck) >= 8:
                    self.info_action_btn.text = "Use"
                    self.info_action_btn.color = (50, 200, 50)
                else:
                    self.info_action_btn.text = "Add"
                    self.info_action_btn.color = (50, 200, 50)
            return

        self.info_action_btn.visible = False
        self.info_close_btn.visible = False

        if self.replacing_card:
            self.popup_info_btn.visible = False
            self.popup_action_btn.visible = False
            return

        # Popup Buttons Logic
        if self.selected_card and not self.dragging_card:
            # Find target button (Deck or Collection)
            target_btn = None
            for btn in self.deck_buttons:
                if btn.card_name == self.selected_card:
                    target_btn = btn
                    break
            if not target_btn:
                for btn in visible_collection_btns:
                    if btn.card_name == self.selected_card and btn.visible:
                        target_btn = btn
                        break
            
            if target_btn:
                self.popup_info_btn.visible = True
                self.popup_action_btn.visible = True
                
                popup_y = target_btn.rect.bottom - 5
                self.popup_info_btn.rect.x = target_btn.rect.centerx - self.popup_info_btn.rect.width // 2
                self.popup_info_btn.rect.y = popup_y + 5
                self.popup_action_btn.rect.x = target_btn.rect.centerx - self.popup_action_btn.rect.width // 2
                self.popup_action_btn.rect.y = popup_y + 40
                
                if self.selected_card in self.deck:
                    self.popup_action_btn.text = "Remove"
                    self.popup_action_btn.color = (200, 50, 50)
                else:
                    if len(self.deck) >= 8:
                        self.popup_action_btn.text = "Use"
                        self.popup_action_btn.color = (50, 200, 50)
                    else:
                        self.popup_action_btn.text = "Add"
                        self.popup_action_btn.color = (50, 200, 50)
            else:
                self.popup_info_btn.visible = False
                self.popup_action_btn.visible = False
        else:
            self.popup_info_btn.visible = False
            self.popup_action_btn.visible = False

    def draw_replacement_screen(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(220)
        s.fill(BLACK)
        self.screen.blit(s, (0,0))
        
        font = pygame.font.SysFont("Arial", 24, bold=True)
        text = font.render("Select card to be replaced", True, WHITE)
        self.screen.blit(text, ((SCREEN_WIDTH - text.get_width())//2, 150))
        
        # Draw Deck Buttons (They are already positioned by update, but might be scrolled off)
        # For replacement screen, we want them visible and centered?
        # Or just show them where they are?
        # User said "shows just that card, your deck above".
        # Let's force draw them in a nice grid for this screen.
        
        start_y = 200
        for i, btn in enumerate(self.deck_buttons):
            # Save original rect
            orig_rect = btn.rect.copy()
            
            # Temp position
            row = i // self.cols
            col = i % self.cols
            btn.rect.x = self.start_x + col * (self.card_w + self.spacing)
            btn.rect.y = start_y + row * (self.card_h + self.spacing)
            
            btn.draw(self.screen)
            
            # Restore rect (so clicks in update still work? No, update sets them back)
            # Actually, if we change rects here, handle_event needs to know.
            # But handle_event uses current rects.
            # If we change them here (in draw), handle_event won't see them until next update?
            # No, draw happens after update. Next frame update will reset them.
            # BUT handle_event happens before update.
            # So if we change them here, next frame handle_event uses these positions?
            # Yes, if we modify the object.
            # So this is actually a good way to override positions for this mode.
            pass 
            
        if self.replacing_card:
            icon = geometric_renderer.get_card_icon(self.replacing_card, (120, 120))
            x = (SCREEN_WIDTH - 120) // 2
            y = 500
            self.screen.blit(icon, (x, y))
            name_surf = font.render(self.replacing_card, True, WHITE)
            self.screen.blit(name_surf, ((SCREEN_WIDTH - name_surf.get_width())//2, y + 130))

    def draw_card_info(self):
        if not self.selected_card:
            return

        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill(BLACK)
        self.screen.blit(s, (0,0))
        
        box_w, box_h = 500, 600
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2
        pygame.draw.rect(self.screen, DARK_GREY, (box_x, box_y, box_w, box_h), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_w, box_h), 2, border_radius=10)
        
        icon_size = 120
        icon = geometric_renderer.get_card_icon(self.selected_card, (icon_size, icon_size))
        self.screen.blit(icon, (box_x + (box_w - icon_size)//2, box_y + 30))
        
        font = pygame.font.SysFont("Arial", 32, bold=True)
        name_surf = font.render(self.selected_card, True, WHITE)
        self.screen.blit(name_surf, (box_x + (box_w - name_surf.get_width())//2, box_y + 160))
        
        stats = UNIT_STATS.get(self.selected_card) or SPELL_STATS.get(self.selected_card)
        if stats:
            font_small = pygame.font.SysFont("Arial", 20)
            start_y = box_y + 270
            col1_x = box_x + 40
            col2_x = box_x + box_w // 2 + 20
            
            items = []
            for key, value in stats.items():
                if key in ["color", "speed_color"]: continue
                items.append((key, value))
                
            for i, (key, value) in enumerate(items):
                text = f"{key.replace('_', ' ').title()}: {value}"
                surf = font_small.render(text, True, LIGHT_GREY)
                if i % 2 == 0:
                    self.screen.blit(surf, (col1_x, start_y + (i//2) * 30))
                else:
                    self.screen.blit(surf, (col2_x, start_y + (i//2) * 30))
                
        font_tiny = pygame.font.SysFont("Arial", 16)
        close_surf = font_tiny.render("Click outside to close", True, GREY)
        self.screen.blit(close_surf, (box_x + (box_w - close_surf.get_width())//2, box_y + box_h - 30))

    def draw(self):
        self.screen.fill(DARK_GREY)
        
        # Draw Scrollable Content
        
        # 1. Deck Background
        # We want the background to cover the deck area.
        # Deck area starts at header_height - scroll_offset + 20
        # Ends at elixir_y
        deck_bg_y = self.header_height - self.scroll_offset
        deck_bg_h = (self.elixir_y + 30) - (self.header_height - self.scroll_offset) 
        # Actually, let's just draw a rect from top of scroll content to below elixir
        
        # Top of content is header_height - scroll_offset
        content_top = self.header_height - self.scroll_offset
        deck_bottom = self.collection_label_y - 10 # Approx
        
        pygame.draw.rect(self.screen, (60, 50, 40), (0, content_top, SCREEN_WIDTH, deck_bottom - content_top))
        pygame.draw.line(self.screen, BLACK, (0, deck_bottom), (SCREEN_WIDTH, deck_bottom), 3)
        
        # 2. Avg Elixir
        total_cost = sum((UNIT_STATS.get(c) or SPELL_STATS.get(c, {})).get("cost", 0) for c in self.deck)
        avg_cost = total_cost / len(self.deck) if self.deck else 0
        font_elixir = pygame.font.SysFont("Arial", 20, bold=True)
        elixir_text = f"Average Elixir Cost: {avg_cost:.1f}"
        elixir_surf = font_elixir.render(elixir_text, True, (255, 100, 255))
        self.screen.blit(elixir_surf, ((SCREEN_WIDTH - elixir_surf.get_width()) // 2, self.elixir_y))
        
        # 3. Collection Label
        font = pygame.font.SysFont("Arial", 24, bold=True)
        label = font.render("Card Collection", True, WHITE)
        self.screen.blit(label, (20, self.collection_label_y))
        
        # 4. Buttons
        for btn in self.deck_buttons:
            btn.draw(self.screen)
        for btn in self.card_buttons:
            if btn.visible:
                btn.draw(self.screen)
                
        # 5. Popup Buttons
        if self.popup_info_btn.visible:
            popup_rect = pygame.Rect(
                min(self.popup_info_btn.rect.x, self.popup_action_btn.rect.x) - 5,
                self.popup_info_btn.rect.y - 5,
                max(self.popup_info_btn.rect.width, self.popup_action_btn.rect.width) + 10,
                self.popup_action_btn.rect.bottom - self.popup_info_btn.rect.top + 10
            )
            pygame.draw.rect(self.screen, DARK_GREY, popup_rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, popup_rect, 2, border_radius=5)
            self.popup_info_btn.draw(self.screen)
            self.popup_action_btn.draw(self.screen)

        # Draw Header (Fixed)
        pygame.draw.rect(self.screen, (40, 40, 40), (0, 0, SCREEN_WIDTH, self.header_height))
        pygame.draw.line(self.screen, WHITE, (0, self.header_height), (SCREEN_WIDTH, self.header_height), 2)
        self.back_btn.draw(self.screen)
        self.title_label.draw(self.screen)

        # Draw Replacement Screen
        if self.replacing_card:
            self.draw_replacement_screen()
            
        # Draw Info Screen
        if self.showing_info:
            self.draw_card_info()
            
        # Draw Dragging Card
        if self.dragging_card:
            mouse_pos = self.engine.get_mouse_pos()
            icon = geometric_renderer.get_card_icon(self.dragging_card, (95, 125))
            x = mouse_pos[0] - self.dragging_offset[0]
            y = mouse_pos[1] - self.dragging_offset[1]
            self.screen.blit(icon, (x, y))
