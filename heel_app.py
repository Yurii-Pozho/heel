import streamlit as st
import pandas as pd
from eco_lec_sales import process_data
from first_second_first import create_pivot_by_group
from source import generate_source_pivots
from region import generate_region_period_pivot
from tashkent import generate_tashkent_pivot, generate_tashkent_sum_sip_pivot,generate_tashkent_divided_pivot, generate_tashkent_sum_sip_divided_pivot
from tashkent_oblast import generate_other_districts_sum_sip_divided_pivot, generate_other_districts_sum_sip_pivot,OBLAST_DISTRICTS,generate_other_districts_divided_pivot, generate_other_districts_pivot
from mp import (
    PHARMACEUTICALS,
    is_excluded,
    calculate_mp_pivot_with_bonus,
    calculate_excluded_mp_pivot
)
from heatmap import calculate_district_heatmap, mp_district_mapping,ALL_MP_DISTRICTS
from region_buds import calculate_regional_pivot,prep_df,SUPPLEMENTS_FOR_MP_BONUS
from stocks import calculate_source_pivot
from utils import БАДЫ, ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ,MONTH_MAP 
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from pathlib import Path


st.set_page_config(layout="wide")

# Функція для перетворення зображення на Base64 (необхідна для використання в st.markdown)
def img_to_base64(img_path):
    # ПЕРЕВІРТЕ ПРАВИЛЬНИЙ ШЛЯХ до вашого файлу "sticker.jpg"
    try:
        img_bytes = Path(img_path).read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        return encoded
    except FileNotFoundError:
        st.error("Файл 'sticker.jpg' не знайдено.")
        return None

img_base64 = img_to_base64("sticker.jpg")

if img_base64:
    st.markdown(
        f"""
        <style>
            /* 1. Перевизначаємо CSS Streamlit, щоб видалити максимальну ширину */
            /* Це впливає на більшу частину вмісту на сторінці */
            .main .block-container {{
                max-width: 100% !important;
                padding-left: 0rem;
                padding-right: 0rem;
            }}

            /* 2. Стилі для контейнера зображення */
            .full-width-image-container {{
                display: flex;
                justify-content: center;
                /* Якщо потрібно, щоб він розтягувався на всю ширину (100% viewport width) */
                width: 100vw; 
                margin-left: calc(-50vw + 50%); /* Компенсуємо зміщення, щоб вийти за межі */
            }}
        </style>

        <div class="full-width-image-container">
            <img src="data:image/jpeg;base64,{img_base64}" style="max-height: 300px; width: auto; object-fit: contain; margin-bottom: 20px;">
        </div>
        """,
        unsafe_allow_html=True
    )

# Завантаження файлу
uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "csv"])
if not uploaded_file:
    st.warning("Пожалуйста, загрузите файл с данными.")
    st.stop()

# --- ЗАВАНТАЖЕННЯ ДАНИХ ---
sales_df = None
stocks_df = None

if uploaded_file.name.endswith(".xlsx"):
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    
    if "Продажи" in sheet_names:
        sales_df = pd.read_excel(uploaded_file, sheet_name="Продажи")
        sales_df['период'] = pd.to_datetime(sales_df['период'])
    
    if "Стоки" in sheet_names:
        stocks_df = pd.read_excel(uploaded_file, sheet_name="Стоки")
        if 'период' in stocks_df.columns:
            stocks_df['период'] = pd.to_datetime(stocks_df['период'])
else:
    # Обробка CSV
    sales_df = pd.read_csv(uploaded_file)
    sales_df['период'] = pd.to_datetime(sales_df['период'])

# Перевірка наявності даних продажів
if sales_df is None:
    st.error("Аркуш 'Продажи' не знайдено в файлі.")
    st.stop()

# --- ГЛОБАЛЬНИЙ ФІЛЬТР РОКУ (ЗАМІСТЬ SIDEBAR) ---
# Розміщуємо вибір року прямо в основному вікні
available_years = sorted(sales_df['период'].dt.year.unique(), reverse=True)
selected_year = st.selectbox("📅 Выберите год", available_years)

# Фільтруємо основні датафрейми за обраним роком
sales_df = sales_df[sales_df['период'].dt.year == selected_year]

if stocks_df is not None and 'период' in stocks_df.columns:
    stocks_df = stocks_df[stocks_df['период'].dt.year == selected_year]

# --- ПЕРЕВІРКА КОЛОНОК ТА ОБРОБКА ---
required_columns = ['регион', 'район', 'период', 'кол-во', 'Сумма СИП', 'источник']
missing_columns = [col for col in required_columns if col not in sales_df.columns]

if missing_columns:
    st.error(f"В данных отсутствуют необходимые колонки: {missing_columns}")
    st.stop()

# Обробка даних через вашу функцію process_data
filtered_df, pivot_qty, pivot_sum, used_months = process_data(sales_df)

if filtered_df is None:
    st.warning(f"Нет данных для источника 'Первичка' за {selected_year} год.")
    st.stop()

# --- СТВОРЕННЯ ВКЛАДОК ---
tabs = st.tabs([
    "📋 Данные продаж",
    "📋 Данные стоков",
    "📈 Остатки",
    "🏭 Первичка + вторичка - первичка",
    "📈 Источники по периодам",
    "🌐 Eco Lec продажи",
    "🏢 Регионы",
    "📊 Ташкент",
    "📊 Ташкентская область",
    "⚕️ МП (HEEL)", 
    # "💊 МП (БАДы)",
    "🏢 Регионы (DORIM 360)",
    "🌆 Тепловая карта по районам"
])

