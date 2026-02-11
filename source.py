import pandas as pd
from utils import MONTH_MAP

def generate_source_pivots(df, selected_period=None):
    """
    Створює зведені таблиці за джерелами, використовуючи хронологію дат.
    """
    # 1. Фільтруємо непотрібні джерела
    filtered_df = df[~df['источник'].isin(['Первичка Минус', 'Первичка'])].copy()
    
    # 2. Очищення та нормалізація дат
    filtered_df['период'] = pd.to_datetime(filtered_df['период'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['период'])
    filtered_df['период'] = filtered_df['период'].dt.to_period('M').dt.to_timestamp()
    
    # 3. Фільтрація за вибраним періодом
    if selected_period is not None:
        selected_period_dt = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        filtered_df = filtered_df[filtered_df['период'].isin(selected_period_dt)]
    
    # 4. Перетворення показників
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    filtered_df['Сумма СИП'] = pd.to_numeric(filtered_df['Сумма СИП'], errors='coerce').fillna(0)
    
    def finalize_pivot(pivot_df):
        if pivot_df.empty:
            return pivot_df
        
        # Сортуємо стовпці хронологічно
        pivot_df = pivot_df.reindex(columns=sorted(pivot_df.columns))
        
        # Додаємо підсумки
        pivot_df['Итого'] = pivot_df.sum(axis=1)
        total_row = pivot_df.sum(axis=0).to_frame().T
        total_row.index = ['Итого']
        pivot_df = pd.concat([pivot_df, total_row])
        
        # Форматування заголовків (Російська мова)
        new_cols = {}
        for col in pivot_df.columns:
            if isinstance(col, pd.Timestamp):
                eng_month = col.strftime('%B')
                ru_month = MONTH_MAP.get(eng_month, eng_month)
                new_cols[col] = f"{ru_month} {col.year}"
        
        return pivot_df.rename(columns=new_cols).round(0).astype(int)

    # 5. Кількість
    pivot_qty = pd.pivot_table(
        filtered_df, index='источник', columns='период', values='кол-во', aggfunc='sum', fill_value=0
    )
    pivot_qty = finalize_pivot(pivot_qty)
    
    # 6. Сума СИП
    pivot_sum = pd.pivot_table(
        filtered_df, index='источник', columns='период', values='Сумма СИП', aggfunc='sum', fill_value=0
    )
    pivot_sum = finalize_pivot(pivot_sum)
    
    return pivot_qty, pivot_sum