from flask import Blueprint, render_template, request, abort
from sqlalchemy import or_
from app.blog.models import Post

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/blog')
def blog_index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '', type=str).strip()

    query = Post.query
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            or_(
                Post.title.ilike(search_filter),
                Post.content.ilike(search_filter),
                Post.author.ilike(search_filter)
            )
        )

    pagination = query.order_by(Post.pub_date.desc(), Post.id.desc()).paginate(
        page=page, per_page=5, error_out=False
    )

    return render_template('blog.html', pagination=pagination, posts=pagination.items, q=q)


@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    post = Post.query.filter_by(slug=slug).first()
    if not post:
        abort(404)
    return render_template('blog_post.html', post=post)