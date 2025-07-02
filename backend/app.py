import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
import threading
import time
import json
import random
from datetime import datetime, timezone
import secrets
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Konfiguracja Bazy Danych ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Upewnij się, że używamy dialektu 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Dodaj sslmode=require, jeśli go brakuje, dla połączeń z Render
    if DATABASE_URL.startswith("postgresql://") and "sslmode" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Model Bazy Danych ---
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

# Tworzenie tabel w bazie danych
with app.app_context():
    db.create_all()
    logging.info("Tabele bazy danych zostały utworzone/sprawdzone.")

# --- Konfiguracja Google Generative AI ---
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    logging.error("Nie znaleziono klucza API Google w zmiennych środowiskowych!")
    genaikey_configured = False
else:
    try:
        genai.configure(api_key=api_key)
        genaikey_configured = True
        logging.info("Konfiguracja Google Generative AI zakończona sukcesem.")
    except Exception as e:
        logging.error(f"Błąd podczas konfiguracji Google Generative AI: {e}")
        genaikey_configured = False

# --- Konfiguracja serwera e-mail ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000") # URL serwera frontendu

def get_gemini_model(model_name='gemini-1.5-flash'):
    if not genaikey_configured:
        return None
    try:
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        logging.error(f"Błąd podczas tworzenia modelu Gemini ({model_name}): {e}")
        return None

# --- Logika Bloga ---

BLOG_TOPICS = [
    "Dlaczego mamy w sprzedaży mały wybór karm suchych - uzasadnienie zdrowotne i alternatywy.",
    "Pierwszy kot w domu: Niezbędna wyprawka i przygotowanie mieszkania.",
    "Mój kot nie chce jeść mokrej karmy! Jak go do niej przekonać?",
    "Higiena kocich zębów: Jak dbać o uśmiech pupila i zapobiegać chorobom.",
    "Dlaczego kot załatwia się poza kuwetą? Diagnoza problemu i rozwiązania.",
    "Jak wybrać kuwetę idealną dla kota? Wielkość, typ i umiejscowienie.",
    "Kot drapie meble, a nie drapak - jak rozwiązać ten problem?",
    "Jak wybrać idealne miski dla kota, by były wygodne i bezpieczne?",
    "Czy warto kupić kotu fontannę do wody? Zalety i wady.",
    "Jakie zabawki dla kota? Czym najchętniej bawią się nasi mruczący przyjaciele.",
    "Podejrzenie alergii u kota: Jak przeprowadzić dietę eliminacyjną.",
    "Bezpieczny transport kota: Jak przygotować się do podróży.",
    "Kot w podróży: Niezbędnik na krótkie i długie wycieczki.",
    "Czy kota trzeba kąpać? Pielęgnacja sierści i pazurków.",
    "Brak apetytu u kota: Kiedy jest groźny i jak zachęcić go do jedzenia.",
    "Objawy stresu u kota: Jak je rozpoznać i pomóc pupilowi.",
    "Odchowanie osieroconych kociąt: Poradnik krok po kroku.",
    "Rekonwalescencja kota po chorobie lub zabiegu: Jak o niego dbać.",
    "Jak skutecznie podać kotu tabletkę? Sprawdzone sposoby.",
    "Wprowadzenie nowego kota do domu, w którym jest już rezydent."
]

