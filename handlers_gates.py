"""
=================================================================
handlers_gates.py — Real Gate Handlers (Single Check)
IGNISX Bot — Production Grade
=================================================================
يحتوي هذا الملف على جميع الـ 38 Handler للبوابات الحقيقية.
كل handler يستدعي gate_handler.handle_real_gate_command() الموحدة.

التصنيف:
    AUTH (11)   : b31 b32 b33 b3s | st1 st2 sts | sq1 sq2 sq3 sqs
    CHARGE (13) : au1 aus | pp1 pp2 pp3 pps | sqc1 sqc2 sqcs | stc1 stc2 stc3 stcs
    LOOKUP (14) : gp1 gp2 gps | gpp1 gpp2 gpps | vp1 vp2 vp3 vps | vs1 vs2 vs3 vss
=================================================================
"""

from aiogram import types
from gate_handler import handle_real_gate_command

# =================================================================
# استيراد جميع دوال process_ من gates/
# =================================================================

# ── AUTH: Braintree ──────────────────────────────────────────────
from gates.Auth.B3_Auth.B3_1 import process_B3_1
from gates.Auth.B3_Auth.B3_2 import process_B3_2
from gates.Auth.B3_Auth.B3_3 import process_B3_3
from gates.Auth.B3_Auth.Single_B3 import process_B3_single

# ── AUTH: Stripe ─────────────────────────────────────────────────
from gates.Auth.ST_AUTH.ST_1 import process_ST_1
from gates.Auth.ST_AUTH.ST_2 import process_ST_2
from gates.Auth.ST_AUTH.ST_single import process_ST_single

# ── AUTH: Square ─────────────────────────────────────────────────
from gates.Auth.SQ_Auth.SQ_1 import process_SQ_1
from gates.Auth.SQ_Auth.SQ_2 import process_SQ_2
from gates.Auth.SQ_Auth.SQ_3 import process_SQ_3
from gates.Auth.SQ_Auth.SQ_single import process_SQ_single

# ── CHARGE: Authorize.Net ────────────────────────────────────────
from gates.Charge.Authorize_Net.Au_1 import process_Au_1
from gates.Charge.Authorize_Net.Au_single import process_Au_single

# ── CHARGE: PayPal ───────────────────────────────────────────────
from gates.Charge.PayPal.paypal_1 import process_paypal_1
from gates.Charge.PayPal.paypal_2 import process_paypal_2
from gates.Charge.PayPal.paypal_3 import process_paypal_3
from gates.Charge.PayPal.paypal_single import process_paypal_single

# ── CHARGE: Square ───────────────────────────────────────────────
from gates.Charge.SQ_Charge.SQ_1_charge import process_SQ_1_charge
from gates.Charge.SQ_Charge.SQ_2_charge import process_SQ_2_charge
from gates.Charge.SQ_Charge.SQ_single_charge import process_SQ_single_charge

# ── CHARGE: Stripe ───────────────────────────────────────────────
from gates.Charge.ST_Charge.St_1 import process_ST_1_charge
from gates.Charge.ST_Charge.ST_2_charge import process_ST_2_charge
from gates.Charge.ST_Charge.ST_3 import process_ST_3_charge
from gates.Charge.ST_Charge.ST_single_charge import process_ST_single_charge

# ── LOOKUP: Global 3DS ───────────────────────────────────────────
from gates.LookUp.Global_3DS.GP_1_3ds import process_GP_1_3ds
from gates.LookUp.Global_3DS.GP_2_3ds import process_GP_2_3ds
from gates.LookUp.Global_3DS.GP_single_3ds import process_GP_single_3ds

# ── LOOKUP: Global Passed ────────────────────────────────────────
from gates.LookUp.Global_Passed.GP_1_passed import process_GP_1_passed
from gates.LookUp.Global_Passed.GP_2_passed import process_GP_2_passed
from gates.LookUp.Global_Passed.GP_single_passed import process_GP_single_passed

# ── LOOKUP: Verify Passed ────────────────────────────────────────
from gates.LookUp.Verify_Passed.B3_LookUp1_passed import process_B3_LookUp1_passed
from gates.LookUp.Verify_Passed.B3_LookUp2_passed import process_B3_LookUp2_passed
from gates.LookUp.Verify_Passed.B3_LookUp3_passed import process_B3_LookUp3_passed
from gates.LookUp.Verify_Passed.B3_LookUp_single_passed import process_B3_LookUp_single_passed

