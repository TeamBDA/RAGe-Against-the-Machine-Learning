# For BASH cmd line run this setup script:
If this fails because you changed files and you only want to refresh the current folder, run:
# Create and activate your virtual environment:

#### 2. Workspace setup

1. Install Git if it is not already installed from [here](https://git-scm.com/install/). For Mac: `brew install git`. For Windows: download and install it.
2. Install [Visual Studio Code](https://code.visualstudio.com/) (or another editor you prefer). I will use VS Code in this module. After installing Git, restart VS Code if it was already open.
3. Open a terminal.
4. Clone the class repository:

```bash
git clone https://github.com/warestack/bda
```

> [!TIP]
>
> If the repository already exists, run `git pull` instead of cloning again.

5. Open the project folder in VS Code.
6. Open a terminal inside VS Code.
7. You will need to navigate to folders using the `cd` command.

#### 3. Check Python installation

Check that Python is installed:

```bash
python3 --version
```

Depending on your Python installation on Windows, one of the above commands may work while others may not.

This part is a recap of the basics. We will reuse these steps in future sessions.

#### 4. Basics you should know

- `Python`: the programming language, not the snake 🐍.

- `Terminal`: a text-based tool where you run commands like `python3 --version` or `pip install`.
- `cd`: changes directory (moves you into another folder).
- `pwd`: prints your current folder path.
- `Virtual environment (.venv)`: keeps each project’s Python packages separate, so different projects don’t conflict. Different projects often need different package versions; isolation avoids conflicts.
- `pip`: Python’s package manager; it installs libraries like `huggingface_hub` or `datasets`.
- `requirements.txt`: a list of required Python packages for the project. It lets everyone install the same dependencies and reproduce the same setup.
- `README.md`: a simple project file where you document what you built, what worked, and what is pending (useful for tracking progress). Not sure about Markdown syntax? [Check here](https://www.markdownguide.org/basic-syntax/).
- `solutions/`: the folder you need to create to store your answers for each tutorial part (no need to submit now, but you can share it with Stelios later, for example for homework).
- `session_solutions/`: reference solutions provided by Stelios. Use them only to review your work after you attempt the tasks.
- Naming convention for exercise files in `solutions/`: use `exercise-<session>-<part>.py` (for example, `exercise-01-02.py`). Helper library modules can use underscores (for example, `exercise_01_02_lib.py`).

You will need to navigate folders in the terminal using `cd`.

Quick examples (macOS/Linux):

```bash
pwd
cd session1
pwd
cd ..
```

Quick examples (Windows PowerShell):

```powershell
Get-Location
cd session1
Get-Location
cd ..
```

#### 5. Create and manage a virtual environment

You will need a virtual environment to install the required packages.

> [!TIP]
>
> Make sure you are in the correct folder before creating it. You can create one environment per session (recommended) or use one environment for the entire `bda` project.
>
> Navigate to the folder using `cd session1`.

Create a virtual environment:

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On windows:

```bash
py -m venv .venv
source .venv/bin/activate
```
> On Windows (VS Code terminal):
>
> - PowerShell: `.venv\Scripts\Activate.ps1` (may be blocked by execution policy on some machines)
> - Optional temporary PowerShell bypass (current session only):
>   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
>   Then run: `.venv\Scripts\Activate.ps1`
> - If activation is blocked, run scripts directly with: `.venv\Scripts\python.exe your_script.py`

Deactivate it when needed:

```bash
deactivate
``
# Install Python module requirements:

```bash
 pip install --upgrade pip
 pip install -r requirements.txt
```

> [!TIP]
>
> A **`requirements.txt`** file lists all Python packages a project needs. It helps everyone recreate the same environment. Pin exact versions when reproducibility is critical.

#### 6. Install dependencies

Activate `.venv` again and install dependencies:

```bash
pip install -r requirements.txt
```

If `pip` is missing, run:

```bash
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
```

Check the output to ensure everything installed successfully. You can ignore most warnings for the moment.
You are now ready to proceed. You can use the `clear` command to clear the terminal. Try it out.