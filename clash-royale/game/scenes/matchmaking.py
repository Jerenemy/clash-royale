import pygame
import uuid
from game.core.scene import Scene
from game.ui.multiplayer import MatchmakingScreen, MatchFoundAnimation
from game.network.discovery import ServerDiscovery
from game.network.client import NetworkClient
from game.utils import load_deck
from game.scenes.battle import BattleScene
from game.assets import assets

class MatchmakingScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.screen_ui = MatchmakingScreen(engine)
        self.player_id = str(uuid.uuid4())
        self.client = None # Initialize lazily after discovery
        self.match_found_anim = None
        self.connected = False
        self.discovery = ServerDiscovery()

    def enter(self, params=None):
        # Try to discover server first
        print("[Matchmaking] Looking for server...")
        server_info = self.discovery.find_server()
        
        if server_info:
            host, port = server_info
            print(f"[Matchmaking] Connecting to discovered server at {host}:{port}")
            self.connect_to_server(host, port)
        else:
            print("[Matchmaking] No server found, showing manual entry")
            self.screen_ui.show_manual_entry()

    def connect_to_server(self, host, port):
        self.client = NetworkClient(self.player_id, host=host, port=port)
        
        if self.client.connect():
            self.connected = True
            self.client.on_match_found = self.on_match_found
            self.client.join_queue(load_deck())
            self.screen_ui.set_status("Connected! Waiting for opponent")
        else:
            print(f"Failed to connect to server at {host}:{port}")
            self.screen_ui.set_status(f"Connection failed to {host}")

    def exit(self):
        if self.client and self.client.connected and not self.match_found_anim:
             pass

    def on_match_found(self, opponent_id, side):
        self.match_found_anim = MatchFoundAnimation(opponent_id)
        self.opponent_id = opponent_id
        self.side = side

    def handle_event(self, event):
        result = self.screen_ui.handle_event(event)
        
        if result == "cancel":
            if self.client:
                self.client.leave_queue()
                self.client.disconnect()
            self.manager.pop()
            
        elif result == "connect":
            ip = self.screen_ui.get_entered_ip()
            if ip:
                self.screen_ui.set_status(f"Connecting to {ip}...")
                # We need to do this in update or thread to not block UI? 
                # For now, synchronous connect is fine as it has timeout
                self.connect_to_server(ip, 5556)

    def update(self, dt):
        self.screen_ui.update(dt)
        if self.connected:
            self.client.poll_messages()

        if self.match_found_anim:
            if self.match_found_anim.update(dt):
                # Animation done, start game
                from game.core.managers import BattleManager
                from game.network.controller import NetworkController
                
                # Create BattleManager
                battle_manager = BattleManager(self.engine)
                
                # Create NetworkController
                controller = NetworkController(battle_manager, self.client, self.side)
                
                # Hack: Pop self, then push Battle.
                self.manager.pop() 
                self.manager.push(BattleScene(self.engine, battle_manager, controller))

    def draw(self, screen):
        # Draw background
        screen.blit(assets.get_image("loading_screen"), (0, 0))
        
        self.screen_ui.draw(screen)
        
        if self.match_found_anim:
            self.match_found_anim.draw(screen)
