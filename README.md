# TaskForce

A comprehensive IT administration toolkit combining PowerShell and Python for managing Windows environments, Active Directory, and network operations.

![TaskForce](TF.ico)

## Overview

TaskForce is a dual-interface application (GUI and CLI) designed for IT administrators to streamline common system administration tasks including user management, system monitoring, software deployment, and network diagnostics.

## Features

### System Administration
- **System Information**: Retrieve detailed hardware, OS, and performance metrics from remote computers
- **User Information**: Search Active Directory for user details by name, employee ID, or office
- **Group Policy Management**: View and verify applied group policies on computers and users
- **PC Rename**: Rename computers in the domain with credential management

### User Management
- **Bulk User Management**: Handle multiple user operations efficiently.
  - **New Batch Processing**: 
    - Process new user creations
    - Import from CSV/Excel
    - Set default parameters
    - Tips:
      - Verify data before bulk operations
      - Use templates for imports
      - Check output for operation status
- **Password Management**: Reset passwords, unlock accounts, force password changes

### Application Management
- **Remote Installation**: Deploy software to remote computers from network shares
- **Remote Uninstallation**: Remove software from remote computers
- **Path Management**: Configure and manage application installation paths

### Network & System Operations
- **Remote Restart**: Restart single or multiple computers with wildcard support
- **Network Tools**: Ping, traceroute, GPUpdate, netstat, DNS flush
- **Update Management**: Install Windows updates remotely

## Screenshots

*(Add screenshots of the GUI interface here)*

## Requirements

### System Requirements
- Windows 10/11 or Windows Server 2016+
- Active Directory domain membership
- Administrator privileges on target computers
- PowerShell 5.1 or higher
- Python 3.8 or higher

### Python Dependencies
```bash
pip install customtkinter
```

### PowerShell Modules
- ActiveDirectory module
- GroupPolicy module (for some features)

## Installation

### Step 1: Clone or Download
```bash
git clone https://github.com/yourusername/TaskForce.git
```

Or download and extract the ZIP file.

### Step 2: File Placement
Move the TaskForce folder to:
```
C:\TaskForce\
```

### Step 3: Unblock Files
Run PowerShell as Administrator and execute:
```powershell
Get-ChildItem "C:\TaskForce" -Recurse | Unblock-File
```

### Step 4: Install Python Dependencies
```bash
cd C:\TaskForce
pip install customtkinter
```

### Step 5: Configure Paths
Edit the configuration files as needed:
- `app_paths.json` - Configure application installation paths
- `domains.json` - Configure domain settings

## Usage

### GUI Interface
Run the Python application:
```bash
python TaskForce.py
```

Or use the compiled executable:
```
TaskForce UI.exe
```

### CLI Interface
Run the PowerShell script:
```powershell
.\TaskForce.ps1
```

## Configuration

### Application Paths
Edit `app_paths.json` to add or modify installation paths:
```json
{
    "paths": [
        {
            "name": "Common Apps",
            "path": "\\\\server\\share\\Apps",
            "description": "Common applications"
        }
    ]
}
```

### Domain Settings
Edit `domains.json` to configure domains:
```json
{
    "domains": [
        {
            "name": "yourdomain\\"
        }
    ]
}
```

**Important**: The default configuration files contain placeholder values. You must update them with your actual domain names and network paths before using the application.

### Hardcoded Paths
The following paths are currently hardcoded and should be customized for your environment:

**In `TaskForce.py`:**
- Line 482: `C:/TaskForce/{folder}` - Script folder paths
- Line 555: `C:\\TaskForce\\Excel` - Export directory

**In `TaskForce.ps1`:**
- Line 182: `C:\TaskForce\New Batch` - Script paths
- Line 194: `C:\TaskForce\Fresh Service` - Script paths
- Line 226: `\\192.168.15.6\it\1Apps\Common Apps` - Network share path

**Domain Configuration:**
- Line 409: `centrogs` - Default domain name

## Security Considerations

⚠️ **Important Security Notes:**

1. **Privilege Requirements**: This application requires administrator privileges and domain admin rights for many operations
2. **Network Paths**: Update hardcoded network paths (`\\192.168.15.6\`) to match your environment
3. **Input Validation**: User input is passed to PowerShell commands - ensure proper validation in production
4. **Credential Handling**: Credentials are handled via Windows credential manager but review for your security requirements
5. **Audit Trail**: Currently no logging mechanism - consider adding audit logging for compliance

## Known Issues

1. **Hardcoded Paths**: Several paths are hardcoded and need customization for different environments
2. **Error Handling**: Some operations lack comprehensive error handling
3. **Logging**: No built-in logging or audit trail functionality
4. **Dependencies**: Requires manual configuration of network shares and domain settings
5. **Cross-platform**: Windows-only due to PowerShell and Active Directory dependencies

## Troubleshooting

### "Cannot connect to computer"
- Verify network connectivity
- Check firewall settings (WinRM must be enabled)
- Ensure target computer is online
- Verify administrator privileges

### "Module not found" errors
- Install required Python packages: `pip install customtkinter`
- Ensure PowerShell modules are installed: `Import-Module ActiveDirectory`

### Script execution errors
- Run PowerShell as Administrator
- Check execution policy: `Set-ExecutionPolicy RemoteSigned`
- Unblock files: `Get-ChildItem | Unblock-File`

## Development

### Project Structure
```
TaskForce/
├── TaskForce.py              # Main GUI application
├── TaskForce.ps1             # CLI PowerShell script
├── domain_manager.py         # Domain configuration dialog
├── path_manager.py           # Path configuration dialog
├── app_paths.json            # Application paths configuration
├── domains.json              # Domain configuration
├── New Batch/                # User creation scripts
├── Fresh Service/            # Service desk scripts
├── Excel/                    # Export directory
└── TF.ico                    # Application icon
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Specify your license here (e.g., MIT, GPL, etc.)

## Acknowledgments

- Built with [customtkinter](https://github.com/TomSchimansky/CustomTkinter)
- PowerShell for Windows administration
- Active Directory integration

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [your email/contact]

## Changelog

### Version 1.0
- Initial release
- GUI and CLI interfaces
- Core system administration features
- User management capabilities
- Network tools integration

---

**Note**: This tool requires proper IT infrastructure and administrative privileges. Always test in a non-production environment first.
