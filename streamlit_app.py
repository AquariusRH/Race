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
st.title("Jockey Race 賽馬程式")

# @title 2. {func} 下載數據
# @title 處理數據
def get_investment_data():
  url = 'https://info.cld.hkjc.com/graphql/base/'
  headers = {'Content-Type': 'application/json'}

  payload_investment = {
      "operationName": "racing",
      "variables": {
          "date": str(Date),
          "venueCode": venue,
          "raceNo": int(race_no),
          "oddsTypes": methodlist
      },
      "query": """
      query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
        raceMeetings(date: $date, venueCode: $venueCode) {
          totalInvestment
          poolInvs: pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
            id
            leg {
              number
              races
            }
            status
            sellStatus
            oddsType
            investment
            mergedPoolId
            lastUpdateTime
          }
        }
      }
      """
  }

  response = requests.post(url, headers=headers, json=payload_investment)

  if response.status_code == 200:
      investment_data = response.json()

      # Extracting the investment into different types of oddsType
      investments = {
          "WIN": [],
          "PLA": [],
          "QIN": [],
          "QPL": []
      }

      race_meetings = investment_data.get('data', {}).get('raceMeetings', [])
      if race_meetings:
          for meeting in race_meetings:
              pool_invs = meeting.get('poolInvs', [])
              for pool in pool_invs:
                  investment = float(pool.get('investment'))
                  investments[pool.get('oddsType')].append(investment)

          #print("Investments:", investments)
      else:
          print("No race meetings found in the response.")

      return investments
  else:
      print(f"Error: {response.status_code}")

def get_odds_data():
  url = 'https://info.cld.hkjc.com/graphql/base/'
  headers = {'Content-Type': 'application/json'}
  payload_odds = {
      "operationName": "racing",
      "variables": {
          "date": str(Date),
          "venueCode": venue,
          "raceNo": int(race_no),
          "oddsTypes": methodlist
      },
      "query": """
      query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
        raceMeetings(date: $date, venueCode: $venueCode) {
          pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
            id
            status
            sellStatus
            oddsType
            lastUpdateTime
            guarantee
            minTicketCost
            name_en
            name_ch
            leg {
              number
              races
            }
            cWinSelections {
              composite
              name_ch
              name_en
              starters
            }
            oddsNodes {
              combString
              oddsValue
              hotFavourite
              oddsDropValue
              bankerOdds {
                combString
                oddsValue
              }
            }
          }
        }
      }
      """
  }

  response = requests.post(url, headers=headers, json=payload_odds)
  if response.status_code == 200:
      odds_data = response.json()
          # Extracting the oddsValue into different types of oddsType and sorting by combString for QIN and QPL
      odds_values = {
          "WIN": [],
          "PLA": [],
          "QIN": [],
          "QPL": []
      }

      race_meetings = odds_data.get('data', {}).get('raceMeetings', [])
      for meeting in race_meetings:
          pm_pools = meeting.get('pmPools', [])
          for pool in pm_pools:
              odds_nodes = pool.get('oddsNodes', [])
              odds_type = pool.get('oddsType')
              for node in odds_nodes:
                  oddsValue = node.get('oddsValue')
                  if oddsValue == 'SCR':
                    oddsValue = np.inf
                  else:
                    oddsValue = float(oddsValue)

                  if odds_type in ["QIN", "QPL"]:
                      odds_values[odds_type].append((node.get('combString'), oddsValue))
                  else:
                      odds_values[odds_type].append(oddsValue)

      # Sorting the QIN and QPL odds values by combString in ascending order
      odds_values["QIN"].sort(key=lambda x: x[0])
      odds_values["QPL"].sort(key=lambda x: x[0])

      #print("WIN Odds Values:", odds_values["WIN"])
      #print("PLA Odds Values:", odds_values["PLA"])
      #print("QIN Odds Values (sorted by combString):", [value for _, value in odds_values["QIN"]])
      #print("QPL Odds Values (sorted by combString):", [value for _, value in odds_values["QPL"]])

      return odds_values
  else:
      print(f"Error: {response.status_code}")

