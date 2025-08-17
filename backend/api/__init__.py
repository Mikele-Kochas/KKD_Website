import os
from flask import Flask
from dotenv import load_dotenv
import logging
import threading
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Inicjalizujemy rozszerzenia na poziomie globalnym, ale jeszcze niekonfigurowane.
# Zostaną one powiązane z konkretną aplikacją wewnątrz fabryki.
db = SQLAlchemy()
cors = CORS()

def create_app(test_config=None):
    """
    Fabryka aplikacji. Tworzy i konfiguruje instancję aplikacji Flask.
    """
    # Globalna konfiguracja środowiska i logowania
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # --- Konfiguracja Aplikacji ---
    # Ustawiamy domyślną, a następnie nadpisujemy ją specyficzną dla instancji konfiguracją
    app.config.from_mapping(
        SECRET_KEY='dev', # Domyślny klucz, powinien być nadpisany w produkcji!
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Konfiguracja bazy danych
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Fix dla Render PostgreSQL URL
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        # Dodaj parametry SSL jeśli to PostgreSQL
        if DATABASE_URL.startswith("postgresql://"):
            if "?" not in DATABASE_URL:
                DATABASE_URL += "?"
            else:
                DATABASE_URL += "&"
            DATABASE_URL += "sslmode=require"
            logging.info("Using PostgreSQL database with SSL")

    # Fallback na plik SQLite w katalogu tymczasowym systemu, jeśli nie podano DATABASE_URL
    if not DATABASE_URL:
        import tempfile
        default_db_path = os.path.join(tempfile.gettempdir(), 'kocikocidrapki_test.db')
        default_db_path = os.path.abspath(default_db_path)
        # Upewnij się, że katalog istnieje
        try:
            os.makedirs(os.path.dirname(default_db_path), exist_ok=True)
        except Exception as e:
            logging.error(f"Nie można utworzyć katalogu dla pliku DB: {e}")
        # Na Windows i ogólnie: użyj forward-slash w URI
        uri_path = default_db_path.replace('\\', '/')
        default_db_uri = f"sqlite:///{uri_path}"
        # Spróbuj utworzyć pusty plik DB (jeśli brak uprawnień to zalogujemy błąd)
        try:
            open(default_db_path, 'a').close()
        except Exception as e:
            logging.error(f"Nie można utworzyć pliku bazy danych: {e}")
        DATABASE_URL = default_db_uri
        logging.info(f"Brak DATABASE_URL w środowisku — używam fallbacku: {DATABASE_URL}")

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

    if test_config is None:
        # załaduj konfigurację instancji, jeśli istnieje, gdy nie testujemy
        app.config.from_pyfile('config.py', silent=True)
    else:
        # załaduj konfigurację testową, jeśli została przekazana
        app.config.from_mapping(test_config)

    # --- Inicjalizacja Rozszerzeń ---
    db.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",  # development
                "https://kkd-website-react.onrender.com"  # production frontend
            ]
        }
    })

    # --- Rejestracja Blueprintów (tras) ---
    from . import routes
    app.register_blueprint(routes.bp)

    # --- Rejestracja Modeli i Tworzenie Bazy Danych ---
    # Musimy zaimportować modele tutaj, aby SQLAlchemy o nich wiedziało
    from . import models

    with app.app_context():
        # Diagnostic logging: sprawdźmy URI DB i prawa do pliku (jeśli sqlite)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        logging.info(f"Używane SQLALCHEMY_DATABASE_URI: {db_uri}")
        try:
            if db_uri and db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                db_path = os.path.abspath(db_path)
                logging.info(f"Resolved sqlite path: {db_path}")
                try:
                    logging.info(f"Exists: {os.path.exists(db_path)}")
                    logging.info(f"Is file writable: {os.access(db_path, os.W_OK)}")
                    stat = os.stat(db_path) if os.path.exists(db_path) else None
                    logging.info(f"Stat: {stat}")
                except Exception as e:
                    logging.error(f"Błąd przy sprawdzaniu pliku DB: {e}")

            db.create_all()
            logging.info("Tabele bazy danych zostały utworzone/sprawdzone w kontekście aplikacji.")
        except Exception as e:
            logging.error(f"Błąd podczas db.create_all(): {e}", exc_info=True)
            # Dodatkowo wypisz szczegóły katalogu roboczego i uprawnień
            try:
                cwd = os.path.abspath(os.getcwd())
                logging.error(f"CWD: {cwd}")
                logging.error(f"Temp dir: {tempfile.gettempdir()}")
            except Exception:
                pass
            raise

        # --- Uruchomienie wątku w tle ---
        # Sprawdzamy, czy wątek nie został już uruchomiony (przydatne przy ponownym ładowaniu serwera deweloperskiego)
        if not app.config.get('GENERATOR_THREAD_STARTED'):
            generator_thread = threading.Thread(target=routes.blog_post_generator_thread_starter, args=(app,), daemon=True)
            generator_thread.start()
            app.config['GENERATOR_THREAD_STARTED'] = True
            logging.info("Wątek generatora postów został uruchomiony.")

    return app