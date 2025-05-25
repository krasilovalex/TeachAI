import React, { useEffect, useState } from 'react';
import './App.css'

function App() {
    const [tg, setTg] = useState(null);
    const [prompt, setPrompt] = useState(null);
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(null);

    useEffect(()=> {
        if (window.Telegram.WebApp) {
            const telegram = window.Telegram.WebApp
            telegram.ready();
            telegram.expand();
            setTg(telegram)
        }
    },[]);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const res = await fetch("https://nfiai.netlify.app", {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body : JSON.stringify({
                    prompt,
                    user_id: tg?.initDataUnsafe?.user?.id || 'anonymous'
                })

            });
            const data = await res.json();
            setResponse(data);

        } catch (err) {
            console.error("Ошибка при отправке запроса.", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
          <h1>Промпт-анализатор</h1>
          <textarea
            placeholder="Введите ваш промпт"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
          />
          <button onClick={handleSubmit} disabled={loading || !prompt}>
            {loading ? 'Анализ...' : 'Анализировать'}
          </button>
    
          {response && (
            <div className="result">
              <h2>Результат анализа:</h2>
              <p><strong>Четкость:</strong> {response.clarity}</p>
              <p><strong>Полнота:</strong> {response.completeness}</p>
              <p><strong>Специфичность:</strong> {response.specificity}</p>
              <p><strong>Отзывы LLaMA:</strong> {response.feedback}</p>
              {response.suggestions?.length > 0 && (
                <div>
                  <strong>Рекомендации:</strong>
                  <ul>
                    {response.suggestions.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      );
    }
    
    export default App;