def save_odds_data(time_now,odds):
  for method in methodlist:
      if method in ['WIN', 'PLA']:
        if odds_dict[method].empty:
            # Initialize the DataFrame with the correct number of columns
            odds_dict[method] = pd.DataFrame(columns=np.arange(1, len(odds[method]) + 1))
        odds_dict[method].loc[time_now] = odds[method]
      elif method in ['QIN','QPL']:
        combination, odds_array = zip(*odds['QIN'])
        if odds_dict[method].empty:
          odds_dict[method] = pd.DataFrame(columns=combination)
        # Set the values with the specified index
        odds_dict[method].loc[time_now] = odds_array

def save_investment_data(time_now,investment,odds):
  for method in methodlist:
      if method in ['WIN', 'PLA']:
        if investment_dict[method].empty:
            # Initialize the DataFrame with the correct number of columns
            investment_dict[method] = pd.DataFrame(columns=np.arange(1, len(odds[method]) + 1))
        investment_df = [round(investments[method][0] * 0.825 / 1000 / odd, 2) for odd in odds[method]]
        investment_dict[method].loc[time_now] = investment_df
      elif method in ['QIN','QPL']:
        combination, odds_array = zip(*odds['QIN'])
        if investment_dict[method].empty:
          investment_dict[method] = pd.DataFrame(columns=combination)
        investment_df = [round(investments[method][0] * 0.825 / 1000 / odd, 2) for odd in odds_array]
        # Set the values with the specified index
        investment_dict[method].loc[time_now] = investment_df

def print_data(time_now,period):
  for watch in watchlist:
    data = odds_dict[watch].tail(period)
    data.index = data.index.strftime('%H:%M:%S')
    if watch in ['WIN','PLA']:
      data.columns = numbered_dict[race_no]
    with pd.option_context('display.max_rows', None, 'display.max_columns',None):  # more options can be specified also
        name = methodCHlist[methodlist.index(watch)]
        print(f'{name} 賠率')
        data

def investment_combined(time_now,method,df):
  sums = {}
  for col in df.columns:
      # Split the column name to get the numbers
      num1, num2 = col.split(',')
      # Convert to integers
      num1, num2 = int(num1), int(num2)

      # Sum the column values
      col_sum = df[col].sum()

      # Add the sum to the corresponding numbers in the dictionary
      if num1 in sums:
          sums[num1] += col_sum
      else:
          sums[num1] = col_sum

      if num2 in sums:
          sums[num2] += col_sum
      else:
          sums[num2] = col_sum

  # Convert the sums dictionary to a dataframe for better visualization
  sums_df = pd.DataFrame([sums],index = [time_now]) /2
  return sums_df

def get_overall_investment(time_now,dict):
    investment_df = investment_dict
    no_of_horse = len(investment_df['WIN'].columns)
    total_investment_df = pd.DataFrame(index =[time_now], columns=np.arange(1,no_of_horse +1))
    for method in methodlist:
      if method in ['WIN','PLA']:
        overall_investment_dict[method] = overall_investment_dict[method]._append(investment_dict[method].tail(1))
      elif method in ['QIN','QPL']:
        overall_investment_dict[method] = overall_investment_dict[method]._append(investment_combined(time_now,method,investment_dict[method].tail(1)))

    for horse in range(1,no_of_horse+1):
        total_investment = 0
        for method in methodlist:
            if method in ['WIN', 'PLA']:
                investment = overall_investment_dict[method][horse].values[-1]
            elif method in ['QIN','QPL']:
                investment = overall_investment_dict[method][horse].values[-1]
            total_investment += investment
        total_investment_df[horse] = total_investment
    overall_investment_dict['overall'] = overall_investment_dict['overall']._append(total_investment_df)

