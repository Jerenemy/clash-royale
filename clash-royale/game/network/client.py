"""
Network Client for Multiplayer

This module provides the client-side networking component that connects
to the matchmaking server and handles game communication.
"""

import socket
import threading
import queue
import time
from game.network.protocol import (
    Message, MessageType, encode_message, decode_message,
    create_queue_join_message, create_queue_leave_message,
    create_game_action_message, create_disconnect_message
)


class NetworkClient:
    """
    Client-side networking component for multiplayer
    """
    
    def __init__(self, player_id, host='localhost', port=5556):
        """
        Initialize the network client
        
        Args:
            player_id: Unique identifier for this player
            host: Server host address
            port: Server port number
        """
        self.player_id = player_id
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        
        # Message queues
        self.incoming_messages = queue.Queue()
        self.outgoing_messages = queue.Queue()
        
        # Callbacks
        self.on_match_found = None
        self.on_game_action = None
        self.on_disconnect = None
        self.on_error = None
        
        # Threads
        self.send_thread = None
        self.receive_thread = None
        
        print(f"[Client {player_id}] Initialized")
    
    def connect(self):
        """
        Connect to the matchmaking server
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout for connection
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)  # Remove timeout after connection
            
            self.connected = True
            self.running = True
            
            # Start send and receive threads
            self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            
            self.send_thread.start()
            self.receive_thread.start()
            
            print(f"[Client {self.player_id}] Connected to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"[Client {self.player_id}] Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.connected:
            # Send disconnect message
            msg = create_disconnect_message(self.player_id)
            self.send_message(msg)
            
            time.sleep(0.1)  # Give time for message to send
        
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print(f"[Client {self.player_id}] Disconnected")
    
    def join_queue(self, deck):
        """
        Join the matchmaking queue
        
        Args:
            deck: List of card names in the player's deck
        """
        msg = create_queue_join_message(self.player_id, deck)
        self.send_message(msg)
        print(f"[Client {self.player_id}] Joined matchmaking queue")
    
    def leave_queue(self):
        """Leave the matchmaking queue"""
        msg = create_queue_leave_message(self.player_id)
        self.send_message(msg)
        print(f"[Client {self.player_id}] Left matchmaking queue")
    
    def send_action(self, action_type, action_data):
        """
        Send a game action to the opponent
        
        Args:
            action_type: Type of action (from ActionType enum)
            action_data: Dictionary with action-specific data
        """
        msg = create_game_action_message(self.player_id, action_type, action_data)
        self.send_message(msg)
    
    def send_message(self, message):
        """
        Queue a message to be sent
        
        Args:
            message: Message object to send
        """
        if self.connected:
            self.outgoing_messages.put(message)
    
    def poll_messages(self):
        """
        Poll for incoming messages and process them
        
        Returns:
            int: Number of messages processed
        """
        messages_processed = 0
        
        while not self.incoming_messages.empty():
            try:
                message = self.incoming_messages.get_nowait()
                self._handle_message(message)
                messages_processed += 1
            except queue.Empty:
                break
        
        return messages_processed
    
    def _send_loop(self):
        """Thread loop for sending messages"""
        while self.running and self.connected:
            try:
                # Get message from queue with timeout
                message = self.outgoing_messages.get(timeout=0.1)
                
                # Encode and send
                encoded = encode_message(message)
                self.socket.sendall(encoded)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Client {self.player_id}] Send error: {e}")
                self.connected = False
                break
    
    def _receive_loop(self):
        """Thread loop for receiving messages"""
        while self.running and self.connected:
            try:
                # Read message length prefix (4 bytes)
                length_data = self._recv_exact(4)
                if not length_data:
                    break
                
                msg_length = int.from_bytes(length_data, byteorder='big')
                
                # Read message data
                msg_data = self._recv_exact(msg_length)
                if not msg_data:
                    break
                
                # Decode message
                message = decode_message(msg_data)
                if message:
                    self.incoming_messages.put(message)
                
            except Exception as e:
                if self.running:
                    print(f"[Client {self.player_id}] Receive error: {e}")
                break
        
        self.connected = False
        
        # Notify disconnect
        if self.on_disconnect:
            try:
                self.on_disconnect("connection_lost")
            except:
                pass
    
    def _recv_exact(self, num_bytes):
        """
        Receive exact number of bytes from socket
        
        Args:
            num_bytes: Number of bytes to receive
            
        Returns:
            bytes or None if connection closed
        """
        data = b''
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _handle_message(self, message):
        """
        Handle an incoming message
        
        Args:
            message: Message object to handle
        """
        msg_type = message.type
        
        if msg_type == MessageType.MATCH_FOUND.value:
            # Match found - extract opponent info and side
            opponent_id = message.data.get("opponent_id")
            side = message.data.get("side")
            
            print(f"[Client {self.player_id}] Match found! Opponent: {opponent_id}, Side: {side}")
            
            if self.on_match_found:
                self.on_match_found(opponent_id, side)
        
        elif msg_type == MessageType.GAME_ACTION.value:
            # Game action from opponent
            action_type = message.data.get("action_type")
            action_data = message.data.get("action_data")
            
            if self.on_game_action:
                self.on_game_action(action_type, action_data)
        
        elif msg_type == MessageType.DISCONNECT.value:
            # Opponent disconnected
            reason = message.data.get("reason", "unknown")
            
            print(f"[Client {self.player_id}] Disconnect: {reason}")
            
            if self.on_disconnect:
                self.on_disconnect(reason)
        
        elif msg_type == MessageType.ERROR.value:
            # Server error
            error = message.data.get("error", "unknown error")
            
            print(f"[Client {self.player_id}] Server error: {error}")
            
            if self.on_error:
                self.on_error(error)
