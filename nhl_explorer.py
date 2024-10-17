import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

file_path = 'stats.json'
df = pd.read_json(file_path, lines=True)

df['game_date'] = pd.to_datetime(df['game_date'], unit='ms')

st.set_page_config(layout="wide")

st.title('NHL Data Explorer')

filter_col, table_col, visual_col = st.columns([1, 1, 2])

with filter_col:
    st.header('Filter Options')
    selected_team = st.selectbox('Select Team', ['All'] + df['team_name'].unique().tolist())
    selected_metric = st.selectbox('Select Metric', ['goals', 'assists', 'shots', 'blocks'])
    selected_date_range = st.slider(
        'Select Date Range',
        min_value=df['game_date'].min().date(),
        max_value=df['game_date'].max().date(),
        value=(df['game_date'].min().date(), df['game_date'].max().date())
    )

filtered_df = df[
    (df['game_date'] >= pd.to_datetime(selected_date_range[0])) &
    (df['game_date'] <= pd.to_datetime(selected_date_range[1]))
]
if selected_team != 'All':
    filtered_df = filtered_df[filtered_df['team_name'] == selected_team]

with table_col:
    st.header('Stat Totals for Each Player')
    player_totals = filtered_df.groupby(['player_name', 'team_name']).sum(numeric_only=True).reset_index()
    player_totals = player_totals.sort_values(by=selected_metric, ascending=False)
    st.dataframe(player_totals.set_index('player_name'))

with visual_col:
    if not player_totals.empty:
        selected_player = st.selectbox('Select Player to View Trend', player_totals['player_name'].unique())
        if selected_player:
            player_data = filtered_df[filtered_df['player_name'] == selected_player]
            if not player_data.empty:
                aggregated_data = player_data.groupby(['game_date'])[selected_metric].sum()
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot(aggregated_data.index, aggregated_data.values, marker='o', linestyle='-', label=f'{selected_metric.capitalize()} Trend for {selected_player}')
                ax.set_xlabel('Date')
                ax.set_ylabel(selected_metric.capitalize())
                ax.set_title(f'{selected_metric.capitalize()} Trend for {selected_player}')
                ax.grid(True)
                ax.legend()
                for x, y in zip(aggregated_data.index, aggregated_data.values):
                    ax.text(x, y, str(y), fontsize=9, ha='center', va='bottom')
                st.pyplot(fig)
            else:
                st.write("No data available for the selected player.")
    else:
        st.write("No data available for the selected filters.")
