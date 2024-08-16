from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, MERGE
from pathlib import Path


spec_hooks = []
hidden_imports = []


app_name = "CSV Visualizer"
main_script = "src/main.py"
icon_file = "UI_componentes\icon.ico"


data_files = [
    ("logs", "logs"),
    ("src", "src"),
    ("UI_componentes", "UI_componentes"),
    ("C:\\Python\\Lib\\site-packages\\customtkinter", "customtkinter"),
    ("example data", "example data")
]


a = Analysis(
    [main_script],
    pathex=[str(Path(SPEC).parent.resolve())],
    binaries=[],
    datas=data_files,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    hiddenimports=hidden_imports,
    cipher=None,
    noarchive=False
)
print("Data files are:", data_files)


pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="output_folder",
)
