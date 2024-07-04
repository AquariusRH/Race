import altair as alt
import pandas as pd
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime , timedelta
from dateutil import relativedelta as datere
import matplotlib.pyplot as plt
import matplotlib
matplotlib.font_manager.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
matplotlib.rc('font', family='Taipei Sans TC Beta')
import time
from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
import math
from streamlit_autorefresh import st_autorefresh

# Show the page title and description.
st.set_page_config(page_title="Jockey Race")
st.title("Jockey Race")

# @title 2. {func} 下載數據
def download_data(type,race_no,venue,Date):
    if type == 'winplaodds':
        link = page + 'type=' + type + '&date=' + Date + '&venue=' + venue + '&start=' + str(race_no) + '&end=' + str(race_no)
    elif type == 'qin' or type == 'qpl' or type == 'fct':
        link = page + 'type=' + type + '&date=' + Date + '&venue=' + venue + '&raceno=' + str(race_no)
    odds_json = requests.get(link)
    odds_data = odds_json.json()
    investment_link = 'https://bet.hkjc.com/racing/getJSON.aspx?type=pooltot&date=' + Date + '&venue=' + venue + '&raceno=' + str(race_no)
    investment_json = requests.get(investment_link)
    investment_data = investment_json.json()
    return odds_data , investment_data

def get_win_pla_data(odds_data, investment_data):
    for i in odds_data['OUT'].split('@')[-1].split('#'):
        time = datetime.now() + datere.relativedelta(hours=8)
        no_of_horse = np.arange(total_no_of_horse) + 1
        odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))], columns=no_of_horse)
        method = i.split(';')[0]
        odd = []
        for j in i.split(';')[1:]:
            if '=' in j:
                odd = j.split('=')
            if odd[1] == 'SCR':
                odds[int(odd[0])] = np.inf
            else:
                odds[int(odd[0])] = float(odd[1])
        race_dict[method]['odds']['data'] = race_dict[method]['odds']['data']._append(odds)
        for horse in range(1, total_no_of_horse + 1):
            indicator = horse
            horse_dict[f'No.{horse}'][method]['odds'] = horse_dict[f'No.{horse}'][method]['odds']._append(odds[[indicator]])
    for k in range(0, 2):
        method = investment_data['inv'][k]['pool']
        odds = pd.DataFrame([race_dict[method]['odds']['data'].iloc[-1]])
        investment = float(investment_data['inv'][k]['value']) * 0.825
        investment_df = round(pd.DataFrame(investment / odds) / 1000 ,0)
        race_dict[method]['investment']['data'] = race_dict[method]['investment']['data']._append(investment_df)
        for horse in range(1, total_no_of_horse + 1):
            indicator = horse
            horse_dict[f'No.{horse}'][method]['investment'] = horse_dict[f'No.{horse}'][method]['investment']._append(investment_df[[indicator]])
        if len(race_dict[method]['odds']['data'].index)>1:
            previous_odds = race_dict[method]['odds']['data'].iloc[[-2]]
            current_odds = race_dict[method]['odds']['data'].iloc[[-1]]
            current_investment = race_dict[method]['investment']['data'].iloc[[-1]]
            expected_investment = pd.DataFrame(investment / previous_odds) / 1000
            error_investment = current_investment - expected_investment.values
            for combination in error_investment.columns:
                error = error_investment[combination].values[0]
                if method == 'WIN':
                  benchmark = benchmark_win
                else:
                  benchmark = benchmark_pla
                if error > benchmark:
                  if error < benchmark * 2 :
                    highlight = '-'
                  elif error < benchmark * 3 :
                    highlight = '*'
                  elif error < benchmark * 4 :
                    highlight = '**'
                  else:
                    highlight = '***'
                  error_df = pd.DataFrame([[combination, error,current_odds[combination].values, highlight]], columns=['No.', 'error','odds', 'Highlight'], index=error_investment.index)
                  weird_dict[method] = weird_dict[method]._append(error_df)

