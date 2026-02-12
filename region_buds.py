import pandas as pd
import streamlit as st
from utils import MONTH_MAP

# ────────────────────── 1. КОНСТАНТИ ──────────────────────

PHARMACEUTICALS = [
    'Вибуркол супп рект № 12', 'Дискус композитум р-р для инъекций 2,2 мл № 5', 
    'Лимфомиозот амп 1,1 мл № 5', 'Лимфомиозот капли 30мл', 'Ньюрексан таблетки № 25', 
    'Ньюрексан таблетки № 50', 'Траумель С амп 2,2 мл № 5', 'Траумель С мазь 50г', 
    'Траумель С р-р для инъекций 2,2 мл № 100', 'Траумель С таблетки № 50', 
    'Цель Т амп 2 мл № 100', 'Цель Т амп № 5', 'Цель Т мазь 50г', 'Цель Т таблетки № 50', 
    'Церебрум композитум р-р д/инъек 2,2мл №10', 'Энгистол таблетки № 50',
]

SUPPLEMENTS_FOR_MP_BONUS = [
    'Витрум ретинорм капс. №90', 'Ксефомиелин таб. №30', 'Синулан Форте таб. №30'
]

TASHKENT_OBLAST_DISTRICTS = [
    'Алмалык', 'Ангрен', 'Ахангаран', 'Бекабад', 'Бостанлыкский', 'Бука',
    'Газалкент', 'Зангиата', 'Келес', 'Кибрай', 'Коканд', 'Паркент',
    'Пискент', 'Ташкент область', 'Чиноз', 'Чирчик', 'Янгиюль'
]

FOCUS_MANAGERS_AND_DISTRICTS = {
    'Бобоев Алишер и Хайиталиев Муслимбек': ['Самарканд'],
    'Хилола': ['Мирабадский', 'Учтепинский'],
    'Исмоилова Нозима Зокиржон кизи': ['Чиланзарский', 'Яшнабадский','Яккасарайский'],
    'Файзиева Дильфуза Дилшод кизи': ['Шайхантахурский', 'Алмазарский', 'Сергелийский'],
    'Нурутдинова Эвилина': ['Мирзо-Улугбекский', 'Юнусабадский'],
    'Мехманова Наргиза': ['Бухара']
}

EXCLUDED_MPS = ['Бады', 'Мед.Представитель', 'вакант']

# ────────────────────── 2. ДОПОМІЖНІ ФУНКЦІЇ ──────────────────────

def prep_df(df):
    df = df.copy()
    df['период'] = pd.to_datetime(df['период'], errors='coerce')
    df = df.dropna(subset=['период', 'Наименование товаров'])
    df['период'] = df['период'].dt.to_period('M').dt.to_timestamp()
    return df

def finalize_pivot(pivot, target_index=None):
    if pivot.empty: return pivot
    date_cols = sorted([c for c in pivot.columns if isinstance(c, pd.Timestamp)])
    if target_index:
        pivot = pivot.reindex(index=target_index, columns=date_cols, fill_value=0)
    else:
        pivot = pivot.reindex(columns=date_cols, fill_value=0)
    
    pivot['Итого'] = pivot.sum(axis=1)
    total_row = pivot.sum(axis=0).to_frame().T
    total_row.index = ['Итого']
    pivot = pd.concat([pivot, total_row])
    
    new_cols = {}
    for col in pivot.columns:
        if isinstance(col, pd.Timestamp):
            eng_m = col.strftime('%B')
            ru_m = MONTH_MAP.get(eng_m, eng_m)
            new_cols[col] = f"{ru_m} {col.year}"
    return pivot.rename(columns=new_cols).fillna(0).round(0).astype(int)

def style_table(df):
    return (df.style.format("{:,.0f}")
            .set_properties(**{'font-weight': 'bold', 'text-align': 'right', 'color': 'black'})
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#f0f2f6')]}
            ])
            .apply(lambda x: ['background-color: #e6f3e6' if (x.name == 'Итого' or c == 'Итого') else '' for c in x.index], axis=1))

# ────────────────────── 3. ФУНКЦІЇ РОЗРАХУНКУ ──────────────────────

def calculate_regional_pivot(df, districts, selected_period=None, value_column='кол-во'):
    """
    Звіт: Рядки - РЕГІОНИ, Стовпці - ПРЕПАРАТИ (БАДи).
    Додано сортування від більшого до меншого за значенням 'Итого'.
    """
    df = prep_df(df)
    df[value_column] = pd.to_numeric(df[value_column], errors='coerce').fillna(0)
    
    # 1. Фільтрація за районами та списком БАДів
    mask = (
        (df['район'].isin(districts)) & 
        (df['Наименование товаров'].isin(SUPPLEMENTS_FOR_MP_BONUS))
    )
    filtered = df[mask].copy()
    
    if selected_period is not None:
        filtered = filtered[filtered['период'].isin(selected_period)]
        
    if filtered.empty: 
        return pd.DataFrame()
    
    # 2. Створюємо таблицю: Рядки - Район, Стовпці - Товари
    pivot = pd.pivot_table(
        filtered, 
        index='район', 
        columns='Наименование товаров', 
        values=value_column, 
        aggfunc='sum', 
        fill_value=0
    )
    
    # 3. Гарантуємо, що всі 3 препарати є в стовпцях
    pivot = pivot.reindex(columns=SUPPLEMENTS_FOR_MP_BONUS, fill_value=0)
    
    # 4. Додаємо підсумок по рядках (Итого для кожного району)
    pivot['Итого'] = pivot.sum(axis=1)
    
    # --- НОВИЙ БЛОК: СОРТУВАННЯ ---
    # Сортуємо райони за спаданням (від більшого до меншого)
    pivot = pivot.sort_values(by='Итого', ascending=False)
    # ------------------------------
    
    # 5. Додаємо підсумковий рядок (Итого для всієї таблиці) в самий кінець
    total_row = pivot.sum(axis=0).to_frame().T
    total_row.index = ['Итого']
    
    final_df = pd.concat([pivot, total_row])
    
    return final_df.fillna(0).round(0).astype(int)

def calculate_excluded_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
    """Для вакантів: Товари vs Дати"""
    df = prep_df(df)
    filtered = df[df['МП'] == mp_name].copy()
    if selected_period is not None:
        filtered = filtered[filtered['период'].isin(selected_period)]
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    if filtered.empty: return pd.DataFrame()
    pivot = pd.pivot_table(filtered, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    return finalize_pivot(pivot)

def calculate_focus_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
    """Для БАД-менеджерів: Товари vs Дати"""
    target_districts = FOCUS_MANAGERS_AND_DISTRICTS.get(mp_name, [])
    df = prep_df(df)
    if selected_period is not None:
        df = df[df['период'].isin(selected_period)]
    filtered = df[(df['МП'] == mp_name) & (df['район'].isin(target_districts)) & (df['Наименование товаров'].isin(SUPPLEMENTS_FOR_MP_BONUS))].copy()
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    if filtered.empty: return pd.DataFrame()
    pivot = pd.pivot_table(filtered, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    return finalize_pivot(pivot, target_index=SUPPLEMENTS_FOR_MP_BONUS)