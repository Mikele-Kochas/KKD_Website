import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import '../App.css';
import API_BASE_URL from '../config';

function formatDate(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString('pl-PL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default function BlogPost() {
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { id } = useParams();

  useEffect(() => {
    const fetchPost = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/blog/posts/${id}`);
        if (!response.ok) {
          if(response.status === 404) {
             throw new Error('Nie znaleziono takiego posta.');
          }
          throw new Error(`Błąd serwera: ${response.status}`);
        }
        const data = await response.json();
        setPost(data);
      } catch (e) {
        console.error("Failed to fetch blog post:", e);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id]);

  if (loading) {
    return <div className="content-section text-center"><h2>Ładowanie posta...</h2></div>;
  }

  if (error) {
    return (
      <section className="content-section text-center">
        <h2>Błąd</h2>
        <p className="error-message">{error}</p>
        <Link to="/blog" className="back-to-blog-link">
          Wróć do listy
        </Link>
      </section>
    );
  }

  if (!post) {
      return null;
  }

  return (
    <section className="content-section blog-post-section">
        <h1>{post.title}</h1>
        <h2>Opublikowano: {formatDate(post.published_at)}</h2>
        <div 
          className="post-content"
          dangerouslySetInnerHTML={{ __html: post.content }} 
        />
        <Link to="/blog" className="back-to-blog-link">
          &larr; Wróć do listy
        </Link>
    </section>
  );
} 