STYLE_EXAMPLE_POST = """
Tytuł: Czy nasze koty naprawdę nie powinny jeść zbóż?

Treść:
<p>Czy zastanawiasz się czasem dlaczego na opakowania karm i przysmaków dla kotów coraz częściej można spotkać znaczek "grain free", czyli bez dodatku zbóż ? Czy to naprawdę istotna informacja i rzeczywiście świadczy o wyższej jakości kupowanych produktów? Czy taka karma jest dla mojego kota zdrowsza czy może to tylko sztuczka marketingowa? A może wystarczające oznakowanie dobrej karmy to "gluten free", czyli bezglutenowy?</p><p>Zacznijmy od określenia kim tak naprawdę są nasze koty? To udomowione od kilku tysięcy lat, ale jednak drapieżniki! I wyłączni mięsożercy. W naturze żywią się niewielkimi zwierzętami, na które polują z wielką precyzją i gracją, ponieważ są do tego doskonale przystosowane. Szczególnie dobrze rozwinięty wzrok, słuch i węch, ostre zęby i pazury, smukła sylwetka, silne mięśnie, bardzo elastyczny układ kostny czynią z nich doskonałych myśliwych. Twój słodki puchaty kotek ma kilkadziesiąt kości szkieletowych więcej, niż Ty! :-) Nasze koty odżywiają się więc przede wszystkim białkiem i tłuszczem zwierzęcym, a węglowodany stanowią ok. 2% ich diety.</p><p>Pierwszy znak stop dla węglowodanów w diecie kota to już ich pyszczek. Zęby kota to zęby typowego drapieżnika i mięsożercy, ostre, bez dużych płaskich powierzchni do żucia pokarmów roślinnych, ale doskonałe do odrywania kawałków mięsa. Ich szczęki również poruszają się tylko w linii pionowej, ruchy boczne pomagające w przeżuwaniu roślin nie są im wcale potrzebne. Dodajmy do tego jeszcze fakt, że ślina kota nie zawiera amylazy ślinowej, czyli enzymu odpowiedzialnego za rozpoczęcie trawienia węglowodanów w organiźmie już w jamie ustnej.</p><p>Kolejne argumenty potwierdzające, że węglowodany nie są odpowiednim pożywieniem dla naszych kotów, znajdziemy w dalszych częściach ich układu pokarmowego. Koty mają stosunkowo krótki żołądek z wysokim stężeniem kwasu solnego, wspomagającym trawienie kości, a krotkie jelito cienkie również zdecydowanie utrudnia trawienie węglowodanów.</p><p>W takim razie "grain free", "gluten free", a może jeszcze inna opcja? Odpowiedzią i kluczem do wyboru zdrowej karmy dla kota są własnie węglowodany, czyli zarówno zboża, jak i np.rośliny strączkowe. Pamiętajmy, że w naturze dieta kota, drapieżnika i wyłącznego mięsożercy, to tylko ok. 2% węglowodanów, czyli tyle ile znajduje się w ciele ofiary, głównie jej żołądku, mięśniach i wątrobie.</p><p>Nadmierne spożycie węglowodanów przez koty niesie ze sobą bardzo duże ryzyko wielu poważnych chorób. Obciąża wątrobę i trzustkę, może prowadzić do cukrzycy, zaburzeń układu pokarmowego, nietolerancji pokarmowych, a także otyłości.</p><p>Najlepszą metodą wyboru zdrowej karmy dla naszych kotów jest dokładne zapoznanie się z jej składem. Przejrzysta lista składników, wysoka zawartość mięsa, brak niepotrzebnych wypełniaczy. A dla zdrowia fizycznego i dobrego samopoczucia pozwalajmy naszym kotom chociaż czasem zapolować na kawałek świeżego, odpowiednio przebadanego czystego mięsa! :-)</p>
"""

