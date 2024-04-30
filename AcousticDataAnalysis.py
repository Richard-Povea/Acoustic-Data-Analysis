import streamlit as st

st.set_page_config(
    page_title="Acoustic Data Analysis",
    page_icon="👋",
)
st.title('Acoustic Data Analysis')
st.write(
    """
    This is a simple acoustic data analysis app.
    Here you can make your own data analysis visualization of your measurements.
    In this moment only vibration analysis to [RION VM-56](https://rion-sv.com/products/10008/VM560009) 
    is available here
    """)

st.page_link("pages/1_📈_Vibration.py", 
             label="Vibration", 
             icon="🏗️")

#SIDEBAR
sidebar = st.sidebar
sidebar.title('Acoustic Data Analysis')
