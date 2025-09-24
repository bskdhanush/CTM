# ── DataMonitorController.py (Optimized for smooth refresh) ────
import glob
import re
import time
from typing import Literal, Optional
import pandas as pd
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

LOG_DIR = r"C:\QSTAF\CTM_logs"
ping_internet_status = 2
backhaul_internet_status = 2

# Cache for data to avoid redundant file reads
_data_cache = {}
_cache_timestamp = {}

def get_df(csv_type, use_cache=True):
    """Creates dataframe and returns it based on csv_type passed with optional caching"""
    
    current_time = time.time()
    cache_key = csv_type
    
    # Use cache if available and recent (within 30 seconds)
    if use_cache and cache_key in _data_cache:
        if current_time - _cache_timestamp.get(cache_key, 0) < 30:
            return _data_cache[cache_key]
    
    csv_files = glob.glob(LOG_DIR + csv_type, recursive=True)
    df = pd.DataFrame()

    try:
        if 'RFBandInfo' in csv_type:
            for csv_file in csv_files:
                if (df.empty) or (df.get('Parsing_Index', None) is None):
                    current_index = 0
                else:
                    current_index = int(df['Parsing_Index'].iloc[-1])

                df_current = pd.read_csv(csv_file, index_col=False)
                _flag = False
                if 'NR_CC_Band' in df_current:
                    df_current['NR_CC_Band'] = df_current['NR_CC_Band'].astype(int)
                    _flag = True
                if 'Parsing_Index' in df_current:
                    df_current['Parsing_Index'] = df_current['Parsing_Index'].apply(lambda x: str(int(x) + current_index))
                    _flag = True
                if _flag and df_current.shape[0] > 0:
                    df = pd.concat([df, df_current], axis=0)

        elif 'qstaf_monitor_connected_devices' in csv_type:
            df = None
            for csv_file in csv_files:
                if df is None:
                    df = pd.read_csv(csv_file, header=None, usecols=[0, 2, 3],
                                   names=['TIMESTAMP', 'SSID', 'NO_OF_CLIENTS'])
                else:
                    df = pd.concat([df, pd.read_csv(csv_file, header=None, usecols=[0, 2, 3],
                                                  names=['TIMESTAMP', 'SSID', 'NO_OF_CLIENTS'])], ignore_index=True,
                                 axis=0)

        elif 'qstaf_monitor' in csv_type:
            for csv_file in csv_files:
                df = pd.concat([df, pd.read_csv(csv_file, header=None,
                                              names=['TIMESTAMP', 'IPV4_DATACALL_STATUS', 'IPV6_DATACALL_STATUS',
                                                    'ETH_DATACALL_STATUS'])], ignore_index=True, axis=0)
        else:
            for csv_file in csv_files:
                if df.empty:
                    df = pd.read_csv(csv_file, index_col=False)
                else:
                    df = pd.concat([df, pd.read_csv(csv_file, index_col=False)], axis=0)

        if isinstance(df, pd.DataFrame) and not df.empty:
            df.columns = df.columns.str.upper()
            if 'TIMESTAMP' in df:
                df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP']).dt.strftime('%H:%M:%S')
            df = df.sort_values(by=['TIMESTAMP'])
            
            # Cache the result
            if use_cache:
                _data_cache[cache_key] = df
                _cache_timestamp[cache_key] = current_time
                
    except Exception as e:
        print(f"Error processing {csv_type}: {e}")
        df = pd.DataFrame()
    
    return df

#### TRAFFIC CSV PROCESSING START ####