def send_approval_email(post, token):
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, RECIPIENT_EMAIL]):
        logging.error("Brak pełnej konfiguracji SMTP. Nie można wysłać e-maila.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Nowy post na bloga do akceptacji: {post['title']}"
    message["From"] = SMTP_USERNAME
    message["To"] = RECIPIENT_EMAIL

    approve_url = f"{BASE_URL}/api/blog/approve/{token}"
    reject_url = f"{BASE_URL}/api/blog/reject/{token}"
    edit_url = f"{FRONTEND_URL}/blog/edit/{token}" # Nowy link do edycji

    html = f"""
    <html>
      <body>
        <h2>Nowy post został wygenerowany i oczekuje na Twoją akceptację.</h2>
        <hr>
        <h3>Tytuł: {post['title']}</h3>
        <div>
          <strong>Treść:</strong>
          {post['content']}
        </div>
        <hr>
        <p><b>Akcja:</b></p>
        <p>
            <a href="{approve_url}" style="padding: 10px 15px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px;">Zatwierdź i Opublikuj</a>
            <a href="{reject_url}" style="padding: 10px 15px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px;">Odrzuć Post</a>
            <a href="{edit_url}" style="padding: 10px 15px; background-color: #ffc107; color: black; text-decoration: none; border-radius: 5px;">Prześlij uwagi do redakcji</a>
        </p>
      </body>
    </html>
    """

    message.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, RECIPIENT_EMAIL, message.as_string())
        logging.info(f"Wysłano e-mail akceptacyjny dla posta '{post['title']}'.")
    except Exception as e:
        logging.error(f"Nie udało się wysłać e-maila: {e}")

def generate_blog_post():
    """Generuje nowy post i zapisuje go jako 'draft' w bazie danych."""
    try:
        model = get_gemini_model()
        if not model:
            logging.error("Nie można utworzyć modelu AI dla generatora bloga.")
            return

        topic = random.choice(BLOG_TOPICS)
        logging.info(f"Wybrano temat na post: {topic}")

        prompt = (
            f"Jesteś ekspertem od kotów i autorem bloga dla sklepu 'Koci Koci Drapki'.\n\n"
            f"Twoim zadaniem jest napisanie wpisu na bloga na temat: '{topic}'.\n\n"
            "Odpowiedź MUSI być pojedynczym obiektem JSON z dwoma kluczami: 'title' (zwięzły, chwytliwy tytuł) i 'content' (treść artykułu w formacie HTML, używając tagów <p> dla akapitów i ewentualnie <strong> lub <em> do wyróżnień).\n\n"
            "Poniżej znajduje się przykładowy artykuł. Użyj go jako wzorca pod względem stylu, tonu, długości i formatowania. Twój artykuł powinien być podobny.\n\n"
            "--- PRZYKŁAD ---\n"
            f"{STYLE_EXAMPLE_POST}\n"
            "--- KONIEC PRZYKŁADU ---\n\n"
            "Artykuł powinien być przyjazny, informacyjny i napisany z pasją, dostarczając wartościowej wiedzy właścicielom kotów.\n"
            "Na końcu artykułu zawrzyj akapit zachęcający do odwiedzenia sklepu stacjonarnego 'Koci Koci Drapki' w Zabrzu lub do kontaktu w celu uzyskania porady.\n\n"
            f"Teraz napisz nowy artykuł na temat: '{topic}'."
        )

        response = model.generate_content(prompt)
        
        response_text = response.text
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1

        if start_index != -1 and end_index != 0:
            json_string = response_text[start_index:end_index]
            try:
                post_data = json.loads(json_string)
            except json.JSONDecodeError as e:
                logging.error(f"Błąd parsowania JSON: {e}\nString: {json_string}")
                return
        else:
            logging.error(f"Nie znaleziono obiektu JSON w odpowiedzi AI.\nOdpowiedź: {response_text}")
            return
        
        if 'title' not in post_data or 'content' not in post_data:
            logging.error("Odpowiedź AI nie zawiera wymaganych kluczy 'title' lub 'content'.")
            return

        token = secrets.token_urlsafe(24)
        new_post = BlogPost(
            title=post_data['title'],
            content=post_data['content'],
            status='draft',
            token=token
        )
        db.session.add(new_post)
        db.session.commit()
        
        logging.info(f"Pomyślnie zapisano wersję roboczą w DB: '{new_post.title}'")
        send_approval_email(post_data, token)

    except Exception as e:
        logging.error(f"Błąd podczas generowania i zapisu posta do DB: {e}")
        db.session.rollback()

