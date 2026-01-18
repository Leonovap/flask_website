
import markdown
from pathlib import Path
from .models import Post

POSTS_DIR = Path(__file__).parent.parent.parent / 'blog_posts'

def slugify(filename: str) -> str:
    return filename.lower().replace(' ', '-').replace('.md', '')

def parse_markdown_file(filepath: Path) -> Post:
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()

    # Title
    title_line = next((line for line in lines if line.startswith('# ')), 'Untitled')
    title = title_line.lstrip('# ').strip()

    # Body
    body_lines = [line for line in lines if line != title_line]
    body_md = ''.join(body_lines).strip()

    # Convert into HTML
    content_html = markdown.markdown(body_md)

    slug = slugify(filepath.stem)

    return Post(title=title, content=content_html, slug=slug)

def load_all_posts() -> list[Post]:
    posts = []
    for file in POSTS_DIR.glob('*.md'):
        try:
            post = parse_markdown_file(file)
            posts.append(post)
        except Exception as e:
            print(f"Reading error {file.name}: {e}")
    return posts

def get_post_by_slug(slug: str) -> Post | None:
    for file in POSTS_DIR.glob('*.md'):
        if slugify(file.stem) == slug:
            return parse_markdown_file(file)
    return None
