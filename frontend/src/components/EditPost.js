import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import '../App.css';
import API_BASE_URL from '../config';

function EditPost() {
    const { token } = useParams();

    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState('');

    useEffect(() => {
        const fetchDraft = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/blog/draft/${token}`);
                if (!response.ok) throw new Error(`Nie znaleziono wersji roboczej. Status: ${response.status}`);
                const data = await response.json();
                setTitle(data.title);
                setContent(data.content);
            } catch (e) {
                setError(e.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchDraft();
    }, [token]);

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

    if (isLoading) {
        return <div className="content-section"><h2>Ładowanie edytora...</h2></div>;
    }

    if (error && !message) {
        return <div className="content-section"><h2>Błąd</h2><p className="error-message">{error}</p><Link to="/">Wróć na stronę główną</Link></div>;
    }

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
                    <header className="edit-post-header">
                        <h2>Edytuj Post</h2>
                        <button onClick={handleFinalSave} disabled={isSaving}>
                            {isSaving ? 'Publikowanie...' : 'Opublikuj Post'}
                        </button>
                    </header>

                    <div className="editor-layout">
                        <div className="main-editor-panel">
                            <label>Tytuł Posta</label>
                            <input
                                type="text"
                                value={title}
                                onChange={e => setTitle(e.target.value)}
                                className="title-input"
                                disabled={isSaving}
                            />
                            <label>Treść Posta</label>
                            <ReactQuill
                                theme="snow"
                                value={content}
                                onChange={setContent}
                                modules={{
                                    toolbar: [
                                        [{ 'header': [1, 2, 3, false] }],
                                        ['bold', 'italic', 'underline', 'strike'],
                                        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                                        ['link', 'clean']
                                    ],
                                }}
                            />
                        </div>
                    </div>
                </>
            )}
        </section>
    );
}

export default EditPost; 