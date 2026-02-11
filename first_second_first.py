import pandas as pd
from utils import БАДЫ, ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ, MONTH_MAP

def create_pivot_by_group(df, selected_period=None):
    df = df.copy()
    
    # 1. ПЕРЕТВОРЕННЯ: перетворюємо період на справжню дату та нормалізуємо
    df['период'] = pd.to_datetime(df['период'], errors='coerce')
    df = df.dropna(subset=['период'])
    df['период'] = df['период'].dt.to_period('M').dt.to_timestamp()

    # 2. ФІЛЬТР
    if selected_period:
        selected_period_dt = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        if isinstance(selected_period, list):
            df = df[df['период'].isin(selected_period_dt)]
        else:
            df = df[df['период'] == selected_period_dt]

    # Перетворюємо показники в числа
    df['кол-во'] = pd.to_numeric(df['кол-во'], errors='coerce').fillna(0)
    df['Сумма СИП'] = pd.to_numeric(df['Сумма СИП'], errors='coerce').fillna(0)

    # 3. СОРТУВАННЯ
    used_months = sorted(df[df['кол-во'] > 0]['период'].unique())

    # Допоміжна функція для форматування назви стовпця (Timestamp -> Ru Text)
    def get_ru_label(ts):
        if not isinstance(ts, pd.Timestamp): return ts
        eng_month = ts.strftime('%B')
        ru_month = MONTH_MAP.get(eng_month, eng_month)
        return f"{ru_month} {ts.year}"

    def make_pivot(group_df):
        if group_df.empty:
            cols = [get_ru_label(m) for m in used_months] + ['Итого'] if used_months else ['Итого']
            empty = pd.DataFrame(0, index=['Итого'], columns=cols, dtype=int)
            return empty, empty.copy()

        def process_val(val_col):
            pivot = pd.pivot_table(group_df, index='Наименование товаров', columns='период',
                                 values=val_col, aggfunc='sum', fill_value=0)
            pivot = pivot.reindex(columns=used_months, fill_value=0)
            
            # Перейменування стовпців на російську
            pivot.columns = [get_ru_label(c) for c in pivot.columns]
            
            # Підсумки
            pivot['Итого'] = pivot.sum(axis=1)
            total_row = pivot.sum().to_frame().T
            total_row.index = ['Итого']
            return pd.concat([pivot, total_row]).round(0).astype(int)

        qty = process_val('кол-во')
        suma = process_val('Сумма СИП')
        return qty, suma

    # Розподіл по групах
    qty_bad, sum_bad = make_pivot(df[df['Наименование товаров'].isin(БАДЫ)])
    qty_lek, sum_lek = make_pivot(df[df['Наименование товаров'].isin(ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ)])

    # Повертаємо російські назви для UI слайдера
    used_months_labels = [get_ru_label(m) for m in used_months]

    return qty_bad, sum_bad, qty_lek, sum_lek, used_months_labels