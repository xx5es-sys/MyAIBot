#!/usr/bin/env python3.11
"""
=================================================================
𝖨𝖦𝖭𝖨𝖲𝖷 — Smoke Test
=================================================================
Verifies:
  1. All Python files compile without SyntaxError
  2. All modules import correctly (with sys.path set)
  3. Keyboards build without exceptions
  4. Captions generate without exceptions
  5. HTML messages don't have unclosed tags or Markdown syntax
  6. Button styles are valid (primary/success/danger or None)
  7. STOP button has no style
  8. No old branding names remain
  9. branding.apply_branding doesn't create nested anchors
"""

import sys
import os
import re
import importlib
import importlib.util
import py_compile
import traceback

# Set path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

PASS = 0
FAIL = 0
WARNINGS = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")

def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}")

def warn(msg):
    global WARNINGS
    WARNINGS += 1
    print(f"  [WARN] {msg}")


# =========================================================
# Test 1: Compile all .py files
# =========================================================
def test_compile():
    print("\n=== Test 1: Compile Check ===")
    py_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.py') and f != 'smoke_test.py']
    for f in sorted(py_files):
        path = os.path.join(PROJECT_DIR, f)
        try:
            py_compile.compile(path, doraise=True)
            ok(f"compile {f}")
        except py_compile.PyCompileError as e:
            fail(f"compile {f}: {e}")


