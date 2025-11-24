import pygame

# Screen settings
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60

# HUD Layout
HUD_HEIGHT = 170#180
CARD_WIDTH = 80
CARD_HEIGHT = 110
CARD_SPACING = 15
CARD_Y_OFFSET = 40 # Relative to HUD top (10px for bar + 15px spacing)

# Grid Settings (Clash Royale Standard)
GRID_WIDTH = 18
GRID_HEIGHT = 32 # Reduced to allow for top/bottom borders (was 24)
# TILE_SIZE = SCREEN_WIDTH // GRID_WIDTH # approx 26.66 -> 26
GRID_MARGIN_Y = 90 # Top and bottom border space
TILE_SIZE = (SCREEN_HEIGHT - HUD_HEIGHT - GRID_MARGIN_Y) // GRID_HEIGHT
GRID_MARGIN_X = (SCREEN_WIDTH - (GRID_WIDTH * TILE_SIZE)) // 2


TITLE = "Clash Royale"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GREY = (100, 100, 100)
GOLD = (255, 215, 0)
LIGHT_GREY = (200, 200, 200)
DARK_GREY = (50, 50, 50)
ORANGE = (255, 165, 0)
RIVER_BLUE = (50, 150, 255)
BRIDGE_BROWN = (139, 69, 19)

# Rarity Colors
RARITY_COMMON = (100, 150, 255)    # Light Blue
RARITY_RARE = (255, 165, 0)        # Orange
RARITY_EPIC = (200, 0, 255)        # Purple
RARITY_LEGENDARY = (0, 255, 255)   # Cyan/Rainbow

# Game Constants
ELIXIR_REGEN_RATE = 2  # Seconds per elixir
MAX_ELIXIR = 10
PUSH_INTENSITY = 0.1 # 0.0 to 1.0, controls how fast units are pushed
PUSH_ALIGNMENT_THRESHOLD = -0.95 # Dot product threshold for centered collision (approx 18 degrees)


# Unit Stats (Placeholder)
# Unit Stats
# Speed: Tiles per second * TILE_SIZE
# Range: Tiles * TILE_SIZE
# Size: Tiles * TILE_SIZE
UNIT_STATS = {
    "knight": {
        "health": 1000,
        "damage": 100,
        "speed": 2.5 * TILE_SIZE, # Was 2 (*20 = 40) -> 2.5 * 16 = 40
        "range": 0.6 * TILE_SIZE, # Was 10 -> 0.625 * 16 = 10
        "attack_speed": 1.2,
        "cost": 3,
        "color": (200, 200, 0),
        "unit_type": "ground",
        "target_type": "ground",
        "count": 1,
        "rarity": "common",
        "size": 1.5 * TILE_SIZE, # Was 25 -> 1.56 * 16 = 25
        "mass": 20
    },
    "archer": {
        "health": 300,
        "damage": 50,
        "speed": 3.75 * TILE_SIZE, # Was 3 (*20 = 60) -> 3.75 * 16 = 60
        "range": 9.0 * TILE_SIZE, # Was 200 -> 12.5 * 16 = 200
        "attack_speed": 1.0,
        "cost": 3,
        "color": (200, 0, 200),
        "unit_type": "ground",
        "target_type": "both",
        "count": 1,
        "rarity": "common",
        "size": 1.25 * TILE_SIZE, # Was 20 -> 1.25 * 16 = 20
        "mass": 10
    },
    "baby_dragon": {
        "health": 800,
        "damage": 80,
        "speed": 3.75 * TILE_SIZE, # Was 3 -> 60
        "range": 6.25 * TILE_SIZE, # Was 100 -> 6.25 * 16 = 100
        "attack_speed": 1.5,
        "cost": 4,
        "color": (255, 100, 0),
        "unit_type": "air",
        "target_type": "both",
        "count": 1,
        "rarity": "epic",
        "size": 1.9 * TILE_SIZE, # Was 30 -> 1.875 * 16 = 30
        "mass": 30
    },
    "minions": {
        "health": 200,
        "damage": 60,
        "speed": 5.0 * TILE_SIZE, # Was 4 (*20 = 80) -> 5 * 16 = 80
        "range": 5.0 * TILE_SIZE, # Was 80 -> 5 * 16 = 80
        "attack_speed": 1.0,
        "cost": 3,
        "color": (100, 100, 255),
        "unit_type": "air",
        "target_type": "both",
        "count": 3,
        "rarity": "common",
        "size": 1.25 * TILE_SIZE, # Was 20
        "mass": 10
    },
    "skeleton_army": {
        "health": 80,
        "damage": 40,
        "speed": 5.0 * TILE_SIZE, # Was 4 -> 80
        "range": 0.3 * TILE_SIZE, # Was 5 -> 0.3125 * 16 = 5
        "attack_speed": 1.5,
        "cost": 3,
        "color": (220, 220, 220),
        "unit_type": "ground",
        "target_type": "ground",
        "count": 15,
        "rarity": "epic",
        "size": 0.9 * TILE_SIZE, # Was 15 -> 0.9375 * 16 = 15
        "mass": 5
    },
    "giant": {
        "health": 3000,
        "damage": 120,
        "speed": 1.25 * TILE_SIZE, # Was 1 (*20 = 20) -> 1.25 * 16 = 20
        "range": 0.6 * TILE_SIZE, # Was 10
        "attack_speed": 1.5,
        "cost": 5,
        "color": (150, 100, 50),
        "unit_type": "ground",
        "target_type": "ground",
        "target_preference": "building",
        "count": 1,
        "rarity": "rare",
        "size": 2.5 * TILE_SIZE, # Was 40 -> 2.5 * 16 = 40
        "mass": 50
    },
    "musketeer": {
        "health": 600,
        "damage": 120,
        "speed": 3.1 * TILE_SIZE, # Was 2.5 (*20 = 50) -> 3.125 * 16 = 50
        "range": 9.0 * TILE_SIZE, # Was 250 -> 15.625 * 16 = 250
        "attack_speed": 1.1,
        "cost": 4,
        "color": (255, 150, 150),
        "unit_type": "ground",
        "target_type": "both",
        "count": 1,
        "rarity": "rare",
        "size": 1.5 * TILE_SIZE, # Was 25
        "mass": 20
    },
    "goblin": {
        "health": 150,
        "damage": 60,
        "speed": 6.25 * TILE_SIZE, # Was 5 (*20 = 100) -> 6.25 * 16 = 100
        "range": 0.3 * TILE_SIZE, # Was 5
        "attack_speed": 1.1,
        "cost": 2,
        "color": (50, 200, 50),
        "unit_type": "ground",
        "target_type": "ground",
        "count": 1,
        "rarity": "common",
        "size": 1.25 * TILE_SIZE, # Was 20
        "mass": 5
    },
    "goblin_gang": {
        "health": 150,
        "damage": 60,
        "speed": 6.25 * TILE_SIZE, # Was 5 -> 100
        "range": 0.3 * TILE_SIZE, # Was 5
        "attack_speed": 1.1,
        "cost": 3,
        "color": (50, 200, 50),
        "unit_type": "ground",
        "target_type": "ground",
        "count": 6,
        "rarity": "rare",
        "size": 1.25 * TILE_SIZE, # Was 20
        "mass": 5
    },
    "wizard": {
        "health": 500,
        "damage": 140,
        "speed": 2.5 * TILE_SIZE, # Was 2 -> 40
        "range": 12.5 * TILE_SIZE, # Was 200
        "attack_speed": 1.4,
        "cost": 5,
        "color": (150, 50, 255),
        "unit_type": "ground",
        "target_type": "both",
        "count": 1,
        "rarity": "legendary",
        "size": 1.5 * TILE_SIZE, # Was 25
        "mass": 20
    },
    "hog_rider": {
        "health": 1200,
        "damage": 150,
        "speed": 7.5 * TILE_SIZE, # Was 6 (*20 = 120) -> 7.5 * 16 = 120
        "range": 0.6 * TILE_SIZE, # Was 10
        "attack_speed": 1.5,
        "cost": 4,
        "color": (255, 100, 50),
        "unit_type": "ground",
        "target_type": "ground",
        "target_preference": "building",
        "count": 1,
        "rarity": "rare",
        "size": 1.9 * TILE_SIZE, # Was 30
        "mass": 25
    },
    "balloon": {
        "health": 1200,
        "damage": 500,
        "speed": 2.5 * TILE_SIZE, # Was 2 -> 40
        "range": 0.6 * TILE_SIZE, # Was 10
        "attack_speed": 3.0,
        "cost": 5,
        "color": (100, 200, 255),
        "unit_type": "air",
        "target_type": "ground",
        "target_preference": "building",
        "count": 1,
        "rarity": "epic",
        "size": 2.2 * TILE_SIZE, # Was 35 -> 2.18 * 16 = 35
        "mass": 30
    },
    "mini_pekka": {
        "health": 1000,
        "damage": 400,
        "speed": 3.75 * TILE_SIZE, # Was 3 -> 60
        "range": 0.6 * TILE_SIZE, # Was 10
        "attack_speed": 1.8,
        "cost": 4,
        "color": (80, 80, 100),
        "unit_type": "ground",
        "target_type": "ground",
        "count": 1,
        "rarity": "rare",
        "size": 1.5 * TILE_SIZE, # Was 25
        "mass": 25
    }
}

