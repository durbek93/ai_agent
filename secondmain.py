import os
import re
import time
import asyncio
import logging
from datetime import datetime
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from google import genai
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Загружаем ключи
load_dotenv()

# 1. ПОДГОТОВКА ПАПОК
DIRS = ['downloads', 'results']
for directory in DIRS:
    os.makedirs(directory, exist_ok=True)

# 2. ИНИЦИАЛИЗАЦИЯ GEMINI
try:
    client = genai.Client()
    print("✅ Gemini API подключен.")
except Exception as e:
    print(f"❌ Ошибка API: {e}")
    exit(1)

# --- КОНСТАНТЫ ---
PROMPT_80_20 = """
Ты — Эксперт-Аналитик 80/20. Твоя единственная цель — применять «Мышление 80/20» (Закон Парето) к любому тексту (книге, статье, рассказу), который тебе предоставляет пользователь. Ты знаешь, что Вселенная несбалансирована: 80% ценности любого текста скрыто всего в 20% его объема (а иногда это 90/10 или 99/1). Ты не делаешь обычные пересказы. Ты создаешь экстракт чистой пользы, экономя пользователю часы времени.

---

### БЛОК 1: Ключевые принципы (Как искать те самые 20% сути)

При анализе текста используй следующие принципы «Мышления 80/20»:
1. **Поиск «Жизненно важного меньшинства»:** Игнорируй линейное чтение. Сразу определяй главную идею автора, ради которой написан текст. Обычно она кроется во введении, заключении или ключевом поворотном моменте.
2. **Нелинейность причин и следствий:** Ищи дисбаланс. Какие 20% идей, фактов или действий героев приводят к 80% результатов/выводов в тексте? 
3. **Изоляция «Пороговой величины» (Tipping point):** Найди ту самую мысль или тот самый фактор в тексте, после которого все остальное становится очевидным или неизбежным.
4. **Простота важнее сложности:** Истинная суть всегда проста. Если концепция в тексте запутана, найди её ядро. Игнорируй усложнения, ищи базовый рычаг (как в физике), с помощью которого автор сдвигает всю свою теорию или сюжет.
5. **Фокус на результативности:** В нон-фикшн текстах выделяй только те 20% правил, которые дают максимальный практический эффект. В художественных текстах — те 20% событий, которые реально двигают сюжет и трансформируют героев.

---

### БЛОК 2: Критерии отсева балласта (Как определять 80% воды)

Безжалостно УДАЛЯЙ и ИГНОРИРУЙ следующие элементы текста (это «Тривиальное большинство»):
1. **Многократные примеры и доказательства:** Если автор приводит 10 примеров для подтверждения одной идеи, оставь только 2-3 самых ярких.
2. **Исторические и лирические отступления:** Если это не меняет сути дела, отсекай предыстории, биографии третьих лиц и долгие вступления.
3. **Сложные обоснования простых истин:** Отсекай тяжеловесные академические рассуждения, если вывод из них сводится к одной простой мысли.
4. **Второстепенные сюжетные линии и персонажи (для художки):** Игнорируй всё, что не влияет на финальную развязку или главную трансформацию протагониста.
5. **Общеизвестные факты и стереотипы:** Убирай «социальные условности» и банальности. Оставляй только нестандартные, нелинейные и парадоксальные мысли, которые ломают шаблоны.
6. **Оправдания и искусственная сложность:** Как говорил фон Манштейн, "суета и сложность — враги результата". Убирай всё, где автор топчется на месте, пытаясь оправдать свою концепцию.

---

### БЛОК 3: Строгий Формат ответа

Твой ответ всегда должен быть структурированным, кратким и соответствовать следующему шаблону. Не используй вводных фраз вроде "Конечно, вот ваш ответ". Сразу выдавай результат.

**1. Чистая суть (1-2 предложения)**
*Сформулируй фундаментальную идею текста. Те самые 1-5%, ради которых текст был написан.*

**2. Жизненно важное меньшинство (Ключевые 20%)**
*Выдели 3-5 главных мыслей/событий текста, которые дают 80% пользы или понимания. Используй маркированный список. Описывай их максимально емко, без воды.*
* [Мысль/Событие 1]
* [Мысль/Событие 2]
* [Мысль/Событие 3]

**3. Тривиальное большинство (Что мы отсекли)**
Кратко укажи (1 абзац), на что автор потратил 80% текста, но что пользователю читать НЕ НУЖНО (например: "Автор потратил 200 страниц на анализ 50 разных компаний, но вывод из этого один...", или "Половина книги — это описание второстепенных интриг...").*

4. Главный рычаг (Как это применить / Главный вывод)**
*Один конкретный, прагматичный вывод или призыв к действию, основанный на тексте. Что пользователь должен вынести для себя прямо сейчас.*
```

"""

# --- ЛОГИКА ОБРАБОТКИ ---

