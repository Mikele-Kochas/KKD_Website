import React, { useState, useEffect, useRef, forwardRef } from 'react';
import '../App.css';
import API_BASE_URL from '../config';

const ChatWindow = forwardRef(({ onClose }, ref) => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Witaj w Koci Koci Drapki! W czym mogę pomóc?' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isBotTyping, setIsBotTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isBotTyping]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const handleSendMessage = async (event) => {
    event.preventDefault();
    const userMessage = inputValue.trim();
    if (userMessage) {
      setMessages(prevMessages => [...prevMessages, { sender: 'user', text: userMessage }]);
      setInputValue('');
      setIsBotTyping(true);

      try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessage })
        });

        setIsBotTyping(false);
        if (!response.ok) throw new Error(`Błąd HTTP: ${response.status}`);
        
        const data = await response.json();
        if (data && data.reply) {
          setMessages(prevMessages => [...prevMessages, { sender: 'bot', text: data.reply }]);
        } else {
           throw new Error('Nieprawidłowa odpowiedź z serwera');
        }
      } catch (error) {
        setIsBotTyping(false);
        console.error("Błąd podczas komunikacji z chatbotem:", error);
        setMessages(prevMessages => [
          ...prevMessages, 
          { sender: 'bot', text: 'Przepraszam, wystąpił błąd podczas przetwarzania Twojej wiadomości.' }
        ]);
      }
    }
  };

  return (
    <div className="chat-window" ref={ref}>
      <div className="chat-header">
        <span>Wirtualny Asystent</span>
        <button onClick={onClose} className="close-chat-btn">×</button>
      </div>
      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}-message`}>
            {msg.text}
          </div>
        ))}
        {isBotTyping && (
          <div className="message bot-message typing-indicator">
            <span>.</span><span>.</span><span>.</span>
          </div>
        )}
        <div ref={messagesEndRef} /> 
      </div>
      <form className="chat-input-area" onSubmit={handleSendMessage}>
        <input 
          type="text" 
          placeholder="Wpisz wiadomość..." 
          value={inputValue} 
          onChange={handleInputChange} 
          disabled={isBotTyping}
        />
        <button type="submit" disabled={isBotTyping}>Wyślij</button>
      </form>
    </div>
  );
});

export default ChatWindow; 