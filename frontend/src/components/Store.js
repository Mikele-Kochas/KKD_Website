import React from 'react';
import '../App.css';

function Store() {
  // Kod iframe z Google Maps
  const mapEmbedCode = `<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2548.8043617935155!2d18.7843308!3d50.29557969999999!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x4711336a816f3951%3A0xe655bee844ed496c!2sKoci%20Koci...Drapki*21!5e0!3m2!1spl!2sus!4v1746027887530!5m2!1spl!2sus" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>`;

  return (
    <section id="store" className="content-section">
      <h2>Odwiedź nasz sklep stacjonarny</h2>
      <div className="store-details-flex">
        <div className="store-info">
          <h3>Lokalizacja</h3>
          <p>
            Klonowa 15<br />
            Zabrze, Polska
          </p>
          <h3>Godziny otwarcia</h3>
          <ul>
            <li>Pon. - Sob.: 9:00 – 18:00</li>
          </ul>
          <div className="cta-section" style={{marginTop: '20px'}}>
          
             <h3>Masz pytania? Zapraszamy!</h3>
             <p>
               Szukasz idealnego drapaka lub zdrowej karmy dla swojego kota? Odwiedź nas w naszym sklepie stacjonarnym! Nasi pracownicy z pasją pomogą Ci dokonać najlepszego wyboru dla Twojego pupila. Czekamy na Ciebie i Twojego mruczącego przyjaciela!
             </p>
          </div>
        </div>
        <div className="store-map-wrapper">
          <div dangerouslySetInnerHTML={{ __html: mapEmbedCode }} />
        </div>
      </div>
    </section>
  );
}

export default Store; 