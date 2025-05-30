import pandas as pd

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# Функція для "Нилуфар" і "Вакант Самарканд" (без урахування районів)
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
    
    # Фільтруємо дані лише для конкретного МП
    mp_subset = filtered_df[filtered_df['МП'] == mp_name]
    print(f"Унікальні значення '{value_column}' для МП '{mp_name}': {mp_subset[value_column].unique()}")
    print(f"Кількість записів для МП '{mp_name}' після фільтрації: {len(mp_subset)}")
    
    if mp_subset.empty:
        print(f"Попередження: Жодних даних не знайдено для МП '{mp_name}'.")
        return pd.DataFrame()
    
    # Групуємо дані для перевірки
    mp_grouped = mp_subset.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
    print(f"Дані для МП '{mp_name}' після групування:\n{mp_grouped}")
    
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
    
    # Перевіряємо "Итого" для дебагу
    if not pivot_table.empty:
        calculated_total = pivot_table.drop('Итого', errors='ignore').sum().round(0)
        print(f"Ручний розрахунок 'Итого' по стовпцях для МП '{mp_name}':\n{calculated_total}")
        if 'Итого' in pivot_table.index:
            print(f"Автоматичний 'Итого' з pivot_table для МП '{mp_name}':\n{pivot_table.loc['Итого']}")
    
    print(f"Зведена таблиця для МП '{mp_name}' після додавання 'Итого':\n{pivot_table}")
    return pivot_table

# Функція для всіх інших МП (з додаванням "Ташкент" і "Ташкент область")
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
    
    # Фільтруємо дані для конкретного МП
    mp_data = filtered_df[filtered_df['МП'] == mp_name].copy()
    if mp_data.empty:
        print(f"Попередження: Жодних даних не знайдено для МП '{mp_name}'.")
        return pd.DataFrame()
    
    print(f"Знайдено {len(mp_data)} записів для МП '{mp_name}'.")
    
    # Групуємо дані для МП
    mp_grouped = mp_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
    print(f"Дані для МП '{mp_name}' після групування:\n{mp_grouped}")
    
    # Додаємо дані для "Ташкент"/4
    tashkent_data = filtered_df[filtered_df['район'] == 'Ташкент'].copy()
    if not tashkent_data.empty:
        tashkent_grouped = tashkent_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
        tashkent_grouped[value_column] = tashkent_grouped[value_column] / 4
        print(f"Дані для 'Ташкент' (поділено на 4):\n{tashkent_grouped}")
    else:
        tashkent_grouped = pd.DataFrame(columns=['Наименование товаров', 'период', value_column])
        print("Попередження: Жодних даних не знайдено для району 'Ташкент'.")
    
    # Додаємо дані для районів "Ташкент область"/4
    tashkent_oblast_districts = [
        'Алмалык', 'Ангрен', 'Ахангаран', 'Бекабад', 'Бостанлыкский', 'Бука',
        'Газалкент', 'Зангиата', 'Келес', 'Кибрай', 'Коканд', 'Паркент',
        'Пискент', 'Ташкент область', 'Чиноз', 'Чирчик', 'Янгиюль'
    ]
    tashkent_oblast_data = filtered_df[filtered_df['район'].isin(tashkent_oblast_districts)].copy()
    if not tashkent_oblast_data.empty:
        tashkent_oblast_grouped = tashkent_oblast_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
        tashkent_oblast_grouped[value_column] = tashkent_oblast_grouped[value_column] / 4
        print(f"Дані для районів 'Ташкент область' (поділено на 4):\n{tashkent_oblast_grouped}")
    else:
        tashkent_oblast_grouped = pd.DataFrame(columns=['Наименование товаров', 'период', value_column])
        print(f"Попередження: Жодних даних не знайдено для районів {tashkent_oblast_districts}.")
    
    # Об'єднуємо всі дані
    result = mp_grouped.copy()
    result = result.merge(tashkent_grouped, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_tashkent'))
    result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_tashkent'].fillna(0)
    result = result.drop(columns=[f'{value_column}_tashkent'])
    print(f"Результат після об'єднання з 'Ташкент' для МП '{mp_name}':\n{result}")
    
    result = result.merge(tashkent_oblast_grouped, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_tashkent_oblast'))
    result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_tashkent_oblast'].fillna(0)
    result = result.drop(columns=[f'{value_column}_tashkent_oblast'])
    print(f"Результат після об'єднання з 'Ташкент область' для МП '{mp_name}':\n{result}")
    
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
    
    print(f"Зведена таблиця для МП '{mp_name}' після додавання 'Итого':\n{pivot_table}")
    return pivot_table