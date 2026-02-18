# DRIVING-EXAM-STADISTIC

PyQt6 desktop app to import, store, filter, and analyze Spain DGT driving exam results (autoescuelas).

Data source: https://www.dgt.es/menusecundario/dgt-en-cifras/matraba-listados/conductores-autoescuelas.html

## Setup
1) Create a virtualenv and install dependencies:
   - `python -m venv .venv`
   - `.venv\\Scripts\\activate`
   - `pip install -r requirements.txt`

2) Run the application:
   - `python -m driving_exams`

## Data import
Download the monthly export from DGT (semicolon-separated TXT/CSV) and import it from the app menu:
- `File -> Import CSV...`

The database tracks already imported periods (`year`, `month`) and prevents importing the same period twice.

The SQLite database is created on first run at `driving_exams/data/driving_exams.db`.

## Windows executable (PyInstaller)
Steps used to generate the Windows executable with PyInstaller:

1) Install PyInstaller in the virtualenv:
   - `pip install pyinstaller`

2) Build from the `driving_exams` folder using the project spec file:
   - `cd driving_exams`
   - `pyinstaller --clean --noconfirm main.spec`

3) Output executable:
   - `driving_exams/dist/main.exe`
   - Final renamed file used in this project: `driving_exams/dist/DGT Stadistic Exams.exe`

Icon used for the executable:
- `driving_exams/dgt.ico`
