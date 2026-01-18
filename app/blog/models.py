# website/blog/models.py
class Post:
    def __init__(self, title: str, content: str, slug: str):
        self.title = title
        self.content = content
        self.slug = slug