def traffic_plots(figsize=(7, 4), fig=None):
    """ Traffic plots - Calls traffic_timeline_plot and hist_plot """
    global ping_internet_status
    df_all = {}
    csv_files = glob.glob(LOG_DIR + '\\*.csv', recursive=True)

    try:
        for csv_file in csv_files:
            csv_name = csv_file.split('\\')[-1]

            m = re.search(r'.*vpid.*(Ping|Zoomcall|BrowseUrl|SpeedTest|HttpDownload|ftpUpload|ftpDownload|GoogleMaps)', csv_name)
            # Skip index and consolidated CSVs, if any
            if not m or csv_name.startswith('index') or csv_name.startswith('consolidated'):
                continue

            m = re.search(r'.*(vpid.*).csv', csv_name)
            if m:
                id = m.group(1)
                if not isinstance(df_all.get(id), pd.DataFrame):
                    df_all[id] = pd.read_csv(csv_file, index_col=False)
                else:
                    df_all[id] = pd.concat([df_all[id], pd.read_csv(csv_file, index_col=False)], axis=0)

        df_indexing_all = pd.DataFrame()
        for id, df_csv in df_all.items():
            df_indexing = traffic_indexing(id, df_csv)
            df_indexing_all = pd.concat([df_indexing_all, df_indexing], axis=0)

        if 'vpid1_seqno1_Ping' in df_all:
            if len(df_all['vpid1_seqno1_Ping']) > 10:
                if df_all['vpid1_seqno1_Ping']['result'].iloc[-10:].eq('Fail').all():
                    ping_internet_status = 0
                else:
                    ping_internet_status = 1
        
        # Return two figures for traffic plots
        return [traffic_timeline_plot(df_all, figsize, fig), hist_plot(figsize, df_indexing_all, fig)]
    
    except Exception as e:
        print(f"Error in traffic_plots: {e}")
        return [None, None]

def traffic_timeline_plot(df_all, figsize=(7, 4), fig=None):
    """ Timeline plot for traffic scenarios """
    df = pd.DataFrame()
    for df_key, df_each in df_all.items():
        try:
            df_each['StartTime'] = pd.to_datetime(df_each['start_time'], format='%Y-%m-%d_%H_%M_%S')
            df_each['RESULT'] = df_each['result'].apply(lambda x: 10 if 'Pass' in x else 0)
            df = pd.concat([
                df,
                pd.DataFrame({'RESULT': df_each['RESULT'], 'TIME': df_each['StartTime'], 'command': df_key})
            ], axis=0)
            df = df.sort_values(by=['TIME'])
        except Exception as e:
            print(f'Exception: {e}')

    if df.empty:
        return fig

    # Reuse if given fig, else create a new one
    if fig is None:
        fig = Figure(figsize, dpi=100)

    # Clear old axes
    fig.clear()

    # Number of unique commands = number of subplots
    commands = df['COMMAND'].unique()
    num_commands = len(commands)

    if num_commands == 0:
        return fig

    for i, command in enumerate(commands, start=1):
        ax = fig.add_subplot(num_commands, 1, i)
        df_cmd = df[df['COMMAND'] == command]
        ax.step(df_cmd['TIME'], df_cmd['RESULT'], where='post')

        # Pretty title
        plot_command = re.sub(r'vpid\d+_', '', command)
        ax.set(title=plot_command)
        ax.set_yticks([0, 10])
        ax.set_yticklabels(['Fail', 'Pass'])
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    fig.suptitle("TRAFFIC TIMELINE", fontsize=16)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig

def traffic_indexing(csv_name, df_csv):
    """Reads Traffic CSV and Creates indexing CSV files"""
    df = pd.DataFrame(0, index=range(1), columns=['TOTAL', 'PASS', 'FAIL'])
    try:
        df['TOTAL'] = df_csv.shape[0]
        df['PASS'] = df_csv[df_csv['result'] == 'Pass'].shape[0]
        df['FAIL'] = df_csv[df_csv['result'] == 'Fail'].shape[0]

        if 'ZoomCall' in csv_name:
            partial_pass = 0
            try:
                partial_pass = df_csv[df_csv['error'].str.contains('Wait and Click Chat Button') == True].shape[0] + \
                              df_csv[df_csv['error'].str.contains('join audio') == True].shape[0] + \
                              df_csv[df_csv['error'].str.contains('Wait and Click un mute') == True].shape[0] + \
                              df_csv[df_csv['error'].str.contains(
                                  "'NoneType' object has no attribute 'get'") == True].shape[0]
            except Exception as e:
                pass
            df['PARTIAL_PASS'] = partial_pass
            df['FAIL'] = df['FAIL'] - partial_pass
            df['UNKNOWN'] = df['TOTAL'] - df['PASS'] - df['FAIL'] - df['PARTIAL_PASS']
            df['PASS%'] = round(100 * (df['PASS'] + df['PARTIAL_PASS']) / df['TOTAL'], 1)

        elif ('ftpDownload' in csv_name) or ('ftpUpload' in csv_name):
            partial_pass = 0
            try:
                if 'ftp_files_info_0_tput_Kbps' in df_csv:
                    partial_pass = df_csv[
                        (df_csv['result'] == 'Fail') & (df_csv['ftp_files_info_0_tput_Kbps'].notna()) & (
                            df_csv['ftp_files_info_0_tput_Kbps'] != 0)].shape[0]
            except Exception as e:
                pass
            df['PARTIAL_PASS'] = partial_pass
            df['FAIL'] = df['FAIL'] - partial_pass
            df['PASS%'] = round(100 * (df['PASS'] + df['PARTIAL_PASS']) / df['TOTAL'], 1)

        else:
            df['UNKNOWN'] = df['TOTAL'] - df['PASS'] - df['FAIL']
            df['PASS%'] = round(100 * df['PASS'] / df['TOTAL'], 1)

        df['COMMAND'] = csv_name.strip('.csv')

    except Exception as e:
        print(f'Exception: {e}')
    return df

def hist_plot(figsize=(7, 4), df_indexing_all=None, fig=None):
    """Generates Histogram plots based on df_all (based on Indexing.csv)"""
    if fig is None:
        fig = Figure(figsize, dpi=100)
    
    fig.clear()
    ax = fig.add_subplot(111)

    try:
        if isinstance(df_indexing_all, pd.DataFrame) and df_indexing_all.shape[0] > 0:
            x_indices = range(len(df_indexing_all['COMMAND']))

            ax.bar(x_indices, df_indexing_all['TOTAL'], width=0.4, label='Total', color='#330C73', align='center')
            ax.bar(x_indices, df_indexing_all['PASS'], width=0.4, label='Pass', color='#EB89B5', align='edge')

            ax.set_xticks(x_indices)
            ax.set_xticklabels(df_indexing_all['COMMAND'], rotation=45, ha="right")

            ax.set_xlabel('COMMAND')
            ax.set_ylabel('TRAFFIC')
            ax.set_title('TOTAL and PASS per TC')
            ax.legend()
            fig.tight_layout()
    except Exception as e:
        print(f"Error in hist_plot: {e}")

    return fig

#### TRAFFIC CSV PROCESSING END ####

#### RF BAND PLOT START ####
def rf_band_plot(figsize=(7, 4), fig=None):
    """ RF Band transitions plot """
    df = get_df('\\*RFBandInfo.csv')
    
    if fig is None:
        fig = Figure(figsize, dpi=100)
    
    fig.clear()
    ax = fig.add_subplot(111)

    try:
        if df is not None and not df.empty:
            df_rf_indexed = get_rfband_df(df)
            if df_rf_indexed is not None and not df_rf_indexed.empty:
                df_rf_indexed = df_rf_indexed.sort_values(by=['TIMESTAMP'])
                ax.scatter(df_rf_indexed['TIMESTAMP'], df_rf_indexed['BAND'])
                ax.set(title='RF BAND TRANSITIONS', ylabel='BAND')
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
                fig.autofmt_xdate()
                fig.tight_layout()
    except Exception as e:
        print(f'Exception during rf_band_plot: {e}')
    
    return fig

