from flask import Flask,session, request, jsonify, render_template, send_from_directory, redirect, url_for, flash
import os
import psutil
import threading
from colorama import Fore, Style, init
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import socket
import logging
import json
import jwt
from datetime import datetime
from functools import wraps
# Ініціалізація кольорів для Windows
init(autoreset=True)

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# MAC-адреса ПК для Wake-on-LAN
TARGET_MAC_ADDRESS = "D8-BB-C1-96-7B-26"


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
LOG_FILE = "program_logs.json"
USERS_FILE = "users.json"

# Flask додаток
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
LOG_FILE = "program_logs.json"
USERS_FILE = "users.json"



def load_users():

    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, ValueError):
            # If the file is empty or corrupted, initialize it as an empty dictionary
            return {}
    return {}

def save_users(users):

    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)

@app.route('/system_info', methods=['GET'])
def system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return jsonify({
        "cpu_usage": f"{cpu_usage}%",
        "memory": {
            "total": f"{memory.total / (1024**3):.2f} GB",
            "used": f"{memory.used / (1024**3):.2f} GB",
            "percent": f"{memory.percent}%"
        },
        "disk": {
            "total": f"{disk.total / (1024**3):.2f} GB",
            "used": f"{disk.used / (1024**3):.2f} GB",
            "percent": f"{disk.percent}%"
        }
    })

# Декоратор для перевірки токену
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm-password')

        # Load existing users
        users = load_users()

        # Check if username already exists
        if username in users:
            return jsonify({"message": "Ім'я користувача вже існує!"}), 400

        # Validate passwords
        if not username or not password or not confirm_password:
            return jsonify({"message": "Всі поля обов'язкові!"}), 400
        if password != confirm_password:
            return jsonify({"message": "Паролі не співпадають!"}), 400

        # Add new user and save
        users[username] = password
        save_users(users)

        # Redirect to login page after successful registration
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Повертаємо HTML-сторінку для входу
        return render_template('login.html')

    elif request.method == 'POST':
        # Обробка даних форми
        try:
            data = request.get_json() if request.is_json else request.form
            username = data.get('username')
            password = data.get('password')

            logging.info(f"Login attempt: username={username}, password={password}")

            users = load_users()  # Завантаження списку користувачів
            if username in users and users[username] == password:
                session['username'] = username
                logging.info(f"Login successful for user: {username}")
                return jsonify({"message": "Login successful!"}), 200

            logging.warning(f"Invalid login credentials for user: {username}")
            return jsonify({"message": "Invalid login credentials!"}), 401

        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            return jsonify({"message": "An error occurred during login. Please try again later."}), 500

@app.route('/control-panel')
def control_panel():
    # Перевірка, чи користувач увійшов у систему
    if 'username' not in session:
        flash('Будь ласка, увійдіть у систему.')
        return redirect(url_for('login'))

    return render_template('index.html')  # Основна сторінка програми
@app.route('/secure_endpoint', methods=['GET'])
@token_required
def secure_endpoint():
    return jsonify({'message': 'This is a secure endpoint accessible only with a valid token.'})



def log_to_json(action, program_name, status):
    """
    Записує лог у JSON-файл.
    """
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,  # "open" або "close"
        "program_name": program_name,
        "status": status  # "success" або "error"
    }

    # Якщо файл логів не існує, створити його
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as file:
            json.dump([log_entry], file, indent=4)
    else:
        # Додати новий запис до існуючого файлу
        with open(LOG_FILE, 'r+') as file:
            logs = json.load(file)
            logs.append(log_entry)
            file.seek(0)
            json.dump(logs, file, indent=4)


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    action_type = data.get('action')
    if action_type == 'shutdown':
        os.system("shutdown /s /t 0")
        return jsonify({"message": "Комп'ютер вимикається."})
    elif action_type == 'restart':
        os.system("shutdown /r /t 0")
        return jsonify({"message": "Комп'ютер перезавантажується."})
    elif action_type == 'sleep':
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return jsonify({"message": "Комп'ютер входить у режим сну."})
    return jsonify({"message": "Невідома дія."})

