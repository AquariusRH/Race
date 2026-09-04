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
# ==================== 3. 繪圖函數 (簡化版) ====================
def print_bar_chart(time_now):
  post_time = st.session_state.post_time_dict[race_no]
  #st.write(post_time)
  #st.write(time_now)  
  time_25_minutes_before = np.datetime64((post_time - timedelta(minutes=25)).replace(tzinfo=None) )
  time_5_minutes_before = np.datetime64((post_time - timedelta(minutes=5)).replace(tzinfo=None))
  
  for method in print_list:
      odds_list = pd.DataFrame()
      df = pd.DataFrame()
      if method == 'overall':
          df = st.session_state.overall_investment_dict[method]
          change_data = st.session_state.diff_dict[method].iloc[-1]
      elif method == 'WIN&QIN':
          df = st.session_state.overall_investment_dict['WIN'] + st.session_state.overall_investment_dict['QIN']
          change_data_1 = st.session_state.diff_dict['WIN'].tail(30).sum(axis = 0) 
          change_data_2 = st.session_state.diff_dict['QIN'].tail(30).sum(axis = 0)
          odds_list = st.session_state.odds_dict['WIN']
      elif method == 'PLA&QPL':
          df = st.session_state.overall_investment_dict['PLA'] + st.session_state.overall_investment_dict['QPL']
          change_data_1 = st.session_state.diff_dict['PLA'].tail(30).sum(axis=0)
          change_data_2 = st.session_state.diff_dict['QPL'].tail(30).sum(axis=0)
          odds_list = st.session_state.odds_dict['PLA']
      elif method in methodlist:
          df = st.session_state.overall_investment_dict[method]
          change_data_1 = st.session_state.diff_dict[method].tail(30).sum(axis = 0)
          change_data_2 = pd.Series(0, index=df.columns)
          odds_list = st.session_state.odds_dict[method]
      if df.empty:
        continue
      fig, ax1 = plt.subplots(figsize=(12, 6))
      df.index = pd.to_datetime(df.index)
      df_1st = pd.DataFrame()
      df_1st_2nd = pd.DataFrame()
      df_2nd = pd.DataFrame()
      #df_3rd = pd.DataFrame()
      df_1st = df[df.index< time_25_minutes_before].tail(1)
      df_1st_2nd = df[df.index >= time_25_minutes_before].head(1)
      df_2nd = df[df.index >= time_25_minutes_before].tail(1)
      df_3rd = df[df.index>= time_5_minutes_before].tail(1)
       
      change_df_1 = pd.DataFrame([change_data_1.apply(lambda x: x*1 if x > 0 else x*1)],columns=change_data_1.index,index =[df.index[-1]])
      change_df_2 = pd.DataFrame([change_data_2.apply(lambda x: x*1 if x > 0 else x*1)],columns=change_data_2.index,index =[df.index[-1]])

      if method in ['WIN', 'PLA', 'WIN&QIN','PLA&QPL']:
        odds_list.index = pd.to_datetime(odds_list.index)
        odds_1st = odds_list[odds_list.index< time_25_minutes_before].tail(1)
        odds_2nd = odds_list[odds_list.index >= time_25_minutes_before].tail(1)
        #odds_3rd = odds_list[odds_list.index>= time_5_minutes_before].tail(1)

      bars_1st = None
      bars_2nd = None
      #bars_3rd = None
      # Initialize data_df
      if not df_1st.empty:
          data_df = df_1st
          data_df = data_df._append(df_2nd)
      elif not df_1st_2nd.empty:
          data_df = df_1st_2nd
          if not df_2nd.empty and not df_2nd.equals(df_1st_2nd):  # Avoid appending identical df_2nd
              data_df = data_df._append(df_2nd)
      else:
          data_df = pd.DataFrame()  # Fallback if both are empty
      #final_data_df = data_df._append(df_3rd)
      final_data_df = data_df
      sorted_final_data_df = final_data_df.sort_values(by=final_data_df.index[0], axis=1, ascending=False)
      diff = sorted_final_data_df.diff().dropna()
      diff[diff < 0] = 0
      X = sorted_final_data_df.columns
      X_axis = np.arange(len(X))
      sorted_change_1 = change_df_1[X]
      sorted_change_2 = change_df_2[X]
      if df_3rd.empty:
                  bar_colour = 'blue'
      else:
                  bar_colour = 'red'
      if not df_1st.empty:
          if df_2nd.empty:
                bars_1st = ax1.bar(X_axis, sorted_final_data_df.iloc[0], 0.4, label='投注額', color='pink')
          else:
                bars_2nd = ax1.bar(X_axis - 0.2, sorted_final_data_df.iloc[1], 0.4, label='25分鐘', color=bar_colour)
                bar = ax1.bar(X_axis+0.2,sorted_change_1.iloc[0],0.4,label='WIN/PLA改變',color='grey')
                if not sorted_change_2.empty:
                    bar = ax1.bar(X_axis+0.2,sorted_change_2.iloc[0].clip(lower=0),0.4,label='QIN/QPL改變',color='green',bottom = sorted_change_1.iloc[0].clip(lower=0))
                    bar = ax1.bar(X_axis+0.2,sorted_change_2.iloc[0].clip(upper=0),0.4,color='green',bottom = sorted_change_1.iloc[0].clip(upper=0))
                    
                #if not df_3rd.empty:
                    #bars_3rd = ax1.bar(X_axis, diff.iloc[0], 0.3, label='5分鐘', color='red')
      else:
            if df_2nd.equals(df_1st_2nd):
              bars_2nd = ax1.bar(X_axis - 0.2, sorted_final_data_df.iloc[0], 0.4, label='25分鐘', color=bar_colour)
            else:
                bars_2nd = ax1.bar(X_axis - 0.2, sorted_final_data_df.iloc[1], 0.4, label='25分鐘', color=bar_colour)
                bar = ax1.bar(X_axis+0.2,sorted_change_1.iloc[0],0.4,label='WIN/PLA改變',color='grey')
                if not sorted_change_2.empty:
                    bar = ax1.bar(X_axis+0.2,sorted_change_2.iloc[0].clip(lower=0),0.4,label='QIN/QPL改變',color='green',bottom = sorted_change_1.iloc[0].clip(lower=0))
                    bar = ax1.bar(X_axis+0.2,sorted_change_2.iloc[0].clip(upper=0),0.4,color='green',bottom = sorted_change_1.iloc[0].clip(upper=0))
                #if not df_3rd.empty:
                    #bars_3rd = ax1.bar(X_axis, diff.iloc[0], 0.3, label='5分鐘', color='red')
            #else:
                #bars_3rd = ax1.bar(X_axis-0.2, sorted_final_data_df.iloc[0], 0.4, label='5分鐘', color='red')
                #bar = ax1.bar(X_axis+0.2,sorted_change_df.iloc[0],0.4,label='改變',color='grey')

      # Add numbers above bars
      if method in ['WIN', 'PLA','WIN&QIN','PLA&QPL']:
        if bars_2nd is not None:
          sorted_odds_list_2nd = odds_2nd[X].iloc[0]
          for bar, odds in zip(bars_2nd, sorted_odds_list_2nd):
              yval = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
        #if bars_3rd is not None:
          #sorted_odds_list_3rd = odds_3rd[X].iloc[0]
          #for bar, odds in zip(bars_3rd, sorted_odds_list_3rd):
               # yval = bar.get_height()
                #ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
        elif bars_1st is not None:
          sorted_odds_list_1st = odds_1st[X].iloc[0]
          for bar, odds in zip(bars_1st, sorted_odds_list_1st):
              yval = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
      namelist_raw = st.session_state.race_dataframes[race_no]['馬名']
      namelist_sort = [str(i) + '. ' + str(namelist_raw.iloc[i - 1]) for i in X]
      formatted_namelist = [label.split('.')[0] + '.' + '\n'.join(label.split('.')[1]) for label in namelist_sort]
      
      plt.xticks(X_axis, formatted_namelist, fontsize=16)
      ax1.grid(color='lightgrey', axis='y', linestyle='--')
      ax1.set_ylabel('投注額',fontsize=15)
      ax1.tick_params(axis='y')
      fig.legend()
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
                else:
                    minutes = int(seconds_left // 60)
                    time_str = f"離開跑 {minutes} 分"  
      if method == 'overall':
          plt.title('綜合', fontsize=15)
      elif method == 'QIN':
          plt.title('連贏', fontsize=15)
      elif method == 'QPL':
          plt.title('位置Q', fontsize=15)
      elif method == 'WIN':
          plt.title('獨贏', fontsize=15)
      elif method == 'PLA':
          plt.title('位置', fontsize=15)
      elif method == 'WIN&QIN':
          plt.title(f'獨贏及連贏 | {time_str}', fontsize=15)
      elif method == 'PLA&QPL':
          plt.title(f'位置及位置Q | {time_str}', fontsize=15)          
      st.pyplot(fig)
def print_bubble(race_no, print_list):
    # 確保有數據
    if 'WIN' not in st.session_state.overall_investment_dict or st.session_state.overall_investment_dict['WIN'].empty:
        return

    for method in print_list:
        if method not in ['WIN&QIN', 'PLA&QPL']: continue
        
        try:
            if method == 'WIN&QIN':
                vol_win = st.session_state.overall_investment_dict.get('WIN', pd.DataFrame())
                vol_qin = st.session_state.overall_investment_dict.get('QIN', pd.DataFrame())
                diff_win = st.session_state.diff_dict.get('WIN', pd.DataFrame())
                diff_qin = st.session_state.diff_dict.get('QIN', pd.DataFrame())
                method_name = ['WIN','QIN']
            else:
                vol_win = st.session_state.overall_investment_dict.get('PLA', pd.DataFrame())
                vol_qin = st.session_state.overall_investment_dict.get('QPL', pd.DataFrame())
                diff_win = st.session_state.diff_dict.get('PLA', pd.DataFrame())
                diff_qin = st.session_state.diff_dict.get('QPL', pd.DataFrame())
                method_name = ['PLA','QPL']

            if vol_win.empty or vol_qin.empty or diff_win.empty or diff_qin.empty:
                continue

            total_volume = vol_win.tail(1) + vol_qin.tail(1)
            # Sum last 10 periods for delta
            delta_I = diff_win.tail(10).sum(axis=0) * 10
            delta_Q = diff_qin.tail(10).sum(axis=0) * 10
            
            df = pd.DataFrame({
                'horse': total_volume.columns.astype(str),
                'ΔI': delta_I.values,
                'ΔQ': delta_Q.values,
                '總投注量': total_volume.iloc[0].fillna(0).round(0).astype(int).values
            })
            
            df = df[df['總投注量'] > 0] # Filter out scratched
            if df.empty: continue

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
                else:
                    minutes = int(seconds_left // 60)
                    time_str = f"離開跑 {minutes} 分"
            # Normalization for bubble size
            raw_size = df['總投注量']
            bubble_size = 20 + (raw_size - raw_size.min()) / (raw_size.max() - raw_size.min() + 1e-6) * 80
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['ΔI'], y=df['ΔQ'],
                mode='markers+text',
                text=df['horse'],
                textposition="middle center",
                textfont=dict(color="white", size=22, weight="bold"),
                marker=dict(
                    size=bubble_size,
                    sizemode='area',
                    sizeref=2.*bubble_size.max()/(60**2),
                    color=df['ΔI'],
                    colorscale='Bluered_r',
                    reversescale=True,
                    line=dict(width=1, color='white'),
                    opacity=0.8
                ),
                hovertemplate="<b>馬號：%{text}</b><br>總量：%{customdata:,}K<br>Δ%{yaxis.title.text}: %{y:.1f}K<br>Δ%{xaxis.title.text}: %{x:.1f}K",
                customdata=df['總投注量']
            ))

            fig.add_hline(y=0, line_color="lightgrey")
            fig.add_vline(x=0, line_color="lightgrey")
            fig.update_layout(
                title=f"{method} 氣泡圖 (第{race_no}場) | {time_str}",
                xaxis_title=method_name[0],
                yaxis_title=method_name[1],
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                dragmode=False
            )
            st.plotly_chart(fig, width='stretch')
            
        except Exception as e:
            st.error(f"Bubble Chart Error: {e}")
