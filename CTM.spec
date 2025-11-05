# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['MainController.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('GUI_modules', 'GUI_modules'), ('.env', '.env')],
    hiddenimports=['ssh2', 'ssh2.agent', 'ssh2.channel', 'ssh2.error_codes', 'ssh2.exceptions', 'ssh2.fileinfo', 'ssh2.knownhost', 'ssh2.listener', 'ssh2.pkey', 'ssh2.publickey', 'ssh2.session', 'ssh2.sftp', 'ssh2.sftp_handle', 'ssh2.statinfo', 'ssh2.utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CTM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logs\\logo.ico'],
)
