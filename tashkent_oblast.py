import pandas as pd
from utils import MONTH_MAP

# Список районів області для фільтрації
OBLAST_DISTRICTS = [
    'Алмалык', 'Ангрен', 'Ахангаран', 'Бекабад', 'Бостанлыкский', 'Бука',
    'Газалкент', 'Зангиата', 'Келес', 'Кибрай', 'Коканд', 'Паркент',
    'Пискент', 'Ташкент область', 'Чиноз', 'Чирчик', 'Янгиюль'
]

def _generate_pivot_base(df, districts, value_column, selected_period=None, divide_by=1):
    """Універсальна функція: правильні розрахунки + робота з датами."""
    df = df.copy()
    
    # 1. Підготовка дат
    df['период'] = pd.to_datetime(df['период'], errors='coerce')
    df = df.dropna(subset=['период', 'Наименование товаров'])
    
    # Нормалізація дат до 1-го числа
    df['период'] = df['период'].dt.to_period('M').dt.to_timestamp()

    # 2. Фільтрація за районами
    if isinstance(districts, str):
        filtered_df = df[df['район'] == districts].copy()
    else:
        filtered_df = df[df['район'].isin(districts)].copy()
        
    if filtered_df.empty:
        return pd.DataFrame()

    # 3. Перетворення значень у числовий формат
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)

    # 4. Фільтрація за вибраним періодом
    if selected_period is not None:
        sel_p = pd.to_datetime(selected_period).to_period('M').to_timestamp()
        filtered_df = filtered_df[filtered_df['период'].isin(sel_p)]

    if filtered_df.empty:
        return pd.DataFrame()

    # 5. Створення зведеної таблиці
    pivot_table = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0
    )

    # 6. Розрахунок підсумків та ділення
    if divide_by != 1:
        pivot_table = pivot_table / divide_by

    # Додаємо "Итого"
    pivot_table['Итого'] = pivot_table.sum(axis=1)
    total_row = pivot_table.sum(axis=0).to_frame().T
    total_row.index = ['Итого']
    pivot_table = pd.concat([pivot_table, total_row])

    # 7. Хронологічне сортування
    date_cols = sorted([c for c in pivot_table.columns if isinstance(c, pd.Timestamp)])
    pivot_table = pivot_table.reindex(columns=date_cols + ['Итого'])

    # 8. Форматування заголовків (Російська мова)
    new_labels = {}
    for col in pivot_table.columns:
        if isinstance(col, pd.Timestamp):
            eng_month = col.strftime('%B')
            ru_month = MONTH_MAP.get(eng_month, eng_month)
            new_labels[col] = f"{ru_month} {col.year}"
    
    # Округлюємо та перетворюємо в int
    pivot_table = pivot_table.rename(columns=new_labels).apply(lambda x: x.round(0).astype(int))

    return pivot_table

# Функції-обгортки для області
def generate_other_districts_pivot(df, p=None):
    return _generate_pivot_base(df, OBLAST_DISTRICTS, 'кол-во', p)

def generate_other_districts_sum_sip_pivot(df, p=None):
    return _generate_pivot_base(df, OBLAST_DISTRICTS, 'Сумма СИП', p)

def generate_other_districts_divided_pivot(df, p=None):
    return _generate_pivot_base(df, OBLAST_DISTRICTS, 'кол-во', p, divide_by=4)

def generate_other_districts_sum_sip_divided_pivot(df, p=None):
    return _generate_pivot_base(df, OBLAST_DISTRICTS, 'Сумма СИП', p, divide_by=4)