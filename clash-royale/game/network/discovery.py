import socket
import threading
import time

class ServerDiscovery:
    """
    Discovers game servers on the local network via UDP broadcast
    """
    def __init__(self, broadcast_port=5557, timeout=3.0):
        self.broadcast_port = broadcast_port
        self.timeout = timeout
        self.found_server = None
        self.running = False
        self.sock = None
        
    def find_server(self):
        """
        Listen for server broadcasts for a short period
        
        Returns:
            tuple: (ip, port) of found server, or None if not found
        """
        self.running = True
        self.found_server = None
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind to all interfaces on the broadcast port
            self.sock.bind(('', self.broadcast_port))
            self.sock.settimeout(self.timeout)
            
            print(f"[Discovery] Listening for servers on port {self.broadcast_port}...")
            
            start_time = time.time()
            while self.running and (time.time() - start_time < self.timeout):
                try:
                    data, addr = self.sock.recvfrom(1024)
                    message = data.decode('utf-8')
                    
                    if message.startswith("CLASH_ROYALE_SERVER:"):
                        # Parse server info
                        try:
                            tcp_port = int(message.split(":")[1])
                            server_ip = addr[0]
                            print(f"[Discovery] Found server at {server_ip}:{tcp_port}")
                            self.found_server = (server_ip, tcp_port)
                            return self.found_server
                        except ValueError:
                            continue
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[Discovery] Error receiving: {e}")
                    break
                    
        except Exception as e:
            print(f"[Discovery] Error binding: {e}")
        finally:
            if self.sock:
                self.sock.close()
            self.running = False
            
        return None
