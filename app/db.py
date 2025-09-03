from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../storage/vectordb/conversations.db'))
engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = relationship('Message', back_populates='conversation', cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sources = relationship('Source', back_populates='message', cascade="all, delete-orphan")
    conversation = relationship('Conversation', back_populates='messages')

class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('messages.id'))
    text = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)
    message = relationship('Message', back_populates='sources')


class Feedback(Base):
    __tablename__ = 'ai_assistant_feedback'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(50), nullable=True)
    user_full_name = Column(String(100), nullable=True)
    feedback_type = Column(String(20), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    time_saved = Column(String(50), nullable=True)
    rating = Column(Integer, nullable=True)
    recommend = Column(String(5), nullable=True)
    liked_aspects = Column(Text, nullable=True)
    other_liked = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)
    other_feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.current_timestamp())

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper to create a conversation (optionally with user_id)
def create_conversation(db, user_id=None):
    conv = Conversation(user_id=user_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

# Helper to add a message to a conversation
def add_message(db, conversation_id, role, content):
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# Helper to add a source to a message
def add_source(db, message_id, text, metadata=None):
    src = Source(message_id=message_id, text=text, meta=metadata)
    db.add(src)
    db.commit()
    db.refresh(src)

    return src 

# Helper to add feedback to the database
def add_feedback(db, user_id, username, user_full_name, feedback_type, conversation_id, time_saved, rating, recommend, liked_aspects, other_liked, improvement_suggestions, issues, other_feedback):
    feedback = Feedback(user_id=user_id, username=username, user_full_name=user_full_name, feedback_type=feedback_type, conversation_id=conversation_id, time_saved=time_saved, rating=rating, recommend=recommend, liked_aspects=liked_aspects, other_liked=other_liked, improvement_suggestions=improvement_suggestions, issues=issues, other_feedback=other_feedback)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
