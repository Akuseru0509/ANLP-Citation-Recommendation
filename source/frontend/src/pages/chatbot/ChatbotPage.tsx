import React from 'react';
import './ChatbotPage.css';

const ChatbotPage: React.FC = () => {
  return (
    <div className="chatbot-page">
      <div className="glass-panel chatbot-container" id="chatbot-container">
        <div className="panel-header">
          <h2>
            <span className="icon">🤖</span> Chatbot
          </h2>
          <p>Ask questions about papers &amp; citations</p>
        </div>

        <div className="chatbot-body">
          <div className="chatbot-placeholder">
            <div className="placeholder-icon">💬</div>
            <h3>Coming Soon</h3>
            <p>
              The citation Q&amp;A chatbot is under development. You'll be able to ask
              questions about papers, explore citation networks, and get research
              recommendations here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotPage;