def top(method_odds_df, method_investment_df, method,time_delay):
    result = {
        "main_table": None,
        "plus_table": None,
        "plus_df": None,
        "notice_table": None
    }
    one_min_no = int (60 / time_delay + 1) 
    third_min_no = int ((one_min_no - 1) * 3 + 1)
    # Extract the first row from odds DataFrame
    first_row_odds = method_odds_df.iloc[0]
    first_row_odds_df = first_row_odds.to_frame(name='Odds').reset_index()
    first_row_odds_df.columns = ['Combination', 'Odds']

    # Extract the last row from odds DataFrame
    last_row_odds = method_odds_df.iloc[-1]
    last_row_odds_df = last_row_odds.to_frame(name='Odds').reset_index()
    last_row_odds_df.columns = ['Combination', 'Odds']
    third_last_row_index = max(-len(method_odds_df), -third_min_no)
    third_last_row_odds = method_odds_df.iloc[third_last_row_index]
    third_last_row_odds_df = third_last_row_odds.to_frame(name='Odds').reset_index()
    third_last_row_odds_df.columns = ['Combination', 'Odds']
    # Extract the second last row from odds DataFrame (or the closest available row)
    second_last_row_index = max(-len(method_odds_df), -one_min_no)
    second_last_row_odds = method_odds_df.iloc[second_last_row_index]
    second_last_row_odds_df = second_last_row_odds.to_frame(name='Odds').reset_index()
    second_last_row_odds_df.columns = ['Combination', 'Odds']

    # Calculate the initial rank and initial odds
    first_row_odds_df['Initial_Rank'] = first_row_odds_df['Odds'].rank(method='min').astype(int)
    first_row_odds_df['Initial_Odds'] = first_row_odds_df['Odds']

    # Calculate the current rank and current odds
    last_row_odds_df['Current_Rank'] = last_row_odds_df['Odds'].rank(method='min').astype(int)
    last_row_odds_df['Initial_Rank'] = first_row_odds_df['Initial_Rank'].values
    last_row_odds_df['Initial_Odds'] = first_row_odds_df['Initial_Odds'].values

    # Calculate the previous rank using the second last row
    second_last_row_odds_df['Previous_Rank'] = second_last_row_odds_df['Odds'].rank(method='min').astype(int)
    last_row_odds_df['Previous_Rank'] = second_last_row_odds_df['Previous_Rank'].values

    # Calculate the change of rank
    last_row_odds_df['Change_of_Rank'] = last_row_odds_df['Initial_Rank'] - last_row_odds_df['Current_Rank']
    last_row_odds_df['Change_of_Rank'] = last_row_odds_df['Change_of_Rank'].apply(lambda x: f'+{x}' if x > 0 else (str(x) if x < 0 else '0'))

    # Combine the initial rank and change of rank into the same column format like 10 (+1)
    last_row_odds_df['Initial_Rank'] = last_row_odds_df.apply(lambda row: f"{row['Initial_Rank']}" f"({row['Change_of_Rank']})", axis=1)

    # Calculate the difference between the current rank and previous rank and add this difference to the previous rank in the format 10 (+1)
    last_row_odds_df['Change_of_Previous_Rank'] = last_row_odds_df['Previous_Rank'] - last_row_odds_df['Current_Rank']
    last_row_odds_df['Change_of_Previous_Rank'] = last_row_odds_df['Change_of_Previous_Rank'].apply(lambda x: f'+{x}' if x > 0 else (str(x) if x < 0 else '0'))
    last_row_odds_df['Previous_Rank'] = last_row_odds_df.apply(lambda row: f"{row['Previous_Rank']}" f"({row['Change_of_Previous_Rank']})", axis=1)

    # Rearrange the columns as requested
    final_df = last_row_odds_df[['Combination', 'Odds', 'Initial_Odds', 'Current_Rank', 'Initial_Rank', 'Previous_Rank']]

    # Format the odds to one decimal place using .loc to avoid SettingWithCopyWarning
    final_df.loc[:, 'Odds'] = final_df['Odds'].round(1)
    final_df.loc[:, 'Initial_Odds'] = final_df['Initial_Odds'].round(1)

    # Extract the first row from investment DataFrame
    first_row_investment = method_investment_df.iloc[0]
    first_row_investment_df = first_row_investment.to_frame(name='Investment').reset_index()
    first_row_investment_df.columns = ['Combination', 'Investment']

    # Extract the last row from investment DataFrame
    last_row_investment = method_investment_df.iloc[-1]
    last_row_investment_df = last_row_investment.to_frame(name='Investment').reset_index()
    last_row_investment_df.columns = ['Combination', 'Investment']

    # Extract the second last row from investment DataFrame (or the closest available row)
    second_last_row_index = max(-len(method_investment_df), -one_min_no)
    second_last_row_investment = method_investment_df.iloc[second_last_row_index]
    second_last_row_investment_df = second_last_row_investment.to_frame(name='Investment').reset_index()
    second_last_row_investment_df.columns = ['Combination', 'Investment']
    third_last_row_index = max(-len(method_investment_df), -third_min_no)
    third_last_row_investment = method_investment_df.iloc[third_last_row_index]
    third_last_row_investment_df = third_last_row_investment.to_frame(name='Investment').reset_index()
    third_last_row_investment_df.columns = ['Combination', 'Investment']
    # Calculate the difference in investment before sorting
    last_row_investment_df['Investment_Change'] = last_row_investment_df['Investment'] - first_row_investment_df['Investment'].values
    last_row_investment_df['Investment_Change'] = last_row_investment_df['Investment_Change'].apply(lambda x: x if x > 0 else 0)
    second_last_row_investment_df['Previous_Investment_Change'] = last_row_investment_df['Investment'] - second_last_row_investment_df['Investment'].values
    second_last_row_investment_df['Previous_Investment_Change'] = second_last_row_investment_df['Previous_Investment_Change'].apply(lambda x: x if x > 0 else 0)
    third_last_row_investment_df['Previous_Investment_Change'] = last_row_investment_df['Investment'] - third_last_row_investment_df['Investment'].values
    third_last_row_investment_df['Previous_Investment_Change'] = third_last_row_investment_df['Previous_Investment_Change'].apply(lambda x: x if x > 0 else 0)

    # Sort the final DataFrame by odds value
    final_df = final_df.sort_values(by='Odds')

    # Combine the investment data with the final DataFrame based on the combination
    final_df = final_df.merge(last_row_investment_df[['Combination', 'Investment_Change', 'Investment']], on='Combination', how='left')
    final_df = final_df.merge(second_last_row_investment_df[['Combination', 'Previous_Investment_Change']], on='Combination', how='left')
    final_df = final_df.merge(third_last_row_investment_df[['Combination', 'Previous_Investment_Change']], on='Combination', how='left')

    if method in ['WIN','PLA']:
        final_df.columns = ['馬匹', '賠率', '最初賠率', '排名', '最初排名', '上一次排名', '投注變化', '投注', '一分鐘投注','三分鐘投注']
        target_df = final_df
        rows_with_plus = target_df[
              target_df['最初排名'].astype(str).str.contains(r'\+') |
              target_df['上一次排名'].astype(str).str.contains(r'\+')
        ][['馬匹', '賠率', '最初排名', '上一次排名']]
          # Apply the conditional formatting to the 初始排名 and 前一排名 columns and add a bar to the 投資變化 column
        styled_df = final_df.style.format({
            '賠率': '{:.1f}',
            '最初賠率': '{:.1f}',
            '投注變化': '{:.2f}k',
            '投注': '{:.2f}k',
            '一分鐘投注': '{:.2f}k',
            '三分鐘投注': '{:.2f}k'
          }).map(highlight_change, subset=['最初排名', '上一次排名']).bar(subset=['投注變化', '一分鐘投注','三分鐘投注'], color='rgba(173, 216, 230, 0.5)').hide(axis='index')
        styled_rows_with_plus = rows_with_plus.style.format({'賠率': '{:.1f}'}).map(highlight_change, subset=['最初排名', '上一次排名']).hide(axis='index')
          # Display the styled DataFrame
        result["main_table"] = styled_df
        result["plus_table"] = styled_rows_with_plus 
        result["plus_df"] = target_df
      #st.write(styled_df.to_html(), unsafe_allow_html=True)
      #st.write(styled_rows_with_plus.to_html(), unsafe_allow_html=True)


    else:
        final_df.columns = ['組合', '賠率', '最初賠率', '排名', '最初排名', '上一次排名', '投注變化', '投注', '一分鐘投注','三分鐘投注']
        target_df = final_df.head(15)
        target_special_df = final_df.head(50)
        rows_with_plus = target_special_df[
              target_special_df['最初排名'].astype(str).str.contains(r'\+') |
              target_special_df['上一次排名'].astype(str).str.contains(r'\+')
        ][['組合', '賠率', '最初排名', '上一次排名', '一分鐘投注','三分鐘投注']]
        
    
          # Apply the conditional formatting to the 初始排名 and 前一排名 columns and add a bar to the 投資變化 column
        styled_df = target_df.style.format({
            '賠率': '{:.1f}',
            '最初賠率': '{:.1f}',
            '投注變化': '{:.2f}k',
            '投注': '{:.2f}k',
            '一分鐘投注': '{:.2f}k',
            '三分鐘投注': '{:.2f}k'
        }).map(highlight_change, subset=['最初排名', '上一次排名']).bar(subset=['投注變化', '一分鐘投注','三分鐘投注'], color='rgba(173, 216, 230, 0.5)').hide(axis='index')
        styled_rows_with_plus = rows_with_plus.style.format({
            '賠率': '{:.1f}',
            '一分鐘投注': '{:.2f}k',
            '三分鐘投注': '{:.2f}k'
        }).bar(subset=['一分鐘投注', '三分鐘投注'], color='rgba(173, 216, 230, 0.5)').map(highlight_change, subset=['最初排名', '上一次排名']).hide(axis='index')
          # Display the styled DataFrame
        result["main_table"] = styled_df
        result["plus_table"] = styled_rows_with_plus  
        result["plus_df"] = final_df
      #st.write(styled_df.to_html(), unsafe_allow_html=True)
        notice_df = None  
        if method in ["QIN","QPL","FCT","TRI","FF"]:
            if method in ["QIN"]:
              notice_df = final_df[(final_df['一分鐘投注'] >= 100) | (final_df['三分鐘投注'] >= 300)][['組合', '賠率', '一分鐘投注', '三分鐘投注']]
            elif method in ["QPL"]:
              notice_df = final_df[(final_df['一分鐘投注'] >= 200) | (final_df['三分鐘投注'] >= 600)][['組合', '賠率', '一分鐘投注', '三分鐘投注']]
            elif method in ["FCT"]:
              notice_df = final_df[(final_df['一分鐘投注'] >= 10) | (final_df['三分鐘投注'] >= 30)][['組合', '賠率', '一分鐘投注', '三分鐘投注']]
            else:
              notice_df = final_df[(final_df['一分鐘投注'] >= 5) | (final_df['三分鐘投注'] >= 15)][['組合', '賠率', '一分鐘投注', '三分鐘投注']]
        if notice_df is not None:
            styled_notice_df = notice_df.style.format({'賠率': '{:.1f}','一分鐘投注': '{:.2f}k','三分鐘投注': '{:.2f}k'}).bar(subset=['一分鐘投注','三分鐘投注'], color='rgba(173, 216, 230, 0.5)').hide(axis='index')
        result["notice_table"] = styled_notice_df  

    return result
      #col1, col2 = st.columns(2)
      #with col1:
        #st.write(styled_rows_with_plus.to_html(), unsafe_allow_html=True)
      #with col2:
        #st.write(styled_notice_df.to_html(), unsafe_allow_html=True)

