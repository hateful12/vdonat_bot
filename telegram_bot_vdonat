# Стандартні бібліотеки
import time
import json
import re

# Зовнішні бібліотеки
import requests
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import Update
from bs4 import BeautifulSoup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)

# Встав свій токен бота тут
TOKEN = "7980921102:AAHgQrVa2ErfaQOLv7B_GJG__mDAiCV0s0k"

async def start(update: Update, context: CallbackContext) -> None:
    try:
        message = (
            "👋 *Вітаю!*  \n\n"
            "Я бот для моніторингу збору коштів благодійної ініціативи *вДонат*. Тут ти можеш перевірити стан збору та дізнатися, "
            "скільки ще потрібно зібрати. 💰  \n\n"
            "📌 Для перегляду команд введи `/help`"
        )
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as e:
        print(f"Помилка в команді /start: {e}")  # Логування помилки


async def check_mono_amount(update: Update, context: CallbackContext, silent=False) -> None:
    url = "https://send.monobank.ua/api/handler"
    headers = {
        "sec-ch-ua-platform": "\"Windows\"",
        "Referer": "",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept": "application/json; charset=utf-8; lang=en",
        "sec-ch-ua": "\"Not(A:Brand)\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
        "Content-Type": "text/plain; charset=UTF-8",
        "sec-ch-ua-mobile": "?0"
    }
    
    data = {
        "c": "hello",
        "clientId": "9rUbpd9U6c",
        "referer": "",
        "Pc": "BAxznRTunHbDeDGc6Q2EL6kH0usCYs6c4F/ldGi5POMuzwKjKRkjmgq1JI3WQU4/iydIUFDXBDXUX+pOSK4LHSA="
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        try:
            response_json = response.json()
            jar_amount = response_json.get("jarAmount", "Немає даних")
            real_jar_amount = jar_amount/100
            if silent is False:
                message = f"🏦 *Зібрано на Mono:* `{real_jar_amount} UAH`"
                await update.message.reply_text(message, parse_mode="MarkdownV2")
            return float(real_jar_amount)
        except json.JSONDecodeError:
            await update.message.reply_text("Не вдалося розпарсити відповідь сервера.")
    else:
        await update.message.reply_text(f"Помилка {response.status_code}: {response.text}")
    return 0


async def check_privat_amount(update: Update, context: CallbackContext, silent=False) -> None:
    # Налаштування Selenium
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://next.privat24.ua/send/g1vmn")
        cookies = {c["name"]: c["value"] for c in driver.get_cookies()}

        pubkey = cookies.get("pubkey")
        if not pubkey:
            print("pubkey не знайдено")
            return

        print("pubkey:", pubkey)

        time_now = int(time.time() * 1000)  # Генеруємо поточний timestamp
    
        headers_for_xref = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,uk;q=0.8",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://next.privat24.ua",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://next.privat24.ua/send/g1vmn",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "x-requested-with-alias": "testRandomToken",
            "cookie": f"i18next=uk; pubkey={pubkey}"
        }

        data_for_xref = {
            "lang": "ua",
            "_": time_now
        }

        url_for_xref = f"https://next.privat24.ua/api/p24/init?lang=ua&_={time_now}"

        async with httpx.AsyncClient() as client:
            response = await client.post(url_for_xref, headers=headers_for_xref, json=data_for_xref)

        try:
            xref = response.json()["data"]["xref"]
        except (KeyError, TypeError):
            return

        url_for_get_balance = "https://next.privat24.ua/api/p24/pub/envelopes/pubinfo"

        headers_for_get_balance = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://next.privat24.ua",
            "referer": "https://next.privat24.ua/send/g1vmn",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "cookie": f"i18next=uk; pubkey={pubkey}"
        }

        data_for_get_balance = {
            "xref": xref,
            "refEnv": "SAMDNWFC000123704862",
            "_": int(time.time() * 1000)
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url_for_get_balance, headers=headers_for_get_balance, json=data_for_get_balance)

        if response.status_code == 200:
            try:
                response_json = response.json()
                if "data" in response_json and "availableBalance" in response_json["data"]:
                    collected_amount = response_json["data"]["availableBalance"][:-3] 

                    if silent is False:
                        message = f"🏦 *Зібрано на Privat:* `{collected_amount} UAH`"
                        await update.message.reply_text(message, parse_mode="MarkdownV2")
                    return int(collected_amount)
                else:
                    print("Помилка: у відповіді API немає 'availableBalance'.")
            except httpx.HTTPStatusError:
                print("Помилка: неможливо розпарсити JSON.")
        else:
            print(f"Помилка {response.status_code}: {response.text}")
    finally:
        driver.quit()