# ── LOOKUP: Verify Secure ────────────────────────────────────────
from gates.LookUp.Verify_Secure.B3_LookUp1_secure import process_B3_LookUp1_secure
from gates.LookUp.Verify_Secure.B3_LookUp2_secure import process_B3_LookUp2_secure
from gates.LookUp.Verify_Secure.B3_LookUp3_secure import process_B3_LookUp3_secure
from gates.LookUp.Verify_Secure.B3_LookUp_single_secure import process_B3_LookUp_single_secure


# =================================================================
# AUTH — Braintree (4 handlers)
# =================================================================

async def handle_b31_command(message: types.Message) -> None:
    """/b31 — Braintree Auth B3-1"""
    await handle_real_gate_command(message, process_B3_1, "Braintree Auth B3-1")


async def handle_b32_command(message: types.Message) -> None:
    """/b32 — Braintree Auth B3-2"""
    await handle_real_gate_command(message, process_B3_2, "Braintree Auth B3-2")


async def handle_b33_command(message: types.Message) -> None:
    """/b33 — Braintree Auth B3-3"""
    await handle_real_gate_command(message, process_B3_3, "Braintree Auth B3-3")


async def handle_b3s_command(message: types.Message) -> None:
    """/b3s — Braintree Auth Single"""
    await handle_real_gate_command(message, process_B3_single, "Braintree Auth Single")


# =================================================================
# AUTH — Stripe (3 handlers)
# =================================================================

async def handle_st1_command(message: types.Message) -> None:
    """/st1 — Stripe Auth ST-1"""
    await handle_real_gate_command(message, process_ST_1, "Stripe Auth ST-1")


async def handle_st2_command(message: types.Message) -> None:
    """/st2 — Stripe Auth ST-2"""
    await handle_real_gate_command(message, process_ST_2, "Stripe Auth ST-2")


async def handle_sts_command(message: types.Message) -> None:
    """/sts — Stripe Auth Single"""
    await handle_real_gate_command(message, process_ST_single, "Stripe Auth Single")


# =================================================================
# AUTH — Square (4 handlers)
# =================================================================

async def handle_sq1_command(message: types.Message) -> None:
    """/sq1 — Square Auth SQ-1"""
    await handle_real_gate_command(message, process_SQ_1, "Square Auth SQ-1")


async def handle_sq2_command(message: types.Message) -> None:
    """/sq2 — Square Auth SQ-2"""
    await handle_real_gate_command(message, process_SQ_2, "Square Auth SQ-2")


async def handle_sq3_command(message: types.Message) -> None:
    """/sq3 — Square Auth SQ-3"""
    await handle_real_gate_command(message, process_SQ_3, "Square Auth SQ-3")


async def handle_sqs_command(message: types.Message) -> None:
    """/sqs — Square Auth Single"""
    await handle_real_gate_command(message, process_SQ_single, "Square Auth Single")


# =================================================================
# CHARGE — Authorize.Net (2 handlers)
# =================================================================

async def handle_au1_command(message: types.Message) -> None:
    """/au1 — Authorize.Net Charge AU-1"""
    await handle_real_gate_command(message, process_Au_1, "Authorize.Net [AIM]", "$0.50")


async def handle_aus_command(message: types.Message) -> None:
    """/aus — Authorize.Net Charge Single"""
    await handle_real_gate_command(message, process_Au_single, "Authorize.Net [AIM] Single", "$0.50")


# =================================================================
# CHARGE — PayPal (4 handlers)
# =================================================================

async def handle_pp1_command(message: types.Message) -> None:
    """/pp1 — PayPal Charge PP-1"""
    await handle_real_gate_command(message, process_paypal_1, "PayPal CVV PP-1", "$1.00")


async def handle_pp2_command(message: types.Message) -> None:
    """/pp2 — PayPal Charge PP-2"""
    await handle_real_gate_command(message, process_paypal_2, "PayPal CVV PP-2", "$1.00")


async def handle_pp3_command(message: types.Message) -> None:
    """/pp3 — PayPal Charge PP-3"""
    await handle_real_gate_command(message, process_paypal_3, "PayPal CVV PP-3", "$1.00")


async def handle_pps_command(message: types.Message) -> None:
    """/pps — PayPal Charge Single"""
    await handle_real_gate_command(message, process_paypal_single, "PayPal CVV Single", "$1.00")


# =================================================================
# CHARGE — Square (3 handlers)
# =================================================================

async def handle_sqc1_command(message: types.Message) -> None:
    """/sqc1 — Square Charge SQ-1"""
    await handle_real_gate_command(message, process_SQ_1_charge, "Square Charge SQ-1", "$1.00")


