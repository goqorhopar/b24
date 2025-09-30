from playwright.sync_api import sync_playwright

COOKIES_PATH = "cookies.json"

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        print("Откройте и авторизуйтесь на всех нужных платформах:")
        print("1. Google Meet: https://accounts.google.com/")
        page.goto("https://accounts.google.com/")
        input("Выполните вход в Google, затем нажмите Enter...")
        print("2. Zoom: https://zoom.us/signin")
        page.goto("https://zoom.us/signin")
        input("Выполните вход в Zoom, затем нажмите Enter...")
        print("3. Яндекс Телемост: https://passport.yandex.ru/auth")
        page.goto("https://passport.yandex.ru/auth")
        input("Выполните вход в Яндекс, затем нажмите Enter...")
        print("4. Контур Толк: https://login.contour.ru/")
        page.goto("https://login.contour.ru/")
        input("Выполните вход в Контур, затем нажмите Enter...")
        # Сохраняем сессию
        context.storage_state(path=COOKIES_PATH)
        print(f"Сессия сохранена в {COOKIES_PATH}. Теперь бот будет автоматически входить на встречи с этими аккаунтами.")
        browser.close()