def get_qin_data(odds_data, investment_data,type):
    method = type
    combination = []
    for i in odds_data['OUT'].split('#'):
        time = datetime.now() + datere.relativedelta(hours=8)
        for j in i.split(';')[1:]:
            if '=' in j:
                odd = j.split('=')
            if not combination:
                combination = [odd[0]]
            else:
                combination.append(odd[0])
        odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))], columns=combination)
        for j in i.split(';')[1:]:
            if '=' in j:
                odd = j.split('=')
            if odd[1] == 'SCR':
                odds[odd[0]] = np.inf
            else:
                odds[odd[0]] = float(odd[1])
    race_dict[method]['odds']['data'] = race_dict[method]['odds']['data']._append(odds)
    k = 2
    odds = pd.DataFrame([race_dict[method]['odds']['data'].iloc[-1]])
    investment = float(investment_data['inv'][k]['value']) * 0.825
    investment_df = round(pd.DataFrame(investment / odds) / 1000,0)
    race_dict[method]['investment']['data'] = race_dict[method]['investment']['data']._append(investment_df)
    for horse in range(1, total_no_of_horse + 1):
        data_odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))])
        data_investment = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))])
        for i in combination:
          if str(horse) in i.split('-'):
            indicator = i
            data_odds[indicator] = odds[indicator]
            data_investment[indicator] = investment_df[indicator]
        horse_dict[f'No.{horse}'][method]['odds'] = horse_dict[f'No.{horse}'][method]['odds']._append(data_odds)
        horse_dict[f'No.{horse}'][method]['investment'] = horse_dict[f'No.{horse}'][method]['investment']._append(data_investment)
    if len(race_dict[method]['odds']['data'].index) > 1:
        previous_odds = race_dict[method]['odds']['data'].iloc[[-2]]
        current_odds = race_dict[method]['odds']['data'].iloc[[-1]]
        current_investment = race_dict[method]['investment']['data'].iloc[[-1]]
        expected_investment = pd.DataFrame(investment / previous_odds) / 1000
        error_investment = current_investment - expected_investment.values
        for combination in error_investment.columns:
            error = error_investment[combination].values[0]
            benchmark = benchmark_qin
            if error > benchmark:
              if error < benchmark * 2 :
                highlight = '-'
              elif error < benchmark * 3 :
                highlight = '*'
              elif error < benchmark * 4 :
                highlight = '**'
              else:
                highlight = '***'
              error_df = pd.DataFrame([[combination, error,current_odds[combination].values, highlight]], columns=['No.', 'error','odds', 'Highlight'], index=error_investment.index)
              weird_dict[method] = weird_dict[method]._append(error_df)

def get_qpl_data(odds_data, investment_data,type):
    method = type
    combination = []
    for i in odds_data['OUT'].split('#'):
        time = datetime.now() + datere.relativedelta(hours=8)
        for j in i.split(';')[1:]:
            if '=' in j:
                odd = j.split('=')
            if not combination:
                combination = [odd[0]]
            else:
                combination.append(odd[0])
        odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))], columns=combination)
        for j in i.split(';')[1:]:
            if '=' in j:
                odd = j.split('=')
            if odd[1] == 'SCR':
                odds[odd[0]] = np.inf
            else:
                odds[odd[0]] = float(odd[1])
    race_dict[method]['odds']['data'] = race_dict[method]['odds']['data']._append(odds)
    k = 3
    odds = pd.DataFrame([race_dict[method]['odds']['data'].iloc[-1]])
    investment = float(investment_data['inv'][k]['value']) * 0.825
    investment_df = round(pd.DataFrame(investment / odds) / 1000, 0)
    race_dict[method]['investment']['data'] = race_dict[method]['investment']['data']._append(investment_df)
    for horse in range(1, total_no_of_horse + 1):
        data_odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))])
        data_investment = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))])
        for i in combination:
          if str(horse) in i.split('-'):
            indicator = i
            data_odds[indicator] = odds[indicator]
            data_investment[indicator] = investment_df[indicator]
        horse_dict[f'No.{horse}'][method]['odds'] = horse_dict[f'No.{horse}'][method]['odds']._append(data_odds)
        horse_dict[f'No.{horse}'][method]['investment'] = horse_dict[f'No.{horse}'][method]['investment']._append(data_investment)
    if len(race_dict[method]['odds']['data'].index) > 1:
        previous_odds = race_dict[method]['odds']['data'].iloc[[-2]]
        current_odds = race_dict[method]['odds']['data'].iloc[[-1]]
        current_investment = race_dict[method]['investment']['data'].iloc[[-1]]
        expected_investment = pd.DataFrame(investment / previous_odds) / 1000
        error_investment = current_investment - expected_investment.values
        for combination in error_investment.columns:
            error = error_investment[combination].values[0]
            benchmark = benchmark_qpl
            if error > benchmark:
              if error < benchmark * 2 :
                    highlight = '-'
              elif error < benchmark * 3 :
                    highlight = '*'
              elif error < benchmark * 4 :
                    highlight = '**'
              else:
                    highlight = '***'
              error_df = pd.DataFrame([[combination, error,current_odds[combination].values, highlight]], columns=['No.', 'error','odds', 'Highlight'], index=error_investment.index)
              weird_dict[method] = weird_dict[method]._append(error_df)