# Вкладка для даних продажів
with tabs[0]:
    st.markdown("### Данные продажи")
    st.dataframe(sales_df, use_container_width=True)
# Вкладка для даних стоків
with tabs[1]:
    st.markdown("### Данные остатки")
    if stocks_df is not None:
        st.dataframe(stocks_df, use_container_width=True)
    else:
        st.warning("Аркуш 'Стоки' не знайдено в файлі Excel.")
# Сводная стоки        
with tabs[2]:
    st.markdown("### Сводная таблица по источникам (Стоки)")
    
    # Твій CSS стиль
    st.markdown("""
        <style>
            [data-testid="stTable"] th { font-weight: bold !important; color: black !important; background-color: #f0f2f6 !important; }
            [data-testid="stTable"] td { font-weight: bold !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    if stocks_df is None:
        st.warning("Лист 'Стоки' не найден.")
        st.stop()

    # Попередня підготовка дат для інтерфейсу
    temp_stocks = stocks_df.copy()
    temp_stocks['период'] = pd.to_datetime(temp_stocks['период'], errors='coerce')
    temp_stocks = temp_stocks.dropna(subset=['период'])
    temp_stocks['период'] = temp_stocks['период'].dt.to_period('M').dt.to_timestamp()
    
    # Отримуємо унікальні дати хронологічно
    raw_months = sorted(temp_stocks['период'].unique())
    
    # Генеруємо російські мітки для слайдера
    month_labels = [
        f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}" 
        for m in raw_months
    ]
    
    if not month_labels:
        st.error("В листе 'Стоки' нет корректных дат.")
        st.stop()

    # Вибір показника
    v_type = st.radio("Показатель", ["Количество", "Сумма СИП"], horizontal=True, key="src_v_type")
    v_col = 'кол-во' if v_type == "Количество" else 'Сумма СИП'
    
    # Слайдер періоду
    slider_opts = ['Все'] + month_labels
    p_range = st.select_slider("Выберите диапазон дат", options=slider_opts, value=('Все', slider_opts[-1]), key="src_slider")
    
    if p_range[0] == 'Все':
        selected_p = raw_months
    else:
        idx_s = month_labels.index(p_range[0])
        idx_e = month_labels.index(p_range[1])
        selected_p = raw_months[idx_s : idx_e + 1]

    # Вибір джерела
    sources = sorted(stocks_df['источник'].dropna().unique().tolist())
    selected_source = st.selectbox("Выберите источник", ["Все источники"] + sources)

    # Функція стилізації (з твоїми кольорами та шрифтами)
    def style_stock_pivot(df):
        if df is None or df.empty:
            return pd.DataFrame().style
        return (df.style.format("{:,.0f}", na_rep='0')
                .set_properties(**{
                    'text-align': 'right', 
                    'font-size': '14px', 
                    'font-weight': 'bold', 
                    'color': 'black'
                })
                .set_table_styles([
                    {'selector': 'th.row_heading', 'props': [('font-weight', 'bold'), ('text-align', 'left')]}
                ])
                .set_properties(**{
                    'background-color': '#f0f0f0', 
                    'color': '#006400'
                }, subset=pd.IndexSlice[df.index == 'Итого', :])
                .set_properties(**{
                    'background-color': '#f0f0f0', 
                    'color': '#006400'
                }, subset=pd.IndexSlice[:, df.columns == 'Итого']))

    # Вивід таблиць
    def render_source(name):
        st.markdown(f"#### {name}")
        tbl = calculate_source_pivot(stocks_df, name, selected_p, value_column=v_col)
        if tbl.empty:
            st.caption("Нет данных")
        else:
            st.table(style_stock_pivot(tbl))

    # Логіка відображення
    if selected_source == "Все источники":
        for s in sources:
            render_source(s)
            st.divider()
    else:
        render_source(selected_source)
# Вкладка "Первичка + вторичка - первичка"
with tabs[3]:
    # 1. Твій CSS для примусового жирного шрифту
    st.markdown("""
        <style>
            [data-testid="stTable"] th { font-weight: bold !important; color: black !important; background-color: #f0f2f6 !important; }
            [data-testid="stTable"] td { font-weight: bold !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    # === Слайдер періоду ===
    temp_df = sales_df.copy()
    temp_df['период'] = pd.to_datetime(temp_df['период'], errors='coerce')
    temp_df = temp_df.dropna(subset=['период'])
    temp_df['период'] = temp_df['период'].dt.to_period('M').dt.to_timestamp()
    temp_df['кол-во'] = pd.to_numeric(temp_df['кол-во'], errors='coerce').fillna(0)

    # Отримуємо унікальні дати хронологічно
    raw_months = sorted(temp_df[temp_df['кол-во'] > 0]['период'].unique())
    
    # Створюємо російські мітки для слайдера через MONTH_MAP
    from utils import MONTH_MAP
    display_labels = [f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}" for m in raw_months]

    if not display_labels:
        st.write("Нет данных за выбранный период")
    else:
        all_labels = ['Все'] + display_labels

        period_range = st.select_slider(
            "Выберите диапазон дат",
            options=all_labels,
            value=(all_labels[0], all_labels[-1]),
            key="items_period_slider"
        )
        
        if period_range[0] == 'Все':
            selected_period = raw_months
        else:
            idx_start = display_labels.index(period_range[0])
            idx_end = display_labels.index(period_range[1])
            selected_period = raw_months[idx_start : idx_end + 1]

        # Розрахунок
        qty_bad, sum_bad, qty_lek, sum_lek, _ = create_pivot_by_group(sales_df, selected_period)

    # === Твоя функція стилізації (без змін) ===
    def styled(df):
        if df is None or df.empty:
            return pd.DataFrame().style
        return (df.style.format("{:,.0f}", na_rep='')
                .set_properties(**{'text-align': 'right', 'font-size': '14px', 'font-weight': 'bold', 'color': 'black'})
                .set_table_styles([{'selector': 'th.row_heading', 'props': [('font-weight', 'bold'), ('text-align', 'left')]}])
                .set_properties(**{'background-color': '#f0f0f0', 'color': '#006400'}, subset=pd.IndexSlice[df.index == 'Итого', :])
                .set_properties(**{'background-color': '#f0f0f0', 'color': '#006400'}, subset=pd.IndexSlice[:, df.columns == 'Итого']))

    # ====================== ВИВІД ======================
    st.markdown("### DORIM 360")
    if qty_bad is not None and not qty_bad.empty:
        st.markdown("**Количество**"); st.table(styled(qty_bad))
        st.markdown("**Сумма СИП**"); st.table(styled(sum_bad))
    else:
        st.write("Данные по БАДам отсутствуют")

    st.divider()

    st.markdown("### HEEL")
    if qty_lek is not None and not qty_lek.empty:
        st.markdown("**Количество**"); st.table(styled(qty_lek))
        st.markdown("**Сумма СИП**"); st.table(styled(sum_lek))
    else:
        st.write("Данные по лекарствам отсутствуют")
# Вкладка "Источники по периодам"
with tabs[4]:
    st.markdown("### Сводная таблица: Продажи по источникам")

    # CSS для стилізації (залишаємо ваш)
    st.markdown("""
        <style>
            [data-testid="stTable"] th { font-weight: bold !important; color: black !important; background-color: #f0f2f6 !important; }
            [data-testid="stTable"] td { font-weight: bold !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    # 1. Підготовка періодів (використовуємо вашу логіку)
    temp_df = sales_df.copy()
    temp_df['период'] = pd.to_datetime(temp_df['период'], errors='coerce')
    temp_df = temp_df.dropna(subset=['период'])
    temp_df['период'] = temp_df['период'].dt.to_period('M').dt.to_timestamp()
    
    raw_months = sorted(temp_df['период'].unique())
    month_labels = [f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}" for m in raw_months]

    if not month_labels:
        st.warning("Нет данных для отображения.")
    else:
        # Слайдер дат (спільний для обох блоків)
        slider_opts = ['Все'] + month_labels
        period_range = st.select_slider(
            "Выберите диапазон дат для всех таблиц",
            options=slider_opts,
            value=('Все', slider_opts[-1]),
            key="src_sales_slider_global"
        )
        
        if period_range[0] == 'Все':
            selected_period = raw_months
        else:
            idx_s = month_labels.index(period_range[0])
            idx_e = month_labels.index(period_range[1])
            selected_period = raw_months[idx_s : idx_e + 1]

        # Допоміжна функція стилізації
        def style_source_pivot(df):
            if df is None or df.empty:
                return pd.DataFrame().style
            return (df.style.format("{:,.0f}", na_rep='')
                    .set_properties(**{'text-align': 'right', 'font-size': '14px', 'font-weight': 'bold', 'color': 'black'})
                    .set_table_styles([{'selector': 'th.row_heading', 'props': [('font-weight', 'bold'), ('text-align', 'left')]}])
                    .set_properties(**{'background-color': '#f0f0f0', 'color': '#006400'}, subset=pd.IndexSlice[df.index == 'Итого', :])
                    .set_properties(**{'background-color': '#f0f0f0', 'color': '#006400'}, subset=pd.IndexSlice[:, df.columns == 'Итого']))

        # --- БЛОК 1: ЛЕКАРСТВЕННЫЕ ПРЕПАРАТЫ ---
        st.header("💊 HEEL")
        qty_drugs, sum_drugs = generate_source_pivots(sales_df, selected_period, category='drugs')
        
        col1, col2 = st.columns(1), st.columns(1) # Для розділення візуально
        st.markdown("##### Кол-во (Лекарства)")
        st.table(style_source_pivot(qty_drugs))
        
        st.markdown("##### Сумма СИП (Лекарства)")
        st.table(style_source_pivot(sum_drugs))

        st.markdown("<br><hr><br>", unsafe_allow_html=True) # Великий роздільник

        # --- БЛОК 2: БАДы ---
        st.header("🌿 DORIM 360")
        qty_supps, sum_supps = generate_source_pivots(sales_df, selected_period, category='supplements')
        
        st.markdown("##### Кол-во (DORIM 360)")
        if not qty_supps.empty:
            st.table(style_source_pivot(qty_supps))
        else:
            st.info("Нет данных по БАДам за этот период")
        
        st.markdown("##### Сумма СИП (DORIM 360)")
        if not sum_supps.empty:
            st.table(style_source_pivot(sum_supps))
        else:
            st.info("Нет данных по БАДам за этот период")
# Вкладка "Eco Lec продажи
with tabs[5]:
    st.markdown("### Сводная таблица и график по 'Первичка'")

    # 1. Твій CSS для примусового жирного шрифту (залишаємо без змін)
    st.markdown("""
        <style>
            [data-testid="stTable"] th { 
                font-weight: bold !important; 
                color: black !important; 
                background-color: #f0f2f6 !important; 
            }
            [data-testid="stTable"] td { 
                font-weight: bold !important; 
                color: black !important; 
            }
        </style>
    """, unsafe_allow_html=True)

    # --- ПІДГОТОВКА ДАНИХ ДЛЯ СЛАЙДЕРА (з російськими назвами) ---
    temp_p = sales_df[sales_df['источник'] == 'Первичка'].copy()
    temp_p['период'] = pd.to_datetime(temp_p['период'], errors='coerce')
    temp_p = temp_p.dropna(subset=['период'])
    temp_p['период'] = temp_p['период'].dt.to_period('M').dt.to_timestamp()
    
    actual_dates = sorted(temp_p['период'].unique())
    # Формуємо мітки "Январь 2025"
    actual_labels = [f"{MONTH_MAP.get(d.strftime('%B'), d.strftime('%B'))} {d.year}" for d in actual_dates]

    if not actual_labels:
        st.warning("В данных 'Первичка' не найдено корректных дат.")
    else:
        # === Слайдер з твоїми налаштуваннями ===
        period_options = ['Все'] + actual_labels
        period_range = st.select_slider(
            "Выберите диапазон дат",
            options=period_options,
            value=('Все', period_options[-1]),
            key="period_slider_tab5_primary"
        )
        
        # Конвертуємо вибір назад у Timestamp для розрахунків
        if period_range[0] == 'Все':
            selected_period = actual_dates
        else:
            start_idx = actual_labels.index(period_range[0])
            end_idx = actual_labels.index(period_range[1])
            selected_period = actual_dates[start_idx : end_idx + 1]

        # === Твоя функція стилізації (styled) — без змін ===
        def styled(df):
            if df is None or df.empty:
                return pd.DataFrame().style
            return (df.style.format("{:,.0f}")
                    .set_properties(**{
                        'text-align': 'right',
                        'font-size': '14px',
                        'font-weight': 'bold',
                        'color': 'black'
                    })
                    .set_table_styles([
                        {'selector': 'th.row_heading', 'props': [('font-weight', 'bold'), ('text-align', 'left')]}
                    ])
                    .set_properties(**{
                        'font-weight': 'bold',
                        'background-color': '#f0f0f0',
                        'color': '#006400'
                    }, subset=pd.IndexSlice[df.index == 'Итого', :])
                    .set_properties(**{
                        'font-weight': 'bold',
                        'background-color': '#f0f0f0',
                        'color': '#006400'
                    }, subset=pd.IndexSlice[:, df.columns == 'Итого'])
            )

        # === Виклик функцій розрахунку ===
        df_bad = sales_df[sales_df['Наименование товаров'].isin(БАДЫ)]
        _, qty_bad, sum_bad, _ = process_data(df_bad, selected_period)

        df_lek = sales_df[sales_df['Наименование товаров'].isin(ЛЕКАРСТВЕННЫЕ_ПРЕПАРАТЫ)]
        _, qty_lek, sum_lek, _ = process_data(df_lek, selected_period)

        # === Вивід: БАДЫ ===
        st.markdown("### DORIM 360")
        if qty_bad is not None and not qty_bad.empty:
            st.markdown("**Количество**")
            st.table(styled(qty_bad)) 
            
            st.markdown("**Сумма**")
            st.table(styled(sum_bad))
        else:
            st.write("Данные отсутствуют за выбранный период.")

        st.markdown("---")

        # === Вивід: ЛЕКАРСТВЕННЫЕ ПРЕПАРАТЫ ===
        st.markdown("### HEEL")
        if qty_lek is not None and not qty_lek.empty:
            st.markdown("**Количество**")
            st.table(styled(qty_lek))
            
            st.markdown("**Сумма**")
            st.table(styled(sum_lek))
        else:
            st.write("Данные отсутствуют за выбранный период.")
# Вкладка "Регионы"
with tabs[6]:
    st.markdown("### Сводная таблица по регионам")

    # Твій CSS стиль
    st.markdown("""
        <style>
            [data-testid="stTable"] th { font-weight: bold !important; color: black !important; background-color: #f0f2f6 !important; }
            [data-testid="stTable"] td { font-weight: bold !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    # Вибір показника
    val_type = st.radio("", ["Количество", "Сумма СИП"], horizontal=True, key="reg_radio")
    val_col = 'кол-во' if val_type == "Количество" else 'Сумма СИП'

    # --- ПІДГОТОВКА ДАНИХ ТА СЛАЙДЕРА ---
    temp_reg = sales_df[~sales_df['источник'].isin(['Первичка', 'Первичка minus'])].copy()
    temp_reg['период'] = pd.to_datetime(temp_reg['период'], errors='coerce')
    temp_reg = temp_reg.dropna(subset=['период'])
    temp_reg['период'] = temp_reg['период'].dt.to_period('M').dt.to_timestamp()
    
    raw_months = sorted(temp_reg['период'].unique())
    # Російські назви місяців
    from utils import MONTH_MAP
    month_labels = [f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}" for m in raw_months]

    if not month_labels:
        st.warning("Нет данных по регионам.")
    else:
        slider_opts = ['Все'] + month_labels
        p_range = st.select_slider("Выберите диапазон дат", options=slider_opts, value=('Все', slider_opts[-1]), key="reg_slider")
        
        if p_range[0] == 'Все':
            selected_p = raw_months
        else:
            idx_s = month_labels.index(p_range[0])
            idx_e = month_labels.index(p_range[1])
            selected_p = raw_months[idx_s : idx_e + 1]

        # Генерація таблиці
        pivot_table = generate_region_period_pivot(sales_df, selected_p, value_column=val_col)

        # Функції стилізації кольорів (Ташкент)
        def highlight_tashkent(df):
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            for row in df.index:
                # Світло-блакитний для Ташкентської області
                if str(row).startswith('Ташкент область'):
                    styles.loc[row, df.columns != 'Итого'] = 'background-color: #ADD8E6;'
                # Світло-зелений для міста Ташкент
                elif str(row).startswith('Ташкент'):
                    styles.loc[row, df.columns != 'Итого'] = 'background-color: #90EE90;'
            return styles

        if not pivot_table.empty:
            # Комбінована стилізація: кольори + підсумки + шрифти
            styled_res = (pivot_table.style
                .format("{:,.0f}", na_rep='0')
                .apply(highlight_tashkent, axis=None)
                .set_properties(**{
                    'text-align': 'right', 
                    'font-size': '14px', 
                    'font-weight': 'bold',
                    'color': 'black'
                })
                .set_table_styles([
                    {'selector': 'th.row_heading', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}
                ])
                .set_properties(**{
                    'background-color': '#f0f0f0', 
                    'color': '#006400'
                }, subset=pd.IndexSlice[pivot_table.index == 'Итого', :])
                .set_properties(**{
                    'background-color': '#f0f0f0', 
                    'color': '#006400'
                }, subset=pd.IndexSlice[:, pivot_table.columns == 'Итого'])
            )

            st.markdown(f"#### {val_type}")
            st.table(styled_res)
        else:
            st.warning("Данные за выбранный период отсутствуют.")
# Решта вкладок (Ташкент, Ташкентская область, МП общее) залишаються без змін
with tabs[7]:
    st.markdown("### Сводные таблицы по г. Ташкент")

    # CSS для стилізації (твій варіант)
    st.markdown("""
        <style>
            [data-testid="stTable"] th { font-weight: bold !important; color: black !important; background-color: #f0f2f6 !important; }
            [data-testid="stTable"] td { font-weight: bold !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    # ПІДГОТОВКА ДИНАМІЧНИХ ДАТ
    t_data = sales_df[sales_df['район'] == 'Ташкент'].copy()
    t_data['период'] = pd.to_datetime(t_data['период'], errors='coerce')
    t_data = t_data.dropna(subset=['период'])
    t_data['период'] = t_data['период'].dt.to_period('M').dt.to_timestamp()
    
    raw_dates = sorted(t_data['период'].unique())
    from utils import MONTH_MAP
    actual_labels = [f"{MONTH_MAP.get(d.strftime('%B'), d.strftime('%B'))} {d.year}" for d in raw_dates]

    if not actual_labels:
        st.error("В данных по району 'Ташкент' не найдено корректных периодов.")
    else:
        # Слайдер
        period_range = st.select_slider(
            "Выберите диапазон дат",
            options=['Все'] + actual_labels,
            value=('Все', actual_labels[-1]),
            key="slider_t_dynamic"
        )
        
        if period_range[0] == 'Все':
            selected_p = raw_dates
        else:
            s_idx = actual_labels.index(period_range[0])
            e_idx = actual_labels.index(period_range[1])
            selected_p = raw_dates[s_idx : e_idx + 1]

        # Функція стилізації з твоїми кольорами для Ташкента
        def style_pivot(df):
            if df.empty: return df
            return (df.style.format("{:,.0f}")
                    .set_properties(**{'text-align': 'right', 'font-size': '14px', 'font-weight': 'bold', 'color': 'black'})
                    .set_table_styles([{'selector': 'th.row_heading', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}])
                    .set_properties(**{'background-color': '#e6f3e6', 'color': '#006400'}, 
                                    subset=pd.IndexSlice[df.index == 'Итого', :])
                    .set_properties(**{'background-color': '#e6f3e6', 'color': '#006400'}, 
                                    subset=pd.IndexSlice[:, df.columns == 'Итого']))

        # Вивід блоків через цикл
        blocks = [
            ("📦 Кол-во по товарам", generate_tashkent_pivot),
            ("💰 Сумма СИП по товарам", generate_tashkent_sum_sip_pivot),
            ("📉 Кол-во по товарам (Разделено на 4)", generate_tashkent_divided_pivot),
            ("📊 Сумма СИП по товарам (Разделено на 4)", generate_tashkent_sum_sip_divided_pivot)
        ]

        for title, func in blocks:
            st.markdown(f"#### {title}")
            result_df = func(sales_df, selected_p)
            
            if not result_df.empty:
                st.table(style_pivot(result_df))
            else:
                st.info(f"Нет данных за выбранный период.")
            st.divider()
# Вкладка "Ташкентская область" (аналогічно оновлюємо)
with tabs[8]:
    st.markdown("### Сводная таблица по Ташкентской области")

    # 1. CSS
    st.markdown("""
        <style>
            [data-testid="stTable"] th { font-weight: bold !important; color: black !important; background-color: #f0f2f6 !important; }
            [data-testid="stTable"] td { font-weight: bold !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    # 2. ДИНАМІЧНИЙ СЛАЙДЕР ДАТ
    temp_obl = sales_df[sales_df['район'].isin(OBLAST_DISTRICTS)].copy()
    temp_obl['период'] = pd.to_datetime(temp_obl['период'], errors='coerce')
    temp_obl = temp_obl.dropna(subset=['период'])
    temp_obl['период'] = temp_obl['период'].dt.to_period('M').dt.to_timestamp()
    
    actual_dates = sorted(temp_obl['период'].unique())
    from utils import MONTH_MAP
    actual_labels = [f"{MONTH_MAP.get(d.strftime('%B'), d.strftime('%B'))} {d.year}" for d in actual_dates]

    if not actual_labels:
        st.warning("В данных не найдено записей для районов Ташкентской области.")
    else:
        period_range = st.select_slider(
            "Выберите диапазон дат",
            options=['Все'] + actual_labels,
            value=('Все', actual_labels[-1]),
            key="slider_oblast_dynamic"
        )
        
        if period_range[0] == 'Все':
            selected_p = actual_dates
        else:
            s_idx = actual_labels.index(period_range[0])
            e_idx = actual_labels.index(period_range[1])
            selected_p = actual_dates[s_idx : e_idx + 1]

        # 3. ФУНКЦІЯ СТИЛІЗАЦІЇ
        def apply_custom_styles(df):
            if df.empty: return df
            return (df.style.format("{:,.0f}")
                    .set_properties(**{'text-align': 'right', 'font-size': '14px', 'font-weight': 'bold', 'color': 'black'})
                    .set_table_styles([{'selector': 'th.row_heading', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}])
                    .set_properties(**{'background-color': '#e6f3e6', 'color': '#006400'}, 
                                    subset=pd.IndexSlice[df.index == 'Итого', :])
                    .set_properties(**{'background-color': '#e6f3e6', 'color': '#006400'}, 
                                    subset=pd.IndexSlice[:, df.columns == 'Итого']))

        # 4. ВИВІД ТАБЛИЦЬ
        blocks = [
            ("📦 Кол-во по товарам (Область)", generate_other_districts_pivot),
            ("💰 Сумма СИП по товарам (Область)", generate_other_districts_sum_sip_pivot),
            ("📉 Кол-во по товарам (Разделено на 4)", generate_other_districts_divided_pivot),
            ("📊 Сумма СИП по товарам (Разделено на 4)", generate_other_districts_sum_sip_divided_pivot)
        ]

        for title, func in blocks:
            st.markdown(f"#### {title}")
            res_df = func(sales_df, selected_p)
            if not res_df.empty:
                st.table(apply_custom_styles(res_df))
            else:
                st.caption("Нет данных за выбранный период")
            st.divider()

# Вкладка "МП общее"

def get_mp_sort_key(mp_name):
    if is_excluded(mp_name):
        if 'бады' in str(mp_name).lower():
            return 2
        else:
            return 3

    return 1


def style_table(df):
    return (
        df.style.format("{:,.0f}")
        .set_properties(**{
            'font-weight': 'bold',
            'text-align': 'right',
            'color': 'black'
        })
        .set_table_styles([
            {
                'selector': 'th',
                'props': [
                    ('font-weight', 'bold'),
                    ('background-color', '#f0f2f6')
                ]
            },
            {
                'selector': '.row_heading',
                'props': [
                    ('font-weight', 'bold'),
                    ('text-align', 'left')
                ]
            }
        ])
        .apply(
            lambda x: [
                'background-color: #e6f3e6; color: #006400'
                if (x.name == 'Итого' or c == 'Итого')
                else ''
                for c in x.index
            ],
            axis=1
        )
    )


# --- ПІДГОТОВКА СПІЛЬНИХ МІСЯЦІВ ДЛЯ МП ---
temp_sales_data = sales_df.copy()
temp_sales_data['период'] = pd.to_datetime(
    temp_sales_data['период'],
    errors='coerce'
)

all_available_months = sorted(
    temp_sales_data['период']
    .dropna()
    .dt.to_period('M')
    .dt.to_timestamp()
    .unique()
)

month_labels_shared = [
    f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}"
    for m in all_available_months
]


# --- ВКЛАДКА 9 / МП HEEL ---
# Якщо ти вже прибрав вкладки Ташкент, Ташкентская область, МП БАДы,
# тоді тут може бути tabs[7], а не tabs[9].
with tabs[9]:
    st.markdown("### Сводная таблица по МП (Лекарственные препараты)")

    if not month_labels_shared:
        st.warning("Нет доступных периодов для отображения.")
    else:
        # --- ВИБІР ПЕРІОДУ ---
        p_range_9 = st.select_slider(
            "Выберите диапазон дат",
            options=['Все'] + month_labels_shared,
            value=('Все', month_labels_shared[-1]),
            key="mp_drugs_slider"
        )

        if p_range_9[0] == 'Все':
            selected_period_9 = all_available_months
        else:
            start_idx_9 = month_labels_shared.index(p_range_9[0])
            end_idx_9 = month_labels_shared.index(p_range_9[1])

            selected_period_9 = all_available_months[
                start_idx_9:end_idx_9 + 1
            ]

        # --- ВИБІР ПОКАЗНИКА ---
        metric_9 = st.radio(
            "Показатель",
            ["Количество", "Сумма СИП"],
            horizontal=True,
            key="metric_drugs"
        )

        val_col_9 = 'кол-во' if metric_9 == "Количество" else 'Сумма СИП'

        # --- ВАКАНСІЇ, ЯКІ ТРЕБА ЗАЛИШИТИ ---
        drug_vacancies = [
            'вакант',
            'вакант Самарканд',
            'вакант Кашкадарья'
        ]

        def get_drug_mp_result(mp_name):
            """
            Повертає готову таблицю для конкретного МП.
            Якщо це вакансія — використовує calculate_excluded_mp_pivot.
            Якщо звичайний МП — calculate_mp_pivot_with_bonus.
            """

            if mp_name in drug_vacancies:
                return calculate_excluded_mp_pivot(
                    sales_df,
                    mp_name,
                    selected_period_9,
                    val_col_9,
                    target_products=PHARMACEUTICALS
                )

            return calculate_mp_pivot_with_bonus(
                sales_df,
                mp_name,
                selected_period_9,
                val_col_9,
                target_products=PHARMACEUTICALS
            )

        def has_real_data(df_res):
            """
            Перевіряє, чи реально є дані.
            Не достатньо просто df.empty, бо таблиця може бути з нулями.
            """

            if df_res is None or df_res.empty:
                return False

            if 'Итого' not in df_res.columns:
                return False

            data_rows = df_res[df_res.index != 'Итого']

            if data_rows.empty:
                return False

            return data_rows['Итого'].sum() > 0

        # --- БЕРЕМО ВСІХ МП, АЛЕ БЕЗ ТЕХНІЧНИХ ---
        all_mps = sorted([
            mp for mp in sales_df['МП'].dropna().unique()
            if (not is_excluded(mp)) or mp in drug_vacancies
        ])

        # --- ФІЛЬТРУЄМО ТІЛЬКИ ТИХ, У КОГО Є РЕАЛЬНІ ДАНІ ---
        mp_results_cache = {}
        standard_mps = []

        for mp in all_mps:
            df_res = get_drug_mp_result(mp)

            if has_real_data(df_res):
                standard_mps.append(mp)
                mp_results_cache[mp] = df_res

        # --- ЯКЩО НЕМАЄ ЖОДНОГО МП З ДАНИМИ ---
        if not standard_mps:
            st.info("Нет данных по МП за выбранный период.")
        else:
            selected_mp_9 = st.selectbox(
                "Выберите МП",
                ['Все МП'] + standard_mps,
                key="sel_drugs_mp"
            )

            def render_drug_mp(mp_name):
                """
                Виводить блок тільки якщо у МП реально є дані.
                """

                df_res = mp_results_cache.get(mp_name)

                if not has_real_data(df_res):
                    return False

                st.subheader(f"👨‍⚕️ {mp_name}")

                actual_districts = (
                    sales_df[sales_df['МП'] == mp_name]['район']
                    .dropna()
                    .unique()
                )

                dist_str = ", ".join(filter(None, actual_districts))

                if dist_str:
                    st.caption(f"📍 Районы: {dist_str}")

                st.table(style_table(df_res))

                return True

            if selected_mp_9 == "Все МП":
                for mp in standard_mps:
                    was_shown = render_drug_mp(mp)

                    if was_shown:
                        st.divider()
            else:
                render_drug_mp(selected_mp_9)

# --- ВКЛАДКА 10 (БАДы) ---
# with tabs[10]:
#     st.markdown("### Сводная таблица по менеджерам (БАДы)")

#     p_range_10 = st.select_slider("Выберите диапазон дат", options=['Все'] + month_labels_shared, value=('Все', month_labels_shared[-1]), key="mp_focus_slider")
    
#     selected_period_10 = all_available_months if p_range_10[0] == 'Все' else \
#                          all_available_months[month_labels_shared.index(p_range_10[0]) : month_labels_shared.index(p_range_10[1]) + 1]

#     # ДИНАМІЧНИЙ ВИБІР СЛОВНИКА
#     current_focus_dict_10 = get_focus_dict(selected_period_10)
#     focus_mps = sorted(list(current_focus_dict_10.keys()) + ['вакант Бады'])
    
#     selected_mp_10 = st.selectbox("Выберите менеджера", ['Все МП'] + focus_mps, key="sel_focus_mp")
#     metric_10 = st.radio("Показатель", ["Количество", "Сумма СИП"], horizontal=True, key="metric_focus")
#     val_col_10 = 'кол-во' if metric_10 == "Количество" else 'Сумма СИП'

#     def render_focus_mp(mp_name, f_dict):
#         st.subheader(f"👨‍⚕️ {mp_name}")
#         target_districts = f_dict.get(mp_name, [])
#         dist_str = ", ".join(target_districts) if target_districts else "все районы"
#         st.caption(f"📍 Целевые районы: {dist_str}")

#         if mp_name == 'вакант Бады':
#             df_res = calculate_excluded_mp_pivot(sales_df, mp_name, selected_period_10, val_col_10)
#         else:
#             df_res = calculate_focus_mp_pivot(sales_df, mp_name, selected_period_10, val_col_10, f_dict)
            
#         if not df_res.empty: st.table(style_table(df_res))
#         else: st.info(f"Нет данных по БАДам ({dist_str})")

#     if selected_mp_10 == "Все МП":
#         for mp in focus_mps:
#             render_focus_mp(mp, current_focus_dict_10)
#             st.divider()
#     else:
#         render_focus_mp(selected_mp_10, current_focus_dict_10)
        
with tabs[10]:
    st.header("🌍 БАДы по регионам")

    # 1. ПІДГОТОВКА ПЕРІОДІВ (Твій стандартний підхід)
    temp_sales_reg = prep_df(sales_df)
    available_months_reg = sorted(temp_sales_reg['период'].unique())
    month_labels_reg = [f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}" for m in available_months_reg]
    
    p_range_reg = st.select_slider(
        "Выберите диапазон дат", 
        options=['Все'] + month_labels_reg, 
        value=('Все', month_labels_reg[-1]), 
        key="reg_slider_final"
    )
    
    selected_p_reg = available_months_reg if p_range_reg[0] == 'Все' else \
                     available_months_reg[month_labels_reg.index(p_range_reg[0]) : month_labels_reg.index(p_range_reg[1]) + 1]

    # 2. ВИБІР МЕТРИКИ
    metric_reg = st.radio("Показатель расчета", ["Количество", "Сумма СИП"], horizontal=True, key="reg_metric_final")
    val_col_reg = 'кол-во' if metric_reg == "Количество" else 'Сумма СИП'

    # 3. АВТОМАТИЧНИЙ РОЗПОДІЛ РАЙОНІВ
    # Визначаємо райони, де є активні МП (не ваканти, не порожньо)
    mask_active = (
        sales_df['МП'].notna() & 
        (sales_df['МП'] != '') & 
        ~sales_df['МП'].str.contains('вакант', case=False, na=False)
    )
    districts_with_mp = sorted(sales_df[mask_active]['район'].unique())
    
    # Визначаємо всі інші райони (де тільки ваканти або порожні записи МП)
    all_dist_in_data = sales_df['район'].unique()
    districts_no_mp = sorted([d for d in all_dist_in_data if d not in districts_with_mp and pd.notna(d)])

    # 4. ВІДОБРАЖЕННЯ ТАБЛИЦЬ
    
    # --- СЕКЦІЯ 1: З МЕНЕДЖЕРАМИ ---
    st.subheader("✅ Продажи в регионах с МП")
    if districts_with_mp:
        df_res_mp = calculate_regional_pivot(sales_df, districts_with_mp, selected_p_reg, val_col_reg)
        if not df_res_mp.empty and df_res_mp.columns.size > 1: # Перевірка, чи є райони крім 'Итого'
            st.table(style_table(df_res_mp))
        else:
            st.info("Нет продаж выбранных БАДов в этих регионах за указанный период.")
    else:
        st.warning("В базе данных не найдено районов с закрепленными МП.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # --- СЕКЦІЯ 2: БЕЗ МЕНЕДЖЕРІВ ---
    st.subheader("⚪ Продажи в свободных регионах (Ваканты / Без МП)")
    if districts_no_mp:
        df_res_no_mp = calculate_regional_pivot(sales_df, districts_no_mp, selected_p_reg, val_col_reg)
        if not df_res_no_mp.empty and df_res_no_mp.columns.size > 1:
            st.table(style_table(df_res_no_mp))
        else:
            st.info("В свободных регионах продаж данных БАДов не зафиксировано.")
    else:
        st.write("Все регионы в базе имеют закрепленных МП.")    
        
with tabs[11]:
    st.markdown("### 🌆 Тепловая карта по районам")
    st.caption("Фільтрація: профілі '(HEEL)' показують Heel, профілі '(БАДы)' показують БАДи Фокус.")
    
    # Підготовка слайдера періодів
    temp_df = sales_df.copy()
    temp_df['период'] = pd.to_datetime(temp_df['период'], errors='coerce')
    available_months = sorted(temp_df['период'].dropna().dt.to_period('M').dt.to_timestamp().unique())
    month_labels = [f"{MONTH_MAP.get(m.strftime('%B'), m.strftime('%B'))} {m.year}" for m in available_months]
    
    if not month_labels:
        st.warning("Недостатньо даних для часової шкали.")
    else:
        p_range = st.select_slider(
            "Выберите диапазон дат", 
            options=['Все'] + month_labels, 
            value=('Все', month_labels[-1]),
            key="heatmap_period_slider"
        )
        
        # Визначаємо вибрані дати
        if p_range[0] == 'Все':
            selected_p = available_months
        else:
            selected_p = available_months[month_labels.index(p_range[0]) : month_labels.index(p_range[1]) + 1]

        # Вибір МП
        all_options = ["Все МП"] + sorted(list(ALL_MP_DISTRICTS.keys()))
        selected_mp = st.selectbox("Выберите МП или Категорию", all_options)

        def render_map(name, districts):
            pivot_data = calculate_district_heatmap(sales_df, districts, selected_p, name)
            
            if not pivot_data.empty:
                st.subheader(f"👨‍⚕️ {name}")
                # Адаптуємо розмір графіка під кількість районів
                fig, ax = plt.subplots(figsize=(10, max(2, len(pivot_data) * 0.7)))
                
                sns.heatmap(
                    pivot_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                    linewidths=0.5, ax=ax, cbar_kws={'label': 'Количество'}
                )
                
                plt.xticks(rotation=45)
                plt.title(f"Продажи (Кол-во): {name}")
                st.pyplot(fig)
                plt.close(fig)
                st.divider()
            elif selected_mp != "Все МП":
                st.info(f"Нет данных по продажам для {name} в указанный период.")

        # Вивід результатів
        if selected_mp == "Все МП":
            for name, districts in ALL_MP_DISTRICTS.items():
                render_map(name, districts)
        else:
            render_map(selected_mp, ALL_MP_DISTRICTS[selected_mp])