# Функція для виконання дій
def execute_action(action):
    if action == "shutdown":
        os.system("shutdown /s /t 1")
    elif action == "restart":
        os.system("shutdown /r /t 1")
    elif action == "sleep":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    else:
        logging.error(f"Unknown action: {action}")

@app.route('/schedule_task', methods=['POST'])
def schedule_task():
    try:
        data = request.json
        action = data.get('action')
        time_in_minutes = data.get('time_in_minutes')

        if not action:
            return jsonify({"error": "Поле 'action' є обов'язковим."}), 400

        if not isinstance(time_in_minutes, (int, float)) or time_in_minutes <= 0:
            return jsonify({"error": "Поле 'time_in_minutes' повинно бути додатним числом."}), 400

        allowed_actions = ["shutdown", "restart", "sleep"]
        if action not in allowed_actions:
            return jsonify({"error": f"Невідома дія '{action}'"}), 400

        threading.Timer(time_in_minutes * 60, execute_action, args=[action]).start()
        logging.info(f"Заплановане завдання: дія '{action}' через {time_in_minutes} хвилин.")

        return jsonify({"message": f"Завдання '{action}' успішно заплановане через {time_in_minutes} хвилин."})
    except Exception as e:
        logging.error(f"Помилка при плануванні завдання: {str(e)}")
        return jsonify({"error": f"Не вдалося запланувати завдання: {str(e)}"}), 500

def find_program_on_disks(program_name):
    """
    Рекурсивний пошук програми на всіх доступних дисках.
    """
    drives = [f"{d.mountpoint}" for d in psutil.disk_partitions() if os.access(d.mountpoint, os.R_OK)]
    for drive in drives:
        for root, dirs, files in os.walk(drive):
            if program_name in files:
                return os.path.join(root, program_name)
    return None


@app.route('/open_program', methods=['POST'])
def open_program():
    """
    Відкриття програми за її назвою.
    """
    data = request.get_json()
    program_name = data.get('program_name')
    if not program_name:
        return jsonify({"error": "Назва програми не вказана."}), 400

    try:
        # Шукаємо програму на всіх дисках
        program_path = find_program_on_disks(program_name)
        if not program_path:
            logging.error(f"Програма '{program_name}' не знайдена.")
            log_to_json("open", program_name, "error")
            return jsonify({"error": f"Програма '{program_name}' не знайдена."}), 404

        logging.info(f"Програма '{program_name}' знайдена за шляхом: {program_path}. Відкриття програми...")
        os.startfile(program_path)
        logging.info(f"Програма '{program_name}' успішно відкрита.")
        log_to_json("open", program_name, "success")
        return jsonify({"message": f"Програма '{program_name}' успішно відкрита!"})
    except Exception as e:
        logging.error(f"Помилка при відкритті програми '{program_name}': {str(e)}")
        log_to_json("open", program_name, "error")
        return jsonify({"error": f"Помилка при відкритті програми: {str(e)}"}), 500

@app.route('/close_program', methods=['POST'])
def close_program():
    """
    Закриття програми за її назвою.
    """
    data = request.get_json()
    program_name = data.get('program_name')
    if not program_name:
        return jsonify({"error": "Назва програми не вказана."}), 400

    try:
        found = False
        for process in psutil.process_iter(['name']):
            if process.info['name'] == program_name:
                logging.info(f"Знайдено запущену програму '{program_name}'. Закриття програми...")
                process.terminate()
                found = True
                logging.info(f"Програма '{program_name}' успішно закрита.")
                log_to_json("close", program_name, "success")
                break
        if not found:
            logging.warning(f"Програма '{program_name}' не знайдена серед запущених.")
            log_to_json("close", program_name, "error")
            return jsonify({"error": f"Програма '{program_name}' не знайдена серед запущених."}), 404
        return jsonify({"message": f"Програма '{program_name}' успішно закрита!"})
    except Exception as e:
        logging.error(f"Помилка при закритті програми '{program_name}': {str(e)}")
        log_to_json("close", program_name, "error")
        return jsonify({"error": f"Помилка при закритті програми: {str(e)}"}), 500

