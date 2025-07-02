import React, { useState, useRef } from 'react';
import '../App.css';
import ChatWindow from './ChatWindow';
import { CSSTransition } from 'react-transition-group';

function ChatbotIcon() {
  const [isOpen, setIsOpen] = useState(false);
  const nodeRef = useRef(null);

  const toggleChat = (event) => {
    event.preventDefault();
    console.log(`TOGGLE: Current isOpen = ${isOpen}. Setting to ${!isOpen}`);
    setIsOpen(prev => !prev);
  };

  return (
    <>
      <div 
        className="chatbot-icon" 
        onClick={(e) => {
          console.log('Chatbot icon clicked!');
          toggleChat(e);
        }}
        title="Porozmawiaj z nami!"
      >
        <img src={process.env.PUBLIC_URL + '/images/icon.png'} alt="" className="chatbot-img" />
      </div>
      
      <CSSTransition
        in={isOpen}            
        timeout={500}          
        classNames="chat-window-transition" 
        unmountOnExit       
        nodeRef={nodeRef} 
      >
        <ChatWindow ref={nodeRef} closeChat={toggleChat} />
      </CSSTransition>
    </>
  );
}

export default ChatbotIcon; 