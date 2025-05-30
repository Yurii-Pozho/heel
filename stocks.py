import pandas as pd

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

def calculate_source_pivot(df, source_name, selected_period=None, value_column=None):
    """
    Створюємо зведену таблицу за джерелом для показника 'кол-во' або 'Сумма СИП'.
    
    Parameters:
    -----------
    df: DataFrame з даними (аркуш 'Стоки')
    source_name: назва джерела для фільтрації
    selected_period: список періодів або None для всіх періодів
    value_column: значення для агрегації ('кол-во' або 'Сумма СИП')
    
    Returns:
    --------
    pandas.pivot_table: зведена таблиця
    """
    # Перевірка необхідних колонок
    required_columns = ['Наименование товаров', 'период', 'источник', value_column]
    if not all(col in df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    df = df.copy()
    df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)
    
    # Фільтрація за вибраним періодом
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = df[df['период'].isin(selected_period)]
        else:
            filtered_df = df[df['период'] == selected_period]
    else:
        filtered_df = df
    
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # Фільтруємо дані лише для конкретного джерела
    source_subset = filtered_df[filtered_df['источник'] == source_name]
    
    if source_subset.empty:
        return pd.DataFrame()
    
    # Визначаємо місяці, які реально є в даних (з ненульовими значеннями)
    used_months = sorted(
        source_subset[source_subset[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    if not used_months:
        return pd.DataFrame()
    
    # Формуємо зведену таблицу без автоматичного "Итого"
    pivot_table = pd.pivot_table(
        source_subset,
        index='Наименование товаров',
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