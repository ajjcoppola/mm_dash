# Created by HotChiliAnalytics
# Github Repo: https://github.com/ajjcoppola/mm_dash
# Date: 2022-01-27
# Author: Alan Coppola
# @Copyright 2022

import logging
import os
import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.express as px
# Creates a sorted dictionary (sorted by key)
from collections import OrderedDict
from github import Github

## Basic setup and app layout
#st.set_page_config(layout="wide")  # this needs to be the first Streamlit command called
st.title("*CCAPI* - Market Making Backtest")
st.title("Avelleneda-Stoikov Strategy: Equity and Benchmark Cumulative Returns")

st.sidebar.title("Control Panel")
st.sidebar.markdown(" Details:  ")
st.sidebar.markdown("[here](https://github.com/crypto-chassis/ccapi) is the ccapi market-making open-source software github repo")  
st.sidebar.markdown("Based on Avelleneda-Stoikovs strategy discussed [here](https://medium.com/open-crypto-market-data-initiative/the-nitty-gritty-of-paper-trading-a-market-making-strategy-792e08116296) and  ") 
st.sidebar.markdown("A hummingbot article on the strategy is [here](https://medium.com/hummingbot/a-comprehensive-guide-to-avellaneda-stoikovs-market-making-strategy-102d64bf5df6)  ")   
st.sidebar.markdown("A few articles on this strategy are [here](https://medium.com/open-crypto-market-data-initiative/backtest-a-market-making-strategy-an-event-driven-approach-cca165d18ea0).") 
st.sidebar.markdown("Finally, the app used from ccapi is [here](https://github.com/crypto-chassis/ccapi/tree/develop/app/src/spot_market_making) ")

left_col, middle_col, right_col = st.columns(3)

tick_size = 12
axis_title_size = 16

import urllib.request
from pathlib import Path
from typing import List, NamedTuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

HERE = Path(__file__).parent
logger = logging.getLogger(__name__)

def file_selector(folder_path='.'):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox('Select a file', filenames)
    return os.path.join(folder_path, selected_filename)
#filename = file_selector()
#st.write('You selected `%s`' % filename)

# This code is based on https://github.com/streamlit/demo-self-driving/blob/230245391f2dda0cb464008195a470751c01770b/streamlit_app.py#L48  # noqa: E501
def download_file(url, download_to: Path, expected_size=None):  
    # Don't download the file twice.
    # (If possible, verify the download using the file length.)
    if download_to.exists():
        if expected_size:
            if download_to.stat().st_size == expected_size:
                return
        else:
            st.info(f"{url} is already downloaded.")
            if not st.button("Download again?"):
                return

    download_to.parent.mkdir(parents=True, exist_ok=True)

    # These are handles to two visual elements to animate.
    weights_warning, progress_bar = None, None
    try:
        weights_warning = st.warning("Downloading %s..." % url)
        progress_bar = st.progress(0)
        with open(download_to, "wb") as output_file:
            with urllib.request.urlopen(url) as response:
                length = int(response.info()["Content-Length"])
                counter = 0.0
                MEGABYTES = 2.0 ** 20.0
                while True:
                    data = response.read(8192)
                    if not data:
                        break
                    counter += len(data)
                    output_file.write(data)

                    # We perform animation by overwriting the elements.
                    weights_warning.warning(
                        "Downloading %s... (%6.2f/%6.2f MB)"
                        % (url, counter / MEGABYTES, length / MEGABYTES)
                    )
                    progress_bar.progress(min(counter / length, 1.0))
    # Finally, we remove these visual elements by calling .empty().
    finally:
        if weights_warning is not None:
            weights_warning.empty()
        if progress_bar is not None:
            progress_bar.empty()

def get_csv_files_in_dir(directory):
    out = []
    for item in os.listdir(directory):
        try:
            name, ext = item.split(".")
        except:
            continue
        if name and ext:
            if ext in ["csv"]:
                out.append(item)
    return out

#traces_dir = os.path.expanduser("~")
#traces_dir = os.path.expanduser(TRACES_LOCAL_PATH)
#files = get_csv_files_in_dir(str( HERE / "./ccapi-bt-data-1/"))
#files


def get_github_dir_dict(token_str="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",
                        repo_str="/mm_dash" , 
                        repo_dir="ccapi-bt-data/kucoin__btc-usdt__2021-12-01__2021-12-24__av-stok-exhaust"):
    g = Github(token_str)
    user = g.get_user()
    repo = g.get_repo(user.login + repo_str)
    print(f"SampleTracesLocation={repo.name}")
    dir_list  =repo.get_contents(repo_dir)    
    upf_dict = dict([(x.name, x.download_url) for x in dir_list])
    upf_dict = OrderedDict(sorted(upf_dict.items()))

    return upf_dict #Returns sorted {file_name: url_name} dict 

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

    day_num = 0
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    traces = st.container()

    chart_visual = traces.selectbox('Select CCAPI Backtest Traces', 
                                    ('Sample Traces', 'Local Traces'), index=0)
    backtest_run_fields = ['exchange','pair','date','stat_field']
    fig = None
     
    if chart_visual == 'Sample Traces':
        upf_dict = get_github_dir_dict()
        upf_list = sorted(upf_dict.keys())

        all = traces.checkbox("Select all", value=False)
    
        if all:
            selected_options = traces.multiselect("Select one or more example traces:",
                upf_list, upf_list)
        else:
            selected_options =  traces.multiselect("Select one or more example traces",
                upf_list)
        #selected_traces = pd.DataFrame(upf_dict).isin(selected_options)
        upf_dict_filt = {k:v for (k,v) in upf_dict.items() if k in selected_options}
        uploaded_files = list(upf_dict_filt.keys())
        st.write(uploaded_files)

    elif chart_visual == 'Local Traces':
        uploaded_files = traces.file_uploader("Choose exchange/pair strategy days to analyze", type=['csv'], accept_multiple_files=True)
        upf_dict_filt =dict([(x.name,x) for i,x in enumerate(uploaded_files)])
        upf_dict_filt = OrderedDict(sorted(upf_dict_filt.items()))
        st.write(list(uploaded_files))

    tot_days = len(uploaded_files)
    for name, uploaded_file in upf_dict_filt.items():
        day_num +=1
        if day_num == 1:
            dataframe = get_data(uploaded_file)
            #st.table(dataframe)
            ###runnames = uploaded_file.name.split('__')
            ###run_dict = dict(zip(runnames, backtest_run_fields))
            ###st.write(run_dict)

            #dataframe = pd.read_csv(uploaded_file)
            fig = px.scatter(dataframe, x='TIME', y=['EQUITY_RETURNS','MIDPT_RETURNS'])
        else:
            df_add = get_data(uploaded_file)
            st.text(name)
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

