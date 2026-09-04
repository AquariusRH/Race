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
# 引入自訂模組（當你把檔案拆分出去時使用）
import config
import data_fetcher
import visualizer

# ==================== 1. 頁面與全域設定 ====================
st.set_page_config(
    page_title="🏇 Jockey Race 賽馬預測",
    page_icon="🏇",
    layout="wide"
)
# 模擬 config.init_session_state()：初始化所有 session_state 變數
def init_session_state():
    defaults = {
        'api_called': False,
        'odds_dict': {},
        'investment_dict': {},
        'overall_investment_dict': {},
        'diff_dict': {},
        'race_dataframes': {},
        'post_time_dict': {},
        'high_moneyflow_alerts': pd.DataFrame(columns=["分鐘", "時間", "馬號", "當刻賠率", "moneyflow"]),
        'last_update': None,
        'top_rank_history': [],
        'top_4_history': []
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()
# --- 輸入區 ---
with st.sidebar:
    st.header("設定")
    Date = st.date_input('日期:', value=datetime.now(timezone(timedelta(hours=8))).date())
    place = st.selectbox('場地:', ['ST', 'HV', 'S1', 'S2', 'S3' , 'S4', 'S5'])
    race_no = st.selectbox('場次:', np.arange(1, 12))
    
    st.markdown("---")
    st.subheader("監控選項")
    
    # 監控開關
    monitoring_on = st.toggle("啟動即時監控", value=False)
    keep_keys = ["show_bubble", "show_bar", "show_move_bar", "show_top", "show_henery","bar_key", "bubble_key"]
    if st.button("重置所有數據"):
        for key in list(st.session_state.keys()):
            if key not in keep_keys:
                del st.session_state[key]
        st.rerun()
        
    show_bubble = st.toggle("📍 顯示氣泡圖", key="show_bubble", value=False)
    show_bar = st.toggle("📊 顯示長條圖", key="show_bar", value=False)
    show_move_bar = st.toggle("📊 顯示移動長條圖", key="show_move_bar", value=True)
    show_top = st.toggle("🏆 顯示連贏賠率排名", key="show_top", value=True)
    show_henery = st.toggle("🚀 顯示Henery Model 預測", key="show_henery", value=True)
# --- 賽事資料加載 ---
@st.cache_data(ttl=3600)
def fetch_race_card(date_str, venue):
    # 這是一個簡化的 RaceCard 抓取，只抓基本資料以顯示
    # 完整邏輯較長，這裡保留核心概念：抓取馬名與基本資料
    url = 'https://info.cld.hkjc.com/graphql/base/'
    headers = {'Content-Type': 'application/json'}
    payload = {
        "operationName": "raceMeetings",
        "variables": {"date": date_str, "venueCode": venue},
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            races = data.get('data', {}).get('raceMeetings', [])
            race_info = {}
            for meeting in races:
                for race in meeting.get('races', []):
                    r_no = race['no']
                    runners = race.get('runners', [])
                    #st.write(runners)
                    # 關鍵修改：過濾後備馬匹 (standbyNo 為空字串或 None)
                    filtered_runners = [r for r in runners if not r.get('standbyNo')]

                    data_list = []
                    for r in filtered_runners:
                        
                        # --- 關鍵修正：將字串評分轉換為整數 ---
                        try:
                            # 讀取字串並轉換為整數 (int("059") -> 59)
                            rating_val = int(r.get('currentRating', '0'))
                        except (ValueError, TypeError):
                            rating_val = 0
                            
                        # 排位和負磅也同樣進行穩健的數字轉換
                        try:
                            draw_val = int(r.get('barrierDrawNumber', '0'))
                        except (ValueError, TypeError):
                            draw_val = 0

                        try:
                            weight_val = int(r.get('handicapWeight', '0'))
                        except (ValueError, TypeError):
                            weight_val = 0
                        data_list.append({
                            "馬號": r['no'],
                            "馬名": r['name_ch'],
                            "騎師": r['jockey']['name_ch'] if r['jockey'] else '',
                            "練馬師": r['trainer']['name_ch'] if r['trainer'] else '',
                            "近績": r.get('last6run', ''),
                            
                            # 使用轉換後的數值
                            "評分": rating_val,
                            "排位": draw_val,
                            "負磅": weight_val
                        })

                    df = pd.DataFrame(data_list)
                    if not df.empty:
                        # 將馬號轉換為數字並排序，確保順序正確
                        df['馬號_int'] = pd.to_numeric(df['馬號'], errors='coerce')
                        df = df.sort_values("馬號_int").drop(columns=['馬號_int']).set_index("馬號")
                    df_age = data_fetcher.fetch_horse_age_only(date_str, venue, r_no)
                    if df_age is not None and not df_age.empty:
                        # 使用馬號索引進行左連接 (Left Join)
                        # df_age 的索引需要是馬號，對應 df 的索引
                        df = df.join(df_age[['馬齡']], how='left')
                    else:
                        # 如果抓不到馬齡，補上空值欄位避免後續計算報錯
                        df['馬齡'] = ""
                    # Post Time
                    pt_str = race.get("postTime")
                    pt = datetime.fromisoformat(pt_str) if pt_str else None
                    
                    race_info[r_no] = {"df": df, "post_time": pt}
            return race_info
    except Exception as e:
        st.error(e)
    return {}

def fetch_race_card_oversea(date_val, place_val,race_no):
        date_str = str(date_val).replace('-', '')
        headers = {
            'accept': '*/*',
            'accept-language': 'en-us,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://racing.hkjc.com',
            'priority': 'u=1, i',
            'referer': 'https://racing.hkjc.com/',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }
        
        json_data = {
            'variables': {
                'date': str(date_val),
                'venueCode': str(place_val),
                'type': 'LIEF_TIME',
                'meetingDate': date_str,
                'raceNumber': str(race_no),
                'venCode': str(place_val),
            },
            'query': '\nquery RaceCardProfile($date: String, $venueCode: String, $type: STStatType, $ids: [String!], $raceNumber: String, $meetingDate: String) {\n  raceMeetingProfile(date: $date, venueCode: $venueCode) {\n    totalNumberOfRace\n    status\n    pmPools {\n      leg {\n        races\n      }\n      status\n      oddsType\n    }\n    races {\n      id\n      no\n      status\n      postTime\n      raceName_en\n      raceName_ch\n      raceResults {\n        status\n      }\n      countryCodeNm {\n        code\n        english\n        chinese\n      }\n      distance\n      raceCourse {\n        code\n        description_en\n        description_ch\n      }\n      raceTrack {\n        code\n        description_en\n        description_ch\n      }\n      raceType_en\n      raceType_ch\n      raceClass_en\n      raceClass_ch\n      country_en\n      country_ch\n      winningMargin {\n        seqNo\n        lbw\n      }\n      go_en\n      go_ch\n      remarks {\n        name_en\n        name_ch\n        seqNo\n      }\n      runners {\n        horse {\n          name_en\n          name_ch\n          id\n        }\n        status\n        color\n        no\n        handicapWeight\n        jockey {\n          code\n          name_en\n          name_ch\n        }\n        trainer {\n          code\n          name_en\n          name_ch\n        }\n        id\n        last6run\n        internationalRating\n        currentRating \n        sire\n        sexNm {\n          chinese\n          english\n          code\n        }\n        age\n        barrierDrawNumber\n        gearInfo\n        stat(type: $type) {\n          statType\n          numStarts\n          numFirst\n          numSecond\n          numThird\n        }\n        damNm {\n          code\n          chinese\n          english\n        }\n        sireOfDamNm {\n          code\n          chinese\n          english\n        }\n        ownerNm {\n          code\n          chinese\n          english\n        }\n        colorNm {\n          code\n          chinese\n          english\n        }\n      }\n    }\n    date\n    venueCode\n  }\n\n  simulcastHorse(ids: $ids, raceNumber: $raceNumber, meetingDate: $meetingDate, venCode: $venueCode) {\n    id\n    brandNumber\n    earings\n    performanceStats {\n      type\n      firstPlace\n      secondPlace\n      thirdPlace\n      totalRun\n      ssn\n    } \n  }\n}\n',
        }
        
        
        try:
            response = requests.post('https://info.cld.hkjc.com/graphql/base/', headers=headers, json=json_data)

            if response.status_code == 200:
                res_json = response.json()
            # 1. 深入資料層級
            # 這裡假設 variables 傳入的是特定場次，races 通常會是一個列表
                data = res_json.get('data', {})
                profile_list = data.get('raceMeetingProfile', [])
                race_info = {}
                # 注意：races 是 [ ] 列表，所以這裡不能接著 .get('runners')
                for profile in profile_list:
                    # 現在的 profile 是字典了，可以使用 .get()
                    races_list = profile.get('races', [])
                    for race in races_list:
                        runners = race.get('runners', [])
                        r_no = race['no']
                        data_list = []
                        for r in runners:
                            # 模仿你的邏輯：抓取 編號、馬名、馬齡
                            h = r.get('horse', {})
                            rating_val = int(r.get('currentRating')) if r.get('currentRating') else 0
                            draw_val = int(r.get('barrierDrawNumber')) if r.get('barrierDrawNumber') else 0
                            weight_val = int(r.get('handicapWeight')) if r.get('handicapWeight') else 0
                            data_list.append({
                                "馬號": str(r.get('no', '')),
                                "馬名": h.get('name_ch', ''),
                                "馬齡": str(r.get('age', '')),
                                "騎師": r['jockey']['name_ch'] if r.get('jockey') else '',
                                "練馬師": r['trainer']['name_ch'] if r.get('trainer') else '',
                                "近績": r.get('last6run', ''),
                                "評分": rating_val,
                                "排位": draw_val,
                                "負磅": weight_val
                            })
                        df = pd.DataFrame(data_list)
                        if not df.empty:
                            # 將馬號轉換為數字並排序，確保順序正確
                            df['馬號_int'] = pd.to_numeric(df['馬號'], errors='coerce')
                            df = df.sort_values("馬號_int").drop(columns=['馬號_int']).set_index("馬號")
                        # Post Time
                        pt_str = race.get("postTime")
                        pt = datetime.fromisoformat(pt_str) if pt_str else None

                        race_info[r_no] = {"df": df, "post_time": pt}
                    # 返回 DataFrame 並設定編號為索引
                return race_info
        except Exception as e:
            st.error(f"解析發生錯誤: {e}")

def parse_form_score(last6run_str):
    """
    將 '1/2/4/11/2' 這樣的字串轉換為實力分數 (0-100)
    名次越小分數越高。
    """
    if not last6run_str or last6run_str == '-': return 50
    
    ranks = []
    # 處理如 "1/2/3" 或 "1 2 3" 的格式
    parts = re.split(r'[/ ]', str(last6run_str))
    for p in parts:
        p = p.strip()
        if p.isdigit(): ranks.append(int(p))
        elif p == '10': ranks.append(10)
        elif p in ['UR', 'FE', 'DISQ']: ranks.append(14) # 意外視為最後

    if not ranks: return 50
    
    # 只取最近 4 場，權重：0.4, 0.3, 0.2, 0.1
    ranks = ranks[:4]
    weights = [0.4, 0.3, 0.2, 0.1][:len(ranks)]
    # 歸一化權重
    weights = [w / sum(weights) for w in weights]
    
    weighted_rank = sum(r * w for r, w in zip(ranks, weights))
    
    # 趨勢獎勵：如果最近一場比前一場好
    bonus = 0
    if len(ranks) >= 2:
        if ranks[0] < ranks[1]: bonus += 5
        if ranks[0] <= 3: bonus += 5 # 進入前三名獎勵
        
    score = 100 - (weighted_rank - 1) * 7.5 + bonus
    return max(0, min(100, score))

def calculate_jockey_score(jockey_name, ranking_df):
    """
    計算騎師評分
    """
    # 錯誤代碼 51: DataFrame 為空或未定義
    if ranking_df is None or not isinstance(ranking_df, pd.DataFrame) or ranking_df.empty:
        return 54.0

    # 處理輸入名稱
    target_name = str(jockey_name).strip()
    
    # 使用 str.contains 進行模糊搜尋，na=False 防止 NaN 導致崩潰
    # 加入 regex=False 提高效能並防止名稱中含特殊字元
    jockey_row = ranking_df[ranking_df['騎師'].str.contains(target_name, na=False, regex=False)]
    
    # 錯誤代碼 52: 找不到該騎師
    if jockey_row.empty:
        return 52.0

    # 修正：使用對應的欄位名稱 '勝' 與 '出賽'
    wins = jockey_row['勝'].iloc[0]
    runs = jockey_row['出賽'].iloc[0]
    
    # 錯誤代碼 53: 出賽數為 0
    if runs == 0:
        return 53.0
    
    # 計算該騎師勝率
    win_rate = wins / runs
    
    # 取得全港最高勝率作為基準 (篩選出賽超過 10 次的騎師，避免 1 戰 1 勝這種極端值)
    bench_df = ranking_df[ranking_df['出賽'] > 10].copy()
    
    if not bench_df.empty:
        # 計算基準勝率
        bench_df['wr'] = bench_df['勝'] / bench_df['出賽']
        max_rate = bench_df['wr'].max()
    else:
        max_rate = 0.20 # 預設基準
    
    # 確保 max_rate 不為 0
    max_rate = max(max_rate, 0.01)
    
    # 計算分數 (0-100)，並限制最小分數為 15 分
    score = (win_rate / max_rate) * 100
    return round(min(max(score, 15), 100), 1)


def calculate_trainer_score(trainer_name, trainer_df):
    """
    計算練馬師評分
    """
    # 51: 數據表為空
    if trainer_df is None or trainer_df.empty:
        return 54.0

    target_name = str(trainer_name).strip()
    # 模糊匹配
    row = trainer_df[trainer_df['練馬師'].str.contains(target_name, na=False, regex=False)]
    
    # 52: 找不到該人
    if row.empty:
        return 52.0

    wins = row['勝'].iloc[0]
    runs = row['出賽'].iloc[0]
    
    # 53: 出賽數為 0
    if runs == 0:
        return 53.0
    
    win_rate = wins / runs
    
    # 基準勝率 (排除出賽太少的練馬師)
    bench_df = trainer_df[trainer_df['出賽'] > 10].copy()
    if not bench_df.empty:
        bench_df['wr'] = bench_df['勝'] / bench_df['出賽']
        max_rate = bench_df['wr'].max()
    else:
        max_rate = 0.15 # 練馬師勝率通常比頂尖騎師低一點，給個合理的預設
    
    max_rate = max(max_rate, 0.01)
    
    score = (win_rate / max_rate) * 100
    return round(min(max(score, 15), 100), 1)
def calculate_smart_score(race_no):
    """
    計算單場賽事的綜合評分，並將所有中間結果整合到單一 df。
    """
    
    # ----------------------------------------------------
    # I. 數據準備與初始 df 建立
    # ----------------------------------------------------
    
    # 1. 獲取最新賠率 (Odds)
    if 'WIN' not in st.session_state.odds_dict or st.session_state.odds_dict['WIN'].empty:
        return pd.DataFrame()
        
    latest_odds = st.session_state.odds_dict['WIN'].tail(1).T
    latest_odds.columns = ['Odds']
    
    # 2. 獲取資金流向 (MoneyFlow)
    # 建立一個基礎的 DataFrame，索引與 latest_odds 一致，初始值為 0
    total_money_flow = pd.DataFrame(0, index=latest_odds.index, columns=['MoneyFlow'])
    total_overall_flow = pd.DataFrame(0, index=latest_odds.index, columns=['OverallMoneyFlow'])
    for method in methodlist:
        # 檢查該種類是否存在於 session_state 且不為空
        if method in st.session_state.diff_dict and not st.session_state.diff_dict[method].empty:
            # 提取最近 10 筆數據並加總
            # .sum() 會根據欄位加總，確保索引對齊
            current_method_sum = st.session_state.diff_dict[method].tail(10).sum()
            all_time_sum = st.session_state.diff_dict[method].sum()
            # 將加總後的數據加到總表中 (使用 add 函數可以自動處理索引不匹配的情況)
            total_money_flow['MoneyFlow'] = total_money_flow['MoneyFlow'].add(current_method_sum, fill_value=0)
            total_overall_flow['OverallMoneyFlow'] = total_overall_flow['OverallMoneyFlow'].add(all_time_sum, fill_value=0)
    # 最後得到的 money_flow 就是四個種類加總後的結果
    money_flow = total_money_flow
        
    # 3. 建立基礎 df (包含動態數據)
    df = pd.concat([latest_odds, money_flow, total_overall_flow], axis=1)
    
    # 4. 獲取靜態數據
    if race_no not in st.session_state.race_dataframes:
        return pd.DataFrame()
        
    # 我們只需要 '馬號' 和計算分數所需的欄位
    static_df = st.session_state.race_dataframes[race_no].copy()
    
    # ----------------------------------------------------
    # II. 索引標準化 (確保合併成功)
    # ----------------------------------------------------
    
    # 確保 static_df 以 '馬號' 作為索引
    if static_df.index.name != '馬號':
        static_df = static_df.reset_index().set_index('馬號')
        
    # **關鍵步驟：強制將兩個 DataFrame 的索引類型統一為字串**
    try:
        df.index = df.index.astype(str)
        static_df.index = static_df.index.astype(str)
    except Exception as e:
        st.error(f"索引轉換錯誤: {e}")
        return pd.DataFrame()
        
    # ----------------------------------------------------
    # III. 靜態數據分數計算 (在 static_df 上計算)
    # ----------------------------------------------------
    
    # 檢查並補齊必要的欄位
    required_cols = ['近績', '評分', '排位'] # 只需要計算所需欄位
    for col in required_cols:
        if col not in static_df.columns:
            static_df[col] = 0
            
    # 1. 狀態分數 (Form Score) - 權重 40%
    static_df['FormScore'] = static_df['近績'].apply(parse_form_score)
    
    # 2. 騎師分數 (Jockey Score) - 權重 15% (取代部分 Synergy)
    j_df, j_err = data_fetcher.fetch_hkjc_jockey_ranking()
    t_df, t_err = data_fetcher.fetch_hkjc_trainer_ranking()
    static_df['JockeyScore'] = static_df['騎師'].apply(
        lambda x: calculate_jockey_score(str(x).strip(), j_df)
    )
    
    # 練馬師分數 (15%)
    static_df['TrainerScore'] = static_df['練馬師'].apply(
        lambda x: calculate_trainer_score(str(x).strip(), t_df)
    )
    
    # 3. 適應性分數 (Draw Score) - 權重 20%
    static_df['排位_int'] = pd.to_numeric(static_df['排位'], errors='coerce').fillna(99)
    static_df['DrawScore'] = 100 - (static_df['排位_int'] - 1) * (100 / 13) 
    
    # 4. 負擔分數 (Rating Score) - 權重 10%
    static_df['Rating_int'] = pd.to_numeric(static_df['評分'], errors='coerce').fillna(0)
    max_rating = static_df['Rating_int'].replace(0, np.nan).max() # 避免 max_rating 為 0
    
    if pd.isna(max_rating):
        static_df['RatingDiffScore'] = 50
    else:
        static_df['RatingDiffScore'] = (static_df['Rating_int'] / max_rating) * 100 
    
    # 最終靜態加權公式
    static_df['TotalFormScore'] = (static_df['FormScore'] * 0.4) + \
                                  (static_df['JockeyScore'] * 0.15) + \
                                  (static_df['TrainerScore'] * 0.15) + \
                                  (static_df['DrawScore'] * 0.2) + \
                                  (static_df['RatingDiffScore'] * 0.1)
    
    # ----------------------------------------------------
    # IV. 使用 join/merge 將靜態分數整合到 df (達成單一 df 目的)
    # ----------------------------------------------------
    
    # 只取出計算好的分數欄位
    static_scores = static_df[['馬名','馬齡','騎師','排位','練馬師','TotalFormScore', 'FormScore', 'JockeyScore','TrainerScore', 'DrawScore', 'RatingDiffScore']]
    
    # 使用 join 進行合併：左連接，以 df 的馬號為準。
    # 由於索引已統一為字串，join 將正確地按馬號匹配。
    df = df.join(static_scores, how='left')
    df['顯示名稱'] = df.index.astype(str) + ". " + df['馬名'].fillna("未知")
    # 如果有馬匹在靜態數據中找不到 (例如 TotalFormScore 為 NaN)，則填入預設值
    df['TotalFormScore'] = df['TotalFormScore'].fillna(50) 
    
    # ----------------------------------------------------
    # V. 在單一 df 上計算最終綜合得分 (TotalScore)
    # ----------------------------------------------------
    
    # A. 資金分數 (MoneyScore)
    min_flow = df['MoneyFlow'].min()
    max_flow = df['MoneyFlow'].max()
    
    # 避免 MoneyFlow 都是 0 時除以 0
    if max_flow != min_flow:
        df['MoneyScore'] = (df['MoneyFlow'] - min_flow) / (max_flow - min_flow) * 100
    else:
        df['MoneyScore'] = 50
        
    # B. 價值分數 (ValueScore: 隱含勝率/熱度)
    # 避免 Odds 為 0 或 NaN 時除以 0
    df['ValueScore'] = np.where(df['Odds'].replace(0, np.nan).isna(), 0, (1 / df['Odds']) * 100)
    
    # C. 最終加權公式 (實力 30% + 資金流向 50% + 賠率熱度 20%)
    df['TotalScore'] = (df['TotalFormScore'] * 0.3) + \
                       (df['MoneyScore'] * 0.5) + \
                       (df['ValueScore'] * 0.2)
    df.loc[np.isinf(df['Odds']), 'TotalScore'] = 0                        
    return df.sort_values('TotalScore', ascending=False)
    
def calculate_smart_score_static(race_no):
    """
    核心預測算法（靜態版）：專為比賽前一日，缺乏賠率和資金流數據時設計。
    權重：狀態 (40%) + 配搭 (30%) + 適應性 (20%) + 負擔 (10%)
    """
    if race_no not in st.session_state.race_dataframes:
        return pd.DataFrame()
    
    static_df = st.session_state.race_dataframes[race_no].copy()
    
    # 確保所有馬匹都有一個馬號索引
    if static_df.index.name != '馬號':
        static_df = static_df.reset_index().set_index('馬號')

    # 檢查關鍵欄位是否存在 (如果沒有，需要先在 fetch_race_card 中獲取)
    required_cols = ['近績', '評分', '排位', '騎師', '練馬師']
    for col in required_cols:
        if col not in static_df.columns:
            # 這是為了兼容，但建議您去 fetch_race_card 補齊這些欄位
            static_df[col] = 0 
            
    # 1. 狀態分數 (Form Score) - 權重 40%
    # 使用原有的 parse_form_score
    static_df['FormScore'] = static_df['近績'].apply(parse_form_score)
    
    # 2. 騎師分數 (Jockey Score) - 權重 15% (取代部分 Synergy)
    j_df, j_err = data_fetcher.fetch_hkjc_jockey_ranking()
    t_df, t_err = data_fetcher.fetch_hkjc_trainer_ranking()
    static_df['JockeyScore'] = static_df['騎師'].apply(
        lambda x: calculate_jockey_score(str(x).strip(), j_df)
    )
    
    # 練馬師分數 (15%)
    static_df['TrainerScore'] = static_df['練馬師'].apply(
        lambda x: calculate_trainer_score(str(x).strip(), t_df)
    )
    
    # 3. 適應性分數 (Adaptability Score) - 權重 20%
    # 排位（檔位）：在該場地/距離下，外檔或內檔表現如何？
    # 假設：通常內檔 (1-4) 較好，中檔 (5-8) 次之，外檔 (9+) 較差
    
    static_df['排位_int'] = pd.to_numeric(static_df['排位'], errors='coerce').fillna(99)
    static_df['DrawScore'] = 100 - (static_df['排位_int'] - 1) * (100 / 13) # 1號檔 100分，14號檔 0分
    
    # 4. 負擔分數 (Burden Score) - 權重 10%
    # 評分與負磅的關係：評分越高負磅越重，負擔越大
    # 簡化：評分最高的馬匹，給予負擔分數較低（因為大家都看好它，但它要負重）
    static_df['Rating_int'] = pd.to_numeric(static_df['評分'], errors='coerce').fillna(0).astype(float)

    # 2. 計算最大評分
    max_rating = static_df['Rating_int'].max()
    
    # 3. 評分差異分數 (相對分數)
    # 加入條件判斷：如果最高評分大於 0 才進行除法，否則全給 0 分（或 100 分，取決於你的邏輯）
    if max_rating > 0:
        static_df['RatingDiffScore'] = (static_df['Rating_int'] / max_rating) * 100
    else:
        static_df['RatingDiffScore'] = 0.0
    
    # 4. 如果你最後一定要轉換回整數，請再次確保填補可能產生的 inf/nan
    static_df['RatingDiffScore'] = static_df['RatingDiffScore'].replace([np.inf, -np.inf], 0).fillna(0).astype(int)
    
    # --- 最終加權公式 (完全基於靜態數據) ---
    df = static_df.copy()
    
    df['TotalScore'] = (df['FormScore'] * 0.40) + \
                       (df['JockeyScore'] * 0.15) + \
                       (df['TrainerScore'] * 0.15) + \
                       (df['DrawScore'] * 0.20) + \
                       (df['RatingDiffScore'] * 0.10)
                       
    # 清理並輸出
    output_cols = ['馬名','馬齡','騎師','排位','練馬師','FormScore', 'JockeyScore', 'TrainerScore', 
                   'DrawScore', 'RatingDiffScore', 'TotalScore']
    
    # 只選取存在的欄位
    final_cols = [col for col in output_cols if col in df.columns]

    df = df[final_cols].sort_values('TotalScore', ascending=False)
    
    return df
# 嘗試加載 Race Card
date_str = str(Date)
if not st.session_state.api_called:
    with st.spinner("載入賽事資料中..."):
        if place in ["ST","HV"]:
            race_card_data = fetch_race_card(date_str, place)
        else:
            race_card_data = fetch_race_card_oversea(date_str, place,race_no)

        if race_card_data:
            st.session_state.race_dataframes = {k: v['df'] for k,v in race_card_data.items()}
            st.session_state.post_time_dict = {k: v['post_time'] for k,v in race_card_data.items()}
            st.session_state.api_called = True

# --- 顯示賽事資訊 ---
if race_no in st.session_state.race_dataframes:
    pt = st.session_state.post_time_dict.get(race_no)
    pt_str = pt.strftime("%H:%M") if pt else "--:--"
    st.info(f"📍 {place} 第 {race_no} 場 | 🕒 開跑: {pt_str}")
    with st.expander("查看排位表", expanded=False):
        st.dataframe(st.session_state.race_dataframes[race_no], width='stretch')
else:
    st.warning("找不到此場次資料，請確認日期與場地。")

# ==================== 5. 監控循環邏輯 ====================

methodlist = ['WIN', 'PLA', 'QIN', 'QPL'] # 簡化預設
time_delay = 10
if len(st.session_state.race_dataframes[race_no]['馬名'])<7:
    print_list = ['WIN&QIN','PLA']
else:
    print_list = ['WIN&QIN', 'PLA&QPL']
top_list = ['QIN']
methodCHlist = ['連贏']
for method in methodlist:
    # 確保 odds_dict, investment_dict, overall_investment_dict, diff_dict 都有 WIN/PLA/QIN/QPL 鍵
    st.session_state.odds_dict.setdefault(method, pd.DataFrame())
    st.session_state.investment_dict.setdefault(method, pd.DataFrame())
    st.session_state.overall_investment_dict.setdefault(method, pd.DataFrame())
    st.session_state.diff_dict.setdefault(method, pd.DataFrame())
    
# 確保 overall 鍵存在於整體投注量和差異字典中
st.session_state.overall_investment_dict.setdefault('overall', pd.DataFrame())
st.session_state.diff_dict.setdefault('overall', pd.DataFrame())

# ==================== 5. 監控與顯示邏輯 (使用 Fragment 避免閃爍) ====================
placeholder = st.empty()
if monitoring_on:
    while monitoring_on:
        # --- 實時監控模式 (比賽當日) ---
        #st.markdown("### 🟢 實時監控與資金流預測中...")
        time_now = datetime.now()+timedelta(hours=8)
        time_str = time_now.strftime('%H:%M:%S')
    
        # 1. 抓取數據 (這裡需要您的實際抓取邏輯)
    
    
        odds = data_fetcher.get_odds_data(Date,place,race_no,methodlist)
        investments = data_fetcher.get_investment_data(Date,place,race_no,methodlist)
    
        if odds and investments:
            with st.spinner(f"更新數據中 ({time_str})..."):
                # 2. 處理數據
                # 這裡需要您的 
                data_fetcher.save_odds_data(time_now,odds,methodlist)
                data_fetcher.save_investment_data(time_now,investments,odds,methodlist)
                data_fetcher.get_overall_investment(time_now,investments,methodlist)
                data_fetcher.weird_data(time_now,investments,odds,methodlist)
                data_fetcher.change_overall(time_now,methodlist)
                # 由於篇幅限制，假設已運行
                st.session_state.last_update = time_now
        
        # 3. 顯示結果
        with placeholder.container():
            HK_TZ = timezone(timedelta(hours=8))
            now_naive = datetime.now()
            now = now_naive + datere.relativedelta(hours=8)
            now = now.replace(tzinfo=HK_TZ)
            post_time_raw = st.session_state.post_time_dict.get(race_no)
            
            if post_time_raw is None:
                        time_str = "未載入"
            else:
                        # 確保 post_time 也有時區
                        if post_time_raw.tzinfo is None:
                            post_time = post_time_raw.replace(tzinfo=HK_TZ)
                        else:
                            post_time = post_time_raw  # 已有時區
                    
                        seconds_left = (post_time - now).total_seconds()
                        
                        if seconds_left <= 0:
                            time_str = "已開跑"
                            minutes = -1
                        else:
                            minutes = int(seconds_left // 60)
                            time_str = f"離開跑 {minutes} 分"  
            last_update_str = st.session_state.last_update.strftime('%H:%M:%S') if st.session_state.last_update else "N/A"
            status_icon = "🏁" if "已開跑" in time_str else "⏳"
    
            st.markdown(f"### {status_icon} {time_str} ｜ ⏱️ 最後同步時間：`{last_update_str}`")
            
            # A. 氣泡圖 (資金流向視覺化)
            if show_bubble:
                visualizer.print_bubble(race_no, print_list)
            if show_bar:    
                visualizer.print_bar_chart(time_now)
            if show_move_bar:
                visualizer.print_plotly_advanced_bar(race_no,print_list)
            #plot_racing_monitor_dashboard()
            # B. 實時預測排名
            st.markdown("### 🤖 實時資金流綜合預測排名")
            prediction_df = calculate_smart_score(race_no)

            if not prediction_df.empty:
                high_flow_df = prediction_df[prediction_df['MoneyFlow'] > 500]
                
                if not high_flow_df.empty:
                    new_alerts = []
                    for horse_no, row in high_flow_df.iterrows():
                        new_alerts.append({
                            "分鐘": minutes,
                            "時間": time_str,
                            "馬號": horse_no,
                            "當刻賠率": f"{row['Odds']:.1f}" if pd.notna(row['Odds']) else "-",
                            "moneyflow": round(row['MoneyFlow'], 1)
                        })
                    new_alerts_df = pd.DataFrame(new_alerts)
                    
                    # 1. 直接將新資料合併到既有的歷史紀錄中
                    combined_df = pd.concat([st.session_state.high_moneyflow_alerts, new_alerts_df], ignore_index=True)
                    
                    # 2. 核心處理：
                    #    - 先按 moneyflow 降序排序（大的在前）
                    #    - 然後針對「時間」和「馬號」這兩個欄位去重，並保留第一個（即最大的那個）
                    st.session_state.high_moneyflow_alerts = (
                        combined_df.sort_values(by='moneyflow', ascending=False)
                                   .drop_duplicates(subset=['時間','馬號'], keep='first')
                                   .reset_index(drop=True)
                    )

                # 使用 st.expander 顯示下拉式表格
                with st.expander("🚨 異常大額資金流紀錄 (MoneyFlow > 500)", expanded=False):
                    if st.session_state.high_moneyflow_alerts.empty:
                        st.info("目前尚無大於 500 的資金流紀錄。")
                    else:
                        # 將最新紀錄排在最上面以利閱讀
                        display_alerts = st.session_state.high_moneyflow_alerts.sort_values(by="分鐘", ascending=True).copy()
        
                        # 2. 在顯示之前，將 moneyflow 轉為格式化字串 (只影響顯示，不影響原始資料)
                        display_alerts["moneyflow"] = display_alerts["moneyflow"].apply(lambda x: f"{x:.1f}")
                        
                        st.table(display_alerts[["時間", "馬號", "當刻賠率", "moneyflow"]], width='stretch', hide_index=True)
                # --- 執行過濾邏輯 ---
                display_df = prediction_df.copy() 
                #current_winner = prediction_df.iloc[0]['顯示名稱']
                #st.session_state.top_rank_history.append(current_winner)
                #current_top_4 = prediction_df.head(4)['顯示名稱'].tolist()
                #st.session_state.top_4_history.extend(current_top_4)
                
                #display_df = prediction_df.copy()
                #display_df = display_df[['馬名','騎師','馬齡','Odds', 'MoneyFlow', 'TotalFormScore', 'TotalScore']]
                #display_df.columns = ['馬名','騎師','馬齡','當前賠率', '近期資金流(K)', '近績評分', '🔥綜合推薦分']
                display_df = display_df[['馬名','馬齡','騎師','排位','練馬師','Odds', 'MoneyFlow', 'OverallMoneyFlow']]
                                         #, 'TotalScore']]
                display_df.columns = ['馬名','馬齡','騎師','排位','練馬師','當前賠率', '近期資金流', '總資金流']
                                      #, '🔥綜合推薦分']
                display_df['當前賠率'] = display_df['當前賠率'].apply(lambda x: f"{x:.1f}")
                display_df['近期資金流'] = display_df['近期資金流'].apply(lambda x: f"{x:.1f}k")
                display_df['總資金流'] = display_df['總資金流'].apply(lambda x: f"{x:.1f}k")
                #display_df['🔥綜合推薦分'] = display_df['🔥綜合推薦分'].astype(int)
                                

                st.markdown("""
                    <style>
                    /* 強制所有表格的數據內容 (td) 不准換行 */
                    .stTable td {
                        white-space: nowrap !important;
                        vertical-align: middle;
                    }
                    /* 允許標題 (th) 換行，並縮小字體以騰出空間 */
                    .stTable th {
                        white-space: normal !important;
                        min-width: 60px; /* 給標題一個最小寬度，迫使它太擠時自動換行 */
                        font-size: 14px !important;
                        line-height: 1.1;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                 
                st.table(display_df.style.hide(axis='index'))   

                # 應用高亮函數
                #st.table(display_df.style.apply(highlight_top_realtime, axis=1).hide(axis='index'))                
                #if len(st.session_state.top_rank_history) > 20:
                    #st.session_state.top_rank_history.pop(0)
                #if len(st.session_state.top_4_history) > 80:
                    #st.session_state.top_4_history = st.session_state.top_4_history[4:]

                #st.markdown("### 🏆 第一名佔有率")
                #counts_1 = Counter(st.session_state.top_rank_history)
                #df_1 = pd.DataFrame({'馬名': list(counts_1.keys()), '次數': list(counts_1.values())})
                #fig1 = px.pie(df_1, values='次數', names='馬名', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                #fig1.update_traces(
                        #textposition='auto',  # 自動判斷放裡面或外面
                        #textinfo='label+percent',
                        #insidetextorientation='horizontal' # 確保裡面的文字是水平的，比較好讀)
                #st.plotly_chart(fig1, width='stretch', key=f"top1_{time_now.strftime('%H%M%S')}")

                #col1, col2 = st.columns(2) # 使用左右兩欄顯示兩個圖
                
                    
            
                #with col2:
                    #st.markdown("### 🐎 頭 4 名出現頻率")
                    #counts_4 = Counter(st.session_state.top_4_history)
                    #df_4 = pd.DataFrame({'馬名': list(counts_4.keys()), '出現次數': list(counts_4.values())})
                    # 排序讓圖表更好看
                    #df_4 = df_4.sort_values(by='出現次數', ascending=False)
                    #fig4 = px.pie(df_4, values='出現次數', names='馬名', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    #fig4.update_traces(
                        #textposition='auto',
                        #textinfo='label+percent',
                        #insidetextorientation='horizontal'
                    #)
                    #st.plotly_chart(fig4, width='stretch', key=f"top4_{time_now.strftime('&H%M%S')}")
            if show_top:
                st.markdown("### 連贏賠率排名")
                visualizer.print_top(top_list,time_delay)
                
            if show_henery:
                visualizer.print_henery_model(1.18,race_no)
            time.sleep(time_delay)
        


else:
    # 4. 賽前預測模式 (靜態)
    st.markdown("### 🔍 賽前靜態預測分析")
    st.info("由於缺乏實時賠率和資金流數據，本分析完全基於馬匹、騎師和場地等靜態資訊。")

    # 執行靜態預測
    static_prediction_df = calculate_smart_score_static(race_no)
    if not static_prediction_df.empty:
        # 整理顯示格式
        display_df = static_prediction_df.copy()
        display_df = display_df[['馬名','馬齡','騎師','排位','練馬師', 'FormScore', 'JockeyScore', 'TrainerScore', 
                   'DrawScore', 'RatingDiffScore', 'TotalScore']]
        display_df.columns = ['馬名','馬齡','騎師','排位','練馬師','近績狀態分','騎師分','練馬師分', '檔位優勢分', '評分負擔分', '🏆 靜態預測分']

        # 格式化
        display_df['近績狀態分'] = display_df['近績狀態分'].astype(int)
        display_df['騎師分'] = display_df['騎師分'].astype(int)
        display_df['練馬師分'] = display_df['練馬師分'].astype(int)
        display_df['檔位優勢分'] = display_df['檔位優勢分'].astype(int)
        display_df['評分負擔分'] = display_df['評分負擔分'].astype(int)
        display_df['🏆 靜態預測分'] = display_df['🏆 靜態預測分'].apply(lambda x: f"{x:.1f}")


        st.dataframe(display_df, width='stretch')
