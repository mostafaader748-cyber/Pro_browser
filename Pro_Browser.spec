# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png', '.'), ('youtube pro_browser background theme.png', '.'), ('users.json', '.')]
binaries = []
hiddenimports = ['PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'hashlib', 'json', 'random', 'os', 'sys', 'socket', 'threading', 'time', 'platform', 'shutil', 'tempfile', 'subprocess', 'datetime', 'QApplication', 'QMainWindow', 'QWidget', 'QTabWidget', 'QVBoxLayout', 'QHBoxLayout', 'QPushButton', 'QLineEdit', 'QDialog', 'QLabel', 'QComboBox', 'QTableWidget', 'QTableWidgetItem', 'QHeaderView', 'QSlider', 'QFrame', 'QGridLayout', 'QMessageBox', 'QToolBar', 'QMenu', 'QInputDialog', 'QFileDialog', 'QScrollArea', 'QCheckBox', 'QTextEdit', 'QSize', 'QUrl', 'Qt', 'QTimer', 'QSettings', 'QEvent', 'pyqtSignal', 'QPoint', 'QMimeData', 'QDrag', 'QPainter', 'QColor', 'QPen', 'QAction', 'QKeySequence', 'QPixmap', 'QIcon', 'QFont', 'QWebEngineView']
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['Pro_Browser.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Pro_Browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png'],
)