def get_data():
    for type in types:
        if type != 'trio':
          odds_data, investment_data = download_data(type,race_no,venue,Date)
        if type == 'winplaodds':
            get_win_pla_data(odds_data, investment_data)
        elif type == 'qin':
            get_qin_data(odds_data, investment_data,type)
        elif type == 'qpl':
            get_qpl_data(odds_data, investment_data,type)
        elif type == 'fct':
            get_fct_data(odds_data, investment_data,type)
    get_overall_investment()

def get_fct_data(odds_data, investment_data,type):
  method = type
  combination = []
  for i in odds_data['OUT'].split('#'):
          time = datetime.now() + datere.relativedelta(hours=8)
          for j in i.split(';')[1:]:
              if '=' in j:
                  odd = j.split('=')
              if not combination:
                  combination = [odd[0]]
              else:
                  combination.append(odd[0])
          odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))], columns=combination)
          for j in i.split(';')[1:]:
              if '=' in j:
                  odd = j.split('=')
              if odd[1] == 'SCR':
                  odds[odd[0]] = np.inf
              else:
                  odds[odd[0]] = float(odd[1])
  race_dict[method]['odds']['data'] = race_dict[method]['odds']['data']._append(odds)
  investment = float(investment_data['inv'][4]['value']) * 0.805
  investment_df = round(pd.DataFrame(investment / odds) / 1000, 1)
  race_dict[method]['investment']['data'] = race_dict[method]['investment']['data']._append(investment_df)

  for horse in range(1, total_no_of_horse + 1):
      data_odds = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))])
      data_investment = pd.DataFrame(index=[pd.to_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))])
      for i in combination:
        if str(horse) in i.split('-'):
          indicator = i
          data_odds[indicator] = odds[indicator]
          data_investment[indicator] = investment_df[indicator]
      horse_dict[f'No.{horse}'][method]['odds'] = horse_dict[f'No.{horse}'][method]['odds']._append(data_odds)
      horse_dict[f'No.{horse}'][method]['investment'] = horse_dict[f'No.{horse}'][method]['investment']._append(data_investment)
  if len(race_dict[method]['odds']['data'].index) > 1:
          previous_odds = race_dict[method]['odds']['data'].iloc[[-2]]
          current_odds = race_dict[method]['odds']['data'].iloc[[-1]]
          current_investment = race_dict[method]['investment']['data'].iloc[[-1]]
          expected_investment = pd.DataFrame(investment / previous_odds) / 1000
          error_investment = current_investment - expected_investment.values
          for combination in error_investment.columns:
              error = error_investment[combination].values[0]
              benchmark = benchmark_fct
              if error > benchmark:
                if error < benchmark * 2 :
                      highlight = '-'
                elif error < benchmark * 3 :
                      highlight = '*'
                elif error < benchmark * 4 :
                      highlight = '**'
                else:
                      highlight = '***'
                error_df = pd.DataFrame([[combination, error,current_odds[combination].values, highlight]], columns=['No.', 'error','odds', 'Highlight'], index=error_investment.index)
                weird_dict[method] = weird_dict[method]._append(error_df)
