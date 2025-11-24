# Game Network Module

The `game/network` module handles all multiplayer networking functionality for the Clash Royale clone.

## Files

-   **`client.py`**: Implements the `NetworkClient` class, which manages the TCP connection to the matchmaking server. It handles:
    -   Connecting and disconnecting.
    -   Joining and leaving the matchmaking queue.
    -   Sending and receiving messages in a separate thread.
    -   Dispatching incoming messages to registered callbacks.
-   **`protocol.py`**: Defines the communication protocol used between the client and server.
    -   `Message`: The standard message container with type, data, and timestamp.
    -   `MessageType`: Enum of available message types (QUEUE_JOIN, MATCH_FOUND, GAME_ACTION, etc.).
    -   `ActionType`: Enum of game actions (PLAY_CARD, EMOTE, etc.).
    -   `encode_message` / `decode_message`: Helper functions for serializing messages to length-prefixed JSON byte strings.
-   **`controller.py`**: Contains the `NetworkController` class, which acts as a bridge between the `BattleManager` (game logic) and the `NetworkClient`. It translates game events into network messages and vice versa.
