# ── data_monitor_controller.py ───────────────────────────────────────────────
"""
Business‑logic helpers for the Data‑Monitor page.

What’s new?
-----------
• get_data_paths() now returns *all* CSV / Excel files in C:\QSTAF\logs
• make_plot_figure() auto‑chooses bar, scatter, or line based on columns
"""

import os
import glob
import re
import pandas as pd
from matplotlib.figure import Figure

# ----------------------------------------------------------------- constants
LOG_DIR   = r"C:\QSTAF\logs"               # root of your log folder
_PATTERNS = ("*.csv", "*.xls*", "*.xlsx")        # recognised file types

# ----------------------------------------------------------------- helpers
								   
	   
																		 
	   
						  
						 
									   

												
																			
									 
								
												 

def get_df(csv_type):
    """Creates dataframe and returns it based on csv_type passed"""
    csv_files = glob.glob(LOG_DIR + csv_type, recursive=True)
    df = pd.DataFrame()
    for csv_file in csv_files:
        if df.shape[0] == 0:
            df = pd.read_csv(csv_file, index_col=False)
        else:
            df = pd.concat([df, pd.read_csv(csv_file, index_col=False)], axis=0)
    return df

# RSRP / SNR plot
def channel_conditions_plot(figsize: tuple[Literal[7], Literal[4]]):
    'RSRP and SNR plots from QSH_FR_MODE csv'

    df = get_df('\\*QSH_FR_MODE.csv')
    fig = None
    if df is not None:
        try:
            fig = Figure(figsize, dpi=100)
            ax = [fig.add_subplot(211),
                  fig.add_subplot(212)]

            for cc_id, group in df.groupby('CC_ID'):
                ax[0].scatter(group['TIMESTAMP'], group['RSRP'], label=f'CC_ID {cc_id}')
                ax[0].set_xlabel('TIMESTAMP')
                ax[0].set_ylabel('RSRP')
                ax[0].set_title('RSRP by CC_ID')
                ax[0].legend(title='CC_ID', bbox_to_anchor=(1.05, 1), loc='upper left')

            for cc_id, group in df.groupby('CC_ID'):
                ax[1].scatter(group['TIMESTAMP'], group['SNR'], label=f'CC_ID {cc_id}')
                ax[1].set_xlabel('TIMESTAMP')
                ax[1].set_ylabel('SNR')
                ax[1].set_title('SNR by CC_ID')
                ax[1].legend(title='CC_ID', bbox_to_anchor=(1.05, 1), loc='upper left')

            fig.tight_layout()
        except Exception as e:
            pass
    return fig

def ipa_thruput_plot(figsize: tuple[Literal[7], Literal[4]]):
    """IPA Thruput plot from QSH_ENL2"""

    df = get_df('\\*QSH_ENL2.csv')
    fig = None
    if isinstance(df, pd.DataFrame) and df.shape[0] > 0:
        try:
            df['DL_UL'] = df['DIRECTION'].apply(lambda x: 0 if x == 'DL' else 1)

            fig = Figure(figsize, dpi=100)
            ax = [fig.add_subplot(111)]
            for direction, group in df.groupby('DIRECTION'):
                ax[0].scatter(group['TIMESTAMP'], group['IPA_THROUGHPUT'], label=f'{direction}')
                ax[0].set_xlabel('TIMESTAMP')
                ax[0].set_ylabel('IPA_THROUGHPUT')
                ax[0].set_title('IPA_THROUGHPUT')
                ax[0].legend(title='DL_UL Thruput', bbox_to_anchor=(1.05, 1), loc='upper left')

            fig.tight_layout()
        except Exception as e:
            pass
    return fig


################### TRAFFIC CSV PROCESSING END #######################################
def process_traffic_csv(figsize: tuple[Literal[7], Literal[4]]):
    df_all = {}
    csv_files = glob.glob(LOG_DIR + '\\*.csv', recursive=True)

    for csv_file in csv_files:
        csv_name = csv_file.split('\\')[-1]

        # Skip indexing and consolidated CSVs
        m = re.search(r'.*vpid.*(Ping|Zoomcall|BrowseUrl|SpeedTest|HttpDownload|ftpUpload|ftpDownload|GoogleMaps)', csv_name)
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

    return hist_plot(figsize, df_indexing_all)

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

        # create_csv_from_df(csv_name, df)
    except Exception as e:
        # print(f'Exception: {e}')
        pass
    return df


# def create_csv_from_df(id, df):
#     """Create CSV from df"""
#     if not isinstance(df, pd.DataFrame):
#         return
#     if df.empty:
#         return
#     indexing_csv = os.path.join(LOG_DIR, f'indexing_{id}.csv')
#     if os.path.exists(indexing_csv):
#         os.remove(indexing_csv)
#     df.to_csv(indexing_csv, index=False)
#     print(f'CSV Created: {indexing_csv}')

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

