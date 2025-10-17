import os
from pathlib import Path

CTM_CONFIG_DIR = r'C:\ProgramData\Qualcomm\CTM\config'
CTM_LOGS_DIR = r'C:\ProgramData\Qualcomm\CTM\logs'
ADB_ID_JSON_DIR = r"C:\QSTAF\CTM_logs\adb_ID.json"

DEFAULT_CRASHDUMP = Path(r"C:\Temp\automation\QSTAF\QSTAFpy\crashdumps")
CRASHDUMP_ROOT_PCAT  = Path(r"C:\ProgramData\Qualcomm\PCAT\AddOns\CrashCollection\MemoryDumps")
RDKBCRASH_ROOT     = Path(r"C:\Temp\automation\QSTAF\QSTAFpy\appcrash_logs")

CTM_BASE_DIR = r'C:\CTM'
CTM_META_DIR = os.path.join(CTM_BASE_DIR, 'Meta')
CTM_MPSS_DIR = os.path.join(CTM_BASE_DIR, 'MPSS')
CTM_DAPP_DIR = os.path.join(CTM_BASE_DIR, 'DAPP')

APP_CONFIG_JSON = os.path.join(CTM_CONFIG_DIR, 'app_config.json')
PROV_CONFIG_JSON = os.path.join(CTM_CONFIG_DIR, 'prov_config.json')


MIN_CRASH_SIZE     = 1.5 * 1024**3   # 1.5 GiB
MIN_RDKBCRASH_SIZE = 2   * 1024**2   # 2 MB


def init_dirs():
    for _dir in [CTM_CONFIG_DIR, CTM_LOGS_DIR, CTM_META_DIR, CTM_MPSS_DIR, CTM_DAPP_DIR]:
        os.makedirs(_dir, exist_ok=True)
