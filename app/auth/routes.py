
import re, socket , pyotp, hmac , os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.auth.models import User
from app.blog.models import Post
from app.auth.forms import LoginForm, ResetOrRegisterForm
from werkzeug.utils import secure_filename
from datetime import date
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Максимум 5 попыток в минуту с одного IP
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()

        # Проверяем пароль И 6-значный код 2FA
        if user and user.check_password(form.password.data) and user.verify_totp(form.otp_code.data):
            login_user(user)
            return redirect(url_for('auth.dashboard'))
        
        flash('ACCESS DENIED: Invalid credentials or 2FA token.', 'error')

    return render_template('login.html', form=form)


@auth_bp.route('/register-or-reset', methods=['GET', 'POST'])
@limiter.limit("3 per 15 minutes")  # Максимум 3 попытки в 15 минут! Брутфорс невозможен
def register_or_reset():
    form = ResetOrRegisterForm()
    invite_code = os.getenv('INVITE_SECRET_CODE', 'default_secret')
    if not invite_code:
        return "Service disabled: INVITE_SECRET_CODE not configured", 403
    
    if form.validate_on_submit():
        # Защита от timing-атак при сверке секретного инвайт-кода
        if not hmac.compare_digest(form.secret_code.data, invite_code):
            flash('CRITICAL: Invalid Master Invite Code.', 'error')
            return render_template('register_reset.html', form=form), 403

        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()

        if not user:
            # Проверяем, является ли это создание аккаунта первым в системе
            is_first_user = (User.query.count() == 0)
            
            user = User(
                username=username, 
                totp_secret=pyotp.random_base32(),
                is_admin=is_first_user  # Первый зарегистрированный юзер получает права админа!
            )
            db.session.add(user)
        elif not user.totp_secret:
            user.totp_secret = pyotp.random_base32()

        user.set_password(form.password.data)
        db.session.commit()

        # Ссылка и ключ для Google Authenticator / Cisco Duo
        provisioning_uri = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
            name=username, issuer_name="DATAFORGE"
        )
        return render_template(
            'register_reset.html',
            form=form,
            totp_secret=user.totp_secret,
            provisioning_uri=provisioning_uri
        )

    return render_template('register_reset.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@auth_bp.route('/dashboard/admin')
@login_required
@admin_required
def admin_panel():
    posts = Post.query.order_by(Post.pub_date.desc(), Post.id.desc()).all()
    users = User.query.order_by(User.id.asc()).all()
    return render_template('admin_panel.html', posts=posts, users=users)


@auth_bp.route('/dashboard/admin/add-tile', methods=['POST'])
@login_required
@admin_required
def add_tile():
    title = request.form.get('title', '').strip()
    url = request.form.get('url', '').strip()
    description = request.form.get('description', '').strip()
    badge = request.form.get('badge', 'PUBLIC').strip()
    badge_type = request.form.get('badge_type', 'status-online').strip()
    is_admin_only = True if request.form.get('is_admin_only') else False

    if title and url:
        tile = ServiceTile(
            title=title, url=url, description=description,
            badge=badge, badge_type=badge_type, is_admin_only=is_admin_only
        )
        db.session.add(tile)
        db.session.commit()
        flash(f'Service tile "{title}" added.', 'info')
    return redirect(url_for('auth.admin_panel'))


@auth_bp.route('/dashboard/admin/update-access/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_access(user_id):
    user = db.session.get(User, user_id)
    if user and not user.is_admin:
        # Sobiraem vse otmechennye galochki (ha, code, qbit)
        selected = request.form.getlist('services')
        user.allowed_services = ",".join(selected)
        db.session.commit()
        flash(f'Access rights updated for user "{user.username}".', 'info')
    return redirect(url_for('auth.admin_panel'))


def get_notes_dir():
    # Храним заметки в папке instance/notes_storage (рядом с site.db)
    notes_dir = os.path.join(current_app.instance_path, 'notes_storage')
    os.makedirs(notes_dir, exist_ok=True)
    return notes_dir


@auth_bp.route('/dashboard/notebook')
@login_required
def notebook():
    notes_dir = get_notes_dir()
    files = sorted(os.listdir(notes_dir))
    return render_template('notebook.html', files=files)


@auth_bp.route('/api/notes/<path:filename>', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_note(filename):
    notes_dir = get_notes_dir()
    safe_name = secure_filename(filename)
    if not safe_name:
        safe_name = 'scratchpad.txt'
    if not safe_name.endswith(('.txt', '.md', '.sh', '.yaml', '.py', '.json', '.conf')):
        safe_name += '.txt'
        
    filepath = os.path.join(notes_dir, safe_name)

    if request.method == 'GET':
        if not os.path.exists(filepath):
            return jsonify({"content": "", "filename": safe_name})
        with open(filepath, 'r', encoding='utf-8') as f:
            return jsonify({"content": f.read(), "filename": safe_name})

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        content = data.get('content', '')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"status": "saved", "filename": safe_name})

    if request.method == 'DELETE':
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"status": "deleted", "filename": safe_name})