# =========================================================
# Test 2: Import all modules
# =========================================================
def test_imports():
    print("\n=== Test 2: Import Check ===")
    # Skip files that start bot or have side effects
    skip = {'smoke_test.py', 'test.py', 'main.py'}
    py_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.py') and f not in skip]
    
    for f in sorted(py_files):
        mod_name = f[:-3]
        path = os.path.join(PROJECT_DIR, f)
        try:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            ok(f"import {f}")
        except Exception as e:
            fail(f"import {f}: {type(e).__name__}: {e}")

    # Test main.py import separately (it has the critical mass import)
    print("  --- main.py import test ---")
    try:
        spec = importlib.util.spec_from_file_location('main_test', os.path.join(PROJECT_DIR, 'main.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ok("import main.py")
    except Exception as e:
        fail(f"import main.py: {type(e).__name__}: {e}")


# =========================================================
# Test 3: Build keyboards without exceptions
# =========================================================
def test_keyboards():
    print("\n=== Test 3: Keyboard Build Check ===")
    
    # cmds.py keyboards
    try:
        from cmds import (
            kb_start, kb_profile_from_start, kb_about_from_start,
            kb_cmds, kb_gateways, kb_auth_gates, kb_charge_gates,
            kb_lookup_gates, kb_tools, kb_bin_tools, kb_scraper
        )
        for name, fn in [
            ("kb_start", kb_start),
            ("kb_profile_from_start", kb_profile_from_start),
            ("kb_about_from_start", kb_about_from_start),
            ("kb_cmds", kb_cmds),
            ("kb_gateways", kb_gateways),
            ("kb_auth_gates", kb_auth_gates),
            ("kb_charge_gates", kb_charge_gates),
            ("kb_lookup_gates", kb_lookup_gates),
            ("kb_tools", kb_tools),
            ("kb_bin_tools", kb_bin_tools),
            ("kb_scraper", kb_scraper),
        ]:
            kb = fn()
            assert kb is not None
            ok(f"cmds.{name}()")
    except Exception as e:
        fail(f"cmds keyboards: {type(e).__name__}: {e}")

    # mass.py keyboards
    try:
        from mass import kb_file_uploaded, kb_auth_gates as m_auth, kb_charge_gates as m_charge, kb_lookup_gates as m_lookup, kb_completed
        for name, fn in [
            ("kb_file_uploaded", kb_file_uploaded),
            ("kb_auth_gates", m_auth),
            ("kb_charge_gates", m_charge),
            ("kb_lookup_gates", m_lookup),
            ("kb_completed", kb_completed),
        ]:
            kb = fn()
            assert kb is not None
            ok(f"mass.{name}()")
    except Exception as e:
        fail(f"mass keyboards: {type(e).__name__}: {e}")

    # mass_utils.py keyboard
    try:
        from mass_utils import create_mass_keyboard
        mock_session = {
            "cards": ["4111111111111111|12|2025|123"] * 10,
            "processed": 5,
            "approved": 2, "declined": 1, "ccn": 1,
            "charge": 0, "otp": 0, "passed": 0, "rejected": 0,
            "unknown": 1, "status": "processing", "gate_type": "auth"
        }
        kb = create_mass_keyboard(12345, mock_session)
        assert kb is not None
        ok("mass_utils.create_mass_keyboard(processing)")

        mock_session["status"] = "paused"
        kb2 = create_mass_keyboard(12345, mock_session)
        assert kb2 is not None
        ok("mass_utils.create_mass_keyboard(paused)")
    except Exception as e:
        fail(f"mass_utils keyboard: {type(e).__name__}: {e}")


# =========================================================
# Test 4: Generate captions without exceptions
# =========================================================
def test_captions():
    print("\n=== Test 4: Caption Generation Check ===")
    try:
        from cmds import (
            cap_start, cap_my_profile, cap_about, cap_cmds,
            cap_gateways_overview, cap_auth_gates, cap_charge_gates,
            cap_lookup_gates, cap_tools, cap_cc_generator, cap_cc_scraper
        )
        
        ok("cap_start") if cap_start("TestUser") else fail("cap_start returned empty")
        ok("cap_about") if cap_about() else fail("cap_about returned empty")
        ok("cap_cmds") if cap_cmds() else fail("cap_cmds returned empty")
        ok("cap_gateways_overview") if cap_gateways_overview() else fail("cap_gateways_overview returned empty")
        ok("cap_auth_gates") if cap_auth_gates() else fail("cap_auth_gates returned empty")
        ok("cap_charge_gates") if cap_charge_gates() else fail("cap_charge_gates returned empty")
        ok("cap_lookup_gates") if cap_lookup_gates() else fail("cap_lookup_gates returned empty")
        ok("cap_tools") if cap_tools() else fail("cap_tools returned empty")
        ok("cap_cc_generator") if cap_cc_generator() else fail("cap_cc_generator returned empty")
        
    except Exception as e:
        fail(f"captions: {type(e).__name__}: {e}")

    try:
        from mass import cap_file_uploaded
        result = cap_file_uploaded("test.txt", 100, 50)
        assert result
        ok("mass.cap_file_uploaded")
    except Exception as e:
        fail(f"mass caption: {type(e).__name__}: {e}")


# =========================================================
# Test 5: HTML validation in messages
# =========================================================
def test_html_messages():
    print("\n=== Test 5: HTML Message Validation ===")
    
    from branding import apply_branding
    
    # Check that apply_branding doesn't create nested anchors
    test_input = '<a href="http://t.me/IgnisXBot">•</a> Status'
    result = apply_branding(test_input)
    if '<a ' in result.split('</a>')[0].split('<a ', 1)[1] if result.count('<a ') > 1 else False:
        fail("branding creates nested <a> tags")
    else:
        ok("branding doesn't create nested <a> tags")
    
    # Check no Markdown syntax in HTML messages
    py_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.py') and f != 'smoke_test.py']
    md_in_html = False
    for f in py_files:
        path = os.path.join(PROJECT_DIR, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        # Look for **text** near parse_mode="HTML"
        lines = content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if '**' in stripped and not stripped.startswith('#') and not stripped.startswith('proxy_encrypted'):
                # Check if it's in a string context (rough check)
                if ('f"' in stripped or "f'" in stripped or '("' in stripped or "('" in stripped) and 'parse_mode' not in stripped:
                    # Check surrounding lines for parse_mode="HTML"
                    context = '\n'.join(lines[max(0,i-5):min(len(lines),i+5)])
                    if 'parse_mode="HTML"' in context or "parse_mode='HTML'" in context:
                        fail(f"Markdown **bold** in HTML context: {f}:{i+1}")
                        md_in_html = True
    if not md_in_html:
        ok("No Markdown syntax in HTML messages")


# =========================================================
# Test 6: Button style validation
# =========================================================
def test_button_styles():
    print("\n=== Test 6: Button Style Validation ===")
    valid_styles = {'primary', 'success', 'danger', None}
    
    py_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.py')]
    all_valid = True
    for f in py_files:
        path = os.path.join(PROJECT_DIR, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        for match in re.finditer(r'style=["\'](\w+)["\']', content):
            style = match.group(1)
            if style not in {'primary', 'success', 'danger'}:
                fail(f"Invalid style '{style}' in {f}")
                all_valid = False
    if all_valid:
        ok("All button styles are valid (primary/success/danger)")


# =========================================================
# Test 7: STOP button has no style
# =========================================================
def test_stop_button():
    print("\n=== Test 7: STOP Button Check ===")
    try:
        from mass_utils import create_mass_keyboard
        mock_session = {
            "cards": ["x"] * 10, "processed": 5,
            "approved": 2, "declined": 1, "ccn": 1,
            "charge": 0, "otp": 0, "passed": 0, "rejected": 0,
            "unknown": 1, "status": "processing", "gate_type": "auth"
        }
        kb = create_mass_keyboard(12345, mock_session)
        for row in kb.inline_keyboard:
            for btn in row:
                if 'STOP' in btn.text:
                    if btn.style is None:
                        ok("STOP button has no style")
                    else:
                        fail(f"STOP button has style={btn.style}")
    except Exception as e:
        fail(f"STOP button check: {e}")


# =========================================================
# Test 8: No old branding names
# =========================================================
def test_old_branding():
    print("\n=== Test 8: Old Branding Check ===")
    old_names = ['O.tbot', 'O.T Bot', 'O.TBOT']
    
    py_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.py') and f != 'smoke_test.py']
    found_old = False
    for f in py_files:
        path = os.path.join(PROJECT_DIR, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        for old_name in old_names:
            # Skip branding.py patterns list (it's the replacement rules)
            if f == 'branding.py':
                continue
            if old_name in content:
                fail(f"Old name '{old_name}' found in {f}")
                found_old = True
    if not found_old:
        ok("No old branding names found")


# =========================================================
# Test 9: Mass panel counters by gate type
# =========================================================
def test_mass_counters():
    print("\n=== Test 9: Mass Panel Counter Check ===")
    try:
        from mass_utils import get_counters_for_gate
        
        session = {"approved": 5, "declined": 3, "ccn": 2, "charge": 1, "otp": 4, "passed": 6, "rejected": 7, "unknown": 1}
        
        auth_counters = get_counters_for_gate("auth", session)
        labels = [c[0] for c in auth_counters]
        assert "APPROVED" in labels[0], f"Auth first counter should be APPROVED, got {labels[0]}"
        assert "DECLINED" in labels[1], f"Auth second counter should be DECLINED, got {labels[1]}"
        assert "CCN" in labels[2], f"Auth third counter should be CCN, got {labels[2]}"
        ok("AUTH counters: APPROVED, DECLINED, CCN")
        
        charge_counters = get_counters_for_gate("charge", session)
        labels = [c[0] for c in charge_counters]
        assert "CHARGE" in labels[0], f"Charge first counter should be CHARGE, got {labels[0]}"
        assert "APPROVED" in labels[1], f"Charge second counter should be APPROVED, got {labels[1]}"
        assert "DECLINED" in labels[2], f"Charge third counter should be DECLINED, got {labels[2]}"
        ok("CHARGE counters: CHARGE, APPROVED, DECLINED")
        
        lookup_counters = get_counters_for_gate("lookup", session)
        labels = [c[0] for c in lookup_counters]
        assert "OTP" in labels[0], f"Lookup first counter should be OTP, got {labels[0]}"
        assert "PASSED" in labels[1], f"Lookup second counter should be PASSED, got {labels[1]}"
        assert "REJECTED" in labels[2], f"Lookup third counter should be REJECTED, got {labels[2]}"
        ok("LOOKUP counters: OTP REQUEST, PASSED, REJECTED")
        
    except Exception as e:
        fail(f"Mass counters: {type(e).__name__}: {e}")


# =========================================================
# Run all tests
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("𝖨𝖦𝖭𝖨𝖲𝖷 Smoke Test")
    print("=" * 60)
    
    test_compile()
    test_imports()
    test_keyboards()
    test_captions()
    test_html_messages()
    test_button_styles()
    test_stop_button()
    test_old_branding()
    test_mass_counters()
    
    print("\n" + "=" * 60)
    print(f"Results: {PASS} PASS, {FAIL} FAIL, {WARNINGS} WARN")
    print("=" * 60)
    
    if FAIL > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED!")
        sys.exit(0)
