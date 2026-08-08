# Import Active Directory module
Import-Module ActiveDirectory

function Show-Menu {
    Clear-Host
    $border = "══════════════════════════════════════════════════════════════════"
    $menuItems = @(
        "1. System Information",
        "2. User Information",
        "3. Group Policy",
        "4. Bulk User Management",
        "5. App Installation",
        "6. App Uninstallation",
        "7. Password Management",
        "8. Update & Restart",
        "9. Rename PC",
        "10. Network Tools",
        "x. Exit"
    )

    Write-Host $border -ForegroundColor Magenta
    Write-Host "                   TaskForce                  " -ForegroundColor Cyan
    Write-Host $border -ForegroundColor Magenta

    foreach ($item in $menuItems) {
        Write-Host ("||  " + $item.PadRight(60) + " ||") -ForegroundColor Yellow
    }

    Write-Host $border -ForegroundColor Magenta
    Write-Host "`r`n" -NoNewline
}

# Function to get system information
function Get-SystemInformation {
    param(
        [string]$computerName
    )
    
    Write-Host "╔═══[ Get System Information ]══════════════════════╗" -ForegroundColor Magenta
    
    if (-not $computerName) {
        $computerName = Read-Host "Enter PC name to retrieve system information"
    }
    
    if ($computerName -eq "x") { return }
    
    try {
        # Test connection first
        if (-not (Test-Connection -ComputerName $computerName -Count 1 -Quiet)) {
            Write-Host "Cannot connect to $computerName" -ForegroundColor Red
            return
        }

        # Get system info
        $systemInfo = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $computerName
        $osInfo = Get-WmiObject -Class Win32_OperatingSystem -ComputerName $computerName
        $processorInfo = Get-WmiObject -Class Win32_Processor -ComputerName $computerName
        $diskInfo = Get-WmiObject -Class Win32_LogicalDisk -ComputerName $computerName -Filter "DriveType=3"
        $memoryInfo = Get-WmiObject -Class Win32_PhysicalMemory -ComputerName $computerName

        # Display information
        Write-Host "`nSystem Information for $computerName" -ForegroundColor Cyan
        Write-Host "----------------------------------------"
        Write-Host "Computer Name: $($systemInfo.Name)"
        Write-Host "Manufacturer: $($systemInfo.Manufacturer)"
        Write-Host "Model: $($systemInfo.Model)"
        Write-Host "OS: $($osInfo.Caption)"
        Write-Host "OS Version: $($osInfo.Version)"
        Write-Host "Processor: $($processorInfo.Name)"
        Write-Host "Total Physical Memory: $([math]::Round($systemInfo.TotalPhysicalMemory/1GB, 2)) GB"
        
        Write-Host "`nDisk Information:" -ForegroundColor Cyan
        foreach ($disk in $diskInfo) {
            $freeSpaceGB = [math]::Round($disk.FreeSpace/1GB, 2)
            $totalSpaceGB = [math]::Round($disk.Size/1GB, 2)
            Write-Host "Drive $($disk.DeviceID): $freeSpaceGB GB free of $totalSpaceGB GB"
        }
    }
    catch {
        Write-Host "Error retrieving system information: $_" -ForegroundColor Red
    }
}