# Spell Stats
SPELL_STATS = {
    "fireball": {
        "damage": 400,
        "radius": 6.25 * TILE_SIZE, # Was 100 -> 6.25 * 16 = 100
        "cost": 4,
        "color": (255, 100, 0),
        "duration": 0.5,
        "rarity": "rare"
    },
    "arrows": {
        "damage": 150,
        "radius": 9.4 * TILE_SIZE, # Was 150 -> 9.375 * 16 = 150
        "cost": 3,
        "color": (180, 180, 220),
        "duration": 0.6,
        "rarity": "common"
    },
    "zap": {
        "damage": 200,
        "radius": 7.5 * TILE_SIZE, # Was 120 -> 7.5 * 16 = 120
        "cost": 2,
        "color": (255, 255, 100),
        "duration": 0.3,
        "rarity": "common"
    },
    "poison": {
        "damage": 350,
        "radius": 8.1 * TILE_SIZE, # Was 130 -> 8.125 * 16 = 130
        "cost": 4,
        "color": (100, 255, 100),
        "duration": 1.0,
        "rarity": "epic"
    }
}

# Tower Stats
TOWER_STATS = {
    "princess": {
        "health": 2500,
        "damage": 100,
        "range": 11.6 * TILE_SIZE, # Was 250
        "attack_speed": 0.8,
        "size": int(2.8 * TILE_SIZE) # Already scaled
    },
    "king": {
        "health": 4000,
        "damage": 120,
        "range": 13.6 * TILE_SIZE, # Was 250
        "attack_speed": 1.0,
        "size": int(3.5 * TILE_SIZE) # Already scaled
    }
}

# Tower Visuals
TOWER_HEIGHT_PRINCESS = 30
TOWER_HEIGHT_KING = 30

# Health Bars
HEALTH_BAR_WIDTH = 40
HEALTH_BAR_HEIGHT = 6

# Lane Settings
LANE_LEFT_COL = 3   # 4th column (0, 1, 2 are empty)
LANE_RIGHT_COL = 14 # 15th column (17, 16, 15 are empty)