def check_mc_server(host, port, timeout=1.2):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False

@auth_bp.route('/dashboard/minecraft')
@login_required
def minecraft():
    # В .env можно задать MC_INTERNAL_HOST (например, 127.0.0.1 или IP контейнера)
    mc_internal_host = os.getenv('MC_INTERNAL_HOST', 'mc.forgeworld.eu')
    mc_port = os.getenv('MC_PORT', '25565')
    mc_public_domain = os.getenv('MC_PUBLIC_DOMAIN', 'mc.forgeworld.eu')
    gdrive_url = os.getenv('MC_GDRIVE_URL', 'https://drive.google.com/drive/folders/ТВОЯ_ССЫЛКА')

    # Проверяем, залит ли уже архив modpack.zip локально в static/files/
    local_pack_path = os.path.join(current_app.static_folder, 'files', 'modpack.zip')
    has_local_pack = os.path.exists(local_pack_path)

    is_online = check_mc_server(mc_internal_host, mc_port)

    return render_template(
        'minecraft.html',
        mc_domain=mc_public_domain,
        mc_port=mc_port,
        is_online=is_online,
        has_local_pack=has_local_pack,
        gdrive_url=gdrive_url
    )

@auth_bp.route('/api/minecraft/status')
@login_required
def minecraft_status_api():
    mc_internal_host = os.getenv('MC_INTERNAL_HOST', 'mc.forgeworld.eu')
    mc_port = os.getenv('MC_PORT', '25565')
    online = check_mc_server(mc_internal_host, mc_port)
    return jsonify({
        "online": online,
        "status_text": "ONLINE [25565]" if online else "OFFLINE / SLEEP"
    })

@auth_bp.route('/dashboard/minecraft/download')
@login_required
def download_modpack():
    # Как только положишь static/files/modpack.zip на сервер — будет отдавать напрямую через Nginx/Flask
    files_dir = os.path.join(current_app.static_folder, 'files')
    local_file = os.path.join(files_dir, 'modpack.zip')
    if os.path.exists(local_file):
        return send_from_directory(files_dir, 'modpack.zip', as_attachment=True)
    
    # Пока локального файла нет — редиректит на Google Drive
    return redirect(os.getenv('MC_GDRIVE_URL', 'https://drive.google.com/'))




def slugify(text):
    # Простая транслитерация и генерация чистого URL-slug для русских/польских/английских заголовков
    slug = re.sub(r'[^\w\s-]', '', text.lower()).strip()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug or f"post-{int(date.today().strftime('%Y%m%d'))}"

@auth_bp.route('/api/blog/publish', methods=['POST'])
@login_required
def publish_post():
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    author = data.get('author', '').strip() or current_user.username
    pub_date = data.get('pub_date', '').strip() or date.today().isoformat()
    content = data.get('content', '').strip()

    if not title or not content:
        return jsonify({"error": "Title and content required"}), 400

    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    # Если пост с таким заголовком уже есть — обновляем его или добавляем индекс
    existing = Post.query.filter_by(title=title).first()
    if existing:
        existing.author = author
        existing.pub_date = pub_date
        existing.content = content
        db.session.commit()
        return jsonify({"status": "updated", "slug": existing.slug})

    while Post.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    new_post = Post(title=title, slug=slug, author=author, pub_date=pub_date, content=content)
    db.session.add(new_post)
    db.session.commit()
    return jsonify({"status": "published", "slug": slug})


# Панель управления постами и юзерами в Pirate Cave
@auth_bp.route('/dashboard/admin')
@login_required
def admin_panell():
    posts = Post.query.order_by(Post.pub_date.desc(), Post.id.desc()).all()
    users = User.query.order_by(User.id.asc()).all()
    return render_template('admin_panel.html', posts=posts, users=users)


@auth_bp.route('/dashboard/admin/delete-post/<int:post_id>', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        flash(f'Post "{post.title}" deleted.', 'info')
    return redirect(url_for('auth.admin_panel'))


@auth_bp.route('/dashboard/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('ERROR: Cannot delete your own active root session!', 'error')
        return redirect(url_for('auth.admin_panel'))
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{user.username}" terminated.', 'info')
    return redirect(url_for('auth.admin_panel'))


def get_notes_dir():
    """Каждому юзеру — свой изолированный каталог заметок"""
    notes_dir = os.path.join(current_app.instance_path, 'notes_storage', f"user_{current_user.id}")
    os.makedirs(notes_dir, exist_ok=True)
    return notes_dir

