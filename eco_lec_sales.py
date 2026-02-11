from utils import finalize_report
import pandas as pd

def process_data(df, selected_period=None):
    # Фільтруємо джерело
    filtered_df = df[df['источник'] == 'Первичка'].copy()
    if filtered_df.empty:
        return None, None, None, []

    # 1. Нормалізація дат (важливо: до 1-го числа місяця!)
    filtered_df['период'] = pd.to_datetime(filtered_df['период'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['период'])
    filtered_df['период'] = filtered_df['период'].dt.to_period('M').dt.to_timestamp()

    # 2. Фільтрація вибраного періоду
    if selected_period is not None:
        sel_p = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        filtered_df = filtered_df[filtered_df['период'].isin(sel_p)]

    if filtered_df.empty:
        return None, None, None, []

    # 3. Підготовка числових даних
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    sum_col = 'сумма' if 'сумма' in filtered_df.columns else 'Сумма СИП'
    filtered_df[sum_col] = pd.to_numeric(filtered_df[sum_col], errors='coerce').fillna(0)

    def make_pivot(val_column):
        pivot = pd.pivot_table(
            filtered_df,
            index='Наименование товаров',
            columns='период',
            values=val_column,
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name='Итого'
        )
        return finalize_report(pivot)

    pivot_qty = make_pivot('кол-во')
    pivot_sum = make_pivot(sum_col)
    
    used_labels = [c for c in pivot_qty.columns if c != 'Итого']
    return filtered_df, pivot_qty, pivot_sum, used_labels