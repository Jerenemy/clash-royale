from game.settings import *

class Card:
    """Base class for all cards."""
    def __init__(self, name, cost, rarity="common", description=""):
        self.name = name
        self.cost = cost
        self.rarity = rarity
        self.description = description

    def play(self, manager, pos, side, network_ids=None):
        """
        Execute the card's effect.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

class UnitCard(Card):
    """Card that spawns units."""
    def __init__(self, name, stats):
        super().__init__(name, stats["cost"])
        self.stats = stats
        self.count = stats.get("count", 1)
        self.unit_type = stats.get("unit_type", "ground")

    def play(self, manager, pos, side, network_ids=None):
        # Ensure we have enough IDs
        if network_ids is None:
            network_ids = [None] * self.count
        
        if self.count == 1:
            self._spawn_single(manager, pos, side, network_ids[0])
        else:
            self._spawn_swarm(manager, pos, side, network_ids)

    def _spawn_single(self, manager, pos, side, network_id):
        if self.unit_type == "air":
            from game.entities.sprites import FlyingUnit
            FlyingUnit(manager, pos[0], pos[1], self.name, side, network_id)
        else:
            from game.entities.sprites import Unit
            Unit(manager, pos[0], pos[1], self.name, side, network_id)

    def _spawn_swarm(self, manager, pos, side, network_ids):
        import math
        radius = 30
        for i in range(self.count):
            from game.core.symmetry import SymmetryUtils
            angle = (2 * math.pi / self.count) * i
            
            # Rotate formation for enemy
            angle = SymmetryUtils.transform_formation_angle(angle, side)
                
            offset_x = math.cos(angle) * radius
            offset_y = math.sin(angle) * radius
            spawn_x = pos[0] + offset_x
            spawn_y = pos[1] + offset_y
            
            nid = network_ids[i] if i < len(network_ids) else None
            self._spawn_single(manager, (spawn_x, spawn_y), side, nid)

class SpellCard(Card):
    """Card that casts a spell."""
    def __init__(self, name, stats):
        super().__init__(name, stats["cost"])
        self.stats = stats

    def play(self, manager, pos, side, network_ids=None):
        from game.entities.sprites import FireballSpell, ArrowsSpell, ZapSpell, Spell
        
        if self.name == "fireball":
            FireballSpell(manager, pos[0], pos[1], side)
        elif self.name == "arrows":
            ArrowsSpell(manager, pos[0], pos[1], side)
        elif self.name == "zap":
            ZapSpell(manager, pos[0], pos[1], side)
        else:
            Spell(manager, pos[0], pos[1], self.name, side)
