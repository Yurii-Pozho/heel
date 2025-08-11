import streamlit as st
import pandas as pd
from eco_lec_sales import process_data
from first_second_first import create_pivot_tables, month_order
from source import generate_source_pivots
from region import generate_region_period_pivot
from tashkent import generate_tashkent_pivot, generate_tashkent_sum_sip_pivot
from tashkent import generate_tashkent_divided_pivot, generate_tashkent_sum_sip_divided_pivot
from tashkent_oblast import generate_other_districts_divided_pivot, generate_other_districts_pivot
from tashkent_oblast import generate_other_districts_sum_sip_divided_pivot, generate_other_districts_sum_sip_pivot
from mp import calculate_excluded_mp_pivot, calculate_mp_pivot_with_tashkent
from stocks import calculate_source_pivot
import seaborn as sns
import matplotlib.pyplot as plt
import io
from heatmap import calculate_district_heatmap, month_order, mp_district_mapping

st.set_page_config(layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #2E7D32; font-size: 100px; font-family: Montserrat, sans-serif;'>- Heel</h1>",
    unsafe_allow_html=True
)

# Завантаження файлу
uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "csv"])
if not uploaded_file:
    st.warning("Пожалуйста, загрузите файл с данными.")
    st.stop()

# Перевірка типу файлу та аркушів
if uploaded_file.name.endswith(".xlsx"):
    # Завантажуємо Excel-файл і перевіряємо аркуші
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names  # Отримуємо список назв аркушів
    sales_df = None
    stocks_df = None

    # Перевіряємо наявність аркушів "Продажи" та "Стоки"
    if "Продажи" in sheet_names:
        sales_df = pd.read_excel(uploaded_file, sheet_name="Продажи")
    if "Стоки" in sheet_names:
        stocks_df = pd.read_excel(uploaded_file, sheet_name="Стоки")

    # Якщо аркуш "Продажи" не знайдено, видаємо попередження
    if sales_df is None:
        st.warning("Аркуш 'Продажи' не знайдено в файлі Excel.")
        st.stop()
else:
    # Якщо файл CSV, вважаємо, що це дані продажів
    sales_df = pd.read_csv(uploaded_file)
    stocks_df = None

# Перевірка необхідних колонок для вкладки "Регионы"
required_columns = ['регион', 'район', 'период', 'кол-во', 'Сумма СИП', 'источник']
missing_columns = [col for col in required_columns if col not in sales_df.columns]
if missing_columns:
    st.error(f"У аркуші 'Продажи' відсутні необхідні колонки: {missing_columns}")
    st.stop()

# Обробка даних із аркуша "Продажи"
filtered_df, pivot_qty, pivot_sum, used_months = process_data(sales_df)

if filtered_df is None:
    st.warning("Немає даних для джерела 'Первичка' в аркуші 'Продажи'.")
    st.stop()