def print_bar_chart(time_now):
  post_time = post_time_dict[race_no]
  time_25_minutes_before = np.datetime64(post_time - timedelta(minutes=25) + timedelta(hours=8))
  time_5_minutes_before = np.datetime64(post_time - timedelta(minutes=5) + timedelta(hours=8))

  for method in print_list:
    fig, ax1 = plt.subplots(figsize=(12, 6))
    odds_list = pd.DataFrame()
    if method == 'overall':
          df = overall_investment_dict[method]
          change_data = diff_dict[method].iloc[-1]
    elif method == 'qin_qpl':
          df = overall_investment_dict['QIN'] + overall_investment_dict['QPL']
          change_data = diff_dict['QIN'].sum(axis = 0) + diff_dict['QPL'].sum(axis = 0)
    elif method == 'qin':
          df = overall_investment_dict['QIN']
          change_data = diff_dict[method].sum(axis = 0)
    elif method in ['WIN', 'PLA']:
          df = overall_investment_dict[method]
          odds_list = odds_dict[method]
          change_data = diff_dict[method].sum(axis = 0)

    df.index = pd.to_datetime(df.index)
    df_1st = pd.DataFrame()
    df_2nd = pd.DataFrame()
    df_3rd = pd.DataFrame()

    df_1st = df[df.index< time_25_minutes_before].tail(1)

    df_2nd = df[(df.index >= time_25_minutes_before) & (df.index < time_5_minutes_before)].tail(1)

    df_3rd = df[df.index>= time_5_minutes_before].tail(1)

    change_df = pd.DataFrame([change_data],columns=change_data.index,index =[df.index[-1]])
    if method in ['WIN', 'PLA']:
        odds_list.index = pd.to_datetime(odds_list.index)
        odds_1st = odds_list[odds_list.index< time_25_minutes_before].tail(1)
        odds_2nd = odds_list[(odds_list.index >= time_25_minutes_before) & (odds_list.index < time_5_minutes_before)].tail(1)
        odds_3rd = odds_list[odds_list.index>= time_5_minutes_before].tail(1)

    bars_1st = None
    bars_2nd = None
    bars_3rd = None
    data_df = df_1st._append(df_2nd)
    final_data_df = data_df._append(df_3rd)
    sorted_final_data_df = final_data_df.sort_values(by=final_data_df.index[0], axis=1, ascending=False)
    diff = sorted_final_data_df.diff().dropna()
    diff[diff < 0] = 0
    X = sorted_final_data_df.columns
    X_axis = np.arange(len(X))
    sorted_change_df = change_df[X]
    if not df_1st.empty:
        if df_2nd.empty:
              bars_1st = ax1.bar(X_axis, sorted_final_data_df.iloc[0], 0.4, label='投注額', color='pink')
        else:
              bars_2nd = ax1.bar(X_axis - 0.3, sorted_final_data_df.iloc[1], 0.3, label='25分鐘', color='blue')
              bar = ax1.bar(X_axis+0.3,sorted_change_df.iloc[0],0.3,label='改變',color='grey')
              if not df_3rd.empty:
                  bars_3rd = ax1.bar(X_axis, diff.iloc[0], 0.3, label='5分鐘', color='red')
    else:
          if not df_2nd.empty:
              bars_2nd = ax1.bar(X_axis - 0.3, sorted_final_data_df.iloc[0], 0.3, label='25分鐘', color='blue')
              bar = ax1.bar(X_axis+0.3,sorted_change_df.iloc[0],0.3,label='改變',color='grey')
              if not df_3rd.empty:
                  bars_3rd = ax1.bar(X_axis, diff.iloc[0], 0.3, label='5分鐘', color='red')
          else:
              bars_3rd = ax1.bar(X_axis-0.2, sorted_final_data_df.iloc[0], 0.4, label='5分鐘', color='red')
              bar = ax1.bar(X_axis+0.2,sorted_change_df.iloc[0],0.4,label='改變',color='grey')

      # Add numbers above bars
    if method in ['WIN', 'PLA']:
        if bars_2nd is not None:
          sorted_odds_list_2nd = odds_2nd[X].iloc[0]
          for bar, odds in zip(bars_2nd, sorted_odds_list_2nd):
              yval = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
        if bars_3rd is not None:
          sorted_odds_list_3rd = odds_3rd[X].iloc[0]
          for bar, odds in zip(bars_3rd, sorted_odds_list_3rd):
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
        elif bars_1st is not None:
          sorted_odds_list_1st = odds_1st[X].iloc[0]
          for bar, odds in zip(bars_1st, sorted_odds_list_1st):
              yval = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')

    namelist_sort = [numbered_dict[race_no][i - 1] for i in X]
    formatted_namelist = [label.split('.')[0] + '.' + '\n'.join(label.split('.')[1]) for label in namelist_sort]
    plt.xticks(X_axis, formatted_namelist, fontsize=15)
    ax1.grid(color='lightgrey', axis='y', linestyle='--')
    ax1.set_ylabel('投注額',fontsize=15)
    ax1.tick_params(axis='y')
    fig.legend()

    if method == 'overall':
          plt.title('綜合', fontsize=15)
    elif method == 'qin_qpl':
          plt.title('連贏 / 位置Q', fontsize=15)
    elif method == 'qin':
          plt.title('連贏', fontsize=15)
    elif method == 'WIN':
          plt.title('獨贏', fontsize=15)
    elif method == 'PLA':
          plt.title('位置', fontsize=15)

    st.pyplot(fig)

