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

# ==================== 2. 數據下載與處理函數 ====================

def _fetch_graphql_data(operation_name, query, variables):
    url = 'https://info.cld.hkjc.com/graphql/base/'
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Referer': 'https://bet.hkjc.com/',
        'Origin': 'https://bet.hkjc.com',
        'Accept': '*/*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }
    
    payload = {
        "operationName": operation_name,
        "variables": variables,
        "query": query
    }
    
    # 使用 Session 保持連線
    session = requests.Session()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = session.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # 處理可能的被封鎖情況，稍微等待
                time.sleep(1)
            else:
                st.warning(f"API 請求失敗 (嘗試 {attempt+1}/{max_retries}): {response.status_code}")
        except Exception as e:
            st.error(f"連線異常: {str(e)}")
        time.sleep(0.5)
    return None

def get_investment_data(Date,place,race_no,methodlist):
    # 這裡假設 Date, place, race_no, methodlist 已在外部定義 (原程式碼結構)
    # 若是在 Streamlit 內執行，會讀取到全域變數
    variables = {
        "date": str(Date),
        "venueCode": place,
        "raceNo": int(race_no),
        "oddsTypes": methodlist
    }
    
    query = """
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
    
    data = _fetch_graphql_data("racing", query, variables)
    
    investments = {
        "WIN": [], "PLA": [], "QIN": [], "QPL": [],
        "FCT": [], "TRI": [], "FF": []
    }
    
    if data and 'data' in data:
        race_meetings = data['data'].get('raceMeetings', [])
        if race_meetings:
            for meeting in race_meetings:
                pool_invs = meeting.get('poolInvs', [])
                for pool in pool_invs:
                    # 原有的場地過濾邏輯
                    if place not in ['ST','HV']:
                        pool_id = pool.get('id')
                        if pool_id and pool_id[8:10] != place:
                            continue                
                    
                    inv_val = pool.get('investment')
                    if inv_val is not None:
                        try:
                            investments[pool.get('oddsType')].append(float(inv_val))
                        except (ValueError, TypeError):
                            pass
        else:
            # 靜默失敗或記錄日誌，不中斷 Streamlit 介面
            pass
            
    return investments

def get_odds_data(Date,place,race_no,methodlist):
    variables = {
        "date": str(Date),
        "venueCode": place,
        "raceNo": int(race_no),
        "oddsTypes": methodlist
    }
    
    query = """
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
    
    data = _fetch_graphql_data("racing", query, variables)
    
    odds_values = {
        "WIN": [], "PLA": [], "QIN": [], "QPL": [],
        "FCT": [], "TRI": [], "FF": []
    }
    
    if data and 'data' in data:
        race_meetings = data['data'].get('raceMeetings', [])
        for meeting in race_meetings:
            pm_pools = meeting.get('pmPools', [])
            for pool in pm_pools:
                if place not in ['ST', 'HV']:
                    pool_id = pool.get('id')
                    if pool_id and pool_id[8:10] != place:
                        continue
                
                odds_nodes = pool.get('oddsNodes', [])
                odds_type = pool.get('oddsType')
                
                if not odds_type or odds_type not in odds_values:
                    continue
                
                # 清空該類型的舊資料（原程式碼邏輯）
                odds_values[odds_type] = []
                
                for node in odds_nodes:
                    oddsValue = node.get('oddsValue')
                    if oddsValue == 'SCR':
                        val = np.inf
                    else:
                        try:
                            val = float(oddsValue)
                        except (ValueError, TypeError):
                            continue
                    
                    if odds_type in ["QIN", "QPL", "FCT", "TRI", "FF"]:
                        comb_string = node.get('combString')
                        if comb_string:
                            odds_values[odds_type].append((comb_string, val))
                    else:
                        odds_values[odds_type].append(val)
                        
        # 排序
        for o_type in ["QIN", "QPL", "FCT", "TRI", "FF"]:
            if odds_values[o_type]:
                odds_values[o_type].sort(key=lambda x: x[0])
                
    return odds_values

