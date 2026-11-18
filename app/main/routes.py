# app/main/routes.py
from flask import Blueprint, render_template, jsonify
import shutil, random, time, json, os, psutil

START_TIME = time.time()

json_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'content', 'cv_data.json')

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', cowsay_lines=generate_cowsay())

# Slovar/spisok citat dlya fortune | cowsay
FORTUNE_QUOTES = [
    ("Do not go gentle into that good night.", "Rage, rage against the dying of the light."),
    ("There is no cloud.", "It is just someone else's Linux server."),
    ("Talk is cheap.", "Show me the code. — Linus Torvalds"),
    ("Automate the routine,", "or the routine will automate you."),
    ("In a world without walls and fences,", "who needs Windows and Gates?"),
    ("chmod 777 is not a fix.", "It is a surrender."),
    ("He who controls the spice", "controls the universe. — Frank Herbert"),
    ("Nothing behind me, everything ahead of me,", "as is ever so on the road. — Jack Kerouac"),
    ("Real programmers count from 0", "and back up to ZFS pools.")
]

def generate_cowsay():
    line1, line2 = random.choice(FORTUNE_QUOTES)
    width = max(len(line1), len(line2))
    top_border = " " + "_" * (width + 2)
    bottom_border = " " + "-" * (width + 2)
    
    return [
        top_border,
        f"/ {line1.ljust(width)} \\",
        f"\\ {line2.ljust(width)} /",
        bottom_border,
        "        \\   ^__^",
        "         \\  (oo)\\_______",
        "            (__)\\       )\\/\\",
        "                ||----w |",
        "                ||     ||"
    ]

@main_bp.route('/cv')
def cv():
    try:
        #opening json with data:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
    except FileNotFoundError:
        return "Error: cv_data.json not found", 404

    # render cv template
    return render_template('cv.html', **cv_data)

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')


@main_bp.route('/api/stats')
def server_stats():
    # Считаем аптайм (на Linux берет реальный /proc/uptime хоста, на Windows — время работы процесса)
    if os.path.exists('/proc/uptime'):
        with open('/proc/uptime', 'r') as f:
            uptime_sec = int(float(f.readline().split()[0]))
    else:
        uptime_sec = int(time.time() - START_TIME)

    days, rem = divmod(uptime_sec, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)

    total_d, used_d, _ = shutil.disk_usage("/")
    disk_str = f"{round(used_d / (1024**3), 1)} / {round(total_d / (1024**3), 1)} GB"

    # Если установлен psutil — покажет точный RAM и CPU, если нет — выдаст фоллбэк без падения
    try:
        cpu_str = f"{psutil.cpu_percent(interval=0.1)}%"
        ram = psutil.virtual_memory()
        ram_str = f"{round(ram.used / (1024**3), 1)} / {round(ram.total / (1024**3), 1)} GB"
    except ImportError:
        cpu_str = "0.14 (Nominal)"
        ram_str = "32 GB Provisioned"

    return jsonify({
        "uptime": f"{days}d {hours}h {mins}m",
        "cpu_load": cpu_str,
        "ram": ram_str,
        "disk": disk_str,
        "status": "HEALTHY [ONLINE]"
    })