def weird_data(investments):
  for method in methodlist:
    latest_investment = investment_dict[method].tail(1).values
    last_time_odds = odds_dict[method].tail(2).head(1)
    expected_investment = investments[method][0]*0.825 / 1000 / last_time_odds
    diff = latest_investment - expected_investment
    if method in ['WIN','PLA']:
        diff_dict[method] = diff_dict[method]._append(diff)
    elif method in ['QIN','QPL']:
        diff_dict[method] = diff_dict[method]._append(investment_combined(time_now,method,diff))
    benchmark = benchmark_dict.get(method)
    diff.index = diff.index.strftime('%H:%M:%S')
    for index in investment_dict[method].tail(1).columns:
      error = diff[index].values[0]
      error_df = []
      if error > benchmark:
        if error < benchmark * 2 :
          highlight = '-'
        elif error < benchmark * 3 :
          highlight = '*'
        elif error < benchmark * 4 :
          highlight = '**'
        else:
          highlight = '***'
        error_df = pd.DataFrame([[index,error,odds_dict[method].tail(1)[index].values,highlight]], columns=['No.', 'error','odds', 'Highlight'],index = diff.index)
      weird_dict[method] = weird_dict[method]._append(error_df)

def change_overall(time_now):
  total_investment = diff_dict['WIN'].sum(axis=0)+diff_dict['PLA'].sum(axis=0)+diff_dict['QIN'].sum(axis=0)+diff_dict['QPL'].sum(axis=0)
  total_investment_df = pd.DataFrame([total_investment],index = [time_now])
  diff_dict['overall'] = diff_dict['overall']._append(total_investment_df)

def print_concern_weird_dict():
    for method in methodlist:
        name = methodCHlist[methodlist.index(method)]
        print(f'{name} 異常投注')
        df = weird_dict[method]
        df.tail(20)[::-1]
        count = df.value_counts('No.')
        count.to_frame().T

def print_highlight():
  df = weird_dict['QIN']
  if not df.empty:
    filtered_df = df[df['Highlight'] == '***']
    if not filtered_df.empty:
      crosstab = pd.crosstab(filtered_df['No.'],filtered_df['Highlight']).sort_values(by='***', ascending=False)
      crosstab

def main(time_now,odds,investments,period):
  save_odds_data(time_now,odds)
  save_investment_data(time_now,investments,odds)
  print_data(time_now,period)
  get_overall_investment(time_now,investments)
  weird_data(investments)
  change_overall(time_now)
  print_concern_weird_dict()
  print_bar_chart(time_now)
  print_highlight()

list1 = ['WIN','PLA','QIN','QPL']
list2 = ['WIN','PLA','QIN']
watchlist = ['WIN','PLA']
list1_ch = ['獨贏','位置','連贏','位置Q']
list2_ch = ['獨贏','位置','連贏']