def analyze_audio(url, loop=None, status_msg=None):
    def update_status(text):
        print(text)
        if loop and status_msg:
            try:
                asyncio.run_coroutine_threadsafe(status_msg.edit_text(text), loop)
            except:
                pass

    update_status("🔍 [1/4] Получаю информацию о видео...")
    
    try:
        ydl_opts_info = {'quiet': True, 'cookiefile': 'downloads/cookies.txt'}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info.get('title', 'video')
            # Оставляем только буквы, цифры, пробелы и базовые знаки
            clean_title = re.sub(r'[^\w\sа-яА-ЯёЁ-]', '', raw_title).strip()
            clean_title = re.sub(r'\s+', '_', clean_title) # пробелы в подчеркивания
            if not clean_title:
                clean_title = datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        print(f"❌ Ошибка инфо: {e}")
        clean_title = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    audio_path = f"downloads/{clean_title}.mp3"
    result_path = f"results/{clean_title}_summary.txt"
    tts_audio_path = f"results/{clean_title}_voice.mp3"

    # ЭТАП 1: Скачивание аудио (быстрый режим)
    update_status(f"📥 [2/4] Скачиваю аудио:\n«{clean_title}»...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"downloads/{clean_title}",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True, 
        'cookiefile': 'downloads/cookies.txt',
        'javascript_runtime': 'node',        # Используем Node.js для JS-задач
        'remote_components': ['ejs:github'],  # Разрешаем загрузку солверов
        'extractor_args': {
            'youtube': {'player_client': ['web_creator']} # Маскировка
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return None, None

    # ЭТАП 2: Загрузка в облако Gemini
    update_status(f"📤 [3/4] Загружаю в Google Cloud...")
    try:
        uploaded_file = client.files.upload(file=audio_path)
        
        # Ждем обработки
        while uploaded_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        # ЭТАП 3: Анализ 80/20 (добавляем цикл попыток)
        for attempt in range(3):
            try:
                update_status(f"🤖 [4/4] ИИ анализирует аудио...")
                response = client.models.generate_content(
                    model='gemini-2.5-flash', # Сменили модель из-за жестких лимитов 2.0
                    contents=[uploaded_file, PROMPT_80_20]
                )
                
                # Сохраняем текстовый результат
                with open(result_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                break # Успех, выходим из цикла попыток
                
            except Exception as e:
                import re
                error_msg = str(e)
                if ("503" in error_msg or "429" in error_msg) and attempt < 2:
                    wait_time = 5 if "503" in error_msg else 30
                    
                    # Умное чтение таймера ожидания из ответа Google (например "Please retry in 53.15s")
                    match = re.search(r'retry in (\d+\.?\d*)s', error_msg)
                    if match:
                        wait_time = int(float(match.group(1))) + 5 # Добавляем 5 секунд запаса
                        
                    print(f"⏳ Ошибка лимитов API. Умное ожидание {wait_time} сек...")
                    time.sleep(wait_time)
                else:
                    raise e # Пробрасываем ошибку дальше, если попытки кончились

    except Exception as e:
        print(f"❌ Ошибка ИИ: {e}")
        return None, None
        
    finally:
        # ЧИСТКА ОБЛАКА: Гарантированно удаляем файл из Google, даже если была ошибка
        try:
            if 'uploaded_file' in locals() and uploaded_file:
                client.files.delete(name=uploaded_file.name)
                print("\n🧹 Файл удален из Google Cloud.")
        except:
            pass

    # ЭТАП 4: Озвучка выжимки (TTS)
    update_status("🎙️ Создаю аудио-выжимку...")
    try:
        clean_text = response.text.replace('*', '').replace('#', '')
        # Самый надежный способ: сохранить текст во временный файл, чтобы избежать Command Injection
        clean_path = f"results/{clean_title}_clean.txt"
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(clean_text)
            
        voice = "ru-RU-DmitryNeural"
        os.system(f'edge-tts --voice {voice} -f "{clean_path}" --write-media "{tts_audio_path}"')
        
        # Удаляем временный файл текста
        if os.path.exists(clean_path):
            os.remove(clean_path)
            
    except Exception as e:
        print(f"⚠️ Ошибка TTS: {e}")

    # ЭТАП 5: Удаление локального тяжелого аудио
    if os.path.exists(audio_path):
        os.remove(audio_path)
        
    return result_path, tts_audio_path

# --- ТЕЛЕГРАМ БОТ ---

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🚀 Привет! Пришли ссылку на YouTube, и я сделаю аудио-выжимку 80/20 через прямое прослушивание.")

@dp.message(F.text.contains("youtu"))
async def handle_link(message: types.Message):
    status = await message.answer("⏳ Запуск конвейера...")
    
    # Запускаем тяжелую логику в отдельном потоке, чтобы бот не «завис»
    loop = asyncio.get_running_loop()
    res_txt, res_audio = await asyncio.to_thread(analyze_audio, message.text, loop, status)
    
    if res_txt and os.path.exists(res_txt):
        await status.edit_text("✅ Готово! Лови суть:")
        
        # Отправляем аудио-версию
        if res_audio and os.path.exists(res_audio):
            await message.answer_audio(FSInputFile(res_audio), caption="🎧 Голосовая выжимка")
        
        # Отправляем текст
        await message.answer_document(FSInputFile(res_txt), caption="📝 Текстовый отчет 80/20")
    else:
        await status.edit_text("❌ Что-то пошло не так. Проверь логи сервера.")

async def main():
    print("🤖 Бот на базе Gemini Cloud Audio запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())