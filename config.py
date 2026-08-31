import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dateutil import relativedelta as datere
import time
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import plotly.graph_objects as go
import os
from warnings import simplefilter
from bs4 import BeautifulSoup
import re
from math import log
from collections import Counter
import plotly.express as px
import itertools
import matplotlib.colors as mcolors

simplefilter(action="ignore", category=pd.errors.PerformanceWarning) #

# ==================== 0. 頁面與字型設定 ====================
def setup_environment(): #
    st.set_page_config(page_title="Jockey Race", layout="wide") #
    
    FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf" #
    FONT_FILE = "NotoSansCJKtc-Regular.otf" #

    @st.cache_resource
    def get_chinese_font(): #[cite: 1]
        if not os.path.exists(FONT_FILE): #[cite: 1]
            with st.spinner("正在下載中文字型 (首次運行需要)..."): #[cite: 1]
                try:
                    r = requests.get(FONT_URL) #[cite: 1]
                    with open(FONT_FILE, "wb") as f: #[cite: 1]
                        f.write(r.content) #[cite: 1]
                except:
                    st.warning("無法下載中文字型，圖表文字可能顯示為方框。") #[cite: 1]
                    return None #[cite: 1]
        
        if os.path.exists(FONT_FILE): #[cite: 1]
            fm.fontManager.addfont(FONT_FILE) #[cite: 1]
            plt.rcParams['font.family'] = fm.FontProperties(fname=FONT_FILE).get_name() #[cite: 1]
        return FONT_FILE #[cite: 1]

    get_chinese_font() #[cite: 1]

# ==================== 1. Session State 初始化 ====================
def init_session_state(): #[cite: 1]
    defaults = {
        'monitoring': False, 'reset': False, 'odds_dict': {}, 'investment_dict': {}, #[cite: 1]
        'overall_investment_dict': {}, 'weird_dict': {}, 'diff_dict': {}, 'race_dict': {}, #[cite: 1]
        'post_time_dict': {}, 'numbered_list_dict': {}, 'race_dataframes': {}, 'ucb_dict': {}, #[cite: 1]
        'count_history' : {}, 'api_called': False, 'last_update': None, #[cite: 1]
        'jockey_ranking_df': pd.DataFrame(), 'trainer_ranking_df': pd.DataFrame(), #[cite: 1]
        'top_rank_history': [], 'top_4_history': [], 'horse_history': {}, #[cite: 1]
        'high_moneyflow_alerts': pd.DataFrame(columns=["分鐘","時間", "馬號", "當刻賠率", "moneyflow"]) #[cite: 1]
    }
    for key, value in defaults.items(): #[cite: 1]
        if key not in st.session_state: #[cite: 1]
            st.session_state[key] = value #[cite: 1]