print_list_1 = ['overall', 'qin_qpl', 'WIN', 'PLA']
print_list_2 = ['overall', 'qin', 'WIN', 'PLA']

methodlist = list1
methodCHlist = list1_ch
print_list = print_list_1

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
        np.arange(1,12)
    )

# 基準
benchmarkColumns = st.columns(4)
    ## 獨贏
with benchmarkColumns[0]:
        benchmark_win = st.number_input('獨贏',min_value=0,value=25,step=1)
    ## 位置
with benchmarkColumns[1]:
        benchmark_pla = st.number_input('位置',min_value=0,value=150,step=1)
    ## 連贏
with benchmarkColumns[2]:
        benchmark_qin = st.number_input('連贏',min_value=0,value=25,step=1)
    ## 位置Q
with benchmarkColumns[3]:
        benchmark_qpl = st.number_input('位置Q',min_value=0,value=150,step=1)

benchmark_dict = {
      "WIN": benchmark_win,
      "PLA": benchmark_pla,
      "QIN": benchmark_qin,
      "QPL": benchmark_qpl
  }


if 'reset' not in st.session_state:
    st.session_state.reset = False

def click_start_button():
    st.session_state.reset =  True

st.button('開始',on_click=click_start_button)

url = 'https://info.cld.hkjc.com/graphql/base/'
headers = {'Content-Type': 'application/json'}
payload = {
    "operationName": "raceMeetings",
    "variables": {"date": str(Date), "venueCode": venue},
    "query": """
    fragment raceFragment on Race {
      id
      no
      status
      raceName_en
      raceName_ch
      postTime
      country_en
      country_ch
      distance
      wageringFieldSize
      go_en
      go_ch
      ratingType
      raceTrack {
        description_en
        description_ch
      }
      raceCourse {
        description_en
        description_ch
        displayCode
      }
      claCode
      raceClass_en
      raceClass_ch
      judgeSigns {
        value_en
      }
    }

    fragment racingBlockFragment on RaceMeeting {
      jpEsts: pmPools(
        oddsTypes: [TCE, TRI, FF, QTT, DT, TT, SixUP]
        filters: ["jackpot", "estimatedDividend"]
      ) {
        leg {
          number
          races
        }
        oddsType
        jackpot
        estimatedDividend
        mergedPoolId
      }
      poolInvs: pmPools(
        oddsTypes: [WIN, PLA, QIN, QPL, CWA, CWB, CWC, IWN, FCT, TCE, TRI, FF, QTT, DBL, TBL, DT, TT, SixUP]
      ) {
        id
        leg {
          races
        }
      }
      penetrometerReadings(filters: ["first"]) {
        reading
        readingTime
      }
      hammerReadings(filters: ["first"]) {
        reading
        readingTime
      }
      changeHistories(filters: ["top3"]) {
        type
        time
        raceNo
        runnerNo
        horseName_ch
        horseName_en
        jockeyName_ch
        jockeyName_en
        scratchHorseName_ch
        scratchHorseName_en
        handicapWeight
        scrResvIndicator
      }
    }

    query raceMeetings($date: String, $venueCode: String) {
      timeOffset {
        rc
      }
      activeMeetings: raceMeetings {
        id
        venueCode
        date
        status
        races {
          no
          postTime
          status
          wageringFieldSize
        }
      }
      raceMeetings(date: $date, venueCode: $venueCode) {
        id
        status
        venueCode
        date
        totalNumberOfRace
        currentNumberOfRace
        dateOfWeek
        meetingType
        totalInvestment
        country {
          code
          namech
          nameen
          seq
        }
        races {
          ...raceFragment
          runners {
            id
            no
            standbyNo
            status
            name_ch
            name_en
            horse {
              id
              code
            }
            color
            barrierDrawNumber
            handicapWeight
            currentWeight
            currentRating
            internationalRating
            gearInfo
            racingColorFileName
            allowance
            trainerPreference
            last6run
            saddleClothNo
            trumpCard
            priority
            finalPosition
            deadHeat
            winOdds
            jockey {
              code
              name_en
              name_ch
            }
            trainer {
              code
              name_en
              name_ch
            }
          }
        }
        obSt: pmPools(oddsTypes: [WIN, PLA]) {
          leg {
            races
          }
          oddsType
          comingleStatus
        }
        poolInvs: pmPools(
          oddsTypes: [WIN, PLA, QIN, QPL, CWA, CWB, CWC, IWN, FCT, TCE, TRI, FF, QTT, DBL, TBL, DT, TT, SixUP]
        ) {
          id
          leg {
            number
            races
          }
          status
          sellStatus
          oddsType
          investment
          mergedPoolId
          lastUpdateTime
        }
        ...racingBlockFragment
        pmPools(oddsTypes: []) {
          id
        }
        jkcInstNo: foPools(oddsTypes: [JKC], filters: ["top"]) {
          instNo
        }
        tncInstNo: foPools(oddsTypes: [TNC], filters: ["top"]) {
          instNo
        }
      }
    }
    """
}

