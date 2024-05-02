import streamlit as st
import pandas as pd
from typing import Literal
from data.vibration_data import RionFile

PROCESSING = False
HELP_MEAN_CHECKER = """
    The mean of the vibration data in "AP" column is calculated for each axis.
    The standard deviation of this is calculated for each axis too."""

HELP_FREQ_CHECKER = """
This option is not available yet."""

st.set_page_config(page_title="Vibration Analysis", page_icon="🏗️")
st.markdown("# Vibration Analysis")
sidebar = st.sidebar.header("Vibration Analysis")

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

uploaded_files = sidebar.file_uploader(
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
def get_values_checkbox(type:Literal['mean', 'freq'], 
                      key:int, 
                      value:bool=False, 
                      disabled:bool=False,
                      help:str=''):
    if type == 'mean':
        return st.checkbox('Get Mean Values',
                    value=value,
                    on_change=get_mean_values_callback,
                    key=key,
                    disabled=disabled,
                    help=help)
    if type == 'freq':
        return st.checkbox('Get Freq Values',
                    value=value,
                    on_change=get_freq_values_callback,
                    key=key,
                    disabled=disabled,
                    help=help)
    
with options:
    check_options = (st.session_state.get_mean_values or st.session_state.get_freq_values) 
    #Verificar si no hay seleccionada una opcion, o 
    if (not (st.session_state.get_mean_values or st.session_state.get_freq_values) 
        or not uploaded_files):
        get_mean_values = get_values_checkbox('mean', 
                                              key=1,
                                              help=HELP_MEAN_CHECKER)
        get_freq_values = get_values_checkbox('freq', 
                                              key=2,
                                              disabled=True)
        calculate = options.button('Go Calculate!', disabled=True)
    elif not st.session_state.calculate_button_clicked:
        get_mean_values = get_values_checkbox('mean', 
                                              key=3, 
                                              value=st.session_state.get_mean_values,
                                              help=HELP_MEAN_CHECKER)
        get_freq_values = get_values_checkbox('freq', 
                                              key=4, 
                                              value=st.session_state.get_freq_values,
                                              disabled=True)
        calculate = options.button('Go Calculate!', 
                                   disabled=False, 
                                   on_click=process_data)
    else:
        get_mean_values = get_values_checkbox('mean', 
                                              key=3, 
                                              value=st.session_state.get_mean_values, 
                                              disabled=True)
        get_freq_values = get_values_checkbox('freq', 
                                              key=4, 
                                              value=st.session_state.get_freq_values, 
                                              disabled=True)
        calculate = options.button('Go Calculate!', disabled=True)

get_mean_values = st.session_state.get_mean_values
get_freq_values = st.session_state.get_freq_values
calculate = st.session_state.calculate_button_clicked

if get_mean_values and calculate:
    mean_df = pd.DataFrame(columns=['X_AP', 'Y_AP', 'Z_AP'])
    std_df = pd.DataFrame(columns=['X_STD', 'Y_STD', 'Z_STD'])
    ppv_df = pd.DataFrame(columns=['Start Time', 'X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']) 
    folder_name = None
    for file in uploaded_files:
        file_name = file.name.split('_')
        if not folder_name:
            folder_name = file_name[0].split('/')[0]
        if 'Inst' in file_name:
            rion_file = RionFile(file)
            name = file_name[6]
            ppv = rion_file.summary
            ppv_df.loc[name] = ppv

    if len(ppv_df) !=0:
        with st.expander(f'Data calculated from {folder_name} folder', expanded=True):
            st.dataframe(ppv_df.rename(columns={'Start Time':'Measurement Time'}
                                       ).rename_axis(
                                           'Receivers'
                                           ), use_container_width=True)