def print_data():
  for watch in watchlist:
    if watch == 'WIN':
      readline = 10
    elif watch == 'PLA':
      readline = 10
    data = race_dict[watch]['odds']['data'].tail(readline)
    idx = data.index.time
    df = data.set_index(idx)
    with pd.option_context('display.max_rows', None, 'display.max_columns',None):  # more options can be specified also
        name = methodCHlist[methodlist.index(watch)]
        st.write(f'{name} 賠率')
        df
# 賠率改變
def find_diff():
  for method in methodlist:
      for focus in focuslist:
          if focus == 'odds':
              diff_df = race_dict[method][focus]['data'].replace('SCR',0).pct_change()*100
          else:
              diff_df = race_dict[method][focus]['data'].replace('SCR', 0).diff()
          diff_df = diff_df.replace(np.nan,0)
          sign_df = np.sign(diff_df)
          sign_df = sign_df.replace(0,'.')
          sign_df = sign_df.replace(1, '+')
          sign_df = sign_df.replace(-1, '-')
          race_dict[method][focus]['diff'] = round(diff_df,2)
          race_dict[method][focus]['sign'] = sign_df

def print_concern_weird_dict():
    for method in methodlist:
        name = methodCHlist[methodlist.index(method)]
        st.write(f'{name} 異常投注')
        printColumns = st.columns(2)
        data = weird_dict[method].tail(20)
        if not data.empty:
            idx = data.index.time
            df = data.set_index(idx)
        else:
            df = data
        with printColumns[0]:
            df
        with printColumns[1]:
            df.value_counts('No.').to_frame().T
            
def print_bar_chart():
    for method in ['overall','qin_qpl','WIN','PLA','fct']:
        if method == 'overall':
            df = overall_investment_dict[method]
        elif method == 'qin_qpl':
            df = overall_investment_dict['qin'] + overall_investment_dict['qpl']
        elif method == 'trio':
            df = overall_investment_dict['trio']
        elif method == 'fct':
            df = overall_investment_dict['fct']
        else:
            df = race_dict[method]['investment']['data']
        first_interval = racetime_df[race_no]["30_minutes_before"]
        second_interval = racetime_df[race_no]["10_minutes_before"]
        third_interval = racetime_df[race_no]["3_minutes_before"]
        df_before = df[df.index < first_interval]
        data_before = df_before.tail(1)
        df_1st = df[df.index >= first_interval]
        df_1st = df_1st[df_1st.index < second_interval]
        data_1st = df_1st.tail(1)
        df_2nd = df[df.index >= second_interval]
        df_2nd = df_2nd[df_2nd.index < third_interval]
        data_2nd = df_2nd.tail(1)
        df_3rd = df[df.index >= third_interval]
        data_3rd = df_3rd.tail(1)
        
        data_df = data_before._append(data_1st)
        data_df = data_df._append(data_2nd)
        data_df = data_df._append(data_3rd)
        
        if len(data_df.index) >1:
          data_df = data_df._append(df.iloc[[-1]])
        data_df = data_df.sort_values(by=data_df.index[0], axis=1, ascending=False)
        diff = data_df.diff().dropna()
        diff[diff<0] = 0
        X = data_df.columns
        X_axis = np.arange(len(X))
        colour = ['pink','blue','lime','red']
        if not data_before.empty:
          if data_1st.empty:
            plt.bar(X_axis, data_df.iloc[-1], 0.4, label='總投注', color=colour[0])
          else:
            if data_2nd.empty:
                plt.bar(X_axis-0.2, diff.iloc[0], 0.2, label='30分鐘', color=colour[1])
            else:
                plt.bar(X_axis-0.2, diff.iloc[0]+diff.iloc[1], 0.2, label='30分鐘', color=colour[1])
                plt.bar(X_axis, diff.iloc[1], 0.2, label='10分鐘', color=colour[2])
                if not data_3rd.empty:
                    plt.bar(X_axis+0.2, diff.iloc[2], 0.2, label='3分鐘', color=colour[3])
        else:
          if not data_1st.empty:
            if data_2nd.empty:
                plt.bar(X_axis-0.2, data_df.iloc[0], 0.2, label='30分鐘', color=colour[1])         
            else:
                plt.bar(X_axis-0.2, data_df.iloc[0]+diff.iloc[0], 0.2, label='30分鐘', color=colour[1])    
                plt.bar(X_axis, diff.iloc[0], 0.2, label='10分鐘', color=colour[2])
                if not data_3rd.empty:
                    plt.bar(X_axis+0.2, diff.iloc[1], 0.2, label='3分鐘', color=colour[3])
          else:
            if not data_2nd.empty:
                plt.bar(X_axis-0.2,data_df.iloc[0],0.4,label = '10分鐘',color = colour[2])
                if not data_3rd.empty:
                    plt.bar(X_axis+0.2, diff.iloc[0], 0.4, label='3分鐘', color=colour[3])
            else:
                if not data_3rd.empty:
                    plt.bar(X_axis,data_df.iloc[0],0.4,label = '3分鐘',color = colour[3])
            
        plt.xticks(X_axis, namelist[X].loc['馬名'],rotation = 45,fontsize = 12)
        plt.grid(color = 'lightgrey' , axis = 'y',linestyle = '--')
        plt.xlabel("No.",fontsize = 10)
        plt.ylabel("投注額",fontsize = 10)
        plt.legend()
        if method == 'overall':
          plt.title('綜合',fontsize = 15)
        elif method == 'qin_qpl':
          plt.title('連贏 / 位置Q',fontsize = 15)
        elif method == 'WIN':
          plt.title('獨贏',fontsize = 15)
        elif method == 'PLA':
          plt.title('位置',fontsize = 15)
        elif method == 'trio':
          plt.title('單T',fontsize = 15)
        elif method == 'fct':
          plt.title('二重彩',fontsize = 15)
        st.set_option('deprecation.showPyplotGlobalUse', False)
        st.pyplot()
        
