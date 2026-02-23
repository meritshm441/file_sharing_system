#!/usr/bin/env python3
"""
Multi-Room File Sharing System - TCP Server
Handles file uploads, downloads, and room management
"""

import socket
import threading
import json
import os
import time
from datetime import datetime
import hashlib

class FileSharingServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.clients = {}
        self.rooms = {
            'general': {'files': {}, 'users': set()}
        }
        self.client_id_counter = 0
        self.storage_dir = 'server_files'
        self.ensure_storage_dir()
        self.server_socket = None
        self.running = False
        
        # File validation settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
            '.mp4', '.avi', '.mov', '.mp3', '.wav',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.py', '.js', '.html', '.css', '.json', '.xml'
        }
        self.blocked_patterns = ['..', '\\', '/', ':', '*', '?', '"', '<', '>', '|']
        
    def ensure_storage_dir(self):
        """Create storage directory if it doesn't exist"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            
    def start_server(self):
        """Start the TCP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"TCP File Server started on {self.host}:{self.port}")
        print("Waiting for client connections...")
        
        try:
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)  # Set timeout for periodic checks
                    client_socket, addr = self.server_socket.accept()
                    
                    self.client_id_counter += 1
                    client_id = f"client_{self.client_id_counter}"
                    
                    self.clients[client_id] = {
                        'socket': client_socket,
                        'address': addr,
                        'username': None,
                        'room': None
                    }
                    
                    print(f"New client connected: {client_id} from {addr}")
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_id,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue  # Periodic timeout to check running state
                except OSError as e:
                    if self.running:  # Only log if we're supposed to be running
                        print(f"Socket error: {e}")
                    break
                    
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            self.shutdown_server()
            
    def handle_client(self, client_id):
        """Handle individual client connection"""
        client = self.clients[client_id]
        socket = client['socket']
        
        try:
            while True:
                # Receive message length first
                length_data = socket.recv(4)
                if not length_data:
                    break
                    
                message_length = int.from_bytes(length_data, byteorder='big')
                
                # Receive actual message
                message_data = b''
                while len(message_data) < message_length:
                    chunk = socket.recv(min(4096, message_length - len(message_data)))
                    if not chunk:
                        break
                    message_data += chunk
                    
                if len(message_data) != message_length:
                    break
                    
                try:
                    message = json.loads(message_data.decode('utf-8'))
                    response = self.process_message(client_id, message)
                    self.send_response(socket, response)
                except json.JSONDecodeError:
                    error_response = {
                        'status': 'error',
                        'message': 'Invalid JSON format'
                    }
                    self.send_response(socket, error_response)
                    
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            self.disconnect_client(client_id)
            
    def process_message(self, client_id, message):
        """Process incoming client message"""
        msg_type = message.get('type')
        client = self.clients[client_id]
        
        if msg_type == 'set_username':
            username = message.get('username')
            if username:
                client['username'] = username
                return {'status': 'success', 'message': 'Username set'}
            else:
                return {'status': 'error', 'message': 'Invalid username'}
                
        elif msg_type == 'join_room':
            room_name = message.get('room')
            if room_name and room_name in self.rooms:
                # Leave current room if any
                if client['room']:
                    self.rooms[client['room']]['users'].discard(client_id)
                
                # Join new room
                client['room'] = room_name
                self.rooms[room_name]['users'].add(client_id)
                
                return {
                    'status': 'success',
                    'message': f'Joined room {room_name}',
                    'room_files': list(self.rooms[room_name]['files'].keys())
                }
            else:
                return {'status': 'error', 'message': 'Room not found'}
                
        elif msg_type == 'create_room':
            room_name = message.get('room')
            if room_name and room_name not in self.rooms:
                self.rooms[room_name] = {'files': {}, 'users': set()}
                return {'status': 'success', 'message': f'Room {room_name} created'}
            else:
                return {'status': 'error', 'message': 'Room already exists or invalid name'}
                
        elif msg_type == 'list_rooms':
            return {
                'status': 'success',
                'rooms': list(self.rooms.keys())
            }
            
        elif msg_type == 'list_files':
            room = client['room']
            if room and room in self.rooms:
                files_info = []
                for filename, file_info in self.rooms[room]['files'].items():
                    files_info.append({
                        'name': filename,
                        'size': file_info['size'],
                        'uploaded_by': file_info['uploaded_by'],
                        'uploaded_at': file_info['uploaded_at']
                    })
                return {'status': 'success', 'files': files_info}
            else:
                return {'status': 'error', 'message': 'Not in a room'}
                
        elif msg_type == 'upload_file':
            return self.handle_file_upload(client_id, message)
            
        elif msg_type == 'download_file':
            return self.handle_file_download(client_id, message)
            
        else:
            return {'status': 'error', 'message': 'Unknown message type'}
            
    def validate_filename(self, filename):
        """Validate filename for security"""
        if not filename or filename.strip() != filename:
            return False, "Invalid filename"
            
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in filename:
                return False, f"Filename contains invalid character: {pattern}"
                
        # Check extension
        import os
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.allowed_extensions:
            return False, f"File type {ext} not allowed"
            
        # Check length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
            
        return True, "Valid filename"
        
    def handle_file_upload(self, client_id, message):
        """Handle file upload request"""
        client = self.clients[client_id]
        room = client['room']
        
        if not room:
            return {'status': 'error', 'message': 'Not in a room'}
            
        filename = message.get('filename')
        file_size = message.get('size')
        file_data = message.get('data')
        
        if not all([filename, file_size is not None, file_data]):
            return {'status': 'error', 'message': 'Missing file information'}
            
        # Validate file size
        if file_size > self.max_file_size:
            return {'status': 'error', 'message': f'File too large (max {self.max_file_size // (1024*1024)}MB)'}
            
        # Validate filename
        is_valid, validation_msg = self.validate_filename(filename)
        if not is_valid:
            return {'status': 'error', 'message': validation_msg}
            
        # Additional validation: check if base64 data size matches expected size
        try:
            import base64
            decoded_content = base64.b64decode(file_data)
            actual_size = len(decoded_content)
            if actual_size != file_size:
                return {'status': 'error', 'message': 'File size mismatch'}
        except Exception as e:
            return {'status': 'error', 'message': f'Invalid file data: {str(e)}'}
            
        try:
            # Save file to storage
            room_dir = os.path.join(self.storage_dir, room)
            if not os.path.exists(room_dir):
                os.makedirs(room_dir)
                
            file_path = os.path.join(room_dir, filename)
            
            # Decode base64 data and save
            import base64
            file_content = base64.b64decode(file_data)
            with open(file_path, 'wb') as f:
                f.write(file_content)
                
            # Update room file list
            self.rooms[room]['files'][filename] = {
                'size': file_size,
                'uploaded_by': client['username'] or client_id,
                'uploaded_at': datetime.now().isoformat(),
                'path': file_path
            }
            
            return {
                'status': 'success',
                'message': f'File {filename} uploaded successfully'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Upload failed: {str(e)}'}
            
    def handle_file_download(self, client_id, message):
        """Handle file download request"""
        client = self.clients[client_id]
        room = client['room']
        
        if not room:
            return {'status': 'error', 'message': 'Not in a room'}
            
        filename = message.get('filename')
        if not filename:
            return {'status': 'error', 'message': 'Filename required'}
            
        if filename not in self.rooms[room]['files']:
            return {'status': 'error', 'message': 'File not found'}
            
        try:
            file_info = self.rooms[room]['files'][filename]
            file_path = file_info['path']
            
            # Read file and encode in base64
            import base64
            with open(file_path, 'rb') as f:
                file_content = f.read()
                
            encoded_data = base64.b64encode(file_content).decode('utf-8')
            
            return {
                'status': 'success',
                'filename': filename,
                'size': file_info['size'],
                'data': encoded_data
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Download failed: {str(e)}'}
            
    def send_response(self, socket, response):
        """Send response to client"""
        response_json = json.dumps(response).encode('utf-8')
        length = len(response_json)
        
        # Send length first, then data
        socket.send(length.to_bytes(4, byteorder='big'))
        socket.send(response_json)
        
    def shutdown_server(self):
        """Clean shutdown of the server"""
        print("🔴 [SERVER] Shutting down...")
        self.running = False
        
        # Disconnect all clients
        client_ids = list(self.clients.keys())
        for client_id in client_ids:
            self.disconnect_client(client_id)
            
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        print("🔴 [SERVER] Server shutdown complete")
        
    def disconnect_client(self, client_id):
        """Handle client disconnection"""
        if client_id in self.clients:
            client = self.clients[client_id]
            
            # Remove from room
            if client['room']:
                self.rooms[client['room']]['users'].discard(client_id)
                
            # Close socket
            try:
                client['socket'].shutdown(socket.SHUT_RDWR)
                client['socket'].close()
            except:
                pass
                
            # Remove client
            del self.clients[client_id]
            print(f"Client {client_id} disconnected")

if __name__ == "__main__":
    server = FileSharingServer()
    server.start_server()
