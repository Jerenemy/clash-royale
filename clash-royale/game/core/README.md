# Game Core Module

The `game/core` module contains the fundamental systems that drive the Clash Royale clone.

## Files

-   **`engine.py`**: Contains the `GameEngine` class, which manages the main game loop, window creation, event handling, and scene management. It ensures a fixed timestep update for deterministic game logic.
-   **`managers.py`**: Contains the `BattleManager` class, which is the heart of the gameplay. It handles:
    -   Game state (elixir, towers, units, projectiles).
    -   Input handling (card selection, dragging, playing).
    -   Game rules (win conditions, sudden death, overtime).
    -   Rendering the battle scene (arena, units, HUD).
-   **`card.py`**: Defines the base `Card` class and its subclasses (`UnitCard`, `SpellCard`). It handles card logic, costs, and effects.
-   **`registry.py`**: A simple registry to look up card classes by name.
-   **`scene.py`**: Defines the abstract `Scene` class and the `SceneManager` for transitioning between different game states (Menu, Battle, etc.).
-   **`symmetry.py`**: Provides utilities for handling coordinate transformations and symmetry between the two players (Player vs. Enemy).
