import pandas as pd
import numpy as np

# ────────────────────── КОНСТАНТИ ──────────────────────

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# 1. ЛІКИ: Препарати, що підлягають бонусній логіці (Ташкент + Область /4)
PHARMACEUTICALS = [
    'Вибуркол супп рект № 12', 'Дискус композитум р-р для инъекций 2,2 мл № 5', 
    'Лимфомиозот амп 1,1 мл № 5', 'Лимфомиозот капли 30мл', 'Ньюрексан таблетки № 25', 
    'Ньюрексан таблетки № 50', 'Траумель С амп 2,2 мл № 5', 'Траумель С мазь 50г', 
    'Траумель С р-р для инъекций 2,2 мл № 100', 'Траумель С таблетки № 50', 
    'Цель Т амп 2 мл № 100', 'Цель Т амп № 5', 'Цель Т мазь 50г', 'Цель Т таблетки № 50', 
    'Церебрум композитум р-р д/инъек 2,2мл №10', 'Энгистол таблетки № 50',
]

# 2. БАДИ: 3 Фокусні препарати для нових менеджерів (ФІО)
SUPPLEMENTS_FOR_MP_BONUS = [
    'Витрум ретинорм капс. №90',
    'Ксефомиелин таб. №30',
    'Синулан Форте таб. №30'
]

# Райони Ташкентської області (для бонусу)
TASHKENT_OBLAST_DISTRICTS = [
    'Алмалык', 'Ангрен', 'Ахангаран', 'Бекабад', 'Бостанлыкский', 'Бука',
    'Газалкент', 'Зангиата', 'Келес', 'Кибрай', 'Коканд', 'Паркент',
    'Пискент', 'Ташкент область', 'Чиноз', 'Чирчик', 'Янгиюль'
]

# Словник "МП": [Список районів] для нових фокусних менеджерів
FOCUS_MANAGERS_AND_DISTRICTS = {
    'Мирзаева Гавхар Абдуразаковна': ['Мирабадский', 'Мирзо-Улугбекский'],
    'Исмоилова Нозима Зокиржон кизи': ['Чиланзарский', 'Яшнабадский', 'Яккасарайский'],
    'Файзиева Дильфуза Дилшод кизи': ['Шайхантахурский', 'Алмазарский', 'Сергелийский'],
    'Нурутдинова Эвилина': ['Учтепинский', 'Юнусабадский']
}


# ────────────────────── ФУНКЦІЇ КЛАСИФІКАЦІЇ ──────────────────────

def is_excluded(mp_name):
    """Визначає, чи є МП 'вакант' або 'бады'."""
    return 'вакант' in str(mp_name).lower() or 'бады' in str(mp_name).lower()

def is_focus_manager(mp_name):
    """Визначає, чи є МП новим фокусним менеджером (за ФІО)."""
    return mp_name in FOCUS_MANAGERS_AND_DISTRICTS

# ────────────────────── ФУНКЦІЇ РОЗРАХУНКУ ──────────────────────

