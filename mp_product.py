# with tabs[9]:
#     st.markdown("### Сводная таблица по МП")
#     filtered_df = sales_df.copy()
#     filtered_df['период'] = pd.Categorical(filtered_df['период'], categories=month_order, ordered=True)
#     used_months = sorted(filtered_df['период'].dropna().unique(), key=lambda x: month_order.index(x))
#     period_labels = ['Все'] + used_months

#     period_range = st.select_slider(
#         "Выберите диапазон дат",
#         options=period_labels,
#         value=(period_labels[0], period_labels[-1]),
#         key="mp_period_slider"
#     )
#     start_period, end_period = period_range
#     if start_period == 'Все':
#         selected_period = None
#     else:
#         start_idx = period_labels.index(start_period)
#         end_idx = period_labels.index(end_period)
#         selected_period = period_labels[start_idx:end_idx + 1]

#     mp_list = sales_df['МП'].dropna().unique().tolist()
#     mp_list.sort()
#     mp_list.insert(0, "Все МП")

#     selected_mp = st.selectbox(
#         "Выберите МП",
#         options=mp_list,
#         key="mp_selectbox"
#     )

#     value_type = st.radio(
#         "Выберите показатель",
#         options=["Количество", "Сумма СИП"],
#         key="value_type_radio"
#     )

#     value_column = 'кол-во' if value_type == "Количество" else 'Сумма СИП'

#     exclude_list = ['Нилуфар', 'вакант Самарканд']
#     mp_pivots = {}

#     if selected_mp == "Все МП":
#         for mp in mp_list[1:]:
#             if mp in exclude_list:
#                 mp_pivots[mp] = calculate_excluded_mp_pivot(sales_df, mp, selected_period, value_column=value_column)
#             else:
#                 mp_pivots[mp] = calculate_mp_pivot_with_tashkent(sales_df, mp, selected_period, value_column=value_column)

#         for mp_name, pivot_table in mp_pivots.items():
#             st.markdown(f"#### {mp_name}")
#             if pivot_table.empty:
#                 st.write("Дані відсутні.")
#             else:
#                 styled_table = pivot_table.style.format("{:,.0f}", na_rep='').set_properties(**{
#                     'text-align': 'right',
#                     'font-size': '14px'
#                 }).set_properties(**{
#                     'font-weight': 'bold',
#                     'background-color': '#f0f0f0'
#                 }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
#                     'font-weight': 'bold',
#                     'background-color': '#f0f0f0'
#                 }, subset=pd.IndexSlice[:, 'Итого'])
#                 st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)
#     else:
#         if selected_mp in exclude_list:
#             pivot_table = calculate_excluded_mp_pivot(sales_df, selected_mp, selected_period, value_column=value_column)
#         else:
#             pivot_table = calculate_mp_pivot_with_tashkent(sales_df, selected_mp, selected_period, value_column=value_column)

#         st.markdown(f"#### МП: {selected_mp}")
#         if pivot_table.empty:
#             st.write("Дані відсутні.")
#         else:
#             styled_table = pivot_table.style.format("{:,.0f}", na_rep='').set_properties(**{
#                 'text-align': 'right',
#                 'font-size': '14px'
#             }).set_properties(**{
#                 'font-weight': 'bold',
#                 'background-color': '#f0f0f0'
#             }, subset=pd.IndexSlice['Итого', :]).set_properties(**{
#                 'font-weight': 'bold',
#                 'background-color': '#f0f0f0'
#             }, subset=pd.IndexSlice[:, 'Итого'])
#             st.dataframe(styled_table, use_container_width=True, height=(len(pivot_table) + 1) * 35 + 3)



# import pandas as pd

# month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
#                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# # Функція для "Нилуфар" і "Вакант Самарканд" (без урахування районів)
# def calculate_excluded_mp_pivot(df, mp_name, selected_period=None, value_column='кол-во'):
#     required_columns = ['Наименование товаров', 'период', 'МП', value_column]
#     if not all(col in df.columns for col in required_columns):
#         raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
#     # Перетворюємо 'период' у категоріальний тип із правильним порядком
#     df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)
    
