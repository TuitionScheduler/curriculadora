# Curriculator Scrapper

(Instructions given with VSCode as the IDE and poetry version 2.1.1)

## Poetry Installation:

1. Check if poetry is already installed in your computer by running
"poetry --version"
2. If no version shows up, install poetry with:
    - curl -sSL https://install.python-poetry.org | python3 -
3. If "poetry --version" still doesnt show anything you may need
to add it to PATH
4. To do so, you will need to add this line to your shell config file
    ### For Windows: ???

    ### For Mac:
    1. Check which shell your computer is using by running:
        - echo $SHELL
    2. You'll either have a "zshrc" or "bash..." shell
    3. Make sure you have VSCode Command-Line Tools by:
        - Cmd + Shift + P
        - Select: "Shell Command: Install ‘code’ command in PATH"
    4. If you you're using zsh run:
        - touch ~/.zshrc
        - ls -a ~ | grep .zshrc
        - code ~/.zshrc
        - Paste this line: export PATH="$HOME/.local/bin:$PATH"
    5. If you you're using bash run:
        - touch ~/.bashrc
        - ls -a ~ | grep .bashrc
        - code ~/.bashrc
5. Poetry should now be installed. Run "poetry --version" to check


## Requirement Installation

1. Open terminal in project directory
2. Run the following commands to set up your enviroment
    - poetry env activate
    - poetry env info  
3. Copy the "Executable" path
4. Cmd + Shift + P
5. Select "Python: Select Interpreter"
6. Select "Enter interpreter path..."
7. Paste the copied path
8. Now that you are on the correct enviroment run
    - poetry install --no-root
9. You should now have all the needed dependencies
and be on the correct enviroment


## How to Run Scrape to SQL:

NOTE: You can change command parameters between Fall, Spring, FirstSummer or SecondSummer. Keep in mind 1 academic year doesnt run as a calendar year. If you wish to collect the data from the semester from January-May of 2025, you wont type spring 2025 in the parameters, you'll type spring 2024 because that's the spring semester of the 24-25 academic year.

### For Windows:

1. Open terminal and stay within the root directory.
2. Make sure to have the correct virtual environment; refer to the previous section "Requirement Installation" to do so,
3. Run the following command:
    - .\sql_run.bat

### For Mac:
1. Open terminal inside the curriculadora folder in which "sql_ru.sh" is:
2. Make sure to have the correct virtual environment; refer to the previous section "Requirement Installation" to do so.
3. Run the following command:
    - export PYTHONPATH=$(pwd)
    - bash sql_run.sh