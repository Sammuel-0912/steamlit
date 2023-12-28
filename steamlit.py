import time
import streamlit as st
import numpy as np
import pandas as pd
import pyodbc
import matplotlib.pyplot as plt
#from session_state import SessionState
from pandas.io.formats.style import Styler

class SessionState(object):
    _state = {}

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def get(cls, **kwargs):
        if cls not in cls._state:
            cls._state[cls] = cls(**kwargs)
        return cls._state[cls]

st.set_page_config(
   page_title="Carmax E-KANBAN",
   page_icon="random",
   layout="centered",
   initial_sidebar_state="expanded",
   menu_items={
        'Get Help': 'https://blog.jiatool.com/about/',
        'About': "# 這是什麼網頁？ \n**[IT空間](https://blog.jiatool.com/)** 示範 streamlit 之用網頁"
    }
)

def custom_styles(val):
    # price column styles
    if val.name == 'value':
        styles = []
        # red prices with 0
        for i in val:
            styles.append('color: %s' % ('blue' if i == 0 else 'black'))
        return styles
    # other columns will be yellow
    return ['background-color: blue'] * len(val)

def smaller_font(val):
    return 'font-size: 16px'

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + st.secrets["server"]
        + ";DATABASE="
        + st.secrets["database"]
        + ";UID="
        + st.secrets["username"]
        + ";PWD="
        + st.secrets["password"]
    )

conn = init_connection()

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 100 min.
@st.cache_data(ttl=3000)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

bar = st.progress(0)
for i in range(100):
    bar.progress(i + 1, f'目前進度 {i+1} %')
    time.sleep(0.05)

# Pagination
# page = st.number_input('Page Number', min_value=1, value=1, step=1)
# items_per_page = st.number_input('Items per Page', min_value=1, value=10, step=1)
# start = (page - 1) * items_per_page
# end = page * items_per_page

# Fetch data with pagination
@st.cache_data(ttl=3000)
def fetch_data(query, start, end):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()[start:end]

# if st.button('儲存', type="primary"):
#     st.toast(':rainbow[你編輯的內容已經保存]', icon='💾')

bar.progress(100, '載入完成！')

def color_survived(val):
    color = 'purple' if val<=0 else 'green' if val>=100 else 'blue' 
    return f'background-color: {color}'

tab1, tab2,tab3 = st.tabs(["PVM", "DVR",'EM'])

with tab1: 
    st.header("PVM")

