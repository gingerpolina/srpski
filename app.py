import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import random
from datetime import datetime
import pytz

# Настройка вкладки браузера
st.set_page_config(
    page_title="Практика сербского", 
    page_icon="🇷🇸",
    layout="centered"
)

# Инициализация состояния
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# Подключение к Google Таблицам
@st.cache_resource
def init_gsheets():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], 
        scopes=scopes
    )
    client = gspread.authorize(creds)
    
    if "spreadsheet_id" in st.secrets:
        return client.open_by_key(st.secrets["spreadsheet_id"])
    return client.open(st.secrets.get("spreadsheet_name", "Практика Сербского"))

# Заголовок приложения
st.title("Генератор тем для разговора 🇷🇸")
st.caption("Сербский язык — практика говорения")

# Блок ввода имени и авторизации
if not st.session_state.user_name:
    input_name = st.text_input(
        "Как тебя зовут?", 
        placeholder="Введи свое имя, чтобы начать...",
        key="temp_name_input"
    ).strip()
    
    # Кнопка активна только если введено минимум 3 символа
    is_valid = len(input_name) >= 3
    if st.button("Старт", type="primary", disabled=not is_valid, use_container_width=True):
        st.session_state.user_name = input_name
        st.rerun()

else:
    # Имя зафиксировано, поле заблокировано для изменений
    col_name, col_reset = st.columns([4, 1])
    with col_name:
        st.text_input("Как тебя зовут?", value=st.session_state.user_name, disabled=True)
    with col_reset:
        st.write("")  # Отступ для выравнивания кнопки
        st.write("")
        if st.button("Сменить", use_container_width=True):
            st.session_state.user_name = ""
            st.rerun()

    st.write(f"Zdravo, **{st.session_state.user_name}**! Выбери формат практики:")
    
    # Выбор режима
    mode = st.radio(
        "Режим:",
        ["Ответ на вопрос", "Презентация", "Составить текст из набора слов"],
        horizontal=False
    )
    
    # Кнопка генерации задания
    if st.button("🎲 Получить задание", type="primary", use_container_width=True):
        with st.spinner("Выбираем тему из базы..."):
            try:
                sheet = init_gsheets()
                log_text = ""
                
                # 1. Режим: Ответ на вопрос
                if mode == "Ответ на вопрос":
                    worksheet = sheet.worksheet("Ответ на вопрос")
                    rows = worksheet.col_values(1)[1:]
                    topics = [t.strip() for t in rows if t.strip()]
                    
                    if not topics:
                        st.warning("В базе 'Ответ на вопрос' пока нет тем.")
                    else:
                        result = random.choice(topics)
                        st.success(f"""
<sub>❓ Твой вопрос/тема:</sub>

### {result}
""")
                        log_text = f"Ответ на вопрос: {result}"
                
                # 2. Режим: Презентация
                elif mode == "Презентация":
                    worksheet = sheet.worksheet("Презентация")
                    all_rows = worksheet.get_all_values()[1:]
                    valid_rows = [r for r in all_rows if len(r) > 0 and r[0].strip()]
                    
                    if not valid_rows:
                        st.warning("В базе 'Презентация' пока нет тем.")
                    else:
                        chosen = random.choice(valid_rows)
                        result_topic = chosen[0].strip()
                        result_vocab = chosen[1].strip() if len(chosen) > 1 and chosen[1].strip() else "—"
                        
                        # Аккордеон со структурой (по умолчанию свернут)
                        with st.expander("📋 Struktura izlaganja (нажми, чтобы открыть структуру)"):
                            st.markdown("""
1. **Uvod:** Izbor i kratka definicija teme.
2. **Lično iskustvo:** Moje lično iskustvo sa ovom temom u svakodnevnom životu.
3. **Situacija u mojoj zemlji:** Kako je to rešeno u mojoj domovini, kakav je opšti stav društva.
4. **Prednosti i mane:** Argumentacija "za" i "protiv", dobre i loše strane fenomena.
5. **Zaključak:** Kratak rezime i lični završni stav.
""")
                        
                        st.success(f"""
<sub>📊 Тема для презентации:</sub>

### {result_topic}
""")
                        
                        st.warning(f"""
<sub>💡 Опорный вокабуляр:</sub>

### {result_vocab}
""")
                        log_text = f"Презентация: {result_topic}"
                
                # 3. Режим: Составить текст из набора слов
                elif mode == "Составить текст из набора слов":
                    worksheet = sheet.worksheet("Составить текст из набора слов")
                    rows = worksheet.col_values(1)[1:]
                    vocab_sets = [v.strip() for v in rows if v.strip()]
                    
                    if not vocab_sets:
                        st.warning("В базе пока нет наборов слов.")
                    else:
                        result = random.choice(vocab_sets)
                        st.success(f"""
<sub>📝 Твой набор слов:</sub>

### {result}
""")
                        log_text = f"Составить текст: {result}"
                
                # Запись в логи
                if log_text:
                    logs_sheet = sheet.worksheet("Логи")
                    tz = pytz.timezone('Europe/Belgrade')
                    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                    
                    logs_sheet.append_row(
                        [st.session_state.user_name, log_text, current_time], 
                        value_input_option='USER_ENTERED'
                    )
                    
            except Exception as e:
                st.error("Произошла ошибка при обращении к Google Таблице.")
                with st.expander("Детали ошибки"):
                    st.write(e)
