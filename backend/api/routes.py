import os
import google.generativeai as genai
from flask import request, jsonify, Blueprint
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
from urllib.parse import urljoin

# Importujemy instancję db z głównego __init__.py
# (To zadziała, gdy __init__.py zostanie zrefaktoryzowany)
from . import db
from .models import BlogPost

# Tworzymy Blueprint - to jest jak mini-aplikacja, którą potem zarejestrujemy
bp = Blueprint('api', __name__, url_prefix='/api')

# --- Konfiguracja, która jest potrzebna w tym module ---
# Pobieramy zmienne środowiskowe, tak jak wcześniej
genaikey_configured = False
if os.getenv("GOOGLE_API_KEY"):
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        genaikey_configured = True
        logging.info("Konfiguracja Google Generative AI w routes.py zakończona sukcesem.")
    except Exception as e:
        logging.error(f"Błąd podczas konfiguracji Google Generative AI w routes.py: {e}")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# --- Logika Bloga (przeniesiona z app.py) ---

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

def get_gemini_model(model_name='gemini-1.5-flash'):
    if not genaikey_configured:
        return None
    try:
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        logging.error(f"Błąd podczas tworzenia modelu Gemini ({model_name}): {e}")
        return None

def send_approval_email(post, token):
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, RECIPIENT_EMAIL]):
        logging.error("Brak pełnej konfiguracji SMTP. Nie można wysłać e-maila.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Nowy post na bloga do akceptacji: {post['title']}"
    message["From"] = SMTP_USERNAME
    message["To"] = RECIPIENT_EMAIL

    # Poprawka: Dodajemy ręcznie /api/ do ścieżki, ponieważ urljoin nie wie o Blueprintach
    approve_url = urljoin(BASE_URL, f"api/blog/approve/{token}")
    reject_url = urljoin(BASE_URL, f"api/blog/reject/{token}")
    edit_url = urljoin(FRONTEND_URL, f"blog/edit/{token}")

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
            <a href="{edit_url}" style="padding: 10px 15px; background-color: #ffc107; color: black; text-decoration: none; border-radius: 5px;">Edytuj Post</a>
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

def extract_json_from_string(text):
    try:
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and start_index < end_index:
            json_str = text[start_index:end_index+1]
            return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        return None

def generate_blog_post_logic(app):
    with app.app_context():
        try:
            # Sprawdzenie czy istnieje już jakiś draft
            existing_draft = BlogPost.query.filter_by(status='draft').first()
            if existing_draft:
                logging.info("Znaleziono istniejącą wersję roboczą. Pomijam generowanie nowego posta.")
                return

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
            
            blog_data = extract_json_from_string(response.text)
            if not blog_data:
                raise ValueError("Nie znaleziono poprawnego obiektu JSON w odpowiedzi modelu.")

            title = blog_data['title']
            content = blog_data['content']
            
            token = secrets.token_urlsafe(24)
            new_post = BlogPost(
                title=title,
                content=content,
                status='draft',
                token=token
            )
            db.session.add(new_post)
            db.session.commit()
            
            logging.info(f"Pomyślnie zapisano wersję roboczą w DB: '{new_post.title}'")
            send_approval_email(blog_data, token)

        except Exception as e:
            logging.error(f"Błąd w `generate_blog_post_logic`: {e}", exc_info=True)
            if 'response' in locals() and hasattr(response, 'text'):
                logging.error(f"Oryginalna odpowiedź, która spowodowała błąd: {response.text}")
            db.session.rollback()


# --- Endpointy API (teraz używają @bp.route) ---

@bp.route('/blog/posts', methods=['GET'])
def get_blog_posts():
    posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc()).all()
    return jsonify([{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'published_at': post.published_at.isoformat()
    } for post in posts])

@bp.route('/blog/posts/<int:post_id>', methods=['GET'])
def get_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if post.status != 'published':
        return jsonify({'error': 'Post not found or not published'}), 404
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'published_at': post.published_at.isoformat()
    })

@bp.route('/blog/draft/<token>', methods=['GET'])
def get_draft_post(token):
    post = BlogPost.query.filter_by(token=token, status='draft').first()
    if not post:
        return jsonify({'error': 'Draft not found'}), 404
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'token': post.token
    })

@bp.route('/blog/suggest', methods=['POST'])
def get_suggestion():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content'}), 400

    original_content = data['content']
    model = get_gemini_model()
    if not model:
        return jsonify({'error': 'AI model not available'}), 500

    try:
        prompt = (
            f"Otrzymałem następujący tekst, który jest częścią wpisu na bloga o kotach: \n\n"
            f"--- TEKST ---\n{original_content}\n--- KONIEC TEKSTU ---\n\n"
            f"Zaproponuj jeden, zwięzły akapit (w formacie HTML, używając tagu <p>), który można by dodać na końcu tego tekstu. "
            f"Akapit powinien płynnie kontynuować myśl, dodawać ciekawą informację lub stanowić dobre podsumowanie. "
            f"Nie dodawaj żadnych nagłówków ani wstępów typu 'Oto moja propozycja:'. Zwróć tylko i wyłącznie sam tag <p> z treścią."
        )
        response = model.generate_content(prompt)
        suggestion = response.text.replace('```html', '').replace('```', '').strip()
        return jsonify({'suggestion': suggestion})
    except Exception as e:
        logging.error(f"Błąd podczas generowania sugestii: {e}")
        return jsonify({'error': 'Failed to generate suggestion'}), 500


