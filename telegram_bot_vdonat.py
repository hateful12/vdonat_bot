# Стандартні бібліотеки
import time
import json
import re
import asyncio

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
        "clientId": "4dcU5kCTq8",
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
        driver.get("https://next.privat24.ua/send/h0njb")
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
            "referer": "https://next.privat24.ua/send/h0njb",
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
            "referer": "https://next.privat24.ua/send/h0njb",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "cookie": f"i18next=uk; pubkey={pubkey}"
        }

        data_for_get_balance = {
            "xref": xref,
            "refEnv": "SAMDNWFC000127555453",
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
    url = "https://e-com.novapay.ua/case/QJeEes1Y1s?og=true"

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
    script_tag = soup.find("script", string=lambda text: text and "window.__NOVA_DATA__" in text)
    if script_tag:
	    text = script_tag.string

	    # знаходимо шматок JSON
	    match = re.search(r'window\.__NOVA_DATA__\s*=\s*({.*});', text)
	    if match:
	        data_str = match.group(1)
	        data = json.loads(data_str)
	        amount = float(data.get("balance").replace(" ", ""))

    if silent is False:
        message = f"🏦 *Зібрано на NovaPay:* {amount:.2f} UAH".replace(".", "\\.")
        await update.message.reply_text(message, parse_mode="MarkdownV2")

    return amount

    
async def check_minibanker_progress(update: Update, context: CallbackContext) -> None:
    # --- Мінібанкіри ---
    minibankers = context.bot_data.get("minibankers", {})
    minibanker_data = {}
    minibanker_total = 0
    message = ''

    for name, jar_id in minibankers.items():
        try:
            url = "https://send.monobank.ua/api/handler"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json",
            }
            data = {
                "c": "hello",
                "clientId": jar_id,
                "referer": "",
                "Pc": "BAxznRTunHbDeDGc6Q2EL6kH0usCYs6c4F/ldGi5POMuzwKjKRkjmgq1JI3WQU4/iydIUFDXBDXUX+pOSK4LHSA="

            }

            print(f"▶️ Перевіряємо {name}: {jar_id}")
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                response_json = response.json()
                print(response_json)
                jar_amount = response_json.get("jarAmount", 0)
                try:
                    real_jar_amount = float(jar_amount) / 100
                except (ValueError, TypeError):
                    real_jar_amount = 0.0
                    print(f"⚠️ jarAmount не число для {name}: {jar_amount}")

                minibanker_data[name] = real_jar_amount
                minibanker_total += real_jar_amount
            else:
                print(f"❗ Помилка {response.status_code} для {name}: {response.text}")
                await update.message.reply_text(
                    f"❗ Помилка {response.status_code} при запиті до Mono для {name}:\n{response.text}"
                )

        except Exception as e:
            print(f"❗ Виняток у мінібанкіра {name}: {e}")
            await update.message.reply_text(f"❗ Помилка під час обробки мінібанкіра {name}:\n{e}")

    if minibanker_data:
        message += f"\n\n👥 *Збір мінібанкірів:* `{minibanker_total:,.2f} UAH`"
        for name, amount in minibanker_data.items():
            message += f"\n▫️ *{escape_markdown_v2(name)}*: `{amount:,.2f} UAH`"
    else:
        message = 'Ще немає мінібанкірів'
    await update.message.reply_text(message, parse_mode="MarkdownV2")
    
def fetch_minibankers_total(bot_data: dict) -> float:
    mini_total = 0.0
    print(bot_data.get("minibankers", {}).values())
    for jar_id in bot_data.get("minibankers", {}).values():
        resp = requests.post(
            "https://send.monobank.ua/api/handler",
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
            json={"c": "hello", "clientId": jar_id, "referer": "", "Pc": "BAxznRTunHbDeDGc6Q2EL6kH0usCYs6c4F/ldGi5POMuzwKjKRkjmgq1JI3WQU4/iydIUFDXBDXUX+pOSK4LHSA="}
        )
        if resp.status_code == 200:
            jar = resp.json().get("jarAmount", 0)
            mini_total += jar / 100.0
    return mini_total



