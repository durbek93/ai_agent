import yt_dlp
import os

def download_video(url):
    # Создаем папку для загрузок, если её нет
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Настройки yt-dlp (План "Спецназ" для обхода блокировок)
    ydl_opts = {
        'cookiefile': 'www.youtube.com_cookies.txt', # Твой файл с куками 
        'format': 'bestvideo+bestaudio/best',        # Максимальное качество
        'outtmpl': 'downloads/%(title)s.%(ext)s',    # Путь сохранения файла
        'merge_output_format': 'mp4',                # Склеиваем с помощью FFmpeg
        
        # --- НОВЫЕ НАСТРОЙКИ МАСКИРОВКИ ---
        'http_client': 'curl_cffi',                  # Подменяем сетевой отпечаток
        'extractor_args': {
            'youtube': ['player_client=ios,android'] # Притворяемся мобильным приложением
        },
    }

    print(f"\n--- Начинаю анализ и загрузку: {url} ---")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("\n✅ Успех! Видео сохранено в папку 'downloads'")
        except Exception as e:
            print(f"\n❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    print("🤖 ИИ-Агент: Модуль загрузки видео (Версия 2.0 - Маскировка)")
    video_url = input("Вставь ссылку на видео (Reels или Shorts): ").strip()
    
    if video_url:
        download_video(video_url)
    else:
        print("❌ Ссылка не введена. Запустите скрипт заново.")
