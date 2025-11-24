"""
Multiplayer UI Components

This module provides UI components for the multiplayer matchmaking experience.
"""

import pygame
import math
from game.settings import *
from game.ui.core import UIManager, Button, Label, TextInput

class MatchmakingScreen:
    """
    UI screen shown while searching for an opponent
    """
    
    def __init__(self, engine):
        """
        Initialize the matchmaking screen
        
        Args:
            engine: GameEngine instance
        """
        self.engine = engine
        self.screen = engine.virtual_surface
        self.ui = UIManager(engine)
        
        self.animation_timer = 0
        self.status_text = "Searching for opponent"
        self.queue_position = None
        
        # Title
        self.ui.add(Label(SCREEN_WIDTH // 2, 100, "Matchmaking", font_size=48, color=BLACK, center=True))
        
        # Status Label
        self.status_label = Label(SCREEN_WIDTH // 2, 200, self.status_text, font_size=32, color=BLACK, center=True)
        self.ui.add(self.status_label)
        
        # Queue Position Label
        self.queue_label = Label(SCREEN_WIDTH // 2, 250, "", font_size=24, color=BLACK, center=True)
        self.ui.add(self.queue_label)
        
        # Manual IP Entry UI (Hidden by default)
        self.ip_input = TextInput(SCREEN_WIDTH // 2 - 150, 300, 300, 40, placeholder="Enter Server IP")
        self.ip_input.visible = False
        self.ip_input.active = False
        self.ui.add(self.ip_input)
        
        self.connect_btn = Button(SCREEN_WIDTH // 2 - 60, 360, 120, 40, "Connect", on_click=self.on_connect)
        self.connect_btn.visible = False
        self.connect_btn.active = False
        self.ui.add(self.connect_btn)
        
        self.connect_clicked = False
        
        # Cancel button
        self.cancel_clicked = False
        self.ui.add(Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 150, 200, 50, "Cancel", 
                           on_click=self.on_cancel, color=RED))
        
    def on_cancel(self):
        self.cancel_clicked = True
        
    def on_connect(self):
        self.connect_clicked = True
    
    def show_manual_entry(self):
        self.status_text = "Discovery failed. Enter IP:"
        self.ip_input.visible = True
        self.ip_input.active = True
        self.connect_btn.visible = True
        self.connect_btn.active = True
        
    def get_entered_ip(self):
        return self.ip_input.text
    
    def handle_event(self, event):
        """
        Handle UI events
        
        Args:
            event: Pygame event
            
        Returns:
            str: Action to take ("cancel", "connect", or None)
        """
        self.ui.handle_event(event)
        
        if self.cancel_clicked:
            self.cancel_clicked = False
            return "cancel"
            
        if self.connect_clicked:
            self.connect_clicked = False
            return "connect"
            
        return None
    
    def update(self, dt):
        """
        Update animation
        
        Args:
            dt: Delta time in seconds
        """
        self.animation_timer += dt
        self.ui.update(dt)
        
        # Animate dots only if NOT in manual entry mode
        if not self.ip_input.visible:
            dots = "." * (int(self.animation_timer * 2) % 4)
            self.status_label.set_text(f"{self.status_text}{dots}")
        else:
            self.status_label.set_text(self.status_text)
        
        if self.queue_position:
            self.queue_label.set_text(f"Position in queue: {self.queue_position}")
            self.queue_label.visible = True
        else:
            self.queue_label.visible = False
    
    def set_status(self, status):
        self.status_text = status
    
    def set_queue_position(self, position):
        self.queue_position = position
    
    def draw(self, screen):
        """Draw the matchmaking screen"""
        screen.fill(LIGHT_GREY)
        
        # Draw spinning circle or something?
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        radius = 50
        angle = self.animation_timer * 5
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        pygame.draw.circle(self.screen, BLUE, (int(x), int(y)), 10)
        
        self.ui.draw(self.screen)


class MatchFoundAnimation:
    """
    Animation shown when a match is found
    """
    def __init__(self, opponent_name):
        self.opponent_name = opponent_name
        self.timer = 0
        self.duration = 2.0 # 2 seconds animation
        self.font_big = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 32)
        
    def update(self, dt):
        self.timer += dt
        return self.timer >= self.duration
        
    def draw(self, screen):
        # Fade out background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Text
        text = self.font_big.render("MATCH FOUND!", True, GOLD)
        rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        
        # Scale effect
        scale = min(1.0, self.timer * 2)
        if scale < 1.0:
            w = int(rect.width * scale)
            h = int(rect.height * scale)
            scaled_text = pygame.transform.scale(text, (w, h))
            rect = scaled_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(scaled_text, rect)
        else:
            screen.blit(text, rect)
            
        # Opponent name
        if self.timer > 0.5:
            text_vs = self.font_small.render(f"VS {self.opponent_name}", True, WHITE)
            rect_vs = text_vs.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(text_vs, rect_vs)
