import pandas as pd
import streamlit as st
from utils import MONTH_MAP


PHARMACEUTICALS = [
    'Вибуркол супп рект № 12', 'Дискус композитум р-р для инъекций 2,2 мл № 5', 
    'Лимфомиозот амп 1,1 мл № 5', 'Лимфомиозот капли 30мл', 'Ньюрексан таблетки № 25', 
    'Ньюрексан таблетки № 50', 'Траумель С амп 2,2 мл № 5', 'Траумель С мазь 50г', 
    'Траумель С р-р для инъекций 2,2 мл № 100', 'Траумель С таблетки № 50', 
    'Цель Т амп 2 мл № 100', 'Цель Т амп № 5', 'Цель Т мазь 50г', 'Цель Т таблетки № 50', 
    'Церебрум композитум р-р д/инъек 2,2мл №10', 'Энгистол таблетки № 50',
]

SUPPLEMENTS_FOR_MP_BONUS = [
    'Витрум ретинорм капс. №90',
    'Ксефомиелин таб. №30',
    'Синулан Форте таб. №30'
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

# ────────────────────── ДОПОМІЖНІ ФУНКЦІЇ ──────────────────────

def is_focus_manager(mp_name):
    return mp_name in FOCUS_MANAGERS_AND_DISTRICTS

def is_excluded(mp_name):
    if not mp_name: return False
    name_low = str(mp_name).lower()
    return any(excl.lower() in name_low for excl in EXCLUDED_MPS)

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

# ────────────────────── ФУНКЦІЇ РОЗРАХУНКУ ──────────────────────

def calculate_excluded_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
    df = prep_df(df)
    filtered = df[df['МП'] == mp_name].copy()
    if selected_period is not None:
        filtered = filtered[filtered['период'].isin(selected_period)]
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    if filtered.empty: return pd.DataFrame()
    pivot = pd.pivot_table(filtered, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    return finalize_pivot(pivot)

def calculate_mp_pivot_with_bonus(df, mp_name, selected_period=None, value_column='кол-во'):
    if is_focus_manager(mp_name): return pd.DataFrame()
    df = prep_df(df)
    df[value_column] = pd.to_numeric(df[value_column], errors='coerce').fillna(0)
    if selected_period is not None:
        df = df[df['период'].isin(selected_period)]
    direct = df[df['МП'] == mp_name].copy()
    if direct.empty: return pd.DataFrame()
    active_months = direct['период'].unique()
    bonus_mask = (df['период'].isin(active_months)) & (df['Наименование товаров'].isin(PHARMACEUTICALS))
    t_bonus = df[bonus_mask & (df['район'] == 'Ташкент')].copy()
    o_bonus = df[bonus_mask & (df['район'].isin(TASHKENT_OBLAST_DISTRICTS))].copy()
    combined = direct[['Наименование товаров', 'период', value_column]].copy()
    for b_df in [t_bonus, o_bonus]:
        if not b_df.empty:
            b_grouped = b_df.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
            b_grouped[value_column] = b_grouped[value_column] / 4
            combined = pd.concat([combined, b_grouped])
    pivot = pd.pivot_table(combined, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    return finalize_pivot(pivot)

def calculate_focus_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
    target_districts = FOCUS_MANAGERS_AND_DISTRICTS.get(mp_name, [])
    df = prep_df(df)
    if selected_period is not None:
        df = df[df['период'].isin(selected_period)]
    filtered = df[(df['МП'] == mp_name) & (df['район'].isin(target_districts)) & (df['Наименование товаров'].isin(SUPPLEMENTS_FOR_MP_BONUS))].copy()
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors='coerce').fillna(0)
    pivot = pd.pivot_table(filtered, index='Наименование товаров', columns='период', values=value_column, aggfunc='sum', fill_value=0)
    return finalize_pivot(pivot, target_index=SUPPLEMENTS_FOR_MP_BONUS)