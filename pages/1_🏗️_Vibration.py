import streamlit as st
from pandas import DataFrame, Series, to_datetime, concat
from typing import Literal, Optional, Dict
from data.data_management import export_data
from measurements.vibration import RIONVibrations
from documents.documents import get_receivers_path, BaseLine, FileNotFoundError, NoFilesError
from plotly.express import box, histogram, line
from time import sleep

HELP_PPV_CHECKER = """
    The ppv value of vibration data in "AP" column is calculated for each axis.
    PPV get the maximum value of data for each axis."""

HELP_FREQ_CHECKER = """
This option is not available yet."""

if 'calculate_button_clicked' not in st.session_state:
    st.session_state['calculate_button_clicked'] = False
if 'get_ppv_values' not in st.session_state:
    st.session_state.get_ppv_values = False
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = False
if 'receivers_file' not in st.session_state:
    st.session_state.receivers_file = False


def process_data():
    st.session_state['calculate_button_clicked'] = not st.session_state['calculate_button_clicked']
def get_ppv_values_callback():
    st.session_state.get_ppv_values = not st.session_state.get_ppv_values
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
 
def reset_page():
    uploaded_files.clear()
    st.cache_resource.clear()
    st.cache_data.clear()
    st.session_state['calculate_button_clicked'] = False
    st.session_state['uploaded_files'] =False
    st.rerun()

st.set_page_config(page_title="Vibration Analysis", 
                   page_icon="🏗️",
                   layout="wide")
st.markdown("# Vibration Analysis")
sidebar = st.sidebar

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

#Side bar
uploaded_files = sidebar.file_uploader(
    "Choose a CSV file or drag and drop a folder with all data.", 
    accept_multiple_files=True,
    disabled=st.session_state.get('uploaded_files'))


#Inputs to read the excel file
input_container = sidebar.container(border=True)
sheetName_diurno = input_container.text_input('SheetName diurno',
                                        value="VIBRACIÓN - Diurno",
                                        disabled=st.session_state['calculate_button_clicked'])
sheetName_nocturno = input_container.text_input('SheetName nocturno',
                                        value="VIBRACIÓN - Nocturno",
                                        disabled=st.session_state['calculate_button_clicked'])
col1, col2 = input_container.columns(2)

receivers_col = col1.text_input('Receivers column', 
                                value="A",
                                disabled=st.session_state['calculate_button_clicked'])
memories_col = col2.text_input('Memories column', 
                               value="E",
                               disabled=st.session_state['calculate_button_clicked'])

#Options to process files
st.markdown('### Select the process you want to upload')
options = st.container(border=True)
   
with options:
    #Verificar si no hay seleccionada una opcion, o 
    if (not (st.session_state.get_ppv_values) or not uploaded_files):
        get_ppv_values = get_values_checkbox('ppv', 
                                              key=1,
                                              help=HELP_PPV_CHECKER)
        calculate = options.button('Go Calculate!', disabled=True)
    elif not st.session_state['calculate_button_clicked']:
        get_ppv_values = get_values_checkbox('ppv', 
                                              key=3, 
                                              value=st.session_state.get_ppv_values,
                                              help=HELP_PPV_CHECKER)
        calculate = options.button('Go Calculate!', 
                                   disabled=False, 
                                   on_click=process_data)
    elif st.session_state['calculate_button_clicked']:
        get_ppv_values = get_values_checkbox('ppv', 
                                              key=3, 
                                              value=st.session_state.get_ppv_values, 
                                              disabled=True)
        calculate = options.button('Go Calculate!', disabled=True)

get_ppv_values = st.session_state.get_ppv_values
calculate = st.session_state['calculate_button_clicked']

if not(get_ppv_values and calculate):
    st.warning('Please upload files')
    st.stop()    

std_df = DataFrame(columns=['X_STD', 'Y_STD', 'Z_STD'])
rion_objects:Dict[str, RIONVibrations] = {}

#Get the list of receivers from a excel file
@st.cache_data
def get_receivers_data(uploaded_files):
    receivers_path = get_receivers_path(uploaded_files)
    baseline = BaseLine(receivers_path)
    return baseline

try:
    baseline = get_receivers_data(uploaded_files)
except FileNotFoundError as error:
    st.warning('Receivers file not found')
    receivers_path = None
    baseline = None
    sleep(2)
except NoFilesError as error:
    if not st.session_state.get('uploaded_files'):
        st.error("No compatible files were uploaded.")
        st.session_state['calculate_button_clicked'] = False
        sleep(2)
        st.rerun()