def get_overall_investment():
    total_investment_df = pd.DataFrame(index =[horse_dict[f'No.{1}']['WIN']['investment'].index[-1]], columns=np.arange(total_no_of_horse)+1)
    investment_df = pd.DataFrame(index=[horse_dict[f'No.{1}']['WIN']['investment'].index[-1]],columns=np.arange(total_no_of_horse) + 1)
    for method in methodlist:
        overall_investment_dict[method] = overall_investment_dict[method]._append(investment_df)
    for horse in range(1,total_no_of_horse+1):
        total_investment = 0
        for method in methodlist:
            if method == 'WIN' or method == 'PLA':
                investment = horse_dict[f'No.{horse}'][method]['investment'].iloc[-1].values
            elif method == 'qin' or method == 'qpl' or method == 'fct':
                investment = horse_dict[f'No.{horse}'][method]['investment'].iloc[-1].sum() /2
            elif method == 'trio':
                investment = horse_dict[f'No.{horse}'][method]['investment'].iloc[-1].sum() /3
            total_investment = investment + total_investment
            overall_investment_dict[method].iloc[-1,(horse-1)] = investment
        total_investment_df[horse] = total_investment
    overall_investment_dict['overall'] = overall_investment_dict['overall']._append(total_investment_df)


page = 'https://bet.hkjc.com/racing/getJSON.aspx?'
types = ['winplaodds','qin','qpl','fct']
methodlist = ['WIN','PLA','qin','qpl','fct']
watchlist = ['WIN','PLA']
focuslist = ['odds','investment']
categorylist = ['data','diff','sign']
methodCHlist = ['獨贏','位置','連贏','位置Q','二重彩']

infoColumns = st.columns(3)
with infoColumns[0]:
    Date = st.date_input('Date').strftime("%Y/%m/%d")
with infoColumns[1]:
    venue = st.selectbox(
        '場地:',
        ['ST','HV','S1','S2','S3','S4','S5']
    )
with infoColumns[2]:
    race_no = st.selectbox(
        '場次:',
        np.arange(1,10)
    )

