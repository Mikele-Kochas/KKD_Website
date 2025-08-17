#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Upewnij się, że katalog 'backend' jest na ścieżce importów
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

# Import fabryki aplikacji i rozszerzenia DB
from api import create_app
from api import db


def main():
    # Tworzymy aplikację (użyje DATABASE_URL z .env lub fallbacku ustawionego w create_app)
    app = create_app()

    with app.app_context():
        print("Tworzę tabele w bazie danych:", app.config.get('SQLALCHEMY_DATABASE_URI'))
        db.create_all()
        print('Inicjalizacja bazy danych zakończona.')


if __name__ == '__main__':
    main()