@app.route('/get_audio_devices', methods=['GET'])
def get_audio_devices():
    """
    Повертає список усіх доступних аудіопристроїв.
    """
    try:
        devices = AudioUtilities.GetAllDevices()
        device_list = []

        for device in devices:
            try:
                friendly_name = device.FriendlyName
                state = "Active" if device.State == 1 else "Inactive"

                device_list.append({
                    "name": friendly_name,
                    "state": state
                })
            except Exception as e:
                logging.warning(f"Не вдалося отримати властивості пристрою: {str(e)}")

        logging.info("Список аудіопристроїв отримано успішно.")
        return jsonify(device_list)

    except Exception as e:
        logging.error(f"Помилка під час отримання списку пристроїв: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/get_active_audio_device', methods=['GET'])
def get_active_audio_device():
    """
    Повертає активний аудіопристрій.
    """
    try:
        active_device = AudioUtilities.GetSpeakers()  # Отримання активного пристрою (динаміків)

        if not active_device:
            logging.warning("Активний аудіопристрій не знайдено.")
            return jsonify({"error": "Активний аудіопристрій не знайдено."}), 404

        friendly_name = active_device.FriendlyName

        logging.info(f"Активний аудіопристрій знайдено: {friendly_name}")
        return jsonify({
            "name": friendly_name
        })

    except Exception as e:
        logging.error(f"Помилка під час отримання активного пристрою: {str(e)}")
        return jsonify({"error": f"Помилка під час отримання активного пристрою: {str(e)}"}), 500

@app.route('/set_volume', methods=['POST'])
def set_volume():
    """
    Встановлює гучність для активного аудіопристрою.
    """
    data = request.json
    volume_level = data.get("volume_level")

    if volume_level is None or not (0.0 <= float(volume_level) <= 1.0):
        return jsonify({"error": "volume_level має бути числом від 0.0 до 1.0."}), 400

    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        volume = interface.QueryInterface(IAudioEndpointVolume)

        # Встановлюємо гучність
        volume.SetMasterVolumeLevelScalar(float(volume_level), None)
        return jsonify({"message": f"Гучність встановлена на {volume_level}"})
    except Exception as e:
        return jsonify({"error": f"Не вдалося встановити гучність: {str(e)}"}), 500

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os.system("shutdown /s /t 0")
    return jsonify({"message": "Вимкнення комп'ютера ініційовано."})

@app.route('/restart', methods=['POST'])
def restart():
    os.system("shutdown /r /t 0")
    return jsonify({"message": "Перезавантаження комп'ютера ініційовано."})

@app.route('/sleep', methods=['POST'])
def sleep():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return jsonify({"message": "Комп'ютер переведено у режим сну."})

def send_wake_on_lan(mac_address):
    mac_bytes = bytes.fromhex(mac_address.replace(":", "").replace("-", ""))
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ('<broadcast>', 9))

@app.route('/wake_computer', methods=['POST'])
def wake_computer():
    data = request.get_json()
    mac_address = data.get('mac')

    if not mac_address:
        return jsonify({"message": "MAC-адреса не вказана"}), 400

    try:
        send_wake_on_lan(mac_address)
        return jsonify({"message": f"Магічний пакет надіслано на {mac_address}!"})
    except Exception as e:
        return jsonify({"message": f"Помилка: {str(e)}"}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'static/favicon.ico')

USERS = load_users()
if __name__ == '__main__':
    print(Fore.CYAN + "🌐 Сервер запущено! Ви можете керувати комп'ютером через API.")
    app.run(host='0.0.0.0', port=2000)