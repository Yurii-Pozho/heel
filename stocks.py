import pandas as pd
from utils import MONTH_MAP

def calculate_source_pivot(df, source_name, selected_period=None, value_column=None):
    """
    Створюємо зведену таблицу за джерелом для показника 'кол-во' або 'Сумма СИП',
    використовуючи хронологію дат.
    """
    # Перевірка необхідних колонок
    required_columns = ['Наименование товаров', 'период', 'источник', value_column]
    if not all(col in df.columns for col in required_columns):
        return pd.DataFrame()
    
    # 1. ПЕРЕТВОРЕННЯ
    df = df.copy()
    df['период'] = pd.to_datetime(df['период'], errors='coerce')
    df = df.dropna(subset=['период'])
    # Нормалізуємо до 1-го числа для точного співпадіння
    df['период'] = df['период'].dt.to_period('M').dt.to_timestamp()
    
    # 2. Фільтрація за вибраним періодом
    if selected_period:
        # Приводимо вибраний період до початку місяця для порівняння
        selected_period_dt = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        if isinstance(selected_period, list):
            filtered_df = df[df['период'].isin(selected_period_dt)]
        else:
            filtered_df = df[df['период'] == selected_period_dt]
    else:
        filtered_df = df
    
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # 3. Фільтруємо джерело
    source_subset = filtered_df[filtered_df['источник'] == source_name]
    
    if source_subset.empty:
        return pd.DataFrame()
    
    # 4. СОРТУВАННЯ
    used_months = sorted(source_subset[source_subset[value_column] > 0]['период'].unique())
    
    if not used_months:
        return pd.DataFrame()
    
    # 5. Формуємо зведену таблицу
    pivot_table = pd.pivot_table(
        source_subset,
        index='Наименование товаров',
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0,
        margins=False
    )
    
    pivot_table = pivot_table.reindex(columns=used_months)
    
    # 6. Додаємо "Итого"
    pivot_table['Итого'] = pivot_table.sum(axis=1)
    total_row = pivot_table.sum(axis=0).to_frame().T
    total_row.index = ['Итого']
    pivot_table = pd.concat([pivot_table, total_row])
    
    # 7. ФОРМАТУВАННЯ (Російські назви)
    new_columns = {}
    for col in pivot_table.columns:
        if isinstance(col, pd.Timestamp):
            eng_month = col.strftime('%B')
            ru_month = MONTH_MAP.get(eng_month, eng_month)
            new_columns[col] = f"{ru_month} {col.year}"
            
    pivot_table = pivot_table.rename(columns=new_columns).round(0).astype(int)
    
    return pivot_table