def get_rfband_df(df=None):
    """Creates RFBand dataframe """
    if df is not None and not df.empty:
        try:
            df["NR_CC_BAND"] = df["NR_CC_BAND"].apply(lambda x: 'N' + str(x).strip())
            df['LTE_BANDS'] = df['LTE_BANDS'].apply(
                lambda x: '+'.join('B' + y for y in str(x).replace('0', '').replace(' ', '').strip(',').split(',')).replace(
                    'Bnan', ''))

            df1 = pd.DataFrame(df, columns=["PARSING_INDEX", "CONNECTIVITY_MODE", "LTE_BANDS", "NR_CC_BAND", "TIMESTAMP"])
            df1["NR_BW"] = df["NR_CC_DL_BW"]

            df2 = pd.concat(
                [df1['CONNECTIVITY_MODE'], df1['LTE_BANDS'],
                 df1.groupby("PARSING_INDEX")["NR_CC_BAND"].transform(lambda x: "+".join(x)),
                 df1.groupby("PARSING_INDEX")["NR_BW"].transform(lambda x: "+".join(x)),
                 df1['TIMESTAMP']],
                axis=1)

            df2_l = pd.concat([df1['CONNECTIVITY_MODE'], df1['NR_CC_BAND'],
                              df2['LTE_BANDS'].where(df2['LTE_BANDS'].shift() != df2['LTE_BANDS']),
                              df1['TIMESTAMP']],
                             axis=1).dropna()

            df2_n = pd.concat([df1['CONNECTIVITY_MODE'], df1['LTE_BANDS'],
                              df2['NR_CC_BAND'].where(df2['NR_CC_BAND'].shift() != df2['NR_CC_BAND']), df1['TIMESTAMP']],
                             axis=1).dropna()

            df2 = pd.concat([df2_l, df2_n], axis=0).dropna()
            df2.sort_values(by=['TIMESTAMP'])
            df2['ORIG_TIMESTAMP'] = df2['TIMESTAMP']
            df2['TIMESTAMP'] = pd.to_datetime(df2['TIMESTAMP'], format='%H:%M:%S').dt.strftime('%H:%M:%S')

            df2["BAND"] = (df2['LTE_BANDS'] + '+' + df2["NR_CC_BAND"]).apply(lambda x: x.strip('+'))
            df2["BAND"] = df2["BAND"].replace(r'(N\d{3})(\+N\d{3}){7}', r"\1" + 'M', regex=True)
            df2["BAND"] = df2['CONNECTIVITY_MODE'] + '_' + df2["BAND"]

            return df2
        except Exception as e:
            print(f"Error processing RF band data: {e}")
    
    return df

#### RF BAND PLOT END ####