def calculate_excluded_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во', focus_products=None):
    """Розрахунок для 'вакант' / 'бады'. Показує ВСІ продукти."""
    filtered = df[df['МП'] == mp_name].copy()

    if selected_period:
        if isinstance(selected_period, list):
            filtered = filtered[filtered['период'].isin(selected_period)]
        else:
            filtered = filtered[filtered['период'] == selected_period]
    
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    if filtered.empty: return pd.DataFrame()
    
    used_months = sorted(filtered['период'].unique(), key=lambda x: month_order.index(x))
    pivot = pd.pivot_table(filtered, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    
    if pivot.empty: return pd.DataFrame()
    pivot = pivot.reindex(columns=used_months)
    pivot['Итого'] = pivot.sum(axis=1)
    total_row = pd.DataFrame(pivot.sum()).T
    total_row.index = ['Итого']
    return pd.concat([pivot, total_row]).astype(int)

def calculate_mp_pivot_with_bonus(df, mp_name, selected_period=None, value_column='кол-во'):
    """
    Розрахунок для стандартних МП.
    !!! ІГНОРУЄ фокусних ФІО-менеджерів, щоб уникнути дублювання !!!
    """
    if mp_name in FOCUS_MANAGERS_AND_DISTRICTS:
        return pd.DataFrame()
    
    filtered = df.copy()
    if selected_period:
        if isinstance(selected_period, list):
            filtered = filtered[filtered['период'].isin(selected_period)]
        else:
            filtered = filtered[filtered['период'] == selected_period]
    
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    direct = filtered[filtered['МП'] == mp_name]
    
    # ... (логіка бонусу Ташкент/Область, не змінюємо) ...
    active_months = direct['период'].dropna().unique()
    tashkent_bonus = filtered[
        (filtered['район'] == 'Ташкент') & (filtered['период'].isin(active_months)) &
        (filtered['Наименование товаров'].isin(PHARMACEUTICALS))
    ].copy()
    if not tashkent_bonus.empty:
        tashkent_bonus = tashkent_bonus.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
        tashkent_bonus[value_column] = (tashkent_bonus[value_column] / 4).round(0)
    
    oblast_bonus = filtered[
        (filtered['район'].isin(TASHKENT_OBLAST_DISTRICTS)) & (filtered['период'].isin(active_months)) &
        (filtered['Наименование товаров'].isin(PHARMACEUTICALS))
    ].copy()
    if not oblast_bonus.empty:
        oblast_bonus = oblast_bonus.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
        oblast_bonus[value_column] = (oblast_bonus[value_column] / 4).round(0)
    
    result = direct.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
    for bonus_df in [tashkent_bonus, oblast_bonus]:
        if not bonus_df.empty:
            result = result.merge(bonus_df, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_bonus'))
            result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_bonus'].fillna(0)
            result = result.drop(columns=[c for c in result.columns if c.endswith('_bonus')], errors='ignore')
    
    result[value_column] = result[value_column].round(0).astype(int)
    if result.empty: return pd.DataFrame()
    used_months = sorted(result['период'].unique(), key=lambda x: month_order.index(x))
    pivot = pd.pivot_table(result, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    pivot = pivot.reindex(columns=used_months)
    pivot['Итого'] = pivot.sum(axis=1)
    total_row = pd.DataFrame(pivot.sum()).T
    total_row.index = ['Итого']
    return pd.concat([pivot, total_row])


def calculate_focus_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
    """Розрахунок для нових фокусних МП (ФІО) за 3 БАДами та їхніми районами."""
    
    target_districts = FOCUS_MANAGERS_AND_DISTRICTS.get(mp_name, [])
    target_products = SUPPLEMENTS_FOR_MP_BONUS 
    
    if not target_districts:
        return pd.DataFrame()

    filtered = df[
        (df['МП'] == mp_name) & # Фільтруємо лише по цьому МП
        (df['район'].isin(target_districts)) & 
        (df['Наименование товаров'].isin(target_products))
    ].copy()

    if selected_period:
        if isinstance(selected_period, list):
            filtered = filtered[filtered['период'].isin(selected_period)]
        else:
            filtered = filtered[filtered['период'] == selected_period]

    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    
    # ... (логіка зведеної таблиці) ...
    if filtered.empty:
        unique_periods = df['период'].dropna().unique()
        # Якщо даних немає, створюємо порожню таблицю з потрібними назвами товарів
        cols = sorted(unique_periods, key=lambda x: month_order.index(x)) if unique_periods.size > 0 else ['Январь']
        empty_pivot = pd.DataFrame(0, index=target_products, columns=cols)
        empty_pivot['Итого'] = 0
        total_row = pd.DataFrame(empty_pivot.sum()).T
        total_row.index = ['Итого']
        return pd.concat([empty_pivot, total_row]).astype(int)

    used_months = sorted(filtered['период'].unique(), key=lambda x: month_order.index(x))
    pivot = pd.pivot_table(filtered, index='Наименование товаров', columns='период',
                           values=value_column, aggfunc='sum', fill_value=0)
    
    pivot = pivot.reindex(columns=used_months)
    pivot['Итого'] = pivot.sum(axis=1)
    pivot = pivot.reindex(target_products).fillna(0)
    
    total_row = pd.DataFrame(pivot.sum()).T
    total_row.index = ['Итого']
    
    return pd.concat([pivot, total_row]).astype(int)