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

# Подключение к Google Таблицам
@st.cache_resource
def init_gsheets():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    # Данные берутся из st.secrets
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], 
        scopes=scopes
    )
    client = gspread.authorize(creds)
    
    # Открываем по ID (или названию) из секретов
    # Если в secrets указан SPREADSHEET_ID, используем его, иначе ищем по названию
    if "spreadsheet_id" in st.secrets:
        return client.open_by_key(st.secrets["spreadsheet_id"])
    return client.open(st.secrets.get("spreadsheet_name", "Практика Сербского"))

# Интерфейс
st.title("Генератор тем для разговора 🇷🇸")
st.caption("Сербский язык — практика говорения")

name = st.text_input("Как тебя зовут?", placeholder="Введи свое имя...").strip()

if name:
    st.write(f"Zdravo, **{name}**! Выбери формат практики:")
    
    mode = st.radio(
        "Режим:",
        ["Короткий монолог", "Презентация", "По вокабуляру"],
        horizontal=True
    )
    
    if st.button("🎲 Получить тему", type="primary", use_container_width=True):
        with st.spinner("Выбираем тему из базы..."):
            try:
                sheet = init_gsheets()
                log_text = ""
                
                # 1. Режим: Короткий монолог
                if mode == "Короткий монолог":
                    worksheet = sheet.worksheet("Монолог")
                    rows = worksheet.col_values(1)[1:]  # пропускаем заголовок
                    topics = [t.strip() for t in rows if t.strip()]
                    
                    if not topics:
                        st.warning("В базе 'Монолог' пока нет тем.")
                    else:
                        result = random.choice(topics)
                        st.success(f"### 🗣 Твоя тема:\n**{result}**")
                        log_text = f"Монолог: {result}"
                
                # 2. Режим: Презентация
                elif mode == "Презентация":
                    worksheet = sheet.worksheet("Презентация")
                    all_rows = worksheet.get_all_values()[1:]  # получаем строки [[тема, слова], ...]
                    valid_rows = [r for r in all_rows if len(r) > 0 and r[0].strip()]
                    
                    if not valid_rows:
                        st.warning("В базе 'Презентация' пока нет тем.")
                    else:
                        chosen = random.choice(valid_rows)
                        result_topic = chosen[0].strip()
                        result_vocab = chosen[1].strip() if len(chosen) > 1 and chosen[1].strip() else "—"
                        
                        st.success(f"### 📊 Тема для презентации:\n**{result_topic}**")
                        st.info(f"**Опорные слова:**\n{result_vocab}")
                        log_text = f"Презентация: {result_topic}"
                
                # 3. Режим: По вокабуляру
                elif mode == "По вокабуляру":
                    worksheet = sheet.worksheet("Вокабуляр")
                    rows = worksheet.col_values(1)[1:]
                    vocab_sets = [v.strip() for v in rows if v.strip()]
                    
                    if not vocab_sets:
                        st.warning("В базе 'Вокабуляр' пока нет наборов слов.")
                    else:
                        result = random.choice(vocab_sets)
                        st.success(f"### 📝 Твой набор слов:\n**{result}**")
                        log_text = f"Вокабуляр: {result}"
                
                # Запись в логи (если тема была успешно выбрана)
                if log_text:
                    logs_sheet = sheet.worksheet("Логи")
                    tz = pytz.timezone('Europe/Belgrade')
                    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Добавляем строку: Имя, Тема, Время (Белград)
                    logs_sheet.append_row(
                        [name, log_text, current_time], 
                        value_input_option='USER_ENTERED'
                    )
                    
            except Exception as e:
                st.error("Произошла ошибка при подключении к Google Таблице.")
                with st.expander("Детали ошибки"):
                    st.write(e)
else:
    st.info("👋 Введи имя выше, чтобы начать.")