def blog_post_scheduler():
    """Sprawdza, czy w bazie danych są wersje robocze i generuje nową, jeśli nie."""
    time.sleep(15)
    with app.app_context(): # Używamy kontekstu aplikacji dla zapytań do DB w wątku
        while True:
            try:
                has_draft = db.session.query(BlogPost).filter_by(status='draft').first()
                if not has_draft:
                    logging.info("Brak wersji roboczych w DB. Generowanie nowego posta...")
                    generate_blog_post()
                else:
                    logging.info("Wersja robocza oczekuje w DB. Pomijanie generowania.")
            except Exception as e:
                logging.error(f"Błąd w harmonogramie (DB): {e}")
            time.sleep(86400) # 24 godziny

@app.route('/api/blog/posts', methods=['GET'])
def get_blog_posts():
    """Zwraca listę opublikowanych postów z bazy danych."""
    posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc()).all()
    posts_list = [{
        'id': p.id, 'title': p.title, 'content': p.content, 
        'published_at': p.published_at.isoformat()
    } for p in posts]
    return jsonify(posts_list)

@app.route('/api/blog/posts/<int:post_id>', methods=['GET'])
def get_blog_post(post_id):
    """Zwraca pojedynczy post z bazy danych."""
    post = BlogPost.query.get(post_id)
    if post and post.status == 'published':
        return jsonify({'id': post.id, 'title': post.title, 'content': post.content, 'published_at': post.published_at.isoformat()})
    return jsonify({"error": "Nie znaleziono takiego posta."}), 404

@app.route('/api/blog/draft/<token>', methods=['GET'])
def get_draft_post(token):
    """Zwraca wersję roboczą posta do edycji."""
    post = BlogPost.query.filter_by(token=token, status='draft').first()
    if post:
        return jsonify({'title': post.title, 'content': post.content})
    return jsonify({"error": "Nie znaleziono wersji roboczej."}), 404

@app.route('/api/blog/suggest', methods=['POST'])
def get_suggestion():
    """
    Przyjmuje treść, tytuł i polecenie, a następnie zwraca sugestię od Gemini.
    Nie modyfikuje żadnych plików.
    """
    data = request.json
    prompt = data.get('prompt')
    title = data.get('title')
    content = data.get('content')
    context = data.get('context') # Opcjonalny, zaznaczony tekst

    if not all([prompt, title, content]):
        return jsonify({"error": "Brakujące dane: prompt, title, content."}), 400

    model = get_gemini_model()
    if not model:
        return jsonify({"error": "Nie można utworzyć modelu AI."}), 500

    if context:
         edit_prompt = (
            f"Jesteś redaktorem bloga. Twoim zadaniem jest poprawienie fragmentu artykułu na podstawie otrzymanych uwag. Skup się tylko na wskazanym fragmencie.\n\n"
            f"CAŁY TYTUŁ: {title}\n"
            f"CAŁY ARTYKUŁ (HTML):\n{content}\n\n"
            f"--- FRAGMENT DO EDYCJI ---\n{context}\n--- KONIEC FRAGMENTU ---\n\n"
            f"--- POLECENIE ---\n{prompt}\n--- KONIEC POLECENIA ---\n\n"
            "Przeredaguj TYLKO wskazany fragment, uwzględniając polecenie. Zwróć całą, pełną treść artykułu po dokonaniu zmiany. "
            "Odpowiedź MUSI być pojedynczym obiektem JSON z jednym kluczem: 'content' (pełna, nowa treść artykułu w formacie HTML)."
        )
    else:
        edit_prompt = (
            f"Jesteś redaktorem bloga. Twoim zadaniem jest poprawienie poniższego artykułu na podstawie otrzymanych uwag.\n\n"
            f"ORYGINALNY TYTUŁ: {title}\n"
            f"ORYGINALNA TREŚĆ (HTML):\n{content}\n\n"
            f"--- POLECENIE ---\n{prompt}\n--- KONIEC POLECENIA ---\n\n"
            "Przeredaguj artykuł, uwzględniając polecenie. Możesz zmienić zarówno tytuł, jak i treść. "
            "Odpowiedź MUSI być pojedynczym obiektem JSON z dwoma kluczami: 'title' (nowy lub poprawiony tytuł) i 'content' (nowa treść artykułu w formacie HTML)."
        )
    
    try:
        response = model.generate_content(edit_prompt)
        response_text = response.text
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1
        json_string = response_text[start_index:end_index]
        
        suggestion_data = json.loads(json_string)

        if 'title' in suggestion_data and suggestion_data['title'] is None:
            suggestion_data.pop('title')
            
        if 'content' in suggestion_data and suggestion_data['content'] is not None:
            content = suggestion_data['content']
            # --- DODANA LOGIKA CZYSZCZĄCA ---
            # Usuwa wszystkie puste tagi <p>, które mogą zawierać spacje lub &nbsp;
            # i które są główną przyczyną nadmiarowych odstępów.
            cleaned_content = re.sub(r'(<p>(\s|&nbsp;)*</p>\s*)+', '', content, flags=re.I)
            suggestion_data['content'] = cleaned_content.strip()
        else:
            suggestion_data.pop('content', None) # Usuń klucz 'content' jeśli jest null
            
        return jsonify(suggestion_data)

    except Exception as e:
        logging.error(f"Błąd podczas generowania sugestii z Gemini: {e}")
        return jsonify({"error": "Wystąpił błąd podczas komunikacji z AI."}), 500

