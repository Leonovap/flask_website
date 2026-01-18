
from flask import render_template, Blueprint, abort
from .loader import load_all_posts, get_post_by_slug

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/blog')
def blog_index():
    posts = load_all_posts()
    return render_template('blog.html', posts=posts)

@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    post = get_post_by_slug(slug)
    if not post:
        return render_template('404.html'), 404
    return render_template('blog_post.html', post=post)
