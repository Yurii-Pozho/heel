import pandas as pd
from utils import MONTH_MAP

def generate_region_period_pivot(df, selected_period=None, value_column='кол-во'):
    """
    Створює зведену таблицю для регіонів і періодів на основі реальних дат.
    """
    # 1. Фільтрація джерел
    filtered_df = df[~df['источник'].isin(['Первичка', 'Первичка Минус'])].copy()
    
    # 2. Очищення дат та показників
    filtered_df['период'] = pd.to_datetime(filtered_df['период'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['период', 'регион', 'район'])
    
    # Нормалізація до початку місяця
    filtered_df['период'] = filtered_df['период'].dt.to_period('M').dt.to_timestamp()
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # 3. Фільтрація за періодом
    if selected_period is not None:
        selected_period_dt = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        filtered_df = filtered_df[filtered_df['период'].isin(selected_period_dt)]
    
    if filtered_df.empty:
        return pd.DataFrame()

    # 4. Об'єднання регіону та району
    filtered_df['регион, район'] = filtered_df['регион'].astype(str) + ', ' + filtered_df['район'].astype(str)
    
    # 5. Формування зведеної таблиці
    pivot_table = pd.pivot_table(
        filtered_df,
        index='регион, район',
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0
    )
    
    # Сортування колонок-дат
    pivot_table = pivot_table.reindex(columns=sorted(pivot_table.columns))
    
    # 6. Розрахунок підсумків
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
            
    return pivot_table.rename(columns=new_columns).round(0).astype(int)