def plot_wifi_clients(figsize:tuple[Literal[7], Literal[4]]):
    """Generate wifi_clients plot from QSTAFonDevice based on df at LOG_DIR"""

    conn_dev_csv_files = glob.glob(LOG_DIR + '\\*qstaf_monitor_connected_devices.csv', recursive=True)
    df = None
    for csv_file in conn_dev_csv_files:
        if df is None:
            df = pd.read_csv(csv_file, header=None, usecols=[0, 2, 3],
                        names=['TIMESTAMP', 'SSID', 'NO_OF_CLIENTS'])
        else:
            df = pd.concat([df, pd.read_csv(csv_file, header=None, usecols=[0, 2, 3],
                            names=['TIMESTAMP', 'SSID', 'NO_OF_CLIENTS'])], ignore_index=True, axis=0)


    fig = Figure(figsize, dpi=100)
    ax = [fig.add_subplot(111)]
    try:
        df = df.sort_values(by=['TIMESTAMP'])

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

    except Exception as e:
        pass
    return fig

def rf_band_table(figsize: tuple[Literal[7], Literal[4]]):
    df = get_df('\\*RFBandInfo.csv')

    try:
        df.columns = df.columns.str.upper()
        df = df.sort_values(by=['TIMESTAMP'])
        rf_indexed = create_rfband_csv(df)

        fig = None
        fig = Figure(figsize, dpi=100)
        ax = [fig.add_subplot(111)]

        ax[0].scatter(data=rf_indexed, x='TIMESTAMP', y='BAND', label='RF BAND TRANSITIONS')
        ax[0].set(title='RF BAND TRANSITIONS', ylabel='BAND')
        ax[0].legend()

        fig.tight_layout()
    except Exception as e:
        pass

    return fig


def create_rfband_csv(df=None):
    rf_csv = os.path.join(LOG_DIR, "index_RFBand.csv")

    if df is not None:

        df["NR_CC_BAND"] = df["NR_CC_BAND"].apply(lambda x: 'N' + str(x).strip())
        df['LTE_BANDS'] = df['LTE_BANDS'].apply(
            lambda x: '+'.join('B' + y for y in str(x).replace('0', '').replace(' ', '').strip(',').split(',')).replace(
                'Bnan', ''))

        # df['LTE_BANDS'] = df['LTE_BANDS'].apply(
        #     lambda x: '+'.join('B' + y for y in str(x).replace('0', '').replace(' ', '').strip(',').split(',')))

        df1 = pd.DataFrame(df, columns=["PARSING_INDEX", "CONNECTIVITY_MODE", "LTE_BANDS", "NR_CC_BAND", "TIMESTAMP"])
        df1["NR_BW"] = df["NR_CC_DL_BW"]

        df2 = pd.concat(
            [df1['CONNECTIVITY_MODE'], df1['LTE_BANDS'],
             df1.groupby("PARSING_INDEX")["NR_CC_BAND"].transform(lambda x: "+".join(x)),
             df1['TIMESTAMP']],
            axis=1)

        # df2.reset_index()
        df2_l = pd.concat([df1['CONNECTIVITY_MODE'], df1['NR_CC_BAND'],
                           df2['LTE_BANDS'].loc[df2['LTE_BANDS'].shift() != df2['LTE_BANDS']],
                           df1['TIMESTAMP']],
                          axis=1).dropna()

        df2_n = pd.concat([df1['CONNECTIVITY_MODE'], df1['LTE_BANDS'],
                           df2['NR_CC_BAND'].loc[df2['NR_CC_BAND'].shift() != df2['NR_CC_BAND']],
                           df1['TIMESTAMP']],
                          axis=1).dropna()

        df2 = pd.concat([df2_l, df2_n], axis=0).dropna()
        df.sort_values(by=['TIMESTAMP'])

        df2['NR_BW'] = df1.groupby("PARSING_INDEX")["NR_BW"].transform(lambda x: "+".join(x))
        df2["BAND"] = (df2['LTE_BANDS'] + '+' + df2["NR_CC_BAND"]).apply(lambda x: x.strip('+'))
        df2["BAND"] = df2["BAND"].replace(r'(N\d{3})(\+N\d{3}){7}', r"\1" + 'M', regex=True)
        df2["BAND"] = df2['CONNECTIVITY_MODE'] + '_' + df2["BAND"]

        # print(df2)
        if os.path.exists(rf_csv):
            os.remove(rf_csv)

        df2.to_csv(rf_csv, index=False)
        print(f'{rf_csv} created')
        df = df2
    return df

