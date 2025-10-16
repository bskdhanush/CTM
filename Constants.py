import os

CTM_CONFIG_DIR = r'C:\ProgramData\Qualcomm\CTM\config'
CTM_LOGS_DIR = r'C:\ProgramData\Qualcomm\CTM\logs'

CTM_BASE_DIR = r'C:\CTM'
CTM_META_DIR = os.path.join(CTM_BASE_DIR, 'Meta')
CTM_MPSS_DIR = os.path.join(CTM_BASE_DIR, 'MPSS')
CTM_DAPP_DIR = os.path.join(CTM_BASE_DIR, 'DAPP')

APP_CONFIG_JSON = os.path.join(CTM_CONFIG_DIR, 'app_config.json')
PROV_CONFIG_JSON = os.path.join(CTM_CONFIG_DIR, 'prov_config.json')

def init_dirs():
    for _dir in [CTM_CONFIG_DIR, CTM_LOGS_DIR, CTM_META_DIR, CTM_MPSS_DIR, CTM_DAPP_DIR]:
        os.makedirs(_dir, exist_ok=True)
