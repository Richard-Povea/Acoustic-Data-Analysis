import streamlit as st
from pandas import DataFrame, read_excel
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
 

st.set_page_config(page_title="Vibration Analysis", page_icon="🏗️")
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
    accept_multiple_files=True)

#Inputs to read the excel file
input_container = sidebar.container(border=True)
sheetName_diurno = input_container.text_input('SheetName diurno',
                                        value="VIBRACIÓN - Diurno",
                                        disabled=st.session_state.calculate_button_clicked)
sheetName_nocturno = input_container.text_input('SheetName nocturno',
                                        value="VIBRACIÓN - Nocturno",
                                        disabled=st.session_state.calculate_button_clicked)
col1, col2 = input_container.columns(2)

receivers_col = col1.text_input('Receivers column', 
                                value="A",
                                disabled=st.session_state.calculate_button_clicked)
memories_col = col2.text_input('Memories column', 
                               value="E",
                               disabled=st.session_state.calculate_button_clicked)

#Options to process files
st.markdown('### Select the process you want to upload')
options = st.container(border=True)
   
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

    #Get the list of receivers from a excel file
    receivers_path = [file for file in uploaded_files if file.name.split('.')[-1] == 'xlsx'][0]
    receivers:dict = read_excel(receivers_path,
                               sheet_name=[sheetName_diurno, sheetName_nocturno],
                               usecols="{},{}".format(receivers_col,
                                                      memories_col))

    with st.expander("See the receivers and memories list", expanded=False):
        diurno:DataFrame = receivers[sheetName_diurno].dropna()
        nocturno:DataFrame = receivers[sheetName_nocturno].dropna()
        merged_records:DataFrame = diurno.merge(nocturno,
                                                how='inner',
                                                on="Punto de medición (AUTOMÁTICO)"
                                                ).rename({"Memoria_x":"Diurno",
                                                          "Memoria_y":"Nocturno"},
                                                          axis=1).set_index("Punto de medición (AUTOMÁTICO)")
        st.dataframe(merged_records, use_container_width=True)

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
            #Maximum PVS value
            max_pvs = ppv_df['PVS'].max()

        with st.expander("Details of a specific measurement"):

            chart_selected = st.selectbox("Select a file to display the a chart with PPV values",
                                        options=ppv_df.index)
            
            #Description of a measurement
            #details_col1, detalis_col2 = st.columns()
            reduce_outliers = st.toggle("Reduce Outliers", 
                                       value=False, 
                                       help="Replace the outliers values to the median value")
            
            if reduce_outliers:
                #st.dataframe(DataFrame(rion_objects[chart_selected].outliers_to_median.describe()).T, use_container_width=True)
                dataframe = rion_objects[chart_selected].outliers_to_median
                st.dataframe(DataFrame(dataframe[['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']].describe().T), 
                             use_container_width=True)
            else:
                dataframe = rion_objects[chart_selected].ppv()
                st.dataframe(DataFrame(dataframe[['X_PPV', 'Y_PPV', 'Z_PPV', 'PVS']].describe().T), 
                             use_container_width=True)
            


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
            #chart.update_yaxes(range=[0,max_pvs])
            st.plotly_chart(chart, use_container_width=True)
        reset_button = st.button("Reset page")
        if reset_button:
            ppv_df = None
            uploaded_files = None
            st.session_state.calculate_button_clicked = False
