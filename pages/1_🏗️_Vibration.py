import streamlit as st
from pandas import DataFrame
from typing import Literal, Dict
from re import search
from data.vibration_data import RionFile
from plotly.express import box, histogram, line

PROCESSING = False
HELP_PPV_CHECKER = """
    The ppv value of vibration data in "AP" column is calculated for each axis.
    PPV get the maximum value of data for each axis."""

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
if 'get_ppv_values' not in st.session_state:
    st.session_state.get_ppv_values = False
if 'get_freq_values' not in st.session_state:
    st.session_state.get_freq_values = False

def process_data():
    st.session_state.calculate_button_clicked = not st.session_state.calculate_button_clicked
def get_ppv_values_callback():
    st.session_state.get_ppv_values = not st.session_state.get_ppv_values
def get_freq_values_callback():
    st.session_state.get_freq_values = not st.session_state.get_freq_values
def get_values_checkbox(type:Literal['ppv', 'freq'], 
                      key:int, 
                      value:bool=False, 
                      disabled:bool=False,
                      help:str=''):
    if type == 'ppv':
        return st.checkbox('Get PPV Values',
                    value=value,
                    on_change=get_ppv_values_callback,
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
    check_options = (st.session_state.get_ppv_values or st.session_state.get_freq_values) 
    #Verificar si no hay seleccionada una opcion, o 
    if (not (st.session_state.get_ppv_values or st.session_state.get_freq_values) 
        or not uploaded_files):
        get_ppv_values = get_values_checkbox('ppv', 
                                              key=1,
                                              help=HELP_PPV_CHECKER)
        get_freq_values = get_values_checkbox('freq', 
                                              key=2,
                                              disabled=True)
        calculate = options.button('Go Calculate!', disabled=True)
    elif not st.session_state.calculate_button_clicked:
        get_ppv_values = get_values_checkbox('ppv', 
                                              key=3, 
                                              value=st.session_state.get_ppv_values,
                                              help=HELP_PPV_CHECKER)
        get_freq_values = get_values_checkbox('freq', 
                                              key=4, 
                                              value=st.session_state.get_freq_values,
                                              disabled=True)
        calculate = options.button('Go Calculate!', 
                                   disabled=False, 
                                   on_click=process_data)
    else:
        get_ppv_values = get_values_checkbox('ppv', 
                                              key=3, 
                                              value=st.session_state.get_ppv_values, 
                                              disabled=True)
        get_freq_values = get_values_checkbox('freq', 
                                              key=4, 
                                              value=st.session_state.get_freq_values, 
                                              disabled=True)
        calculate = options.button('Go Calculate!', disabled=True)

get_ppv_values = st.session_state.get_ppv_values
get_freq_values = st.session_state.get_freq_values
calculate = st.session_state.calculate_button_clicked

if get_ppv_values and calculate:
    std_df = DataFrame(columns=['X_STD', 'Y_STD', 'Z_STD'])
    ppv_df = DataFrame(columns=['Start Time', 'X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']) 
    folder_name = None
    rion_objects:Dict[str, RionFile] = {}

    for file in uploaded_files:
        file_name = file.name.split('_')
        if not folder_name:
            folder_name = file_name[0].split('/')[0]
        if 'Inst' in file_name:
            rion_file = RionFile(file)
            name = search(r'_(\d){4}_', file.name).group()[1:-1]
            rion_objects[name] = rion_file
            ppv = rion_file.summary
            ppv_df.loc[name] = ppv
    ppv_df = ppv_df.rename(columns={'Start Time':'Measurement Time'}
                           ).rename_axis(
                               'Receivers'
                               ).sort_index()
    if len(ppv_df) !=0:
        with st.expander(f'Data calculated from {folder_name} folder', expanded=True):
            st.dataframe(ppv_df, use_container_width=True)

        with st.expander("Details of a specific measurement"):

            chart_selected = st.selectbox("Select a file to display the a chart with PPV values",
                                        options=ppv_df.index)
            
            #Description of a measurement
            erase_outliers = st.toggle("Reduce Outliers", 
                                       value=False, 
                                       help="Replace the outliers values to the median value")
            st.dataframe(DataFrame(rion_objects[chart_selected].describe).T, use_container_width=True)
            if erase_outliers:
                dataframe = rion_objects[chart_selected].outliers_to_median
            else:
                dataframe = rion_objects[chart_selected].ppv()

            chart_type = st.selectbox("Select a type of chart", 
                                      options=["Line", "Histogram", "Box"])
            if chart_type == "Histogram":
                chart = histogram(dataframe,
                                     x=['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS'])
            if chart_type == "Line":
                chart = line(dataframe,
                                x="Start Time",
                                y=['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS'])
            if chart_type == "Box":
                chart = box(dataframe,
                               x=['PVS'])
            st.plotly_chart(chart, use_container_width=True)
        reset_button = st.button("Reset page")
        if reset_button:
            ppv_df = None
            uploaded_files = None
            st.session_state.calculate_button_clicked = False
