# Assets Directory

This directory contains the static assets used by the game.

## Contents

-   **`arena_map.png`**: The background image for the battle arena.
-   **`loading_screen.png`**: The image displayed during the game's loading phase.
-   **`menu_background.png`**: The background image for the main menu.

## Note on Sprites

Most game units and towers are rendered procedurally using the `geometric_sprites.py` module in `game/entities/`, so you won't find individual sprite images for them here. This approach allows for:
-   Dynamic team coloring.
-   Smooth rotation.
-   Scalable graphics without pixelation.
