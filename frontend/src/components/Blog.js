import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../App.css';
import API_BASE_URL from '../config';

function createExcerpt(htmlContent, maxLength = 150) {
  // Usuwa tagi HTML, aby uzyskać czysty tekst
  const text = htmlContent.replace(/<[^>]*>/g, '');
  if (text.length <= maxLength) {
    return text;
  }
  // Skraca tekst i dodaje "..."
  return text.substr(0, text.lastIndexOf(' ', maxLength)) + '...';
}

function Blog() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        // Zakładamy, że serwer deweloperski React (port 3000)
        // ma skonfigurowany proxy do serwera Flask (port 5000)
        const response = await fetch(`${API_BASE_URL}/api/blog/posts`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPosts(data);
      } catch (e) {
        console.error("Błąd podczas pobierania postów:", e);
        setError("Nie udało się załadować postów. Spróbuj ponownie później.");
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []); // Pusta tablica zależności oznacza, że efekt uruchomi się tylko raz

  return (
    <section id="blog" className="content-section blog-list-section">
      <h2>Nasz Blog</h2>
      <p>Tutaj dzielimy się wiedzą i ciekawostkami ze świata kotów i drapaków!</p>
      
      {loading && <p>Ładowanie postów...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <div className="blog-post-list">
        {!loading && !error && posts.map(post => (
          <article key={post.id} className="blog-post-summary">
            <h3>
              <Link to={`/blog/${post.id}`}>{post.title}</Link>
            </h3>
            {/* Usunięto subtitle, bo model AI go nie generuje */}
            <p className="post-date">
              Opublikowano: {new Date(post.published_at).toLocaleDateString('pl-PL')}
            </p>
            <p className="excerpt">
              {createExcerpt(post.content)}
            </p>
            <Link to={`/blog/${post.id}`} className="read-more-link">Czytaj dalej...</Link>
          </article>
        ))}
      </div>
    </section>
  );
}

export default Blog; 