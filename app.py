def generate_content(topic: str):
   recent_news = get_recent_news(topic)

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
               "content": f"Напишите очень краткое мета-описание (1-2 предложения) для статьи с заголовком '{title}', основываясь на новостях:\n{recent_news}."
           }],
           max_tokens=60,
           temperature=0.5,
           stop=["."]
       ).choices[0].message.content.strip()

       # Генерация развернутого контента поста
       post_content = openai.ChatCompletion.create(
           model="gpt-4o-mini",
           messages=[{
               "role": "user", 
               "content": f"""Напишите очень подробную и структурированную статью на тему '{topic}', основываясь на новостях:\n{recent_news}.

Требования:
1. Минимум 2000 символов
2. Четкая структура с подзаголовками
3. Вступление, основная часть (минимум 3 подраздела), заключение
4. Включить анализ трендов и прогнозы
5. Добавить примеры и цитаты из новостей
6. Каждый абзац минимум 3-4 предложения
7. Текст должен быть легким для чтения и информативным"""
           }],
           max_tokens=2000,
           temperature=0.7,
           presence_penalty=0.6,
           frequency_penalty=0.6
       ).choices[0].message.content.strip()

       return {
           "title": title,
           "meta_description": meta_description,
           "post_content": post_content
       }
   
   except Exception as e:
       raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента: {str(e)}")
