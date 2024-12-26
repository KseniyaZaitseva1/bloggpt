def generate_content(topic: str):
    recent_news = get_recent_news(topic)
    
    if not recent_news:
        raise HTTPException(status_code=400, detail="Не удалось получить актуальные новости по заданной теме.")
    
    try:
        # Генерация заголовка
        title = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"Создайте привлекательный заголовок для статьи на тему '{topic}', с учётом актуальных новостей:\n{recent_news}. Заголовок должен быть интересным и актуальным."
            }],
            max_tokens=50,
            temperature=0.5,
            stop=["\n"]
        ).choices[0].message.content.strip()

        # Генерация краткого мета-описания 
        meta_description = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"Напишите краткое мета-описание для статьи с заголовком '{title}', основываясь на новостях:\n{recent_news}. Описание должно быть информативным и в пределах 150 символов."
            }],
            max_tokens=150,  # Увеличено до 150
            temperature=0.5,
            stop=["."]
        ).choices[0].message.content.strip()

        # Генерация развернутого контента поста
        post_content = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"""Напишите подробную, структурированную статью на тему '{topic}', основываясь на новостях:\n{recent_news}. 

Требования:
1. Минимум 2000 символов
2. Четкая структура с подзаголовками
3. Вступление, основная часть (минимум 3 подраздела), заключение
4. Включить анализ трендов и прогнозы
5. Добавить примеры и цитаты из новостей
6. Каждый абзац минимум 3-4 предложения
7. Текст должен быть легким для чтения и информативным"""
            }],
            max_tokens=1500,  # уменьшено до 1500
            temperature=0.5,  # Температура понижена
            presence_penalty=0.3,  # Уменьшено
            frequency_penalty=0.3  # Уменьшено
        ).choices[0].message.content.strip()

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента: {str(e)}")
