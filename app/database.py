from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Строка подключения к MySQL
# Формат: mysql+pymysql://пользователь:пароль@localhost:3306/имя_базы
DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/coworking_app"

# Создаём движок SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# Создаём фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()