async def handle_sqc2_command(message: types.Message) -> None:
    """/sqc2 — Square Charge SQ-2"""
    await handle_real_gate_command(message, process_SQ_2_charge, "Square Charge SQ-2", "$1.00")


async def handle_sqcs_command(message: types.Message) -> None:
    """/sqcs — Square Charge Single"""
    await handle_real_gate_command(message, process_SQ_single_charge, "Square Charge Single", "$1.00")


# =================================================================
# CHARGE — Stripe (4 handlers)
# =================================================================

async def handle_stc1_command(message: types.Message) -> None:
    """/stc1 — Stripe Charge ST-1"""
    await handle_real_gate_command(message, process_ST_1_charge, "Stripe Charge ST-1", "$1.00")


async def handle_stc2_command(message: types.Message) -> None:
    """/stc2 — Stripe Charge ST-2"""
    await handle_real_gate_command(message, process_ST_2_charge, "Stripe Charge ST-2", "$1.00")


async def handle_stc3_command(message: types.Message) -> None:
    """/stc3 — Stripe Charge ST-3"""
    await handle_real_gate_command(message, process_ST_3_charge, "Stripe Charge ST-3", "$1.00")


async def handle_stcs_command(message: types.Message) -> None:
    """/stcs — Stripe Charge Single"""
    await handle_real_gate_command(message, process_ST_single_charge, "Stripe Charge Single", "$1.00")


# =================================================================
# LOOKUP — Global 3DS (3 handlers)
# =================================================================

async def handle_gp1_command(message: types.Message) -> None:
    """/gp1 — Global 3DS GP-1"""
    await handle_real_gate_command(message, process_GP_1_3ds, "Global 3DS GP-1")


async def handle_gp2_command(message: types.Message) -> None:
    """/gp2 — Global 3DS GP-2"""
    await handle_real_gate_command(message, process_GP_2_3ds, "Global 3DS GP-2")


async def handle_gps_command(message: types.Message) -> None:
    """/gps — Global 3DS Single"""
    await handle_real_gate_command(message, process_GP_single_3ds, "Global 3DS Single")


# =================================================================
# LOOKUP — Global Passed (3 handlers)
# =================================================================

async def handle_gpp1_command(message: types.Message) -> None:
    """/gpp1 — Global Passed GP-1"""
    await handle_real_gate_command(message, process_GP_1_passed, "Global Passed GP-1")


async def handle_gpp2_command(message: types.Message) -> None:
    """/gpp2 — Global Passed GP-2"""
    await handle_real_gate_command(message, process_GP_2_passed, "Global Passed GP-2")


async def handle_gpps_command(message: types.Message) -> None:
    """/gpps — Global Passed Single"""
    await handle_real_gate_command(message, process_GP_single_passed, "Global Passed Single")


# =================================================================
# LOOKUP — Verify Passed (4 handlers)
# =================================================================

async def handle_vp1_command(message: types.Message) -> None:
    """/vp1 — Verify Passed B3-1"""
    await handle_real_gate_command(message, process_B3_LookUp1_passed, "Verify Passed B3-1")


async def handle_vp2_command(message: types.Message) -> None:
    """/vp2 — Verify Passed B3-2"""
    await handle_real_gate_command(message, process_B3_LookUp2_passed, "Verify Passed B3-2")


async def handle_vp3_command(message: types.Message) -> None:
    """/vp3 — Verify Passed B3-3"""
    await handle_real_gate_command(message, process_B3_LookUp3_passed, "Verify Passed B3-3")


async def handle_vps_command(message: types.Message) -> None:
    """/vps — Verify Passed Single"""
    await handle_real_gate_command(message, process_B3_LookUp_single_passed, "Verify Passed Single")


# =================================================================
# LOOKUP — Verify Secure (4 handlers)
# =================================================================

async def handle_vs1_command(message: types.Message) -> None:
    """/vs1 — Verify Secure B3-1"""
    await handle_real_gate_command(message, process_B3_LookUp1_secure, "Verify Secure B3-1")


async def handle_vs2_command(message: types.Message) -> None:
    """/vs2 — Verify Secure B3-2"""
    await handle_real_gate_command(message, process_B3_LookUp2_secure, "Verify Secure B3-2")


async def handle_vs3_command(message: types.Message) -> None:
    """/vs3 — Verify Secure B3-3"""
    await handle_real_gate_command(message, process_B3_LookUp3_secure, "Verify Secure B3-3")


async def handle_vss_command(message: types.Message) -> None:
    """/vss — Verify Secure Single"""
    await handle_real_gate_command(message, process_B3_LookUp_single_secure, "Verify Secure Single")
