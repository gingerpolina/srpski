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
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], 
        scopes=scopes
    )
    client = gspread.authorize(creds)
    
    if "spreadsheet_id" in st.secrets:
        return client.open_by_key(st.secrets["spreadsheet_id"])
    return client.open(st.secrets.get("spreadsheet_name", "Практика Сербского"))

# Интерфейс
st.title("Генератор тем для разговора 🇷🇸")
st.caption("Сербский язык — практика говорения")

name = st.text_input("Как тебя зовут?", placeholder="Введи свое имя...").strip()

if name:
    st.write(f"Zdravo, **{name}**! Выбери формат практики:")
    
    # Обновленные режимы в соответствии с вкладками таблицы
    mode = st.radio(
        "Режим:",
        ["Ответ на вопрос", "Презентация", "Составить текст из набора слов"],
        horizontal=False
    )
    
    if st.button("🎲 Получить задание", type="primary", use_container_width=True):
        with st.spinner("Выбираем тему из базы..."):
            try:
                sheet = init_gsheets()
                log_text = ""
                
                # 1. Режим: Ответ на вопрос
                if mode == "Ответ на вопрос":
                    worksheet = sheet.worksheet("Ответ на вопрос")
                    rows = worksheet.col_values(1)[1:]  # пропускаем заголовок
                    topics = [t.strip() for t in rows if t.strip()]
                    
                    if not topics:
                        st.warning("В базе 'Ответ на вопрос' пока нет тем.")
                    else:
                        result = random.choice(topics)
                        st.success(f"### ❓ Твой вопрос/тема:\n**{result}**")
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
                        
                        # Напоминалка о структуре презентации
                        st.info("""
### 📋 Struktura izlaganja:
1. **Uvod:** Izbor i kratka definicija teme.
2. **Lično iskustvo:** Moje lično iskustvo sa ovom temom u svakodnevnom životu.
3. **Situacija u mojoj zemlji:** Kako je to rešeno u mojoj domovini, kakav je opšti stav društva.
4. **Prednosti i mane:** Argumentacija "za" i "protiv", dobre i loše strane fenomena.
5. **Zaključak:** Kratak rezime i lični završni stav.
""")
                        
                        st.success(f"### 📊 Тема для презентации:\n**{result_topic}**")
                        st.warning(f"**Опорный вокабуляр:**\n{result_vocab}")
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
                        st.success(f"### 📝 Твой набор слов:\n**{result}**")
                        log_text = f"Составить текст: {result}"
                
                # Запись в логи
                if log_text:
                    logs_sheet = sheet.worksheet("Логи")
                    tz = pytz.timezone('Europe/Belgrade')
                    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                    
                    logs_sheet.append_row(
                        [name, log_text, current_time], 
                        value_input_option='USER_ENTERED'
                    )
                    
            except Exception as e:
                st.error("Произошла ошибка при обращении к Google Таблице.")
                with st.expander("Детали ошибки"):
                    st.write(e)
else:
    st.info("👋 Введи свое имя выше, чтобы начать.")
