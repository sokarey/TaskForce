import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import threading
import re
import datetime
import json
from path_manager import PathManagerDialog
from domain_manager import DomainManagerDialog
import sys

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Color scheme
COLORS = {
    "bg_dark": "#1e2430",        # Dark background
    "bg_medium": "#252d3b",      # Medium background
    "accent": "#60a5fa",         # Blue accent
    "accent_hover": "#3b82f6",   # Darker blue hover
    "text": "#ffffff",           # White text
    "border": "#374151",         # Border color
    "error": "#ef4444"          # Error text color
}

class ScrollableFrame(ctk.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main content frame
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            border_color=COLORS["border"],
            border_width=2,
            corner_radius=10
        )
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Create main scrollable frame
        self.main_scrollable = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            orientation="vertical",
            scrollbar_button_color=COLORS["accent"],
            scrollbar_button_hover_color=COLORS["accent_hover"]
        )
        self.main_scrollable.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.main_scrollable.grid_columnconfigure(0, weight=1)

    def configure_scrollable_content(self):
        """Configure the scrollable content to expand properly"""
        for child in self.main_scrollable.winfo_children():
            if isinstance(child, (ctk.CTkFrame, ctk.CTkTextbox)):
                child.grid(sticky="nsew")
                if isinstance(child, ctk.CTkFrame):
                    child.grid_columnconfigure(0, weight=1)

