const vimApp = document.getElementById('vim-app');
const apiBase = vimApp ? vimApp.dataset.apiBase : '/api/notes/';
const csrfToken = vimApp ? vimApp.dataset.csrf : '';

async function loadFile(name) {
    document.getElementById('current-filename').value = name;
    const res = await fetch(apiBase + encodeURIComponent(name));
    if (res.ok) {
        const data = await res.json();
        document.getElementById('vim-editor').value = data.content;
        document.getElementById('vim-msg').textContent = `Loaded "${data.filename}"`;
    } else {
        document.getElementById('vim-msg').textContent = `ERROR: Could not load "${name}"`;
    }
}

async function saveCurrentFile() {
    const rawName = document.getElementById('current-filename').value.trim() || 'scratchpad.txt';
    const content = document.getElementById('vim-editor').value;
    
    const res = await fetch(apiBase + encodeURIComponent(rawName), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ content })
    });
    
    if (res.ok) {
        const data = await res.json();
        document.getElementById('current-filename').value = data.filename;
        document.getElementById('vim-msg').textContent = `":w" ${data.filename} written`;
        setTimeout(() => location.reload(), 350);
    } else {
        document.getElementById('vim-msg').textContent = `ERROR: Failed to save (Status ${res.status})`;
    }
}

async function deleteFile(name) {
    if (!confirm(`Delete ${name}?`)) return;
    const res = await fetch(apiBase + encodeURIComponent(name), {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken
        }
    });
    if (res.ok) {
        location.reload();
    } else {
        document.getElementById('vim-msg').textContent = `ERROR: Failed to delete "${name}"`;
    }
}

function deleteCurrentFile() {
    const name = document.getElementById('current-filename').value.trim();
    if (name) deleteFile(name);
}

function createNewFile() {
    document.getElementById('current-filename').value = 'new_note.txt';
    const editor = document.getElementById('vim-editor');
    editor.value = '';
    editor.focus();
    document.getElementById('vim-msg').textContent = 'New buffer opened';
}

function toggleMarkdownPreview() {
    const editor = document.getElementById('vim-editor');
    const preview = document.getElementById('vim-preview');
    const btn = document.getElementById('btn-preview');

    if (preview.style.display === 'none') {
        const rawMd = editor.value;
        preview.innerHTML = DOMPurify.sanitize(marked.parse(rawMd));
        editor.style.display = 'none';
        preview.style.display = 'block';
        btn.textContent = '[:e Edit]';
        document.getElementById('vim-mode').textContent = '-- PREVIEW MODE --';
    } else {
        preview.style.display = 'none';
        editor.style.display = 'block';
        btn.textContent = '[:md Preview]';
        document.getElementById('vim-mode').textContent = '-- INSERT --';
    }
}

function togglePublishBar() {
    const bar = document.getElementById('publish-bar');
    const dateInput = document.getElementById('post-date');
    if (!dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    bar.style.display = bar.style.display === 'none' ? 'block' : 'none';
}

async function publishToBlog() {
    const publishUrl = vimApp.dataset.publishUrl;
    const title = document.getElementById('post-title').value.trim();
    const author = document.getElementById('post-author').value.trim();
    const pub_date = document.getElementById('post-date').value;
    const content = document.getElementById('vim-editor').value.trim();

    if (!title || !content) {
        document.getElementById('vim-msg').textContent = 'ERROR: Title and content required to publish!';
        return;
    }

    const res = await fetch(publishUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ title, author, pub_date, content })
    });

    if (res.ok) {
        const data = await res.json();
        document.getElementById('vim-msg').textContent = `[+] PUBLISHED: /blog/${data.slug}`;
        document.getElementById('publish-bar').style.display = 'none';
    } else {
        document.getElementById('vim-msg').textContent = 'ERROR: Failed to publish post';
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const editor = document.getElementById('vim-editor');
    const filenameInput = document.getElementById('current-filename');

    if (editor) {
        // Поддержка Tab внутри textarea (4 пробела)
        editor.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 4;
            }
        });
    }

    // Хоткей Ctrl+S
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
            e.preventDefault();
            saveCurrentFile();
        }
    });

    // Автозагрузка первого файла при открытии страницы
    if (filenameInput && filenameInput.value) {
        loadFile(filenameInput.value);
    }
});