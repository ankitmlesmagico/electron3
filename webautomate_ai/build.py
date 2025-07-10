import os
import shutil
import subprocess
from pathlib import Path

def install_playwright_browsers():
    """Install Playwright browsers in a custom location."""
    # Set custom browser installation path
    custom_browser_path = Path(__file__).parent / "playwright-browsers"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(custom_browser_path)
    
    # Install browsers
    subprocess.run(["playwright", "install"], check=True)
    subprocess.run(["playwright", "install-deps"], check=True)
    
    return custom_browser_path

def build_executable():
    """Build the PyInstaller executable with proper configuration."""
    # Install browsers first
    browser_path = install_playwright_browsers()
    
    # Create the PyInstaller spec file
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['agent.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('modules', 'modules'),
        ('utils', 'utils'),
        (str(browser_path), 'playwright-browsers'),
    ],
    hiddenimports=[
        'browser_use',
        'playwright',
        'google.generativeai',
        'httpx',
        'dotenv',
    ],
    hookspy=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WebAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    # Write the spec file
    with open("agent.spec", "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller
    subprocess.run(["pyinstaller", "agent.spec", "--clean"], check=True)
    

if __name__ == "__main__":
    build_executable()
