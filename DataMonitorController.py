# ── DataMonitorController.py ───────────────────────────────────────────────
import glob
import re
from typing import Literal
import pandas as pd
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from Constants import CTM_LOGS_DIR

ping_internet_status = 2
backhaul_internet_status = 2

def get_df(csv_type):
    """Creates dataframe and returns it based on csv_type passed"""
    csv_files = glob.glob(CTM_LOGS_DIR + csv_type, recursive=True)
    df = pd.DataFrame()

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
    return df

################### TRAFFIC CSV PROCESSING START #######################################

def traffic_plots(figsize: tuple[Literal[7], Literal[4]]):
    """ Traffic plots - Calls traffic_timeline_plot and hist_plot """

    global ping_internet_status
    df_all = {}
    csv_files = glob.glob(CTM_LOGS_DIR + '\\*.csv', recursive=True)

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
                
    return [traffic_timeline_plot(df_all), hist_plot(figsize, df_indexing_all)]

def traffic_timeline_plot(df_all):
    """ Timeline plot for traffic scenarios """

    df = pd.DataFrame()
    for df_key, df_each in df_all.items():
        try:
            df_each['StartTime'] = pd.to_datetime(df_each['start_time'], format='%Y-%m-%d_%H_%M_%S')
            df_each['RESULT'] = df_each['result'].apply(lambda x: 10 if 'Pass' in x else 0)
            df = pd.concat([df, pd.DataFrame({'RESULT': df_each['RESULT'], 'TIME': df_each['StartTime'], 'command': df_key})],
                           axis=0)
            df = df.sort_values(by=['TIME'])
                       
        except Exception as e:
            print(f'Exception: {e}')

    fig = None
    try:
        if df is not None and not df.empty:
            df.columns = df.columns.str.upper()
            num_commands = df['COMMAND'].nunique()
            commands = df['COMMAND'].unique()
            fig = Figure((7, num_commands), dpi=100)
            ax = []
            for i in range(1, num_commands+1):
                ax.append(fig.add_subplot(int(f'{num_commands}1{i}')))

            for i in range(len(commands)):
                df_cmd = df[df['COMMAND'] == commands[i]]
                ax[i].step(df_cmd['TIME'], df_cmd['RESULT'], where='post', label=df_cmd)
                plot_command = commands[i]
                m = re.search(r'vpid\d+_(.*)', commands[i])
                if m:
                    plot_command = m.group(1)
                ax[i].set(title=plot_command)
                ax[i].set_yticks([0, 10])
                ax[i].set_yticklabels(['Fail', 'Pass'])
                ax[i].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))

            fig.suptitle("TRAFFIC TIMELINE", fontsize=16)
            fig.autofmt_xdate()
            fig.tight_layout()

    except Exception as e:
        print('Exception during traffic_timeline_plot')

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

def hist_plot(figsize: tuple[Literal[7], Literal[4]], df_indexing_all=None):
    """Generates Histogram plots based on df_all (based on Indexing.csv)"""

    fig = Figure(figsize, dpi=100)
    ax = [fig.add_subplot(111)]

    if isinstance(df_indexing_all, pd.DataFrame) and df_indexing_all.shape[0] > 0:

        x_indices = range(len(df_indexing_all['COMMAND']))

        ax[0].bar(x_indices, df_indexing_all['TOTAL'], width=0.4, label='Total', color='#330C73', align='center')
        ax[0].bar(x_indices, df_indexing_all['PASS'], width=0.4, label='Pass', color='#EB89B5', align='edge')

        ax[0].set_xticks(x_indices)
        ax[0].set_xticklabels(df_indexing_all['COMMAND'], rotation=45)

        ax[0].set_xlabel('COMMAND')
        ax[0].set_ylabel('TRAFFIC')
        ax[0].set_title('TOTAL and PASS per TC')
        ax[0].legend()
        fig.tight_layout()

    return fig

################### TRAFFIC CSV PROCESSING END #######################################


