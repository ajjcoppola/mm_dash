import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.express as px
# Creates a sorted dictionary (sorted by key)
from collections import OrderedDict


## Basic setup and app layout
#st.set_page_config(layout="wide")  # this needs to be the first Streamlit command called
st.title("Market Making Backtest Equity Cumulative Returns")

st.sidebar.title("Control Panel")
st.sidebar.markdown(" Details:  ")
st.sidebar.markdown("[here](https://github.com/crypto-chassis/ccapi) is the ccapi market-making open-source software github, and  ")  
st.sidebar.markdown("Based on avellaneda-stoikovs strategy discussed [here](https://medium.com/open-crypto-market-data-initiative/the-nitty-gritty-of-paper-trading-a-market-making-strategy-792e08116296) and  ") 
st.sidebar.markdown(" a hummingbot article on the strategy is [here](https://medium.com/hummingbot/a-comprehensive-guide-to-avellaneda-stoikovs-market-making-strategy-102d64bf5df6)  ")   
st.sidebar.markdown("A few articles on this strategy are [here](https://medium.com/open-crypto-market-data-initiative/backtest-a-market-making-strategy-an-event-driven-approach-cca165d18ea0).") 
st.sidebar.markdown("Finally, the app used from ccapi is [here](https://github.com/crypto-chassis/ccapi/tree/develop/app/src/spot_market_making) ")

left_col, middle_col, right_col = st.columns(3)

tick_size = 12
axis_title_size = 16



#data_dir = '/home/ajjc/hca/sl_code/ccapi-bt-data/kucoin__btc-usdt__2021-12-01__2021-12-24/'
#data_balance ='kucoin__btc-usdt__2021-12-23__account-balance.csv'
#data_path = data_dir + data_balance
#df = get_data()


with st.echo(code_location='below'): 
    @st.cache
    def get_data(data_path):
        df = pd.read_csv(data_path)

        df['EQUITY'] = df['BASE_AVAILABLE_BALANCE']*df['BEST_BID_PRICE'] + df['QUOTE_AVAILABLE_BALANCE']
        df['EQUITY_RETURNS'] = (1.0 + df['EQUITY'].pct_change()).cumprod()
        df['MIDPT'] = (df['BEST_BID_PRICE'] + df['BEST_ASK_PRICE'])/2.0
        df['MIDPT_RETURNS'] = (1.0 + df['MIDPT'].pct_change()).cumprod()
        df['TIME']=pd.to_datetime(df['TIME'])
        #df.set_index(df['TIME'], inplace=True)

        return df

    import os
    def file_selector(folder_path='.'):
        filenames = os.listdir(folder_path)
        selected_filename = st.selectbox('Select a file', filenames)
        return os.path.join(folder_path, selected_filename)
    #filename = file_selector()
    #st.write('You selected `%s`' % filename)

    day_num = 0
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    uploaded_files = st.file_uploader("Choose exchange/pair strategy days to analyze", type=['csv'], accept_multiple_files=True)
    upf_dict =dict([(x.name,x) for i,x in enumerate(uploaded_files)])
    upf_dict = OrderedDict(sorted(upf_dict.items()))
    upf_dict

    backtest_run_fields = ['exchange','pair','date','stat_field']
    fig = None
    tot_days = len(uploaded_files)
    for uploaded_file in upf_dict.values():
        day_num +=1
        if day_num == 1:
            dataframe = get_data(uploaded_file)
            #st.table(dataframe)
            runnames = uploaded_file.name.split('__')
            run_dict = dict(zip(runnames, backtest_run_fields))
            st.write(run_dict)

            #dataframe = pd.read_csv(uploaded_file)
            fig = px.scatter(dataframe, x='TIME', y=['EQUITY_RETURNS','MIDPT_RETURNS'])
        else:
            df_add = get_data(uploaded_file)
            st.text(uploaded_file.name)
            dataframe = dataframe.append(df_add)
            fig = px.scatter(dataframe, x='TIME', y=['EQUITY_RETURNS','MIDPT_RETURNS'])


        pct_comp = int(100.0*float(day_num)/tot_days)
        status_text.text("%i%% Complete" % pct_comp)
        progress_bar.progress(pct_comp)
        time.sleep(0.001)

    fig
#fig = px.scatter(df, x='TIME', y=['EQUITY_RETURNS','MIDPT_RETURNS'])

#st.plotly_chart(fig)

progress_bar.empty()

#  Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")