#     filtered_df = df.copy()
#     if selected_period:
#         if isinstance(selected_period, list):
#             filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
#         else:
#             filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
#     filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
#     # Фільтруємо дані лише для конкретного МП
#     mp_subset = filtered_df[filtered_df['МП'] == mp_name]
#     print(f"Унікальні значення '{value_column}' для МП '{mp_name}': {mp_subset[value_column].unique()}")
#     print(f"Кількість записів для МП '{mp_name}' після фільтрації: {len(mp_subset)}")
    
#     if mp_subset.empty:
#         print(f"Попередження: Жодних даних не знайдено для МП '{mp_name}'.")
#         return pd.DataFrame()
    
#     # Групуємо дані для перевірки
#     mp_grouped = mp_subset.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
#     print(f"Дані для МП '{mp_name}' після групування:\n{mp_grouped}")
    
#     # Визначаємо місяці, які реально є в даних
#     used_months = sorted(mp_subset['период'].dropna().unique(), key=lambda x: month_order.index(x))
    
#     # Формуємо зведену таблицю без автоматичного "Итого"
#     pivot_table = pd.pivot_table(
#         mp_subset,
#         index='Наименование товаров',
#         columns='период',
#         values=value_column,
#         aggfunc='sum',
#         fill_value=0,
#         margins=False
#     )
    
#     # Сортуємо стовпці за наявними місяцями
#     pivot_table = pivot_table.reindex(columns=used_months)
    
#     # Додаємо "Итого" вручну
#     pivot_table['Итого'] = pivot_table.sum(axis=1).round(0)
#     total_row = pivot_table.sum(axis=0).to_frame().T
#     total_row.index = ['Итого']
#     pivot_table = pd.concat([pivot_table, total_row])
    
#     # Перевіряємо "Итого" для дебагу
#     if not pivot_table.empty:
#         calculated_total = pivot_table.drop('Итого', errors='ignore').sum().round(0)
#         print(f"Ручний розрахунок 'Итого' по стовпцях для МП '{mp_name}':\n{calculated_total}")
#         if 'Итого' in pivot_table.index:
#             print(f"Автоматичний 'Итого' з pivot_table для МП '{mp_name}':\n{pivot_table.loc['Итого']}")
    
#     print(f"Зведена таблиця для МП '{mp_name}' після додавання 'Итого':\n{pivot_table}")
#     return pivot_table

# # Функція для всіх інших МП (з додаванням "Ташкент" і "Ташкент область")
# def calculate_mp_pivot_with_tashkent(df, mp_name, selected_period=None, value_column='кол-во'):
#     required_columns = ['Наименование товаров', 'период', 'МП', 'район', value_column]
#     if not all(col in df.columns for col in required_columns):
#         raise KeyError(f"Колонки {required_columns} мають бути в датафреймі. Доступні колонки: {list(df.columns)}")
    
#     # Перетворюємо 'период' у категоріальний тип із правильним порядком
#     df['период'] = pd.Categorical(df['период'], categories=month_order, ordered=True)
    
#     filtered_df = df.copy()
#     if selected_period:
#         if isinstance(selected_period, list):
#             filtered_df = filtered_df[filtered_df['период'].isin(selected_period)]
#         else:
#             filtered_df = filtered_df[filtered_df['период'] == selected_period]
    
#     filtered_df[value_column] = pd.to_numeric(filtered_df[value_column], errors='coerce').fillna(0)
    
#     # Фільтруємо дані для конкретного МП
#     mp_data = filtered_df[filtered_df['МП'] == mp_name].copy()
#     if mp_data.empty:
#         print(f"Попередження: Жодних даних не знайдено для МП '{mp_name}'.")
#         return pd.DataFrame()
    
#     print(f"Знайдено {len(mp_data)} записів для МП '{mp_name}'.")
    
