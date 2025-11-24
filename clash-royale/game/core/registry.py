from game.settings import UNIT_STATS, SPELL_STATS
from game.core.card import UnitCard, SpellCard

class CardRegistry:
    _cards = {}

    @classmethod
    def initialize(cls):
        """Load all cards from settings."""
        cls._cards.clear()
        
        # Load Units
        for name, stats in UNIT_STATS.items():
            cls._cards[name] = UnitCard(name, stats)
            
        # Load Spells
        for name, stats in SPELL_STATS.items():
            cls._cards[name] = SpellCard(name, stats)

    @classmethod
    def get(cls, name):
        """Get a Card instance by name."""
        if not cls._cards:
            cls.initialize()
        return cls._cards.get(name)

    @classmethod
    def get_all(cls):
        """Get all available cards."""
        if not cls._cards:
            cls.initialize()
        return list(cls._cards.values())
