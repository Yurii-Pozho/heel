import pandas as pd

def generate_tashkent_pivot(df, selected_period=None):
    # Перевіряємо наявність колонки 'район'
    if 'район' not in df.columns:
        raise KeyError("Колонка 'район' відсутня в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Фільтруємо дані для району "Ташкент" і виводимо діагностику
    filtered_df = df[df['район'] == 'Ташкент'].copy()
    if filtered_df.empty:
        print("Попередження: Жодних даних не знайдено для району 'Ташкент'. Перевірте значення в колонці 'район'.")
    else:
        print(f"Знайдено {len(filtered_df)} записів для району 'Ташкент'. Унікальні значення 'район': {df['район'].dropna().unique()}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    
    # Перетворюємо 'кол-во' у числовий тип
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    
    # Перевіряємо наявність колонок
    required_columns = ['Наименование товаров', 'период', 'кол-во']
    if not all(col in filtered_df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Видаляємо записи з пропусками в 'Наименование товаров' або 'период'
    filtered_df = filtered_df.dropna(subset=['Наименование товаров', 'период'])
    
    # Фільтруємо за вибраним списком періодів, якщо задано
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    # Створюємо зведену таблицю
    pivot_table = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='кол-во',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )
    
    # Сортуємо стовпці (періоди) за порядком
    used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))
    pivot_table = pivot_table.reindex(columns=used_months + ['Итого']).round(0)
    
    # Переносимо 'Итого' в кінець індексу
    if 'Итого' in pivot_table.index:
        idx = pivot_table.index.tolist()
        idx.remove('Итого')
        idx.append('Итого')
        pivot_table = pivot_table.reindex(idx)
    
    return pivot_table

def generate_tashkent_sum_sip_pivot(df, selected_period=None):
    # Перевіряємо наявність колонки 'район'
    if 'район' not in df.columns:
        raise KeyError("Колонка 'район' відсутня в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Фільтруємо дані для району "Ташкент" і виводимо діагностику
    filtered_df = df[df['район'] == 'Ташкент'].copy()
    if filtered_df.empty:
        print("Попередження: Жодних даних не знайдено для району 'Ташкент'. Перевірте значення в колонці 'район'.")
    else:
        print(f"Знайдено {len(filtered_df)} записів для району 'Ташкент'. Унікальні значення 'район': {df['район'].dropna().unique()}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    
    # Перетворюємо 'Сумма СИП' у числовий тип
    filtered_df['Сумма СИП'] = pd.to_numeric(filtered_df['Сумма СИП'], errors='coerce').fillna(0)
    
    # Перевіряємо наявність колонок
    required_columns = ['Наименование товаров', 'период', 'Сумма СИП']
    if not all(col in filtered_df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Видаляємо записи з пропусками в 'Наименование товаров' або 'период'
    filtered_df = filtered_df.dropna(subset=['Наименование товаров', 'период'])
    
    # Фільтруємо за вибраним списком періодів, якщо задано
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    # Створюємо зведену таблицю
    pivot_table = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='Сумма СИП',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )
    
    # Сортуємо стовпці (періоди) за порядком
    used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))
    pivot_table = pivot_table.reindex(columns=used_months + ['Итого']).round(0)
    
    # Переносимо 'Итого' в кінець індексу
    if 'Итого' in pivot_table.index:
        idx = pivot_table.index.tolist()
        idx.remove('Итого')
        idx.append('Итого')
        pivot_table = pivot_table.reindex(idx)
    
    return pivot_table

def generate_tashkent_divided_pivot(df, selected_period=None):
    # Перевіряємо наявність колонки 'район'
    if 'район' not in df.columns:
        raise KeyError("Колонка 'район' відсутня в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Фільтруємо дані для району "Ташкент" і виводимо діагностику
    filtered_df = df[df['район'] == 'Ташкент'].copy()
    if filtered_df.empty:
        print("Попередження: Жодних даних не знайдено для району 'Ташкент'. Перевірте значення в колонці 'район'.")
    else:
        print(f"Знайдено {len(filtered_df)} записів для району 'Ташкент'. Унікальні значення 'район': {df['район'].dropna().unique()}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    
    # Перетворюємо 'кол-во' у числовий тип
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    
    # Перевіряємо наявність колонок
    required_columns = ['Наименование товаров', 'период', 'кол-во']
    if not all(col in filtered_df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Видаляємо записи з пропусками в 'Наименование товаров' або 'период'
    filtered_df = filtered_df.dropna(subset=['Наименование товаров', 'период'])
    
    # Фільтруємо за вибраним списком періодів, якщо задано
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    # Створюємо зведену таблицю
    pivot_table = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='кол-во',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )
    
    # Ділимо всі значення на 4, залишаючи 0 там, де значення вже 0
    pivot_table = pivot_table.where(pivot_table == 0, pivot_table / 4)
    
    # Сортуємо стовпці (періоди) за порядком
    used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))
    pivot_table = pivot_table.reindex(columns=used_months + ['Итого']).round(0)
    
    # Переносимо 'Итого' в кінець індексу
    if 'Итого' in pivot_table.index:
        idx = pivot_table.index.tolist()
        idx.remove('Итого')
        idx.append('Итого')
        pivot_table = pivot_table.reindex(idx)
    
    return pivot_table

def generate_tashkent_sum_sip_divided_pivot(df, selected_period=None):
    # Перевіряємо наявність колонки 'район'
    if 'район' not in df.columns:
        raise KeyError("Колонка 'район' відсутня в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Фільтруємо дані для району "Ташкент" і виводимо діагностику
    filtered_df = df[df['район'] == 'Ташкент'].copy()
    if filtered_df.empty:
        print("Попередження: Жодних даних не знайдено для району 'Ташкент'. Перевірте значення в колонці 'район'.")
    else:
        print(f"Знайдено {len(filtered_df)} записів для району 'Ташкент'. Унікальні значення 'район': {df['район'].dropna().unique()}")
    
    # Перетворюємо 'период' у категоріальний тип із правильним порядком
    month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    
    # Перетворюємо 'Сумма СИП' у числовий тип
    filtered_df['Сумма СИП'] = pd.to_numeric(filtered_df['Сумма СИП'], errors='coerce').fillna(0)
    
    # Перевіряємо наявність колонок
    required_columns = ['Наименование товаров', 'период', 'Сумма СИП']
    if not all(col in filtered_df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Видаляємо записи з пропусками в 'Наименование товаров' або 'период'
    filtered_df = filtered_df.dropna(subset=['Наименование товаров', 'период'])
    
    # Фільтруємо за вибраним списком періодів, якщо задано
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
        else:
            filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
    # Створюємо зведену таблицю
    pivot_table = pd.pivot_table(
        filtered_df,
        index='Наименование товаров',
        columns='период',
        values='Сумма СИП',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Итого'
    )
    
    # Ділимо всі значення на 4, залишаючи 0 там, де значення вже 0
    pivot_table = pivot_table.where(pivot_table == 0, pivot_table / 4)
    
    # Сортуємо стовпці (періоди) за порядком
    used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))
    pivot_table = pivot_table.reindex(columns=used_months + ['Итого']).round(0)
    
    # Переносимо 'Итого' в кінець індексу
    if 'Итого' in pivot_table.index:
        idx = pivot_table.index.tolist()
        idx.remove('Итого')
        idx.append('Итого')
        pivot_table = pivot_table.reindex(idx)
    
    return pivot_table