async def acumulated_sum(update: Update, context: CallbackContext) -> None:
    mono = await check_mono_amount(update, context, silent=True) or 0.0
    privat = await check_privat_amount(update, context, silent=True) or 0.0
    novapay = await check_novapay_amount(update, context, silent=True) or 0.0

    # ——— підрахунок внеску мінібанкірів ———
    minibankers = context.bot_data.get("minibankers", {})
    mini_total = fetch_minibankers_total(context.bot_data)

    total_goal = context.bot_data.get("total_goal", 630000)
    spent = context.bot_data.get("spent_amount", 0)

    total_cards = float(mono) + float(privat) + float(novapay)
    total_all = total_cards + spent
    
    progress = (total_cards + spent) / total_goal * 100
    needed_amount = total_goal - total_cards - spent
    sami_total = total_all - mini_total
    
    message = (
    f"*Всього зібрано:* `{total_all:,.2f} UAH`\n"
    f"*Залишилось зібрати:* `{needed_amount:,.2f} UAH`\n\n"
    f"*Прогрес:* `{progress:.2f}%`\n\n"
    "🏦🏦🏦🏦🏦\n\n"
    f"*Самі зібрали:* `{sami_total:,.2f} UAH`\n"
    f"*Мінібанкіри:* `{mini_total:,.2f} UAH`\n\n"
    "🏦🏦🏦🏦🏦\n\n"
    f"*Вже знято:* `{spent:,.2f} UAH`\n"
    f"*Зараз на рахунках:* `{total_cards:,.2f} UAH`\n\n"
    "🏦🏦🏦🏦🏦\n\n"
    f"*моно:* `{mono:,.2f}`\n"
    f"*приват:* `{privat:,.2f}`\n"
    f"*новапей:* `{novapay:,.2f}`"
)




    # Форматований рядок

    await update.message.reply_text(message, parse_mode="MarkdownV2")

async def help_command(update: Update, context: CallbackContext) -> None:
    message = (
        "📌 *Доступні команди:*\n\n"
        "▶️ `/start` – Почати роботу з ботом\n"
        "💳 `/check_mono_amount` – Перевірити баланс Mono\n"
        "🏦 `/check_privat_amount` – Перевірити баланс Privat\n"
        "📮 `/check_novapay_amount` – Перевірити баланс NovaPay\n"
        "📊 `/acumulated_sum` – Переглянути загальну суму збору\n"
        "😼 `/set_goal` – Змінити цільову суму збору\n"
         "💸 `/set_spent` – Додати суму знятих коштів\n"
        "🥸 `/add_minibanker` – Додати мінібанкіра у форматі: команда Ім'я посилання\n"
         "👶 `/check_minibanker_progress` – Перевірити прогрес мінібанкірів\n"
        "❓ `/help` – Показати це меню"
    )
    
    await update.message.reply_text(message, parse_mode="MarkdownV2")

def escape_markdown_v2(text: str) -> str:
    return re.sub(r'([_\*\[\]\(\)~`>#+=|{}.!-])', r'\\\1', text)


async def set_goal(update: Update, context: CallbackContext) -> None:
    message = update.message
    if message is None:
        return  # Немає текстового повідомлення, нічого відповідати

    try:
        if context.args:
            goal = float(context.args[0].replace(",", "").strip())
            context.bot_data["total_goal"] = goal
            text = f"✅ Цільову суму змінено на {goal:,.2f} UAH"
        else:
            text = "❗️ Будь ласка, введи суму після команди"
    except ValueError:
        text = "❗️ Невірний формат суми. Введи число"

    await message.reply_text(
        escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()


async def set_spent(update: Update, context: CallbackContext) -> None:
    message = update.message
    if message is None:
        return

    try:
        if context.args:
            new_spent = float(context.args[0].replace(",", "").strip())
            current_spent = context.bot_data.get("spent_amount", 0.0)
            updated_spent = current_spent + new_spent
            context.bot_data["spent_amount"] = updated_spent

            text = f"✅ Додано {new_spent:,.2f} UAH до витрачених коштів.\n💸 Загальна сума витрат: {updated_spent:,.2f} UAH"
        else:
            text = "❗️ Будь ласка, введи суму після команди `/set_spent <сума>`"
    except ValueError:
        text = "❗️ Невірний формат суми. Введи число."

    await message.reply_text(
        escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )


async def add_minibanker(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("❗️ Використання: /add_minibanker <ім'я> <посилання на банку Mono>")
        return

    name = context.args[0]
    url = context.args[1]

    # Витягуємо jar_id з URL
    match = re.search(r"jar/([a-zA-Z0-9]+)", url)
    if not match:
        await update.message.reply_text("❗️ Невірний формат посилання. Має містити /jar/<id>")
        return

    jar_id = match.group(1)

    minibankers = context.bot_data.setdefault("minibankers", {})
    minibankers[name] = jar_id

    await update.message.reply_text(
        f"✅ Мінібанкіра *{escape_markdown_v2(name)}* додано",
        parse_mode="MarkdownV2"
    )



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
    app.add_handler(CommandHandler("set_goal", set_goal))
    app.add_handler(CommandHandler("set_spent", set_spent))
    app.add_handler(CommandHandler("add_minibanker", add_minibanker))
    app.add_handler(CommandHandler("check_minibanker_progress", check_minibanker_progress))


    # Запускаємо бота
    print("Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()
