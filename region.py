import pandas as pd
from utils import MONTH_MAP


PHARMACEUTICALS = [
    'Вибуркол супп рект № 12',
    'Дискус композитум р-р для инъекций 2,2 мл № 5',
    'Лимфомиозот амп 1,1 мл № 5',
    'Лимфомиозот капли 30мл',
    'Ньюрексан таблетки № 25',
    'Ньюрексан таблетки № 50',
    'Траумель С амп 2,2 мл № 5',
    'Траумель С мазь 50г',
    'Траумель С р-р для инъекций 2,2 мл № 100',
    'Траумель С таблетки № 50',
    'Цель Т амп 2 мл № 100',
    'Цель Т амп № 5',
    'Цель Т мазь 50г',
    'Цель Т таблетки № 50',
    'Церебрум композитум р-р д/инъек 2,2мл №10',
    'Энгистол таблетки № 50',
]


def generate_region_period_pivot(
    df,
    selected_period=None,
    value_column='кол-во',
    drug_column='Наименование товаров',
    selected_products=None
):
    """
    Створює зведену таблицю для регіонів і періодів на основі реальних дат.

    Логіка:
    1. Прибирає джерела Первичка / Первичка Минус.
    2. Фільтрує дані тільки по препаратах зі списку PHARMACEUTICALS.
    3. Нормалізує період до початку місяця.
    4. Групує по регіону + району.
    5. Робить pivot по місяцях.
    6. Додає Итого по рядках і колонках.
    """

    # 1. Перевірка обов'язкових колонок
    required_columns = [
        'источник',
        'период',
        'регион',
        'район',
        value_column,
        drug_column,
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        print(f"Відсутні колонки: {missing_columns}")
        return pd.DataFrame()

    # 2. Фільтрація джерел
    filtered_df = df[
        ~df['источник'].isin([
            'Первичка',
            'Первичка Минус',
            'Первичка минус',
        ])
    ].copy()

    # 3. Нормалізація назви препарату
    filtered_df[drug_column] = (
        filtered_df[drug_column]
        .astype(str)
        .str.strip()
    )

    # 4. Фільтр тільки по потрібних препаратах
    products_to_use = selected_products if selected_products else PHARMACEUTICALS
    filtered_df = filtered_df[
        filtered_df[drug_column].isin(products_to_use)
    ].copy()

    if filtered_df.empty:
        return pd.DataFrame()

    # 5. Очищення дат
    filtered_df['период'] = pd.to_datetime(
        filtered_df['период'],
        errors='coerce'
    )

    # 6. Прибираємо рядки без дати, регіону або району
    filtered_df = filtered_df.dropna(
        subset=[
            'период',
            'регион',
            'район',
        ]
    )

    if filtered_df.empty:
        return pd.DataFrame()

    # 7. Нормалізація дати до початку місяця
    filtered_df['период'] = (
        filtered_df['период']
        .dt.to_period('M')
        .dt.to_timestamp()
    )

    # 8. Очищення числового показника
    filtered_df[value_column] = pd.to_numeric(
        filtered_df[value_column],
        errors='coerce'
    ).fillna(0)

    # 9. Фільтрація за вибраним періодом
    if selected_period is not None:
        selected_period_dt = (
            pd.to_datetime(selected_period)
            .to_period('M')
            .to_timestamp()
        )

        filtered_df = filtered_df[
            filtered_df['период'].isin(selected_period_dt)
        ].copy()

    if filtered_df.empty:
        return pd.DataFrame()

    # 10. Об'єднання регіону та району
    filtered_df['регион, район'] = (
        filtered_df['регион'].astype(str).str.strip()
        + ', '
        + filtered_df['район'].astype(str).str.strip()
    )

    # 11. Формування зведеної таблиці
    pivot_table = pd.pivot_table(
        filtered_df,
        index=['регион, район', drug_column],
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0
    )

    # 12. Сортування колонок-дат
    pivot_table = pivot_table.reindex(
        columns=sorted(pivot_table.columns)
    )

    # 13. Додаємо підсумок по рядках
    pivot_table['Итого'] = pivot_table.sum(axis=1)

    # 14. Додаємо підсумковий рядок
    total_row = pivot_table.sum(axis=0).to_frame().T
    total_row.index = pd.MultiIndex.from_tuples([('Итого', '')], names=pivot_table.index.names)

    pivot_table = pd.concat([
        pivot_table,
        total_row,
    ])

    # 15. Форматування назв місяців
    new_columns = {}

    for col in pivot_table.columns:
        if isinstance(col, pd.Timestamp):
            eng_month = col.strftime('%B')
            ru_month = MONTH_MAP.get(eng_month, eng_month)
            new_columns[col] = f"{ru_month} {col.year}"

    pivot_table = pivot_table.rename(columns=new_columns)

    # 16. Округлення і приведення до int
    return pivot_table.round(0).astype(int)

#  app