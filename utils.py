# utils.py  ← лежить в тій самій папці, що й твій heel_app.py
import pandas as pd

БАДЫ = [
    "Витрум ретинорм капс. №90",
    "Ксефомиелин таб. №30",
    "Синулан Форте таб. №30"
]

ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ = [
    "Вибуркол супп рект № 12",
    "Дискус композитум р-р для инъекций 2,2 мл № 5",
    "Лимфомиозот амп 1,1 мл № 5",
    "Лимфомиозот капли 30мл",
    "Ньюрексан таблетки № 25",
    "Ньюрексан таблетки № 50",
    "Траумель С амп 2,2 мл № 5",
    "Траумель С мазь 50г",
    "Траумель С р-р для инъекций 2,2 мл № 100",
    "Траумель С таблетки № 50",
    "Цель Т амп 2 мл № 100",
    "Цель Т амп № 5",
    "Цель Т мазь 50г",
    "Цель Т таблетки № 50",
    "Церебрум композитум р-р д/инъек 2,2мл №10",
    "Энгистол таблетки № 50"
]

MONTH_MAP = {
    'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
    'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
    'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
    'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
}

def format_pivot_titles_ru(pivot_df):
    """Перекладає англійські назви місяців у заголовках на російські."""
    if pivot_df.empty: return pivot_df
    new_cols = {}
    for col in pivot_df.columns:
        if isinstance(col, pd.Timestamp):
            eng_month = col.strftime('%B')
            ru_month = MONTH_MAP.get(eng_month, eng_month)
            new_cols[col] = f"{ru_month} {col.year}"
    return pivot_df.rename(columns=new_cols)

def finalize_report(pivot):
    """Сортування, підсумки та переклад."""
    if pivot.empty: return pivot
    
    # Сортування колонок-дат (залишаємо 'Итого' в кінці)
    date_cols = sorted([c for c in pivot.columns if isinstance(c, pd.Timestamp)])
    final_cols = date_cols + (['Итого'] if 'Итого' in pivot.columns else [])
    pivot = pivot.reindex(columns=final_cols)
    
    # Переклад місяців
    pivot = format_pivot_titles_ru(pivot)
    
    # Округлення та цілі числа
    return pivot.fillna(0).round(0).astype(int)