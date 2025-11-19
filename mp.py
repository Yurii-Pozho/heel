import pandas as pd

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# Функція для МП з словом "вакант" (без урахування районів)
def calculate_excluded_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
    required_columns = ['Наименование товаров', 'период', 'МП', value_column]
    if not all(col in df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)
    
    filtered_df = df.copy()
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # ТІЛЬКИ ті записи, де МП == mp_name
    mp_subset = filtered_df[filtered_df['МП'] == mp_name]
    
    if mp_subset.empty:
        return pd.DataFrame()
    
    # Визначаємо місяці, які реально є в даних
    used_months = sorted(mp_subset['период'].dropna().unique(), key=lambda x: month_order.index(x))
    
    # Формуємо зведену таблицю без автоматичного "Итого"
    pivot_table = pd.pivot_table(
        mp_subset,
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
    pivot_table = pd.concat([pivot_table, total_row])
    
    return pivot_table


# Функція для всіх інших МП (без слова "вакант" - з додаванням Ташкент і Ташкент область)
def calculate_mp_pivot_with_tashkent(df, mp_name, selected_period=None, value_column='кол-во'):
    required_columns = ['Наименование товаров', 'период', 'МП', 'район', value_column]
    if not all(col in df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)
    
    filtered_df = df.copy()
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # ТІЛЬКИ ті записи, де МП == mp_name
    mp_data = filtered_df[filtered_df['МП'] == mp_name].copy()
    if mp_data.empty:
        return pd.DataFrame()
    
    # Визначаємо місяці, коли МП реально працювало (є записи в даних)
    mp_active_months = mp_data['период'].dropna().unique().tolist()
    
    # Групуємо дані для МП
    mp_grouped = mp_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
    
    # Додаємо дані для "Ташкент"/4 ТІЛЬКИ для місяців, коли МП працювало
    tashkent_data = filtered_df[
        (filtered_df['район'] == 'Ташкент') & 
        (filtered_df['период'].isin(mp_active_months))
    ].copy()
    if not tashkent_data.empty:
        tashkent_grouped = tashkent_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
        tashkent_grouped[value_column] = tashkent_grouped[value_column] / 4
    else:
        tashkent_grouped = pd.DataFrame(columns=['Наименование товаров', 'период', value_column])
    
    # Додаємо дані для районів "Ташкент область"/4 ТІЛЬКИ для місяців, коли МП працювало
    tashkent_oblast_districts = [
        'Алмалык', 'Ангрен', 'Ахангаран', 'Бекабад', 'Бостанлыкский', 'Бука',
        'Газалкент', 'Зангиата', 'Келес', 'Кибрай', 'Коканд', 'Паркент',
        'Пискент', 'Ташкент область', 'Чиноз', 'Чирчик', 'Янгиюль'
    ]
    tashkent_oblast_data = filtered_df[
        (filtered_df['район'].isin(tashkent_oblast_districts)) & 
        (filtered_df['период'].isin(mp_active_months))
    ].copy()
    if not tashkent_oblast_data.empty:
        tashkent_oblast_grouped = tashkent_oblast_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
        tashkent_oblast_grouped[value_column] = tashkent_oblast_grouped[value_column] / 4
    else:
        tashkent_oblast_grouped = pd.DataFrame(columns=['Наименование товаров', 'период', value_column])
    
    # Об'єднуємо всі дані
    result = mp_grouped.copy()
    
    if not tashkent_grouped.empty:
        result = result.merge(tashkent_grouped, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_tashkent'))
        result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_tashkent'].fillna(0)
        result = result.drop(columns=[f'{value_column}_tashkent'])
    
    if not tashkent_oblast_grouped.empty:
        result = result.merge(tashkent_oblast_grouped, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_tashkent_oblast'))
        result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_tashkent_oblast'].fillna(0)
        result = result.drop(columns=[f'{value_column}_tashkent_oblast'])
    
    result[value_column] = result[value_column].round(0)
    
    # Визначаємо місяці, які реально є в даних (лише з ненульовими значеннями)
    used_months = sorted(
        result[result[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    # Формуємо зведену таблицю без автоматичного "Итого"
    pivot_table = pd.pivot_table(
        result,
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
    pivot_table = pd.concat([pivot_table, total_row])
    
    return pivot_table