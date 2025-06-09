import pandas as pd
import plotly.express as px

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

def generate_source_pivots(df, selected_period=None):
    # Фільтруємо дані, виключаючи джерело 'Первичка минус'
    filtered_df = df[~df['источник'].isin(['Первичка минус', 'Первичка'])].copy()
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    
    # Фільтрація за вибраним діапазоном періодів
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    # Перетворюємо 'кол-во' і 'Сумма СИП' у числові типи
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    filtered_df['Сумма СИП'] = pd.to_numeric(filtered_df['Сумма СИП'], errors='coerce').fillna(0)
    
    # Визначаємо місяці, які реально є в даних (з ненульовими значеннями для 'кол-во')
    used_months_qty = sorted(
        filtered_df[filtered_df['кол-во'] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    # Визначаємо місяці, які реально є в даних (з ненульовими значеннями для 'Сумма СИП')
    used_months_sum = sorted(
        filtered_df[filtered_df['Сумма СИП'] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    # Створюємо зведену таблицю для кількості
    pivot_qty_by_source = pd.pivot_table(
        filtered_df,
        index='источник',
        columns='период',
        values='кол-во',
        aggfunc='sum',
        fill_value=0,
        margins=False
    )
    
    # Сортуємо стовпці за наявними місяцями
    pivot_qty_by_source = pivot_qty_by_source.reindex(columns=used_months_qty)
    
    # Додаємо "Итого" вручну
    pivot_qty_by_source['Итого'] = pivot_qty_by_source.sum(axis=1)
    total_row_qty = pivot_qty_by_source.sum(axis=0).to_frame().T
    total_row_qty.index = ['Итого']
    pivot_qty_by_source = pd.concat([pivot_qty_by_source, total_row_qty]).round(0)
    
    # Створюємо зведену таблицю для суми СИП
    pivot_sum_by_source = pd.pivot_table(
        filtered_df,
        index='источник',
        columns='период',
        values='Сумма СИП',
        aggfunc='sum',
        fill_value=0,
        margins=False
    )
    
    # Сортуємо стовпці за наявними місяцями
    pivot_sum_by_source = pivot_sum_by_source.reindex(columns=used_months_sum)
    
    # Додаємо "Итого" вручну
    pivot_sum_by_source['Итого'] = pivot_sum_by_source.sum(axis=1)
    total_row_sum = pivot_sum_by_source.sum(axis=0).to_frame().T
    total_row_sum.index = ['Итого']
    pivot_sum_by_source = pd.concat([pivot_sum_by_source, total_row_sum]).round(0)
    
    return pivot_qty_by_source, pivot_sum_by_source

def plot_source_pie(pivot_sum_by_source):
    # Використовуємо стовпець "Итого" для кругової діаграми
    pie_data = pivot_sum_by_source['Итого'].drop('Итого')
    pie_df = pie_data.reset_index()
    pie_df.columns = ['источник', 'Сумма СИП']
    
    # Створюємо кругову діаграму
    pie_chart = px.pie(
        pie_df,
        values='Сумма СИП',
        names='источник',
        hole=0.3
    )
    
    pie_chart.update_layout(
        width=600,
        height=600
    )
    
    return pie_chart