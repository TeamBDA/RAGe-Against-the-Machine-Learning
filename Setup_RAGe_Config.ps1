#### Before running this config script install Powershell 7.0+ (pwsh) or install automatically in your chosen IDE via plugins
#### Alternatively just use the BASH script
#### Run in terminal here

#### Prerequisites

#### In Visual Studio Code/PyCharm or other IDE terminal, update your local repository. Activate virtual env first

$findos = Read-Host "Are you using windows or a mac? (enter w or m)..."models

Write-Host "Activating the virtual environment..." -ForegroundColor w

try
{
    Write-host "Older version of python is currently installed... " -ForegroundColor Yellow

    $oldpy      = python --version
    $getinstall = pip --version

    Write-host "Older version of python is installed {$oldpy} and pip version {$getinstall}... " -ForegroundColor Green
}

catch
{
    Write-host "Older version of python not installed...checking more recent install... " -ForegroundColor Yellow

    $newpy      = python3 --version
    $getinstall = pip3 --version

    Write-host "Newer version of python is installed {$newpy} and pip version {$getinstall}... " -ForegroundColor Green
}

if($findos -eq "m" -or $findos -eq "M")
{
    if ($oldpy)
    {
        python -m venv .venv
        . .venv/bin/activate.ps1
    }

    else
    {
        python3 -m venv .venv
        . .venv/bin/activate.ps1
    }
        Write-Host "Activated the virtual environment on MAC..." -ForegroundColor Green
}

elseif($findos -eq "w"  -or $findos -eq "W"){
    if($oldpy)
    {
        python -m venv .venv
        . venv/Scripts/Activate.ps1
        source .venv/bin/activate
        Write-Host "Activated the virtual environment on Windows or Linux..." -ForegroundColor Green
    }

    else
    {
        python3 -m venv .venv
        . venv/Scripts/Activate.ps1
        source .venv/bin/activate
        Write-Host "Activated the virtual environment on Windows or Linux..." -ForegroundColor Green
    }
}

else{
        Write-Host "You are using an unsupported OS...please run on Linux, windows or a mac..." -f r
}

Write-Host "checking git version on the environment..." -ForegroundColor y

$gitinstall = git --version

if($gitinstall){
    try
    {
        Write-Host "Git version is $( $gitinstall ) " -ForegroundColor green
    }

    catch{
        Write-Host "Git is not install or provision it first..." -f r
        break
    }
}

Write-Host "Make a GIT pull request of the following team branch: 'Test', opening Git repository..." -ForegroundColor y

if ($findos -eq "m" -or $findos -eq "M")
{
    Write-Host "Opening GitHub repo on chrome on macOS..." -ForegroundColor y
    open -a "Safari" "https://github.com/TeamBDA/RAGe-Against-the-Machine-Learning"
    Write-Host "Opened GitHub repo on chrome on MAC..." -ForegroundColor Green
}

elseif ($findos -eq "w" -or $findos -eq "W") {
    Write-Host "Opening GitHub repo..." -ForegroundColor y
    Start-Process "chrome.exe" "https://github.com/TeamBDA/RAGe-Against-the-Machine-Learning"
    Write-Host "Opened GitHub repo..." -ForegroundColor Green

    Write-Host "Opening GitHub cheat sheet with basic GIT cmds..." -ForegroundColor y
    Start-Process "chrome.exe" "https://education.github.com/git-cheat-sheet-education.pdf"
    Write-Host "Opened GitHubcheat sheet with basic git cmds..." -ForegroundColor Green
}

Write-Host "Installing requirements for python..." -ForegroundColor Yellow

$installprereqs = Read-Host "Do you want to install the required modules for this project? Enter y or n "

if($installprereqs -eq "y" -or $installprereqs -eq "Y")
{
    Write-Host "Checking the PIP is upgraded for python then installing requirements..." -ForegroundColor Yellow
    python3 -m ensurepip --upgrade
    pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "Checked the PIP is upgraded for python then installed requirements..." -ForegroundColor Green
    Write-Host "Completed setup and config for your environment...*****END***" -ForegroundColor Green
    continue
}

else{
    Write-Host "Requirements already installed on your environment *****END****..." -ForegroundColor Green
    continue
}