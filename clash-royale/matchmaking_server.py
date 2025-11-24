"""
Matchmaking Server for Multiplayer

This server manages the matchmaking queue and coordinates game sessions
between pairs of players.

Run this script directly to start the server:
    python matchmaking_server.py
"""

import socket
import threading
import time
import uuid
from game.network.protocol import (
    Message, MessageType, encode_message, decode_message,
    create_match_found_message, create_error_message, create_disconnect_message
)


class GameSession:
    """Represents an active game between two players"""
    
    def __init__(self, player1_id, player1_conn, player2_id, player2_conn):
        """
        Create a new game session
        
        Args:
            player1_id: ID of first player
            player1_conn: Socket connection for player 1
            player2_id: ID of second player
            player2_conn: Socket connection for player 2
        """
        self.session_id = str(uuid.uuid4())
        self.player1_id = player1_id
        self.player1_conn = player1_conn
        self.player2_id = player2_id
        self.player2_conn = player2_conn
        self.active = True
        self.created_at = time.time()
        
        print(f"[GameSession {self.session_id}] Created: {player1_id} vs {player2_id}")
    
    def route_message(self, from_player_id, message):
        """
        Broadcast a message to BOTH players (Server Echo pattern).
        
        Args:
            from_player_id: ID of sender
            message: Message object to broadcast
        """
        if not self.active:
            return
        
        try:
            # Broadcast to BOTH players for Server Echo
            encoded = encode_message(message)
            
            # Send to player 1
            try:
                self.player1_conn.sendall(encoded)
            except Exception as e:
                print(f"[GameSession {self.session_id}] Error sending to player1: {e}")
            
            # Send to player 2
            try:
                self.player2_conn.sendall(encoded)
            except Exception as e:
                print(f"[GameSession {self.session_id}] Error sending to player2: {e}")
            
        except Exception as e:
            print(f"[GameSession {self.session_id}] Error broadcasting message: {e}")
            self.active = False
    
    def close(self):
        """Close the game session"""
        self.active = False
        print(f"[GameSession {self.session_id}] Closed")



class BroadcastSender:
    """
    Broadcasts server existence via UDP to allow clients to discover it on LAN
    """
    def __init__(self, tcp_port, broadcast_port=5557):
        self.tcp_port = tcp_port
        self.broadcast_port = broadcast_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.running = False
        self.thread = None
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.thread.start()
        print(f"[Broadcast] Started broadcasting on port {self.broadcast_port}")
        
    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
            
    def _get_local_ip(self):
        try:
            # Connect to a public DNS server to determine the most appropriate local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def _broadcast_loop(self):
        message = f"CLASH_ROYALE_SERVER:{self.tcp_port}".encode('utf-8')
        
        # Try to determine the broadcast address dynamically
        # Default to <broadcast> (255.255.255.255)
        broadcast_addrs = ['<broadcast>']
        
        try:
            local_ip = self._get_local_ip()
            if local_ip != "127.0.0.1":
                # Assuming /24 subnet for simplicity (common for home/hotspots)
                # This is a heuristic: replace last octet with 255
                parts = local_ip.split('.')
                subnet_broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                broadcast_addrs.append(subnet_broadcast)
                print(f"[Broadcast] Local IP: {local_ip}, Target Broadcast: {subnet_broadcast}")
        except Exception as e:
            print(f"[Broadcast] Error determining subnet: {e}")

        while self.running:
            sent = False
            for addr in broadcast_addrs:
                try:
                    self.sock.sendto(message, (addr, self.broadcast_port))
                    sent = True
                except Exception as e:
                    # Don't spam errors for every attempt, but log if all fail
                    pass
            
            if not sent and self.running:
                 # If we couldn't send to any, log the last error or generic
                 # print(f"[Broadcast] Failed to send broadcast")
                 pass
                 
            time.sleep(1)  # Broadcast every 1 second