# Function to get user information
function Get-UserInformation {
    param(
        [string]$searchTerm
    )
    
    Write-Host "╔═══[ User Information Lookup ]═════════════════════╗" -ForegroundColor Magenta
    
    if (-not $searchTerm) {
        $searchTerm = Read-Host "Enter name, employee ID, or office number"
    }
    
    if ($searchTerm -eq "x") { return }
    
    try {
        # Search for user based on different criteria
        $user = Get-ADUser -Filter {
            (Name -like "*$searchTerm*") -or
            (SamAccountName -like "*$searchTerm*") -or
            (EmployeeID -like "*$searchTerm*") -or
            (Office -like "*$searchTerm*")
        } -Properties *
        
        if ($user) {
            Write-Host "`nUser Information:" -ForegroundColor Cyan
            Write-Host "----------------------------------------"
            Write-Host "Name: $($user.Name)"
            Write-Host "Username: $($user.SamAccountName)"
            Write-Host "Email: $($user.EmailAddress)"
            Write-Host "Office: $($user.Office)"
            Write-Host "Department: $($user.Department)"
            Write-Host "Title: $($user.Title)"
            Write-Host "Account Status: $(if($user.Enabled){'Enabled'}else{'Disabled'})"
            Write-Host "Last Logon: $($user.LastLogonDate)"
        }
        else {
            Write-Host "No user found matching '$searchTerm'" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Error retrieving user information: $_" -ForegroundColor Red
    }
}

# Function to show group policies
function Show-GroupPolicies {
    param(
        [string]$target
    )
    
    Write-Host "╔═══[ Group Policy Information ]═══════════════════╗" -ForegroundColor Magenta
    
    if (-not $target) {
        $target = Read-Host "Enter computer name or user name"
    }
    
    if ($target -eq "x") { return }
    
    try {
        if ($target -match '\s') {
            # It's a user name
            $user = Get-ADUser -Filter "Name -like '*$target*'" -Properties *
            if ($user) {
                Write-Host "`nGroup Policy Results for user: $($user.Name)" -ForegroundColor Cyan
                gpresult /USER $user.SamAccountName /V
            }
            else {
                Write-Host "User not found: $target" -ForegroundColor Yellow
            }
        }
        else {
            # It's a computer name
            if (Test-Connection -ComputerName $target -Count 1 -Quiet) {
                Write-Host "`nGroup Policy Results for computer: $target" -ForegroundColor Cyan
                gpresult /COMPUTER $target /V
            }
            else {
                Write-Host "Cannot connect to computer: $target" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "Error retrieving group policies: $_" -ForegroundColor Red
    }
}

# Function for bulk user management
function Manage-BulkUsers {
    Write-Host "╔═══[ Bulk User Management ]════════════════════════╗" -ForegroundColor Magenta
    Write-Host "1. New Batch"
    Write-Host "x. Back to main menu"
    
    $choice = Read-Host "Select an option"
    
    switch ($choice) {
        "1" {
            $scriptPath = "C:\TaskForce\New Batch"
            $scripts = Get-ChildItem -Path $scriptPath -Filter "*.ps1"
            Write-Host "`nAvailable scripts:"
            for ($i = 0; $i -lt $scripts.Count; $i++) {
                Write-Host "$($i+1). $($scripts[$i].Name)"
            }
            $scriptChoice = Read-Host "Select script number"
            if ($scriptChoice -match '^\d+$' -and [int]$scriptChoice -le $scripts.Count) {
                & $scripts[$scriptChoice-1].FullName
            }
        }
    }
}

# Function to install applications
function Install-Application {
    param(
        [string]$computerName,
        [string]$appPath
    )
    
    Write-Host "╔═══[ Application Installation ]═══════════════════╗" -ForegroundColor Magenta
    
    if (-not $computerName) {
        $computerName = Read-Host "Enter target PC name"
    }
    
    if (-not $appPath) {
        $appPath = "\\192.168.15.6\it\1Apps\Common Apps"
        $files = Get-ChildItem -Path $appPath -Filter "*.exe"
        Write-Host "`nAvailable applications:"
        for ($i = 0; $i -lt $files.Count; $i++) {
            Write-Host "$($i+1). $($files[$i].Name)"
        }
        $appChoice = Read-Host "Select application number"
        if ($appChoice -match '^\d+$' -and [int]$appChoice -le $files.Count) {
            $appPath = $files[$appChoice-1].FullName
        }
    }
    
    try {
        if (Test-Connection -ComputerName $computerName -Count 1 -Quiet) {
            Write-Host "Installing $appPath on $computerName..."
            $result = Invoke-Command -ComputerName $computerName -ScriptBlock {
                param($app)
                Start-Process -FilePath $app -Wait
            } -ArgumentList $appPath
            Write-Host "Installation completed successfully" -ForegroundColor Green
        }
        else {
            Write-Host "Cannot connect to $computerName" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Error during installation: $_" -ForegroundColor Red
    }
}

# Function to uninstall applications
function Uninstall-Application {
    param(
        [string]$computerName
    )
    
    Write-Host "╔═══[ Application Uninstallation ]═════════════════╗" -ForegroundColor Magenta
    
    if (-not $computerName) {
        $computerName = Read-Host "Enter target PC name"
    }
    
    try {
        if (Test-Connection -ComputerName $computerName -Count 1 -Quiet) {
            $apps = Get-WmiObject -Class Win32_Product -ComputerName $computerName | 
                   Select-Object Name, Version, IdentifyingNumber
            
            Write-Host "`nInstalled applications:"
            for ($i = 0; $i -lt $apps.Count; $i++) {
                Write-Host "$($i+1). $($apps[$i].Name) - $($apps[$i].Version)"
            }
            
            $choice = Read-Host "Select application number to uninstall"
            if ($choice -match '^\d+$' -and [int]$choice -le $apps.Count) {
                $app = $apps[$choice-1]
                Write-Host "Uninstalling $($app.Name)..."
                $result = Invoke-Command -ComputerName $computerName -ScriptBlock {
                    param($appId)
                    Start-Process -FilePath "msiexec.exe" -ArgumentList "/x $appId /qn" -Wait
                } -ArgumentList $app.IdentifyingNumber
                Write-Host "Uninstallation completed successfully" -ForegroundColor Green
            }
        }
        else {
            Write-Host "Cannot connect to $computerName" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Error during uninstallation: $_" -ForegroundColor Red
    }
}

# Function to manage passwords
function Manage-Password {
    param(
        [string]$username,
        [string]$newPassword,
        [bool]$unlockAccount = $true,
        [bool]$changeAtNextLogin = $false
    )
    
    Write-Host "╔═══[ Password Management ]══════════════════════════╗" -ForegroundColor Magenta
    
    if (-not $username) {
        $username = Read-Host "Enter username or Hits ID"
    }
    
    try {
        $user = Get-ADUser -Filter {(SamAccountName -eq $username) -or (EmployeeID -eq $username)} -Properties *
        
        if ($user) {
            if (-not $newPassword) {
                $newPassword = Read-Host "Enter new password" -AsSecureString
            }
            
            Set-ADAccountPassword -Identity $user -NewPassword (ConvertTo-SecureString -String $newPassword -AsPlainText -Force)
            
            if ($unlockAccount) {
                Unlock-ADAccount -Identity $user
                Write-Host "Account unlocked" -ForegroundColor Green
            }
            
            if ($changeAtNextLogin) {
                Set-ADUser -Identity $user -ChangePasswordAtLogon $true
                Write-Host "User will be required to change password at next login" -ForegroundColor Green
            }
            
            Write-Host "Password changed successfully" -ForegroundColor Green
        }
        else {
            Write-Host "User not found" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Error managing password: $_" -ForegroundColor Red
    }
}

# Function to update and restart computers
function Update-AndRestart {
    param(
        [string]$computerName
    )
    
    Write-Host "╔═══[ Update and Restart ]════════════════════════════╗" -ForegroundColor Magenta
    
    if (-not $computerName) {
        $computerName = Read-Host "Enter computer name (supports wildcards)"
    }
    
    try {
        if ($computerName -match "[*?]") {
            $computers = Get-ADComputer -Filter "Name -like '$computerName'" | Select-Object -ExpandProperty Name
        }
        else {
            $computers = @($computerName)
        }
        
        foreach ($computer in $computers) {
            if (Test-Connection -ComputerName $computer -Count 1 -Quiet) {
                Write-Host "Processing $computer..."
                Invoke-Command -ComputerName $computer -ScriptBlock {
                    Write-Host "Running Windows Update..."
                    $updateSession = New-Object -ComObject Microsoft.Update.Session
                    $updateSearcher = $updateSession.CreateUpdateSearcher()
                    $searchResult = $updateSearcher.Search("IsInstalled=0")
                    
                    if ($searchResult.Updates.Count -gt 0) {
                        Write-Host "Installing updates..."
                        $updatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
                        $searchResult.Updates | ForEach-Object { $updatesToInstall.Add($_) }
                        
                        $installer = $updateSession.CreateUpdateInstaller()
                        $installer.Updates = $updatesToInstall
                        $installationResult = $installer.Install()
                        
                        Write-Host "Update installation completed with result code: $($installationResult.ResultCode)"
                    }
                    else {
                        Write-Host "No updates found"
                    }
                    
                    Write-Host "Restarting computer..."
                    Restart-Computer -Force
                }
            }
            else {
                Write-Host "Cannot connect to $computer" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Error updating/restarting: $_" -ForegroundColor Red
    }
}

# Function to rename computers
function Rename-PC {
    param(
        [string]$currentName,
        [string]$newName,
        [string]$username,
        [string]$password,
        [string]$domain = "centrogs"
    )
    
    Write-Host "╔═══[ Rename PC ]════════════════════════════════════╗" -ForegroundColor Magenta
    
    if (-not $currentName) {
        $currentName = Read-Host "Enter current PC name"
    }
    if (-not $newName) {
        $newName = Read-Host "Enter new PC name"
    }
    if (-not $username) {
        $username = Read-Host "Enter username with permissions"
    }
    if (-not $password) {
        $password = Read-Host "Enter password" -AsSecureString
    }
    
    try {
        if (Test-Connection -ComputerName $currentName -Count 1 -Quiet) {
            $credential = New-Object System.Management.Automation.PSCredential("$domain\$username", $password)
            
            Rename-Computer -ComputerName $currentName -NewName $newName -DomainCredential $credential -Force -Restart
            Write-Host "Computer renamed successfully. Restarting..." -ForegroundColor Green
        }
        else {
            Write-Host "Cannot connect to $currentName" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Error renaming computer: $_" -ForegroundColor Red
    }
}

# Function for network tools
function Use-NetworkTools {
    param(
        [string]$computerName,
        [string]$destination,
        [ValidateSet('ping', 'traceroute', 'gpupdate', 'netstat', 'flushdns')]
        [string]$operation
    )
    
    Write-Host "╔═══[ Network Tools ]══════════════════════════════════╗" -ForegroundColor Magenta
    
    if (-not $computerName) {
        $computerName = Read-Host "Enter target PC name"
    }
    
    try {
        if (Test-Connection -ComputerName $computerName -Count 1 -Quiet) {
            switch ($operation) {
                'ping' {
                    if (-not $destination) {
                        $destination = Read-Host "Enter destination to ping"
                    }
                    Invoke-Command -ComputerName $computerName -ScriptBlock {
                        param($dest)
                        Test-Connection -ComputerName $dest -Count 4
                    } -ArgumentList $destination
                }
                'traceroute' {
                    if (-not $destination) {
                        $destination = Read-Host "Enter destination for traceroute"
                    }
                    Invoke-Command -ComputerName $computerName -ScriptBlock {
                        param($dest)
                        tracert $dest
                    } -ArgumentList $destination
                }
                'gpupdate' {
                    Invoke-Command -ComputerName $computerName -ScriptBlock {
                        gpupdate /force
                    }
                }
                'netstat' {
                    Invoke-Command -ComputerName $computerName -ScriptBlock {
                        netstat -ano
                    }
                }
                'flushdns' {
                    Invoke-Command -ComputerName $computerName -ScriptBlock {
                        ipconfig /flushdns
                    }
                }
            }
        }
        else {
            Write-Host "Cannot connect to $computerName" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Error executing network operation: $_" -ForegroundColor Red
    }
}

# Main menu loop
do {
    Show-Menu
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "1" { Get-SystemInformation }
        "2" { Get-UserInformation }
        "3" { Show-GroupPolicies }
        "4" { Manage-BulkUsers }
        "5" { Install-Application }
        "6" { Uninstall-Application }
        "7" { Manage-Password }
        "8" { Update-AndRestart }
        "9" { Rename-PC }
        "10" { 
            Write-Host "1. Ping"
            Write-Host "2. Traceroute"
            Write-Host "3. GPUpdate"
            Write-Host "4. Netstat"
            Write-Host "5. Flush DNS"
            $netChoice = Read-Host "Select network operation"
            switch ($netChoice) {
                "1" { Use-NetworkTools -operation "ping" }
                "2" { Use-NetworkTools -operation "traceroute" }
                "3" { Use-NetworkTools -operation "gpupdate" }
                "4" { Use-NetworkTools -operation "netstat" }
                "5" { Use-NetworkTools -operation "flushdns" }
            }
        }
        "x" { break }
        default { Write-Host "Invalid choice" -ForegroundColor Red }
    }
    
    if ($choice -ne "x") {
        Write-Host "`nPress Enter to continue..."
        Read-Host
    }
} while ($choice -ne "x")
