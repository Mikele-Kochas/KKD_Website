import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css'; // Style dla edytora
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import '../App.css'; // Nasze customowe styles
import API_BASE_URL from '../config';

// Komponent dla modala porównującego zmiany
const SuggestionModal = ({ oldContent, newContent, onAccept, onReject }) => {
    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Sugestia zmian</h2>
                <p>Sprawdź poniższe zmiany i zdecyduj, czy chcesz je zaakceptować.</p>
                <ReactDiffViewer
                    oldValue={oldContent}
                    newValue={newContent}
                    splitView={true}
                    compareMethod={DiffMethod.WORDS}
                    leftTitle="Wersja oryginalna"
                    rightTitle="Wersja sugerowana"
                />
                <div className="modal-actions">
                    <button onClick={onAccept} className="button-accept">Zaakceptuj zmiany</button>
                    <button onClick={onReject} className="button-reject">Odrzuć</button>
                </div>
            </div>
        </div>
    );
};

function EditPost() {
    const { token } = useParams();
    // Stan posta
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const originalPost = useRef(null); // Przechowujemy oryginał do porównań

    // Stan UI
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isSuggesting, setIsSuggesting] = useState(false);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState('');

    // Stan AI
    const [aiPrompt, setAiPrompt] = useState(''); // Przywracamy stan dla custom promptu
    const [suggestion, setSuggestion] = useState(null);
    const quillRef = useRef(null);

    useEffect(() => {
        const fetchDraft = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/blog/draft/${token}`);
                if (!response.ok) {
                    throw new Error('Nie znaleziono wersji roboczej posta lub wystąpił błąd.');
                }
                const data = await response.json();
                setTitle(data.title);
                setContent(data.content);
                originalPost.current = data; // Zapisz oryginał
            } catch (e) {
                setError(e.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchDraft();
    }, [token]);
    
    // Zmodyfikowana obsługa generowania sugestii
    const handleGetSuggestion = async (prompt) => {
        setIsSuggesting(true);
        setError(null);

        const editor = quillRef.current.getEditor();
        const selection = editor.getSelection();
        const context = selection && selection.length > 0 ? editor.getText(selection.index, selection.length) : content;
        
        // Używamy promptu przekazanego jako argument, domyślnie z pola tekstowego
        const finalPrompt = prompt || aiPrompt; 

        if (!finalPrompt) {
            setError("Polecenie dla AI nie może być puste.");
            setIsSuggesting(false);
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/blog/suggest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: finalPrompt, title, content, context }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Błąd serwera AI');
            
            setSuggestion(data);

        } catch (e) {
            setError(e.message);
        } finally {
            setIsSuggesting(false);
        }
    };

    // Obsługa finalnego zapisu
    const handleFinalSave = async () => {
        setIsSaving(true);
        setError(null);
        setMessage('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/blog/edit/${token}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Nie udało się zapisać zmian.');
            setMessage('Post został pomyślnie opublikowany! Możesz teraz wrócić na stronę główną lub zamknąć to okno.');
        } catch (e) {
            setError(e.message);
        } finally {
            setIsSaving(false);
        }
    };
    
    // Akcje dla modala
    const acceptSuggestion = () => {
        if(suggestion.title) setTitle(suggestion.title);
        if(suggestion.content) setContent(suggestion.content);
        setSuggestion(null); // Zamknij modal
        setAiPrompt(''); // Wyczyść pole promptu
    };

    const rejectSuggestion = () => {
        setSuggestion(null); // Zamknij modal
    };

    if (isLoading) return <div className="content-section"><h2>Ładowanie edytora...</h2></div>;
    if (error && !message) return <div className="content-section"><h2>Błąd</h2><p className="error-message">{error}</p><Link to="/">Wróć na stronę główną</Link></div>;

    return (
        <section className="content-section edit-post-container">
            {message ? (
                <div className="success-message">
                    <h3>Sukces!</h3>
                    <p>{message}</p>
                    <Link to="/">Wróć na stronę główną</Link>
                </div>
            ) : (
                <>
                    {suggestion && (
                        <SuggestionModal 
                            oldContent={suggestion.title ? `<h1>${originalPost.current.title}</h1>${originalPost.current.content}` : content}
                            newContent={suggestion.title ? `<h1>${suggestion.title}</h1>${suggestion.content}` : suggestion.content}
                            onAccept={acceptSuggestion}
                            onReject={rejectSuggestion}
                        />
                    )}
                    <header className="edit-post-header">
                        <h2>Interaktywny Edytor Posta</h2>
                        <button onClick={handleFinalSave} disabled={isSaving || isSuggesting}>
                            {isSaving ? 'Publikowanie...' : 'Opublikuj Post'}
                        </button>
                    </header>

                    {error && <p className="error-message">{error}</p>}

                    <div className="editor-layout">
                        <div className="main-editor-panel">
                            <label>Tytuł Posta</label>
                            <input 
                                type="text"
                                value={title}
                                onChange={e => setTitle(e.target.value)}
                                className="title-input"
                                disabled={isSaving || isSuggesting}
                            />
                            <label>Treść Posta</label>
                             <ReactQuill
                                ref={quillRef}
                                theme="snow"
                                value={content}
                                onChange={setContent}
                                modules={{
                                    toolbar: [
                                        [{ 'header': [1, 2, 3, false] }],
                                        ['bold', 'italic', 'underline', 'strike'],
                                        [{'list': 'ordered'}, {'list': 'bullet'}],
                                        ['link', 'clean']
                                    ],
                                }}
                            />
                        </div>
                        <div className="ai-tools-panel">
                            <h3>Asystent AI</h3>
                             <div className="quick-actions">
                                <h4>Szybkie akcje:</h4>
                                <button onClick={() => handleGetSuggestion('Popraw stylistykę i gramatykę tego tekstu')} disabled={isSuggesting || isSaving}>Lekka redakcja</button>
                                <button onClick={() => handleGetSuggestion('Przepisz ten tekst, aby był bardziej angażujący i profesjonalny')} disabled={isSuggesting || isSaving}>Głęboka redakcja</button>
                                <button onClick={() => handleGetSuggestion('Zaproponuj 5 alternatywnych tytułów dla tego artykułu')} disabled={isSuggesting || isSaving}>Zaproponuj tytuły</button>
                            </div>
                            <div className="custom-action">
                                <h4>Redakcja niestandardowa:</h4>
                                <textarea
                                    value={aiPrompt}
                                    onChange={e => setAiPrompt(e.target.value)}
                                    placeholder="Wpisz własne polecenie, np. 'Skróć tekst o połowę' lub 'Dodaj na końcu akapit o bezpieczeństwie kotów w domu'"
                                    rows="4"
                                    disabled={isSuggesting || isSaving}
                                />
                                <button onClick={() => handleGetSuggestion()} disabled={!aiPrompt || isSuggesting || isSaving}>
                                    {isSuggesting ? 'Przetwarzam...' : 'Wykonaj polecenie'}
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </section>
    );
}

export default EditPost; 