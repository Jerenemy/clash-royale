import pygame
import json
import os

DECK_FILE = "deck.json"
DEFAULT_DECK = ["knight", "archer", "knight", "archer", "knight", "archer", "knight", "archer"]

def load_image(path):
    # Placeholder for asset loading
    pass

def save_deck(deck):
    try:
        with open(DECK_FILE, "w") as f:
            json.dump(deck, f)
    except Exception as e:
        print(f"Error saving deck: {e}")

def load_deck():
    from game.settings import UNIT_STATS, SPELL_STATS
    valid_cards = set(UNIT_STATS.keys()) | set(SPELL_STATS.keys())
    
    if not os.path.exists(DECK_FILE):
        return DEFAULT_DECK
    
    try:
        with open(DECK_FILE, "r") as f:
            deck = json.load(f)
            # Basic validation: ensure list of strings
            if isinstance(deck, list) and all(isinstance(card, str) for card in deck):
                # Filter out invalid cards
                valid_deck = [card for card in deck if card in valid_cards]
                
                # Ensure exactly 8 cards, fill with default if needed
                if len(valid_deck) < 8:
                    valid_deck.extend(DEFAULT_DECK[:8-len(valid_deck)])
                return valid_deck[:8] # truncate if too long
            else:
                return DEFAULT_DECK
    except Exception as e:
        print(f"Error loading deck: {e}")
        return DEFAULT_DECK
