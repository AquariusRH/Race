import altair as alt
import pandas as pd
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime , timedelta
from dateutil import relativedelta as datere
import time
from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
import math

# Show the page title and description.
st.set_page_config(page_title="Jockey Race")
st.title("Jockey Race")

@st.cache_data
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
benchmarkColumns = st.columns(4)
    ## 獨贏
with benchmarkColumns[0]:
        benchmark_win = st.number_input('獨贏',min_value=0,value=30,step=1)
    ## 位置
with benchmarkColumns[1]:
        benchmark_pla = st.number_input('位置',min_value=0,value=150,step=1)
    ## 連贏
with benchmarkColumns[2]:
        benchmark_qin = st.number_input('連贏',min_value=0,value=75,step=1)
    ## 位置Q
with benchmarkColumns[3]:
        benchmark_qpl = st.number_input('位置Q',min_value=0,value=150,step=1)


odds_data, investment_data = download_data(types[0],race_no,venue,Date)

detailf = 'https://bet.hkjc.com/racing/script/rsdata.js?lang=ch&date='
detail = detailf + Date + '&venue=' + venue + '&CV=L4.07R2a'
rsdata = requests.get(detail)
text = rsdata.text.split('\n')
for line in text:
    if 'racePostTime' in line:
        raceposttime = line.split(' = ')[1].replace(";", "").replace("[", "").replace("]", "").replace('"', "").split(',')[1:]
racetime_df = pd.DataFrame(index=['Time', '20_minutes_before','5_minutes_before'])
for i in range(0, len(raceposttime)):
    racetime = datetime.strptime(raceposttime[i], '%Y-%m-%d %H:%M:%S')
    first_interval = racetime - timedelta(minutes = 20)
    second_interval = racetime - timedelta(minutes = 5)
    racetime_df[i + 1] = [racetime, first_interval,second_interval]

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
