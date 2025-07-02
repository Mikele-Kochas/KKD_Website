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
    app = Flask(__name__, instance_relative_config=True)
    
    # Konfiguracja logowania
    logging.basicConfig(level=logging.INFO)
    
    # Załaduj zmienne środowiskowe z pliku .env
    load_dotenv()
    
    # --- Konfiguracja Aplikacji ---
    # Ustawiamy domyślną, a następnie nadpisujemy ją specyficzną dla instancji konfiguracją
    app.config.from_mapping(
        SECRET_KEY='dev', # Domyślny klucz, powinien być nadpisany w produkcji!
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

    if test_config is None:
        # załaduj konfigurację instancji, jeśli istnieje, gdy nie testujemy
        app.config.from_pyfile('config.py', silent=True)
    else:
        # załaduj konfigurację testową, jeśli została przekazana
        app.config.from_mapping(test_config)
        
    # --- Inicjalizacja Rozszerzeń ---
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}) # Lepsza konfiguracja CORS

    # --- Rejestracja Blueprintów (tras) ---
    from . import routes
    app.register_blueprint(routes.bp)

    # --- Rejestracja Modeli i Tworzenie Bazy Danych ---
    # Musimy zaimportować modele tutaj, aby SQLAlchemy o nich wiedziało
    from . import models

    with app.app_context():
        db.create_all()
        logging.info("Tabele bazy danych zostały utworzone/sprawdzone w kontekście aplikacji.")

        # --- Uruchomienie wątku w tle ---
        # Sprawdzamy, czy wątek nie został już uruchomiony (przydatne przy ponownym ładowaniu serwera deweloperskiego)
        if not app.config.get('GENERATOR_THREAD_STARTED'):
            generator_thread = threading.Thread(target=routes.blog_post_generator_thread_starter, args=(app,), daemon=True)
            generator_thread.start()
            app.config['GENERATOR_THREAD_STARTED'] = True
            logging.info("Wątek generatora postów został uruchomiony.")

    return app 