# Оновлюємо вкладки, додаючи вкладку "Дані стоків"
tabs = st.tabs([
    "📋 Данные продаж",
    "📋 Данные стоков",
    "📈 Остатки",
    "📈 Первичка + вторичка - первичка",
    "📈 Источники по периодам",
    "🌐 Eco Lec продажи",
    "📈 Регионы",
    "📊 Ташкент",
    "📊 Ташкентская область",
    "📈 МП",
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
        
with tabs[2]:
    st.markdown("### Сводная таблица по источникам (Стоки)")
    
    if stocks_df is None:
        st.warning("Аркуш 'Стоки' не знайдено в файлі Excel.")
        st.stop()

    
    # Перевірка необхідних колонок
    required_columns = ['Наименование товаров', 'период', 'источник', 'кол-во', 'Сумма СИП']
    missing_columns = [col for col in required_columns if col not in stocks_df.columns]
    if missing_columns:
        st.error(f"У аркуші 'Стоки' відсутні необхідні колонки: {missing_columns}")
        st.stop()
    
    # Вибір показника
    value_type = st.radio(
        "Выберите показатель",
        options=["Количество", "Сумма СИП"],
        key="stocks_value_type_radio",
        horizontal=True
    )
    value_column = 'кол-во' if value_type == "Количество" else 'Сумма СИП'
    
    # Вибір діапазону дат
    filtered_df = stocks_df.copy()
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    used_months = sorted(
        filtered_df[filtered_df[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    period_labels = ['Все'] + used_months
    
    if not used_months:
        st.warning(f"Немає ненульових даних для показника '{value_type}' у аркуші 'Стоки'.")
        st.stop()
    
    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="stocks_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]
    
    # Вибір джерела
    source_list = stocks_df['источник'].dropna().unique().tolist()
    source_list.sort()
    source_list.insert(0, "Все источники")
    
    selected_source = st.selectbox(
        "Выберите источник",
        options=source_list,
        key="stocks_source_selectbox"
    )
    
    # Генерація зведеної таблиці
    if selected_source == "Все источники":
        for source in source_list[1:]:
            st.markdown(f"{source}")
            pivot_table = calculate_source_pivot(stocks_df, source, selected_period, value_column=value_column)
            if pivot_table.empty:
                st.write("Дані відсутні.")
            else:
                styled_table = pivot_table.style.format("{:,.0f}", na_rep='').set_properties(**{
                    'text-align': 'right',
                    'font-size': '14px'
                }).set_properties(**{
                    'font-weight': 'bold',
                    'background-color': '#f0f0f0'
                }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
                    'font-weight': 'bold',
                    'background-color': '#f0f0f0'
                }, subset=pd.IndexSlice[:, 'Итого'])
                st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)
    else:
        st.markdown(f"#### {selected_source}")
        pivot_table = calculate_source_pivot(stocks_df, selected_source, selected_period, value_column=value_column)
        if pivot_table.empty:
            st.write("Дані відсутні.")
        else:
            styled_table = pivot_table.style.format("{:,.0f}", na_rep='').set_properties(**{
                'text-align': 'right',
                'font-size': '14px'
            }).set_properties(**{
                'font-weight': 'bold',
                'background-color': '#f0f0f0'
            }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
                'font-weight': 'bold',
                'background-color': '#f0f0f0'
            }, subset=pd.IndexSlice[:, 'Итого'])
            st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)        

# Вкладка "Первичка + вторичка - первичка"
with tabs[3]:
    filtered_df = sales_df.copy()
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    used_months = sorted(
        filtered_df[filtered_df['кол-во'] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    period_labels = ['Все'] + used_months

    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="items_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    pivot_qty_no_filter, pivot_sum_no_filter, used_months_no_filter = create_pivot_tables(sales_df, selected_period)

    styled_qty_no_filter = pivot_qty_no_filter.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    styled_sum_no_filter = pivot_sum_no_filter.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.markdown("### Количество")
    st.dataframe(styled_qty_no_filter, use_container_width=True, height=(len(pivot_qty_no_filter) + 1) * 35 + 3)

    st.markdown("### Сумма")
    st.dataframe(styled_sum_no_filter, use_container_width=True, height=(len(pivot_sum_no_filter) + 1) * 35 + 3)


# Вкладка "Источники по периодам"
with tabs[4]:
    st.markdown("### Сводная таблица: Кол-во по источнику и периоду")
    filtered_df = sales_df[~sales_df['источник'].isin(['Первичка минус', 'Первичка'])].copy()
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    filtered_df['кол-во'] = pd.to_numeric(filtered_df['кол-во'], errors='coerce').fillna(0)
    used_months = sorted(
        filtered_df[filtered_df['кол-во'] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    period_labels = ['Все'] + used_months

    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="source_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    pivot_qty_by_source, pivot_sum_by_source = generate_source_pivots(sales_df, selected_period)

    styled_qty_by_source = pivot_qty_by_source.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_qty_by_source, use_container_width=True, height=(len(pivot_qty_by_source) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Сумма СИП по источнику и периоду")
    styled_sum_by_source = pivot_sum_by_source.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_sum_by_source, use_container_width=True, height=(len(pivot_sum_by_source) + 1) * 35 + 3)



# Вкладка "Eco Lec продажи"
with tabs[5]:
    st.markdown("### Сводная таблица и график по 'Первичка'")
    period_labels = ['Все'] + month_order
    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="period_slider_tab1"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    filtered_df, pivot_qty, pivot_sum, used_months = process_data(sales_df, selected_period)

    if filtered_df is not None and not pivot_qty.empty and not pivot_sum.empty:
        styled_qty = pivot_qty.style.format("{:,.0f}").set_properties(**{
            'text-align': 'right',
            'font-size': '14px'
        }).set_properties(**{
            'font-weight': 'bold',
            'background-color': '#f0f0f0'
        }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
            'font-weight': 'bold',
            'background-color': '#f0f0f0'
        }, subset=pd.IndexSlice[:, 'Итого'])

        styled_sum = pivot_sum.style.format("{:,.0f}").set_properties(**{
            'text-align': 'right',
            'font-size': '14px'
        }).set_properties(**{
            'font-weight': 'bold',
            'background-color': '#f0f0f0'
        }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
            'font-weight': 'bold',
            'background-color': '#f0f0f0'
        }, subset=pd.IndexSlice[:, 'Итого'])

        st.markdown("### Количество")
        st.dataframe(styled_qty, use_container_width=True, height=(len(pivot_qty) + 1) * 35 + 3)

        st.markdown("### Сумма")
        st.dataframe(styled_sum, use_container_width=True, height=(len(pivot_sum) + 1) * 35 + 3)

    else:
        st.write("Дані відсутні.")

# Вкладка "Регионы"
with tabs[6]:
    st.markdown("### Сводная таблиця по регионам")

    # Вибір показника
    value_type = st.radio(
        "Выберите показатель",
        options=["Количество", "Сумма СИП"],
        key="region_value_type_radio",
        horizontal=True  # Горизонтальне розташування
    )
    value_column = 'кол-во' if value_type == "Количество" else 'Сумма СИП'

    # Перевірка наявності обраного стовпця
    if value_column not in sales_df.columns:
        st.error(f"Колонка '{value_column}' відсутня в аркуші 'Продажи'. Доступні колонки: {sales_df.columns.tolist()}")
        st.stop()

    # Вибір діапазону дат
    filtered_df = sales_df[~sales_df['источник'].isin(['Первичка', 'Первичка минус'])].copy()
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    used_months = sorted(
        filtered_df[filtered_df[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    period_labels = ['Все'] + used_months

    if not used_months:
        st.warning(f"Немає ненульових даних для показника '{value_type}' у аркуші 'Продажи'.")
        st.stop()

    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="region_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    # Генерація зведеної таблиці
    try:
        pivot_table = generate_region_period_pivot(sales_df, selected_period, value_column=value_column)
    except KeyError as e:
        st.error(f"Помилка в даних: {e}")
        st.stop()

    # Стилізація таблиці з підсвічуванням
    def highlight_tashkent(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for row in df.index:
            if row.startswith('Ташкент область'):
                for col in df.columns:
                    if col != 'Итого':
                        styles.at[row, col] = 'background-color: #ADD8E6'
            elif row.startswith('Ташкент'):
                for col in df.columns:
                    if col != 'Итого':
                        styles.at[row, col] = 'background-color: #90EE90'
        return styles

    if not pivot_table.empty:
        styled_table = pivot_table.style.format("{:,.0f}", na_rep='').apply(
            highlight_tashkent, axis=None
        ).set_properties(**{
            'text-align': 'right',
            'font-size': '14px'
        }).set_properties(**{
            'font-weight': 'bold',
            'background-color': '#f0f0f0'
        }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
            'font-weight': 'bold',
            'background-color': '#f0f0f0'
        }, subset=pd.IndexSlice[:, 'Итого'])

        st.markdown(f"### {value_type}")
        st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)
    else:
        st.warning(f"Дані відсутні для показника '{value_type}' у вибраний період.")

# Решта вкладок (Ташкент, Ташкентская область, МП общее) залишаються без змін
# Наприклад, вкладка "Ташкент"
with tabs[7]:
    st.markdown("### Сводная таблица: Кол-во по товарам (Ташкент)")
    period_labels = ['Все'] + month_order
    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="tashkent_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    pivot_tashkent = generate_tashkent_pivot(sales_df, selected_period)
    styled_tashkent = pivot_tashkent.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_tashkent, use_container_width=True, height=(len(pivot_tashkent) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Сумма СИП по товарам (Ташкент)")
    pivot_tashkent_sum_sip = generate_tashkent_sum_sip_pivot(sales_df, selected_period)
    styled_tashkent_sum_sip = pivot_tashkent_sum_sip.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_tashkent_sum_sip, use_container_width=True, height=(len(pivot_tashkent_sum_sip) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Кол-во по товарам (Ташкент, разделено на 4)")
    pivot_tashkent_divided = generate_tashkent_divided_pivot(sales_df, selected_period)
    styled_tashkent_divided = pivot_tashkent_divided.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_tashkent_divided, use_container_width=True, height=(len(pivot_tashkent_divided) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Сумма СИП по товарам (Ташкент, разделено на 4)")
    pivot_tashkent_sum_sip_divided = generate_tashkent_sum_sip_divided_pivot(sales_df, selected_period)
    styled_tashkent_sum_sip_divided = pivot_tashkent_sum_sip_divided.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_tashkent_sum_sip_divided, use_container_width=True, height=(len(pivot_tashkent_sum_sip_divided) + 1) * 35 + 3)

# Вкладка "Ташкентская область" (аналогічно оновлюємо)
with tabs[8]:
    st.markdown("### Сводная таблица: Кол-во по товарам (Ташкентская область)")
    period_labels = ['Все'] + month_order
    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="other_districts_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    pivot_other_districts = generate_other_districts_pivot(sales_df, selected_period)
    styled_other_districts = pivot_other_districts.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_other_districts, use_container_width=True, height=(len(pivot_other_districts) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Сумма СИП по товарам (Ташкентская область)")
    pivot_other_districts_sum_sip = generate_other_districts_sum_sip_pivot(sales_df, selected_period)
    styled_other_districts_sum_sip = pivot_other_districts_sum_sip.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_other_districts_sum_sip, use_container_width=True, height=(len(pivot_other_districts_sum_sip) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Кол-во по товарам (Ташкентская область, разделено на 4)")
    pivot_other_districts_divided = generate_other_districts_divided_pivot(sales_df, selected_period)
    styled_other_districts_divided = pivot_other_districts_divided.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_other_districts_divided, use_container_width=True, height=(len(pivot_other_districts_divided) + 1) * 35 + 3)

    st.markdown("### Сводная таблица: Сумма СИП по товарам (Ташкентская область, разделено на 4)")
    pivot_other_districts_sum_sip_divided = generate_other_districts_sum_sip_divided_pivot(sales_df, selected_period)
    styled_other_districts_sum_sip_divided = pivot_other_districts_sum_sip_divided.style.format("{:,.0f}", na_rep='').set_properties(**{
        'text-align': 'right',
        'font-size': '14px'
    }).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
        'font-weight': 'bold',
        'background-color': '#f0f0f0'
    }, subset=pd.IndexSlice[:, 'Итого'])

    st.dataframe(styled_other_districts_sum_sip_divided, use_container_width=True, height=(len(pivot_other_districts_sum_sip_divided) + 1) * 35 + 3)

# Вкладка "МП общее"
with tabs[9]: 
    st.markdown("### Сводная таблица по МП")
    filtered_df = sales_df.copy()
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))
    period_labels = ['Все'] + used_months

    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="mp_period_slider"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]

    mp_list = sales_df['МП'].dropna().unique().tolist()
    mp_list.sort()
    mp_list.insert(0, "Все МП")

    selected_mp = st.selectbox(
        "Выберите МП",
        options=mp_list,
        key="mp_selectbox"
    )

    value_type = st.radio(
        "Выберите показатель",
        options=["Количество", "Сумма СИП"],
        key="value_type_radio"
    )

    value_column = 'кол-во' if value_type == "Количество" else 'Сумма СИП'

    exclude_list = ['Нилуфар', 'вакант Самарканд']
    mp_pivots = {}

    if selected_mp == "Все МП":
        for mp in mp_list[1:]:
            if mp in exclude_list:
                mp_pivots[mp] = calculate_excluded_mp_pivot(sales_df, mp, selected_period, value_column=value_column)
            else:
                mp_pivots[mp] = calculate_mp_pivot_with_tashkent(sales_df, mp, selected_period, value_column=value_column)

        for mp_name, pivot_table in mp_pivots.items():
            st.markdown(f"#### {mp_name}")
            if pivot_table.empty:
                st.write("Дані відсутні.")
            else:
                styled_table = pivot_table.style.format("{:,.0f}", na_rep='').set_properties(**{
                    'text-align': 'right',
                    'font-size': '14px'
                }).set_properties(**{
                    'font-weight': 'bold',
                    'background-color': '#f0f0f0'
                }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
                    'font-weight': 'bold',
                    'background-color': '#f0f0f0'
                }, subset=pd.IndexSlice[:, 'Итого'])
                st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)
    else:
        if selected_mp in exclude_list:
            pivot_table = calculate_excluded_mp_pivot(sales_df, selected_mp, selected_period, value_column=value_column)
        else:
            pivot_table = calculate_mp_pivot_with_tashkent(sales_df, selected_mp, selected_period, value_column=value_column)

        st.markdown(f"#### МП: {selected_mp}")
        if pivot_table.empty:
            st.write("Дані відсутні.")
        else:
            styled_table = pivot_table.style.format("{:,.0f}", na_rep='').set_properties(**{
                'text-align': 'right',
                'font-size': '14px'
            }).set_properties(**{
                'font-weight': 'bold',
                'background-color': '#f0f0f0'
            }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
                'font-weight': 'bold',
                'background-color': '#f0f0f0'
            }, subset=pd.IndexSlice[:, 'Итого'])
            st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)

