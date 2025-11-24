# Game Module

This directory contains the core logic for the Clash Royale clone. It is divided into several submodules, each responsible for a specific aspect of the game.

## Submodules

-   **`core/`**: Contains the fundamental systems of the game, including the game engine, state managers, and the main game loop.
-   **`entities/`**: Defines the game entities (units, buildings, spells) and handles their rendering and behavior.
-   **`network/`**: Manages network communication for multiplayer matches, including the client-side implementation and the communication protocol.
-   **`scenes/`**: Implements the different scenes of the game, such as the Main Menu, Battle Scene, and Deck Builder.
-   **`ui/`**: Provides a UI framework and components for building the game's user interface.

## Key Files

-   **`assets.py`**: Handles loading and management of game assets (images, sounds, etc.).
-   **`models.py`**: Defines the data models used throughout the game, such as `Player`, `Card`, and `Deck`.
-   **`settings.py`**: Contains global configuration settings and constants for the game (screen resolution, frame rate, game balance values).
-   **`utils.py`**: Provides utility functions and helper classes used across the project.