#Read data from files
def get_summary_df(uploaded_files,
                   baseline:Optional[BaseLine]=None,
                   replace_outliers:Optional[bool]=False):
    summary = DataFrame(columns=['Start Time', 'X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']) 
    for file in uploaded_files:
        file.seek(0)
        file_name = file.name.split('_')
        if 'Inst' not in file_name:
            continue
        rion_file = RIONVibrations(file, baseline)
        file_number = rion_file.file_number
        if rion_file == None:
            continue
        rion_file.set_replace_outliers(replace_outliers)
        rion_objects[file_number] = rion_file
        summary.loc[file_number] = rion_file.data.loc[rion_file.data['PVS'].idxmax()]
    return summary

summary_df = st.session_state.get('summary_df', None)
if summary_df is None:
    summary_df = get_summary_df(uploaded_files=uploaded_files,
                                baseline=baseline,
                                replace_outliers=False)
    summary_df_non_outliers = get_summary_df(uploaded_files=uploaded_files,
                                baseline=baseline,
                                replace_outliers=True)
    st.session_state['summary_df'] = summary_df
    st.session_state['summary_df_non_outliers'] = summary_df_non_outliers
    st.session_state['rion_objects'] = rion_objects
    st.session_state['baseline'] = baseline
summary_df_non_outliers = st.session_state.get('summary_df_non_outliers', None)
rion_objects = st.session_state.get('rion_objects', None)
baseline = st.session_state.get('baseline', None)

n_files = [rion for rion in rion_objects]
if len(n_files)==0:
    st.error("No compatible files were uploaded.")
    st.session_state['calculate_button_clicked'] = False
    sleep(2)
    st.rerun()
st.session_state['uploaded_files'] = True
if baseline is not None:
    receivers_baseline = baseline.receivers
    not_receivers_founded = receivers_baseline[receivers_baseline.isin(n_files)]
    all_files:Series = concat([not_receivers_founded['Diurno'],
                        not_receivers_founded['Nocturno']])
    summary_df['Receivers'] = None
    summary_df.loc[all_files[all_files.notna()], 'Receivers'] = all_files[all_files.notna()].index

summary_df = summary_df.rename(columns={'Start Time':'Measurement Time'}
                        ).rename_axis(
                            'File Number'
                            )
summary_df['Measurement Time'] = to_datetime(summary_df['Measurement Time'])

with st.expander(f'Data calculated', expanded=True):
    st.dataframe(summary_df, use_container_width=True)

with st.expander("Details of a specific measurement"):
    reduce_outliers = st.toggle("Reduce Outliers", 
                                value=False, 
                                help="Replace the outliers values to the median value")
    st.session_state['reduce_outliers'] = reduce_outliers
    chart_selected = st.selectbox("Select a file to display the a chart with PPV values",
                                options=summary_df.index)
    rion_file = rion_objects[chart_selected]
    if reduce_outliers:
        dataframe = st.session_state.get('non_outliers_data', None)
        if not isinstance(dataframe, DataFrame):
            rion_file.set_replace_outliers(True)
            dataframe = rion_file.data
            st.session_state['non_outliers_data'] = dataframe
            st.dataframe(DataFrame(dataframe[['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']].describe().T),
                         use_container_width=True)
        st.dataframe(DataFrame(dataframe[['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']].describe().T), 
                        use_container_width=True)
    else:
        dataframe = st.session_state.get('original_data', None)
        if not isinstance(dataframe, DataFrame):
            rion_file.set_replace_outliers(False)
            dataframe = rion_file.data
            st.dataframe(DataFrame(dataframe[['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']].describe().T),
                         use_container_width=True)
            st.session_state['original_data'] = dataframe
        else:
            st.dataframe(DataFrame(dataframe[['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']].describe().T), 
                            use_container_width=True)
    
    chart_type = st.selectbox("Select a type of chart", 
                                options=["Line", "Histogram", "Box"])
    
    labels = ('Time, m/s')
    if chart_type == "Histogram":
        chart = histogram(dataframe,
                                x=['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS'])
    if chart_type == "Line":
        chart = line(dataframe,
                        x="Start Time",
                        y=['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']).update_layout(
                            xaxis_title = "Time [hh:mm]", 
                            yaxis_title = "Displacement [m/s]",
                            legend_title = "Metrics"
                        )
    if chart_type == "Box":
        chart = box(dataframe,
                        x=['PVS'])
    #st.plotly_chart(chart, use_container_width=True)
    col1, col2 = st.columns(2)
    col1.plotly_chart(chart, use_container_width=True)

def export_summary():
    reduce_outliers = st.session_state['reduce_outliers']
    if reduce_outliers:
        dataframe = st.session_state.get('summary_df_non_outliers')
    else:
        dataframe = st.session_state.get('summary_df')
    return export_data(dataframe)


st.download_button(
    label="Download Summary",
    data=export_summary(),
    file_name="Vibration_summary.xlsx",
    mime="application/vnd.ms-excel"
)

reset_button = st.button("Reset page")
if reset_button:
    reset_page()
