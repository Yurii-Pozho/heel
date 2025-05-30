import pandas as pd

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

def generate_region_period_pivot(df, selected_period=None, value_column='кол-во'):
    """
    Створює зведену таблицю для регіонів і періодів за обраним показником (кол-во або Сумма СИП).
    
    Parameters:
        df: DataFrame з даними
        selected_period: список періодів або None для всіх періодів
        value_column: стовпець для агрегації ('кол-во' або 'Сумма СИП')
    Returns:
        pivot_table: зведена таблиця
    """
    # Фільтруємо дані, виключаючи джерела 'Первичка' і 'Первичка минус'
    filtered_df = df[~df['источник'].isin(['Первичка', 'Первичка минус'])].copy()
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    
    # Фільтрація за вибраним діапазоном періодів
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    # Перетворюємо обраний стовпець у числовий тип
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # Перевіряємо наявність колонок 'регион' і 'район'
    if 'регион' not in filtered_df.columns or 'район' not in filtered_df.columns:
        raise KeyError(f"Колонки 'регион' і 'район' мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Видаляємо записи з пропусками в 'регион' або 'район'
    filtered_df = filtered_df.dropna(subset=['регион', 'район'])
    
    # Отримуємо унікальні комбінації 'регион' і 'район'
    valid_combinations = filtered_df[['регион', 'район']].drop_duplicates()
    
    # Фільтруємо дані, щоб залишити лише дійсні комбінації
    filtered_df = filtered_df.merge(
        valid_combinations,
        on=['регион', 'район'],
        how='inner'
    )
    
    # Об’єднуємо 'регион' і 'район' у нову колонку 'регион, район'
    filtered_df['регион, район'] = filtered_df['регион'] + ', ' + filtered_df['район']
    
    # Визначаємо місяці, які реально є в даних (з ненульовими значеннями)
    used_months = sorted(
        filtered_df[filtered_df[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    if not used_months:
        return pd.DataFrame()  # Повертаємо порожній DataFrame, якщо немає даних
    
    # Створюємо зведену таблицю без автоматичного "Итого"
    pivot_table = pd.pivot_table(
        filtered_df,
        index='регион, район',
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0,
        margins=False
    )
    
    # Сортуємо стовпці за наявними місяцями
    pivot_table = pivot_table.reindex(columns=used_months)
    
    # Додаємо "Итого" вручну
    pivot_table['Итого'] = pivot_table.sum(axis=1).round(0)
    total_row = pivot_table.sum(axis=0).to_frame().T
    total_row.index = ['Итого']
    pivot_table = pd.concat([pivot_table, total_row]).round(0)
    
    return pivot_table