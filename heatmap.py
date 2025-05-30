import pandas as pd

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# Мапінг МП → райони
mp_district_mapping = {
    'Отабек': ['Мирабадский', 'Яшнабадский', 'Яккасарайский', 'Бектимирский'],
    'Шахноза': ['Мирзо-Улугбекский', 'Юнусабадский'],
    'Шаходат': ['Алмазарский', 'Шайхантахурский'],
    'Нилуфар': ['Кашкадарья'],
    'вакант': ['Чиланзарский', 'Учтепинский', 'Сергелийский', 'Янгихает'],
    'вакант Самарканд': ['Самарканд']
}

def calculate_district_heatmap(df, districts, selected_period=None, value_column='кол-во'):
    """
    Створює зведену таблицю для теплової карти для списку районів, агрегуючи по товарах.
    
    Parameters:
    -----------
    df: DataFrame з даними (аркуш 'Продажи')
    districts: список районів
    selected_period: список періодів або None для всіх періодів
    value_column: стовпець для агрегації ('кол-во' або 'Сумма СИП')
    
    Returns:
    --------
    pandas.DataFrame: зведена таблиця з районами (індекс) і періодами (стовпці)
    """
    required_columns = ['Наименование товаров', 'период', 'район', value_column]
    if not all(col in df.columns for col in required_columns):
        raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
    # Копіюємо дані
    df = df.copy()
    df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)
    
    # Фільтрація за періодом
    if selected_period:
        if isinstance(selected_period, list):
            filtered_df = df[df['период'].isin(selected_period)]
        else:
            filtered_df = df[df['период'] == selected_period]
    else:
        filtered_df = df
    
    # Перетворюємо значення в числові
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    # Фільтруємо за районами
    district_subset = filtered_df[filtered_df['район'].isin(districts)]
    
    if district_subset.empty:
        return pd.DataFrame()
    
    # Групуємо по району, періоду, підсумовуючи по товарах
    grouped_df = district_subset.groupby(['район', 'период'])[value_column].sum().reset_index()
    
    # Визначаємо місяці з ненульовими даними
    used_months = sorted(
        grouped_df[grouped_df[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    
    if not used_months:
        return pd.DataFrame()
    
    # Створюємо зведену таблицю
    pivot_table = pd.pivot_table(
        grouped_df,
        index='район',
        columns='период',
        values=value_column,
        aggfunc='sum',
        fill_value=0
    )
    
    # Сортуємо за місяцями
    pivot_table = pivot_table.reindex(columns=used_months)
    
    # Сортуємо райони за порядком у districts
    pivot_table = pivot_table.reindex(index=[d for d in districts if d in pivot_table.index])
    
    return pivot_table