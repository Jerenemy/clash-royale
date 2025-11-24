# Game UI Module

The `game/ui` module provides a simple UI framework for creating user interfaces in Pygame.

## Files

-   **`core.py`**: Defines the core UI classes:
    -   `UIManager`: Manages a collection of UI elements, handling event propagation and rendering.
    -   `UIElement`: Base class for all UI widgets.
    -   `Button`: A clickable button with hover effects and text.
    -   `Label`: A simple text label.
    -   `Panel`: A colored rectangular container.
-   **`multiplayer.py`**: Contains UI components specific to the multiplayer experience, such as status indicators or connection screens.
