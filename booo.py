import subprocess
import sys

packages = [
    "aiogram",
    "aiohttp",
    "aiofiles",
    "telethon",
    "beautifulsoup4",
    "faker",
    "pyjwt",
    "cryptography",
]

def pip_install(pkg: str) -> bool:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    failed = []
    skipped = []

    for pkg in packages:
        print(f"\nInstalling {pkg} ...")
        ok = pip_install(pkg)

        if not ok:
            if pkg == "cryptography":
                print("⚠️ cryptography فشل على Pydroid/Python 3.13 (يحتاج Rust/Wheel غير متوفر). سيتم تخطيه.")
                skipped.append(pkg)
            else:
                print(f"❌ فشل تثبيت {pkg}")
                failed.append(pkg)

    if not failed:
        if skipped:
            print(f"\n✅ تم تثبيت جميع المكتبات ما عدا: {', '.join(skipped)}")
        else:
            print("\n✅ تم تثبيت جميع المكتبات بنجاح")
    else:
        print(f"\n❌ تم التثبيت مع أخطاء. فشل: {', '.join(failed)}")
        if skipped:
            print(f"⚠️ وتم تخطي: {', '.join(skipped)}")