#!/usr/bin/env python3
"""
Multi-Room File Sharing System - UDP Notification Server
Handles real-time notifications and user presence tracking
"""

import socket
import threading
import json
import time
from datetime import datetime

class NotificationServer:
    def __init__(self, host='127.0.0.1', port=65433):
        self.host = host
        self.port = port
        self.clients = {}  # client_id -> {'address': (ip, port), 'username': str, 'room': str, 'last_heartbeat': float}
        self.rooms = {
            'general': set()  # set of client_ids
        }
        self.client_id_counter = 0
        self.running = True
        self.server_socket = None
        self.cleanup_thread = None
        
    def start_server(self):
        """Start the UDP notification server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(1.0)  # Set timeout for periodic cleanup
        
        print(f"🟢 [UDP SERVER] Started on {self.host}:{self.port}")
        print("🟢 [UDP SERVER] Waiting for notification messages...")
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self.cleanup_inactive_clients)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
        
        try:
            while self.running:
                try:
                    data, addr = self.server_socket.recvfrom(4096)
                    print(f"🟢 [UDP SERVER] Received from {addr}: {data}")  # Debug
                    
                    try:
                        message = json.loads(data.decode('utf-8'))
                        print(f"🟢 [UDP SERVER] Parsed message: {message}")  # Debug
                        self.process_message(message, addr, self.server_socket)
                    except json.JSONDecodeError:
                        print(f"🔴 [UDP SERVER] Invalid JSON from {addr}")
                        
                except socket.timeout:
                    continue  # Periodic timeout for cleanup
                except Exception as e:
                    if self.running:  # Only log if we're supposed to be running
                        print(f"Error receiving message: {e}")
                    
        except KeyboardInterrupt:
            print("\nNotification server shutting down...")
        finally:
            self.shutdown_server()
            
    def shutdown_server(self):
        """Clean shutdown of the UDP server"""
        print("🔴 [UDP SERVER] Shutting down...")
        self.running = False
        
        # Clear all clients
        client_ids = list(self.clients.keys())
        for client_id in client_ids:
            self.remove_client(client_id)
            
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        print("🔴 [UDP SERVER] Server shutdown complete")
        
    def process_message(self, message, addr, server_socket):
        """Process incoming notification message"""
        print(f"🟢 [UDP SERVER] Processing message: {message}")  # Debug
        msg_type = message.get('type')
        client_id = message.get('client_id')
        
        if msg_type == 'register':
            # Register new client
            username = message.get('username', 'Anonymous')
            room = message.get('room', 'general')
            client_udp_port = message.get('udp_port')  # Get the client's UDP port
            
            if client_id not in self.clients:
                self.client_id_counter += 1
                if not client_id:
                    client_id = f"client_{self.client_id_counter}"
                    
            # Update the client's address to include the correct UDP port
            if client_udp_port:
                client_addr = (addr[0], client_udp_port)
            else:
                client_addr = addr
                
            self.clients[client_id] = {
                'address': client_addr,
                'username': username,
                'room': room,
                'last_heartbeat': time.time()
            }
            
            # Add to room
            if room not in self.rooms:
                self.rooms[room] = set()
            self.rooms[room].add(client_id)
            
            # Broadcast welcome message to all clients in room (including new user)
            welcome_msg = {
                'type': 'notification',
                'message': f'{username} joined the room',
                'room': room,
                'timestamp': datetime.now().isoformat(),
                'users': self.get_room_users(room)
            }
            self.broadcast_to_room(room, welcome_msg, server_socket)
            
            # Send current room info to new client specifically
            room_info = {
                'type': 'room_info',
                'room': room,
                'users': self.get_room_users(room),
                'timestamp': datetime.now().isoformat()
            }
            self.send_to_client(client_id, room_info, server_socket)
            
        elif msg_type == 'unregister':
            # Handle client unregistration
            if client_id in self.clients:
                self.remove_client(client_id)
                
        elif msg_type == 'heartbeat':
            # Update client heartbeat
            if client_id in self.clients:
                self.clients[client_id]['last_heartbeat'] = time.time()
                
        elif msg_type == 'join_room':
            # Handle room change
            new_room = message.get('room')
            if client_id in self.clients and new_room:
                old_room = self.clients[client_id]['room']
                username = self.clients[client_id]['username']
                
                # Leave old room
                if old_room in self.rooms:
                    self.rooms[old_room].discard(client_id)
                    leave_msg = {
                        'type': 'notification',
                        'message': f'{username} left the room',
                        'room': old_room,
                        'timestamp': datetime.now().isoformat(),
                        'users': self.get_room_users(old_room)
                    }
                    self.broadcast_to_room(old_room, leave_msg, server_socket)
                
                # Join new room
                self.clients[client_id]['room'] = new_room
                if new_room not in self.rooms:
                    self.rooms[new_room] = set()
                self.rooms[new_room].add(client_id)
                
                # Broadcast join message to all clients in room (including new user)
                join_msg = {
                    'type': 'notification',
                    'message': f'{username} joined the room',
                    'room': new_room,
                    'timestamp': datetime.now().isoformat(),
                    'users': self.get_room_users(new_room)
                }
                self.broadcast_to_room(new_room, join_msg, server_socket)
                
                # Send room info to new client specifically
                room_info = {
                    'type': 'room_info',
                    'room': new_room,
                    'users': self.get_room_users(new_room),
                    'timestamp': datetime.now().isoformat()
                }
                self.send_to_client(client_id, room_info, server_socket)
                
        elif msg_type == 'file_notification':
            # Broadcast file activity
            if client_id in self.clients:
                room = self.clients[client_id]['room']
                username = self.clients[client_id]['username']
                action = message.get('action')  # 'upload', 'download'
                filename = message.get('filename')
                
                notification = {
                    'type': 'notification',
                    'message': f'{username} {action}ed {filename}',
                    'room': room,
                    'timestamp': datetime.now().isoformat(),
                    'users': self.get_room_users(room)
                }
                self.broadcast_to_room(room, notification, server_socket)
                
        elif msg_type == 'chat_message':
            # Handle chat messages (optional feature)
            if client_id in self.clients:
                room = self.clients[client_id]['room']
                username = self.clients[client_id]['username']
                chat_content = message.get('message', '')
                
                chat_msg = {
                    'type': 'chat',
                    'username': username,
                    'message': chat_content,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                }
                self.broadcast_to_room(room, chat_msg, server_socket)
                
    def get_room_users(self, room):
        """Get list of users in a room"""
        users = []
        if room in self.rooms:
            for client_id in self.rooms[room]:
                if client_id in self.clients:
                    users.append(self.clients[client_id]['username'])
        return users
        
    def broadcast_to_room(self, room, message, server_socket, exclude_client=None):
        """Broadcast message to all clients in a room"""
        if room not in self.rooms:
            return
            
        message_json = json.dumps(message).encode('utf-8')
        
        for client_id in self.rooms[room].copy():
            if client_id != exclude_client and client_id in self.clients:
                self.send_to_client(client_id, message_json, server_socket)
                
    def send_to_client(self, client_id, message, server_socket):
        """Send message to specific client"""
        if client_id in self.clients:
            client = self.clients[client_id]
            addr = client['address']
            
            try:
                if isinstance(message, str):
                    message = message.encode('utf-8')
                elif isinstance(message, dict):
                    message = json.dumps(message).encode('utf-8')
                    
                server_socket.sendto(message, addr)
            except Exception as e:
                print(f"Failed to send to {client_id}: {e}")
                # Remove inactive client
                self.remove_client(client_id)
                
    def cleanup_inactive_clients(self):
        """Remove inactive clients (no heartbeat for 30 seconds)"""
        while self.running:
            try:
                current_time = time.time()
                inactive_clients = []
                
                for client_id, client in self.clients.items():
                    if current_time - client['last_heartbeat'] > 30:
                        inactive_clients.append(client_id)
                        
                for client_id in inactive_clients:
                    self.remove_client(client_id)
                    
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Cleanup error: {e}")
                
    def remove_client(self, client_id):
        """Remove client from all rooms and client list"""
        if client_id in self.clients:
            client = self.clients[client_id]
            room = client['room']
            username = client['username']
            
            # Remove from room
            if room in self.rooms:
                self.rooms[room].discard(client_id)
                
            # Remove client
            del self.clients[client_id]
            print(f"Client {client_id} ({username}) removed due to inactivity")

if __name__ == "__main__":
    server = NotificationServer()
    server.start_server()
