
def get_current_rfband_rsrp():
    rfband = None
    rsrp = None

    try:
        rfband, rsrp = copy_and_process_latest_rf_csv()
    except Exception as e:
        print(f'Exception during copy_and_process_latest_csv : {e}')

    return rfband, rsrp

def copy_and_process_latest_rf_csv():
    # to be implemented
    pass
	