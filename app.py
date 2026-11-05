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
}
</style>
""", unsafe_allow_html=True)

# Функция для вывода красивых карточек (мелкий заголовок + крупный текст)
def render_card(label: str, content: str, card_type: str = "green"):
    # Полупрозрачные фоны и цвет текста по теме Streamlit — читается и в светлой, и в тёмной теме
    if card_type == "green":
        bg = "rgba(34, 197, 94, 0.15)"
        border = "rgba(34, 197, 94, 0.45)"
    elif card_type == "orange":
        bg = "rgba(245, 158, 11, 0.15)"
        border = "rgba(245, 158, 11, 0.45)"
    else:
        bg = "rgba(59, 130, 246, 0.15)"
        border = "rgba(59, 130, 246, 0.45)"

    html = f"""
    <div style="
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 10px;
        margin-bottom: 12px;
    ">
        <div style="font-size: 0.85rem; color: inherit; opacity: 0.7; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">
            {label}
        </div>
        <div style="font-size: 1.4rem; font-weight: 700; color: inherit; line-height: 1.4;">
            {content}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# Инициализация состояния
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "seen" not in st.session_state:
    st.session_state.seen = {}  # режим -> задания, которые уже выпадали в этой сессии
if "task" not in st.session_state:
    st.session_state.task = {}  # текущее задание: режим, строка, показан ли ответ

# Случайный выбор без повторов: пока не выпадут все задания режима, одно и то же не повторится
def pick_unseen(mode: str, items: list):
    seen = st.session_state.seen.setdefault(mode, [])
    candidates = [i for i in items if i not in seen]
    if not candidates:
        # Всё уже было — начинаем круг заново, но не с того же задания, что только что выпало
        last = seen[-1] if seen else None
        seen.clear()
        candidates = [i for i in items if i != last] or items
    choice = random.choice(candidates)
    seen.append(choice)
    return choice

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

# Чтение листа целиком (кэш 5 минут, чтобы кнопки вроде «Показать ответ» не дёргали таблицу заново)
@st.cache_data(ttl=300, show_spinner=False)
def load_rows(sheet_name: str):
    rows = init_gsheets().worksheet(sheet_name).get_all_values()[1:]
    return [[c.strip() for c in r] for r in rows if r and r[0].strip()]

def log_task(log_text: str):
    tz = pytz.timezone('Europe/Belgrade')
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    init_gsheets().worksheet("Логи").append_row(
        [st.session_state.user_name, log_text, current_time],
        value_input_option='USER_ENTERED'
    )

STRUKTURA = """
1. **Uvod:** Izbor i kratka definicija teme.
2. **Lično iskustvo:** Moje lično iskustvo sa ovom temom u svakodnevnom životu.
3. **Situacija u mojoj zemlji:** Kako je to rešeno u mojoj domovini, kakav je opšti stav društva.
4. **Prednosti i mane:** Argumentacija "za" i "protiv", dobre i loše strane fenomena.
5. **Zaključak:** Kratak rezime i lični završni stav.
"""

# --- Отрисовка заданий по режимам ---
def show_question(row):
    render_card("❓ Твой вопрос/тема", row[0], card_type="green")

def show_presentation(row):
    with st.expander("📋 Struktura izlaganja (нажми, чтобы открыть структуру)"):
        st.markdown(STRUKTURA)
    render_card("📊 Тема для презентации", row[0], card_type="green")
    vocab = row[1] if len(row) > 1 and row[1] else "—"
    render_card("💡 Опорный вокабуляр", vocab, card_type="orange")

def show_word_set(row):
    render_card("📝 Твой набор слов", row[0], card_type="green")

def show_grammar(row):
    # Колонки листа «Грамматика»: Тема | Блок | Как строить | Русский | Подсказка | Ответ
    row = row + [""] * (6 - len(row))
    topic, block, rule, rus, hint, answer = row[:6]
    label = f"🧩 {topic} · {block}" if block else f"🧩 {topic}"
    content = rus + (f'<div style="font-size: 1.05rem; font-weight: 500; opacity: 0.75; margin-top: 6px;">({hint})</div>' if hint else "")
    render_card(label, content, card_type="green")
    if st.session_state.task.get("show_answer"):
        render_card("✅ Ответ", "<br>".join(a.strip() for a in answer.split(" / ")), card_type="orange")
        if rule:
            st.caption(f"Как строить: {rule}")
    elif st.button("👀 Показать ответ", use_container_width=True):
        st.session_state.task["show_answer"] = True
        st.rerun()

# Все режимы в одном месте: чтобы добавить новый — допиши сюда строку
# sheet — лист в таблице, show — как показать задание, log — что записать в «Логи»
MODES = {
    "Ответ на вопрос": dict(sheet="Ответ на вопрос", show=show_question,
                            log=lambda r: f"Ответ на вопрос: {r[0]}"),
    "Презентация": dict(sheet="Презентация", show=show_presentation,
                        log=lambda r: f"Презентация: {r[0]}"),
    "Составить текст из набора слов": dict(sheet="Составить текст из набора слов", show=show_word_set,
                                           log=lambda r: f"Составить текст: {r[0]}"),
    "Грамматика": dict(sheet="Грамматика", show=show_grammar, by_topic=True,
                       log=lambda r: f"Грамматика ({r[0]}): {r[3] if len(r) > 3 else ''}"),
}
ALL_TOPICS = "Все темы вперемешку"

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

    mode = st.radio("Режим:", list(MODES), horizontal=False)
    cfg = MODES[mode]

    try:
        rows = load_rows(cfg["sheet"])
        seen_key = mode
        if cfg.get("by_topic"):
            topics = list(dict.fromkeys(r[0] for r in rows))
            options = topics + [ALL_TOPICS] if len(topics) > 1 else topics
            topic = st.selectbox("Тема:", options) if options else None
            if topic and topic != ALL_TOPICS:
                rows = [r for r in rows if r[0] == topic]
            seen_key = f"{mode}: {topic}"

        if st.button("🎲 Получить задание", type="primary", use_container_width=True):
            if not rows:
                st.session_state.task = {}
                st.warning(f"В базе «{cfg['sheet']}» пока нет заданий.")
            else:
                row = pick_unseen(seen_key, rows)
                st.session_state.task = {"mode": mode, "row": row, "show_answer": False}
                log_task(cfg["log"](row))

        task = st.session_state.task
        if task and task["mode"] == mode:
            cfg["show"](task["row"])

    except Exception as e:
        st.error("Произошла ошибка при обращении к Google Таблице.")
        with st.expander("Детали ошибки"):
            st.write(e)