with tab2:
    #st.markdown('<p style="font-size: 40px;">DVR 電子看板</p>', unsafe_allow_html=True)
    #st.header("DVR 電子看板")
    st.cache_resource(ttl=3000, show_spinner="正在加載資料...")  # 👈 Add the caching decorator
   
    search_all_query = (
        "SELECT "
        "tblWIPLOTBasis.CREATEDATE, "
        "tblWIPCont_PartialIn.AreaNo, "
        "tblWIPLOTBasis.MONO, "
        "tblWIPLOTBasis.PRODUCTNO, "
        "tblWIPLOTBasis.BASELOTNO, "
        "tblPRDProductBasis.PRODUCTNAME, "
        "tblWIPLOTBasis.INPUTQTY "
        "FROM tblWIPLOTBasis "
        "LEFT JOIN tblPRDProductBasis ON tblPRDProductBasis.PRODUCTNO = tblWIPLOTBasis.PRODUCTNO "
        "LEFT JOIN tblWIPCont_PartialIn ON tblWIPCont_PartialIn.LotNo = tblWIPLOTBasis.BASELOTNO "
        "WHERE tblPRDProductBasis.PRODUCTNAME LIKE 'DVR%' "
    )

    # Execute the query and fetch data into DataFrame

    df1 = run_query(search_all_query)
    CREATEDATE = [row[0] for row in df1]
    AREANO = [row[1] for row in df1]
    MONO = [row[2] for row in df1]
    PRODUCTNO = [row[3] for row in df1]
    BASELOTNO = [row[4] for row in df1]
    PRODUCTNAME = [row[5] for row in df1]
    INPUTQTY = [row[6] for row in df1]
    
        #Creating a DataFrame with proper column names
    df1_processed = pd.DataFrame({
        "DATE": CREATEDATE,
        "Line" :AREANO,
        "Orderno": MONO,
        "Productno" : PRODUCTNO,
        "Baselotno": BASELOTNO,
        "Productname" : PRODUCTNAME,
        "Orderqty" : INPUTQTY,
        }) 

    #st.dataframe(df1_processed)
    # 创建下拉菜单
    state_1 = SessionState.get(selected_option="")
    options_1 = sorted(list(df1_processed["DATE"].unique()))
    state_1.selected_option = st.sidebar.selectbox("Select an date for querying production information", options_1)
    filtered_df_1 = df1_processed[df1_processed["DATE"] == state_1.selected_option ]
    filtered_df_1 = filtered_df_1.round(2) 
    #original_title = '<p style="font-family:Courier; color:Blue; font-size: 40px;">Original image</p>'
    #st.markdown(original_title, unsafe_allow_html=True)
    #st.dataframe(filtered_df_1)
    styled_table = filtered_df_1[["Line",'Orderno',"Productno","Baselotno",'Productname', 'Orderqty']].sort_values(['Orderqty'], ascending=False).reset_index(drop=True).style.applymap(color_survived, subset=['Orderqty'])
    styled_table = styled_table.format({'Orderqty': '{:.0f}'})

    # Apply styling to the DataFrame
    styled_table.set_table_styles([{
        'selector': 'th',
        'props': [('font-size', '20px'), ('color', 'white')]
    }])
    # Convert the styled DataFrame into an HTML table
    st.table(styled_table)
    # Display the HTML table in Streamlit
    
    # Extracting numeric values
    query = (
        "SELECT "
        "CAST(CREATEDATE AS DATE) AS Date, "
        "SUM(CASE WHEN PositionNo = '01-DVR-ASSY1' THEN 1 ELSE 0 END) AS NumberOfInput, "
        "SUM(CASE WHEN PositionNo = '10-DVR-WEIGH' THEN 1 ELSE 0 END) AS NumberOfOutput "
        "FROM TBLWIPCONT_PCS_LOG "
        "GROUP BY CAST(CREATEDATE AS DATE)"
    )
    df2 = run_query(query)

    #df2 = pd.read_sql_query(query,conn)
    dates = [row[0] for row in df2]
    inputs = [row[1] for row in df2]
    outputs = [row[2] for row in df2]
    # Calculating WIP (outputs - inputs) element-wise
    WIP = [inp - output for inp,output in zip(inputs, outputs)]
    #order_completion = [output / input_qty if input_qty != 0 else 0 for output, input_qty in zip(outputs, INPUTQTY)]
    # Creating a DataFrame with proper column names
    df2_processed = pd.DataFrame({
        "Date": dates,
        "Input": inputs,
        "Output": outputs,
        "WIP" : WIP,
    })
    
    # Styling df2_processed DataFrame
   
    state_2 = SessionState.get(selected_option="")
    options_2 = sorted(list(df2_processed["Date"].unique()))
    state_2.selected_option = st.sidebar.selectbox("Select date for querying Input and Output", options_2)
    filtered_df_2 = df2_processed[df2_processed["Date"] == state_2.selected_option]
    # df2_styled = filtered_df_2.style \
    # .set_table_styles([{
    #     'selector': 'th',
    #     'props': [('font-size', '40px'), ('color', 'blue')]
    # }])
    styled_table_2 = filtered_df_2[['Input',"Output","WIP"]].sort_values(["Input",'Output',"WIP"], ascending=False).reset_index(drop=True).style.applymap(color_survived, subset=["Input",'Output',"WIP"])
    #st.dataframe(df2_styled) 
    styled_table_2.set_table_styles([{
        'selector': 'th',
        'props': [('font-size', '28px'), ('color', 'white')]}])
    st.table(styled_table_2)
    #st.table(order_completion)