#     # Групуємо дані для МП
#     mp_grouped = mp_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
#     print(f"Дані для МП '{mp_name}' після групування:\n{mp_grouped}")
    
#     # Додаємо дані для "Ташкент"/4
#     tashkent_data = filtered_df[filtered_df['район'] == 'Ташкент'].copy()
#     if not tashkent_data.empty:
#         tashkent_grouped = tashkent_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
#         tashkent_grouped[value_column] = tashkent_grouped[value_column] / 4
#         print(f"Дані для 'Ташкент' (поділено на 4):\n{tashkent_grouped}")
#     else:
#         tashkent_grouped = pd.DataFrame(columns=['Наименование товаров', 'период', value_column])
#         print("Попередження: Жодних даних не знайдено для району 'Ташкент'.")
    
#     # Додаємо дані для районів "Ташкент область"/4
#     tashkent_oblast_districts = [
#         'Алмалык', 'Ангрен', 'Ахангаран', 'Бекабад', 'Бостанлыкский', 'Бука',
#         'Газалкент', 'Зангиата', 'Келес', 'Кибрай', 'Коканд', 'Паркент',
#         'Пискент', 'Ташкент область', 'Чиноз', 'Чирчик', 'Янгиюль'
#     ]
#     tashkent_oblast_data = filtered_df[filtered_df['район'].isin(tashkent_oblast_districts)].copy()
#     if not tashkent_oblast_data.empty:
#         tashkent_oblast_grouped = tashkent_oblast_data.groupby(['Наименование товаров', 'период'])[value_column].sum().reset_index()
#         tashkent_oblast_grouped[value_column] = tashkent_oblast_grouped[value_column] / 4
#         print(f"Дані для районів 'Ташкент область' (поділено на 4):\n{tashkent_oblast_grouped}")
#     else:
#         tashkent_oblast_grouped = pd.DataFrame(columns=['Наименование товаров', 'период', value_column])
#         print(f"Попередження: Жодних даних не знайдено для районів {tashkent_oblast_districts}.")
    
#     # Об'єднуємо всі дані
#     result = mp_grouped.copy()
#     result = result.merge(tashkent_grouped, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_tashkent'))
#     result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_tashkent'].fillna(0)
#     result = result.drop(columns=[f'{value_column}_tashkent'])
#     print(f"Результат після об'єднання з 'Ташкент' для МП '{mp_name}':\n{result}")
    
#     result = result.merge(tashkent_oblast_grouped, on=['Наименование товаров', 'период'], how='outer', suffixes=('', '_tashkent_oblast'))
#     result[value_column] = result[value_column].fillna(0) + result[f'{value_column}_tashkent_oblast'].fillna(0)
#     result = result.drop(columns=[f'{value_column}_tashkent_oblast'])
#     print(f"Результат після об'єднання з 'Ташкент область' для МП '{mp_name}':\n{result}")
    
#     result[value_column] = result[value_column].round(0)
    
#     # Визначаємо місяці, які реально є в даних (лише з ненульовими значеннями)
#     used_months = sorted(
#         result[result[value_column] > 0]['период'].dropna().unique(),
#         key=lambda x: month_order.index(x)
#     )
    
#     # Формуємо зведену таблицю без автоматичного "Итого"
#     pivot_table = pd.pivot_table(
#         result,
#         index='Наименование товаров',
#         columns='период',
#         values=value_column,
#         aggfunc='sum',
#         fill_value=0,
#         margins=False
#     )
    
#     # Сортуємо стовпці за наявними місяцями
#     pivot_table = pivot_table.reindex(columns=used_months)
    
#     # Додаємо "Итого" вручну
#     pivot_table['Итого'] = pivot_table.sum(axis=1).round(0)
#     total_row = pivot_table.sum(axis=0).to_frame().T
#     total_row.index = ['Итого']
#     pivot_table = pd.concat([pivot_table, total_row])
    
#     print(f"Зведена таблиця для МП '{mp_name}' після додавання 'Итого':\n{pivot_table}")
#     return pivot_table