class MatchmakingServer:
    """
    Matchmaking server that manages player queues and game sessions
    """
    
    def __init__(self, host='0.0.0.0', port=5556):
        """
        Initialize the matchmaking server
        
        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        # Queue of waiting players
        self.queue = []  # List of (player_id, connection, deck)
        self.queue_lock = threading.Lock()
        
        # Active game sessions
        self.sessions = {}  # session_id -> GameSession
        self.sessions_lock = threading.Lock()
        
        # Player to session mapping
        self.player_sessions = {}  # player_id -> session_id
        
        # LAN Discovery
        self.broadcaster = BroadcastSender(port)
        
        print(f"[Server] Initializing on {host}:{port}")
    
    def start(self):
        """Start the matchmaking server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"[Server] Listening on {self.host}:{self.port}")
        
        # Start broadcaster
        self.broadcaster.start()
        
        # Start accept thread
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()
        
        # Start matchmaking thread
        matchmaking_thread = threading.Thread(target=self._matchmaking_loop, daemon=True)
        matchmaking_thread.start()
    
    def stop(self):
        """Stop the matchmaking server"""
        print("[Server] Shutting down...")
        self.running = False
        
        if self.broadcaster:
            self.broadcaster.stop()
        
        if self.server_socket:
            self.server_socket.close()
        
        # Close all sessions
        with self.sessions_lock:
            for session in self.sessions.values():
                session.close()
    
    def _accept_connections(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[Server] New connection from {address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"[Server] Error accepting connection: {e}")
    
    def _handle_client(self, client_socket, address):
        """
        Handle communication with a connected client
        
        Args:
            client_socket: Socket connection to client
            address: Client address tuple
        """
        player_id = None
        
        try:
            while self.running:
                # Read message length prefix (4 bytes)
                length_data = self._recv_exact(client_socket, 4)
                if not length_data:
                    break
                
                msg_length = int.from_bytes(length_data, byteorder='big')
                
                # Read message data
                msg_data = self._recv_exact(client_socket, msg_length)
                if not msg_data:
                    break
                
                # Decode message
                message = decode_message(msg_data)
                if not message:
                    continue
                
                # Handle message based on type
                if message.type == MessageType.QUEUE_JOIN.value:
                    player_id = message.data.get("player_id")
                    deck = message.data.get("deck", [])
                    self._add_to_queue(player_id, client_socket, deck)
                    print(f"[Server] Player {player_id} joined queue")
                
                elif message.type == MessageType.QUEUE_LEAVE.value:
                    player_id = message.data.get("player_id")
                    self._remove_from_queue(player_id)
                    print(f"[Server] Player {player_id} left queue")
                
                elif message.type == MessageType.GAME_ACTION.value:
                    # Route game action to opponent
                    sender_id = message.data.get("player_id")
                    self._route_game_message(sender_id, message)
                
                elif message.type == MessageType.DISCONNECT.value:
                    player_id = message.data.get("player_id")
                    print(f"[Server] Player {player_id} disconnected")
                    break
                
        except Exception as e:
            print(f"[Server] Error handling client {address}: {e}")
        
        finally:
            # Clean up on disconnect
            if player_id:
                self._remove_from_queue(player_id)
                self._handle_player_disconnect(player_id)
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"[Server] Client {address} connection closed")
    
    def _recv_exact(self, sock, num_bytes):
        """
        Receive exact number of bytes from socket
        
        Args:
            sock: Socket to receive from
            num_bytes: Number of bytes to receive
            
        Returns:
            bytes or None if connection closed
        """
        data = b''
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _add_to_queue(self, player_id, connection, deck):
        """Add a player to the matchmaking queue"""
        with self.queue_lock:
            # Check if already in queue
            for pid, _, _ in self.queue:
                if pid == player_id:
                    return
            
            self.queue.append((player_id, connection, deck))
    
    def _remove_from_queue(self, player_id):
        """Remove a player from the matchmaking queue"""
        with self.queue_lock:
            self.queue = [(pid, conn, deck) for pid, conn, deck in self.queue if pid != player_id]
    
    def _matchmaking_loop(self):
        """Continuously check for matches in the queue"""
        while self.running:
            time.sleep(0.5)  # Check every 500ms
            
            with self.queue_lock:
                if len(self.queue) >= 2:
                    # Match first two players in queue
                    player1_id, player1_conn, player1_deck = self.queue.pop(0)
                    player2_id, player2_conn, player2_deck = self.queue.pop(0)
                    
                    # Create match in separate thread to not block queue
                    match_thread = threading.Thread(
                        target=self._create_match,
                        args=(player1_id, player1_conn, player1_deck, 
                              player2_id, player2_conn, player2_deck),
                        daemon=True
                    )
                    match_thread.start()
    
    def _create_match(self, player1_id, player1_conn, player1_deck,
                     player2_id, player2_conn, player2_deck):
        """
        Create a match between two players
        
        Args:
            player1_id: ID of first player
            player1_conn: Connection for player 1
            player1_deck: Deck for player 1
            player2_id: ID of second player
            player2_conn: Connection for player 2
            player2_deck: Deck for player 2
        """
        print(f"[Server] Creating match: {player1_id} vs {player2_id}")
        
        # Create game session
        session = GameSession(player1_id, player1_conn, player2_id, player2_conn)
        
        with self.sessions_lock:
            self.sessions[session.session_id] = session
            self.player_sessions[player1_id] = session.session_id
            self.player_sessions[player2_id] = session.session_id
        
        # Send match found messages
        try:
            # Player 1 controls bottom (player side)
            msg1 = create_match_found_message(player1_id, player2_id, "player")
            player1_conn.sendall(encode_message(msg1))
            
            # Player 2 controls top (enemy side, but from their perspective)
            msg2 = create_match_found_message(player2_id, player1_id, "enemy")
            player2_conn.sendall(encode_message(msg2))
            
            print(f"[Server] Match started: {session.session_id}")
            
        except Exception as e:
            print(f"[Server] Error starting match: {e}")
            session.close()
            
            with self.sessions_lock:
                if session.session_id in self.sessions:
                    del self.sessions[session.session_id]
                if player1_id in self.player_sessions:
                    del self.player_sessions[player1_id]
                if player2_id in self.player_sessions:
                    del self.player_sessions[player2_id]
    
    def _route_game_message(self, sender_id, message):
        """Route a game message to the appropriate session"""
        session_id = self.player_sessions.get(sender_id)
        
        if not session_id:
            return
        
        with self.sessions_lock:
            session = self.sessions.get(session_id)
            if session and session.active:
                session.route_message(sender_id, message)
    
    def _handle_player_disconnect(self, player_id):
        """Handle a player disconnecting"""
        session_id = self.player_sessions.get(player_id)
        
        if not session_id:
            return
        
        with self.sessions_lock:
            session = self.sessions.get(session_id)
            if session:
                # Notify other player
                disconnect_msg = create_disconnect_message(player_id, "opponent_disconnected")
                
                try:
                    if player_id == session.player1_id:
                        session.player2_conn.sendall(encode_message(disconnect_msg))
                    else:
                        session.player1_conn.sendall(encode_message(disconnect_msg))
                except:
                    pass
                
                session.close()
                
                # Clean up
                if session.session_id in self.sessions:
                    del self.sessions[session.session_id]
            
            if player_id in self.player_sessions:
                del self.player_sessions[player_id]


def main():
    """Run the matchmaking server"""
    server = MatchmakingServer()
    server.start()
    
    print("[Server] Press Ctrl+C to stop")
    
    try:
        # Keep server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Server] Received shutdown signal")
        server.stop()


if __name__ == "__main__":
    main()
