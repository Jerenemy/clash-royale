# Clash Royale Clone

A Python-based clone of the popular mobile game Clash Royale, built using Pygame. This project features a custom game engine, multiplayer networking, and 3D-like rendering using 2D sprites.

## Project Structure

The project is organized into the following directories:

-   `assets/`: Contains game assets (images, etc.).
-   `game/`: The core game logic and modules.
    -   `core/`: Game engine, state management, and core systems.
    -   `entities/`: Game entities, sprites, and rendering logic.
    -   `network/`: Networking client, protocol, and controller.
    -   `scenes/`: Game scenes (Menu, Battle, etc.).
    -   `ui/`: User interface components.
-   `tests/`: Unit tests for various game components.

## Getting Started

### Prerequisites

-   Python 3.x
-   `pip` (Python package installer)

### Installation

1.  Clone the repository.
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Game

To run the game client:

```bash
python main.py
```

### Running the Matchmaking Server

To run the matchmaking server for multiplayer:

```bash
python matchmaking_server.py
```

## Features

-   **Real-time Battles**: Deploy troops and spells to destroy enemy towers.
-   **Multiplayer**: Play against other players over a network.
-   **Deck Building**: Create custom decks from available cards.
-   **3D-like Rendering**: Uses geometric sprites and perspective logic to simulate 3D units.
-   **Physics Engine**: Custom physics for unit movement and collisions.

## Testing

To run the tests:

```bash
pytest
```
