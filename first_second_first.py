import pandas as pd


month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

def create_pivot_tables(df, selected_period=None):
    filtered_df = df.copy()
    
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
    
    # Визначаємо місяці, які реально є в даних (з ненульовими значеннями)
    used_months = sorted(
        filtered_df[filtered_df['кол-во'] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    # Створюємо зведену таблицю для кількості
    pivot_qty = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='кол-во',
        aggfunc='sum',
        fill_value=0,
        margins=False
    )
    
    # Сортуємо стовпці за наявними місяцями
    pivot_qty = pivot_qty.reindex(columns=used_months)
    
    # Додаємо "Итого" вручну
    pivot_qty['Итого'] = pivot_qty.sum(axis=1)
    total_row_qty = pivot_qty.sum(axis=0).to_frame().T
    total_row_qty.index = ['Итого']
    pivot_qty = pd.concat([pivot_qty, total_row_qty]).round(0)
    
    # Створюємо зведену таблицю для суми СИП
    pivot_sum = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='Сумма СИП',
        aggfunc='sum',
        fill_value=0,
        margins=False
    )
    
    # Сортуємо стовпці за наявними місяцями
    pivot_sum = pivot_sum.reindex(columns=used_months)
    
    # Додаємо "Итого" вручну
    pivot_sum['Итого'] = pivot_sum.sum(axis=1)
    total_row_sum = pivot_sum.sum(axis=0).to_frame().T
    total_row_sum.index = ['Итого']
    pivot_sum = pd.concat([pivot_sum, total_row_sum]).round(0)
    
    return pivot_qty, pivot_sum, used_months

