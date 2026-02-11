import pandas as pd
from utils import MONTH_MAP

def _generate_tashkent_pivot_base(df, value_column, selected_period=None, divide_by=1):
    df = df.copy()
    
    # 1. Перетворення на число (робимо це ДО фільтрації, щоб уникнути помилок)
    df[value_column] = pd.to_numeric(df[value_column], errors='coerce').fillna(0)
    
    # 2. Обробка дат
    df['период'] = pd.to_datetime(df['период'], errors='coerce')
    df = df.dropna(subset=['период', 'Наименование товаров', 'район'])
    
    # Зводимо до 1-го числа місяця для уніфікації
    df['период'] = df['период'].dt.to_period('M').dt.to_timestamp()

    # 3. Фільтрація по Ташкенту
    filtered_df = df[df['район'] == 'Ташкент'].copy()
    
    if filtered_df.empty:
        return pd.DataFrame()

    # 4. Фільтрація за вибраним періодом
    if selected_period is not None:
        # Перетворюємо вибрані періоди на такі ж дати (1-ше число)
        selected_period_dt = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        filtered_df = filtered_df[filtered_df['период'].isin(selected_period_dt)]

    if filtered_df.empty:
        return pd.DataFrame()

    # 5. Створення зведеної таблиці
    pivot_table = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )

    # 6. Розрахунок бонусів (ділення на 4)
    # Важливо: спочатку ділимо, потім округлюємо
    if divide_by != 1:
        pivot_table = (pivot_table / divide_by)

    # 7. Сортування стовпців
    date_cols = sorted([c for c in pivot_table.columns if isinstance(c, pd.Timestamp)])
    final_cols = date_cols + (['Итого'] if 'Итого' in pivot_table.columns else [])
    pivot_table = pivot_table.reindex(columns=final_cols)

    # 8. Форматування заголовків через MONTH_MAP
    format_map = {}
    for col in pivot_table.columns:
        if isinstance(col, pd.Timestamp):
            eng_month = col.strftime('%B')
            ru_month = MONTH_MAP.get(eng_month, eng_month)
            format_map[col] = f"{ru_month} {col.year}"
            
    pivot_table = pivot_table.rename(columns=format_map)

    # 9. Округлення та фінальний тип (round(0) перед int)
    return pivot_table.round(0).astype(int)

# Функції-обгортки
def generate_tashkent_pivot(df, p): return _generate_tashkent_pivot_base(df, 'кол-во', p)
def generate_tashkent_sum_sip_pivot(df, p): return _generate_tashkent_pivot_base(df, 'Сумма СИП', p)
def generate_tashkent_divided_pivot(df, p): return _generate_tashkent_pivot_base(df, 'кол-во', p, divide_by=4)
def generate_tashkent_sum_sip_divided_pivot(df, p): return _generate_tashkent_pivot_base(df, 'Сумма СИП', p, divide_by=4)