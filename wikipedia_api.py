import wikipediaapi

# Поиск и получение статьи
def get_wikipedia_summary(query, lang="ru"):
    user_agent = 'TechOlimpBots/1.4 (onexoffalex@gmail.com)'  # Указание user-agent
    
    headers = {
        'User-Agent': user_agent
    }

    
    wiki = wikipediaapi.Wikipedia(lang, headers=headers)
    page = wiki.page(query)

    
    if not page.exists():
        return "Статья не найдена."

    return page.summary[:1000]    

# Функция полной статьи
def get_wikipedia_article_for_llama(query, lang="ru"):
    user_agent = 'TechOlimpBots/1.4 (onexoffalex@gmail.com)'  # Указание user-agent
    
    headers = {
        'User-Agent': user_agent
    }
    
    wiki = wikipediaapi.Wikipedia(lang, headers=headers)
    page = wiki.page(query)

    

    if not page.exists():
        return "Статья не найдена."

    summary = page.summary[:1000]
    title = page.title

    # Можем также извлечь дополнительные разделы, ссылки и другие данные, если нужно
    sections = []
    for section in page.sections:
        sections.append(f"### {section.title}\n{section.text[:500]}...")  # Добавляем только первые 500 символов

    # Собираем весь текст в одну строку
    full_text = f"Заголовок: {title}\n\nКраткое описание:\n{summary}\n\nРазделы:\n" + "\n".join(sections)

    return full_text                