############################ RF BAND PLOT START ######################################
def rf_band_plot(figsize: tuple[Literal[7], Literal[4]]):
    """ RF Band transitions plot """
    df = get_df('\\*RFBandInfo.csv')
    fig = None

    try:
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.columns = [str(column).upper() for column in df.columns]
            df_rf_indexed = get_rfband_df(df)
            if df_rf_indexed is not None:
                df_rf_indexed = df_rf_indexed.sort_values(by=['TIMESTAMP'])
            else:
                return None
        else:
            return None

        fig = Figure(figsize, dpi=100)
        ax = [fig.add_subplot(111)]

        ax[0].scatter(data=df_rf_indexed, x='TIMESTAMP', y='BAND')
        ax[0].set(title='RF BAND TRANSITIONS', ylabel='BAND')
        ax[0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        fig.autofmt_xdate()
        fig.tight_layout()

    except Exception as e:
        print(f'Exception during rf_band_plot : {e}')

    return fig

def get_rfband_df(df=None):
    """Creates RFBand dataframe """

    if isinstance(df, pd.DataFrame) and not df.empty:
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
    return df

############################ RF BAND PLOT END #####################################


def ipa_thruput_plot(figsize: tuple[Literal[7], Literal[4]]):
    """IPA Thruput plot from QSH_ENL2"""

    df = get_df('\\*QSH_ENL2.csv')
    fig = None
    if isinstance(df, pd.DataFrame) and df.shape[0] > 0:
        try:
            df['DL_UL'] = df['DIRECTION'].apply(lambda x: 0 if x == 'DL' else 1)
            df['IPA_THROUGHPUT'] = df['IPA_THROUGHPUT'] / 1000
            df = df.sort_values(by=['TIMESTAMP'])

            fig = Figure(figsize, dpi=100)
            ax = [fig.add_subplot(111)]
            for direction, group in df.groupby('DIRECTION'):
                ax[0].scatter(group['TIMESTAMP'], group['IPA_THROUGHPUT'], label=f'{direction} (Mbps)')
                # ax[0].set_xlabel('TIMESTAMP')
                # ax[0].set_ylabel('IPA_THROUGHPUT')
                ax[0].set_title('IPA_THROUGHPUT')
                ax[0].legend(title='DL_UL Thruput', bbox_to_anchor=(1.05, 1), loc='upper left')
                ax[0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            fig.autofmt_xdate()
            fig.tight_layout()
        except Exception as e:
            print(f'Exception during ipa_thruput_plot: {e}')
    return fig

def speedtest_plot(figsize:tuple[Literal[7], Literal[4]]):
    """Generate Speedtest plot from QSTAFonDevice based on df at CTM_LOGS_DIR"""
    df = get_df('\\*vpid1111_seqno1_SpeedTest.csv')
    fig = Figure(figsize, dpi=100)
    ax = [fig.add_subplot(111)]
    if not isinstance(df, pd.DataFrame) or df.empty:
        return fig
    try:
        df = df.sort_values(by=['end_time'])

        # Group the data by the 'color' column
        for label, group in df.groupby('SSID'):
            ax[0].plot(
                group['TIMESTAMP'],
                group['NO_OF_CLIENTS'],
                label=label,
                marker='o',
                linestyle='-'
            )

        # Set title and labels
        ax[0].set_title('WifiClients')
        ax[0].set_xlabel('TIMESTAMP')
        ax[0].set_ylabel('NO_OF_CLIENTS')
        ax[0].legend(title='SSID')
        ax[0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        fig.autofmt_xdate()

    except Exception as e:
        print(f'Exception during speedtest_plot: {e}')
    return fig

def wifi_clients_plot(figsize:tuple[Literal[7], Literal[4]]):
    """Generate wifi_clients plot from QSTAFonDevice based on df at CTM_LOGS_DIR"""

    df = get_df('\\*qstaf_monitor_connected_devices.csv')
    fig = Figure(figsize, dpi=100)
    ax = [fig.add_subplot(111)]
    try:
        df = df[df['SSID'].str.contains('SLO|MLO|Ethernet', na=False)] # type: ignore
        df = df.sort_values(by=['TIMESTAMP']) # type: ignore

        # Group the data by the 'color' column
        for label, group in df.groupby('SSID'):
            ax[0].plot(
                group['TIMESTAMP'],
                group['NO_OF_CLIENTS'],
                label=label,
                marker='o',
                linestyle='-'
            )

        # Set title and labels
        ax[0].set_title('WifiClients')
        ax[0].set_xlabel('TIMESTAMP')
        ax[0].set_ylabel('NO_OF_CLIENTS')
        handles, labels = ax[0].get_legend_handles_labels()
        if labels:
            ax[0].legend(title='SSID')
        ax[0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        fig.autofmt_xdate()

    except Exception as e:
        print(f'Exception during wifi_clients_plot: {e}')
    return fig

def data_call_state_plot(figsize:tuple[Literal[7], Literal[4]]):
    global backhaul_internet_status
    df = get_df('\\*qstaf_monitor.csv')
    fig = None
    if isinstance(df, pd.DataFrame) and df.shape[0] > 0:
        try:
            df['IPV4_DATACALL_STATUS'] = df['IPV4_DATACALL_STATUS'].str.replace(r'ipv4_datacall_status:\s*', '', regex=True)
            df.rename(columns={'IPV4_DATACALL_STATUS': 'BACKHAUL_STATE'}, inplace=True)

            fig = Figure(figsize, dpi=100)
            ax = [fig.add_subplot(111)]

            ax[0].scatter(df['TIMESTAMP'], df['BACKHAUL_STATE'])
            ax[0].set_title('BACKHAUL_STATE')
            ax[0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            fig.autofmt_xdate()
            fig.tight_layout()
            if len(df) > 10:
                if df['BACKHAUL_STATE'].iloc[-10:].eq('FALSE').all():
                    backhaul_internet_status = 0 #RED
                else:
                    backhaul_internet_status = 1 #GREEN
        except Exception as e:
            pass
    return fig


def channel_conditions_plot(figsize: tuple[Literal[7], Literal[4]]):
    """ RSRP and SNR plots from QSH_FR_MODE csv """

    df = get_df('\\*QSH_FR_MODE.csv')
    fig = None
    if df is not None:
        try:
            fig = Figure(figsize, dpi=100)
            ax = [fig.add_subplot(211),
                  fig.add_subplot(212)]

            rsrp_median = df['RSRP'].median()
            snr_median = df['SNR'].median()
            df['RSRP'] = df['RSRP'].where(df['RSRP'].between(-140, 0), rsrp_median)
            df['SNR'] = df['RSRP'].where(df['RSRP'].between(-25, 50), snr_median)

            for cc_id, group in df.groupby('CC_ID'):
                ax[0].scatter(group['TIMESTAMP'], group['RSRP'], label=f'CC_ID {cc_id}')
                ax[0].set_xlabel('TIMESTAMP')
                ax[0].set_ylabel('RSRP')
                ax[0].set_title('RSRP by CC_ID')
                ax[0].legend(title='CC_ID', bbox_to_anchor=(1.05, 1), loc='upper left')
                ax[0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))

            for cc_id, group in df.groupby('CC_ID'):
                ax[1].scatter(group['TIMESTAMP'], group['SNR'], label=f'CC_ID {cc_id}')
                ax[1].set_xlabel('TIMESTAMP')
                ax[1].set_ylabel('SNR')
                ax[1].set_title('SNR by CC_ID')
                ax[1].legend(title='CC_ID', bbox_to_anchor=(1.05, 1), loc='upper left')
                ax[1].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))

            fig.autofmt_xdate()
            fig.tight_layout()
        except Exception as e:
            print(f'Exception during channel_conditions_plot: {e}')
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
 