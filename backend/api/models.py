from . import db
from datetime import datetime, timezone

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False, default='draft') # 'draft' lub 'published'
    token = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<BlogPost {self.title}>' 