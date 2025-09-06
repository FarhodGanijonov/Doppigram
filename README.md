Real-time Chat System (Doppigram)

  1. Loyihaning asosiy vazifalari
  
    Shaxsiy va guruh chatlarini real vaqt rejimida amalga oshirish.
    
    Har bir xabar uchun read/unread statuslarini kuzatish.
    
    WebSocket orqali xabarlarni instant yetkazish.
    
    Katta hajmli foydalanuvchilar uchun (10k+) real-time prototip yaratish.
  
  2. Foydalanilgan texnologiyalar
  
    Python
    
    Django
    
    Django Channels — WebSocket va real-time aloqa uchun
    
    Redis — message broker va cache uchun
    
    WebSockets — real-time xabar almashish uchun
  
  3. Swagger’dan foydalanish
  
  API hujjatlari Swagger UI orqali taqdim etilgan.
  Swagger sahifasiga kirish uchun serverni ishga tushirgandan so‘ng quyidagiga o‘ting:
  
  http://doppigram.digitallaboratory.uz/swagger/
  
  Swagger sahifasida:
  
  Barcha endpoint’lar ro‘yxatini ko‘rishingiz mumkin.
  Parametrlar va javob misollari bilan tanishish mumkin.
  “Try it out” tugmasi orqali API’ni bevosita sinab ko‘rish mumkin.
  
  3. Ishga tushirish
    git clone https://github.com/FarhodGanijonov/Doppigram.git
    cd Doppigram
    pip install -r requirements.txt
    python manage.py runserver
    
    
    Server ishga tushgandan so‘ng:
    
    API: http://localhost:8000/api/
    
    WebSocket endpoint: ws://localhost:8000/ws/chat/
    
    Admin panel: http://localhost:8000/admin/
  
  👨‍💻 Muallif
  
  Farhod Ganijonov
  Backend Developer (Python/Django, Channels, WebSockets, Redis, Postgresql)