async def check_novapay_amount(update:Update, context:CallbackContext, silent=False) -> None:
    # URL, з якого отримуємо HTML
    url = "https://e-com.novapay.ua/case/xfdt7WWURn?og=true"

    # Заголовки для запиту
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://campsite.bio/",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    # Кукі (можливо, доведеться оновлювати перед кожним запитом)
    cookies = {
        "_cfuvid": "ISHldXlRExFMoy021VH_2D13YPXST6sKieLp5IaET30-1740839406690-0.0.1.1-604800000",
        "cf_clearance": "zWFKr6WjNxZ0_ULkqzm20tiETlM6RjEmhSnFKcDrZwc-1740851051-1.2.1.1-XpfSUZu7okk..."
    }

    # Виконання запиту
    response = requests.get(url, headers=headers, cookies=cookies)

    # Вивід HTML-коду сторінки

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

    # Знайти потрібний div за класами
    amount_div = soup.find("div", class_="amount body-15-bold word-uah-en-fixed")
    
    if amount_div:
        amount_text = amount_div.get_text(strip=True)  # Отримуємо текст без зайвих пробілів
        amount = int(re.sub(r"\D", "", amount_text))  # Видаляємо всі нечислові символи (пробіли теж)
        print(amount) 
    else:
        print("Не вдалося знайти суму.")

    if silent is False:
        message = f"🏦 *Зібрано на NovaPay:* {amount} UAH"
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    return int(amount)

    


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обробка вхідних повідомлень"""
    await send_request(update, context)

async def acumulated_sum(update: Update, context: CallbackContext) -> None:
    mono = await check_mono_amount(update, context, silent=True)
    privat = await check_privat_amount(update, context, silent=True)
    novapay = await check_novapay_amount(update, context, silent=True)

    total = mono + privat + novapay
    total_goal = 530000
    progress = (total / total_goal) * 100
    needed_amount = total_goal - total

    # Форматований рядок
    message = (
    f"📊 *Звіт про збір коштів*\n\n"
    f"💰 *Зібрано загалом:* `{total:,.2f} UAH`\n\n"
    f"▫️ *Mono:* `{mono:,.2f}`\n"
    f"▫️ *Приват:* `{privat:,.2f}`\n"
    f"▫️ *NovaPay:* `{novapay:,.2f}`\n\n"
    f"📈 *Прогрес:* `{progress:.2f}%`\n\n"
    f"🔻 *Залишилось зібрати:* `{needed_amount:,.2f} UAH`"
)

    await update.message.reply_text(message, parse_mode="MarkdownV2")

async def help_command(update: Update, context: CallbackContext) -> None:
    message = (
        "📌 *Доступні команди:*\n\n"
        "▶️ `/start` – Почати роботу з ботом\n"
        "💳 `/check_mono_amount` – Перевірити баланс Mono\n"
        "🏦 `/check_privat_amount` – Перевірити баланс Privat\n"
        "📮 `/check_novapay_amount` – Перевірити баланс NovaPay\n"
        "📊 `/acumulated_sum` – Переглянути загальну суму збору\n"
        "❓ `/help` – Показати це меню"
    )
    
    await update.message.reply_text(message, parse_mode="MarkdownV2")

def main():
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()

    # Обробники команд і повідомлень
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check_mono_amount", check_mono_amount))
    app.add_handler(CommandHandler("check_privat_amount", check_privat_amount))
    app.add_handler(CommandHandler("check_novapay_amount", check_novapay_amount))
    app.add_handler(CommandHandler("acumulated_sum", acumulated_sum))
    app.add_handler(CommandHandler("help", help_command))

    # Запускаємо бота
    print("Бот запущено!")
    app.run_polling()

if __name__ == "__main__":
    main()
