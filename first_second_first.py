import streamlit as st
import pandas as pd
from utils import БАДЫ, ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ

# month_order залишається тут
month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# ─────────────────────── НОВА ФУНКЦІЯ (повністю безпечна) ───────────────────────
def create_pivot_by_group(df, selected_period=None):
    df = df.copy()
    df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)

    # фільтр по періоду
    if selected_period:
        if isinstance(selected_period, list):
            df = df[df['период'].isin(selected_period)]
        else:
            df = df[df['период'] == selected_period]

    df['кол-во'] = pd.to_numeric(df['кол-во'], errors='coerce').fillna(0)
    df['Сумма СИП'] = pd.to_numeric(df['Сумма СИП'], errors='coerce').fillna(0)

    used_months = sorted(
        df[df['кол-во'] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )

    def make_pivot(group_df):
        if group_df.empty:
            cols = used_months + ['Итого'] if used_months else ['Итого']
            empty = pd.DataFrame(0, index=['Итого'], columns=cols, dtype=int)
            return empty, empty.copy()

        # кількість
        qty = pd.pivot_table(group_df, index='Наименование товаров', columns='период',
                             values='кол-во', aggfunc='sum', fill_value=0)
        qty = qty.reindex(columns=used_months, fill_value=0)
        qty['Итого'] = qty.sum(axis=1)
        total_qty = qty.sum().to_frame().T
        total_qty.index = ['Итого']
        qty = pd.concat([qty, total_qty]).round(0).astype(int)

        # сума
        suma = pd.pivot_table(group_df, index='Наименование товаров', columns='период',
                              values='Сумма СИП', aggfunc='sum', fill_value=0)
        suma = suma.reindex(columns=used_months, fill_value=0)
        suma['Итого'] = suma.sum(axis=1)
        total_suma = suma.sum().to_frame().T
        total_suma.index = ['Итого']
        suma = pd.concat([suma, total_suma]).round(0).astype(int)

        return qty, suma

    # дві групи
    qty_bad, sum_bad = make_pivot(df[df['Наименование товаров'].isin(БАДЫ)])
    qty_lek, sum_lek = make_pivot(df[df['Наименование товаров'].isin(ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ)])

    return qty_bad, sum_bad, qty_lek, sum_lek, used_months