@app.route('/api/blog/edit/<token>', methods=['POST'])
def edit_post(token):
    """Aktualizuje post w DB i zmienia jego status na 'published'."""
    data = request.json
    post = BlogPost.query.filter_by(token=token).first()
    if not post:
        return jsonify({"error": "Nie znaleziono posta o podanym tokenie"}), 404
    
    post.title = data.get('title')
    post.content = data.get('content')
    post.status = 'published'
    post.published_at = datetime.now(timezone.utc)
    db.session.commit()
    
    logging.info(f"Post '{post.title}' został opublikowany przez edytor.")
    return jsonify({"message": "Post został pomyślnie opublikowany!"})

@app.route('/api/blog/approve/<token>', methods=['GET'])
def approve_post(token):
    """Zatwierdza post - zmienia status na 'published'."""
    post = BlogPost.query.filter_by(token=token, status='draft').first()
    if post:
        post.status = 'published'
        post.published_at = datetime.now(timezone.utc)
        db.session.commit()
        return "Post został zatwierdzony i opublikowany!"
    return "Nie znaleziono posta lub został już przetworzony.", 404

@app.route('/api/blog/reject/<token>', methods=['GET'])
def reject_post(token):
    """Odrzuca post - usuwa go z bazy danych."""
    post = BlogPost.query.filter_by(token=token, status='draft').first()
    if post:
        db.session.delete(post)
        db.session.commit()
        return "Post został odrzucony i usunięty."
    return "Nie znaleziono posta lub został już przetworzony.", 404

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    logging.info("Otrzymano zapytanie do /api/chat")
    
    if not genaikey_configured:
        logging.error("API Google AI nie jest skonfigurowane.")
        return jsonify({"error": "Konfiguracja AI nie powiodła się."}), 500
        
    data = request.json
    if not data or 'message' not in data:
        logging.warning("Otrzymano nieprawidłowe dane w zapytaniu.")
        return jsonify({"error": "Brak wiadomości w zapytaniu"}), 400

    user_message = data['message']
    logging.info(f"Otrzymano wiadomość: {user_message}")

    model = get_gemini_model()
    if not model:
         return jsonify({"error": "Nie można utworzyć modelu AI."}), 500

    context = (
        "Jesteś pomocnym asystentem obsługi klienta dla sklepu 'Koci Koci Drapki'. "
        "Sklep specjalizuje się w wysokiej jakości drapakach dla kotów. "
        "Sklep stacjonarny znajduje się w Zabrzu przy ul. Jana III Sobieskiego. "
        "Istnieje również sklep online, ale ta strona służy głównie promocji sklepu stacjonarnego i udzielaniu informacji. "
        "Odpowiadaj krótko i przyjaźnie, koncentrując się na pomocy klientom zainteresowanym ofertą sklepu stacjonarnego i drapakami. "
        "Jeśli nie znasz odpowiedzi, zasugeruj kontakt telefoniczny lub mailowy podany na stronie."
        "\n\nPytanie klienta: "
    )
    
    full_prompt = context + user_message
    logging.info(f"Pełny prompt wysyłany do AI: {full_prompt}")

    try:
        response = model.generate_content(full_prompt) 
        
        if hasattr(response, 'text') and response.text:
            ai_reply = response.text
            logging.info(f"Odpowiedź AI: {ai_reply}")
            return jsonify({"reply": ai_reply})
        else:
            logging.warning("Model AI nie zwrócił tekstu.")
            try:
                logging.warning(f"Prompt feedback: {response.prompt_feedback}")
            except Exception:
                pass 
                
            if response.candidates:
                try:
                    ai_reply = response.candidates[0].content.parts[0].text
                    logging.info(f"Odpowiedź AI (z kandydata): {ai_reply}")
                    return jsonify({"reply": ai_reply})
                except (IndexError, AttributeError, KeyError):
                     logging.warning("Nie znaleziono tekstu w kandydacie odpowiedzi AI.")
                     return jsonify({"reply": "Przepraszam, wystąpił problem z przetworzeniem odpowiedzi."})
            else:
                logging.warning("Model AI nie zwrócił tekstu ani kandydatów.")
                return jsonify({"reply": "Przepraszam, nie mogę przetworzyć tej wiadomości."})

    except Exception as e:
        logging.error(f"Błąd podczas generowania odpowiedzi AI: {e}")
        return jsonify({"error": "Wystąpił błąd podczas komunikacji z AI"}), 500

