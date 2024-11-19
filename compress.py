import os
import subprocess
import time

# Параметры по умолчанию
default_target_size_mb = 94
output_suffix = ""
output_subfolder = "Compressed"
supported_extensions = (".mp4", ".mkv", ".avi", ".mov", ".webm")

# Запрашиваем путь к папке
input_folder = input("Введите путь к папке c видеофайлами (по умолчанию директория со скриптом):\n").strip()
if not input_folder:
    # Установить текущую директорию на папку, где находится скрипт
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    input_folder = os.getcwd()

# Собираем список подходящих файлов
video_files = [
    f for f in os.listdir(input_folder)
    if os.path.isfile(os.path.join(input_folder, f)) and  # Это файл
    not f.startswith(".") and                            # Не скрытый файл
    f.lower().endswith(supported_extensions)             # Поддерживаемое расширение
]

# Если подходящих файлов нет, выводим сообщение и выходим
if not video_files:
    print("В папке нет ни одного подходящего видеофайла для конвертации.")
    exit(0)

# Запрашиваем целевой размер файла
target_size_mb = input(f"Введите целевой размер файла в МБ (по умолчанию {default_target_size_mb} МБ):\n").strip()
if not target_size_mb:
    target_size_mb = default_target_size_mb
else:
    target_size_mb = int(target_size_mb)

# Создаём папку для выходных файлов
output_folder = os.path.join(input_folder, output_subfolder)  # Определяем путь к подпапке
os.makedirs(output_folder, exist_ok=True)  # Создаём папку, если её нет

def get_hardware_acceleration():
    """Проверяет доступные видеоускорения и возвращает подходящий кодек."""
    try:
        # Получаем список поддерживаемых аппаратных ускорений
        result = subprocess.run(
            ["ffmpeg", "-hwaccels"], capture_output=True, text=True, check=True
        )
        available_hwaccels = result.stdout.lower()

        if "cuda" in available_hwaccels:
            print("Аппаратное ускорение NVIDIA (CUDA) доступно и используется.")
            return "h264_nvenc"
        elif "qsv" in available_hwaccels:
            print("Аппаратное ускорение Intel (QuickSync Video) доступно и используется.")
            return "h264_qsv"
        elif "amf" in available_hwaccels:
            print("Аппаратное ускорение AMD (AMF) доступно и используется.")
            return "h264_amf"
        elif "videotoolbox" in available_hwaccels:
            print("Аппаратное ускорение Apple (VideoToolbox) доступно и используется.")
            return "h264_videotoolbox"
        else:
            print("Аппаратное ускорение недоступно, используется программное кодирование и используется.")
            return "libx264"
    except Exception as e:
        print(f"Ошибка при проверке видеоускорения: {e}")
        return "libx264"

def calculate_bitrate(file_path, target_size_mb):
    """Рассчитывает видеобитрейт на основе длительности файла и целевого размера."""
    cmd = [
        "ffprobe", "-i", file_path,
        "-show_entries", "format=duration",
        "-v", "quiet", "-of", "csv=p=0"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not result.stdout.strip():
        raise ValueError(f"Не удалось определить длительность для файла: {file_path}")

    try:
        duration = float(result.stdout.strip())  # Длительность видео в секундах
    except ValueError:
        raise ValueError(f"Некорректный формат длительности: {result.stdout.strip()} для файла: {file_path}")

    target_size_bits = target_size_mb * 1024 * 1024 * 8
    audio_bitrate_kbps = 96
    total_bitrate_kbps = target_size_bits / duration / 1000
    video_bitrate_kbps = total_bitrate_kbps - audio_bitrate_kbps

    return max(100, video_bitrate_kbps)  # Минимальный видеобитрейт = 100 кбит/с

def compress_video(file_path, output_path, video_bitrate, encoder):
    """Сжимает видео в два прохода."""
    log_file = "ffmpeg2pass-0.log"
    log_file_mbtree = "ffmpeg2pass-0.log.mbtree"

    print("  Проход 1/2...")
    subprocess.run([
        "ffmpeg", "-y", "-i", file_path,
        "-c:v", encoder, "-b:v", f"{int(video_bitrate)}k",
        "-pass", "1", "-an", "-f", "null", "/dev/null"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print("  Проход 2/2...")
    subprocess.run([
        "ffmpeg", "-y", "-i", file_path,
        "-c:v", encoder, "-b:v", f"{int(video_bitrate)}k",
        "-c:a", "aac", "-b:a", "96k",
        "-pass", "2", 
        output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Удаляем файлы логов
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(log_file_mbtree):
        os.remove(log_file_mbtree)

def get_file_size(file_path):
    """Возвращает размер файла в МБ."""
    return os.path.getsize(file_path) / (1024 * 1024)

def format_time(seconds):
    """Форматирует время в минуты и секунды, если больше 60 секунд."""
    minutes = seconds // 60
    seconds = seconds % 60
    if minutes > 0:
        return f"{int(minutes)} мин. {int(seconds)} сек."
    else:
        return f"{int(seconds)} сек."

video_encoder = get_hardware_acceleration()
start_time = time.time()  # Начало общего таймера
processed_count = 0  # Счётчик успешно обработанных файлов

# Основной цикл обработки
for filename in video_files:
    input_path = os.path.join(input_folder, filename)
    output_filename = f"{os.path.splitext(filename)[0]}{output_suffix}.mp4"
    output_path = os.path.join(output_folder, output_filename)

    print(f"\nОбрабатывается файл: {filename}...")
    file_start_time = time.time()

    try:
        video_bitrate = calculate_bitrate(input_path, target_size_mb)
        compress_video(input_path, output_path, video_bitrate, video_encoder)

        compressed_size = get_file_size(output_path)
        time_spent = time.time() - file_start_time

        # Форматируем время
        formatted_time = format_time(time_spent)

        # Выводим информацию об успешном сжатии
        print(f"Файл {filename} успешно сжат! ({compressed_size:.2f} МБ за {formatted_time})")

        processed_count += 1
    except Exception as e:
        print(f"Ошибка при обработке файла {filename}: {e}\n")


total_time = time.time() - start_time # Конец общего таймера
print(f"\nВсего обработано {processed_count} файлов за {format_time(total_time)}")
