import React from 'react';
// import { Link } from 'react-router-dom'; // Użyjemy NavLink
import { NavLink } from 'react-router-dom'; // Przywracamy NavLink dla routingu
import '../App.css'; // Zaimportujmy główne style

function Header() {

  // Usunięta logika płynnego przewijania
  // const scrollToSection = (sectionId) => { ... };
  // const handleNavClick = (e, sectionId) => { ... };

  // Definicja stylu tła
  const headerStyle = {
    backgroundImage: `url(${process.env.PUBLIC_URL + '/images/header.png'})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat'
  };

  return (
    <header className="App-header" style={headerStyle}> {/* Dodanie stylu inline */} 
      <div className="header-content"> {/* Dodajemy wewnętrzny kontener */} 
        {/* Logo jako NavLink do strony głównej */}
        <NavLink to="/" className="logo-link">
           <img src={process.env.PUBLIC_URL + '/images/logo.png'} alt="Koci Koci Drapki Logo" className="logo-img" />
        </NavLink>
        <nav>
          {/* Nowa kolejność linków */}
          <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>Kim jesteśmy?</NavLink> 
          <NavLink to="/blog" className={({ isActive }) => isActive ? 'active' : ''}>Blog</NavLink> 
          <NavLink to="/kontakt" className={({ isActive }) => isActive ? 'active' : ''}>Kontakt</NavLink>
          <NavLink to="/sklep" className={({ isActive }) => isActive ? 'active' : ''}>Sklep stacjonarny</NavLink>
          {/* Usunięte linki Produkty, Opinie, Facebook */}
          <a href="https://sklep.kocikocidrapki.pl/" target="_blank" rel="noopener noreferrer">Sklep online</a>
        </nav>
      </div>
    </header>
  );
}

export default Header; 