def fetch_hkjc_jockey_ranking():
    # 目前 2026 年 1 月正處於 2025/26 賽季中期
    season = "25/26" 

    # 1. 完整的 Query Payload (與官方 F12 抓取內容完全一致，不進行任何簡化)
    query = """query rw_GetJockeyRanking($season: String) {
  jockeyStat(season: $season) {
    code
    name_ch
    name_en
    status
    id
    isCurSsn
    season
    ssnStat {
      numFirst
      numSecond
      numThird
      numFourth
      numFifth
      numStarts
      stakeWon
      trk
      ven
    }
    dhStat {
      numFirst
      numSecond
      numThird
      numFourth
      numFifth
      numStarts
      stakeWon
      trk
      ven
    }
  }
}"""

    # 官方請求通常包含 operationName
    payload = {
        "operationName": "rw_GetJockeyRanking",
        "variables": {
            "season": season
        },
        "query": query
    }

    # 2. 完整的 Headers (模擬瀏覽器真實環境，防止被攔截)
    headers = {
        "accept": "*/*",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Referer": "https://racing.hkjc.com/racing/information/Chinese/Jockey/JockeyRanking.aspx",
        "Origin": "https://racing.hkjc.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    try:
        # 執行請求
        response = requests.post(
            "https://info.cld.hkjc.com/graphql/base/", 
            json=payload, 
            headers=headers, 
            timeout=15
        )
        response.raise_for_status()
        result = response.json()

        # 錯誤處理邏輯
        if isinstance(result, list):
            return None, f"API 返回錯誤列表: {result[0].get('message')}"
            
        data = result.get("data")
        if not data:
            error_msg = result.get("errors", [{}])[0].get("message", "Unknown error")
            return None, f"GraphQL 錯誤: {error_msg}"

        jockeys = data.get("jockeyStat", [])
        if not jockeys:
            return None, f"找不到賽季 {season} 的資料 (請確認官方 API 是否變動)"

        rows = []
        for j in jockeys:
            # 解析 ssnStat (這是一個 List)
            ssn_stats = j.get("ssnStat", [])
            
            # 初始化數據容器
            stat_all = {}
            
            # 遍歷列表尋找 trk="ALL" and ven="ALL" (總計數據)
            if isinstance(ssn_stats, list):
                for s in ssn_stats:
                    if s.get("trk") == "ALL" and s.get("ven") == "ALL":
                        stat_all = s
                        break
                
                # 若找不到 ALL，則嘗試抓取第一筆
                if not stat_all and len(ssn_stats) > 0:
                    stat_all = ssn_stats[0]

            rows.append({
                "騎師編號": j.get("code"),
                "騎師": j.get("name_ch"),
                "英文名": j.get("name_en"),
                "勝": stat_all.get("numFirst", 0),
                "亞": stat_all.get("numSecond", 0),
                "季": stat_all.get("numThird", 0),
                "殿": stat_all.get("numFourth", 0),
                "第五": stat_all.get("numFifth", 0),
                "出賽": stat_all.get("numStarts", 0),
                "獎金": stat_all.get("stakeWon", 0),
                "賽季": j.get("season")
            })

        df = pd.DataFrame(rows)
        
        # 數據清理：轉換為數字以便排序
        numeric_cols = ["勝", "亞", "季", "殿", "第五", "出賽", "獎金"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # 計算勝率
        df["勝率 (%)"] = (df["勝"] / df["出賽"].replace(0, 1) * 100).round(1)
        
        # 按照馬會排名規則排序 (勝 > 亞 > 季)
        df = df.sort_values(by=["勝", "亞", "季"], ascending=False).reset_index(drop=True)
        
        # 插入排名欄
        df.insert(0, "排名", df.index + 1)

        return df, None

    except Exception as e:
        return None, f"系統抓取異常: {str(e)}"

def fetch_hkjc_trainer_ranking():
    # 25/26 賽季，嚴格遵循官方格式
    season = "25/26"

    # 完全還原你提供的 Query 字串，不省略任何欄位
    query = """
query rw_GetTrainerRanking($season: String) {
  trainerStat(season: $season) {
    code
    name_ch
    name_en
    status 
    id
    isCurSsn
    season
    visitingIndex
    ssnStat {
      numFirst
      numSecond
      numThird
      numFourth
      numFifth
      numStarts
      stakeWon
      trk
      ven
    }
    dhStat {
      numFirst
      numSecond
      numThird
      numFourth
      numFifth
      numStarts
      stakeWon
      trk
      ven
    }
  }
}
"""

    # 嚴格遵循官方的 Payload 結構
    payload = {
        "operationName": "rw_GetTrainerRanking",
        "variables": {
            "season": season
        },
        "query": query
    }

    # 模擬 200 OK 請求所需的完整 Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0",
        "Referer": "https://racing.hkjc.com/racing/information/Chinese/Trainers/TrainerRanking.aspx",
        "Origin": "https://racing.hkjc.com",
        "Accept": "*/*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }

    try:
        # 使用你測試成功的 URL
        url = "https://info.cld.hkjc.com/graphql/base/"
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        
        result = resp.json()

        # 檢查 GraphQL 內層是否有錯誤
        if "errors" in result:
            return None, f"GraphQL 錯誤: {result['errors'][0].get('message')}"

        data_section = result.get("data")
        if not data_section:
            return None, "API 回傳 data 欄位為空"

        # 關鍵：針對練馬師，Key 是 trainerStat
        trainers = data_section.get("trainerStat", [])
        if not trainers:
            return None, f"找不到賽季 {season} 的練馬師資料"

        rows = []
        for t in trainers:
            # 解析 ssnStat (List 格式)
            ssn_list = t.get("ssnStat", [])
            target_stat = {}
            
            # 遍歷尋找 trk="ALL" 且 ven="ALL" 的總計數據
            if isinstance(ssn_list, list):
                for s in ssn_list:
                    if s.get("trk") == "ALL" and s.get("ven") == "ALL":
                        target_stat = s
                        break
                # 保底邏輯：如果沒找到 ALL，取列表第一筆
                if not target_stat and len(ssn_list) > 0:
                    target_stat = ssn_list[0]

            # 封裝數據
            rows.append({
                "練馬師": t.get("name_ch", "").strip(),
                "勝": target_stat.get("numFirst", 0),
                "亞": target_stat.get("numSecond", 0),
                "季": target_stat.get("numThird", 0),
                "出賽": target_stat.get("numStarts", 0),
                "獎金": target_stat.get("stakeWon", 0)
            })

        df = pd.DataFrame(rows)
        # 強制轉換數字類型確保後續計算不報錯
        numeric_cols = ["勝", "亞", "季", "出賽", "獎金"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        return df, None

    except Exception as e:
        return None, f"抓取異常: {str(e)}"
        
def fetch_horse_age_only(date_val, place_val, race_no):
    if place_val in ['ST','HV']:
        base_url = "https://racing.hkjc.com/racing/information/Chinese/racing/RaceCard.aspx?"
        date_str = str(date_val).replace('-', '/')
        url = f"{base_url}RaceDate={date_str}&Racecourse={place_val}&RaceNo={race_no}"
    
        try:
            # 使用同步 requests 取得網頁
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 這是馬會排位表每行馬匹數據的 class
                table_rows = soup.find_all('tr', class_='f_tac f_fs13')
                
                age_data = []
                for row in table_rows:
                    tds = row.find_all('td')
                    if tds[16]:  # 確保索引 16 (馬齡) 存在
                        age_data.append({
                            "編號": tds[0].text.strip(),
                            "馬名": tds[3].text.strip(),
                            "馬齡": tds[16].text.strip()
                        })
                
                # 返回 DataFrame 並設定編號為索引
                return pd.DataFrame(age_data).set_index("編號")
        except Exception as e:
            st.error(f"獲取馬齡失敗: {e}")
            return None


def save_odds_data(time_now,odds,methodlist):
  for method in methodlist:
      if method in ['WIN', 'PLA']:
        if st.session_state.odds_dict[method].empty:
            # Initialize the DataFrame with the correct number of columns
            st.session_state.odds_dict[method] = pd.DataFrame(columns=np.arange(1, len(odds[method]) + 1))
        st.session_state.odds_dict[method].loc[time_now] = odds[method]
      elif method in ['QIN','QPL',"FCT","TRI","FF"]:
        if odds[method]:
          combination, odds_array = zip(*odds[method])
          if st.session_state.odds_dict[method].empty:
            st.session_state.odds_dict[method] = pd.DataFrame(columns=combination)
            # Set the values with the specified index
          st.session_state.odds_dict[method].loc[time_now] = odds_array
  #st.write(st.session_state.odds_dict)

def save_investment_data(time_now,investments,odds,methodlist):
  for method in methodlist:
      if method in ['WIN', 'PLA']:
        if st.session_state.investment_dict[method].empty:
            # Initialize the DataFrame with the correct number of columns
            st.session_state.investment_dict[method] = pd.DataFrame(columns=np.arange(1, len(odds[method]) + 1))
        investment_df = [round(investments[method][0]  / 1000 / odd, 2) for odd in odds[method]]
        st.session_state.investment_dict[method].loc[time_now] = investment_df
      elif method in ['QIN','QPL',"FCT","TRI","FF"]:
        if odds[method]:
          combination, odds_array = zip(*odds[method])
          if st.session_state.investment_dict[method].empty:
            st.session_state.investment_dict[method] = pd.DataFrame(columns=combination)
          investment_df = [round(investments[method][0]  / 1000 / odd, 2) for odd in odds_array]
              # Set the values with the specified index
          st.session_state.investment_dict[method].loc[time_now] = investment_df

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

def get_overall_investment(time_now,dict,methodlist):
    investment_df = st.session_state.investment_dict
    no_of_horse = len(investment_df['WIN'].columns)
    total_investment_df = pd.DataFrame(index =[time_now], columns=np.arange(1,no_of_horse +1))
    for method in methodlist:
        if method in ['WIN', 'PLA']:
            # Replace _append with pd.concat
            new_data = st.session_state.investment_dict[method].tail(1)
            st.session_state.overall_investment_dict[method] = pd.concat(
                [st.session_state.overall_investment_dict[method], new_data]
            )
            
        elif method in ['QIN', 'QPL']:
            if not investment_df[method].empty:
                # Replace _append with pd.concat
                new_data = investment_combined(time_now, method, st.session_state.investment_dict[method].tail(1))
                st.session_state.overall_investment_dict[method] = pd.concat(
                    [st.session_state.overall_investment_dict[method], new_data]
                )
            else:
                continue

    for horse in range(1,no_of_horse+1):
        total_investment = 0
        for method in methodlist:
            if method in ['WIN', 'PLA']:
                investment = st.session_state.overall_investment_dict[method][horse].values[-1]
            elif method in ['QIN','QPL']:
              if not investment_df[method].empty: 
                investment = st.session_state.overall_investment_dict[method][horse].values[-1]
              else:
                continue
            total_investment += investment
        total_investment_df[horse] = total_investment
    st.session_state.overall_investment_dict['overall'] = pd.concat([st.session_state.overall_investment_dict['overall'], total_investment_df])


def weird_data(time_now, investments, odds, methodlist):
    for method in methodlist:
        if st.session_state.investment_dict[method].empty or len(st.session_state.investment_dict[method]) < 2:
            continue
            
        latest_investment = st.session_state.investment_dict[method].tail(1).values
        # Using previous odds for expectation calculation might be safer, but logic follows user code
        last_time_odds_df = st.session_state.odds_dict[method].tail(2).head(1)
        
        if last_time_odds_df.empty: continue
        last_time_odds = last_time_odds_df.values
        
        try:
            pool_total = investments[method][0]
            expected = pool_total / 1000 / last_time_odds
            # Handling infinity/zero division
            expected = np.where(last_time_odds == np.inf, 0, expected)
            
            diff = np.round(latest_investment - expected, 0)
            diff_df = pd.DataFrame(diff, columns=st.session_state.investment_dict[method].columns, index=[time_now])

            if method in ['WIN','PLA']:
                st.session_state.diff_dict[method] = pd.concat([st.session_state.diff_dict.get(method, pd.DataFrame()), diff_df])
            elif method in ['QIN','QPL']:
                combined_diff = investment_combined(time_now, method, diff_df)
                st.session_state.diff_dict[method] = pd.concat([st.session_state.diff_dict.get(method, pd.DataFrame()), combined_diff])
        except Exception as e:
            # st.error(f"Error in weird_data: {e}")
            pass

def weird_data(investments,methodlist):
    for method in methodlist:
        if st.session_state.investment_dict[method].empty:
            continue
            
        latest_investment = st.session_state.investment_dict[method].tail(1).values
        last_time_odds = st.session_state.odds_dict[method].tail(2).head(1)
        
        # Calculation logic remains the same
        expected_investment = investments[method][0] / 1000 / last_time_odds
        diff = (latest_investment - expected_investment).round(0)
        
        if method in ['WIN', 'PLA']:
            # Replace _append with pd.concat
            st.session_state.diff_dict[method] = pd.concat(
                [st.session_state.diff_dict[method], diff]
            )
        elif method in ['QIN', 'QPL']:
            # Replace _append with pd.concat
            combined_diff = investment_combined(time_now, method, diff)
            st.session_state.diff_dict[method] = pd.concat(
                [st.session_state.diff_dict[method], combined_diff]
            )
    
def change_overall(time_now,methodlist):
    total_investment = 0
    for method in methodlist:
        # Summing the diffs for each method
        total_investment += st.session_state.diff_dict[method].sum(axis=0)
    
    # Create the single-row DataFrame for the current time
    total_investment_df = pd.DataFrame([total_investment], index=[time_now])
    
    # Replace _append with pd.concat
    st.session_state.diff_dict['overall'] = pd.concat(
        [st.session_state.diff_dict['overall'], total_investment_df]
    )
