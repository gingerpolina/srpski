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

# Стили для скрытия подсказки "Press Enter", увеличения шрифтов и подсветки аккордеона
st.markdown("""
<style>
/* Прячем подсказку 'Press Enter to apply' */
div[data-testid="InputInstructions"] {
    display: none !important;
}

/* Стилизуем аккордеон структуры: делаем его цветным и заметным */
div[data-testid="stExpander"] {
    background-color: rgba(30, 64, 175, 0.2) !important;
    border: 1px solid rgba(96, 165, 250, 0.5) !important;
    border-radius: 10px !important;
    margin-top: 10px !important;
    margin-bottom: 14px !important;
}
div[data-testid="stExpander"] summary p {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #93c5fd !important;
}
</style>
""", unsafe_allow_html=True)

# Функция для вывода красивых карточек (мелкий заголовок + крупный текст)
def render_card(label: str, content: str, card_type: str = "green"):
    if card_type == "green":
        bg = "rgba(34, 197, 94, 0.15)"
        border = "rgba(34, 197, 94, 0.45)"
        label_color = "#86efac"
    elif card_type == "orange":
        bg = "rgba(245, 158, 11, 0.15)"
        border = "rgba(245, 158, 11, 0.45)"
        label_color = "#fcd34d"
    else:
        bg = "rgba(59, 130, 246, 0.15)"
        border = "rgba(59, 130, 246, 0.45)"
        label_color = "#93c5fd"

    html = f"""
    <div style="
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 10px;
        margin-bottom: 12px;
    ">
        <div style="font-size: 0.85rem; color: {label_color}; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">
            {label}
        </div>
        <div style="font-size: 1.4rem; font-weight: 700; color: #ffffff; line-height: 1.4;">
            {content}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

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

# Шапка сайта
st.title("Генератор тем для разговора 🇷🇸")
st.caption("Сербский язык — практика говорения")

# Блок ввода имени
if not st.session_state.user_name:
    with st.form("name_form", border=False):
        input_name = st.text_input(
            "Как тебя зовут?", 
            placeholder="Введи свое имя, чтобы начать...",
            key="temp_name_input"
        )
        submitted = st.form_submit_button("Старт", type="primary", use_container_width=True)
        if submitted:
            cleaned_name = input_name.strip()
            if len(cleaned_name) >= 3:
                st.session_state.user_name = cleaned_name
                st.rerun()
            else:
                st.warning("Имя должно содержать минимум 3 буквы.")

else:
    # Зафиксированное имя (нельзя редактировать, пока не нажата кнопка "Сменить")
    col_name, col_reset = st.columns([4, 1])
    with col_name:
        st.text_input("Как тебя зовут?", value=st.session_state.user_name, disabled=True)
    with col_reset:
        st.write("")
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
    
    # Кнопка получения темы
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
                        render_card("❓ Твой вопрос/тема", result, card_type="green")
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
                        
                        # Аккордеон со структурой презентации
                        with st.expander("📋 Struktura izlaganja (нажми, чтобы открыть структуру)"):
                            st.markdown("""
1. **Uvod:** Izbor i kratka definicija teme.
2. **Lično iskustvo:** Moje lično iskustvo sa ovom temom u svakodnevnom životu.
3. **Situacija u mojoj zemlji:** Kako je to rešeno u mojoj domovini, kakav je opšti stav društva.
4. **Prednosti i mane:** Argumentacija "za" i "protiv", dobre i loše strane fenomena.
5. **Zaključak:** Kratak rezime i lični završni stav.
""")
                        
                        # Карточка темы
                        render_card("📊 Тема для презентации", result_topic, card_type="green")
                        
                        # Карточка вокабуляра
                        render_card("💡 Опорный вокабуляр", result_vocab, card_type="orange")
                        
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
                        render_card("📝 Твой набор слов", result, card_type="green")
                        log_text = f"Составить текст: {result}"
                
                # Запись в лист "Логи"
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