@app.route('/api/admin/clear-drafts', methods=['POST'])
def force_new_draft():
    """
    Specjalny, tymczasowy endpoint do usunięcia wszystkich istniejących 
    wersji roboczych i wygenerowania nowej.
    """
    try:
        # Ten klucz działa jak proste hasło, aby nikt przypadkowy nie mógł tego uruchomić.
        # W normalnej aplikacji byłoby tu logowanie administratora.
        secret_key = request.headers.get('X-Admin-Key')
        if secret_key != 'KociKociDrapkiSecretKey':
            return jsonify({"error": "Brak autoryzacji"}), 403

        logging.info("ADMIN: Ręczne wymuszenie generowania nowego draftu.")
        
        # Usuń istniejące drafty
        drafts = BlogPost.query.filter_by(status='draft').all()
        num_deleted = len(drafts)
        for draft in drafts:
            db.session.delete(draft)
        db.session.commit()
        logging.info(f"ADMIN: Usunięto {num_deleted} starych wersji roboczych.")
        
        # Wygeneruj nowy post
        generate_blog_post()
        
        return jsonify({"message": f"Pomyślnie usunięto {num_deleted} starych draftów i wygenerowano nowy."}), 200
    except Exception as e:
        logging.error(f"ADMIN: Błąd podczas wymuszania nowego draftu: {e}")
        db.session.rollback()
        return jsonify({"error": "Wystąpił błąd serwera."}), 500

# --- Uruchomienie wątku z harmonogramem ---
# Uruchamiamy wątek w tle, który będzie automatycznie generował posty na bloga.
# Ten kod jest teraz poza blokiem __main__, aby gunicorn go uruchomił.
scheduler_thread = threading.Thread(target=blog_post_scheduler, daemon=True)
scheduler_thread.start()
logging.info("Wątek harmonogramu bloga został uruchomiony.")

if __name__ == '__main__':
    # Ten blok jest teraz używany tylko do lokalnego developmentu.
    # Tworzenie tabel i start wątku dzieje się teraz wyżej w kodzie,
    # aby działało również na serwerze produkcyjnym.
    app.run(debug=True) 