def ipa_thruput_plot(figsize=(7, 4), fig=None):
    """IPA Thruput plot from QSH_ENL2"""
    df = get_df('\\*QSH_ENL2.csv')
    
    if fig is None:
        fig = Figure(figsize, dpi=100)
    
    fig.clear()
    ax = fig.add_subplot(111)
    
    try:
        if isinstance(df, pd.DataFrame) and df.shape[0] > 0:
            df['DL_UL'] = df['DIRECTION'].apply(lambda x: 0 if x == 'DL' else 1)
            df['IPA_THROUGHPUT'] = df['IPA_THROUGHPUT'] / 1000
            df = df.sort_values(by=['TIMESTAMP'])

            for direction, group in df.groupby('DIRECTION'):
                ax.scatter(group['TIMESTAMP'], group['IPA_THROUGHPUT'], label=f'{direction} (Mbps)')
            
            ax.set_title('IPA_THROUGHPUT')
            ax.legend(title='DL_UL Thruput', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            fig.autofmt_xdate()
            fig.tight_layout()
    except Exception as e:
        print(f"Error in ipa_thruput_plot: {e}")
        
    return fig

def wifi_clients_plot(figsize=(7, 4), fig=None):
    """Generate wifi_clients plot from QSTAFonDevice based on df at LOG_DIR"""
    df = get_df('\\*qstaf_monitor_connected_devices.csv')
    
    if fig is None:
        fig = Figure(figsize, dpi=100)
    
    fig.clear()
    ax = fig.add_subplot(111)
    
    try:
        if df is not None and not df.empty:
            df = df[df['SSID'].str.contains('SLO|MLO|Ethernet', na=False)]
            df = df.sort_values(by=['TIMESTAMP'])

            # Group the data by the 'SSID' column
            for label, group in df.groupby('SSID'):
                ax.plot(
                    group['TIMESTAMP'],
                    group['NO_OF_CLIENTS'],
                    label=label,
                    marker='o',
                    linestyle='-'
                )

            # Set title and labels
            ax.set_title('WifiClients')
            ax.set_xlabel('TIMESTAMP')
            ax.set_ylabel('NO_OF_CLIENTS')
            ax.legend(title='SSID')
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            fig.autofmt_xdate()
            fig.tight_layout()

    except Exception as e:
        print(f"Error in wifi_clients_plot: {e}")
        
    return fig

def data_call_state_plot(figsize=(7, 4), fig=None):
    global backhaul_internet_status
    df = get_df('\\*qstaf_monitor.csv')
    
    if fig is None:
        fig = Figure(figsize, dpi=100)
    
    fig.clear()
    ax = fig.add_subplot(111)
    
    try:
        if isinstance(df, pd.DataFrame) and df.shape[0] > 0:
            df['IPV4_DATACALL_STATUS'] = df['IPV4_DATACALL_STATUS'].str.replace(r'ipv4_datacall_status:\s*', '', regex=True)
            df.rename(columns={'IPV4_DATACALL_STATUS': 'BACKHAUL_STATE'}, inplace=True)

            ax.scatter(df['TIMESTAMP'], df['BACKHAUL_STATE'])
            ax.set_title('BACKHAUL_STATE')
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            fig.autofmt_xdate()
            fig.tight_layout()
            
            if len(df) > 10:
                if df['BACKHAUL_STATE'].iloc[-10:].eq('FALSE').all():
                    backhaul_internet_status = 0  # RED
                else:
                    backhaul_internet_status = 1  # GREEN
    except Exception as e:
        print(f"Error in data_call_state_plot: {e}")
        
    return fig

def channel_conditions_plot(figsize=(7, 4), fig=None):
    """ RSRP and SNR plots from QSH_FR_MODE csv """
    df = get_df('\\*QSH_FR_MODE.csv')
    
    if fig is None:
        fig = Figure(figsize, dpi=100)
    
    fig.clear()
    
    try:
        if df is not None and not df.empty:
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)

            rsrp_median = df['RSRP'].median()
            snr_median = df['SNR'].median()
            df['RSRP'] = df['RSRP'].where(df['RSRP'].between(-140, 0), rsrp_median)
            df['SNR'] = df['SNR'].where(df['SNR'].between(-25, 50), snr_median)

            for cc_id, group in df.groupby('CC_ID'):
                ax1.scatter(group['TIMESTAMP'], group['RSRP'], label=f'CC_ID {cc_id}')
            ax1.set_xlabel('TIMESTAMP')
            ax1.set_ylabel('RSRP')
            ax1.set_title('RSRP by CC_ID')
            ax1.legend(title='CC_ID', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

            for cc_id, group in df.groupby('CC_ID'):
                ax2.scatter(group['TIMESTAMP'], group['SNR'], label=f'CC_ID {cc_id}')
            ax2.set_xlabel('TIMESTAMP')
            ax2.set_ylabel('SNR')
            ax2.set_title('SNR by CC_ID')
            ax2.legend(title='CC_ID', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")

            fig.autofmt_xdate()
            fig.tight_layout()
    except Exception as e:
        print(f"Error in channel_conditions_plot: {e}")
        
    return fig

def get_internet_status():
    """
    internet_status
    'RED' : 0,
    'GREEN' : 1
    """
    global ping_internet_status, backhaul_internet_status
    if backhaul_internet_status == 0 or ping_internet_status == 0:
        return 0
    elif ping_internet_status == 1 or backhaul_internet_status == 1:
        return 1
    else:
        return 2

def clear_cache():
    """Clear the data cache to force fresh data loading"""
    global _data_cache, _cache_timestamp
    _data_cache.clear()
    _cache_timestamp.clear()