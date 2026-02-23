# Multi-Room File Sharing System
## Socket Programming Assignment II - Group 8

**Group Members:**
- Hadis Masresha
- Meron Teshome
- Yoftahe Gizaw

### Project Overview

This project implements a **Multi-Room File Sharing System** that allows multiple users to connect to different rooms, share files, and receive real-time notifications about file activities. The application demonstrates advanced socket programming concepts by implementing both TCP and UDP versions of the client-server architecture with a modern GUI interface.

### Key Features

1. **🖥️ Modern GUI Interface**: User-friendly tkinter-based desktop application
2. **🏠 Multi-Room System**: Create and join different rooms for organized file sharing
3. **📁 File Operations**: Upload and download files with reliable TCP-based transfer
4. **🔔 Real-time Notifications**: UDP-based instant notifications for user activities
5. **👥 User Management**: See active users in your room with real-time presence
6. **💬 Chat System**: Optional quick chat for room communication
7. **🔄 Dual Protocol**: TCP for reliable file transfers, UDP for fast notifications

### 🖥️ GUI Interface Overview

The application features a modern, intuitive graphical interface with:

- **Connection Panel**: Username entry and connection status
- **Room Management**: Dropdown for room selection, create/join buttons
- **File Operations Panel**: File list, upload/download buttons, file info display
- **Users & Notifications Panel**: Active users list, real-time notifications
- **Quick Chat**: Optional chat for room communication

### Architecture

#### TCP Implementation
- **Server** (`tcp_file_server.py`): Handles file uploads, downloads, and room management
- **Client**: Integrated in GUI client for reliable file operations

#### UDP Implementation  
- **Server** (`udp_notification_server.py`): Manages real-time notifications and user presence
- **Client**: Integrated in GUI client for instant updates

### Technical Implementation Details

#### Message Protocol
All communication uses JSON-formatted messages with the following structure:

```json
{
    "type": "message_type",
    "data": "message_content"
}
```

#### TCP Message Types
- `set_username`: Set client username
- `join_room`: Join a specific room
- `create_room`: Create a new room
- `list_rooms`: Get available rooms
- `list_files`: Get files in current room
- `upload_file`: Upload a file to current room
- `download_file`: Download a file from current room

#### UDP Message Types
- `register`: Register client with notification server
- `heartbeat`: Keep-alive messages
- `join_room`: Notify room changes
- `file_notification`: Broadcast file activities
- `chat_message`: Optional chat functionality

#### File Transfer Protocol
- Files are encoded in base64 for JSON compatibility
- TCP ensures reliable delivery with proper error handling
- File metadata includes size, uploader, and timestamp

### Key Differences Between TCP and UDP Versions

| Aspect | TCP Version | UDP Version |
|--------|-------------|--------------|
| **Purpose** | Reliable file operations | Real-time notifications |
| **Reliability** | Guaranteed delivery | Best-effort delivery |
| **Data Type** | File data and commands | Lightweight notifications |
| **Connection** | Persistent connections | Connectionless |
| **Overhead** | Higher (reliable delivery) | Lower (fast notifications) |
| **Use Case** | Critical file transfers | Instant user updates |

### Usage Instructions

#### 🚀 Quick Start (Recommended for GUI Demo)

**Option A: Start Both Servers Together**
```cmd
.\Start_All_Servers.bat
```
This opens two separate console windows for TCP and UDP servers.

**Option B: Start Servers Individually**  
```cmd
# Window 1 - TCP Server
python tcp_file_server.py

# Window 2 - UDP Server  
python udp_notification_server.py
```

2. **Start GUI Client (Best for Demo):**
   ```cmd
   python file_client_gui.py
   ```
   **This launches the modern GUI interface with visual file sharing!**

> **💡 Pro Tip:** Use individual server commands for better debugging and clear console output!

#### 📋 Step-by-Step Manual Setup

##### Step 1: Start TCP Server
Open a new command prompt/terminal and run:
```cmd
python tcp_file_server.py
```
**Expected Output:**
```
TCP File Server started on 127.0.0.1:65432
Waiting for client connections...
```
**Keep this window open!**

