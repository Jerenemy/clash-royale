# Game Entities Module

The `game/entities` module handles the game objects that populate the battlefield, including units, towers, projectiles, and spells.

## Files

-   **`sprites.py`**: Defines the main entity classes:
    -   `Entity`: Base class for all game entities with health and animation support.
    -   `Unit`: Represents mobile units (Knight, Archer, etc.) with AI for movement, targeting, and attacking.
    -   `FlyingUnit`: Subclass of `Unit` for air units that ignore terrain (river).
    -   `Tower`: Represents static defensive structures (King Tower, Princess Towers).
    -   `Projectile`: Base class for projectiles (arrows, fireballs) with movement logic.
    -   `Spell`: Base class for spell effects (Fireball, Arrows, Zap).
-   **`geometric_sprites.py`**: A custom rendering system that procedurally generates sprite images using geometric shapes. This allows for scalable, team-colored assets without needing external image files. It supports:
    -   360-degree rotation for units.
    -   Animation frames (walking, attacking).
    -   Card icons.
-   **`figurine_builder.py`**: A helper module for constructing 3D-like figurines for the geometric renderer. It handles perspective projection and shape assembly.
-   **`particles.py`**: A simple particle system for visual effects like explosions, projectile trails, and hit impacts.