# Make a POST request to the API
response = requests.post(url, json=payload)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    # Extract the 'race_no' and 'name_ch' fields and save them into a dictionary
    race_meetings = data.get('data', {}).get('raceMeetings', [])
    race_dict = {}
    post_time_dict = {}
    for meeting in race_meetings:
        for race in meeting.get('races', []):
            race_no = race["no"]
            post_time = race.get("postTime", "Field not found")
            time_part = datetime.fromisoformat(post_time)
            post_time_dict[race_no] = time_part
            race_dict[race_no] = {"馬名": [], "騎師": [],'練馬師':[],'最近賽績':[]}
            for runner in race.get('runners', []):
              if runner.get('standbyNo') == "":
                name_ch = runner.get('name_ch', 'Field not found')
                jockey_name_ch = runner.get('jockey', {}).get('name_ch', 'Field not found')
                trainer_name_ch = runner.get('trainer', {}).get('name_ch', 'Field not found')
                last6run = runner.get('last6run', 'Field not found')
                race_dict[race_no]["馬名"].append(name_ch)
                race_dict[race_no]["騎師"].append(jockey_name_ch)
                race_dict[race_no]["練馬師"].append(trainer_name_ch)
                race_dict[race_no]["最近賽績"].append(last6run)
    

else:
    print(f'Failed to retrieve data. Status code: {response.status_code}')

race_dataframes = {}
numbered_dict ={}

for race_no in race_dict:
    df = pd.DataFrame(race_dict[race_no])
    df.index += 1  # Set index to start from 1
    numbered_list = [f"{i+1}. {name}" for i, name in enumerate(race_dict[race_no]['馬名'])]
    numbered_dict[race_no] = numbered_list
    race_dataframes[race_no] = df

if st.session_state.reset:
    odds_dict = {}
    for method in methodlist:
        odds_dict[method] = pd.DataFrame()
    investment_dict = {}
    for method in methodlist:
        investment_dict[method] = pd.DataFrame()
    overall_investment_dict = {}
    for method in methodlist:
        overall_investment_dict.setdefault(method, pd.DataFrame())
    overall_investment_dict.setdefault('overall',pd.DataFrame())
    weird_dict = {}
    for method in methodlist:
        weird_dict.setdefault(method,pd.DataFrame([],columns=['No.','error','odds','Highlight']))
    diff_dict = {}
    for method in methodlist:
        diff_dict.setdefault(method, pd.DataFrame())
    diff_dict.setdefault('overall',pd.DataFrame())
    print(f"DataFrame for Race No: {race_no}")
    race_dataframes[race_no]

    start_time = time.time()
    end_time = start_time + 60*100
    placeholder = st.empty()
    with st.empty():
        while time.time() <= end_time:
            with st.container():
                time_now = datetime.now() + datere.relativedelta(hours=8)
                odds = get_odds_data()
                investments = get_investment_data()
                period = 10
                main(time_now,odds,investments,period)
                time.sleep(8)