##### Step 2: Start UDP Server  
Open another command prompt/terminal and run:
```cmd
python udp_notification_server.py
```
**Expected Output:**
```
UDP Notification Server started on 127.0.0.1:65433
Waiting for notification messages...
```
**Keep this window open!**

##### Step 3: Launch GUI Client 🖥️
Open a third command prompt/terminal and run:
```cmd
python file_client_gui.py
```
**🎉 GUI Window Opens!** You'll see the modern file sharing interface with:
- Connection panel for username entry
- Room management controls
- File sharing interface
- Real-time notifications panel

**Expected Console Output:**
```
🔵 [TCP] Sending: {'type': 'set_username', 'username': 'your_name'}
🟢 [UDP] Sending: {'type': 'register', 'username': 'your_name', ...}
```

**💡 GUI Features:**
- Visual file browser with upload/download buttons
- Real-time user presence indicators
- Live notifications with timestamps
- Room-based organization
- Optional chat functionality

#### 🎯 Using the Application

##### Step 4: Connect to Server
1. **Enter Username** - Type any username (e.g., "Meron", "TestUser")
2. **Click "Connect"** - Status should turn green
3. **Verify Connection** - Check console for connection messages

##### Step 5: Room Operations
1. **Join Default Room** - Select "general" from dropdown
2. **Click "Join Room"** - Your username should appear in users list
3. **Create New Room** (optional):
   - Click "Create Room"
   - Enter room name (e.g., "room1")
   - Click OK
   - Select new room from dropdown
   - Click "Join Room"

##### Step 6: File Operations
1. **Upload Files:**
   - Click "Upload File"
   - Select any file from your computer
   - File should appear in "Files in Room" list
   - Check notifications for upload confirmation

2. **Download Files:**
   - Select a file from the "Files in Room" list
   - Click "Download File"
   - Choose save location
   - File downloads to selected location

3. **Refresh File List:**
   - Click "Refresh Files" to update the file list
   - Check console for debug messages

##### Step 7: Real-time Features
1. **View Notifications** - All activities appear in notifications panel
2. **See Active Users** - Users in current room appear in users list
3. **Send Chat Messages:**
   - Type message in "Quick Message" box
   - Press Enter or click "Send"
   - Message appears in notifications panel

#### 🔍 Debug Information

The application provides detailed console logs with visual indicators:

- 🔵 **[TCP]** - Reliable file operations (uploads, downloads, room management)
- 🟢 **[UDP]** - Fast notifications (chat, user presence, file activities)
- 🏠 **[ROOM]** - Room operations
- 📁 **[FILES]** - File list updates
- 👥 **[USERS]** - User list updates
- 💬 **[CHAT]** - Chat messages

#### 🛠️ Troubleshooting

##### Common Issues and Solutions:

1. **"Please connect to a room first" Error**
   - **Solution:** Join a room before uploading files
   - **Steps:** Select room → Click "Join Room"

2. **Room not appearing in dropdown**
   - **Solution:** Click "Refresh Rooms" or restart client
   - **Check:** Console should show room list response

3. **File upload not showing in list**
   - **Solution:** Click "Refresh Files" after upload
   - **Check:** Console should show file list update

4. **Chat messages not working**
   - **Solution:** Ensure UDP server is running
   - **Check:** Console should show UDP send/receive messages

5. **Connection errors**
   - **Solution:** Ensure both servers are running before starting client
   - **Check:** Server windows should show "Waiting for connections"

#### 📁 Alternative: Using Executables

If you prefer not to use Python directly:

**Option A: Using Batch Files**
```cmd
.\Start_TCP_Server.bat
.\Start_UDP_Server.bat
.\Start_Client.bat
```

**Option B: Using Executables Directly**
1. **Navigate to executables folder:**
   ```cmd
   cd executables
   ```

