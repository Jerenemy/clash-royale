import uuid
from game.network.protocol import ActionType
from game.core.registry import CardRegistry
from game.core.card import SpellCard

class NetworkController:
    """
    Handles network communication for the BattleManager.
    Uses composition to control the game state based on network messages.
    """
    def __init__(self, battle_manager, client, server_side):
        self.game = battle_manager
        self.client = client
        self.server_side = server_side # "player" or "enemy" from server perspective
        
        # Setup callbacks
        self.client.on_game_action = self.handle_remote_action
        self.client.on_disconnect = self.handle_opponent_disconnect
        
        # Hook into local game actions
        self.game.on_card_played = self.handle_local_card_play

    def update(self, dt):
        """Update network state."""
        self.client.poll_messages()

    def handle_local_card_play(self, card, pos, network_ids, target_tick):
        """
        Called when the local player plays a card.
        We need to send this action to the server.
        """
        is_spell = isinstance(card, SpellCard)
        
        # Send action to opponent
        # We send our LOCAL coordinates. The opponent will flip them.
        action_data = {
            "card_name": card.name,
            "pos_x": pos[0],
            "pos_y": pos[1],
            "side": self.server_side,
            "is_spell": is_spell,
            "network_ids": network_ids,
            "target_tick": target_tick
        }
        
        self.send_action(ActionType.PLAY_CARD, action_data)

    def handle_remote_action(self, action_type, action_data):
        """Handle action received from opponent."""
        if action_type == ActionType.PLAY_CARD.value or action_type == "play_card":
            self._handle_remote_play_card(action_data)
        elif action_type == ActionType.EMOTE.value or action_type == "emote":
            pass # TODO: Handle emotes

    def _handle_remote_play_card(self, data):
        card_name = data.get("card_name")
        pos_x = data.get("pos_x")
        pos_y = data.get("pos_y")
        sender_side = data.get("side")
        network_ids = data.get("network_ids", [])
        target_tick = data.get("target_tick")
        
        print(f"[Network] Received play_card from {sender_side}. My side: {self.server_side}")
        
        # If the sender is us, we need to handle the echo!
        if sender_side == self.server_side:
            print("[Network] Handling Echo - Executing as player")
            self.game.execute_play_card(card_name, (pos_x, pos_y), "player", network_ids, target_tick)
            return

        # Flip coordinates for enemy
        # Enemy played at (x, y) on THEIR screen.
        # On OUR screen, that is (WIDTH - x, HEIGHT - y)
        
        from game.core.symmetry import SymmetryUtils
        spawn_x, spawn_y = SymmetryUtils.flip_pos((pos_x, pos_y))
        
        # Spawn the card for the ENEMY
        self.game.execute_play_card(card_name, (spawn_x, spawn_y), "enemy", network_ids, target_tick)
        

    def send_action(self, action_type, data):
        if hasattr(action_type, "value"):
            action_type = action_type.value
        self.client.send_action(action_type, data)

    def handle_opponent_disconnect(self, reason):
        print(f"Opponent disconnected: {reason}")
        # We could trigger a game over or show a message
        # For now, let's just print it. The BattleManager might need a method to force game over.
        pass