with tab3:
    #st.header("EM")

    search_all_query = (
        "SELECT "
        "tblWIPLOTBasis.CREATEDATE, "
        "tblWIPCont_PartialIn.AreaNo, "
        "tblWIPLOTBasis.MONO, "
        "tblWIPLOTBasis.PRODUCTNO, "
        "tblWIPLOTBasis.BASELOTNO, "
        "tblPRDProductBasis.PRODUCTNAME, "
        "tblWIPLOTBasis.INPUTQTY "
        "FROM tblWIPLOTBasis "
        "LEFT JOIN tblPRDProductBasis ON tblPRDProductBasis.PRODUCTNO = tblWIPLOTBasis.PRODUCTNO "
        "LEFT JOIN tblWIPCont_PartialIn ON tblWIPCont_PartialIn.LotNo = tblWIPLOTBasis.BASELOTNO "
        "WHERE tblPRDProductBasis.PRODUCTNAME LIKE 'E-MIRROR%' "
    )

    # Execute the query and fetch data into DataFrame

    df3 = run_query(search_all_query)
    CREATEDATE = [row[0] for row in df3]
    AREANO = [row[1] for row in df3]
    MONO = [row[2] for row in df3]
    PRODUCTNO = [row[3] for row in df3]
    BASELOTNO = [row[4] for row in df3]
    PRODUCTNAME = [row[5] for row in df3]
    INPUTQTY = [row[6] for row in df3]

    #Creating a DataFrame with proper column names
    df3_processed = pd.DataFrame({
        "DATE": CREATEDATE,
        "Line" :AREANO,
        "Productno" : PRODUCTNO,
        "baselotno": BASELOTNO,
        "Productname" : PRODUCTNAME,
        "Orderqty" : INPUTQTY,
    })
    
    # 创建下拉菜单
    pd.io.formats.style.Styler(df3_processed, precision=2,
                           caption="My table")
      
    state_3 = SessionState.get(selected_option="")

    options_3 = sorted(list(df3_processed["DATE"].unique()))
    state_3.selected_option = st.sidebar.selectbox("Select date for querying production information", options_3)
    filtered_df_3 = df3_processed[df3_processed["DATE"] == state_3.selected_option]
    

    styled_table_3 = filtered_df_3[["Line", "Productno", "baselotno", 'Productname', 'Orderqty']].sort_values(['Orderqty'], ascending=False).reset_index(drop=True).style.applymap(color_survived, subset=['Orderqty'])
    styled_table_3 = styled_table_3.applymap(smaller_font, subset = ['Productname'])
    styled_table_3 = styled_table_3.format({'Orderqty': '{:.0f}'})
    
    #styled_table_3_transposed = styled_table_3.T
    # html_table_without_index = styled_table_3.render(index=False)
    # st.write(html_table_without_index, unsafe_allow_html=True)
    
    styled_table_3 = styled_table_3.set_table_styles([
        {'selector': 'th', 'props': [('font-size', '26px'), ('color', 'white')]},
        {'selector': '.col3', 'props': [('font-size', '26px'), ('color', 'white'), ('width', '600px')]},
        {'selector': '.col2', 'props': [('font-size', '26px'), ('color', 'white'), ('width', '350px')]},
        {'selector': '.data', 'props': [('font-size', '12px')]}
    ]) 
    st.table(styled_table_3)
   
    query = (
        "SELECT "
        "CAST(CREATEDATE AS DATE) AS Date, "
        "SUM(CASE WHEN PositionNo = '01-RC-ASSY1' THEN 1 ELSE 0 END) AS NumberOfInput, "
        "SUM(CASE WHEN PositionNo = '10-EM-WEIGH' THEN 1 ELSE 0 END) AS NumberOfOutput "
        "FROM TBLWIPCONT_PCS_LOG "
        "GROUP BY CAST(CREATEDATE AS DATE)"
    )
    df4 = run_query(query)

    dates = [row[0] for row in df4]
    inputs = [row[1] for row in df4]
    outputs = [row[2] for row in df4]
    WIP = [inp - outputs for inp, outputs in zip(inputs, outputs)]

    df4_processed = pd.DataFrame({
        "Date": dates,
        "Input": inputs,
        "Output": outputs,
        "WIP" : WIP
    })

    state_4 = SessionState.get(selected_option="")
    options_4 = sorted(list(df4_processed["Date"].unique()))
    state_4.selected_option = st.sidebar.selectbox("Select a date for querying Input and Output", options_2)
    filtered_df_4 = df4_processed[df4_processed["Date"] == state_4.selected_option]
    df4_styled = filtered_df_4.style.set_table_styles([{
        'selector': 'th',
        'props': [('font-size', '40px'), ('color', 'blue')]
    }])
    
    styled_table_4 = filtered_df_4[['Input', "Output", "WIP"]].sort_values(["Input", 'Output', "WIP"], ascending=False).reset_index(drop=True).style.applymap(color_survived, subset=["Input", 'Output', "WIP"])
    
    styled_table_4.set_table_styles([{
        'selector': 'th',
        'props': [('font-size', '36px'), ('color', 'white')]
    }])
    # Convert the DataFrame to an HTML table without the index
    html_table_without_index = styled_table_4.to_html(index=False)

    # Display the HTML table in Streamlit
    st.write(html_table_without_index, unsafe_allow_html=True)
    
    



