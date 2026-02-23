#!/usr/bin/env python3
"""
Multi-Room File Sharing System - GUI Client
Tkinter-based client with file sharing and real-time notifications
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import socket
import threading
import json
import base64
import time
import os
from datetime import datetime

class FileSharingClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Room File Sharing System")
        self.root.geometry("900x700")
        
        # Network settings
        self.tcp_host = '127.0.0.1'
        self.tcp_port = 65432
        self.udp_host = '127.0.0.1'
        self.udp_port = 65433
        
        # Client state
        self.tcp_socket = None
        self.udp_socket = None
        self.client_id = None
        self.username = None
        self.current_room = None
        self.connected = False
        self.pending_downloads = {}  # filename -> save_path
        self.udp_listener_thread = None
        self.tcp_receiver_thread = None
        
        # Setup GUI
        self.setup_gui()
        
        # Start UDP listener thread
        self.start_udp_listener()
        
    def setup_gui(self):
        """Setup the GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(conn_frame, text="Username:").grid(row=0, column=0, padx=5)
        self.username_entry = ttk.Entry(conn_frame, width=15)
        self.username_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(conn_frame, text="Connect", command=self.connect_to_server).grid(row=0, column=2, padx=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect).grid(row=0, column=3, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=4, padx=20)
        
        # Room management frame
        room_frame = ttk.LabelFrame(main_frame, text="Room Management", padding="5")
        room_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(room_frame, text="Room:").grid(row=0, column=0, padx=5)
        self.room_combo = ttk.Combobox(room_frame, width=15, state="readonly")
        self.room_combo.grid(row=0, column=1, padx=5)
        self.room_combo.bind("<<ComboboxSelected>>", self.on_room_selected)
        
        ttk.Button(room_frame, text="Create Room", command=self.create_room).grid(row=0, column=2, padx=5)
        ttk.Button(room_frame, text="Join Room", command=self.join_current_room).grid(row=0, column=3, padx=5)
        ttk.Button(room_frame, text="Refresh Rooms", command=self.refresh_rooms).grid(row=0, column=4, padx=5)
        
        self.current_room_label = ttk.Label(room_frame, text="Current Room: None")
        self.current_room_label.grid(row=0, column=4, padx=20)
        
        # Left panel - File operations
        left_frame = ttk.LabelFrame(main_frame, text="File Operations", padding="5")
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # File list
        ttk.Label(left_frame, text="Files in Room:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        self.file_listbox = tk.Listbox(left_frame, height=15, width=40)
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        file_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.file_listbox.yview)
        file_scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        # File info
        self.file_info_label = ttk.Label(left_frame, text="Select a file for details")
        self.file_info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # File operation buttons
        ttk.Button(left_frame, text="Upload File", command=self.upload_file).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(left_frame, text="Download File", command=self.download_file).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(left_frame, text="Refresh Files", command=self.refresh_files).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Right panel - Notifications and users
        right_frame = ttk.LabelFrame(main_frame, text="Notifications & Users", padding="5")
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        # Users list
        ttk.Label(right_frame, text="Users in Room:").grid(row=0, column=0, sticky=tk.W)
        
        self.users_listbox = tk.Listbox(right_frame, height=8, width=30)
        self.users_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Notifications
        ttk.Label(right_frame, text="Notifications:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        self.notifications_text = scrolledtext.ScrolledText(right_frame, height=12, width=30, wrap=tk.WORD)
        self.notifications_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.notifications_text.config(state=tk.DISABLED)
        
        # Chat message (optional)
        chat_frame = ttk.LabelFrame(main_frame, text="Quick Message", padding="5")
        chat_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.chat_entry = ttk.Entry(chat_frame, width=60)
        self.chat_entry.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E))
        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())
        
        ttk.Button(chat_frame, text="Send", command=self.send_chat_message).grid(row=0, column=1, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(3, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        
    def connect_to_server(self):
        """Connect to both TCP and UDP servers"""
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return
            
        try:
            # Connect to TCP server
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.tcp_host, self.tcp_port))
            
            # Set username
            self.send_tcp_message({
                'type': 'set_username',
                'username': username
            })
            
            # Create UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.username = username
            self.client_id = f"client_{int(time.time())}"  # Generate unique client ID
            self.connected = True
            self.status_label.config(text="Connected", foreground="green")
            
            # Register with UDP server
            self.register_with_udp()
            
            # Start TCP receiver thread
            self.tcp_receiver_thread = threading.Thread(target=self.tcp_receiver)
            self.tcp_receiver_thread.daemon = True
            self.tcp_receiver_thread.start()
            
            # Small delay to ensure TCP receiver is ready
            time.sleep(0.1)
            
            # Set default room list initially
            self.room_combo['values'] = ['general']
            self.room_combo.set('general')
            
            # Refresh rooms
            self.refresh_rooms()
            
            messagebox.showinfo("Success", "Connected to server successfully!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.disconnect()
            
    def register_with_udp(self):
        """Register with UDP notification server"""
        if self.udp_socket and self.connected:
            message = {
                'type': 'register',
                'username': self.username,
                'room': self.current_room or 'general',
                'client_id': self.client_id,
                'udp_port': self.udp_port  # Send the actual UDP port we're listening on
            }
            self.send_udp_message(message)
            
    def start_udp_listener(self):
        """Start UDP listener thread"""
        def udp_listener():
            if not self.udp_socket:
                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_socket.bind(('', 0))  # Bind to any available port
                
                # Store the actual port for registration
                self.udp_port = self.udp_socket.getsockname()[1]
                print(f"🟢 [UDP] Listening on port {self.udp_port}")
                
            while self.connected:
                try:
                    data, addr = self.udp_socket.recvfrom(4096)
                    message = json.loads(data.decode('utf-8'))
                    self.handle_udp_message(message)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.connected:  # Only log if we're supposed to be connected
                        print(f"UDP listener error: {e}")
                    time.sleep(1)
                    
        self.udp_listener_thread = threading.Thread(target=udp_listener)
        self.udp_listener_thread.daemon = True
        self.udp_listener_thread.start()
        
    def handle_udp_message(self, message):
        """Handle incoming UDP notification message"""
        msg_type = message.get('type')
        print(f"🟢 [UDP] Received: {message}")  # Debug
        
        if msg_type == 'notification':
            self.add_notification(message.get('message', ''))
            users = message.get('users', [])
            if users:
                print(f"👥 [USERS] Updating from notification: {users}")  # Debug
                self.update_users_list(users)
            
        elif msg_type == 'room_info':
            users = message.get('users', [])
            if users:
                print(f"👥 [USERS] Updating from room_info: {users}")  # Debug
                self.update_users_list(users)
            # Also add current user if not in list
            current_users = list(self.users_listbox.get(0, tk.END))
            if self.username not in current_users:
                self.users_listbox.insert(tk.END, self.username)
            
        elif msg_type == 'chat':
            username = message.get('username', '')
            chat_msg = message.get('message', '')
            self.add_notification(f"[Chat] {username}: {chat_msg}")
            
    def tcp_receiver(self):
        """Receive messages from TCP server"""
        while self.connected and self.tcp_socket:
            try:
                # Receive message length
                length_data = self.tcp_socket.recv(4)
                if not length_data:
                    break
                    
                message_length = int.from_bytes(length_data, byteorder='big')
                
                # Receive actual message
                message_data = b''
                while len(message_data) < message_length:
                    chunk = self.tcp_socket.recv(min(4096, message_length - len(message_data)))
                    if not chunk:
                        break
                    message_data += chunk
                    
                if len(message_data) == message_length:
                    message = json.loads(message_data.decode('utf-8'))
                    self.handle_tcp_message(message)
                    
            except Exception as e:
                print(f"TCP receiver error: {e}")
                break
                
        self.connected = False
        self.status_label.config(text="Disconnected", foreground="red")
        
    def handle_tcp_message(self, message):
        """Handle incoming TCP message"""
        print(f"🔵 [TCP] Received: {message}")  # Debug
        status = message.get('status')
        
        if status == 'success':
            msg_type = message.get('message', '')
            
            if 'Joined room' in msg_type:
                room_files = message.get('room_files', [])
                self.update_file_list(room_files)
                self.current_room = self.room_combo.get()
                self.current_room_label.config(text=f"Current Room: {self.current_room}")
                
                # Add current user to users list
                self.update_users_list([self.username])
                
                # Update UDP server about room change
                self.send_udp_message({
                    'type': 'join_room',
                    'room': self.current_room,
                    'client_id': self.client_id
                })
                
                # Re-register with UDP server with new room
                self.register_with_udp()
                
            elif 'created' in msg_type:
                self.refresh_rooms()
                messagebox.showinfo("Success", msg_type)
                
            elif 'downloaded' in msg_type:
                # Refresh files immediately
                self.refresh_files()
                self.add_notification(msg_type)
                
                # Notify UDP server about file activity
                filename = msg_type.split()[-1]
                self.send_udp_message({
                    'type': 'file_notification',
                    'action': 'download',
                    'filename': filename,
                    'client_id': self.client_id
                })
                
            # Handle file download response
            elif 'filename' in message and 'data' in message:
                filename = message.get('filename')
                file_data = message.get('data')
                
                if filename in self.pending_downloads:
                    save_path = self.pending_downloads.pop(filename)
                    try:
                        # Decode base64 data and save file
                        import base64
                        file_content = base64.b64decode(file_data)
                        with open(save_path, 'wb') as f:
                            f.write(file_content)
                        self.add_notification(f"Successfully downloaded {filename}")
                        messagebox.showinfo("Success", f"File {filename} downloaded successfully!")
                    except Exception as e:
                        self.add_notification(f"Failed to save {filename}: {str(e)}")
                        messagebox.showerror("Download Error", f"Failed to save file: {str(e)}")
                else:
                    self.add_notification(f"Received unexpected file data for {filename}")
                
            elif 'uploaded' in msg_type:
                # Refresh files immediately
                self.refresh_files()
                self.add_notification(msg_type)
                
                # Also manually add the file to the list if upload
                filename = msg_type.split()[-1]
                # Add file to list immediately
                current_files = list(self.file_listbox.get(0, tk.END))
                if filename not in current_files:
                    self.file_listbox.insert(tk.END, filename)
                
                # Notify UDP server about file activity
                self.send_udp_message({
                    'type': 'file_notification',
                    'action': 'upload',
                    'filename': filename,
                    'client_id': self.client_id
                })
            elif 'rooms' in message:
                rooms = message.get('rooms', [])
                self.room_combo['values'] = rooms
                if rooms and not self.current_room:
                    self.room_combo.set(rooms[0])
                    
            # Handle list_files response
            elif 'files' in message:
                files = message.get('files', [])
                file_names = [file['name'] for file in files]
                self.update_file_list(file_names)
                print(f"Updated file list with: {file_names}")  # Debug
                    
        elif status == 'error':
            messagebox.showerror("Error", message.get('message', 'Unknown error'))
            
    def send_tcp_message(self, message):
        """Send message to TCP server"""
        if self.tcp_socket and self.connected:
            try:
                print(f"🔵 [TCP] Sending: {message}")  # Debug
                message_json = json.dumps(message).encode('utf-8')
                length = len(message_json)
                
                self.tcp_socket.send(length.to_bytes(4, byteorder='big'))
                self.tcp_socket.send(message_json)
            except Exception as e:
                print(f"🔴 [TCP] Send error: {e}")
                
    def send_udp_message(self, message):
        """Send message to UDP server"""
        if self.udp_socket:
            try:
                print(f"🟢 [UDP] Sending: {message}")  # Debug
                message_json = json.dumps(message).encode('utf-8')
                self.udp_socket.sendto(message_json, (self.udp_host, self.udp_port))
            except Exception as e:
                print(f"🔴 [UDP] Send error: {e}")
                
    def refresh_rooms(self):
        """Refresh list of available rooms"""
        if self.connected:
            self.send_tcp_message({'type': 'list_rooms'})
            # Add a small delay to wait for response
            self.root.after(100, self.check_room_update)
            
    def check_room_update(self):
        """Check if room list was updated, fallback to default if needed"""
        if not self.room_combo['values']:
            # Fallback to default rooms if server didn't respond
            self.room_combo['values'] = ['general']
            if not self.current_room:
                self.room_combo.set('general')
            
    def create_room(self):
        """Create a new room"""
        room_name = tk.simpledialog.askstring("Create Room", "Enter room name:")
        if room_name and self.connected:
            self.send_tcp_message({
                'type': 'create_room',
                'room': room_name
            })
            
    def on_room_selected(self, event):
        """Handle room selection"""
        selected_room = self.room_combo.get()
        print(f"🏠 [ROOM] Selected: {selected_room}")  # Debug
        if selected_room and self.connected:
            print(f"🏠 [ROOM] Joining: {selected_room}")  # Debug
            self.send_tcp_message({
                'type': 'join_room',
                'room': selected_room
            })
        else:
            print(f"🔴 [ROOM] Cannot join - connected: {self.connected}, room: {selected_room}")  # Debug
            
    def join_current_room(self):
        """Manually join the selected room"""
        selected_room = self.room_combo.get()
        print(f"🏠 [ROOM] Manual join: {selected_room}")  # Debug
        if selected_room and self.connected:
            print(f"🏠 [ROOM] Manual joining: {selected_room}")  # Debug
            self.send_tcp_message({
                'type': 'join_room',
                'room': selected_room
            })
        else:
            messagebox.showerror("Error", "Please select a room and ensure you're connected")
            
    def refresh_files(self):
        """Refresh file list for current room"""
        if self.connected and self.current_room:
            self.send_tcp_message({'type': 'list_files'})
            
    def update_file_list(self, files):
        """Update file listbox"""
        print(f"📁 [FILES] Updating list: {files}")  # Debug
        self.file_listbox.delete(0, tk.END)
        for filename in files:
            self.file_listbox.insert(tk.END, filename)
            
    def update_users_list(self, users):
        """Update users listbox"""
        print(f"👥 [USERS] Updating list: {users}")  # Debug
        self.users_listbox.delete(0, tk.END)
        for username in users:
            self.users_listbox.insert(tk.END, username)
            
    def add_notification(self, message):
        """Add notification to the notifications text area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        notification = f"[{timestamp}] {message}\n"
        
        self.notifications_text.config(state=tk.NORMAL)
        self.notifications_text.insert(tk.END, notification)
        self.notifications_text.see(tk.END)
        self.notifications_text.config(state=tk.DISABLED)
        
    def upload_file(self):
        """Upload a file to the current room"""
        if not self.connected or not self.current_room:
            messagebox.showerror("Error", "Please connect to a room first")
            return
            
        file_path = filedialog.askopenfilename(title="Select file to upload")
        if file_path:
            try:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Read file and encode in base64
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    
                encoded_data = base64.b64encode(file_content).decode('utf-8')
                
                self.send_tcp_message({
                    'type': 'upload_file',
                    'filename': filename,
                    'size': file_size,
                    'data': encoded_data
                })
                
            except Exception as e:
                messagebox.showerror("Upload Error", f"Failed to upload file: {str(e)}")
                
    def download_file(self):
        """Download selected file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a file to download")
            return
            
        filename = self.file_listbox.get(selection[0])
        
        save_path = filedialog.asksaveasfilename(
            title="Save file as",
            initialfile=filename
        )
        
        if save_path and self.connected:
            # Store the pending download path
            self.pending_downloads[filename] = save_path
            
            self.send_tcp_message({
                'type': 'download_file',
                'filename': filename
            })
            
            self.add_notification(f"Downloading {filename}...")
            
    def send_chat_message(self):
        """Send chat message"""
        message = self.chat_entry.get().strip()
        if message and self.connected:
            print(f"💬 [CHAT] Sending: {message}")  # Debug
            self.send_udp_message({
                'type': 'chat_message',
                'message': message,
                'client_id': self.client_id
            })
            self.chat_entry.delete(0, tk.END)
            
    def disconnect(self):
        """Disconnect from servers"""
        self.connected = False
        
        # Send unregister message to UDP server
        if self.udp_socket and self.client_id:
            try:
                self.send_udp_message({
                    'type': 'unregister',
                    'client_id': self.client_id
                })
            except:
                pass
        
        # Close TCP socket
        if self.tcp_socket:
            try:
                self.tcp_socket.shutdown(socket.SHUT_RDWR)
                self.tcp_socket.close()
            except:
                pass
            self.tcp_socket = None
            
        # Close UDP socket
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
            self.udp_socket = None
            
        # Clear state
        self.status_label.config(text="Disconnected", foreground="red")
        self.current_room = None
        self.current_room_label.config(text="Current Room: None")
        self.pending_downloads.clear()
        
        print("🔴 [CLIENT] Disconnected and cleaned up")

def main():
    root = tk.Tk()
    app = FileSharingClient(root)
    root.mainloop()

if __name__ == "__main__":
    import tkinter.simpledialog
    main()
