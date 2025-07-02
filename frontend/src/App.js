import React, { useState, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CSSTransition } from 'react-transition-group';
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './components/Home';
import Store from './components/Store';
import Blog from './components/Blog';
import BlogPost from './components/BlogPost';
import Contact from './components/Contact';
import EditPost from './components/EditPost';
import ChatbotIcon from './components/ChatbotIcon';
import ChatWindow from './components/ChatWindow';

function App() {
  const [isChatVisible, setChatVisible] = useState(false);
  const chatNodeRef = useRef(null);

  return (
    <Router>
      <div className="page-wrapper">
        <div className="App">
          <Header />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/sklep" element={<Store />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/blog/:id" element={<BlogPost />} />
              <Route path="/blog/edit/:token" element={<EditPost />} />
              <Route path="/kontakt" element={<Contact />} />
            </Routes>
          </main>
        </div>
        <Footer />
        <ChatbotIcon onClick={() => setChatVisible(true)} />
        <CSSTransition
          in={isChatVisible}
          nodeRef={chatNodeRef}
          timeout={300}
          classNames="chat-window-transition"
          unmountOnExit
        >
          <ChatWindow ref={chatNodeRef} onClose={() => setChatVisible(false)} />
        </CSSTransition>
      </div>
    </Router>
  );
}

export default App;