2. **Run servers individually:**
   ```cmd
   # Window 1
   TCP_File_Server.exe
   
   # Window 2  
   UDP_Notification_Server.exe
   ```

3. **Run client:**
   ```cmd
   File_Sharing_Client.exe
   ```

**Option C: All-in-One Batch**
```cmd
.\Start_All_Servers.bat
```

#### 🎮 Demo Workflow

For a complete demonstration:

1. **Start all servers** (Step 1-3)
2. **Connect with username "DemoUser"**
3. **Join "general" room**
4. **Upload a test file** (e.g., a simple .txt file)
5. **Verify file appears in list**
6. **Send chat message "Hello World!"**
7. **Create new room "testroom"**
8. **Join "testroom"**
9. **Upload another file**
10. **Test download functionality**

This demonstrates all major features: TCP file operations, UDP notifications, room management, and real-time collaboration.

### Socket Programming Concepts Demonstrated

1. **Dual Protocol Architecture**: TCP for reliability, UDP for speed
2. **Client-Server Model**: Clear separation of concerns
3. **Concurrent Connections**: Multi-threaded handling of multiple clients
4. **Protocol Design**: JSON-based structured communication
5. **Connection Management**: Proper handling of client lifecycle
6. **Data Synchronization**: Real-time state synchronization across clients
7. **Error Handling**: Robust error handling for network issues
8. **GUI Integration**: Desktop application with network communication

### Advanced Features

#### TCP Server Features
- Room-based file organization
- Concurrent client handling
- File metadata management
- Reliable file transfer with base64 encoding
- Automatic client disconnection detection

#### UDP Server Features
- Connectionless client management
- Heartbeat mechanism for client tracking
- Automatic cleanup of inactive clients
- Real-time notification broadcasting
- Room-based message distribution

#### GUI Client Features
- Modern tkinter interface
- Real-time file browser
- User presence indicators
- Notification system
- File upload/download dialogs
- Room management interface

### Testing and Validation

The application has been tested with:
- Multiple concurrent clients (up to 10 tested)
- Simultaneous file operations
- Room creation and management
- Client connection/disconnection scenarios
- Large file transfers (up to 10MB tested)
- Real-time notification delivery
- Network interruption recovery

### Requirements

- Python 3.6 or higher
- Standard library modules: `socket`, `threading`, `json`, `tkinter`, `base64`, `os`, `time`, `datetime`
- No external dependencies required

### Project Structure

```
file_sharing_system/
├── tcp_file_server.py      # TCP server for file operations
├── udp_notification_server.py  # UDP server for notifications
├── file_client_gui.py      # GUI client application
├── README.md              # This documentation
└── server_files/          # Server-side file storage (created automatically)
```

### Security Considerations

- File uploads are stored in a designated server directory
- Base64 encoding prevents binary data injection
- Client validation for room operations
- Connection timeout handling for UDP clients

### Future Enhancements

1. **Authentication**: User login and authorization system
2. **File Permissions**: Access control per room and user
3. **File Search**: Search functionality within rooms
4. **File Preview**: Preview functionality for common file types
5. **Transfer Progress**: Progress bars for file transfers
6. **File Versioning**: Keep multiple versions of files
7. **Compression**: File compression for faster transfers
8. **Encryption**: End-to-end encryption for sensitive files

### Conclusion

This Multi-Room File Sharing System successfully demonstrates advanced socket programming concepts by implementing a practical, real-world application. The dual implementation (TCP and UDP) showcases understanding of different transport protocols and their appropriate use cases. The project goes beyond basic chat applications by implementing a sophisticated file sharing system with real-time notifications, proper error handling, and a modern GUI interface.

The application is suitable for educational purposes, demonstrating key networking concepts while providing a functional tool that could be extended for production use in small team environments.

### Assignment Requirements Compliance

✅ **Client/server application using Socket Programming**
✅ **Both UDP and TCP implementations**
✅ **Source code and executable files included**
✅ **Clear write-up explaining the program**
✅ **Different from discussed class examples and samples**
✅ **Original implementation not repeating sample code**
