from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../storage/vectordb/conversations.db'))
# engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
engine = create_engine(
    f'sqlite:///{DB_PATH}',
    connect_args={"check_same_thread": False},
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)
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