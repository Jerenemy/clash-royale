import pygame
from game.settings import *

class UIElement:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.active = True
        self.manager = None # Set when added to manager

    def handle_event(self, event, mouse_pos):
        pass

    def update(self, dt, mouse_pos):
        pass

    def draw(self, surface):
        pass

class UIManager:
    def __init__(self, engine):
        self.engine = engine
        self.elements = []

    def add(self, element):
        self.elements.append(element)
        element.manager = self
        return element

    def clear(self):
        self.elements = []

    def handle_event(self, event):
        virtual_pos = self.engine.get_mouse_pos()
        for element in reversed(self.elements):
            if element.active and element.visible:
                if element.handle_event(event, virtual_pos):
                    return True
        return False

    def update(self, dt):
        virtual_pos = self.engine.get_mouse_pos()
        for element in self.elements:
            if element.active:
                element.update(dt, virtual_pos)

    def draw(self, surface):
        for element in self.elements:
            if element.visible:
                element.draw(surface)

class Button(UIElement):
    def __init__(self, x, y, w, h, text, on_click=None, color=BLUE, hover_color=None, text_color=WHITE, font_size=24):
        super().__init__(x, y, w, h)
        self.text = text
        self.on_click = on_click
        self.color = color
        self.hover_color = hover_color or (min(color[0]+30, 255), min(color[1]+30, 255), min(color[2]+30, 255))
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size, bold=True)
        self.hovered = False

    def handle_event(self, event, mouse_pos):
        if not self.active or not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                if self.on_click:
                    self.on_click()
                return True
        return False
    
    def update(self, dt, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class Label(UIElement):
    def __init__(self, x, y, text, font_size=24, color=WHITE, center=False):
        self.font = pygame.font.SysFont("Arial", font_size)
        self.text = text
        self.color = color
        self.center = center
        
        surf = self.font.render(text, True, color)
        w, h = surf.get_size()
        if center:
            x -= w // 2
        super().__init__(x, y, w, h)
        
    def set_text(self, text):
        self.text = text
        # Re-calculate rect?
        
    def draw(self, surface):
        surf = self.font.render(self.text, True, self.color)
        surface.blit(surf, self.rect)

class Panel(UIElement):
    def __init__(self, x, y, w, h, color=DARK_GREY):
        super().__init__(x, y, w, h)
        self.color = color
        
    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)

class TextInput(UIElement):
    def __init__(self, x, y, w, h, placeholder="Enter text...", font_size=24):
        super().__init__(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.font = pygame.font.SysFont("Arial", font_size)
        self.active_input = False
        self.cursor_timer = 0
        
    def handle_event(self, event, mouse_pos):
        if not self.active or not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos):
                self.active_input = True
                return True
            else:
                self.active_input = False
                
        elif event.type == pygame.KEYDOWN and self.active_input:
            if event.key == pygame.K_RETURN:
                # self.active_input = False # Keep active for multiple entries?
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Filter for printable characters
                if len(event.unicode) > 0 and event.unicode.isprintable():
                    self.text += event.unicode
            return True
            
        return False
    
    def update(self, dt, mouse_pos):
        self.cursor_timer += dt
        
    def draw(self, surface):
        # Background
        color = WHITE if self.active_input else LIGHT_GREY
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        
        # Text
        display_text = self.text
        text_color = BLACK
        
        if not self.text and not self.active_input:
            display_text = self.placeholder
            text_color = GREY
            
        text_surf = self.font.render(display_text, True, text_color)
        
        # Center vertically, left align with padding
        text_rect = text_surf.get_rect(midleft=(self.rect.left + 10, self.rect.centery))
        surface.blit(text_surf, text_rect)
        
        # Cursor
        if self.active_input and int(self.cursor_timer * 2) % 2 == 0:
            cursor_x = text_rect.right + 2
            pygame.draw.line(surface, BLACK, (cursor_x, self.rect.top + 5), (cursor_x, self.rect.bottom - 5), 2)