def print_top(top_list,time_delay):
  for method in top_list:
        tables = top(st.session_state.odds_dict[method], st.session_state.investment_dict[method], method,time_delay)
        if tables["main_table"]:
            st.write(tables["main_table"].to_html(), unsafe_allow_html=True)
        if tables["plus_table"] or tables["notice_table"]:
            col1, col2 = st.columns(2)
            with col1:
                if tables["plus_table"]:
                    st.write(tables["plus_table"].to_html(), unsafe_allow_html=True)
            with col2:
                if tables["notice_table"]:
                    st.write(tables["notice_table"].to_html(), unsafe_allow_html=True)
                    
def highlight_change(val):
    color = 'limegreen' if '+' in val else 'crimson' if '-' in val else ''
    return f'color: {color}'

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def print_plotly_advanced_bar(race_no, print_list): # 建議傳入 method 區分
    # 1. 取得對應數據 (這裡以 WIN/QIN 為例，你可以根據 method 調整)
    # 假設你的 method 分別是 'WIN&QIN' 或 'PLA&QPL'
    for method in print_list:
        # --- 1. 數據源判斷與提取 ---
        if method == 'WIN&QIN':
            df_base, df_top = st.session_state.overall_investment_dict['WIN'], st.session_state.overall_investment_dict['QIN']
            diff_base, diff_top = st.session_state.diff_dict['WIN'], st.session_state.diff_dict['QIN']
            odds_df = st.session_state.odds_dict['WIN']
            label_base, label_top = "WIN", "QIN"
        elif method == 'PLA&QPL':
            df_base, df_top = st.session_state.overall_investment_dict['PLA'], st.session_state.overall_investment_dict['QPL']
            diff_base, diff_top = st.session_state.diff_dict['PLA'], st.session_state.diff_dict['QPL']
            odds_df = st.session_state.odds_dict['PLA']
            label_base, label_top = "PLA", "QPL"
        elif method == 'PLA':
            df_base = st.session_state.overall_investment_dict['PLA']
            df_top = pd.DataFrame(0, index=df_base.index, columns=df_base.columns)
            diff_base = st.session_state.diff_dict['PLA']
            diff_top = pd.DataFrame(0, index=diff_base.index, columns=diff_base.columns)
            odds_df = st.session_state.odds_dict['PLA']
            label_base, label_top = "PLA", ""
    
        all_ts = df_base.index
        data_len = len(all_ts)
        if data_len < 1: return
    
        # --- 2. 準備馬名與排序 (以最新數據為準固定 X 軸) ---
        current_total = (df_base + df_top).iloc[-1]
        sorted_cols = current_total.sort_values(ascending=False).index
        namelist_raw = st.session_state.race_dataframes[race_no]['馬名']
        horse_labels = []
        for c in sorted_cols:
            name = namelist_raw.iloc[c-1]
            # 讓馬名垂直排列：每個字中間加 <br>
            vertical_name = "<br>".join(list(name))
            horse_labels.append(f"{c}.<br>{vertical_name}")
        post_time = st.session_state.post_time_dict[race_no].replace(tzinfo=None)
    
        # --- 3. 預先計算所有動畫幀 (Frames) ---
        frames = []
        for i, ts in enumerate(all_ts):
            ts_raw = ts.replace(tzinfo=None)
            time_diff = (post_time - ts_raw).total_seconds() / 60
            
            # 根據該幀的時間決定顏色
            if time_diff <= 5: 
                current_frame_color = 'rgb(255, 99, 132)'   # 紅 (5分內)
                show_diff = True
            elif time_diff <= 25: 
                current_frame_color = 'rgb(54, 162, 235)'   # 藍 (5-25分)
                show_diff = True
            else: 
                current_frame_color = 'rgb(255, 205, 210)' # 粉 (>25分)
                show_diff = False
    
            # 建立該幀的數據圖層
            frame_data = [
                go.Bar(
                    x=horse_labels, 
                    y=(df_base + df_top).iloc[i][sorted_cols], 
                    marker_color=current_frame_color, # ⬅️ 確保顏色被寫入這一幀
                    offsetgroup=1, 
                    text=odds_df.iloc[i][sorted_cols], 
                    textposition='outside', 
                    name='總投注'
                )
            ]
            
            # 25分內才顯示變動棒
            if time_diff <= 25:
                start_idx = max(0, i - 9)
                raw_c_base = diff_base.iloc[start_idx:i+1].sum(axis=0)[sorted_cols]
                raw_c_top = diff_top.iloc[start_idx:i+1].sum(axis=0)[sorted_cols]
                
                # --- 關鍵：執行放大邏輯 (正數 * 6, 負數 * 3) ---
                def amplify(val):
                    return val * 6 if val > 0 else val * 3
    
                amp_c_base = raw_c_base.apply(amplify)
                amp_c_top = raw_c_top.apply(amplify)
                frame_data.append(go.Bar(x=horse_labels, y=amp_c_base, marker_color='grey', offsetgroup=2, name=f'{label_base}變'))
                if method != 'PLA':
                    frame_data.append(go.Bar(x=horse_labels, y=amp_c_top, marker_color='green', offsetgroup=2, base=amp_c_base, name=f'{label_top}變'))
    
            frames.append(go.Frame(data=frame_data, name=ts.strftime("%H:%M:%S")))
    
            # --- 4. 配置佈局與 Plotly 滑塊 ---
            fig = go.Figure(
            data=frames[-1].data,
            layout=go.Layout(
                title=f"{method} 數據回溯",
                barmode='group',
                dragmode=False,
                # 1. 顯著增加高度 (例如從 500 改為 700 或 800)
                height=850, 
                
                # 2. 移除不必要的空白邊距，讓圖表充滿畫布
                # t (top), b (bottom), l (left), r (right)
                margin=dict(l=20, r=20, t=60, b=350), 
                
                xaxis={
                    'fixedrange': True,
                    'tickangle': 0,      # 既然馬名已經垂直處理，角度設為 0
                    'automargin': True,  # 強制自動補償標籤高度
                    'tickfont': {'size': 14}
                },
                yaxis={
                    'fixedrange': True,
                    # 確保金額不會被切掉
                    'automargin': True 
                },
                
                # 3. 圖例位置優化 (放在頂部，不佔用側面寬度)
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
    
                # 4. 滑塊配置
                sliders=[{
                    "active": data_len - 1,
                    "currentvalue": {"prefix": "時間: ", "offset": 30},
                    "pad": {"t": 180},
                    "steps": [
                        {
                            # 關鍵：redraw 設為 True，確保顏色切換能被渲染
                            "args": [[f.name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                            "label": f.name,
                            "method": "animate",
                        } for f in frames
                    ]
                }]
            ),
            frames=frames
        )
    
        # 5. 使用 use_container_width=True 讓圖表隨網頁寬度自動撐滿
        latest_ts = all_ts[-1].strftime("%H%M%S")
        st.plotly_chart(fig, width='stretch', key=f"fluent_{race_no}_{method}_{latest_ts}")
def get_rank_font_colors(series):
    """
    對應原本的 highlight_change 邏輯：
    '+' -> limegreen (綠色)
    '-' -> crimson (紅色)
    其餘 -> white (白色)
    """
    colors = []
    for val in series:
        val_str = str(val)
        if '+' in val_str:
            colors.append('limegreen')
        elif '-' in val_str:
            colors.append('crimson')
        else:
            colors.append('white') # 預設顏色
    return colors
def print_henery_model(gamma=1.18,race_no):
    """
    Henery Model 完整實作版
    解決問題：
    1. 1號馬缺失 (不再使用 iloc[1:])
    2. 雙位數馬匹 (10, 11, 12) 匹配失敗
    3. 格式相容性 (支援 "02,10", "2-10", "2.0,10.0" 等格式)
    """
    # --- 1. 時間處理與合併顯示 ---
    HK_TZ = timezone(timedelta(hours=8))
    now = datetime.now(HK_TZ)
    
    # 獲取開跑倒數
    post_time_raw = st.session_state.post_time_dict[race_no]
    if post_time_raw:
        post_time = post_time_raw.replace(tzinfo=HK_TZ) if post_time_raw.tzinfo is None else post_time_raw
        seconds_left = (post_time - now).total_seconds()
        time_str = "🏁 已開跑" if seconds_left <= 0 else f"⏳ 離開跑 {int(seconds_left // 60)} 分"
    else:
        time_str = "未載入"

    # 獲取最後更新時間
    last_upd = st.session_state.last_update.strftime('%H:%M:%S') if st.session_state.get('last_update') else "N/A"
    
    # 合併顯示在一句 Markdown 中
    st.markdown(f"#### {time_str} ｜ 📟 數據最後同步: `{last_upd}`")

    # --- 2. 數據合法性檢查 ---
    if 'odds_dict' not in st.session_state: return
    win_df = st.session_state.odds_dict.get('WIN')
    qin_df = st.session_state.odds_dict.get('QIN')
    if win_df is None or qin_df is None or len(win_df) == 0: return

    # --- 3. 處理 WIN (以整數作為馬號 Key) ---
    latest_win = win_df.iloc[-1]
    win_probs, win_odds_map = {}, {}
    inv_sum = 0
    
    for col, odds in latest_win.items():
        try:
            # 關鍵：馬號統一存成整數 2, 10
            h_num = int(float(str(col).strip()))
            val = pd.to_numeric(odds, errors='coerce')
            if val > 0 and val != np.inf and not pd.isna(val):
                win_probs[h_num] = 1.0 / val
                win_odds_map[h_num] = val
                inv_sum += 1.0 / val
        except: continue
            
    if inv_sum == 0: return
    for h in win_probs: win_probs[h] /= inv_sum

    # --- 4. 處理 QIN (最強力模糊解析) ---
    latest_qin = qin_df.iloc[-1]
    actual_qin = {}
    
    for comb_col, odds in latest_qin.items():
        val = pd.to_numeric(odds, errors='coerce')
        if val > 0 and not pd.isna(val):
            # 使用正則表達式抓取所有數字，無視 "02,10" 中的 0 或逗號
            nums = re.findall(r'\d+', str(comb_col))
            if len(nums) == 2:
                # 關鍵：轉成整數後排序，確保 (2, 10) 永遠是 (2, 10)
                n1, n2 = int(nums[0]), int(nums[1])
                key = tuple(sorted([n1, n2])) 
                actual_qin[key] = val

    # --- 5. Henery 計算 ---
    results = []
    # 按馬號大小排序
    horses = sorted(win_probs.keys())
    
    for h1, h2 in itertools.combinations(horses, 2):
        p1, p2 = win_probs[h1], win_probs[h2]
        denom1 = sum(win_probs[h]**gamma for h in horses if h != h1)
        denom2 = sum(win_probs[h]**gamma for h in horses if h != h2)
        p_qin = (p1 * (p2**gamma / denom1)) + (p2 * (p1**gamma / denom2))
        theo_odds = 1.0 / p_qin
        
        # 精確整數匹配： (2, 10)
        a_odds = actual_qin.get((h1, h2))
        if a_odds:
            val_score = a_odds / theo_odds
            results.append({
                "組合": f"{h1}-{h2}",
                #"馬1獨贏": win_odds_map[h1],
                #"馬2獨贏": win_odds_map[h2],
                "實時Q": a_odds,
                "理論Q": round(theo_odds, 1),
                "Value": round(val_score, 2)
            })

    tables = top(st.session_state.odds_dict["QIN"], st.session_state.investment_dict["QIN"], "QIN")
    plus_df = tables.get("plus_df")
    plus_df_clean = plus_df.copy()
    plus_df_clean = plus_df_clean[['組合', '排名','最初排名', '上一次排名']]
    if plus_df_clean is not None and not plus_df_clean.empty:
        # --- 關鍵步驟：格式化 plus_df 的組合名稱 ---
        # 假設 plus_df['組合'] 是 "01,02" 或 "1, 2"，統一轉成 "1-2"
        def normalize_comb(comb_str):
            nums = re.findall(r'\d+', str(comb_str))
            if len(nums) == 2:
                n1, n2 = sorted([int(nums[0]), int(nums[1])])
                return f"{n1}-{n2}"
            return comb_str
    plus_df_clean['組合'] = plus_df_clean['組合'].apply(normalize_comb)
    def get_table_html(df, cmap_name):
        return (
            df.style.background_gradient(subset=['Value'], cmap=cmap_name)
            .format({"實時Q": "{:.1f}", "理論Q": "{:.1f}", "Value": "{:.2f}"})
            .hide(axis='index').map(highlight_change, subset=['最初排名', '上一次排名'])
            # This CSS ensures headers don't wrap and the table fills the width
            .set_table_attributes('style="width:100%; border-collapse: collapse; white-space: nowrap;"')
            .to_html()
        )
      
    # --- 6. 渲染雙表格介面 ---
    if results:
        full_df = pd.DataFrame(results)
        full_df = pd.merge(full_df, plus_df_clean, on='組合', how='left')
        full_df = full_df[['組合', '排名','最初排名', '上一次排名','實時Q','理論Q','Value']]
        full_df = full_df[full_df["實時Q"] < 100]
        col1, col2 = st.columns(2)
    
        #with col1:
           # st.success("✅ **高價值組合 (Value > 1.1)**")
           # high_df = full_df[full_df["Value"] > 1.1].sort_values("實時Q", ascending=False).head(25).sort_values("Value", ascending=True)
            #if not high_df.empty:
                #st.markdown(get_table_html(high_df, 'Greens'), unsafe_allow_html=True)
            #else:
                #st.info("目前無符合條件組合")
    
        
        st.error("🔥 **過熱組合 (Value < 0.9)**")
        overheated_df = full_df[full_df["Value"] < 0.9].sort_values("實時Q", ascending=True).head(25)
        #.sort_values("Value", ascending=True)
        if not overheated_df.empty:
            st.markdown(get_table_html(overheated_df, 'Reds_r'), unsafe_allow_html=True)
        else:
            st.info("目前無過熱組合")
        # --- 7. 最終優化版：支援系統 Dark Mode + 左對齊 ---
        ov_df = full_df[full_df["Value"] < 0.9].copy()
            
        # 獲取場中所有馬號（即使沒過熱也顯示按鈕）
        all_horse_list = sorted(list(win_probs.keys()))
        num_horses = len(all_horse_list)
        fig = go.Figure()
        buttons = []

        for i, h_num in enumerate(all_horse_list):
            mask = ov_df['組合'].apply(lambda x: any(int(part) == h_num for part in x.split('-')))
            sub_df = ov_df[mask].sort_values("Value").reset_index(drop=True)

            if not sub_df.empty:
                # 🌈 同時取得背景與字體顏色
                val_bg_colors, val_font_colors = get_adaptive_colors(sub_df["Value"])
                init_font_colors = get_rank_font_colors(sub_df["最初排名"])
                prev_font_colors = get_rank_font_colors(sub_df["上一次排名"])
                fig.add_trace(
                    go.Table(
                        columnwidth = [100, 80, 80, 80, 80, 100],
                        header=dict(
                            values=["<b>組合</b>", "<b>排名</b>","<b>最初</b>", "<b>上一次</b>", "<b>實時Q</b>", "<b>理論Q</b>", "<b>Value</b>"],
                            fill_color='#111111', align='center', font=dict(color='white',size = 18),
                            line_color='#333333'
                        ),
                        cells=dict(
                            values=[sub_df["組合"],sub_df["排名"], sub_df["最初排名"], sub_df["上一次排名"], 
                                    sub_df["實時Q"], sub_df["理論Q"], sub_df["Value"]],
                            fill_color=[
                                ['rgba(30,30,30,0.5)']*len(sub_df),
                                ['rgba(30,30,30,0.5)']*len(sub_df),
                                ['rgba(30,30,30,0.5)']*len(sub_df),
                                ['rgba(30,30,30,0.5)']*len(sub_df),
                                ['rgba(30,30,30,0.5)']*len(sub_df),
                                ['rgba(30,30,30,0.5)']*len(sub_df),
                                val_bg_colors  # 背景漸層
                            ],
                            font=dict(
                                color=[
                                    ['white']*len(sub_df), # 其他欄位固定白字
                                    ['white']*len(sub_df),
                                    init_font_colors,
                                    prev_font_colors,
                                    ['white']*len(sub_df),
                                    ['white']*len(sub_df),
                                    val_font_colors        # ⬅️ Value 字體動態黑白切換
                                ],
                                size=18,
                            ),
                            align='center', line_color='#333333',height=45
                        ),
                        visible=(i == 0),
                        domain=dict(x=[0, 1.0])
                    )
                )
            else:
                # --- 無組合的提示表格 ---
                fig.add_trace(
                    go.Table(
                        header=dict(
                            values=["<b>狀態提示</b>"], 
                            fill_color='#111111', font=dict(color='white')
                        ),
                        cells=dict(
                            values=[[f"馬匹 {h_num} 目前沒有過熱組合"]], 
                            fill_color=['rgba(30,30,30,0.5)'], 
                            font=dict(color='#888888', size=20), height=60
                        ),
                        visible=(i == 0),
                        domain=dict(x=[0, 1.0])
                    )
                )

            # 按鈕列表
            buttons_per_row = 7
            row_count = (num_horses + buttons_per_row - 1) // buttons_per_row
            menu_list = []
            
            for row_idx in range(0, num_horses, buttons_per_row):
                row_horses = all_horse_list[row_idx : row_idx + buttons_per_row]
                row_buttons = []
                
                for h_btn in row_horses:
                    mask = ov_df['組合'].apply(lambda x: any(int(part) == h_btn for part in x.split('-')))
                    sub_ov = ov_df[mask]
                    count = len(ov_df[mask])
                    plus_count = 0
                    if not sub_ov.empty and '上一次排名' in sub_ov.columns:
                        plus_count = sub_ov['上一次排名'].astype(str).str.contains(r'\+').sum()
                        
                    g_idx = all_horse_list.index(h_btn)
                    
                    # 建立 visibility 陣列：只有點擊的那匹馬對應的 Trace 是 True
                    # 其餘全部（包含其他行的馬）都是 False
                    vis = [False] * num_horses
                    vis[g_idx] = True
                    
                    # 這裡我們不依賴系統的 active 顏色
                    row_buttons.append(dict(
                        label=f" {h_btn}號</b><br> ({count}) (+{plus_count})",
                        method="update",
                        # 當點擊時，我們更新 Trace 的可見性，並可以順便更新 Layout 標題作為提示
                        args=[{"visible": vis}, {"title": f"<b>正在檢視：{h_btn} 號馬過熱組合</b>"}]
                    ))
                current_row_from_bottom = row_count - 1 - (row_idx // buttons_per_row)
                menu_list.append(dict(
                    type="buttons",
                    direction="right",
                    x=0, 
                    xanchor="left",
                    yanchor="bottom",
                    # ⬇️ 這裡改為 1.01，按鈕就會直接坐在表格頂線上
                    y=1.01 + (current_row_from_bottom * 0.08), 
                    buttons=row_buttons,
                    showactive=False,
                    bgcolor="#333333",
                    font=dict(color="white", size=15),
                    bordercolor="#555555",
                    borderwidth=1,
                    pad={"r": 8, "t": 2, "b": 0} 
                ))
    
            # --- 2. 修正 Layout (壓縮頂部空間讓表格上移) ---
            fig.update_layout(
                dragmode=False,
                updatemenus=menu_list,
                # ⬇️ 關鍵：t 不能太小（否則按鈕會出界），但也不能太大（否則表格會下沉）
                # 建議設為 30 + (行數 * 35)，這樣能確保按鈕剛好頂到最上方，表格跟著上移
                margin=dict(t=30 + (row_count * 35), b=10, l=0, r=0), 
                height=650,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white", family="Arial")
            )

        st.plotly_chart(
            fig, 
            width='stretch', 
            key=f"dark_left_table_{race_no}_{time_now.strftime('%H%M%S')}", 
            config={'displayModeBar': False}
        )
        
        # --- 8. 新增：全寬熱力圖趨勢 ---
        st.markdown("---") # 分割線
        st.subheader("🔥 歷史熱度掃描 (Heatmap)")
        if win_df is not None:
            # 排除非馬號的 column (如果有)，並排序
            latest_win_series = win_df.iloc[-1]
            current_horses = sorted([c for c in win_df.columns if str(c).isdigit()], key=lambda x: int(x))
            full_horse_list = sorted(current_horses, key=lambda h: pd.to_numeric(latest_win_series.get(h, 999), errors='coerce'))
            full_horse_list = [str(h) for h in full_horse_list]
            sync_time = win_df.index[-1]
        else:
            full_horse_list = [str(h) for h in sorted(win_probs.keys())]
        # 確保 session_state 存在
        if 'horse_count_history' not in st.session_state:
            st.session_state.horse_count_history = {}
       
        y_labels_filtered = []
        
        # 這裡放入前面討論的數據採集與繪圖代碼
        current_time = datetime.now(HK_TZ).strftime('%H:%M:%S')
        current_horse_counts = {str(h): 0 for h in all_horse_list}
        
        for h_num in all_horse_list:
            mask = ov_df['組合'].apply(lambda x: any(int(part) == h_num for part in x.split('-')))
            current_horse_counts[str(h_num)] = len(ov_df[mask])
    
        if race_no not in st.session_state.horse_count_history:
            st.session_state.horse_count_history[race_no] = pd.DataFrame()
    
        hist_df = st.session_state.horse_count_history[race_no]
        new_entry = pd.DataFrame([current_horse_counts], index=[sync_time])
        
        if hist_df.empty or current_time != hist_df.index[-1]:
            updated_hist = pd.concat([hist_df, new_entry]).tail(40)
            st.session_state.horse_count_history[race_no] = updated_hist
    
        # 渲染圖表
        plot_data = st.session_state.horse_count_history[race_no]
        if not plot_data.empty:
            # 只顯示有過熱記錄的馬，避免 14 匹馬太多空白
            active_cols = [c for c in plot_data.columns if plot_data[c].iloc[-1] >2]
            
            if active_cols:
                active_cols = [h for h in full_horse_list if h in active_cols]
                z_df = plot_data[active_cols].T.iloc[::-1] # 轉置讓 Y 軸是馬號
                # 3. 從 win_df 抽取對應的賠率矩陣 (Text 軸)
                # 確保 win_df 的 columns 與 active_cols 格式一致 (處理 int/str 差異)
                # win_col_keys = [int(c) if int(c) in win_df.columns else str(c) for c in active_cols]
                # 直接抽取這幾匹馬的所有歷史賠率，並對齊熱力圖的時間點 (z_df.columns)
                # reindex 會自動處理時間對齊，若 win_df 漏了某秒會補 NaN
                # odds_sub_df = win_df[win_col_keys].reindex(z_df.columns).T.iloc[::-1]
                # 將 NaN 轉為 0 方便顯示，並轉為 values 給 Plotly
                # raw_matrix = odds_sub_df.fillna(0).values
                # clean_text_matrix = []
                # for row in raw_matrix:
                    # new_row = []
                    # last_val = None
                    # for i, val in enumerate(row):
                        # 邏輯：如果是第一格，或者數值跟上一格不同，就顯示數字
                        # if i == 0 or val != last_val:
                            # new_row.append(f"{val:.1f}")
                        # else:
                            # 數值相同則留空，減少視覺壓力
                            # new_row.append("")
                        # last_val = val
                    # clean_text_matrix.append(new_row)
                    
                y_labels_filtered = []
                latest_win = win_df.iloc[-1] if win_df is not None else None
                prev_win = (win_df.iloc[-4] if len(win_df) >= 4 else win_df.iloc[0]) if win_df is not None else None
                prev_3_win = (win_df.iloc[-10] if len(win_df) >= 10 else win_df.iloc[0]) if win_df is not None else None
                for h_str in active_cols:
                    col_key = int(h_str) if win_df is not None and int(h_str) in win_df.columns else h_str
                    
                    if latest_win is not None and col_key in latest_win:
                        curr_o = pd.to_numeric(latest_win[col_key], errors='coerce')
                        prev_o = pd.to_numeric(prev_win[col_key], errors='coerce')
                        prev_3_o = pd.to_numeric(prev_3_win[col_key], errors='coerce')
                        #diff =  prev_o - curr_o
                        #arrow = "▼" if diff < 0 else "▲" if diff > 0 else ""
                        #diff_color = "#00ff00" if diff > 0 else "#ff4b4b" if diff < 0 else "#888"
                        
                        label = (
                            f"<b>{int(h_str):02d} 號</b> <span>{curr_o:.1f}</span> <br>"
                            f"<span style='color:#888; font-size:20px'>({prev_o:.1f})</span> <span style='color:#888; font-size:20px'>(({prev_3_o:.1f}))</span></b>"
                            #f"<span style='color:{diff_color}; font-size:14px'><b>{arrow} {abs(diff):.1f}</b></span>"
                        )#style='color:#fff'
                    else:
                        label = f"<b>{int(h_str):02d} 號</b><br>-" #<br>-"
                    y_labels_filtered.append(label)
                y_labels_rich = y_labels_filtered[::-1]
                fixed_zmin = 2
                #fixed_zmax = z_df.values.max()
                colorscale_thresholds = [
                    [0, '#FFFFFF'],       # 0: 純白 (背景)
                    [0.1, '#FFEEEE'],     # 1: 極淡粉紅
                    [0.2, '#FFFF99'],     # 2: 淺黃
                    [0.4, '#FFFF00'],     # 3-4: 亮黃
                    [0.6, '#FF9999'],     # 5-6: 淺紅
                    [0.8, '#FF0000'],     # 7-9: 正紅
                    [1.0, '#330066']      # 10+: 深紫 (焦點)
                ]
                fig_heat = go.Figure(data=go.Heatmap(
                    z=z_df.values,
                    x=z_df.columns,
                    y=y_labels_rich,
                    # text=clean_text_matrix,
                    # texttemplate="%{text:.1f}",
                    # textfont={"size": 20},
                    ygap=2.5,
                    zmin=fixed_zmin,      
                    #zmax=fixed_zmax,
                    colorscale=colorscale_thresholds, # 深黑到鮮紅
                    showscale=True,
                    zauto=False,
                    colorbar=dict(title="過熱數")
                ))
                dynamic_height = 150 + (len(full_horse_list) * 25)
                fig_heat.update_layout(
                    height=dynamic_height, # 動態高度
                    width = 1500,
                    margin=dict(t=10, b=10, l=100, r=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    dragmode=False,
                    font=dict(color="white"),
                    xaxis=dict(showticklabels=False, showgrid=False,zeroline=False, fixedrange=True),
                    #xaxis=dict(showgrid=False, tickangle=-45,fixedrange=True),
                    yaxis=dict(showgrid=False, title="馬號",fixedrange=True,tickfont=dict(size=20))
                )
                st.plotly_chart(fig_heat, width='content')
        
        return full_df # 最後回傳完整 DataFrame
    
    return pd.DataFrame()
    
def get_adaptive_colors(values, cmap_name='Reds_r'):
    """
    回傳背景色列表與對應的字體顏色列表 (黑或白)
    """
    if len(values) == 0: return [], []
    
    cmap = plt.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=0.2, vmax=1.0) 
    
    bg_colors = []
    font_colors = []
    
    for v in values:
        # 1. 取得背景 RGBA
        rgba = cmap(norm(v))
        bg_hex = mcolors.to_hex(rgba)
        bg_colors.append(bg_hex)
        
        # 2. 計算亮度 (Luminance) 演算法
        # 公式: 0.299*R + 0.587*G + 0.114*B
        r, g, b, _ = rgba
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        
        # 3. 根據亮度決定字體顏色 (閾值通常設為 0.5)
        font_colors.append('white' if luminance < 0.5 else '#31333F')
        
    return bg_colors, font_colors
    
def plot_racing_monitor_dashboard():
    """
    整合賠率與投注量監控，併排顯示兩張獨立圖表
    """
    # 1. 檢查數據來源
    if 'odds_dict' not in st.session_state or 'overall_investment_dict' not in st.session_state:
        st.warning("數據加載中，請稍候...")
        return

    # 取得數據
    df_odds = st.session_state.odds_dict.get('WIN', pd.DataFrame())
    inv_dict = st.session_state.overall_investment_dict
    
    if df_odds.empty:
        st.info("暫無賠率數據")
        return

    # ---------------------------------------------------------
    # 2. 核心排序邏輯 (兩圖統一按賠率排序)
    # ---------------------------------------------------------
    latest_odds = df_odds.iloc[-1].sort_values()
    sorted_horses = latest_odds.index.tolist()
    top_6_horses = sorted_horses[:6]
    
    # 統一顏色序列
    colors = px.colors.qualitative.Dark24
    def get_horse_color(horse_name):
        # 根據馬號固定顏色，避免排名變動時顏色亂跳
        try:
            return colors[int(horse_name) % len(colors)]
        except:
            return "#FFFFFF"

    # ---------------------------------------------------------
    # 3. 繪製賠率圖 (Odds Chart)
    # ---------------------------------------------------------
    fig_odds = go.Figure()
    for horse in sorted_horses:
        is_top_6 = horse in top_6_horses
        fig_odds.add_trace(go.Scatter(
            x=df_odds.index, y=df_odds[horse],
            name=f"{horse} 號",
            mode='lines+markers',
            marker=dict(size=4),
            visible=True if is_top_6 else "legendonly",
            line=dict(width=3 if is_top_6 else 2, color=get_horse_color(horse)),
            hovertemplate=f"馬號 {horse}<br>賠率: %{{y:.1f}}<extra></extra>"
        ))

    fig_odds.update_layout(
        title="📉 獨贏賠率 (熱門在上)",
        template="plotly_dark",
        yaxis=dict(type='log',  tickformat=".1f", dtick=0.301, gridcolor='rgba(255,255,255,0.1)'), #autorange='reversed',
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        dragmode=False, hovermode="x unified",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", traceorder="normal"),
        height=600, margin=dict(t=80, b=50, l=60, r=20)
    )

    # ---------------------------------------------------------
    # 4. 繪製金額圖 (Investment Chart)
    # ---------------------------------------------------------
    # 合併 WIN 與 QIN 投注額 (假設馬號是相同的 Index)
    df_win_inv = pd.DataFrame(inv_dict.get("WIN", {}))
    df_qin_inv = pd.DataFrame(inv_dict.get("QIN", {}))
    # 這裡假設你是想加總同一隻馬在不同池的表現，或者是對比
    df_total_inv = df_win_inv.add(df_qin_inv, fill_value=0) if not df_win_inv.empty else df_qin_inv

    fig_inv = go.Figure()
    # 保持與賠率圖「完全相同」的馬匹順序添加 Trace，讓 Legend 對齊
    for horse in sorted_horses:
        if horse not in df_total_inv.columns: continue
        is_top_6 = horse in top_6_horses
        
        fig_inv.add_trace(go.Scatter(
            x=df_total_inv.index, y=df_total_inv[horse],
            name=f"{horse} 號",
            mode='lines+markers',
            marker=dict(size=4),
            visible=True if is_top_6 else "legendonly",
            line=dict(width=3 if is_top_6 else 1.5, color=get_horse_color(horse)),
            hovertemplate=f"馬號 {horse}<br>金額: %{{y:,.0f}}<extra></extra>"
        ))

    fig_inv.update_layout(
        title="💰 投注量走勢 (對齊賠率排序)",
        template="plotly_dark",
        yaxis=dict(side='right', tickformat=",.0f", gridcolor='rgba(255,255,255,0.1)'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        dragmode=False, hovermode="x unified",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", traceorder="normal"),
        height=600, margin=dict(t=80, b=50, l=20, r=60)
    )

    # ---------------------------------------------------------
    # 5. Streamlit Layout 併排顯示
    # ---------------------------------------------------------
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_odds, width='content', config={'displayModeBar': False})
    #with c2:
        #st.plotly_chart(fig_inv, width='stretch', config={'displayModeBar': False})
