import pandas as pd
from utils import MONTH_MAP

SUPPLEMENTS_FOR_MP_BONUS = [
    'Витрум ретинорм капс. №90',
    'Ксефомиелин таб. №30',
    'Синулан Форте таб. №30'
]
PHARMACEUTICALS = [
    'Вибуркол супп рект № 12', 'Дискус композитум р-р для инъекций 2,2 мл № 5', 
    'Лимфомиозот амп 1,1 мл № 5', 'Лимфомиозот капли 30мл', 'Ньюрексан таблетки № 25', 
    'Ньюрексан таблетки № 50', 'Траумель С амп 2,2 мл № 5', 'Траумель С мазь 50г', 
    'Траумель С р-р для инъекций 2,2 мл № 100', 'Траумель С таблетки № 50', 
    'Цель Т амп 2 мл № 100', 'Цель Т амп № 5', 'Цель Т мазь 50г', 'Цель Т таблетки № 50', 
    'Церебрум композитум р-р д/инъек 2,2мл №10', 'Энгистол таблетки № 50',
]

def generate_source_pivots(df, selected_period=None, category='all'):
    """
    Створює зведені таблиці за джерелами.
    category: 'all', 'drugs' (лекарства), 'supplements' (БАДы)
    """
    # 1. Фільтруємо непотрібні джерела
    filtered_df = df[~df['источник'].isin(['Первичка Минус', 'Первичка'])].copy()
    
    # 2. Очищення дат
    filtered_df['период'] = pd.to_datetime(filtered_df['период'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['период'])
    filtered_df['период'] = filtered_df['период'].dt.to_period('M').dt.to_timestamp()
    
    # 3. Фільтрація за категорією
    if category == 'drugs':
        filtered_df = filtered_df[filtered_df['Наименование товаров'].isin(PHARMACEUTICALS)]
    elif category == 'supplements':
        filtered_df = filtered_df[filtered_df['Наименование товаров'].isin(SUPPLEMENTS_FOR_MP_BONUS)]
    
    # 4. Фільтрація за вибраним періодом
    if selected_period is not None:
        filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
    
    # 5. Перетворення показників
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    filtered_df['Сумма СИП'] = pd.to_numeric(filtered_df['Сумма СИП'], errors='coerce').fillna(0)
    
    def finalize_pivot(pivot_df):
        if pivot_df.empty:
            return pd.DataFrame()
        
        pivot_df = pivot_df.reindex(columns=sorted(pivot_df.columns))
        pivot_df['Итого'] = pivot_df.sum(axis=1)
        total_row = pivot_df.sum(axis=0).to_frame().T
        total_row.index = ['Итого']
        pivot_df = pd.concat([pivot_df, total_row])
        
        new_cols = {}
        for col in pivot_df.columns:
            if isinstance(col, pd.Timestamp):
                eng_month = col.strftime('%B')
                ru_month = MONTH_MAP.get(eng_month, eng_month)
                new_cols[col] = f"{ru_month} {col.year}"
        
        return pivot_df.rename(columns=new_cols).round(0).astype(int)

    # Кількість
    pivot_qty = pd.pivot_table(
        filtered_df, index='источник', columns='период', values='кол-во', aggfunc='sum', fill_value=0
    )
    pivot_qty = finalize_pivot(pivot_qty)
    
    # Сума
    pivot_sum = pd.pivot_table(
        filtered_df, index='источник', columns='период', values='Сумма СИП', aggfunc='sum', fill_value=0
    )
    pivot_sum = finalize_pivot(pivot_sum)
    
    return pivot_qty, pivot_sum