# 基準
benchmarkColumns = st.columns(5)
    ## 獨贏
with benchmarkColumns[0]:
        benchmark_win = st.number_input('獨贏',min_value=0,value=50,step=1)
    ## 位置
with benchmarkColumns[1]:
        benchmark_pla = st.number_input('位置',min_value=0,value=150,step=1)
    ## 連贏
with benchmarkColumns[2]:
        benchmark_qin = st.number_input('連贏',min_value=0,value=50,step=1)
    ## 位置Q
with benchmarkColumns[3]:
        benchmark_qpl = st.number_input('位置Q',min_value=0,value=150,step=1)
    ## 二重彩
with benchmarkColumns[4]:
        benchmark_fct = st.number_input('二重彩',min_value=0.0,value=5.0,step=0.1)


detailf = 'https://bet.hkjc.com/racing/script/rsdata.js?lang=ch&date='
detail = detailf + Date + '&venue=' + venue + '&CV=L4.07R2a'
rsdata = requests.get(detail)
text = rsdata.text.split('\n')
for line in text:
    if 'racePostTime' in line:
        raceposttime = line.split(' = ')[1].replace(";", "").replace("[", "").replace("]", "").replace('"', "").split(',')[1:]
racetime_df = pd.DataFrame(index=['Time', '30_minutes_before','10_minutes_before','3_minutes_before'])
for i in range(0, len(raceposttime)):
    racetime = datetime.strptime(raceposttime[i], '%Y-%m-%d %H:%M:%S')
    first_interval = racetime - timedelta(minutes = 30)
    second_interval = racetime - timedelta(minutes = 10)
    third_interval = racetime - timedelta(minutes = 3)
    racetime_df[i + 1] = [racetime, first_interval,second_interval,third_interval]

link = 'https://bet.hkjc.com/racing/pages/odds_wp.aspx?lang=ch&date='+Date+'&venue='+venue+'&raceno='+str(race_no)
data = requests.get(link)
text = data.text.split('\n')
namelist = pd.DataFrame(index=['馬名','騎師'])

for line in text:
    if 'normalRunnerList' in line:
      j=1
      for i in line.split(','):
        if 'nameCh' in i:
          k = i.split(':')[-1].replace('"','')
          name = f'{j}.{k}'
        if 'jockeyNameCh' in i:
          jockeyname = i.split(':')[-1].replace('"','')
          namelist[j] = [name,jockeyname]
          j+=1
namelist
total_no_of_horse = len(namelist.columns)
st.write(f'總馬匹:{total_no_of_horse}')


if 'reset' not in st.session_state:
    st.session_state.reset = False

def click_start_button():
    st.session_state.reset =  True

st.button('開始',on_click=click_start_button)


if st.session_state.reset:
    race_dict={}
    concern_dict = {}
    horse_dict = {}
    weird_dict = {}
    overall_investment_dict = {}
    for method in methodlist:
        race_dict.setdefault(method,{})
        for focus in focuslist:
            race_dict[method].setdefault(focus,{})
            for category in categorylist:
                race_dict[method][focus][category] = pd.DataFrame()
        concern_dict.setdefault(method,pd.DataFrame([],columns=['No.','Old','New','Diff','Highlight']))
        weird_dict.setdefault(method,pd.DataFrame([],columns=['No.','error','odds','Highlight']))
        overall_investment_dict.setdefault(method, pd.DataFrame())
    overall_investment_dict.setdefault('overall',pd.DataFrame())
    for horse in range(1,total_no_of_horse+1):
        horse_dict.setdefault(f'No.{horse}',{})
        for method in methodlist:
            horse_dict[f'No.{horse}'].setdefault(method, {})
            for focus in focuslist:
                horse_dict[f'No.{horse}'][method].setdefault(focus,pd.DataFrame())

    start_time = time.time()
    end_time = start_time + 60*45
    placeholder = st.empty()
    with st.empty():
        while time.time() <= end_time:
            with st.container():
                get_data()
                find_diff()
                print_data()
                print_concern_weird_dict()
                print_bar_chart()
                time.sleep(30)