class ScrollableSystemInfoFrame(ScrollableFrame):
    def __init__(self, master, history=""):
        super().__init__(master)
        self.history = str(history) if history else ""
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="System Information",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=0, pady=5, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Computer name entry
        self.computer_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter computer name",
            height=35,
            fg_color="transparent"
        )
        self.computer_entry.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.computer_entry.bind("<Return>", lambda event: self.get_system_info())
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.button_frame.grid(row=0, column=1, padx=(0, 20), pady=10)
        
        # Get Info button
        self.get_info_button = ctk.CTkButton(
            self.button_frame,
            text="Get System Info",
            command=self.get_system_info,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.get_info_button.grid(row=0, column=0, padx=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.button_frame,
            text="Clear Output",
            command=self.clear_output,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.clear_button.grid(row=0, column=1, padx=5)
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=400,
            width=800,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Initialize output
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", self.history)
        self.output_text.configure(state="disabled")
        
        self.configure_scrollable_content()

    def get_system_info(self):
        computer_name = self.computer_entry.get().strip()
        if not computer_name:
            messagebox.showwarning("Warning", "Please enter a computer name")
            return
            
        # Add timestamp to history
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.append_output(f"\n[{timestamp}] Querying {computer_name}...\n")
        
        def execute_query():
            try:
                ps_script = r'''
                $ErrorActionPreference = "Stop"
                $ComputerPattern = "{0}"

                # Get list of computers matching the pattern
                $Computers = @()
                if ($ComputerPattern -match '[*?]') {{
                    try {{
                        $Computers = Get-ADComputer -Filter "Name -like '$ComputerPattern'" | Select-Object -ExpandProperty Name | Sort-Object
                    }} catch {{
                        $Computers = @($ComputerPattern)
                    }}
                }} else {{
                    $Computers = @($ComputerPattern)
                }}

                foreach ($ComputerName in $Computers) {{
                    try {{
                        Write-Output "Connecting to $ComputerName..."
                        
                        # Create CimSession with fallback options
                        $SessionOption = New-CimSessionOption -Protocol Wsman
                        $Session = New-CimSession -ComputerName $ComputerName -SessionOption $SessionOption -ErrorAction Stop
                        
                        # Basic System Information using CIM
                        $CS = Get-CimInstance -CimSession $Session -ClassName Win32_ComputerSystem
                        $OS = Get-CimInstance -CimSession $Session -ClassName Win32_OperatingSystem
                        $Processor = Get-CimInstance -CimSession $Session -ClassName Win32_Processor
                        $Network = Get-CimInstance -CimSession $Session -ClassName Win32_NetworkAdapterConfiguration | 
                            Where-Object {{ $_.IPEnabled -eq $true }} | Select-Object -First 1
                        $Disk = Get-CimInstance -CimSession $Session -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'"

                        # Session and Lock Status Detection
                        $SessionInfo = @{{
                            LockStatus = "Unknown"
                            ActiveUser = $null
                            SessionType = "Unknown"
                            Sessions = @()
                        }}

                        try {{
                            # Get all sessions
                            $queryResult = query session /server:$ComputerName 2>$null
                            $SessionInfo.Sessions = $queryResult | ForEach-Object {{
                                if ($_ -match '^\s*(\S+)\s+(\S+)\s+(\d+)\s+(\S+)') {{
                                    @{{
                                        SessionName = $matches[1]
                                        Username = $matches[2]
                                        ID = $matches[3]
                                        State = $matches[4]
                                    }}
                                }}
                            }} | Where-Object {{ $_ -ne $null }}

                            # Determine session types and active user
                            $consoleSession = $SessionInfo.Sessions | Where-Object {{ $_.SessionName -eq 'console' }}
                            $rdpSessions = $SessionInfo.Sessions | Where-Object {{ $_.SessionName -match '^rdp-tcp#' }}
                            
                            if ($consoleSession) {{
                                if ($consoleSession.State -eq 'Active') {{
                                    $SessionInfo.SessionType = "Local"
                                    $SessionInfo.LockStatus = "Unlocked"
                                    $SessionInfo.ActiveUser = $consoleSession.Username
                                }} else {{
                                    $SessionInfo.SessionType = "Local"
                                    $SessionInfo.LockStatus = "Locked"
                                    $SessionInfo.ActiveUser = $consoleSession.Username
                                }}
                            }}
                            
                            if ($rdpSessions) {{
                                $activeRdp = $rdpSessions | Where-Object {{ $_.State -eq 'Active' }}
                                if ($activeRdp) {{
                                    $SessionInfo.SessionType = "Remote (RDP)"
                                    $SessionInfo.LockStatus = "Unlocked"
                                    $SessionInfo.ActiveUser = $activeRdp.Username
                                }} elseif (!$consoleSession) {{
                                    $SessionInfo.SessionType = "Remote (RDP)"
                                    $SessionInfo.LockStatus = "Locked"
                                    $SessionInfo.ActiveUser = $rdpSessions[0].Username
                                }}
                            }}

                            # If no active user found, try getting it from CS
                            if (!$SessionInfo.ActiveUser -and $CS.UserName) {{
                                $SessionInfo.ActiveUser = $CS.UserName
                            }}

                                                       try {{
                                # Method 1: LogonUI process
                                $logonUI = Get-Process -ComputerName $ComputerName -Name "LogonUI" -ErrorAction SilentlyContinue
                                if ($logonUI) {{ $SessionInfo.LockStatus = "Locked" }}
                                
                                # Method 2: Query session state if not already determined
                                if (-not $SessionInfo.LockStatus -or $SessionInfo.LockStatus -eq "Unknown") {{
                                    $quser = query session /server:$ComputerName 2>$null
                                    if ($quser) {{
                                        $lockedSession = $quser | Where-Object {{ $_ -match 'Disc' }}
                                        if ($lockedSession) {{ $SessionInfo.LockStatus = "Locked" }}
                                        else {{ $SessionInfo.LockStatus = "Unlocked" }}
                                    }}
                                }}
                                
                                # Method 3: Terminal Services if still not determined
                                if (-not $SessionInfo.LockStatus -or $SessionInfo.LockStatus -eq "Unknown") {{
                                    $ts = Get-WmiObject -ComputerName $ComputerName -Class Win32_Process -Filter "name = 'LogonUI.exe'" -ErrorAction SilentlyContinue
                                    if ($ts) {{ $SessionInfo.LockStatus = "Locked" }}
                                    else {{ $SessionInfo.LockStatus = "Unlocked" }}
                                }}
                            }} catch {{
                                Write-Warning "Lock status detection failed: $_"
                                if (-not $SessionInfo.LockStatus) {{ $SessionInfo.LockStatus = "Unknown" }}
                            }}

                        }} catch {{
                            Write-Output "Warning: Could not detect session status: $_"
                        }}

                        # Performance Metrics using CIM
                        $CPUInfo = Get-CimInstance -CimSession $Session -ClassName Win32_PerfFormattedData_PerfOS_Processor | 
                            Where-Object {{ $_.Name -eq '_Total' }}
                        $CPU_Usage = if ($CPUInfo) {{ "$($CPUInfo.PercentProcessorTime)%" }} else {{ "N/A" }}

                        # Memory calculations
                        $TotalRAM = [math]::Round($OS.TotalVisibleMemorySize / 1MB, 2)
                        $FreeRAM = [math]::Round($OS.FreePhysicalMemory / 1MB, 2)
                        $UsedRAM = [math]::Round($TotalRAM - $FreeRAM, 2)
                        $RAMUsagePercent = [math]::Round(($UsedRAM / $TotalRAM) * 100, 2)

                        # Disk performance
                        $DiskPerf = Get-CimInstance -CimSession $Session -ClassName Win32_PerfFormattedData_PerfDisk_LogicalDisk |
                            Where-Object {{ $_.Name -eq '_Total' }}
                        $DiskActiveTime = if ($DiskPerf) {{ "$($DiskPerf.PercentDiskTime)%" }} else {{ "0%" }}

                        # Top processes by disk I/O
                        $TopProcesses = Get-CimInstance -CimSession $Session -ClassName Win32_PerfFormattedData_PerfProc_Process |
                            Where-Object {{ $_.Name -ne '_Total' -and $_.Name -ne 'Idle' }} |
                            Sort-Object -Property IODataBytesPersec -Descending |
                            Select-Object -First 5 |
                            ForEach-Object {{
                                $IORate = [math]::Round($_.IODataBytesPersec / 1MB, 2)
                                "$($_.Name) - $IORate MB"
                            }}

                        # Format output
                        Write-Output "`nSystem Information"
                        Write-Output ("-" * 51)
                        Write-Output ("=" * 51)
                        Write-Output "Computer Name    : $ComputerName"
                        Write-Output ("=" * 51)
                        Write-Output "Username         : $($SessionInfo.ActiveUser)"
                        Write-Output "Session Type     : $($SessionInfo.SessionType)"
                        Write-Output "Screen Lock      : $($SessionInfo.LockStatus)"
                        Write-Output "Manufacturer     : $($CS.Manufacturer)"
                        Write-Output "Model           : $($CS.Model)"
                        Write-Output "IP Address       : $($Network.IPAddress[0])"
                        Write-Output "MAC Address      : $($Network.MACAddress)"
                        Write-Output "Processor        : $($Processor.Name)"
                        Write-Output "RAM              : $TotalRAM GB"
                        Write-Output "Operating System : $($OS.Caption)"
                        Write-Output "Last Deployment  : $($OS.LastBootUpTime)"
                        Write-Output "System Uptime    : $([TimeSpan]::FromSeconds($OS.LocalDateTime.Subtract($OS.LastBootUpTime).TotalSeconds).ToString('d\d\ h\h\ m\m'))"
                        Write-Output "Free Disk Space  : $([math]::Round($Disk.FreeSpace / 1GB, 2)) GB"
                        Write-Output "`nPerformance Metrics"
                        Write-Output ("-" * 51)
                        Write-Output "CPU Usage        : $CPU_Usage"
                        Write-Output "Memory Usage     : $RAMUsagePercent% ($UsedRAM GB used)"
                        Write-Output "Disk Active Time : $DiskActiveTime"
                        Write-Output "`nTop 5 Processes by Disk I/O"
                        Write-Output ("-" * 51)
                        $TopProcesses | ForEach-Object {{ Write-Output $_ }}
                        Write-Output ("-" * 51)

                        # Clean up
                        Remove-CimSession -CimSession $Session
                    }} catch {{
                        Write-Output "Error processing $ComputerName : $_"
                    }}
                }}
                '''
                
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script.format(computer_name)],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    self.append_output(result.stdout)
                else:
                    self.append_output(f"Error getting system information:\n{result.stderr}")
                    
            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                
        # Run in separate thread
        thread = threading.Thread(target=execute_query)
        thread.daemon = True
        thread.start()
        
    def append_output(self, text):
        text = str(text)
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.configure(state="disabled")
            self.output_text.see("end")
            self.history = self.get_output()
            # Update parent's history
            if hasattr(self.master, 'master'):
                parent = self.master.master
                if isinstance(parent, TaskForceApp):
                    parent.system_info_history = self.history
        self.after(0, update)
        
    def clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.history = ""
        # Clear parent's history
        if hasattr(self.master, 'master'):
            parent = self.master.master
            if isinstance(parent, TaskForceApp):
                parent.system_info_history = ""

    def get_output(self):
        return self.output_text.get("1.0", "end-1c")

class ScrollableBulkUserFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Bulk User Management",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Action dropdown
        self.action_var = ctk.StringVar(value="New Batch")
        self.action_dropdown = ctk.CTkOptionMenu(
            self.main_scrollable,
            values=["New Batch"],
            variable=self.action_var,
            width=200,
            command=self.update_script_list,
            fg_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"]
        )
        self.action_dropdown.grid(row=0, column=0, padx=20, pady=10)
        
        # Scripts frame
        self.scripts_frame = ctk.CTkFrame(
            self.main_scrollable,
            fg_color="transparent",
            border_color=COLORS["border"],
            border_width=2,
            corner_radius=10
        )
        self.scripts_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.scripts_frame.grid_columnconfigure(0, weight=1)
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=200,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        # Initialize script list
        self.update_script_list(self.action_var.get())
        
        self.configure_scrollable_content()

    def update_script_list(self, action):
        # Clear existing buttons
        for widget in self.scripts_frame.winfo_children():
            widget.destroy()
        
        # Map action to folder
        folder_map = {
            "New Batch": "New Batch"
        }
        
        folder = folder_map.get(action)
        if folder:
            script_path = f"C:/TaskForce/{folder}"
            if os.path.exists(script_path):
                scripts = [f for f in os.listdir(script_path) if f.endswith('.ps1')]
                for idx, script in enumerate(sorted(scripts)):
                    script_name = os.path.splitext(script)[0].replace('_', ' ').title()
                    button = ctk.CTkButton(
                        self.scripts_frame,
                        text=script_name,
                        command=lambda s=script, f=folder: self.execute_script(s, f),
                        fg_color=COLORS["accent"],
                        hover_color=COLORS["accent_hover"],
                        text_color=COLORS["text"],
                        corner_radius=8,
                        height=30
                    )
                    # Calculate row and column position
                    row = idx // 2  
                    col = idx % 2   
                    button.grid(row=row, column=col, padx=10, pady=3)

    def execute_script(self, script_name, folder):
        script_path = f"C:/TaskForce/{folder}/{script_name}"
        
        def run_command():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            separator = "-" * 50 + "\n"
            
            try:
                self.output_text.configure(state="normal")
                self.output_text.insert("end", f"\n{separator}Executing {script_name} - {timestamp}\n{separator}")
                
                user_input = None
                # Only show OU paths dialog for New Batch scripts
                if folder == "New Batch":
                    # PowerShell script to get OU paths
                    ps_command = """
                    $scriptContent = Get-Content "{0}"
                    $ouPaths = @()
                    $inOUPathsBlock = $false

                    foreach ($line in $scriptContent) {{
                        if ($line -match '^\s*\$ouPaths\s*=\s*@\(') {{
                            $inOUPathsBlock = $true
                            continue
                        }}
                        if ($inOUPathsBlock) {{
                            if ($line -match '^\s*\)') {{
                                break
                            }}
                            if ($line.Trim() -match '^"([^"]+)".*$|^''([^'']+)''.*$') {{
                                $ouPaths += $matches[1]
                            }}
                        }}
                    }}

                    for ($i = 0; $i -lt $ouPaths.Count; $i++) {{
                        Write-Output "$($i + 1): $($ouPaths[$i])"
                    }}
                    """
                    
                    # Get the OU paths
                    process = subprocess.run(
                        ["powershell.exe", "-Command", ps_command.format(script_path)],
                        capture_output=True,
                        text=True
                    )
                    
                    ou_paths_output = process.stdout.strip()
                    
                    # Create a dialog with the OU paths listed
                    dialog = ctk.CTkInputDialog(
                        text=f"Available OU Paths:\n\n{ou_paths_output}\n\nEnter the number of your choice:",
                        title="Script Input Required"
                    )
                    user_input = dialog.get_input()
                
                if folder != "New Batch" or (folder == "New Batch" and user_input is not None):
                    # Run the actual script
                    process = subprocess.Popen(
                        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", script_path],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Only send input if we're in New Batch folder
                    if folder == "New Batch":
                        stdout, stderr = process.communicate(input=user_input + "\n")
                    else:
                        stdout, stderr = process.communicate()
                    
                    if stdout:
                        self.output_text.insert("end", f"Output:\n{stdout}\n")
                    if stderr:
                        self.output_text.insert("end", f"Errors:\n{stderr}\n")
                        
                    self.output_text.insert("end", f"{separator}Execution completed\n")
                else:
                    self.output_text.insert("end", f"{separator}Script execution cancelled by user\n")
                
                self.output_text.see("end")
                self.output_text.configure(state="disabled")
                
            except Exception as e:
                error_msg = f"\n{separator}Error executing {script_name} - {timestamp}\n{separator}Error: {str(e)}\n"
                self.output_text.insert("end", error_msg)
                self.output_text.configure(state="disabled")
                self.output_text.see("end")
        
        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()

class ScrollableGroupPolicyFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Group Policy Management",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        # Name entry
        self.name_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter Computer Name",
            width=200,
            fg_color="transparent"
        )
        self.name_entry.grid(row=0, column=0, padx=10, pady=5)
        self.name_entry.bind("<Return>", lambda event: self.show_policies())
        
        # Show button
        self.show_button = ctk.CTkButton(
            self.input_frame,
            text="Show Policies",
            command=self.show_policies,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.show_button.grid(row=0, column=1, padx=10, pady=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.input_frame,
            text="Clear",
            command=self.clear_history,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.clear_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=400,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        self.configure_scrollable_content()

    def show_policies(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a computer name")
            return
            
        def run_command():
            try:
                # PowerShell script to show group policies using Invoke-Command
                ps_script = r'''
                $target = "{0}"

                function Get-GPODetails($computerName) {{
                    $formatted = @()
                    
                    if (Test-Connection $computerName -Count 1 -Quiet) {{
                        $formatted += "Computer is online. Retrieving group policies..."
                        
                        try {{
                            # Create script block to run on remote computer
                            $scriptBlock = {{
                                $results = @()
                                
                                # Get Computer Policy Info
                                $results += "`nComputer Configuration"
                                $results += "---------------------"
                                
                                # Use built-in command to get policy info with /f for full output
                                $output = gpresult /f /scope computer /v 2>&1
                                if($LASTEXITCODE -ne 0) {{
                                    throw "Failed to get computer policies: $output"
                                }}
                                $policyInfo = $output
                                
                                $inSection = $false
                                $currentSection = ""
                                
                                foreach($line in $policyInfo) {{
                                    $line = $line.Trim()
                                    
                                    # Skip empty lines and headers
                                    if([string]::IsNullOrWhiteSpace($line) -or $line -match "^Microsoft|^Copyright|^VERBOSE") {{ continue }}
                                    
                                    # Main section detection
                                    if($line -match "^Computer Settings:") {{
                                        $results += "`nComputer Settings:"
                                        $currentSection = "settings"
                                        continue
                                    }}
                                    elseif($line -match "^Applied Group Policy Objects:") {{
                                        $results += "`nApplied Group Policy Objects:"
                                        $currentSection = "applied"
                                        continue
                                    }}
                                    elseif($line -match "^The following GPOs were not applied") {{
                                        $results += "`nFiltered GPOs:"
                                        $currentSection = "filtered"
                                        continue
                                    }}
                                    
                                    # Process based on current section
                                    if($currentSection -eq "settings") {{
                                        if($line -match "^([^:]+):\s*(.+)$") {{
                                            $setting = $matches[1].Trim()
                                            $value = $matches[2].Trim()
                                            $results += "    $setting : $value"
                                        }}
                                    }}
                                    elseif($currentSection -eq "applied" -or $currentSection -eq "filtered") {{
                                        if(-not ($line -match "^INFO:|^WARNING:|^ERROR:|^VERBOSE:")) {{
                                            $results += "    $line"
                                        }}
                                    }}
                                }}
                                
                                # Get User Policy Info
                                $results += "`n`nUser Configuration"
                                $results += "-------------------"
                                
                                # Use built-in command to get policy info with /f for full output
                                $output = gpresult /f /scope user /v 2>&1
                                if($LASTEXITCODE -ne 0) {{
                                    throw "Failed to get user policies: $output"
                                }}
                                $policyInfo = $output
                                
                                $inSection = $false
                                $currentSection = ""
                                
                                foreach($line in $policyInfo) {{
                                    $line = $line.Trim()
                                    
                                    # Skip empty lines and headers
                                    if([string]::IsNullOrWhiteSpace($line) -or $line -match "^Microsoft|^Copyright|^VERBOSE") {{ continue }}
                                    
                                    # Main section detection
                                    if($line -match "^User Settings:") {{
                                        $results += "`nUser Settings:"
                                        $currentSection = "settings"
                                        continue
                                    }}
                                    elseif($line -match "^Applied Group Policy Objects:") {{
                                        $results += "`nApplied Group Policy Objects:"
                                        $currentSection = "applied"
                                        continue
                                    }}
                                    elseif($line -match "^The following GPOs were not applied") {{
                                        $results += "`nFiltered GPOs:"
                                        $currentSection = "filtered"
                                        continue
                                    }}
                                    
                                    # Process based on current section
                                    if($currentSection -eq "settings") {{
                                        if($line -match "^([^:]+):\s*(.+)$") {{
                                            $setting = $matches[1].Trim()
                                            $value = $matches[2].Trim()
                                            $results += "    $setting : $value"
                                        }}
                                    }}
                                    elseif($currentSection -eq "applied" -or $currentSection -eq "filtered") {{
                                        if(-not ($line -match "^INFO:|^WARNING:|^ERROR:|^VERBOSE:")) {{
                                            $results += "    $line"
                                        }}
                                    }}
                                }}
                                
                                return $results -join "`n"
                            }}
                            
                            # Try to execute the command on remote computer
                            $result = Invoke-Command -ComputerName $computerName -ScriptBlock $scriptBlock -ErrorAction Stop
                            $formatted += $result
                            
                        }} catch {{
                            # If Invoke-Command fails, try local gpresult with remote target
                            try {{
                                $formatted += "`nAttempting alternative method..."
                                
                                # Get Computer Policies
                                $formatted += "`nComputer Configuration"
                                $formatted += "---------------------"
                                
                                $output = gpresult /f /S $computerName /scope computer /v 2>&1
                                if($LASTEXITCODE -ne 0) {{
                                    throw "Failed to get computer policies: $output"
                                }}
                                $result = $output
                                
                                $currentSection = ""
                                foreach($line in $result) {{
                                    $line = $line.Trim()
                                    
                                    # Skip empty lines and headers
                                    if([string]::IsNullOrWhiteSpace($line) -or $line -match "^Microsoft|^Copyright|^VERBOSE") {{ continue }}
                                    
                                    # Main section detection
                                    if($line -match "^Computer Settings:") {{
                                        $formatted += "`nComputer Settings:"
                                        $currentSection = "settings"
                                        continue
                                    }}
                                    elseif($line -match "^Applied Group Policy Objects:") {{
                                        $formatted += "`nApplied Group Policy Objects:"
                                        $currentSection = "applied"
                                        continue
                                    }}
                                    elseif($line -match "^The following GPOs were not applied") {{
                                        $formatted += "`nFiltered GPOs:"
                                        $currentSection = "filtered"
                                        continue
                                    }}
                                    
                                    # Process based on current section
                                    if($currentSection -eq "settings") {{
                                        if($line -match "^([^:]+):\s*(.+)$") {{
                                            $setting = $matches[1].Trim()
                                            $value = $matches[2].Trim()
                                            $formatted += "    $setting : $value"
                                        }}
                                    }}
                                    elseif($currentSection -eq "applied" -or $currentSection -eq "filtered") {{
                                        if(-not ($line -match "^INFO:|^WARNING:|^ERROR:|^VERBOSE:")) {{
                                            $formatted += "    $line"
                                        }}
                                    }}
                                }}
                                
                                # Get User Policies
                                $formatted += "`n`nUser Configuration"
                                $formatted += "-------------------"
                                
                                $output = gpresult /f /S $computerName /scope user /v 2>&1
                                if($LASTEXITCODE -ne 0) {{
                                    throw "Failed to get user policies: $output"
                                }}
                                $result = $output
                                
                                $currentSection = ""
                                foreach($line in $result) {{
                                    $line = $line.Trim()
                                    
                                    # Skip empty lines and headers
                                    if([string]::IsNullOrWhiteSpace($line) -or $line -match "^Microsoft|^Copyright|^VERBOSE") {{ continue }}
                                    
                                    # Main section detection
                                    if($line -match "^User Settings:") {{
                                        $formatted += "`nUser Settings:"
                                        $currentSection = "settings"
                                        continue
                                    }}
                                    elseif($line -match "^Applied Group Policy Objects:") {{
                                        $formatted += "`nApplied Group Policy Objects:"
                                        $currentSection = "applied"
                                        continue
                                    }}
                                    elseif($line -match "^The following GPOs were not applied") {{
                                        $formatted += "`nFiltered GPOs:"
                                        $currentSection = "filtered"
                                        continue
                                    }}
                                    
                                    # Process based on current section
                                    if($currentSection -eq "settings") {{
                                        if($line -match "^([^:]+):\s*(.+)$") {{
                                            $setting = $matches[1].Trim()
                                            $value = $matches[2].Trim()
                                            $formatted += "    $setting : $value"
                                        }}
                                    }}
                                    elseif($currentSection -eq "applied" -or $currentSection -eq "filtered") {{
                                        if(-not ($line -match "^INFO:|^WARNING:|^ERROR:|^VERBOSE:")) {{
                                            $formatted += "    $line"
                                        }}
                                    }}
                                }}
                                
                            }} catch {{
                                $formatted += "Error: Unable to retrieve group policies using alternative method. $_"
                            }}
                        }}
                    }} else {{
                        throw "Computer is offline or not accessible"
                    }}
                    
                    return $formatted -join "`n"
                }}

                try {{
                    $result = Get-GPODetails $target
                    Write-Output $result
                }} catch {{
                    Write-Output "Error retrieving group policies: $_"
                }}
                '''
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(["powershell", "-Command", ps_script.format(name)], startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(stderr or "Unknown error occurred")
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                separator = "=" * 80 + "\n"
                output = f"\n{separator}Group Policies for {name} - {timestamp}\n{separator}{stdout}\n"
                
                self.append_output(output)
                # Save history to parent
                if hasattr(self.master, 'master'):
                    parent = self.master.master
                    if isinstance(parent, TaskForceApp):
                        parent.group_policy_history = self.get_output()
            except Exception as e:
                error_msg = f"\n{separator}Error querying {name} - {timestamp}\n{separator}Error: {str(e)}\n"
                raise Exception(error_msg)
            
        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
        
    def append_output(self, text):
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.configure(state="disabled")
            self.output_text.see("end")
            self.history = self.get_output()
            # Save history to parent
            if hasattr(self.master, 'master'):
                parent = self.master.master
                if isinstance(parent, TaskForceApp):
                    parent.group_policy_history = self.history
        self.after(0, update)
        
    def clear_history(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.history = ""
        # Clear history in parent
        if hasattr(self.master, 'master'):
            parent = self.master.master
            if isinstance(parent, TaskForceApp):
                parent.group_policy_history = ""

    def get_output(self):
        return self.output_text.get("1.0", "end-1c")

class ScrollableUserInfoFrame(ScrollableFrame):
    def __init__(self, master, history=""):
        super().__init__(master)
        self.history = str(history) if history else ""
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="User Information Lookup",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=0, pady=5, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # User name entry
        self.user_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter name, employee ID, or office number",
            width=300,
            fg_color="transparent"
        )
        self.user_entry.grid(row=0, column=0, padx=(20, 10), pady=10)
        self.user_entry.bind("<Return>", lambda event: self.get_user_info())
        
        # Search button
        self.search_button = ctk.CTkButton(
            self.input_frame,
            text="Search",
            command=self.get_user_info,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.search_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Clear history button
        self.clear_button = ctk.CTkButton(
            self.input_frame,
            text="Clear History",
            command=self.clear_history,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.clear_button.grid(row=0, column=2, padx=(10, 20), pady=10)
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=400,
            width=800,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=1, column=0, padx=0, pady=10, sticky="nsew")
        self.output_text.configure(state="normal")
        self.output_text.insert("1.0", self.history)
        self.output_text.configure(state="disabled")
        
        self.configure_scrollable_content()

    def get_user_info(self):
        user_input = self.user_entry.get().strip()
        if not user_input:
            messagebox.showwarning("Warning", "Please enter a Username, Full Name, or Hits ID")
            return
            
        # Sanitize user input to prevent issues with PowerShell command
        user_input = user_input.replace('"', '\"')  # Escape double quotes

        def run_command():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            separator = "=" * 80 + "\n"
            
            try:
                ps_script = r'''
                try {{
                    $ErrorActionPreference = "Stop"
                    $userInput = "{0}"
                    
                    # Function to find user
                    function Find-User {{
                        param($searchValue)
                        
                        # Try direct username first
                        try {{
                            return Get-ADUser -Identity $searchValue -Properties DisplayName, EmailAddress, Office, EmployeeId, Title, Department, Manager, MemberOf, LockedOut, Enabled, DistinguishedName
                        }} catch {{
                            # If direct username fails, try other search methods
                            
                            # If input is a number, try EmployeeID and Office
                            if ($searchValue -match '^\d+$') {{
                                Write-Host "Input is numeric, trying EmployeeID and Office search..."
                                $user = Get-ADUser -Filter "Office -eq '$searchValue' -or EmployeeId -eq '$searchValue'" -Properties DisplayName, EmailAddress, Office, EmployeeId, Title, Department, Manager, MemberOf, LockedOut, Enabled, DistinguishedName
                            }}
                            
                            # If not found or not a number, try DisplayName
                            if (-not $user) {{
                                Write-Host "Trying DisplayName search..."
                                $user = Get-ADUser -Filter "DisplayName -eq '$searchValue'" -Properties DisplayName, EmailAddress, Office, EmployeeId, Title, Department, Manager, MemberOf, LockedOut, Enabled, DistinguishedName
                            }}
                            
                            # If not found and input contains space, try first/last name
                            if (-not $user -and $searchValue -match ' ') {{
                                Write-Host "Trying first/last name search..."
                                $nameParts = $searchValue -split ' '
                                if ($nameParts.Count -ge 2) {{
                                    $user = Get-ADUser -Filter "GivenName -eq '$($nameParts[0])' -and Surname -eq '$($nameParts[1])'" -Properties DisplayName, EmailAddress, Office, EmployeeId, Title, Department, Manager, MemberOf, LockedOut, Enabled, DistinguishedName
                                }}
                            }}
                        }}
                        
                        return $user
                    }}
                    
                    # Find the user
                    $user = Find-User -searchValue $userInput
                    if (-not $user) {{
                        throw "User not found"
                    }}
                    
                    Write-Host "Found user: $($user.SamAccountName)"
                    
                    # Convert properties to string
                    $manager = if ($user.Manager) {{ (Get-ADUser -Identity $user.Manager).Name }} else {{ "No manager listed" }}
                    $groups = $user.MemberOf | ForEach-Object {{ (Get-ADGroup $_).Name }}
                    
                    $output = @"
User Information:
----------------
Display Name: $($user.DisplayName)
Username: $($user.SamAccountName)
Email: $($user.EmailAddress)
Office: $($user.Office)
Employee ID: $($user.EmployeeId)
Title: $($user.Title)
Department: $($user.Department)
Manager: $manager
Account Status: $(if ($user.Enabled) {{ 'Enabled' }} else {{ 'Disabled' }})
Account Locked: $(if ($user.LockedOut) {{ 'Yes' }} else {{ 'No' }})

Group Memberships:
-----------------
$($groups -join "`n")

Distinguished Name:
-----------------
$($user.DistinguishedName)
"@
                    Write-Output $output
                }} catch {{
                    Write-Error "Error occurred during user lookup: $_"
                    throw
                }}
                '''
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    ["powershell", "-Command", ps_script.format(user_input)],
                    startupinfo=startupinfo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"PowerShell error (code {process.returncode}): {stderr}")
                
                if stderr:
                    self.append_output(f"\nWarning: {stderr}\n")
                
                output = f"\n{stdout}\n"
                self.append_output(output)
                
                # Save history to parent
                if hasattr(self.master, 'master') and hasattr(self.master.master, 'user_info_history'):
                    self.master.master.user_info_history = self.history
                    
            except Exception as e:
                error_msg = f"\n{separator}Error looking up user {user_input} - {timestamp}\n{separator}Error: {str(e)}\n"
                self.append_output(error_msg)
                
        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
        
    def append_output(self, text):
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.configure(state="disabled")
            self.output_text.see("end")
            self.history = self.get_output()
            # Save history to parent
            if hasattr(self.master, 'master') and hasattr(self.master.master, 'user_info_history'):
                self.master.master.user_info_history = self.history
        self.after(0, update)
        
    def clear_history(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.history = ""
        # Clear history in parent
        if hasattr(self.master, 'master') and hasattr(self.master.master, 'user_info_history'):
            self.master.master.user_info_history = ""
            
    def get_output(self):
        return self.output_text.get("1.0", "end-1c")

class ScrollableAppInstallFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Application Installation",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)  # Make path selection expand
        
        # PC name entry
        self.pc_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter PC Name",
            width=200,
            fg_color="transparent"
        )
        self.pc_entry.grid(row=0, column=0, padx=10, pady=5)
        self.pc_entry.bind("<Return>", lambda event: self.list_apps())
        
        # Path selection frame
        self.path_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.path_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        # Path dropdown
        self.path_var = ctk.StringVar()
        self.path_dropdown = ctk.CTkOptionMenu(
            self.path_frame,
            variable=self.path_var,
            values=["Select Path..."],
            width=300,  # Made smaller to accommodate edit button
            dynamic_resizing=False
        )
        self.path_dropdown.grid(row=0, column=0, sticky="ew")
        
        # Manage Paths button
        self.manage_paths_btn = ctk.CTkButton(
            self.path_frame,
            text="Edit",
            width=60,  # Made button slightly wider to fit "Edit" text
            command=self.open_path_manager,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.manage_paths_btn.grid(row=0, column=1, padx=(5, 0))
        
        # List Apps button
        self.list_button = ctk.CTkButton(
            self.input_frame, 
            text="List Apps", 
            command=self.list_apps,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.list_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.input_frame,
            text="Clear",
            command=self.clear_history,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.clear_button.grid(row=0, column=3, padx=10, pady=5)
        
        # Apps frame
        self.apps_frame = ctk.CTkFrame(
            self.main_scrollable,
            fg_color="transparent"
        )
        self.apps_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.apps_frame.grid_columnconfigure(0, weight=1)

        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=200,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        # Store available apps and paths
        self.available_apps = []
        self.paths_data = {}
        
        self.configure_scrollable_content()
        self.load_paths()
        
    def load_paths(self):
        try:
            with open('app_paths.json', 'r') as f:
                self.paths_data = json.load(f)
            
            # Update dropdown values
            path_names = ["Select Path..."] + [p['name'] for p in self.paths_data['paths']]
            self.path_dropdown.configure(values=path_names)
            self.path_dropdown.set("Select Path...")
            
        except Exception as e:
            self.append_output(f"Error loading paths: {str(e)}\n")
            
    def open_path_manager(self):
        dialog = PathManagerDialog(self, callback=self.on_paths_updated)
        
    def on_paths_updated(self, paths):
        self.load_paths()
        
    def get_selected_path(self):
        selected = self.path_var.get()
        if selected == "Select Path...":
            return None
            
        for path_info in self.paths_data['paths']:
            if path_info['name'] == selected:
                return path_info['path']
        return None

    def list_apps(self):
        pc_name = self.pc_entry.get().strip()
        apps_path = self.get_selected_path()
        
        if not pc_name:
            messagebox.showerror("Error", "Please enter a computer name")
            return
            
        if not apps_path:
            messagebox.showerror("Error", "Please select an application path")
            return

        # Clear previous apps
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
        self.available_apps.clear()
        
        self.append_output(f"Attempting to list applications from {apps_path}...\n")

        def execute_list():
            try:
                # First test connectivity to target PC
                test_conn = f'''
                if (Test-Connection -ComputerName {pc_name} -Count 1 -Quiet) {{
                    $true
                }} else {{
                    throw "Unable to connect to {pc_name}. Please verify the computer name and network connectivity."
                }}
                '''
                
                process = subprocess.Popen(["powershell", "-Command", test_conn], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(stderr.decode())

                # Get list of applications in the specified path
                ps_command = f'''
                $ErrorActionPreference = "Stop"
                
                # Test path accessibility
                if (-not (Test-Path "{apps_path}")) {{
                    throw "Cannot access path: {apps_path}"
                }}
                
                # Get all setup files recursively
                $apps = Get-ChildItem -Path "{apps_path}" -Recurse -Include *.exe,*.msi |
                    Where-Object {{ -not $_.PSIsContainer }} |
                    Select-Object @{{
                        Name='Name';
                        Expression={{$_.Directory.Name}}
                    }},
                    @{{
                        Name='Path';
                        Expression={{$_.FullName}}
                    }},
                    @{{
                        Name='Type';
                        Expression={{$_.Extension}}
                    }},
                    @{{
                        Name='ID';
                        Expression={{$_.BaseName}}
                    }}
                
                if ($apps.Count -eq 0) {{
                    throw "No installation files found in the specified path."
                }}

                $apps | ConvertTo-Json
                '''

                process = subprocess.Popen(["powershell", "-Command", ps_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    raise Exception(stderr.decode())

                apps = json.loads(stdout.decode())
                if not isinstance(apps, list):
                    apps = [apps]

                def create_install_button(app_index):
                    return lambda: self.install_app(app_index)

                # Display apps in a grid layout
                for i, app in enumerate(apps):
                    app_frame = ctk.CTkFrame(self.apps_frame, fg_color='#2E2E2E' if i % 2 == 0 else '#1C1C1C')
                    app_frame.pack(fill="x", padx=5, pady=2)
                    
                    app_label = ctk.CTkLabel(
                        app_frame,
                        text=f"{app['Name']} (ID: {app['ID']})",
                        anchor="w"
                    )
                    app_label.pack(side="left", padx=5)
                    
                    install_btn = ctk.CTkButton(
                        app_frame,
                        text="Install",
                        command=create_install_button(i),
                        fg_color=COLORS["accent"],
                        hover_color=COLORS["accent_hover"],
                        text_color=COLORS["text"],
                        corner_radius=8,
                        height=30
                    )
                    install_btn.pack(side="right", padx=5)

                    self.available_apps.append(app)

                self.append_output(f"Found {len(apps)} applications\n")

            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                
        threading.Thread(target=execute_list).start()
    
    def install_app(self, app_index):
        if not 0 <= app_index < len(self.available_apps):
            return

        pc_name = self.pc_entry.get().strip()
        app = self.available_apps[app_index]
        
        self.append_output(f"\nInstalling {app['Name']} on {pc_name}...\n")

        def execute_install():
            try:
                # Enhanced installation process with network access handling
                ps_command = f'''
                $ErrorActionPreference = "Stop"
                try {{
                    # Create PSSession with administrative privileges
                    $session = New-PSSession -ComputerName {pc_name} -EnableNetworkAccess
                    
                    # Get network share credentials if needed
                    $sourcePath = "{app['Path']}"
                    $sourceShare = Split-Path $sourcePath
                    
                    # Create temp directory on remote PC
                    $remoteTempDir = Invoke-Command -Session $session -ScriptBlock {{
                        $tempPath = Join-Path $env:SystemDrive "TaskForceTemp"
                        if (-not (Test-Path $tempPath)) {{
                            New-Item -ItemType Directory -Path $tempPath -Force | Out-Null
                        }}
                        # Set full permissions for SYSTEM and Administrators
                        $acl = Get-Acl $tempPath
                        $acl.SetAccessRuleProtection($true, $false)
                        $adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                            "Administrators","FullControl","ContainerInherit,ObjectInherit","None","Allow"
                        )
                        $systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                            "SYSTEM","FullControl","ContainerInherit,ObjectInherit","None","Allow"
                        )
                        $acl.AddAccessRule($adminRule)
                        $acl.AddAccessRule($systemRule)
                        Set-Acl $tempPath $acl
                        return $tempPath
                    }}
                    
                    Write-Output "Created temporary directory on remote PC..."
                    
                    # Copy installer to remote PC with progress
                    $fileName = Split-Path $sourcePath -Leaf
                    $destPath = Join-Path $remoteTempDir $fileName
                    Write-Output "Copying installer to remote PC..."
                    
                    # Try direct copy first
                    try {{
                        Copy-Item -Path $sourcePath -Destination $destPath -ToSession $session -Force
                    }} catch {{
                        Write-Output "Direct copy failed, trying alternative method..."
                        # If direct copy fails, try copying through admin share
                        $adminPath = "\\\\$pc_name\\C$\\TaskForceTemp\\$fileName"
                        Copy-Item -Path $sourcePath -Destination $adminPath -Force
                    }}
                    
                    Write-Output "Starting installation..."
                    
                    # Execute installation with enhanced error handling
                    $result = Invoke-Command -Session $session -ScriptBlock {{
                        param($installerPath, $isExe)
                        
                        $env:SEE_MASK_NOZONECHECKS = 1
                        $success = $false
                        $errorMsg = ""
                        
                        try {{
                            if ($isExe) {{
                                # For .exe installers
                                $commonArgs = @("/S", "/quiet", "/norestart")
                                foreach ($argSet in @($commonArgs, @("/VERYSILENT"), @("/quiet", "/passive"))) {{
                                    try {{
                                        $proc = Start-Process -FilePath $installerPath -ArgumentList $argSet -Wait -PassThru
                                        if ($proc.ExitCode -eq 0) {{
                                            $success = $true
                                            break
                                        }}
                                        $errorMsg = "Exit code: $($proc.ExitCode)"
                                    }} catch {{
                                        $errorMsg = $_.Exception.Message
                                        continue
                                    }}
                                }}
                            }} else {{
                                # For MSI installers
                                $msiArgs = @(
                                    "/i",
                                    "`"$installerPath`"",
                                    "/qn",
                                    "/norestart",
                                    "ALLUSERS=1",
                                    "MSIRESTARTMANAGERCONTROL=Disable"
                                )
                                $proc = Start-Process msiexec -ArgumentList $msiArgs -Wait -PassThru
                                $success = ($proc.ExitCode -eq 0)
                                $errorMsg = "MSI exit code: $($proc.ExitCode)"
                            }}
                            
                            if (-not $success) {{
                                throw "Installation failed: $errorMsg"
                            }}
                            
                            return @{{
                                Success = $true
                                Message = "Installation completed successfully"
                            }}
                            
                        }} catch {{
                            return @{{
                                Success = $false
                                Message = "Installation error: $_"
                            }}
                        }} finally {{
                            # Cleanup
                            Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
                            $env:SEE_MASK_NOZONECHECKS = 0
                        }}
                    }} -ArgumentList $destPath, ($fileName -like "*.exe")
                    
                    # Handle installation result
                    if (-not $result.Success) {{
                        throw "Installation failed: $($result.Message)"
                    }}
                    
                    Write-Output $result.Message
                    
                }} catch {{
                    throw "Installation failed: $_"
                }} finally {{
                    if ($session) {{
                        Remove-PSSession $session
                    }}
                    # Cleanup remote temp directory if empty
                    if (Test-Path "\\\\$pc_name\\C$\\TaskForceTemp") {{
                        if (-not (Get-ChildItem "\\\\$pc_name\\C$\\TaskForceTemp")) {{
                            Remove-Item "\\\\$pc_name\\C$\\TaskForceTemp" -Force
                        }}
                    }}
                }}
                '''

                process = subprocess.Popen(["powershell", "-Command", ps_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    raise Exception(stderr.decode())

                self.append_output(stdout.decode())

            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                
        thread = threading.Thread(target=execute_install)
        thread.daemon = True
        thread.start()
    
    def clear_history(self):
        self.available_apps = []
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
        # Clear the apps frame
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
            
    def append_output(self, text):
        """Append text to the output box"""
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        self.output_text.see("end")  # Auto-scroll to bottom
        self.output_text.configure(state="disabled")
        
class ScrollableAppUninstallFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Application Uninstallation",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        # PC name entry
        self.pc_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter PC Name",
            width=200,
            fg_color="transparent"
        )
        self.pc_entry.grid(row=0, column=0, padx=10, pady=5)
        self.pc_entry.bind("<Return>", lambda event: self.list_apps())
        
        # List Apps button
        self.list_button = ctk.CTkButton(
            self.input_frame,
            text="List Apps",
            command=self.list_apps,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.list_button.grid(row=0, column=1, padx=10, pady=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.input_frame,
            text="Clear",
            command=self.clear_history,
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.clear_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Apps frame
        self.apps_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.apps_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=200,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        self.configure_scrollable_content()
        
        # Store installed apps
        self.installed_apps = []
        
    def list_apps(self):
        pc_name = self.pc_entry.get().strip()
        if not pc_name:
            messagebox.showerror("Error", "Please enter a PC name")
            return
            
        # Destroy all existing widgets in the apps frame
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
        
        # Recreate the apps frame to ensure a clean slate
        self.apps_frame.destroy()
        self.apps_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.apps_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Reset the installed apps list
        self.installed_apps = []
        self.append_output(f"Attempting to list applications from {pc_name}...\n")

        def run_command():
            try:
                # Use PowerShell remoting for everything
                ps_command = f'''
                $ErrorActionPreference = "Stop"
                try {{
                    # Test connection first
                    if (-not (Test-Connection -ComputerName {pc_name} -Count 1 -Quiet)) {{
                        throw "Cannot connect to {pc_name}. Please verify the computer name and network connectivity."
                    }}
                    
                    # Use PowerShell remoting for everything
                    $session = New-PSSession -ComputerName {pc_name} -EnableNetworkAccess
                    
                    $script = {{
                        $apps = @()
                        
                        # Get MSI apps using WMI
                        try {{
                            $msiApps = Get-WmiObject -Class Win32_Product -ErrorAction SilentlyContinue |
                                Select-Object Name, Version, IdentifyingNumber
                            foreach ($app in $msiApps) {{
                                if ($app.Name) {{
                                    $apps += @{{
                                        Name = $app.Name
                                        Version = $app.Version
                                        IsMSI = $true
                                        IdentifyingNumber = $app.IdentifyingNumber
                                        UninstallString = $null
                                        QuietUninstallString = $null
                                    }}
                                }}
                            }}
                        }} catch {{
                            Write-Warning "Could not retrieve MSI applications: $_"
                        }}
                        
                        # Get apps from registry
                        $registryPaths = @(
                            "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
                            "HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"
                        )
                        
                        foreach ($path in $registryPaths) {{
                            try {{
                                Get-ItemProperty -Path $path -ErrorAction SilentlyContinue | 
                                Where-Object {{ $_.DisplayName }} | 
                                ForEach-Object {{
                                    # Check if this app is not already in the list
                                    if (-not ($apps | Where-Object {{ $_.Name -eq $_.DisplayName -and $_.Version -eq $_.DisplayVersion }})) {{
                                        $apps += @{{
                                            Name = $_.DisplayName
                                            Version = $_.DisplayVersion
                                            IsMSI = $false
                                            IdentifyingNumber = $null
                                            UninstallString = $_.UninstallString
                                            QuietUninstallString = $_.QuietUninstallString
                                        }}
                                    }}
                                }}
                            }} catch {{
                                Write-Warning "Error accessing registry path $path : $_"
                            }}
                        }}
                        
                        if ($apps.Count -eq 0) {{
                            throw "No applications found. This could be due to insufficient permissions."
                        }}
                        
                        return $apps
                    }}
                    
                    $result = Invoke-Command -Session $session -ScriptBlock $script
                    Remove-PSSession $session
                    
                    $result | ConvertTo-Json
                }} catch {{
                    throw $_
                }}
                '''

                process = subprocess.Popen(["powershell", "-Command", ps_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode()
                    if "network path was not found" in error_msg.lower() or "cannot connect" in error_msg.lower():
                        raise Exception(f"Cannot connect to {pc_name}. Please verify:\n" +
                                     "1. The computer name is correct\n" +
                                     "2. The remote computer is turned on\n" +
                                     "3. You have network connectivity to the remote computer\n" +
                                     "4. Windows Remote Management (WinRM) is enabled on both computers\n\n" +
                                     "To enable WinRM, run these commands as administrator on both computers:\n" +
                                     "1. winrm quickconfig\n" +
                                     "2. Enable-PSRemoting -Force")
                    elif "access is denied" in error_msg.lower():
                        raise Exception(f"Access denied when connecting to {pc_name}. Please verify:\n" +
                                     "1. You have administrative rights on the remote computer\n" +
                                     "2. Your credentials are valid for the remote computer\n" +
                                     "3. Run this command as administrator to trust the remote computer:\n" +
                                     f"   Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value {pc_name} -Force")
                    else:
                        raise Exception(f"Failed to list applications: {error_msg}")

                try:
                    apps = json.loads(stdout.decode())
                except json.JSONDecodeError:
                    raise Exception("Failed to parse application list. Please check permissions and try again.")

                if not apps:
                    self.append_output("No applications found. This might be due to insufficient permissions.\n")
                    return

                self.installed_apps = apps
                
                # Sort apps by name
                self.installed_apps.sort(key=lambda x: x['Name'].lower())

                # Create buttons for each app
                for i, app in enumerate(self.installed_apps):
                    app_frame = ctk.CTkFrame(self.apps_frame, fg_color='#2E2E2E' if i % 2 == 0 else '#1C1C1C')
                    app_frame.pack(fill="x", padx=5, pady=2)
                    
                    app_label = ctk.CTkLabel(
                        app_frame,
                        text=f"{app['Name']} (v{app['Version'] if app['Version'] else 'N/A'})",
                        anchor="w"
                    )
                    app_label.pack(side="left", padx=5)
                    
                    uninstall_btn = ctk.CTkButton(
                        app_frame,
                        text="Uninstall",
                        command=lambda idx=i: self.uninstall_app(idx),
                        width=100
                    )
                    uninstall_btn.pack(side="right", padx=5)

                self.append_output(f"Successfully retrieved {len(apps)} applications from {pc_name}\n")

            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                self.append_output("\nTroubleshooting steps:\n")
                self.append_output("1. Run these PowerShell commands as administrator on both computers:\n")
                self.append_output("   winrm quickconfig\n")
                self.append_output("   Enable-PSRemoting -Force\n\n")
                self.append_output("2. Configure WinRM trusted hosts (run as administrator):\n")
                self.append_output(f"   Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value {pc_name} -Force\n\n")
                self.append_output("3. Verify you are running the application as Administrator\n")
                self.append_output("4. Check that WinRM is properly configured:\n")
                self.append_output("   - Ensure WinRM ports (5985, 5986) are open\n")
                self.append_output("   - Temporarily disable firewall to test connectivity\n\n")
                self.append_output("5. Verify network connectivity:\n")
                self.append_output(f"   ping {pc_name}\n\n")
                self.append_output("6. Check credentials and permissions:\n")
                self.append_output("   - Run the application as administrator\n")
                self.append_output("   - Ensure you have admin rights on the remote computer\n")
                
        threading.Thread(target=run_command).start()
    
    def uninstall_app(self, app_index):
        app = self.installed_apps[app_index]
        pc_name = self.pc_entry.get().strip()
        
        if messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {app['Name']} v{app['Version']} from {pc_name}?"):
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            action_text = "Uninstalling"
            self.append_output(f"\n{timestamp} {action_text} {app['Name']} v{app['Version']} from {pc_name}...\n")
            
            def run_uninstall():
                separator = "=" * 80 + "\n"
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    # Validate required parameters
                    if not app.get('Name'):
                        raise ValueError("Application name is missing")
                    
                    # Ensure uninstall strings are not None
                    uninstall_string = app.get('UninstallString', '')
                    quiet_uninstall_string = app.get('QuietUninstallString', '')
                    identifying_number = app.get('IdentifyingNumber', '')
                    
                    # Create PowerShell script for uninstallation
                    ps_script = f'''
$ErrorActionPreference = "Stop"
$computerName = "{pc_name}"
$appName = "{app['Name']}"

Write-Output "Testing connection to $computerName..."
if (Test-Connection $computerName -Count 1 -Quiet) {{
    try {{
        Write-Output "Attempting to rename computer..."
        
        # Use Rename-Computer cmdlet with domain credentials
        $scriptBlock = {{
            param($appName)
            
            function Invoke-UninstallCommand {{
                param($cmd)
                $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $cmd" -Wait -PassThru -NoNewWindow
                return $process.ExitCode -eq 0
            }}
            
            # Try MSI uninstall first
            try {{
                $app = Get-WmiObject -Class Win32_Product -Filter "Name='$appName'"
                if ($app) {{
                    Write-Output "Found MSI application, uninstalling..."
                    $result = $app.Uninstall()
                    if ($result.ReturnValue -eq 0) {{
                        Write-Output "MSI uninstall successful"
                        return $true
                    }}
                    Write-Output "MSI uninstall failed with code: $($result.ReturnValue)"
                }}
            }} catch {{
                Write-Output "MSI uninstall failed: $_"
            }}
            
            # Try registry uninstall
            Write-Output "Attempting registry-based uninstall..."
            $paths = @(
                "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
                "HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"
            )
            
            foreach ($path in $paths) {{
                $apps = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue | 
                      Where-Object {{ $_.DisplayName -eq $appName }}
                
                foreach ($app in $apps) {{
                    if ($app.QuietUninstallString) {{
                        Write-Output "Found quiet uninstall string, executing..."
                        if (Invoke-UninstallCommand $app.QuietUninstallString) {{
                            Write-Output "Quiet uninstall successful"
                            return $true
                        }}
                    }}
                    
                    if ($app.UninstallString) {{
                        Write-Output "Found uninstall string, adding silent parameters..."
                        $cmd = $app.UninstallString
                        if ($cmd -match "msiexec") {{
                            $cmd = "$cmd /quiet /norestart"
                        }} else {{
                            $cmd = "$cmd /S /SILENT /VERYSILENT /NORESTART"
                        }}
                        
                        if (Invoke-UninstallCommand $cmd) {{
                            Write-Output "Silent uninstall successful"
                            return $true
                        }}
                    }}
                }}
            }}
            
            # Try direct WMIC uninstall as last resort
            Write-Output "Attempting WMIC uninstall..."
            if (Invoke-UninstallCommand "wmic product where `"name='$appName'`" call uninstall /nointeractive") {{
                Write-Output "WMIC uninstall successful"
                return $true
            }}
            
            Write-Output "All uninstall methods failed"
            return $false
        }}
        
        $session = New-PSSession -ComputerName $computerName -EnableNetworkAccess
        $result = Invoke-Command -Session $session -ScriptBlock $scriptBlock -ArgumentList $appName
        Remove-PSSession $session
        
        if ($result) {{
            Write-Output "Uninstall completed successfully"
            exit 0
        }} else {{
            Write-Output "Failed to uninstall application"
            exit 1
        }}
    }} catch {{
        Write-Output "ERROR: Failed to uninstall application: $_"
        exit 1
    }}
}} else {{
    Write-Output "ERROR: Unable to connect to $computerName"
    exit 1
}}
'''

                    # Execute the PowerShell command with detailed output
                    process = subprocess.Popen(
                        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            self.append_output(output.strip())

                    process.wait()
                    self.append_output("Uninstallation completed.")

                except Exception as e:
                    error_msg = f"\n{separator}Uninstallation Failed - {timestamp}\n{separator}"
                    error_msg += f"Error uninstalling {app['Name']}: {str(e)}\n\n"
                    error_msg += "Troubleshooting steps:\n"
                    error_msg += "1. Verify you are running the application as Administrator\n"
                    error_msg += "2. Check that WinRM is properly configured:\n"
                    error_msg += "   - Ensure WinRM ports (5985, 5986) are open\n"
                    error_msg += "   - Temporarily disable firewall to test connectivity\n\n"
                    error_msg += "3. Verify network connectivity:\n"
                    error_msg += f"   ping {pc_name}\n\n"
                    error_msg += "4. Check credentials and permissions:\n"
                    error_msg += "   - Run the application as administrator\n"
                    error_msg += "   - Ensure you have admin rights on the remote computer\n"
                    error_msg += "5. If the issue persists, try manual uninstallation"
                    raise Exception(error_msg)
            
            threading.Thread(target=run_uninstall).start()
    
    def clear_history(self):
        self.installed_apps = []
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
        # Clear the apps frame
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
            
    def append_output(self, text):
        """Append text to the output box"""
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        self.output_text.see("end")  # Auto-scroll to bottom
        self.output_text.configure(state="disabled")
        
class ScrollablePasswordChangeFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Password Management",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # User/Hits ID entry
        self.name_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter Username or Hits ID",
            width=300,
            height=35,
            fg_color="transparent"
        )
        self.name_entry.grid(row=0, column=0, padx=20, pady=10)
        self.name_entry.bind("<Return>", lambda event: self.change_password())
        
        # Password entry
        self.password_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter New Password",
            width=300,
            height=35,
            show="*",
            fg_color="transparent"
        )
        self.password_entry.grid(row=1, column=0, padx=20, pady=10)
        
        # Checkbox frame
        self.checkbox_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.checkbox_frame.grid(row=2, column=0, padx=20, pady=5)
        
        # Unlock user checkbox (checked by default)
        self.unlock_var = ctk.BooleanVar(value=True)
        self.unlock_checkbox = ctk.CTkCheckBox(
            self.checkbox_frame,
            text="Unlock User",
            variable=self.unlock_var,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.unlock_checkbox.grid(row=0, column=0, padx=10, pady=5)
        
        # Change at next login checkbox (unchecked by default)
        self.change_next_login_var = ctk.BooleanVar(value=False)
        self.change_next_login_checkbox = ctk.CTkCheckBox(
            self.checkbox_frame,
            text="Change at Next Login",
            variable=self.change_next_login_var,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.change_next_login_checkbox.grid(row=0, column=1, padx=10, pady=5)
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Change password button
        self.change_button = ctk.CTkButton(
            self.button_frame,
            text="Change Password",
            command=self.change_password,
            width=120,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.change_button.grid(row=0, column=0, padx=10, pady=5)
        
        # Unlock only button
        self.unlock_button = ctk.CTkButton(
            self.button_frame,
            text="Unlock Only",
            command=self.unlock_user,
            width=120,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.unlock_button.grid(row=0, column=1, padx=10, pady=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.button_frame,
            text="Clear",
            command=self.clear_history,
            width=120,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.clear_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=400,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        self.configure_scrollable_content()
        
    def unlock_user(self):
        user_input = self.name_entry.get().strip()
        
        if not user_input:
            messagebox.showerror("Error", "Please enter a username or Hits ID")
            return
            
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        separator = "-" * 80
        self.append_output(f"\n{separator}\nUnlocking user {user_input} - {timestamp}\n{separator}\n")

        def execute_unlock():
            try:
                ps_script = f'''
                try {{
                    $ErrorActionPreference = "Stop"
                    $userInput = "{user_input}"
                    
                    # Function to find user
                    function Find-User {{
                        param($searchValue)
                        
                        # Try direct username first
                        try {{
                            return Get-ADUser -Identity $searchValue -Properties SamAccountName, LockedOut
                        }} catch {{
                            # If direct username fails, try other search methods
                            
                            # If input is a number, try EmployeeID and Office
                            if ($searchValue -match '^\d+$') {{
                                Write-Host "Input is numeric, trying EmployeeID and Office search..."
                                $user = Get-ADUser -Filter "Office -eq '$searchValue' -or EmployeeId -eq '$searchValue'" -Properties SamAccountName, LockedOut
                            }}
                            
                            # If not found or not a number, try DisplayName
                            if (-not $user) {{
                                Write-Host "Trying DisplayName search..."
                                $user = Get-ADUser -Filter "DisplayName -eq '$searchValue'" -Properties SamAccountName, LockedOut
                            }}
                            
                            # If not found and input contains space, try first/last name
                            if (-not $user -and $searchValue -match ' ') {{
                                Write-Host "Trying first/last name search..."
                                $nameParts = $searchValue -split ' '
                                if ($nameParts.Count -ge 2) {{
                                    $user = Get-ADUser -Filter "GivenName -eq '$($nameParts[0])' -and Surname -eq '$($nameParts[1])'" -Properties SamAccountName, LockedOut
                                }}
                            }}
                        }}
                        
                        return $user
                    }}
                    
                    # Find the user
                    $user = Find-User -searchValue $userInput
                    if (-not $user) {{
                        throw "User not found"
                    }}
                    
                    Write-Host "Found user: $($user.SamAccountName)"
                    
                    # Check if user is locked
                    if ($user.LockedOut) {{
                        Unlock-ADAccount -Identity $user.SamAccountName
                        Write-Host "User account was locked and has been unlocked successfully"
                    }} else {{
                        Write-Host "User account is not locked"
                    }}
                    
                }} catch {{
                    Write-Error "Error: $_"
                    throw
                }}
                '''
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    ["powershell", "-Command", ps_script],
                    startupinfo=startupinfo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"PowerShell error (code {process.returncode}): {stderr}")
                
                if stderr:
                    self.append_output(f"\nWarning: {stderr}\n")
                
                self.append_output(f"{stdout}\n")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}\n"
                self.append_output(error_msg)
                
        thread = threading.Thread(target=execute_unlock)
        thread.daemon = True
        thread.start()

    def change_password(self):
        user_input = self.name_entry.get().strip()
        new_password = self.password_entry.get().strip()
        
        if not user_input:
            messagebox.showerror("Error", "Please enter a username or Hits ID")
            return
            
        if not new_password:
            messagebox.showerror("Error", "Please enter a new password")
            return
        
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        separator = "-" * 80
        self.append_output(f"\n{separator}\nChanging password for {user_input} - {timestamp}\n{separator}\n")
        
        def execute_change():
            try:
                ps_script = f'''
                try {{
                    $ErrorActionPreference = "Stop"
                    $userInput = "{user_input}"
                    $newPassword = "{new_password}"
                    $unlockUser = ${str(self.unlock_var.get()).lower()}
                    $changeAtNextLogin = ${str(self.change_next_login_var.get()).lower()}
                    
                    # Function to find user
                    function Find-User {{
                        param($searchValue)
                        
                        # Try direct username first
                        try {{
                            return Get-ADUser -Identity $searchValue -Properties SamAccountName
                        }} catch {{
                            # If direct username fails, try other search methods
                            
                            # If input is a number, try EmployeeID and Office
                            if ($searchValue -match '^\d+$') {{
                                Write-Host "Input is numeric, trying EmployeeID and Office search..."
                                $user = Get-ADUser -Filter "Office -eq '$searchValue' -or EmployeeId -eq '$searchValue'" -Properties SamAccountName
                            }}
                            
                            # If not found or not a number, try DisplayName
                            if (-not $user) {{
                                Write-Host "Trying DisplayName search..."
                                $user = Get-ADUser -Filter "DisplayName -eq '$searchValue'" -Properties SamAccountName
                            }}
                            
                            # If not found and input contains space, try first/last name
                            if (-not $user -and $searchValue -match ' ') {{
                                Write-Host "Trying first/last name search..."
                                $nameParts = $searchValue -split ' '
                                if ($nameParts.Count -ge 2) {{
                                    $user = Get-ADUser -Filter "GivenName -eq '$($nameParts[0])' -and Surname -eq '$($nameParts[1])'" -Properties SamAccountName
                                }}
                            }}
                        }}
                        
                        return $user
                    }}
                    
                    # Find the user
                    $user = Find-User -searchValue $userInput
                    if (-not $user) {{
                        throw "User not found"
                    }}
                    
                    Write-Host "Found user: $($user.SamAccountName)"
                    
                    # Convert password to secure string
                    $securePassword = ConvertTo-SecureString $newPassword -AsPlainText -Force
                    
                    # Change password
                    Set-ADAccountPassword -Identity $user.SamAccountName -NewPassword $securePassword -Reset
                    Write-Host "Password changed successfully"
                    
                    # Unlock if requested
                    if ($unlockUser) {{
                        Unlock-ADAccount -Identity $user.SamAccountName
                        Write-Host "User account unlocked"
                    }}
                    
                    # Set change password at next login if requested
                    if ($changeAtNextLogin) {{
                        Set-ADUser -Identity $user.SamAccountName -ChangePasswordAtLogon $true
                        Write-Host "User will be required to change password at next login"
                    }}
                    
                }} catch {{
                    Write-Error "Error: $_"
                    throw
                }}
                '''
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    ["powershell", "-Command", ps_script],
                    startupinfo=startupinfo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"PowerShell error (code {process.returncode}): {stderr}")
                
                if stderr:
                    self.append_output(f"\nWarning: {stderr}\n")
                
                self.append_output(f"{stdout}\n")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}\n"
                self.append_output(error_msg)
                
        thread = threading.Thread(target=execute_change)
        thread.daemon = True
        thread.start()
        
    def append_output(self, text):
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.see("end")
            self.output_text.configure(state="disabled")
        
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.after(0, update)
            
    def clear_history(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
class ScrollableUpdateRestartFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Power Control",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Computer name entry
        self.computer_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Enter computer name (supports wildcards like PC* or PC-1,PC-2)",
            height=35,
            fg_color="transparent"
        )
        self.computer_entry.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.computer_entry.bind("<Return>", lambda event: self.list_computers())
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.button_frame.grid(row=0, column=1, padx=(0, 20), pady=10)
        
        # List PCs button
        self.list_button = ctk.CTkButton(
            self.button_frame,
            text="List Computers",
            command=self.list_computers,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.list_button.grid(row=0, column=0, padx=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.button_frame,
            text="Clear Output",
            command=self.clear_history,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.clear_button.grid(row=0, column=1, padx=5)
        
        # Computers frame for listing PCs
        self.computers_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.computers_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.computers_frame.grid_columnconfigure(0, weight=1)

        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=200,
            width=800,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # Store found computers
        self.computers = []
        
        self.configure_scrollable_content()
        
    def list_computers(self):
        computer_input = self.computer_entry.get().strip()
        
        if not computer_input:
            messagebox.showerror("Error", "Please enter a computer name or pattern")
            return
            
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.append_output(f"\n{'='*80}\nSearching for computers matching '{computer_input}' - {timestamp}\n{'='*80}\n")
        
        # Clear previous computer list
        for widget in self.computers_frame.winfo_children():
            widget.destroy()
        self.computers = []
        
        def execute_search():
            try:
                # Handle multiple computer names separated by commas
                computer_patterns = [p.strip() for p in computer_input.split(',')]
                
                # PowerShell script to search for computers
                ps_script = f'''
                $ErrorActionPreference = "Stop"
                
                $results = @()
                
                foreach ($pattern in @({','.join(f'"{p}"' for p in computer_patterns)})) {{
                    # Handle different pattern types
                    if ($pattern -like "*[?]*" -or $pattern -like "*[*]*") {{
                        # It's a wildcard pattern, search in Active Directory
                        try {{
                            $computers = Get-ADComputer -Filter "Name -like '$pattern'" | Select-Object -ExpandProperty Name | Sort-Object
                            $results += $computers
                        }} catch {{
                            # Fallback to direct pattern if AD search fails
                            if (Test-Connection -ComputerName $pattern -Count 1 -Quiet -ErrorAction SilentlyContinue) {{
                                $results += $pattern
                            }}
                        }}
                    }} else {{
                        # It's a direct computer name
                        $results += $pattern
                    }}
                }}
                
                $results = $results | Sort-Object -Unique
                
                if ($results.Count -eq 0) {{
                    throw "No computers found matching the specified pattern(s)"
                }}

                $computerStatus = @()
                foreach ($computer in $results) {{
                    $status = @{{
                        Name = $computer
                        Online = Test-Connection -ComputerName $computer -Count 1 -Quiet
                    }}
                    $computerStatus += $status
                }}
                
                $computerStatus | ConvertTo-Json
                '''

                process = subprocess.Popen(["powershell", "-Command", ps_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    raise Exception(stderr.decode())

                computers = json.loads(stdout.decode())
                if not isinstance(computers, list):
                    computers = [computers]

                if not computers:
                    raise Exception("No computers found matching the specified pattern(s)")

                def create_restart_button(computer_name):
                    return lambda: self.restart_computer(computer_name)

                def create_shutdown_button(computer_name):
                    return lambda: self.shutdown_computer(computer_name)

                # Create the "Restart All Online" button if there are online computers
                online_computers = [c["Name"] for c in computers if c["Online"]]
                if online_computers:
                    restart_all_frame = ctk.CTkFrame(self.computers_frame)
                    restart_all_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
                    
                    restart_all_btn = ctk.CTkButton(
                        restart_all_frame,
                        text=f"Restart All Online Computers ({len(online_computers)})",
                        command=lambda: self.restart_all_computers(online_computers),
                        fg_color=COLORS["accent"],
                        hover_color=COLORS["accent_hover"]
                    )
                    restart_all_btn.pack(fill="x", padx=5)

                    shutdown_all_btn = ctk.CTkButton(
                        restart_all_frame,
                        text=f"Shutdown All Online Computers ({len(online_computers)})",
                        command=lambda: self.shutdown_all_computers(online_computers),
                        fg_color="#dc3545",  # Red color for shutdown
                        hover_color="#c82333"
                    )
                    shutdown_all_btn.pack(fill="x", padx=5)

                # Display each computer with its status
                for i, computer in enumerate(computers, start=1):
                    computer_frame = ctk.CTkFrame(self.computers_frame, fg_color='#2E2E2E' if i % 2 == 0 else '#1C1C1C')
                    computer_frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
                    computer_frame.grid_columnconfigure(1, weight=1)

                    # Status indicator
                    status_color = "#28a745" if computer["Online"] else "#dc3545"
                    status_label = ctk.CTkLabel(
                        computer_frame,
                        text="●",
                        text_color=status_color,
                        font=("Segoe UI", 14)
                    )
                    status_label.grid(row=0, column=0, padx=(5,0))

                    # Computer name
                    name_label = ctk.CTkLabel(
                        computer_frame,
                        text=f"{computer['Name']} ({'Online' if computer['Online'] else 'Offline'})",
                        anchor="w"
                    )
                    name_label.grid(row=0, column=1, padx=5, sticky="w")

                    # Restart button (enabled only if online)
                    restart_btn = ctk.CTkButton(
                        computer_frame,
                        text="Restart",
                        command=create_restart_button(computer["Name"]),
                        width=80,
                        state="normal" if computer["Online"] else "disabled",
                        fg_color=COLORS["accent"],
                        hover_color=COLORS["accent_hover"]
                    )
                    restart_btn.grid(row=0, column=2, padx=5)

                    # Shutdown button (enabled only if online)
                    shutdown_btn = ctk.CTkButton(
                        computer_frame,
                        text="Shutdown",
                        command=create_shutdown_button(computer["Name"]),
                        width=80,
                        state="normal" if computer["Online"] else "disabled",
                        fg_color="#dc3545",  # Red color for shutdown
                        hover_color="#c82333"
                    )
                    shutdown_btn.grid(row=0, column=3, padx=5)

                    self.computers.append(computer["Name"])

                self.append_output(f"Found {len(computers)} computers ({len(online_computers)} online)\n")

            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                self.append_output("\nTroubleshooting steps:\n")
                self.append_output("1. Run these PowerShell commands as administrator on both computers:\n")
                self.append_output("   winrm quickconfig\n")
                self.append_output("   Enable-PSRemoting -Force\n\n")
                self.append_output("2. Configure WinRM trusted hosts (run as administrator):\n")
                self.append_output(f"   Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value {computer_input} -Force\n\n")
                self.append_output("3. Verify you are running the application as Administrator\n")
                self.append_output("4. Check that WinRM is properly configured:\n")
                self.append_output("   - Ensure WinRM ports (5985, 5986) are open\n")
                self.append_output("   - Temporarily disable firewall to test connectivity\n\n")
                self.append_output("5. Verify network connectivity:\n")
                self.append_output(f"   ping {computer_input}\n\n")
                self.append_output("6. Check credentials and permissions:\n")
                self.append_output("   - Run the application as administrator\n")
                self.append_output("   - Ensure you have admin rights on the remote computer\n")
                
        threading.Thread(target=execute_search).start()
    
    def restart_computer(self, computer_name):
        self.append_output(f"\nInitiating restart for {computer_name}...\n")

        def execute_restart():
            try:
                # Clean computer name - remove any backslashes and spaces
                clean_computer_name = computer_name.strip('\\').strip()
                
                # PowerShell script to restart computer with multiple fallback methods
                ps_script = f'''
                $ErrorActionPreference = "Stop"
                $computerName = "{clean_computer_name}"

                if (Test-Connection $computerName -Count 1 -Quiet) {{
                    try {{
                        Write-Output "Attempting restart via Invoke-Command..."
                        Invoke-Command -ComputerName $computerName -ScriptBlock {{ Restart-Computer -Force }}
                        Write-Output "Restart command sent successfully via Invoke-Command"
                        exit 0
                    }} catch {{
                        Write-Output "Invoke-Command failed, trying shutdown command..."
                        try {{
                            $result = shutdown.exe /r /m \\$computerName /t 10 /f /c "TaskForce: System will restart in 10 seconds"
                            if ($LASTEXITCODE -eq 0) {{
                                Write-Output "Restart command sent successfully via shutdown.exe"
                                exit 0
                            }}
                            Write-Output "Shutdown command failed, trying WMI..."
                        }} catch {{
                            Write-Output "Shutdown command failed, trying WMI..."
                        }}
                        try {{
                            Write-Output "Attempting restart via WMI..."
                            $os = Get-WmiObject -Class Win32_OperatingSystem -ComputerName $computerName
                            $result = $os.Win32Shutdown(6)
                            if ($result.ReturnValue -eq 0) {{
                                Write-Output "Restart command sent successfully via WMI"
                                exit 0
                            }}
                            Write-Output "WMI restart failed"
                            exit 1
                        }} catch {{
                            Write-Output "ERROR: Failed to restart computer"
                            Write-Output $_.Exception.Message
                            exit 1
                        }}
                    }}
                }} else {{
                    Write-Output "Unable to connect to $computerName. Please verify the computer name and network connectivity."
                    exit 1
                }}
                '''
                
                # Execute the PowerShell command with detailed output
                process = subprocess.Popen(
                    ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.append_output(output.strip())

                process.wait()
                self.append_output("Restart completed.")

            except Exception as e:
                self.output_text.configure(state="normal")
                self.output_text.insert("end", f"System Error: {str(e)}\n")
                self.output_text.configure(state="disabled")
                self.output_text.see("end")
                
        thread = threading.Thread(target=execute_restart)
        thread.daemon = True
        thread.start()

    def shutdown_computer(self, computer_name):
        self.append_output(f"\nInitiating shutdown for {computer_name}...\n")

        def execute_shutdown():
            try:
                # Clean computer name - remove any backslashes and spaces
                clean_computer_name = computer_name.strip('\\').strip()
                
                # PowerShell script to shutdown computer with multiple fallback methods
                ps_script = f'''
                $ErrorActionPreference = "Stop"
                $computerName = "{clean_computer_name}"

                if (Test-Connection $computerName -Count 1 -Quiet) {{
                    try {{
                        Write-Output "Attempting shutdown via Invoke-Command..."
                        Invoke-Command -ComputerName $computerName -ScriptBlock {{ Stop-Computer -Force }}
                        Write-Output "Shutdown command sent successfully via Invoke-Command"
                        exit 0
                    }} catch {{
                        Write-Output "Invoke-Command failed, trying shutdown command..."
                        try {{
                            $result = shutdown.exe /s /m \\$computerName /t 10 /f /c "TaskForce: System will shutdown in 10 seconds"
                            if ($LASTEXITCODE -eq 0) {{
                                Write-Output "Shutdown command sent successfully via shutdown.exe"
                                exit 0
                            }}
                            Write-Output "Shutdown command failed, trying WMI..."
                        }} catch {{
                            Write-Output "Shutdown command failed, trying WMI..."
                        }}
                        try {{
                            Write-Output "Attempting shutdown via WMI..."
                            $os = Get-WmiObject -Class Win32_OperatingSystem -ComputerName $computerName
                            $result = $os.Win32Shutdown(5)
                            if ($result.ReturnValue -eq 0) {{
                                Write-Output "Shutdown command sent successfully via WMI"
                                exit 0
                            }}
                            Write-Output "WMI shutdown failed"
                            exit 1
                        }} catch {{
                            Write-Output "ERROR: Failed to shutdown computer"
                            Write-Output $_.Exception.Message
                            exit 1
                        }}
                    }}
                }} else {{
                    Write-Output "Unable to connect to $computerName. Please verify the computer name and network connectivity."
                    exit 1
                }}
                '''
                
                # Execute the PowerShell command with detailed output
                process = subprocess.Popen(
                    ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.append_output(output.strip())

                process.wait()
                self.append_output("Shutdown command completed.")

            except Exception as e:
                self.output_text.configure(state="normal")
                self.output_text.insert("end", f"System Error: {str(e)}\n")
                self.output_text.configure(state="disabled")
                self.output_text.see("end")
                
        thread = threading.Thread(target=execute_shutdown)
        thread.daemon = True
        thread.start()

    def restart_all_computers(self, computers):
        if not computers:
            return

        if not messagebox.askyesno("Confirm Restart", f"Are you sure you want to restart {len(computers)} computers?"):
            return

        self.append_output(f"\nRestarting {len(computers)} computers...\n")
        for computer in computers:
            self.restart_computer(computer)
        
    def shutdown_all_computers(self, computers):
        if not computers:
            return

        if not messagebox.askyesno("Confirm Shutdown", f"Are you sure you want to shutdown {len(computers)} computers?"):
            return

        self.append_output(f"\nShutting down {len(computers)} computers...\n")
        for computer in computers:
            self.shutdown_computer(computer)
        
    def append_output(self, text):
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.configure(state="disabled")
            self.output_text.see("end")
        
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.after(0, update)
            
    def clear_history(self):
        # Clear output text
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
        # Clear computer list
        for widget in self.computers_frame.winfo_children():
            widget.destroy()
        self.computers = []
        
class ScrollableRenamePCFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Initialize domains list
        self.domains = []
        try:
            if os.path.exists('domains.json'):
                with open('domains.json', 'r') as f:
                    data = json.load(f)
                    self.domains = [d['name'] for d in data.get('domains', [])]
            if not self.domains:  # fallback to defaults if no domains loaded
                self.domains = ["centrogs\\", "hitachi\\", "domain\\"]
        except Exception as e:
            self.domains = ["centrogs\\", "hitachi\\", "domain\\"]
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="PC Rename",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Input frame in the main scrollable area
        self.input_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # PC name input
        self.current_pc_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Enter current PC name",
            width=300,
            height=35,
            fg_color="transparent"
        )
        self.current_pc_entry.grid(row=0, column=0, padx=20, pady=10)
        self.current_pc_entry.bind("<Return>", lambda event: self.rename_pc())
        
        # New PC name input
        self.new_pc_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Enter new PC name",
            width=300,
            height=35,
            fg_color="transparent"
        )
        self.new_pc_entry.grid(row=1, column=0, padx=20, pady=10)
        self.new_pc_entry.bind("<Return>", lambda event: self.rename_pc())
        
        # Username input
        self.username_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter username",
            width=300,
            height=35,
            fg_color="transparent"
        )
        self.username_entry.grid(row=2, column=0, padx=20, pady=10)
        
        # Password input
        self.password_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter password",
            show="*",
            width=300,
            height=35,
            fg_color="transparent"
        )
        self.password_entry.grid(row=3, column=0, padx=20, pady=10)
        self.password_entry.bind("<Return>", lambda event: self.rename_pc())
        
        # Domain selection frame
        self.domain_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.domain_frame.grid(row=4, column=0, padx=20, pady=10)
        
        # Domain dropdown with edit button
        self.domain_var = ctk.StringVar(value=self.domains[0])
        self.domain_dropdown = ctk.CTkOptionMenu(
            self.domain_frame,
            values=self.domains,
            variable=self.domain_var,
            width=255,
            height=35,
            fg_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"]
        )
        self.domain_dropdown.grid(row=0, column=0, padx=(0,10))
        
        # Edit domains button
        self.edit_domains_button = ctk.CTkButton(
            self.domain_frame,
            text="Edit",
            width=35,
            height=35,
            command=self.open_domain_manager,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.edit_domains_button.grid(row=0, column=1)
        
        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.action_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.action_frame.grid_columnconfigure((0,1), weight=1)
        
        # Buttons
        self.rename_button = ctk.CTkButton(
            self.action_frame,
            text="Rename PC",
            command=self.rename_pc,
            width=120,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.rename_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.clear_button = ctk.CTkButton(
            self.action_frame,
            text="Clear Output",
            command=self.clear_output,
            width=120,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.clear_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Break/Stop button
        self.break_button = ctk.CTkButton(
            self.action_frame,
            text="Break",
            command=self.break_operation,
            width=120,
            height=35,
            fg_color="#dc3545",  # Red color for break
            hover_color="#c82333",
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.break_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Output text
        self.output_text = ctk.CTkTextbox(
            self.main_scrollable,
            height=200,
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"]
        )
        self.output_text.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        self.configure_scrollable_content()
        
        # Store process reference for termination
        self.current_process = None
        
    def open_domain_manager(self):
        DomainManagerDialog(self, self.update_domains)
    
    def update_domains(self, new_domains):
        if new_domains:  
            self.domains = new_domains
            self.domain_dropdown.configure(values=self.domains)
            self.domain_var.set(self.domains[0])
            # Save domains to file
            with open('domains.json', 'w') as f:
                json.dump({'domains': [{'name': d} for d in new_domains]}, f, indent=4)
    
    def break_operation(self):
        """Break/stop the current operation"""
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.append_output("\n[BREAK] Operation terminated by user.\n")
            except Exception as e:
                self.append_output(f"\n[ERROR] Failed to terminate operation: {str(e)}\n")
        else:
            self.append_output("\n[INFO] No active operation to break.\n")
    
    def rename_pc(self):
        current_pc = self.current_pc_entry.get().strip()
        new_pc = self.new_pc_entry.get().strip()
        domain = self.domain_var.get()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Combine domain and username if username doesn't already include domain
        if not username.startswith(domain):
            username = f"{domain}{username}"
        
        if not all([current_pc, new_pc, username, password]):
            messagebox.showerror("Error", "Please enter all required fields")
            return
        
        # Add timestamp to output
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.append_output(f"\n[{timestamp}] Starting rename operation for {current_pc}...\n")
        
        def execute():
            try:
                ps_script = f'''
                $ErrorActionPreference = "Stop"
                $securePassword = ConvertTo-SecureString "{password}" -AsPlainText -Force
                $credentials = New-Object System.Management.Automation.PSCredential ("{username}", $securePassword)

                Write-Output "Testing connection to {current_pc}..."
                if (Test-Connection {current_pc} -Count 1 -Quiet) {{
                    Write-Output "Connection successful. Verifying credentials..."
                    
                    # First, verify credentials work with different transport options
                    $credentialTestFailed = $false
                    $credentialTestError = ""
                    
                    # Test with basic connection first
                    try {{
                        Write-Output "Testing credentials with basic connection..."
                        $testSession = New-PSSession -ComputerName {current_pc} -Credential $credentials -ErrorAction Stop
                        Remove-PSSession $testSession
                        Write-Output "Credentials verified successfully with basic connection."
                    }} catch {{
                        Write-Output "Basic connection failed: $($_.Exception.Message)"
                        $credentialTestFailed = $true
                        $credentialTestError = $_.Exception.Message
                        
                        # Try with HTTPS (WinRM over SSL)
                        try {{
                            Write-Output "Testing credentials with HTTPS (WinRM over SSL)..."
                            $testSession = New-PSSession -ComputerName {current_pc} -Credential $credentials -UseSSL -ErrorAction Stop
                            Remove-PSSession $testSession
                            Write-Output "Credentials verified successfully with HTTPS."
                            $credentialTestFailed = $false
                        }} catch {{
                            Write-Output "HTTPS connection failed: $($_.Exception.Message)"
                        }}
                    }}
                    
                    if ($credentialTestFailed) {{
                        Write-Output "ERROR: Credential verification failed."
                        Write-Output "Last error: $credentialTestError"
                        Write-Output "Please check:"
                        Write-Output "1. Username and password are correct"
                        Write-Output "2. Account has domain administrator privileges"
                        Write-Output "3. Account is not locked or disabled"
                        Write-Output "4. You are using the correct domain format (e.g., DOMAIN\\username)"
                        Write-Output "5. WinRM is enabled on target: Enable-PSRemoting -Force"
                        Write-Output "6. For HTTPS, ensure SSL certificate is configured on target"
                        exit 1
                    }}
                    
                    Write-Output "Attempting to rename computer..."
                    
                    # Method 1: Try Rename-Computer cmdlet first (most reliable)
                    try {{
                        Write-Output "Method 1: Trying Rename-Computer cmdlet..."
                        Rename-Computer -ComputerName {current_pc} -NewName "{new_pc}" -DomainCredential $credentials -Force -Restart -ErrorAction Stop
                        Write-Output "Successfully renamed computer from {current_pc} to {new_pc} using Rename-Computer."
                        Write-Output "Computer will restart automatically to apply changes."
                        exit 0
                    }} catch {{
                        Write-Output "Method 1 failed: $($_.Exception.Message)"
                        Write-Output "Attempting fallback methods..."
                    }}
                    
                    # Method 2: Try netdom command (works better in restricted network environments)
                    try {{
                        Write-Output "Method 2: Trying netdom command..."
                        $netdomResult = netdom renamecomputer {current_pc} /NewName:"{new_pc}" /UserD:"{username}" /PasswordD:"{password}" /Force /Reboot 2>&1
                        if ($LASTEXITCODE -eq 0) {{
                            Write-Output "Successfully renamed computer from {current_pc} to {new_pc} using netdom."
                            Write-Output "Computer will restart automatically to apply changes."
                            exit 0
                        }} else {{
                            Write-Output "Method 2 failed with exit code: $LASTEXITCODE"
                            Write-Output "Netdom output: $netdomResult"
                        }}
                    }} catch {{
                        Write-Output "Method 2 failed: $($_.Exception.Message)"
                    }}
                    
                    # Method 3: Try WMI with different approach
                    try {{
                        Write-Output "Method 3: Trying WMI method..."
                        $wmic = Get-WmiObject -Class Win32_ComputerSystem -ComputerName {current_pc} -Credential $credentials
                        $wmic.Rename("{new_pc}")
                        Write-Output "Successfully renamed computer from {current_pc} to {new_pc} using WMI."
                        Write-Output "Restarting computer to apply changes..."
                        Restart-Computer -ComputerName {current_pc} -Credential $credentials -Force
                        exit 0
                    }} catch {{
                        Write-Output "Method 3 failed: $($_.Exception.Message)"
                    }}
                    
                    # Method 4: Try PowerShell remoting with Invoke-Command (HTTP)
                    try {{
                        Write-Output "Method 4: Trying PowerShell remoting (HTTP)..."
                        Invoke-Command -ComputerName {current_pc} -Credential $credentials -ScriptBlock {{
                            param($newName)
                            Rename-Computer -NewName $newName -Force -Restart
                        }} -ArgumentList "{new_pc}"
                        Write-Output "Successfully renamed computer from {current_pc} to {new_pc} using PowerShell remoting."
                        exit 0
                    }} catch {{
                        Write-Output "Method 4 failed: $($_.Exception.Message)"
                    }}
                    
                    # Method 5: Try PowerShell remoting with HTTPS (secure protocol)
                    try {{
                        Write-Output "Method 5: Trying PowerShell remoting with HTTPS..."
                        $sessionOptions = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck
                        Invoke-Command -ComputerName {current_pc} -Credential $credentials -UseSSL -SessionOption $sessionOptions -ScriptBlock {{
                            param($newName)
                            Rename-Computer -NewName $newName -Force -Restart
                        }} -ArgumentList "{new_pc}"
                        Write-Output "Successfully renamed computer from {current_pc} to {new_pc} using PowerShell remoting over HTTPS."
                        exit 0
                    }} catch {{
                        Write-Output "Method 5 failed: $($_.Exception.Message)"
                    }}
                    
                    # Method 6: Try using Active Directory directly (LDAP/LDAPS)
                    try {{
                        Write-Output "Method 6: Trying Active Directory direct operation..."
                        # This requires the Active Directory module and appropriate permissions
                        Import-Module ActiveDirectory -ErrorAction Stop
                        
                        # Get the computer object from AD
                        $computerObj = Get-ADComputer -Identity {current_pc} -ErrorAction Stop
                        
                        # Try to rename using AD cmdlet (this changes the AD object, not the computer itself)
                        # Note: This only renames the AD object, the computer still needs to be joined with new name
                        Write-Output "AD computer object found. Note: This only renames the AD object."
                        Write-Output "The computer itself will need to be rejoined with the new name."
                        Write-Output "This method is not recommended for complete rename operations."
                        
                    }} catch {{
                        Write-Output "Method 6 failed: $($_.Exception.Message)"
                    }}
                    
                    # All methods failed
                    Write-Output "ERROR: All rename methods failed."
                    Write-Output "Common causes and solutions:"
                    Write-Output "1. ACCESS DENIED: Your account lacks sufficient privileges"
                    Write-Output "   - Use a Domain Admin account"
                    Write-Output "   - Ensure the account has 'Rename Computer' rights in AD"
                    Write-Output "2. RPC UNAVAILABLE: Network/firewall blocking RPC"
                    Write-Output "   - Enable RPC services on target computer"
                    Write-Output "   - Check firewall allows RPC (ports 135, 445)"
                    Write-Output "3. WINRM NOT ENABLED: PowerShell remoting not available"
                    Write-Output "   - Run 'Enable-PSRemoting -Force' on target computer"
                    Write-Output "   - For HTTPS: 'Enable-PSRemoting -Force' then 'Set-WSManQuickConfig -ForceTransport HTTPS'"
                    Write-Output "4. HTTPS/SSL ISSUES: Certificate problems"
                    Write-Output "   - Ensure SSL certificate is valid on target computer"
                    Write-Output "   - Or use -SkipCACheck for testing (not recommended for production)"
                    Write-Output "5. UAC ISSUES: User Account Control blocking"
                    Write-Output "   - Try disabling UAC temporarily on target computer"
                    Write-Output "6. COMPUTER ALREADY RENAMED: Target name already exists"
                    Write-Output "   - Check if new computer name is already in use in AD"
                    exit 1
                    
                }} else {{
                    Write-Output "Unable to connect to {current_pc}. Please verify the computer name and network connectivity."
                    exit 1
                }}
                '''
                
                # Use Popen for real-time output streaming
                self.current_process = subprocess.Popen(
                    ["powershell", "-Command", ps_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Stream output in real-time
                while True:
                    output = self.current_process.stdout.readline()
                    if output == '' and self.current_process.poll() is not None:
                        break
                    if output:
                        self.append_output(output.strip())
                
                # Check for errors
                if self.current_process.returncode != 0:
                    self.append_output(f"\nOperation failed with exit code: {self.current_process.returncode}")
                
                self.current_process = None
                    
            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                self.current_process = None
        
        threading.Thread(target=execute).start()
    
    def append_output(self, text):
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        self.output_text.configure(state="disabled")
        self.output_text.see("end")
    
    def clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
class ScrollableNetworkFrame(ScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame
        self.main_scrollable = ctk.CTkScrollableFrame(self)
        self.main_scrollable.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_scrollable.grid_rowconfigure(0, weight=1)
        self.main_scrollable.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)  # Make output frame expand
        
        # Title Label
        self.title_label = ctk.CTkLabel(
            main_frame,
            text="Network",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text"]
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))
        
        # PC Name input
        pc_label = ctk.CTkLabel(main_frame, text="PC Name:", text_color=COLORS["text"])
        pc_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.pc_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter PC name (supports wildcards like PC* or PC-1,PC-2)",
            fg_color="transparent"
        )
        self.pc_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.pc_entry.bind("<Return>", lambda event: self.execute_network_command("ping"))
        
        # Destination input
        dest_label = ctk.CTkLabel(main_frame, text="Destination:", text_color=COLORS["text"])
        dest_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.dest_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter destination (required for ping/traceroute)",
            fg_color="transparent"
        )
        self.dest_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.dest_entry.bind("<Return>", lambda event: self.execute_network_command("ping"))
        
        # Buttons Frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        buttons_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        # Network Operation Buttons
        ctk.CTkButton(
            buttons_frame,
            text="Ping",
            command=lambda: self.execute_network_command("ping"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Traceroute",
            command=lambda: self.execute_network_command("traceroute"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="GPUpdate",
            command=lambda: self.execute_network_command("gpupdate"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        ).grid(row=0, column=2, padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Netstat",
            command=lambda: self.execute_network_command("netstat"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        ).grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Flush DNS",
            command=lambda: self.execute_network_command("flushdns"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        ).grid(row=0, column=4, padx=5, pady=5)
        
        # Output Frame with Border
        output_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS["bg_medium"],
            border_color=COLORS["border"],
            border_width=2
        )
        output_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        
        # Output Header
        output_header = ctk.CTkLabel(
            output_frame,
            text="Network",
            font=("Roboto", 16, "bold"),
            text_color=COLORS["text"],
            fg_color="transparent"
        )
        output_header.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Output Text
        self.output_text = ctk.CTkTextbox(
            output_frame,
            fg_color="transparent",
            text_color=COLORS["text"],
            border_width=0
        )
        self.output_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.output_text.configure(state="disabled")

    def append_output(self, text):
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        self.output_text.configure(state="disabled")
        self.output_text.see("end")
        
    def execute_network_command(self, command_type):
        pc_name = self.pc_entry.get().strip()
        destination = self.dest_entry.get().strip()
        
        if not pc_name:
            messagebox.showerror("Error", "Please enter a PC name")
            return
            
        if command_type in ["ping", "traceroute"] and not destination:
            messagebox.showerror("Error", "Please enter a destination for ping/traceroute")
            return
            
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.append_output(f"\n{timestamp} Executing {command_type} command...\n")

        def execute():
            try:
                # Base PowerShell script with error handling
                ps_script = f'''
                $ErrorActionPreference = "Stop"
                $computerName = "{pc_name}"

                if ("{pc_name}" -match "[*?]") {{
                    $computers = Get-ADComputer -Filter "Name -like '$pc_name'" | Select-Object -ExpandProperty Name
                }} else {{
                    $computers = @("{pc_name}")
                }}

                foreach ($computer in $computers) {{
                    Write-Output "`nProcessing computer: $computer"
                    if (-not (Test-Connection -ComputerName $computer -Count 1 -Quiet)) {{
                        Write-Output "Cannot connect to $computer. Skipping..."
                        continue
                    }}
                '''
                
                # Add command-specific PowerShell code
                if command_type == "ping":
                    ps_script += f'''
                        Invoke-Command -ComputerName $computer -ScriptBlock {{
                            Test-Connection -ComputerName "{destination}" -Count 4 -ErrorAction Stop
                        }}
                    '''
                elif command_type == "traceroute":
                    ps_script += f'''
                        Invoke-Command -ComputerName $computer -ScriptBlock {{
                            $result = cmd /c "tracert {destination}"
                            $result | ForEach-Object {{ Write-Host $_ }}
                        }}
                    '''
                elif command_type == "gpupdate":
                    ps_script += '''
                        Invoke-Command -ComputerName $computer -ScriptBlock {
                            gpupdate /force
                        }
                    '''
                elif command_type == "netstat":
                    ps_script += '''
                        Invoke-Command -ComputerName $computer -ScriptBlock {
                            netstat -ano
                        }
                    '''
                elif command_type == "flushdns":
                    ps_script += '''
                        Invoke-Command -ComputerName $computer -ScriptBlock {
                            ipconfig /flushdns
                        }
                    '''
                
                # Close the try-catch blocks
                ps_script += '''
                    }
                } catch {{
                    Write-Output "ERROR: Failed to execute command"
                    Write-Output $_.Exception.Message
                    throw
                }}
                '''
                
                # Execute the PowerShell script
                process = subprocess.Popen(
                    ["powershell", "-Command", ps_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    self.append_output(stdout)
                if stderr:
                    self.append_output(f"Error: {stderr}")
                    
            except Exception as e:
                self.append_output(f"Error: {str(e)}\n")
                
        threading.Thread(target=execute).start()

class TaskForceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Set app icon
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                icon_path = os.path.join(sys._MEIPASS, "TF.ico")
            else:
                # Running in development
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TF.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"Warning: Icon file not found at {icon_path}")
        except Exception as e:
            print(f"Warning: Could not set application icon: {str(e)}")
            
        # Configure window
        self.title("TaskForce System Management Tool")
        self.geometry("1000x600")  # Increased width to 1000px
        
        # Configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create navigation frame
        self.navigation_frame = ctk.CTkFrame(
            self, 
            corner_radius=10,
            fg_color="#1a1b26",
            border_color=COLORS["border"],
            border_width=2,
            width=250  # Fixed width for navigation
        )
        self.navigation_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.navigation_frame.grid_rowconfigure(1, weight=1)
        self.navigation_frame.grid_columnconfigure(0, weight=1)
        self.navigation_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        # Navigation frame label
        self.navigation_frame_label = ctk.CTkLabel(
            self.navigation_frame, 
            text="TaskForce", 
            font=("Roboto", 15, "bold"),
            text_color="white"
        )
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=(20,10))

        # Create scrollable frame for buttons
        self.nav_buttons_frame = ctk.CTkScrollableFrame(
            self.navigation_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent"],
            scrollbar_button_hover_color=COLORS["accent_hover"],
            orientation="vertical"
        )
        self.nav_buttons_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.nav_buttons_frame.grid_rowconfigure(11, weight=1)

        # Create navigation buttons with consistent spacing
        self.system_info_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="System Info",
            command=self.system_info_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color="transparent",
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.system_info_button.grid(row=1, column=0, sticky="ew", pady=2)
        
        self.user_info_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="User Info",
            command=self.user_info_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color="transparent",
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.user_info_button.grid(row=2, column=0, sticky="ew", pady=2)
        
        self.group_policy_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Group Policy",
            command=self.group_policy_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color="transparent",
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.group_policy_button.grid(row=3, column=0, sticky="ew", pady=2)
        
        self.bulk_user_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Bulk User",
            command=self.bulk_user_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color="transparent",
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.bulk_user_button.grid(row=4, column=0, sticky="ew", pady=2)
        
        self.app_install_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="App Install",
            command=self.app_install_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.app_install_button.grid(row=5, column=0, sticky="ew", pady=2)
        
        self.app_uninstall_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="App Uninstall",
            command=self.app_uninstall_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.app_uninstall_button.grid(row=6, column=0, sticky="ew", pady=2)
        
        self.change_password_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Change Password",
            command=self.change_password_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.change_password_button.grid(row=7, column=0, sticky="ew", pady=2)
        
        self.update_restart_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Power Control",
            command=self.update_restart_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.update_restart_button.grid(row=8, column=0, sticky="ew", pady=2)
        
        self.rename_pc_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Rename PC",
            command=self.rename_pc_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.rename_pc_button.grid(row=9, column=0, sticky="ew", pady=2)
        
        self.network_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Network Tools",
            command=self.network_button_event,
            corner_radius=0,
            height=40,
            border_spacing=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.network_button.grid(row=10, column=0, sticky="ew", pady=2)
        
        # Create frames for each section
        self.system_info_frame = ScrollableSystemInfoFrame(self)
        self.user_info_frame = ScrollableUserInfoFrame(self)
        self.group_policy_frame = ScrollableGroupPolicyFrame(self)
        self.bulk_user_frame = ScrollableBulkUserFrame(self)
        self.app_install_frame = ScrollableAppInstallFrame(self)
        self.app_uninstall_frame = ScrollableAppUninstallFrame(self)  
        self.change_password_frame = ScrollablePasswordChangeFrame(self)
        self.update_restart_frame = ScrollableUpdateRestartFrame(self)
        self.rename_pc_frame = ScrollableRenamePCFrame(self)
        self.network_frame = ScrollableNetworkFrame(self)

        # Select default frame
        self.select_frame_by_name("system_info")

        # Add banner at the bottom
        banner_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", height=30)
        banner_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        banner_frame.grid_columnconfigure(0, weight=1)
        banner_frame.grid_rowconfigure(0, weight=1)
        banner_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        # Configure banner frame grid
        banner_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Add subtle design elements
        left_accent = ctk.CTkFrame(banner_frame, fg_color="#4a9eff", width=50, height=2)
        left_accent.grid(row=0, column=0, sticky="e", padx=(0, 10), pady=14)
        
        # Create banner text
        banner_text = "Developed By A.Sokary"
        banner_label = ctk.CTkLabel(
            banner_frame,
            text=banner_text,
            font=("Segoe UI", 12, "bold"),
            text_color="#4a9eff",  # Modern blue color
            fg_color="transparent"
        )
        banner_label.grid(row=0, column=1, pady=5)
        
        right_accent = ctk.CTkFrame(banner_frame, fg_color="#4a9eff", width=50, height=2)
        right_accent.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=14)
        
    def select_frame_by_name(self, name):
        # Hide all frames
        self.system_info_frame.grid_remove()
        self.user_info_frame.grid_remove()
        self.group_policy_frame.grid_remove()
        self.bulk_user_frame.grid_remove()
        self.app_install_frame.grid_remove()
        self.app_uninstall_frame.grid_remove()
        self.change_password_frame.grid_remove()
        self.update_restart_frame.grid_remove()
        self.rename_pc_frame.grid_remove()
        self.network_frame.grid_remove()

        # Reset button colors
        self.system_info_button.configure(fg_color="transparent")
        self.user_info_button.configure(fg_color="transparent")
        self.group_policy_button.configure(fg_color="transparent")
        self.bulk_user_button.configure(fg_color="transparent")
        self.app_install_button.configure(fg_color="transparent")
        self.app_uninstall_button.configure(fg_color="transparent")
        self.change_password_button.configure(fg_color="transparent")
        self.update_restart_button.configure(fg_color="transparent")
        self.rename_pc_button.configure(fg_color="transparent")
        self.network_button.configure(fg_color="transparent")
        
        # Show selected frame
        if name == "system_info":
            self.system_info_frame.grid(row=0, column=1, sticky="nsew")
            self.system_info_button.configure(fg_color=COLORS["accent"])
        
        elif name == "user_info":
            self.user_info_frame.grid(row=0, column=1, sticky="nsew")
            self.user_info_button.configure(fg_color=COLORS["accent"])
            
        elif name == "group_policy":
            self.group_policy_frame.grid(row=0, column=1, sticky="nsew")
            self.group_policy_button.configure(fg_color=COLORS["accent"])
            
        elif name == "bulk_user":
            self.bulk_user_frame.grid(row=0, column=1, sticky="nsew")
            self.bulk_user_button.configure(fg_color=COLORS["accent"])
            
        elif name == "app_install":
            self.app_install_frame.grid(row=0, column=1, sticky="nsew")
            self.app_install_button.configure(fg_color=COLORS["accent"])
            
        elif name == "app_uninstall":
            self.app_uninstall_frame.grid(row=0, column=1, sticky="nsew")
            self.app_uninstall_button.configure(fg_color=COLORS["accent"])
            
        elif name == "change_password":
            self.change_password_frame.grid(row=0, column=1, sticky="nsew")
            self.change_password_button.configure(fg_color=COLORS["accent"])
            
        elif name == "update_restart":
            self.update_restart_frame.grid(row=0, column=1, sticky="nsew")
            self.update_restart_button.configure(fg_color=COLORS["accent"])
            
        elif name == "rename_pc":
            self.rename_pc_frame.grid(row=0, column=1, sticky="nsew")
            self.rename_pc_button.configure(fg_color=COLORS["accent"])
            
        elif name == "network":
            self.network_frame.grid(row=0, column=1, sticky="nsew")
            self.network_button.configure(fg_color=COLORS["accent"])
            
    def system_info_button_event(self):
        self.select_frame_by_name("system_info")

    def user_info_button_event(self):
        self.select_frame_by_name("user_info")

    def group_policy_button_event(self):
        self.select_frame_by_name("group_policy")

    def bulk_user_button_event(self):
        self.select_frame_by_name("bulk_user")

    def app_install_button_event(self):
        self.select_frame_by_name("app_install")

    def app_uninstall_button_event(self):
        self.select_frame_by_name("app_uninstall")

    def change_password_button_event(self):
        self.select_frame_by_name("change_password")

    def update_restart_button_event(self):
        self.select_frame_by_name("update_restart")

    def rename_pc_button_event(self):
        self.select_frame_by_name("rename_pc")

    def network_button_event(self):
        self.select_frame_by_name("network")

if __name__ == "__main__":
    app = TaskForceApp()
    app.mainloop()
