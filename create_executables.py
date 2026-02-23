#!/usr/bin/env python3
"""
Create executable files for the Multi-Room File Sharing System
Uses PyInstaller to create standalone executables
"""

import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def create_executable(script_path, output_name=None, icon=None):
    """Create executable from Python script"""
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        return False
        
    script_name = os.path.basename(script_path).replace('.py', '')
    if not output_name:
        output_name = script_name
        
    print(f"Creating executable for {script_name}...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create single executable
        "--windowed" if script_name == "file_client_gui" else "--console",  # GUI vs console
        "--name", output_name,
        "--distpath", "executables",
        "--workpath", "build",
        "--specpath", "spec"
    ]
    
    if icon and os.path.exists(icon):
        cmd.extend(["--icon", icon])
        
    cmd.append(script_path)
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Successfully created {output_name}.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating executable: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def create_batch_files():
    """Create batch files for easy execution"""
    batch_files = {
        "Start_TCP_Server.bat": [
            "@echo off",
            "echo Starting TCP File Server...",
            "executables\\tcp_file_server.exe",
            "pause"
        ],
        "Start_UDP_Server.bat": [
            "@echo off",
            "echo Starting UDP Notification Server...",
            "executables\\udp_notification_server.exe",
            "pause"
        ],
        "Start_Client.bat": [
            "@echo off",
            "echo Starting File Sharing Client...",
            "executables\\file_client_gui.exe",
            "pause"
        ],
        "Start_All_Servers.bat": [
            "@echo off",
            "echo Starting both servers...",
            "start \"TCP Server\" executables\\tcp_file_server.exe",
            "start \"UDP Server\" executables\\udp_notification_server.exe",
            "echo Servers started in separate windows",
            "pause"
        ]
    }
    
    for filename, content in batch_files.items():
        with open(filename, 'w') as f:
            f.write('\n'.join(content))
        print(f"✅ Created {filename}")

def main():
    """Main function to create all executables"""
    print("🚀 Creating executables for Multi-Room File Sharing System...")
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("❌ Failed to install PyInstaller")
        return
        
    # Create directories
    os.makedirs("executables", exist_ok=True)
    os.makedirs("build", exist_ok=True)
    os.makedirs("spec", exist_ok=True)
    
    # Scripts to convert
    scripts = [
        ("tcp_file_server.py", "TCP_File_Server"),
        ("udp_notification_server.py", "UDP_Notification_Server"),
        ("file_client_gui.py", "File_Sharing_Client")
    ]
    
    success_count = 0
    
    for script, output_name in scripts:
        if create_executable(script, output_name):
            success_count += 1
            
    print(f"\n📊 Results: {success_count}/{len(scripts)} executables created successfully")
    
    if success_count == len(scripts):
        print("\n🎉 All executables created successfully!")
        
        # Create batch files
        create_batch_files()
        
        # Clean up build files
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("spec"):
            shutil.rmtree("spec")
            
        print("\n📁 Executables are located in the 'executables' folder")
        print("📁 Batch files are created for easy execution")
        print("\n📋 Usage:")
        print("   1. Run 'Start_TCP_Server.bat' to start the TCP server")
        print("   2. Run 'Start_UDP_Server.bat' to start the UDP server")
        print("   3. Run 'Start_Client.bat' to start the GUI client")
        print("   4. Or use 'Start_All_Servers.bat' to start both servers")
        
    else:
        print("\n❌ Some executables failed to create. Check the errors above.")

if __name__ == "__main__":
    main()
