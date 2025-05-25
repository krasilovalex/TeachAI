import faiss
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup


#
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


# Parse Habr

def get_habr_article(topic):
    search_url = f"https://habr.com/ru/search/?q={topic}&target_type=posts"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        print(f"Ошибка получения данных: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify())  # Выводим HTML-структуру страницы для диагностики

    articles = soup.find_all("article", class_="tm-articles-list_ime", limit=5)  # Получаем 5 статей

    results = []
    for article in articles:
        title_tag = article.find("a", class_="tm-title-link")
        if title_tag:
            title = title_tag.text.strip()
            link = "https://habr.com" + title_tag["href"]

            # Получаем текст статьи по ссылке
            article_page = requests.get(link, headers=headers)
            article_soup = BeautifulSoup(article_page.text, "html.parser")
            article_text = article_soup.find("div", class_="tm-article-body").get_text(strip=True)

            results.append({'title': title, 'link': link, 'text': article_text})  # Сохраняем текст статьи

    return results


# Функция FAISS
def create_faiss_index(articles):
    if not articles:
        return None  # Возвращаем None, если нет статей
    
    # Преобразование текста статей в эмбеддинги
    embeddings = [model.encode(article['text']) for article in articles]
    
    # Проверка на пустые эмбеддинги
    if not embeddings or len(embeddings[0]) == 0:
        return None  # Если эмбеддинги пусты, возвращаем None
    
    embeddings = np.array(embeddings).astype('float32')
    
    # Проверка на правильную форму эмбеддингов
    if embeddings.shape[1] == 0:
        return None  # Если форма эмбеддингов неправильная, возвращаем None
    
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

def load_faiss_index():
    try:
        index = faiss.read_index("habr_articles.index")
    except:
        index = None
    return index

def search_faiss(query, index, articles):
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding).astype('float32')
    _, indices = index.search(query_embedding, 5)  # Ищем 5 наиболее похожих статей
    return [articles[i] for i in indices[0]]