@bp.route('/blog/edit/<token>', methods=['POST'])
def edit_post(token):
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Missing title or content'}), 400

    post = BlogPost.query.filter_by(token=token, status='draft').first_or_404()
    
    post.title = data['title']
    post.content = data['content']
    db.session.commit()
    
    logging.info(f"Zaktualizowano wersję roboczą posta: {post.title}")
    return jsonify({'message': 'Draft updated successfully'})


@bp.route('/blog/approve/<token>', methods=['GET'])
def approve_post(token):
    try:
        post = BlogPost.query.filter_by(token=token, status='draft').first_or_404()
        
        logging.info(f"Znaleziono post '{post.title}' do zatwierdzenia. Zmieniam status na 'published'.")
        post.status = 'published'
        post.published_at = datetime.now(timezone.utc)
        
        db.session.commit()
        logging.info("Zatwierdzono zmiany w sesji (commit).")

        # --- KROK DIAGNOSTYCZNY ---
        # Sprawdzamy, jaki jest status posta w bazie NATYCHMIAST po commicie
        db.session.expire(post) # Wymuszamy odświeżenie obiektu z bazy
        verify_post = BlogPost.query.get(post.id)
        
        if verify_post.status == 'published':
            logging.info("SUKCES: Weryfikacja potwierdziła, że status w DB to 'published'.")
            return "Post został pomyślnie opublikowany! Weryfikacja w bazie danych powiodła się."
        else:
            logging.error(f"KRYTYCZNY BŁĄD: Commit wykonany, ale status w DB to wciąż '{verify_post.status}'!")
            return f"BŁĄD KRYTYCZNY: Serwer myślał, że opublikował post, ale w bazie danych wciąż jest on w stanie '{verify_post.status}'. Skontaktuj się z administratorem."

    except Exception as e:
        db.session.rollback()
        logging.error(f"WYSTĄPIŁ WYJĄTEK podczas próby zatwierdzenia posta: {e}", exc_info=True)
        return "Wystąpił wewnętrzny błąd serwera podczas publikacji. Sprawdź logi."

@bp.route('/blog/reject/<token>', methods=['GET'])
def reject_post(token):
    post = BlogPost.query.filter_by(token=token, status='draft').first_or_404()
    db.session.delete(post)
    db.session.commit()
    return "Post został odrzucony i usunięty. Możesz zamknąć tę kartę."

@bp.route('/chat', methods=['POST'])
def chat_with_ai():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    user_message = data['message']
    model = get_gemini_model()
    if not model:
        return jsonify({'error': 'AI model not available'}), 500

    try:
        response = model.generate_content(user_message)
        return jsonify({'reply': response.text})
    except Exception as e:
        logging.error(f"Błąd podczas komunikacji z AI: {e}")
        return jsonify({'error': 'Failed to get response from AI'}), 500

@bp.route('/admin/clear-drafts', methods=['POST'])
def clear_drafts():
    try:
        num_deleted = db.session.query(BlogPost).filter_by(status='draft').delete()
        db.session.commit()
        logging.info(f"Usunięto {num_deleted} wersji roboczych postów.")
        return jsonify({'message': f'Successfully deleted {num_deleted} draft(s).'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Błąd podczas usuwania wersji roboczych: {e}")
        return jsonify({'error': 'Failed to clear drafts'}), 500

@bp.route('/admin/generate-now', methods=['POST'])
def force_generate_post():
    """
    Manualny endpoint do wymuszenia generowania posta.
    """
    from flask import current_app
    
    logging.info("Ręczne uruchomienie generatora postów...")
    
    # Uruchamiamy logikę w nowym wątku, aby nie blokować odpowiedzi HTTP
    # To jest ważne, bo generowanie + wysyłka maila może chwilę potrwać
    thread = threading.Thread(target=generate_blog_post_logic, args=(current_app._get_current_object(),))
    thread.start()
    
    return jsonify({'message': 'Proces generowania posta został uruchomiony w tle.'}), 202

def blog_post_generator_thread_starter(app):
    """
    Funkcja, która będzie uruchamiana w osobnym wątku.
    """
    while True:
        sleep_time = random.uniform(43200, 86400) # Między 12 a 24 godziny
        logging.info(f"Następny post zostanie wygenerowany za {sleep_time/3600:.2f} godzin.")
        time.sleep(sleep_time)

        logging.info("Rozpoczynanie generowania nowego posta na bloga...")
        generate_blog_post_logic(app) 