# Game Scenes Module

The `game/scenes` module implements the different states or screens of the game.

## Files

-   **`menu.py`**: Implements the `MainMenuScene`, which is the entry point for the user. It provides buttons to navigate to other scenes:
    -   **Multiplayer**: Starts the matchmaking process.
    -   **Practice**: Starts a local single-player game against a simple AI.
    -   **Deck Builder**: Opens the deck customization screen.
    -   **Quit**: Exits the application.
-   **`battle.py`**: Implements the `BattleScene`, which wraps the `BattleManager` to display the actual gameplay. It handles updating the game state and drawing the battle to the screen.
-   **`matchmaking.py`**: Implements the `MatchmakingScene`, which connects to the server and waits for a match to be found. It displays a "Searching..." status and transitions to the `BattleScene` when a match is made.
-   **`builder.py`**: Implements the `DeckBuilderScene`, allowing players to view their card collection and modify their active deck.
