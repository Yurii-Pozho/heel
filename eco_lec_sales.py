import pandas as pd

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

def process_data(df, selected_period=None):
    filtered_df = df[df['источник'] == 'Первичка'].copy()
    if filtered_df.empty:
        return None, None, None, []

    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))

    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
        used_months = [m for m in used_months if m in selected_period]

    pivot_qty = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='кол-во',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )[used_months + ['Итого']].round(0)

    pivot_sum = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='сумма',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )[used_months + ['Итого']].round(0)

    return filtered_df, pivot_qty, pivot_sum, used_months

# def plot_top_items(filtered_df, used_months, top_n=5):
#     top_items = (
#         filtered_df.groupby('Наименование товаров')['сумма']
#         .sum()
#         .sort_values(ascending=False)
#         .head(top_n)
#         .index
#     )

#     top_df = filtered_df[filtered_df['Наименование товаров'].isin(top_items)].copy()
#     top_df['период'] = pd.Categorical(top_df['период'], categories=used_months, ordered=True)

#     grouped = top_df.groupby(['период', 'Наименование товаров']).agg({
#         'сумма': 'sum',
#         'кол-во': 'sum'
#     }).reset_index()

    # fig = go.Figure()
    # for name in top_items:
    #     product_data = grouped[grouped['Наименование товаров'] == name]
    #     fig.add_trace(go.Bar(
    #         x=product_data['период'],
    #         y=product_data['сумма'],
    #         name=name,
    #         text=product_data['кол-во'],
    #         textposition='outside',
    #         textangle=-90,
    #         textfont=dict(size=12),
    #     ))

    # fig.update_layout(
    #     barmode='group',
    #     xaxis_title="Місяць",
    #     yaxis_title="Сума",
    #     xaxis=dict(categoryorder='array', categoryarray=used_months),
    #     legend_title="Товари",
    #     uniformtext_minsize=8,
    #     uniformtext_mode='hide',
    # )
    # return fig