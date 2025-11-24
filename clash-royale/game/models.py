import pygame
from game.settings import *
from game.core.registry import CardRegistry
import random

class Player:
    def __init__(self, side, deck_names):
        self.side = side # "player" or "enemy"
        self.elixir = 5
        self.elixir_timer = 0
        self.max_elixir = MAX_ELIXIR
        
        # Initialize Deck with Card objects
        self.deck = []
        for name in deck_names:
            card = CardRegistry.get(name)
            if card:
                self.deck.append(card)
            else:
                print(f"Warning: Card {name} not found in registry")
                
        random.shuffle(self.deck)
        
        self.hand = []
        self.next_card = None
        
        # Draw initial hand
        for _ in range(4):
            if self.deck:
                self.hand.append(self.deck.pop(0))
        if self.deck:
            self.next_card = self.deck.pop(0)
            
        self.towers = pygame.sprite.Group()
        
    def update_elixir(self, dt):
        self.elixir_timer += dt
        if self.elixir_timer >= ELIXIR_REGEN_RATE:
            if self.elixir < self.max_elixir:
                self.elixir += 1
            self.elixir_timer = 0
            
    def play_card(self, card_index):
        """
        Plays the card at the given index in hand.
        Returns the played Card object.
        """
        if 0 <= card_index < len(self.hand):
            card = self.hand[card_index]
            
            # Remove played card from hand
            self.hand.pop(card_index)
            
            # Add Next card to hand at the same position
            if self.next_card:
                self.hand.insert(card_index, self.next_card)
                self.next_card = None
            
            # Add played card to bottom of deck
            self.deck.append(card)
            
            # Draw new Next card from top of deck
            if self.deck:
                self.next_card = self.deck.pop(0)
                
            return card
        return None

    def has_elixir(self, cost):
        return self.elixir >= cost

    def spend_elixir(self, cost):
        self.elixir -= cost
