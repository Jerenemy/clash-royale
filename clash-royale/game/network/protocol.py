# network_protocol.py
"""
Defines the message protocol used between the client and the matchmaking server.
All messages are JSON objects with the following structure:
    {
        "type": "MESSAGE_TYPE",
        "data": {...},
        "timestamp": <float unix time>
    }
The helper functions encode_message and decode_message handle serialization.
"""

import json
import time
from enum import Enum
from typing import Any, Dict

# Message Types
MSG_QUEUE_JOIN = "QUEUE_JOIN"
MSG_QUEUE_LEAVE = "QUEUE_LEAVE"
MSG_MATCH_FOUND = "MATCH_FOUND"
MSG_GAME_ACTION = "GAME_ACTION"
MSG_DISCONNECT = "DISCONNECT"
MSG_HEARTBEAT = "HEARTBEAT"
MSG_ERROR = "ERROR"

class MessageType(Enum):
    """Types of messages exchanged between client and server"""
    QUEUE_JOIN = MSG_QUEUE_JOIN
    QUEUE_LEAVE = MSG_QUEUE_LEAVE
    MATCH_FOUND = MSG_MATCH_FOUND
    GAME_ACTION = MSG_GAME_ACTION
    DISCONNECT = MSG_DISCONNECT
    HEARTBEAT = MSG_HEARTBEAT
    ERROR = MSG_ERROR

class ActionType(Enum):
    """Types of game actions that can be synchronized"""
    PLAY_CARD = "play_card"
    SPAWN_UNIT = "spawn_unit"
    CAST_SPELL = "cast_spell"
    TOWER_HEALTH = "tower_health"
    EMOTE = "emote"

class Message:
    """Represents a network message"""

    def __init__(self, msg_type: MessageType | str, data: Dict[str, Any] | None = None):
        """
        Create a new message

        Args:
            msg_type: MessageType enum value or raw string
            data: Optional dictionary with message payload
        """
        self.type = msg_type if isinstance(msg_type, str) else msg_type.value
        self.data = data or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        msg = cls(d["type"], d.get("data", {}))
        msg.timestamp = d.get("timestamp", time.time())
        return msg

def encode_message(message: Message) -> bytes:
    """
    Serialize a Message object to a length‑prefixed byte string.
    Returns:
        bytes: 4‑byte big‑endian length prefix + UTF‑8 JSON payload.
    """
    payload = json.dumps(message.to_dict()).encode("utf-8")
    length_prefix = len(payload).to_bytes(4, byteorder="big")
    return length_prefix + payload

def decode_message(raw: bytes) -> Message:
    """
    Deserialize a raw JSON payload (without length prefix) into a Message.
    """
    try:
        obj = json.loads(raw.decode("utf-8"))
        return Message.from_dict(obj)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
        print(f"Error decoding message: {e}")
        raise

# Factory helpers
def create_queue_join_message(player_id: str, deck: list) -> Message:
    return Message(MessageType.QUEUE_JOIN, {"player_id": player_id, "deck": deck})

def create_queue_leave_message(player_id: str) -> Message:
    return Message(MessageType.QUEUE_LEAVE, {"player_id": player_id})

def create_match_found_message(player_id: str, opponent_id: str, side: str) -> Message:
    return Message(
        MessageType.MATCH_FOUND,
        {"player_id": player_id, "opponent_id": opponent_id, "side": side},
    )

def create_game_action_message(player_id: str, action_type: ActionType | str, action_data: dict) -> Message:
    at = action_type if isinstance(action_type, str) else action_type.value
    return Message(
        MessageType.GAME_ACTION,
        {"player_id": player_id, "action_type": at, "action_data": action_data},
    )

def create_disconnect_message(player_id: str, reason: str = "") -> Message:
    return Message(MessageType.DISCONNECT, {"player_id": player_id, "reason": reason})

def create_heartbeat_message(player_id: str) -> Message:
    return Message(MessageType.HEARTBEAT, {"player_id": player_id})

def create_error_message(error_msg: str) -> Message:
    return Message(MessageType.ERROR, {"error": error_msg})