with tabs[10]:
    st.markdown("### Тепловая карта по районам")
    
    # Перевірка даних
    required_columns = ['Наименование товаров', 'период', 'район', 'кол-во', 'Сумма СИП']
    missing_columns = [col for col in required_columns if col not in sales_df.columns]
    if missing_columns:
        st.error(f"У аркуші 'Продажи' відсутні необхідні колонки: {missing_columns}")
        st.stop()
    
    # Очищення даних
    sales_df['кол-во'] = pd.to_numeric(sales_df['кол-во'], errors='coerce').fillna(0)
    sales_df['Сумма СИП'] = pd.to_numeric(sales_df['Сумма СИП'], errors='coerce').fillna(0)
    
    # Вибір показника
    value_type = st.radio(
        "Выберите показатель",
        options=["Количество", "Сумма СИП"],
        key="district_value_type_radio_10",
        horizontal=True
    )
    value_column = 'кол-во' if value_type == "Количество" else 'Сумма СИП'
    
    # Вибір діапазону дат
    filtered_df = sales_df.copy()
    filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
    filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
    used_months = sorted(
        filtered_df[filtered_df[value_column] > 0]['период'].dropna().unique(),
        key=lambda x: month_order.index(x)
    )
    period_labels = ['Все'] + used_months
    
    if not used_months:
        st.warning(f"Немає ненульових даних для показника '{value_type}' у аркуші 'Продажи'.")
        st.stop()
    
    period_range = st.select_slider(
        "Выберите диапазон дат",
        options=period_labels,
        value=(period_labels[0], period_labels[-1]),
        key="district_period_slider_10"
    )
    start_period, end_period = period_range
    if start_period == 'Все':
        selected_period = None
    else:
        start_idx = period_labels.index(start_period)
        end_idx = period_labels.index(end_period)
        selected_period = period_labels[start_idx:end_idx + 1]
    
    # Вибір МП
    mp_list = list(mp_district_mapping.keys())
    mp_list.insert(0, "Все МП")
    selected_mp = st.selectbox(
        "Выберите МП",
        options=mp_list,
        key="district_mp_selectbox_10"
    )
    
    # Налаштування шрифтів для читабельності
    sns.set_context("notebook", font_scale=0.8)
    
    # Генерація теплових карт
    if selected_mp == "Все МП":
        for mp, districts in mp_district_mapping.items():
            st.markdown(
                f'<h2 style="font-size: 48px;">{mp}</h2>',
                unsafe_allow_html=True
            )
            available_districts = [d for d in districts if d in sales_df['район'].values]
            if not available_districts:
                st.write("Жоден район цього МП відсутній у даних.")
                continue
            
            pivot_table = calculate_district_heatmap(sales_df, available_districts, selected_period, value_column=value_column)
            
            if pivot_table.empty:
                st.write("Дані відсутні.")
            else:
                plt.figure(figsize=(10, max(2, len(pivot_table) * 0.3)))
                sns.heatmap(
                    pivot_table,
                    annot=True,
                    fmt='.0f',
                    cmap='YlOrRd',
                    cbar_kws={'label': value_type},
                    linewidths=0.5,
                    annot_kws={'size': 8},
                    square=False
                )
                plt.title(f'Тепловая карта: {mp} ({value_type})')
                plt.xlabel('Период')
                plt.ylabel('Район')
                plt.tight_layout()
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                st.image(buf, use_container_width=True)
                plt.close()
    else:
        st.markdown(
            f'<h2 style="font-size: 48px;">{selected_mp}</h2>',
            unsafe_allow_html=True
        )
        districts = mp_district_mapping.get(selected_mp, [])
        available_districts = [d for d in districts if d in sales_df['район'].values]
        if not available_districts:
            st.write("Жоден район цього МП відсутній у даних.")
        else:
            pivot_table = calculate_district_heatmap(sales_df, available_districts, selected_period, value_column=value_column)
            
            if pivot_table.empty:
                st.write("Дані відсутні.")
            else:
                plt.figure(figsize=(6, max(2, len(pivot_table) * 0.3)))
                sns.heatmap(
                    pivot_table,
                    annot=True,
                    fmt='.0f',
                    cmap='YlOrRd',
                    cbar_kws={'label': value_type},
                    linewidths=0.5,
                    annot_kws={'size': 8},
                    square=False
                )
                plt.title(f'Тепловая карта: {selected_mp} ({value_type})')
                plt.xlabel('Период')
                plt.ylabel('Район')
                plt.tight_layout()
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                st.image(buf, use_container_width=True)
                plt.close()