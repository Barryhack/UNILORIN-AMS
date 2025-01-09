# Download Python 3.11
$pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
$installerPath = "$env:TEMP\python-3.11.7-amd64.exe"

Write-Host "Downloading Python 3.11.7..."
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath

# Install Python 3.11
Write-Host "Installing Python 3.11.7..."
Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait

# Create and activate virtual environment
Write-Host "Creating virtual environment..."
& "C:\Program Files\Python311\python.exe" -m venv venv311
& .\venv311\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing requirements..."
pip install -r requirements.txt

# Initialize database
Write-Host "Initializing database..."
python init_db.py

Write-Host "Setup complete!"
