import whisper
import sys

def audio_to_text(file_path):
    print(f"🧠 Загружаю ИИ-модель Whisper...")
    model = whisper.load_model("base")
    
    print(f"🎧 Начинаю слушать файл: {file_path}")
    result = model.transcribe(file_path)
    
    text_data = result["text"]
    print("\n✅ Речь распознана!")
    
    # --- НОВЫЙ БЛОК: Сохраняем в файл ---
    output_filename = "transcript.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(text_data)
        
    print(f"📁 Текст успешно сохранен в файл: {output_filename}")

if __name__ == "__main__":
    print("🤖 ИИ-Агент: Модуль распознавания речи")
    
    # Запрашиваем имя файла у пользователя
    user_input = input("Введи имя файла для анализа (например, video.mp4): ").strip()
    
    if user_input:
        # Умная проверка: если ты забыл написать "downloads/", скрипт добавит это сам
        if not user_input.startswith("downloads/"):
            video_file = f"downloads/{user_input}"
        else:
            video_file = user_input
            
        audio_to_text(video_file)
    else:
        print("❌ Имя файла не введено. Завершение работы.")
