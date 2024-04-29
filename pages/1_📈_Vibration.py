import streamlit as st
import pandas as pd
from typing import Literal

PROCESSING = False

st.set_page_config(page_title="Vibration Analysis", page_icon="📈")
st.markdown("# Vibration Analysis")
sidebar = st.sidebar.header("Vibration Analysis")

@st.cache_data
def get_mean_axis(file):
    data = pd.read_csv(file, skiprows=1)
    #Filter Only the AP data
    ap = data.filter(items=['Start Time', 'X_AP', 'Y_AP', 'Z_AP'])
    #Parse time series
    ap['Start Time'] = pd.to_datetime(ap['Start Time'])
    ap.set_index('Start Time', inplace=True)
    return ap[['X_AP', 'Y_AP', 'Z_AP']].mean().rename_axis('Receivers')

@st.cache_data
def get_sd_axis(file):
    data = pd.read_csv(file, skiprows=1)
    #Filter Only the AP data
    ap = data.filter(items=['Start Time', 'X_AP', 'Y_AP', 'Z_AP'])
    #Parse time series
    ap['Start Time'] = pd.to_datetime(ap['Start Time'])
    ap.set_index('Start Time', inplace=True)
    return ap[['X_AP', 'Y_AP', 'Z_AP']].rename(columns={'X_AP':'X_STD',
                                                        'Y_AP':'Y_STD',
                                                        'Z_AP':'Z_STD'}).std(
                                                        ).rename_axis('Receivers')

def parse_receivers_name(name:str) -> str:
    return f'R{name[-2:]}'


with st.expander('Example of folder'):
    st.write('You can drag and drop a folder with all data from RION vibrometer like this')
    code = '''
        Vibrations/
        │
        ├── Auto_0055/
        │   ├── Auto_Calc/
        │       └── VM_001_OCT_Calc_0055_0001.rnd
        │   ├── Auto_Inst/
        │       └── VM_001_OCT_Inst_0055_0001.rnd
        │   └── Auto_0055.rnh
        .
        .
        .
        ├── Auto_0070/
        │   ├── Auto_Calc/
        │       └── VM_001_OCT_Calc_0070_0001.rnd
        │   ├── Auto_Inst/
        │       └── VM_001_OCT_Inst_0070_0001.rnd
        │   └── Auto_0070.rnh

    '''
    st.code(code, language='python')

uploaded_files = st.file_uploader(
    "Choose a CSV file or drag and drop a folder with all data.", 
    accept_multiple_files=True)

#Options to process files
st.markdown('### Select the process you want to upload')
options = st.container(border=True)

if 'calculate_button_clicked' not in st.session_state:
    st.session_state.calculate_button_clicked = False
if 'get_mean_values' not in st.session_state:
    st.session_state.get_mean_values = False
if 'get_freq_values' not in st.session_state:
    st.session_state.get_freq_values = False

def process_data():
    st.session_state.calculate_button_clicked = not st.session_state.calculate_button_clicked
def get_mean_values_callback():
    st.session_state.get_mean_values = not st.session_state.get_mean_values
def get_freq_values_callback():
    st.session_state.get_freq_values = not st.session_state.get_freq_values
def get_values_button(type:Literal['mean', 'freq'], 
                      key:int, 
                      value:bool=False, 
                      disabled:bool=False):
    if type == 'mean':
        return st.checkbox('Get Mean Values',
                    value=value,
                    on_change=get_mean_values_callback,
                    key=key,
                    disabled=disabled)
    if type == 'freq':
        return st.checkbox('Get Freq Values',
                    value=value,
                    on_change=get_freq_values_callback,
                    key=key,
                    disabled=disabled)
    
with options:
    check_options = (st.session_state.get_mean_values or st.session_state.get_freq_values) 
    #Verificar si no hay seleccionada una opcion, o 
    if (not (st.session_state.get_mean_values or st.session_state.get_freq_values) 
        or not uploaded_files):
        get_mean_values = get_values_button('mean', key=1)
        get_freq_values = get_values_button('freq', key=2)
        calculate = options.button('Go Calculate!', disabled=True)
    elif not st.session_state.calculate_button_clicked:
        get_mean_values = get_values_button('mean', key=3, value=st.session_state.get_mean_values)
        get_freq_values = get_values_button('freq', key=4, value=st.session_state.get_freq_values)
        calculate = options.button('Go Calculate!', disabled=False, on_click=process_data)
    else:
        get_mean_values = get_values_button('mean', key=3, value=st.session_state.get_mean_values, disabled=True)
        get_freq_values = get_values_button('freq', key=4, value=st.session_state.get_freq_values, disabled=True)
        calculate = options.button('Go Calculate!', disabled=True)

get_mean_values = st.session_state.get_mean_values
get_freq_values = st.session_state.get_freq_values
calculate = st.session_state.calculate_button_clicked

if get_mean_values and calculate:
    mean_df = pd.DataFrame(columns=['X_AP', 'Y_AP', 'Z_AP'])
    std_df = pd.DataFrame(columns=['X_STD', 'Y_STD', 'Z_STD'])
    folder_name = None
    for file in uploaded_files:
        file_name = file.name.split('_')
        if not folder_name:
            folder_name = file_name[0].split('/')[0]
        if 'Inst' in file_name:
            original_name = file_name[6]
            name = parse_receivers_name(original_name)
            mean_data = get_mean_axis(file)
            file.seek(0)
            std_data = get_sd_axis(file)
            mean_df.loc[name] = mean_data.values
            std_df.loc[name] = std_data

    if len(mean_df) !=0:
        with st.expander(f'Data calculated from {folder_name} folder', expanded=True):
            st.dataframe(
                pd.concat(
                    [mean_df, std_df],axis=1
                    ).rename_axis(
                        'Receivers'
                        ), use_container_width=True)
