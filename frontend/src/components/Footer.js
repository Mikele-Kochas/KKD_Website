import React from 'react';
import '../App.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFacebookF, faInstagram, faTiktok } from '@fortawesome/free-brands-svg-icons';

function Footer() {
  return (
    <footer className="App-footer">
      <div className="footer-content">
        <div className="footer-section footer-contact">
          <h4>Kontakt</h4>
          <p>Telefon: +48 666-668-687</p>
          <p>Email: <a href="mailto:sklep@kocikocidrapki.pl">sklep@kocikocidrapki.pl</a></p>
          <p>ul. Klonowa 15<br />Zabrze, 41-800</p> 
        </div>
        <div className="footer-section footer-social">
          <h4>Znajdź nas</h4>
          <div className="social-icons">
            <a href="https://www.facebook.com/" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
              <FontAwesomeIcon icon={faFacebookF} />
            </a>
            <a href="https://www.instagram.com/" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
              <FontAwesomeIcon icon={faInstagram} />
            </a>
            <a href="https://www.tiktok.com/" target="_blank" rel="noopener noreferrer" aria-label="TikTok">
              <FontAwesomeIcon icon={faTiktok} />
            </a>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} Koci Koci Drapki. Wszelkie prawa zastrzeżone.</p>
      </div>
    </footer>
  );
}

export default Footer; 