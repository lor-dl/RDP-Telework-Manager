import os
import sys
import ctypes
import subprocess
import urllib.request
import winreg
import shutil
import random
import string
import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QClipboard
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QTabWidget, 
    QMessageBox, QFileDialog, QFrame, QTextEdit, QCheckBox
)

def get_bundle_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, get_bundle_dir())

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1
        )
        sys.exit(0)

def get_desktop_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        desktop, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        return desktop
    except Exception:
        return os.path.join(os.path.expanduser("~"), "Desktop")

# کد داخلی پورتال دورکار با قابلیت ذخیره امن رمزنگاری‌شده و دکمه اتصال به نرم‌افزار هلو
WORKER_LAUNCHER_CODE = '''
import sys
import os
import json
import base64
import subprocess
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox, QHBoxLayout
)

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_cache_path():
    appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    cache_dir = os.path.join(appdata, "NegaranPortalCache")
    if not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir)
        except Exception:
            pass
    return os.path.join(cache_dir, "session_cache.json")

def encrypt_text(text):
    if not text:
        return ""
    key = 0x5A
    encrypted = "".join(chr(ord(c) ^ key) for c in text)
    return base64.b64encode(encrypted.encode("utf-8")).decode("utf-8")

def decrypt_text(encoded_text):
    try:
        decoded = base64.b64decode(encoded_text.encode("utf-8")).decode("utf-8")
        key = 0x5A
        return "".join(chr(ord(c) ^ key) for c in decoded)
    except Exception:
        return ""

class PortalLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ورود به سامانه دورکاری نگاران")
        self.resize(380, 280)
        self.setFixedSize(380, 280)

        self.config = {}
        config_path = get_resource_path("config_temp.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception:
            pass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title_lbl = QLabel("لطفاً اطلاعات حساب کاربری خود را وارد کنید:")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 10.5pt; color: #F8FAFC;")
        layout.addWidget(title_lbl)

        layout.addWidget(QLabel("نام کاربری (Username):"))
        self.ent_user = QLineEdit()
        self.ent_user.setStyleSheet("background-color: #1E293B; border: 1px solid #475569; border-radius: 6px; padding: 6px; color: white;")
        layout.addWidget(self.ent_user)

        layout.addWidget(QLabel("رمز عبور (Password):"))
        pass_layout = QHBoxLayout()
        self.ent_pass = QLineEdit()
        self.ent_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.ent_pass.setStyleSheet("background-color: #1E293B; border: 1px solid #475569; border-radius: 6px; padding: 6px; color: white;")
        
        self.btn_show_pass = QPushButton("👁️")
        self.btn_show_pass.setFixedWidth(40)
        self.btn_show_pass.setCheckable(True)
        self.btn_show_pass.setStyleSheet("background-color: #475569; color: white; border-radius: 6px; font-weight: bold;")
        self.btn_show_pass.clicked.connect(self.toggle_password_visibility)
        
        pass_layout.addWidget(self.ent_pass)
        pass_layout.addWidget(self.btn_show_pass)
        layout.addLayout(pass_layout)

        self.chk_remember = QCheckBox("ذخیره نام کاربری و رمز عبور")
        self.chk_remember.setStyleSheet("color: #E2E8F0; font-size: 9pt;")
        layout.addWidget(self.chk_remember)

        self.btn_connect = QPushButton("🚀 اتصال به نرم افزار هلو")
        self.btn_connect.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; border-radius: 6px; padding: 8px;")
        self.btn_connect.clicked.connect(self.launch_rdp)
        layout.addWidget(self.btn_connect)

        self.setStyleSheet("background-color: #0F172A; color: #F8FAFC; font-family: Tahoma, sans-serif; font-size: 9pt;")
        
        self.load_cached_credentials()

    def toggle_password_visibility(self, checked):
        if checked:
            self.ent_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_pass.setText("🙈")
        else:
            self.ent_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_pass.setText("👁️")

    def load_cached_credentials(self):
        cache_path = get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    username = data.get("username", "")
                    enc_pass = data.get("password", "")
                    if username:
                        self.ent_user.setText(username)
                    if enc_pass:
                        dec_pass = decrypt_text(enc_pass)
                        self.ent_pass.setText(dec_pass)
                    if username or enc_pass:
                        self.chk_remember.setChecked(True)
            except Exception:
                pass

    def save_cached_credentials(self, username, password):
        cache_path = get_cache_path()
        if self.chk_remember.isChecked():
            data = {
                "username": username,
                "password": encrypt_text(password)
            }
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception:
                pass
        else:
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception:
                    pass

    def launch_rdp(self):
        username = self.ent_user.text().strip()
        password = self.ent_pass.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "خطا", "لطفاً نام کاربری و رمز عبور را وارد کنید.")
            return

        self.save_cached_credentials(username, password)

        rdp_content = self.config.get("rdp_content", "")
        if not rdp_content:
            QMessageBox.warning(self, "خطا", "فایل RDP مرجع یافت نشد.")
            return

        lines = rdp_content.splitlines()
        new_lines = []
        user_found = False
        for line in lines:
            if line.lower().startswith("username:s:"):
                new_lines.append(f"username:s:{username}")
                user_found = True
            else:
                new_lines.append(line)
        if not user_found:
            new_lines.append(f"username:s:{username}")

        updated_rdp = "\\n".join(new_lines)

        temp_rdp = os.path.join(os.environ["TEMP"], "negaran_portal_session.rdp")
        try:
            with open(temp_rdp, "w", encoding="utf-8") as f:
                f.write(updated_rdp)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در ایجاد نشست موقت: {e}")
            return

        server_addr = ""
        for line in new_lines:
            if line.lower().startswith("full address:s:"):
                server_addr = line.split(":", 2)[2].strip()
                break

        if server_addr:
            subprocess.run(f'cmdkey /generic:TERMSRV/{server_addr} /delete', shell=True, capture_output=True)
            subprocess.run(f'cmdkey /generic:TERMSRV/{server_addr} /user:{username} /pass:{password}', shell=True, capture_output=True)

        subprocess.Popen(f'mstsc "{temp_rdp}"', shell=True)
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PortalLoginWindow()
    window.show()
    sys.exit(app.exec())
'''

LANGUAGES = {
    "fa": {
        "title": "نگاران | مدیریت پیشرفته دورکاری و RDP",
        "header_title": "سامانه جامع مدیریت دورکاری و RDP نگاران",
        "header_subtitle": "مدیریت کاربران، تغییر پورت، پیکربندی RDP Wrapper و پورتال دورکار",
        "tab_user": "👤 مدیریت کاربر",
        "tab_network": "🌐 شبکه و فایروال",
        "tab_rdp": "📄 ساخت RDP",
        "tab_wrapper": "🛡️ RDP Wrapper",
        "tab_portal": "📦 پورتال دورکار",
        
        "username_lbl": "نام کاربر جدید:",
        "password_lbl": "رمز عبور کاربر:",
        "btn_create_user": "✨ ساخت کاربر و اعمال تنظیمات ریجن و کیبورد",
        "btn_gen_pass": "🔑 ساخت رمز تصادفی",
        "chk_admin": "عضویت در گروه Administrators (دسترسی کامل ادمین)",
        "chk_rdp": "عضویت در گروه Remote Desktop Users (اجازه اتصال ریموت)",
        "console_title": "گزارش وضعیت و لاگ‌های اجرایی:",
        "btn_open_log": "📂 باز کردن فایل لیست کاربران روی دسکتاپ",
        "help_title": "راهنمای تنظیمات خودکار کاربر",
        "help_msg": "مواردی که با ساخت کاربر به‌صورت خودکار روی پروفایل جدید اعمال می‌شوند:\n\n"
                    "1. تنظیم کیبورد فارسی (fa-IR) و انگلیسی (en-US)\n"
                    "2. تنظیم فرمت تاریخ yyyy/MM/dd و ریجن ایران\n"
                    "3. اعطای دسترسی ادمین و ریموت دسکتاپ بسته به انتخاب شما\n"
                    "4. غیرفعال‌سازی Easy Print جهت حل مشکل پرینتر دورکار\n"
                    "5. تنظیم سیاست خروج سریع و بستن نشست‌های قطع‌شده",
        "btn_help": "❓ راهنما",

        "port_lbl": "شماره پورت جدید RDP:",
        "btn_change_port": "🔄 تغییر پورت و بروزرسانی فایروال ویندوز",
        "btn_check_port": "🔍 بررسی وضعیت پورت (Listening)",
        "public_ip_lbl": "آی‌پی عمومی سرور: در حال انتظار...",
        "btn_fetch_ip": "🌍 استخراج IP استاتیک / عمومی",
        "btn_copy_ip": "📋 کپی آی‌پی",
        "net_console_title": "کنسول وضعیت شبکه و فایروال:",

        "rdp_ip_lbl": "آدرس آی‌پی (استاتیک / عمومی):",
        "rdp_port_lbl": "شماره پورت RDP:",
        "rdp_user_lbl": "نام کاربری (اختیاری):",
        "rdp_holoo_lbl": "مسیر اجرای برنامه هلو (Holoo.exe):",
        "btn_browse_holoo": "📂 انتخاب فایل...",
        "btn_grab_ip": "📥 دریافت IP",
        "chk_smart_sizing": "تناسب هوشمند صفحه (Smart Sizing)",
        "chk_redirect": "انتقال درایو، کلیپ‌بورد و پرینتر محلی",
        "btn_gen_rdp": "💾 تولید فایل RDP",
        "btn_test_mstsc": "🚀 اجرای مستقیم (MSTSC)",
        "rdp_console_title": "کنسول ساخت فایل اتصال:",
        
        "portal_desc": "انتخاب فایل RDP مرجع (بدون تغییر ساختار فایل) جهت ساخت پورتال انحصاری دورکار:",
        "btn_browse_rdp": "📂 انتخاب فایل RDP دلخواه",
        "btn_build_portal": "🛠️ ساخت پورتال انحصاری دورکار (EXE)",
        "portal_console_title": "کنسول ساخت و کامپایل پورتال:",

        "card1_title": "نصب سرویس",
        "card1_desc": "فعال‌سازی قابلیت چندکاربری RDP",
        "card1_btn": "⚡ نصب و فعال‌سازی",
        
        "card2_title": "پیکربندی (RDPConf)",
        "card2_desc": "بررسی وضعیت و تنظیمات اصلی پکیج",
        "card2_btn": "⚙️ اجرای تنظیمات",
        
        "card3_title": "تست اتصال (RDPCheck)",
        "card3_desc": "بررسی امکان اتصال هم‌زمان محلی",
        "card3_btn": "🧪 تست اتصال",
        
        "card4_title": "جایگزینی دستی INI",
        "card4_desc": "انتخاب و جایگزینی فایل تنظیمات",
        "card4_btn": "📁 انتخاب فایل",
        
        "card5_title": "بروزرسانی آنلاین",
        "card5_desc": "دریافت آخرین نسخه rdpwrap.ini از وب",
        "card5_btn": "📥 بروزرسانی خودکار",
        
        "card6_title": "حذف سرویس",
        "card6_desc": "پاکسازی کامل و غیرفعال‌سازی پکیج",
        "card6_btn": "❌ حذف سرویس",
        
        "btn_check_wrapper": "🔍 بررسی جامع وضعیت و سلامت RDP Wrapper",
        "wrapper_console_title": "کنسول تشخیص و عیب‌یابی RDP Wrapper:",
        
        "footer": "شرکت نگاران • نسخه ۳.۳"
    },
    "en": {
        "title": "Negaran | Advanced Remote Desktop Manager",
        "header_title": "Negaran Telework & RDP Manager",
        "header_subtitle": "User Management, Port Customization, RDP Wrapper & Client Portal",
        "tab_user": "👤 User Setup",
        "tab_network": "🌐 Network & Firewall",
        "tab_rdp": "📄 RDP Gen",
        "tab_wrapper": "🛡️ RDP Wrapper",
        "tab_portal": "📦 Client Portal",
        
        "username_lbl": "New Username:",
        "password_lbl": "Password:",
        "btn_create_user": "✨ Create User & Apply Auto Policies",
        "btn_gen_pass": "🔑 Generate Pass",
        "chk_admin": "Add to Administrators Group",
        "chk_rdp": "Add to Remote Desktop Users",
        "console_title": "Execution Console Log:",
        "btn_open_log": "📂 Open Users Desktop Log",
        "help_title": "Automated Setup Help",
        "help_msg": "Actions applied automatically upon user creation:\n\n"
                    "1. Configures Persian & English Keyboards for New Users.\n"
                    "2. Sets yyyy/MM/dd Date format and Iran Region.\n"
                    "3. Grants Administrator & Remote Desktop privileges.\n"
                    "4. Disables Easy Print to fix remote printer issues.\n"
                    "5. Enforces immediate disconnect reset policy.",
        "btn_help": "❓ Help",

        "port_lbl": "New RDP Port Number:",
        "btn_change_port": "🔄 Change Port & Update Windows Firewall",
        "btn_check_port": "🔍 Check Port Status (Listening)",
        "public_ip_lbl": "Server Public IP: Pending...",
        "btn_fetch_ip": "🌍 Fetch Public / Static IP",
        "btn_copy_ip": "📋 Copy IP",
        "net_console_title": "Network & Firewall Console Log:",

        "rdp_ip_lbl": "IP Address (Static / Public):",
        "rdp_port_lbl": "RDP Port Number:",
        "rdp_user_lbl": "Username (Optional):",
        "rdp_holoo_lbl": "Holoo Executable Path (Holoo.exe):",
        "btn_browse_holoo": "📂 Browse...",
        "btn_grab_ip": "📥 Grab IP",
        "chk_smart_sizing": "Smart Sizing",
        "chk_redirect": "Redirect Drives, Clipboard & Printers",
        "btn_gen_rdp": "💾 Generate RDP",
        "btn_test_mstsc": "🚀 Launch MSTSC",
        "rdp_console_title": "RDP Generation Console Log:",
        
        "portal_desc": "Select reference RDP file (without modifying structure) to build client portal:",
        "btn_browse_rdp": "📂 Select Reference RDP File",
        "btn_build_portal": "🛠️ Build Client Portal (EXE)",
        "portal_console_title": "Portal Build Console Log:",

        "card1_title": "Install Service",
        "card1_desc": "Enable multi-user RDP capability",
        "card1_btn": "⚡ Install Service",
        
        "card2_title": "Configuration",
        "card2_desc": "Check status and core settings",
        "card2_btn": "⚙️ Open RDPConf",
        
        "card3_title": "Connection Test",
        "card3_desc": "Test concurrent local sessions",
        "card3_btn": "🧪 Test Connection",
        
        "card4_title": "Manual INI Replace",
        "card4_desc": "Browse and replace INI file",
        "card4_btn": "📁 Browse File",
        
        "card5_title": "Online Update",
        "card5_desc": "Download latest rdpwrap.ini online",
        "card5_btn": "📥 Auto Update",
        
        "card6_title": "Uninstall Service",
        "card6_desc": "Completely remove RDP wrapper",
        "card6_btn": "❌ Uninstall",
        
        "btn_check_wrapper": "🔍 Check RDP Wrapper Status & Health",
        "wrapper_console_title": "RDP Wrapper Diagnostics Console:",
        
        "footer": "Negaran Company • v3.3"
    }
}

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip() if result.returncode == 0 else result.stderr.strip()

def run_powershell(cmd):
    ps_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{cmd}"'
    result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip() if result.returncode == 0 else result.stderr.strip()

def log_user_to_desktop(username, password, lang="fa"):
    desktop_dir = get_desktop_path()
    file_path = os.path.join(desktop_dir, "کاربرا.txt")
    
    user_count = 1
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                user_count = content.count("-------------------------") + 1
        except Exception:
            pass

    entry = f"کاربر {user_count}:\nنام کاربری: {username}\nرمز عبور: {password}\n-------------------------\n" if lang == "fa" \
            else f"User {user_count}:\nUsername: {username}\nPassword: {password}\n-------------------------\n"

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return file_path
    except Exception:
        return None

def create_and_setup_user_advanced(parent, username, password, make_admin, make_rdp, console_widget, lang_code):
    if not username or not password:
        QMessageBox.warning(parent, "خطا / Error", "لطفاً نام کاربری و رمز عبور را وارد کنید.")
        return

    console_widget.clear()
    def append_log(text, color="#38BDF8"):
        console_widget.append(f'<span style="color: {color};">[استاندارد نگاران] {text}</span>')
        QApplication.processEvents()

    append_log(f"شروع فرآیند ایجاد و پیکربندی کاربر '{username}'...", "#FACC15")

    ps_script = """
    Set-WinSystemLocale -SystemLocale fa-IR
    Set-WinHomeLocation -GeoId 117
    Set-Culture -CultureInfo fa-IR
    $LangList = New-WinUserLanguageList -Language fa-IR
    $LangList.Add("en-US")
    Set-WinUserLanguageList -LanguageList $LangList -Force
    Copy-UserInternationalSettingsToSystem -WelcomeScreen $true -NewUser $true

    $RegTSPath = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services"
    if (!(Test-Path $RegTSPath)) {
        New-Item -Path $RegTSPath -Force | Out-Null
    }
    Set-ItemProperty -Path $RegTSPath -Name "fEnableEasyPrint" -Value 0 -PropertyType DWord -Force
    Set-ItemProperty -Path $RegTSPath -Name "fDisableCpn" -Value 0 -PropertyType DWord -Force
    Set-ItemProperty -Path $RegTSPath -Name "MaxDisconnectionTime" -Value 60000 -PropertyType DWord -Force
    Set-ItemProperty -Path $RegTSPath -Name "MaxIdleTime" -Value 60000 -PropertyType DWord -Force
    Set-ItemProperty -Path $RegTSPath -Name "ResetBroken" -Value 1 -PropertyType DWord -Force
    """
    run_powershell(ps_script)
    append_log("تنظیمات سراسری سیستم و پالیسی‌های ترمینال سرور اعمال شد.", "#10B981")

    ok, err = run_cmd(f'net user "{username}" "{password}" /add')
    if not ok and "already exists" not in err and "پیش‌تر وجود دارد" not in err:
        append_log(f"خطا در ایجاد کاربر: {err}", "#EF4444")
        QMessageBox.warning(parent, "خطا / Error", f"خطا در ساخت کاربر: {err}")
        return
    append_log("کاربر با موفقیت ایجاد شد یا از قبل وجود داشت.", "#10B981")

    if make_admin:
        append_log("افزودن کاربر به گروه Administrators...")
        run_cmd(f'net localgroup "Administrators" "{username}" /add')
    if make_rdp:
        append_log("افزودن کاربر به گروه Remote Desktop Users...")
        run_cmd(f'net localgroup "Remote Desktop Users" "{username}" /add')

    run_powershell(f'Set-LocalUser -Name "{username}" -PasswordNeverExpires $true')
    append_log("تنظیم انقضای رمز عبور روی حالت دائمی (Never Expires).", "#10B981")

    log_path = log_user_to_desktop(username, password, lang_code)
    if log_path:
        append_log(f"اطلاعات اکانت در فایل دسکتاپ ذخیره شد: {log_path}", "#34D399")

    append_log("تمامی مراحل با موفقیت به پایان رسید!", "#10B981")
    QMessageBox.information(parent, "نگاران | Negaran", f"کاربر '{username}' با موفقیت ساخته شد و تمام تنظیمات اعمال گردید.")

def change_rdp_port_advanced(parent, port_str, console_widget, lang_code):
    if not port_str.isdigit():
        QMessageBox.warning(parent, "خطا / Error", "شماره پورت باید عدد باشد.")
        return
    
    port = int(port_str)
    console_widget.clear()
    def append_log(text, color="#38BDF8"):
        console_widget.append(f'<span style="color: {color};">[شبکه نگاران] {text}</span>')
        QApplication.processEvents()

    append_log(f"شروع فرآیند تغییر پورت RDP به {port}...", "#FACC15")

    try:
        key_path = r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "PortNumber", 0, winreg.REG_DWORD, port)
        winreg.CloseKey(key)
        append_log("پورت در رجیستری ویندوز با موفقیت بروزرسانی شد.", "#10B981")
    except Exception as e:
        append_log(f"خطا در ویرایش رجیستری: {e}", "#EF4444")
        QMessageBox.warning(parent, "خطا / Error", f"خطا در ریجستری: {e}")
        return

    append_log("در حال پاکسازی قوانین قبلی فایروال ویندوز...")
    run_cmd('netsh advfirewall firewall delete rule name="Custom RDP Port TCP"')
    run_cmd('netsh advfirewall firewall delete rule name="Custom RDP Port UDP"')

    append_log(f"ایجاد قوانین جدید فایروال برای پورت {port} (TCP/UDP)...")
    run_cmd(f'netsh advfirewall firewall add rule name="Custom RDP Port TCP" dir=in action=allow protocol=TCP localport={port}')
    run_cmd(f'netsh advfirewall firewall add rule name="Custom RDP Port UDP" dir=in action=allow protocol=UDP localport={port}')
    append_log("قوانین فایروال با موفقیت اعمال شدند.", "#10B981")

    append_log("در حال ری‌استارت کردن سرویس Remote Desktop (TermService)...")
    run_cmd('net stop TermService /y')
    run_cmd('net start TermService')
    append_log("سرویس ترمینال سرور با موفقیت ری‌استارت شد.", "#10B981")

    append_log("تغییرات پورت و شبکه کامل شد!", "#34D399")
    msg = f"پورت RDP با موفقیت به {port} تغییر یافت و فایروال تنظیم شد." if lang_code == "fa" \
          else f"RDP Port changed to {port} and Firewall updated."
    QMessageBox.information(parent, "نگاران | Negaran", msg)

def check_port_listening(port_str, console_widget):
    if not port_str.isdigit():
        return
    port = port_str.strip()
    console_widget.clear()
    def append_log(text, color="#38BDF8"):
        console_widget.append(f'<span style="color: {color};">[بررسی پورت] {text}</span>')
        QApplication.processEvents()

    append_log(f"در حال بررسی وضعیت پورت {port} روی سیستم...", "#FACC15")
    ok, output = run_cmd(f'netstat -ano | findstr :{port}')
    if ok and output:
        append_log(f"پورت {port} فعال و در حال شنود (Listening) است:\n{output}", "#10B981")
    else:
        append_log(f"پورت {port} در حال حاضر فعال نیست یا سرویس ریموت روی آن گوش نمی‌دهد.", "#EF4444")

def fetch_public_ip(label_widget, target_entry=None, lang_code="fa"):
    try:
        url = "https://api.ipify.org"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            ip = response.read().decode('utf-8')
            text = f"آی‌پی عمومی سرور: {ip}" if lang_code == "fa" else f"Server Public IP: {ip}"
            label_widget.setText(text)
            label_widget.setStyleSheet("color: #10B981; font-weight: bold;")
            if target_entry:
                target_entry.setText(ip)
    except Exception:
        err_text = "خطا در دریافت IP (اینترنت را بررسی کنید)" if lang_code == "fa" else "IP fetch failed"
        label_widget.setText(err_text)
        label_widget.setStyleSheet("color: #EF4444; font-weight: bold;")

def create_client_portal_package(parent, rdp_file_path, console_widget, lang_code):
    if not rdp_file_path or not os.path.exists(rdp_file_path):
        msg = "لطفاً ابتدا یک فایل RDP معتبر انتخاب کنید." if lang_code == "fa" else "Please select a valid RDP file first."
        QMessageBox.warning(parent, "خطا / Error", msg)
        return

    console_widget.clear()
    def append_log(text, color="#38BDF8"):
        console_widget.append(f'<span style="color: {color};">[سازنده پورتال] {text}</span>')
        QApplication.processEvents()

    append_log("در حال خواندن فایل RDP مرجع بدون تغییر ساختار...", "#FACC15")

    try:
        with open(rdp_file_path, "r", encoding="utf-8", errors="ignore") as f:
            rdp_content = f.read()
    except Exception as e:
        append_log(f"خطا در خواندن فایل RDP: {e}", "#EF4444")
        return

    desktop_dir = get_desktop_path()
    output_folder = os.path.join(desktop_dir, "RemoteAccess_Portal")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    config_data = {
        "rdp_content": rdp_content
    }

    base_dir = get_bundle_dir()
    script_path = os.path.join(base_dir, "worker_launcher.py")
    font_path = os.path.join(base_dir, "IRANSans.ttf")
    config_temp_path = os.path.join(base_dir, "config_temp.json")

    if not os.path.exists(script_path):
        try:
            with open(script_path, "w", encoding="utf-8") as wf:
                wf.write(WORKER_LAUNCHER_CODE)
            append_log("اسکریپت داخلی پورتال با موفقیت آماده شد.", "#10B981")
        except Exception as e:
            append_log(f"خطا در ساخت اسکریپت پورتال: {e}", "#EF4444")
            return

    try:
        with open(config_temp_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        append_log("فایل تنظیمات داخلی ایجاد شد.", "#10B981")
    except Exception as e:
        append_log(f"خطا در ایجاد کانفیگ: {e}", "#EF4444")
        return

    add_font_arg = f'--add-data="{font_path};."' if os.path.exists(font_path) else ''
    cmd = [
        "python", "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        f'--add-data="{config_temp_path};."',
        add_font_arg,
        f'--name=RemoteAccess',
        f'--distpath="{output_folder}"',
        f'"{script_path}"'
    ]
    cmd_str = " ".join([c for c in cmd if c])

    append_log("در حال ساخت و کامپایل فایل اجرایی پورتال (چند لحظه صبر کنید)...", "#FACC15")

    try:
        process = subprocess.Popen(
            cmd_str, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            shell=True, 
            cwd=base_dir
        )
        stdout, stderr = process.communicate()
        
        if os.path.exists(config_temp_path):
            os.remove(config_temp_path)

        if process.returncode == 0:
            append_log("پورتال انحصاری دورکار با موفقیت ساخته شد!", "#34D399")
            msg = f"پورتال اجرایی کاربر در پوشه زیر آماده شد:\n\n{output_folder}\n\nهنگام اجرای این پورتال، کاربر نام کاربری و رمز خود را وارد کرده و دقیقاً همان فایل RDP شما اجرا می‌شود." if lang_code == "fa" \
                  else f"Portal created successfully in:\n\n{output_folder}"
            QMessageBox.information(parent, "موفقیت‌آمیز", msg)
        else:
            append_log(f"خطا در کامپایل:\n{stderr}", "#EF4444")
            QMessageBox.critical(parent, "خطا در ساخت", f"خطایی رخ داد:\n{stderr}")

    except Exception as e:
        append_log(f"خطای سیستمی: {e}", "#EF4444")
        if os.path.exists(config_temp_path):
            os.remove(config_temp_path)

def generate_rdp_file_advanced(parent, ip, port, username, holoo_path, smart_sizing, redirect_enabled, console_widget, lang_code):
    if not ip or not port:
        QMessageBox.warning(parent, "خطا / Error", "آدرس آی‌پی و پورت الزامی هستند.")
        return

    console_widget.clear()
    def append_log(text, color="#38BDF8"):
        console_widget.append(f'<span style="color: {color};">[سازنده RDP] {text}</span>')
        QApplication.processEvents()

    append_log("در حال ساخت فایل کانفیگ استاندارد اتصال...", "#FACC15")

    if holoo_path and os.path.exists(holoo_path):
        exe_name = os.path.basename(holoo_path)
        app_name = os.path.splitext(exe_name)[0]
        shell_cmd = holoo_path
        working_dir = os.path.dirname(holoo_path)
        append_log(f"برنامه اختصاصی شناسایی شد: {app_name}", "#10B981")
    else:
        app_name = "logonsession"
        shell_cmd = "rdpinit.exe"
        working_dir = "C:\\ProgramData"
        append_log("حالت ریموت دسکتاپ عمومی استاندارد اعمال شد.", "#10B981")

    smart_val = "1" if smart_sizing else "0"
    redirect_val = "1" if redirect_enabled else "0"

    rdp_content = f"""screen mode id:i:2
desktopwidth:i:1024
desktopheight:i:768
session bpp:i:16
full address:s:{ip}:{port}
server port:i:{port}
username:s:{username}
keyboardhook:i:0
audiocapturemode:i:1
videoplaybackmode:i:1
connection type:i:2
audiomode:i:0
displayconnectionbar:i:1
winposstr:s:0,3,0,0,800,600
allow desktop composition:i:0
allow font smoothing:i:1
disable cursor setting:i:0
redirectdrives:i:{redirect_val}
redirectprinters:i:{redirect_val}
redirectcomports:i:{redirect_val}
redirectsmartcards:i:{redirect_val}
redirectclipboard:i:{redirect_val}
redirectposdevices:i:{redirect_val}
bitmapcachepersistenable:i:1
compression:i:1
disable themes:i:0
disable menu anims:i:1
disable wallpaper:i:1
smart sizing:i:{smart_val}
autoreconnection enabled:i:1
auto connect:i:1
domain:s:''
prompt for credentials on client:i:0
disable full window drag:i:1
remoteapplicationmode:i:1
remoteapplicationprogram:s:{app_name}
remoteapplicationname:s:||{app_name}
alternate shell:s:{shell_cmd}
shell working directory:s:{working_dir}
disableremoteappcapscheck:i:1"""

    desktop_dir = get_desktop_path()
    default_filename = f"Negaran_{username if username else 'Remote'}.rdp"
    
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "ذخیره فایل RDP نگاران" if lang_code == "fa" else "Save Negaran RDP File",
        os.path.join(desktop_dir, default_filename),
        "RDP Files (*.rdp)"
    )

    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(rdp_content)
            append_log(f"فایل با موفقیت ذخیره شد: {file_path}", "#34D399")
            msg = f"فایل RDP ذخیره شد:\n{file_path}" if lang_code == "fa" else f"RDP File saved:\n{file_path}"
            QMessageBox.information(parent, "نگاران | Negaran", msg)
        except Exception as e:
            append_log(f"خطا در ذخیره فایل: {e}", "#EF4444")
            QMessageBox.warning(parent, "خطا / Error", f"خطا در ذخیره فایل: {e}")

def launch_mstsc_direct(ip, port, console_widget):
    if not ip or not port:
        QMessageBox.warning(None, "خطا", "لطفاً ابتدا آی‌پی و پورت را وارد کنید.")
        return
    console_widget.clear()
    console_widget.append(f'<span style="color: #FACC15;">[تست اتصال] در حال اجرای MSTSC برای {ip}:{port}...</span>')
    subprocess.Popen(f'mstsc /v:{ip}:{port}', shell=True)

def get_rdpwrap_dir():
    base_dir = get_bundle_dir()
    wrapper_path = os.path.join(base_dir, "RDPWrap-v1.6.2")
    if not os.path.exists(wrapper_path):
        wrapper_path = base_dir
    return wrapper_path

def run_rdpwrap_installer(parent, action="-i", lang_code="fa"):
    wrapper_dir = get_rdpwrap_dir()
    installer_exe = os.path.join(wrapper_dir, "RDPWInst.exe")
    
    if not os.path.exists(installer_exe):
        QMessageBox.warning(parent, "خطا / Error", f"فایل RDPWInst.exe یافت نشد:\n{installer_exe}")
        return

    cmd = f'"{installer_exe}" {action}'
    run_cmd(cmd)
    
    msg = "سرویس RDP Wrapper با موفقیت فعال گردید." if action == "-i" else "سرویس RDP Wrapper حذف شد."
    QMessageBox.information(parent, "نگاران | Negaran", msg)

def launch_rdpwrap_tool(parent, exe_name):
    wrapper_dir = get_rdpwrap_dir()
    tool_exe = os.path.join(wrapper_dir, exe_name)
    
    if not os.path.exists(tool_exe):
        QMessageBox.warning(parent, "خطا / Error", f"فایل {exe_name} یافت نشد:\n{tool_exe}")
        return
    
    subprocess.Popen([tool_exe], shell=True)

def check_rdp_wrapper_diagnostics(console_widget):
    console_widget.clear()
    def append_log(text, color="#38BDF8"):
        console_widget.append(f'<span style="color: {color};">[بررسی Wrapper] {text}</span>')
        QApplication.processEvents()

    append_log("در حال بررسی وضعیت سرویس TermService و فایل‌های RDP Wrapper...", "#FACC15")
    
    ok_svc, svc_out = run_cmd('sc query TermService')
    if ok_svc and "RUNNING" in svc_out:
        append_log("سرویس Remote Desktop (TermService) در حال اجراست.", "#10B981")
    else:
        append_log("هشدار: سرویس TermService متوقف است یا در حال اجرا نیست.", "#EF4444")

    target_dir = r"C:\Program Files\RDP Wrapper"
    ini_path = os.path.join(target_dir, "rdpwrap.ini")
    if os.path.exists(ini_path):
        append_log(f"پوشه و فایل تنظیمات rdpwrap.ini در مسیر استاندارد یافت شد: {target_dir}", "#10B981")
        try:
            with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines_count = len(content.splitlines())
                append_log(f"تعداد خطوط فایل کانفیگ INI: {lines_count} خط.", "#38BDF8")
        except Exception:
            pass
    else:
        append_log("هشدار: فایل rdpwrap.ini در مسیر اصلی Program Files یافت نشد.", "#EF4444")

    wrapper_dir = get_rdpwrap_dir()
    conf_exe = os.path.join(wrapper_dir, "RDPConf.exe")
    if os.path.exists(conf_exe):
        append_log("فایل ابزار پیکربندی RDPConf موجود است.", "#34D399")
    
    append_log("بررسی و عیب‌یابی اولیه به پایان رسید.", "#10B981")

def replace_rdpwrap_ini(parent, lang_code="fa"):
    file_path, _ = QFileDialog.getOpenFileName(
        parent, "انتخاب فایل rdpwrap.ini جدید", "", "INI Files (*.ini);;All Files (*.*)"
    )
    if not file_path:
        return

    target_dir = r"C:\Program Files\RDP Wrapper"
    target_path = os.path.join(target_dir, "rdpwrap.ini")

    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        run_cmd('net stop TermService /y')
        shutil.copy2(file_path, target_path)
        run_cmd('net start TermService')

        msg = "فایل rdpwrap.ini با موفقیت جایگزین گردید." if lang_code == "fa" else "rdpwrap.ini replaced successfully."
        QMessageBox.information(parent, "نگاران | Negaran", msg)
    except Exception as e:
        QMessageBox.warning(parent, "خطا / Error", f"خطا در جایگزینی فایل: {e}")

def auto_download_rdpwrap_ini(parent, lang_code="fa"):
    sources = [
        "https://raw.githubusercontent.com/stascorp/rdpwrap/master/res/rdpwrap.ini",
        "https://raw.githubusercontent.com/binaryify/RdpWrapConfig/master/rdpwrap.ini",
        "https://raw.githubusercontent.com/asardarian/rdpwrap/main/res/rdpwrap.ini",
        "https://raw.githubusercontent.com/sebaxinus/rdpwrap/main/res/rdpwrap.ini"
    ]
    target_dir = r"C:\Program Files\RDP Wrapper"
    target_path = os.path.join(target_dir, "rdpwrap.ini")
    downloaded = False
    last_err = ""

    for url in sources:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read()
                if len(content) > 1000 and b"[10.0." in content:
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    run_cmd('net stop TermService /y')
                    with open(target_path, "wb") as f:
                        f.write(content)
                    run_cmd('net start TermService')
                    downloaded = True
                    break
        except Exception as e:
            last_err = str(e)
            continue

    if downloaded:
        msg = "آخرین نسخه rdpwrap.ini با موفقیت دریافت و اعمال شد." if lang_code == "fa" else "Latest rdpwrap.ini downloaded successfully."
        QMessageBox.information(parent, "نگاران | Negaran", msg)
    else:
        msg = f"خطا در دریافت آنلاین فایل:\n{last_err}" if lang_code == "fa" else f"Download failed:\n{last_err}"
        QMessageBox.warning(parent, "خطا / Error", msg)

class ModernNegaranPyQtApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "fa"
        
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("نگاران | مدیریت دورکاری")
        
        self.resize(640, 680)
        self.setFixedSize(640, 680)

        self.applied_font_family = "IRANSans"
        app_font = QFont(self.applied_font_family, 10)
        app_font.setBold(True)
        self.setFont(app_font)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        self.header_frame.setFixedHeight(60)
        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(2)
        
        self.lbl_head_title = QLabel()
        self.lbl_head_title.setObjectName("HeaderTitle")
        header_layout.addWidget(self.lbl_head_title)

        self.lbl_head_sub = QLabel()
        self.lbl_head_sub.setObjectName("HeaderSub")
        header_layout.addWidget(self.lbl_head_sub)
        
        main_layout.addWidget(self.header_frame)

        self.tabview = QTabWidget()
        main_layout.addWidget(self.tabview)

        self.tab_user = QWidget()
        self.tab_network = QWidget()
        self.tab_rdp = QWidget()
        self.tab_wrapper = QWidget()
        self.tab_portal = QWidget()

        self.tabview.addTab(self.tab_user, "")
        self.tabview.addTab(self.tab_network, "")
        self.tabview.addTab(self.tab_rdp, "")
        self.tabview.addTab(self.tab_wrapper, "")
        self.tabview.addTab(self.tab_portal, "")

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(5, 0, 5, 0)

        self.lbl_footer = QLabel()
        footer_layout.addWidget(self.lbl_footer)

        footer_layout.addStretch()

        self.lang_btn = QPushButton("English 🌐")
        self.lang_btn.setFixedSize(100, 30)
        self.lang_btn.clicked.connect(self.toggle_language)
        footer_layout.addWidget(self.lang_btn)

        main_layout.addLayout(footer_layout)

        self.setup_user_tab()
        self.setup_network_tab()
        self.setup_rdp_tab()
        self.setup_wrapper_tab()
        self.setup_portal_tab()

        self.update_language()

    def toggle_language(self):
        self.current_lang = "en" if self.current_lang == "fa" else "fa"
        self.lang_btn.setText("فارسی 🌐" if self.current_lang == "en" else "English 🌐")
        self.update_language()

    def generate_random_password(self):
        chars = string.ascii_letters + string.digits + "@#$!%*"
        password = "".join(random.choice(chars) for _ in range(10))
        self.ent_pass.setText(password)

    def toggle_password_visibility(self, checked):
        if checked:
            self.ent_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_pass.setText("🙈")
        else:
            self.ent_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_pass.setText("👁️")

    def open_desktop_log_file(self):
        desktop = get_desktop_path()
        log_path = os.path.join(desktop, "کاربرا.txt")
        if os.path.exists(log_path):
            os.startfile(log_path)
        else:
            QMessageBox.warning(self, "فایل یافت نشد", "هنوز فایلی بر روی دسکتاپ ایجاد نشده است.")

    def copy_ip_to_clipboard(self):
        text = self.lbl_ip_result.text()
        if ":" in text:
            ip_val = text.split(":")[-1].strip()
            if ip_val and "در حال" not in ip_val and "خطا" not in ip_val:
                clipboard = QApplication.clipboard()
                clipboard.setText(ip_val)
                QMessageBox.information(self, "موفق", "آی‌پی در کلیپ‌بورد کپی شد!")

    def grab_ip_to_rdp(self):
        text = self.lbl_ip_result.text()
        if ":" in text:
            ip_val = text.split(":")[-1].strip()
            if ip_val and "در حال" not in ip_val and "خطا" not in ip_val:
                self.ent_rdp_ip.setText(ip_val)
                return
        fetch_public_ip(self.lbl_ip_result, self.ent_rdp_ip, self.current_lang)

    def select_portal_rdp_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب فایل RDP مرجع", get_desktop_path(), "RDP Files (*.rdp);;All Files (*.*)"
        )
        if file_path:
            self.ent_portal_rdp_path.setText(file_path)

    def setup_user_tab(self):
        layout = QVBoxLayout(self.tab_user)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(6)

        self.lbl_user = QLabel()
        layout.addWidget(self.lbl_user)
        self.ent_user = QLineEdit()
        self.ent_user.setObjectName("FormInput")
        layout.addWidget(self.ent_user)

        self.lbl_pass = QLabel()
        layout.addWidget(self.lbl_pass)

        pass_layout = QHBoxLayout()
        self.ent_pass = QLineEdit()
        self.ent_pass.setObjectName("FormInput")
        self.ent_pass.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_show_pass = QPushButton("👁️")
        self.btn_show_pass.setFixedWidth(40)
        self.btn_show_pass.setCheckable(True)
        self.btn_show_pass.setObjectName("SecondaryButton")
        self.btn_show_pass.clicked.connect(self.toggle_password_visibility)

        self.btn_gen_pass = QPushButton()
        self.btn_gen_pass.setObjectName("SecondaryButton")
        self.btn_gen_pass.clicked.connect(self.generate_random_password)

        pass_layout.addWidget(self.ent_pass)
        pass_layout.addWidget(self.btn_show_pass)
        pass_layout.addWidget(self.btn_gen_pass)
        layout.addLayout(pass_layout)

        self.chk_admin_box = QCheckBox()
        self.chk_admin_box.setChecked(True)
        layout.addWidget(self.chk_admin_box)

        self.chk_rdp_box = QCheckBox()
        self.chk_rdp_box.setChecked(True)
        layout.addWidget(self.chk_rdp_box)

        btn_layout = QHBoxLayout()
        self.btn_create = QPushButton()
        self.btn_create.setObjectName("PrimaryButton")
        self.btn_create.clicked.connect(lambda: create_and_setup_user_advanced(
            self, self.ent_user.text().strip(), self.ent_pass.text().strip(),
            self.chk_admin_box.isChecked(), self.chk_rdp_box.isChecked(),
            self.console_box, self.current_lang
        ))
        
        self.btn_help = QPushButton()
        self.btn_help.setObjectName("SecondaryButton")
        self.btn_help.setFixedWidth(80)
        self.btn_help.clicked.connect(lambda: QMessageBox.information(self, LANGUAGES[self.current_lang]["help_title"], LANGUAGES[self.current_lang]["help_msg"]))

        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_help)
        layout.addLayout(btn_layout)

        self.lbl_console = QLabel()
        layout.addWidget(self.lbl_console)

        self.console_box = QTextEdit()
        self.console_box.setObjectName("ConsoleBox")
        self.console_box.setReadOnly(True)
        self.console_box.setFixedHeight(95)
        layout.addWidget(self.console_box)

        log_layout = QHBoxLayout()
        self.btn_open_log = QPushButton()
        self.btn_open_log.setObjectName("SecondaryButton")
        self.btn_open_log.clicked.connect(self.open_desktop_log_file)
        log_layout.addWidget(self.btn_open_log)
        layout.addLayout(log_layout)

    def setup_network_tab(self):
        layout = QVBoxLayout(self.tab_network)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(6)

        self.lbl_port = QLabel()
        layout.addWidget(self.lbl_port)
        
        port_layout = QHBoxLayout()
        self.ent_port = QLineEdit("4111")
        self.ent_port.setObjectName("FormInputCenter")
        
        btn_preset1 = QPushButton("3389")
        btn_preset1.setFixedWidth(60)
        btn_preset1.setObjectName("SecondaryButton")
        btn_preset1.clicked.connect(lambda: self.ent_port.setText("3389"))

        btn_preset2 = QPushButton("4111")
        btn_preset2.setFixedWidth(60)
        btn_preset2.setObjectName("SecondaryButton")
        btn_preset2.clicked.connect(lambda: self.ent_port.setText("4111"))

        port_layout.addWidget(self.ent_port)
        port_layout.addWidget(btn_preset1)
        port_layout.addWidget(btn_preset2)
        layout.addLayout(port_layout)

        net_btn_layout = QHBoxLayout()
        self.btn_port = QPushButton()
        self.btn_port.setObjectName("PrimaryButton")
        self.btn_port.clicked.connect(lambda: change_rdp_port_advanced(self, self.ent_port.text().strip(), self.net_console_box, self.current_lang))

        self.btn_check_port = QPushButton()
        self.btn_check_port.setObjectName("SecondaryButton")
        self.btn_check_port.clicked.connect(lambda: check_port_listening(self.ent_port.text().strip(), self.net_console_box))

        net_btn_layout.addWidget(self.btn_port)
        net_btn_layout.addWidget(self.btn_check_port)
        layout.addLayout(net_btn_layout)

        layout.addSpacing(5)

        ip_box_layout = QHBoxLayout()
        self.lbl_ip_result = QLabel()
        self.lbl_ip_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ip_result.setStyleSheet("color: #38BDF8; font-weight: bold;")
        
        self.btn_copy_ip = QPushButton()
        self.btn_copy_ip.setObjectName("SecondaryButton")
        self.btn_copy_ip.setFixedWidth(90)
        self.btn_copy_ip.clicked.connect(self.copy_ip_to_clipboard)

        ip_box_layout.addWidget(self.lbl_ip_result)
        ip_box_layout.addWidget(self.btn_copy_ip)
        layout.addLayout(ip_box_layout)

        self.btn_ip = QPushButton()
        self.btn_ip.setObjectName("SuccessButton")
        self.btn_ip.clicked.connect(lambda: fetch_public_ip(self.lbl_ip_result, self.ent_rdp_ip, self.current_lang))
        layout.addWidget(self.btn_ip)

        self.lbl_net_console = QLabel()
        layout.addWidget(self.lbl_net_console)

        self.net_console_box = QTextEdit()
        self.net_console_box.setObjectName("ConsoleBox")
        self.net_console_box.setReadOnly(True)
        self.net_console_box.setFixedHeight(105)
        layout.addWidget(self.net_console_box)

    def setup_rdp_tab(self):
        layout = QVBoxLayout(self.tab_rdp)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        self.lbl_rdp_ip = QLabel()
        layout.addWidget(self.lbl_rdp_ip)
        
        ip_layout = QHBoxLayout()
        self.ent_rdp_ip = QLineEdit()
        self.ent_rdp_ip.setObjectName("FormInputCenter")
        
        self.btn_grab_ip = QPushButton()
        self.btn_grab_ip.setObjectName("SecondaryButton")
        self.btn_grab_ip.setFixedWidth(95)
        self.btn_grab_ip.clicked.connect(self.grab_ip_to_rdp)

        ip_layout.addWidget(self.ent_rdp_ip)
        ip_layout.addWidget(self.btn_grab_ip)
        layout.addLayout(ip_layout)

        self.lbl_rdp_port = QLabel()
        layout.addWidget(self.lbl_rdp_port)
        
        rdp_port_layout = QHBoxLayout()
        self.ent_rdp_port = QLineEdit("4111")
        self.ent_rdp_port.setObjectName("FormInputCenter")
        
        btn_p1 = QPushButton("3389")
        btn_p1.setFixedWidth(60)
        btn_p1.setObjectName("SecondaryButton")
        btn_p1.clicked.connect(lambda: self.ent_rdp_port.setText("3389"))

        btn_p2 = QPushButton("4111")
        btn_p2.setFixedWidth(60)
        btn_p2.setObjectName("SecondaryButton")
        btn_p2.clicked.connect(lambda: self.ent_rdp_port.setText("4111"))

        rdp_port_layout.addWidget(self.ent_rdp_port)
        rdp_port_layout.addWidget(btn_p1)
        rdp_port_layout.addWidget(btn_p2)
        layout.addLayout(rdp_port_layout)

        self.lbl_rdp_user = QLabel()
        layout.addWidget(self.lbl_rdp_user)
        self.ent_rdp_user = QLineEdit()
        self.ent_rdp_user.setObjectName("FormInput")
        layout.addWidget(self.ent_rdp_user)

        self.lbl_rdp_holoo = QLabel()
        layout.addWidget(self.lbl_rdp_holoo)
        
        holoo_layout = QHBoxLayout()
        self.ent_holoo = QLineEdit()
        self.ent_holoo.setObjectName("FormInput")
        
        self.btn_browse = QPushButton()
        self.btn_browse.setObjectName("SecondaryButton")
        self.btn_browse.setFixedWidth(100)
        self.btn_browse.clicked.connect(self.browse_holoo_file)

        holoo_layout.addWidget(self.ent_holoo)
        holoo_layout.addWidget(self.btn_browse)
        layout.addLayout(holoo_layout)

        options_layout = QHBoxLayout()
        self.chk_smart_sizing = QCheckBox()
        self.chk_smart_sizing.setChecked(True)
        
        self.chk_redirect = QCheckBox()
        self.chk_redirect.setChecked(True)

        options_layout.addWidget(self.chk_smart_sizing)
        options_layout.addWidget(self.chk_redirect)
        layout.addLayout(options_layout)

        action_layout = QHBoxLayout()
        self.btn_gen_rdp = QPushButton()
        self.btn_gen_rdp.setObjectName("SuccessButton")
        self.btn_gen_rdp.clicked.connect(lambda: generate_rdp_file_advanced(
            self, self.ent_rdp_ip.text().strip(), self.ent_rdp_port.text().strip(),
            self.ent_rdp_user.text().strip(), self.ent_holoo.text().strip(),
            self.chk_smart_sizing.isChecked(), self.chk_redirect.isChecked(),
            self.rdp_console_box, self.current_lang
        ))

        self.btn_test_mstsc = QPushButton()
        self.btn_test_mstsc.setObjectName("PrimaryButton")
        self.btn_test_mstsc.clicked.connect(lambda: launch_mstsc_direct(
            self.ent_rdp_ip.text().strip(), self.ent_rdp_port.text().strip(), self.rdp_console_box
        ))

        action_layout.addWidget(self.btn_gen_rdp)
        action_layout.addWidget(self.btn_test_mstsc)
        layout.addLayout(action_layout)

        self.lbl_rdp_console = QLabel()
        layout.addWidget(self.lbl_rdp_console)

        self.rdp_console_box = QTextEdit()
        self.rdp_console_box.setObjectName("ConsoleBox")
        self.rdp_console_box.setReadOnly(True)
        self.rdp_console_box.setFixedHeight(70)
        layout.addWidget(self.rdp_console_box)

    def setup_portal_tab(self):
        layout = QVBoxLayout(self.tab_portal)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)

        self.lbl_portal_desc = QLabel()
        layout.addWidget(self.lbl_portal_desc)

        file_layout = QHBoxLayout()
        self.ent_portal_rdp_path = QLineEdit()
        self.ent_portal_rdp_path.setObjectName("FormInput")
        self.ent_portal_rdp_path.setReadOnly(True)

        self.btn_browse_rdp_file = QPushButton()
        self.btn_browse_rdp_file.setObjectName("SecondaryButton")
        self.btn_browse_rdp_file.setFixedWidth(160)
        self.btn_browse_rdp_file.clicked.connect(self.select_portal_rdp_file)

        file_layout.addWidget(self.ent_portal_rdp_path)
        file_layout.addWidget(self.btn_browse_rdp_file)
        layout.addLayout(file_layout)

        self.btn_build_portal = QPushButton()
        self.btn_build_portal.setObjectName("SuccessButton")
        self.btn_build_portal.clicked.connect(lambda: create_client_portal_package(
            self, self.ent_portal_rdp_path.text().strip(),
            self.portal_console_box, self.current_lang
        ))
        layout.addWidget(self.btn_build_portal)

        self.lbl_portal_console = QLabel()
        layout.addWidget(self.lbl_portal_console)

        self.portal_console_box = QTextEdit()
        self.portal_console_box.setObjectName("ConsoleBox")
        self.portal_console_box.setReadOnly(True)
        self.portal_console_box.setFixedHeight(120)
        layout.addWidget(self.portal_console_box)

    def create_card(self, title_key, desc_key, btn_key, btn_obj_name, callback):
        card = QFrame()
        card.setObjectName("CardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        
        lbl_title = QLabel()
        lbl_title.setObjectName("CardTitle")
        setattr(card, "lbl_title", lbl_title)
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel()
        lbl_desc.setObjectName("CardDesc")
        lbl_desc.setWordWrap(True)
        setattr(card, "lbl_desc", lbl_desc)
        layout.addWidget(lbl_desc)
        
        layout.addStretch()
        
        btn = QPushButton()
        btn.setObjectName(btn_obj_name)
        btn.clicked.connect(callback)
        setattr(card, "btn", btn)
        layout.addWidget(btn)
        
        setattr(card, "title_key", title_key)
        setattr(card, "desc_key", desc_key)
        setattr(card, "btn_key", btn_key)
        
        return card

    def setup_wrapper_tab(self):
        main_wrapper_layout = QVBoxLayout(self.tab_wrapper)
        main_wrapper_layout.setContentsMargins(10, 8, 10, 8)
        main_wrapper_layout.setSpacing(6)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(8)
        grid_layout.setVerticalSpacing(8)

        self.cards = []
        
        c1 = self.create_card("card1_title", "card1_desc", "card1_btn", "PrimaryButton", lambda: run_rdpwrap_installer(self, "-i", self.current_lang))
        c2 = self.create_card("card2_title", "card2_desc", "card2_btn", "SecondaryButton", lambda: launch_rdpwrap_tool(self, "RDPConf.exe"))
        c3 = self.create_card("card3_title", "card3_desc", "card3_btn", "SecondaryButton", lambda: launch_rdpwrap_tool(self, "RDPCheck.exe"))
        c4 = self.create_card("card4_title", "card4_desc", "card4_btn", "SecondaryButton", lambda: replace_rdpwrap_ini(self, self.current_lang))
        c5 = self.create_card("card5_title", "card5_desc", "card5_btn", "SuccessButton", lambda: auto_download_rdpwrap_ini(self, self.current_lang))
        c6 = self.create_card("card6_title", "card6_desc", "card6_btn", "DangerButton", lambda: run_rdpwrap_installer(self, "-u", self.current_lang))

        self.cards = [c1, c2, c3, c4, c5, c6]

        grid_layout.addWidget(c1, 0, 0)
        grid_layout.addWidget(c2, 0, 1)
        grid_layout.addWidget(c3, 1, 0)
        grid_layout.addWidget(c4, 1, 1)
        grid_layout.addWidget(c5, 2, 0)
        grid_layout.addWidget(c6, 2, 1)

        main_wrapper_layout.addLayout(grid_layout)

        self.btn_check_wrapper = QPushButton()
        self.btn_check_wrapper.setObjectName("SecondaryButton")
        self.btn_check_wrapper.clicked.connect(lambda: check_rdp_wrapper_diagnostics(self.wrapper_console_box))
        main_wrapper_layout.addWidget(self.btn_check_wrapper)

        self.lbl_wrapper_console = QLabel()
        main_wrapper_layout.addWidget(self.lbl_wrapper_console)

        self.wrapper_console_box = QTextEdit()
        self.wrapper_console_box.setObjectName("ConsoleBox")
        self.wrapper_console_box.setReadOnly(True)
        self.wrapper_console_box.setFixedHeight(75)
        main_wrapper_layout.addWidget(self.wrapper_console_box)

    def browse_holoo_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل Holoo.exe", "", "Executable Files (*.exe);;All Files (*.*)")
        if path:
            self.ent_holoo.setText(path)

    def update_language(self):
        lang = LANGUAGES[self.current_lang]
        
        self.setWindowTitle(lang["title"])
        self.lbl_head_title.setText(lang["header_title"])
        self.lbl_head_sub.setText(lang["header_subtitle"])

        self.tabview.setTabText(0, lang["tab_user"])
        self.tabview.setTabText(1, lang["tab_network"])
        self.tabview.setTabText(2, lang["tab_rdp"])
        self.tabview.setTabText(3, lang["tab_wrapper"])
        self.tabview.setTabText(4, lang["tab_portal"])

        self.lbl_user.setText(lang["username_lbl"])
        self.lbl_pass.setText(lang["password_lbl"])
        self.btn_create.setText(lang["btn_create_user"])
        self.btn_gen_pass.setText(lang["btn_gen_pass"])
        self.chk_admin_box.setText(lang["chk_admin"])
        self.chk_rdp_box.setText(lang["chk_rdp"])
        self.lbl_console.setText(lang["console_title"])
        self.btn_open_log.setText(lang["btn_open_log"])
        self.btn_help.setText(lang["btn_help"])

        self.lbl_port.setText(lang["port_lbl"])
        self.btn_port.setText(lang["btn_change_port"])
        self.btn_check_port.setText(lang["btn_check_port"])
        self.lbl_ip_result.setText(lang["public_ip_lbl"])
        self.btn_ip.setText(lang["btn_fetch_ip"])
        self.btn_copy_ip.setText(lang["btn_copy_ip"])
        self.lbl_net_console.setText(lang["net_console_title"])

        self.lbl_rdp_ip.setText(lang["rdp_ip_lbl"])
        self.lbl_rdp_port.setText(lang["rdp_port_lbl"])
        self.lbl_rdp_user.setText(lang["rdp_user_lbl"])
        self.lbl_rdp_holoo.setText(lang["rdp_holoo_lbl"])
        self.btn_browse.setText(lang["btn_browse_holoo"])
        self.btn_grab_ip.setText(lang["btn_grab_ip"])
        self.chk_smart_sizing.setText(lang["chk_smart_sizing"])
        self.chk_redirect.setText(lang["chk_redirect"])
        self.btn_gen_rdp.setText(lang["btn_gen_rdp"])
        self.btn_test_mstsc.setText(lang["btn_test_mstsc"])
        self.lbl_rdp_console.setText(lang["rdp_console_title"])

        self.lbl_portal_desc.setText(lang["portal_desc"])
        self.btn_browse_rdp_file.setText(lang["btn_browse_rdp"])
        self.btn_build_portal.setText(lang["btn_build_portal"])
        self.lbl_portal_console.setText(lang["portal_console_title"])

        for card in self.cards:
            card.lbl_title.setText(lang[card.title_key])
            card.lbl_desc.setText(lang[card.desc_key])
            card.btn.setText(lang[card.btn_key])

        self.btn_check_wrapper.setText(lang["btn_check_wrapper"])
        self.lbl_wrapper_console.setText(lang["wrapper_console_title"])

        self.lbl_footer.setText(lang["footer"])

if __name__ == "__main__":
    run_as_admin()
    app = QApplication(sys.argv)
    
    font_file_path = os.path.join(get_bundle_dir(), "IRANSans.ttf")
    if os.path.exists(font_file_path):
        QFontDatabase.addApplicationFont(font_file_path)

    app.setStyleSheet("""
        QMainWindow { background-color: #0F172A; font-family: 'IRANSans', 'Segoe UI', Tahoma, sans-serif; }
        QWidget { background-color: #0F172A; color: #F8FAFC; font-size: 10pt; font-family: 'IRANSans', 'Segoe UI', Tahoma, sans-serif; }
        
        #HeaderFrame { background-color: #1E293B; border-radius: 8px; border: 1px solid #334155; }
        #HeaderTitle { font-size: 11pt; font-weight: bold; color: #F8FAFC; }
        #HeaderSub { font-size: 9pt; color: #94A3B8; }
        
        QTabWidget::pane { border: 1px solid #334155; background: #1E293B; border-radius: 8px; }
        QTabBar::tab { background: #334155; color: #94A3B8; padding: 6px 12px; margin: 2px; border-radius: 5px; font-size: 9.5pt; }
        QTabBar::tab:selected { background: #3B82F6; color: white; font-weight: bold; }
        
        #CardFrame { background-color: #1E293B; border: 1px solid #334155; border-radius: 8px; }
        #CardFrame:hover { border: 1px solid #3B82F6; }
        #CardTitle { font-size: 9.5pt; font-weight: bold; color: #F8FAFC; }
        #CardDesc { font-size: 8pt; color: #94A3B8; }
        
        #FormInput { background-color: #1E293B; border: 1px solid #475569; border-radius: 6px; padding: 5px; color: white; height: 24px; }
        #FormInputCenter { background-color: #1E293B; border: 1px solid #475569; border-radius: 6px; padding: 5px; color: white; height: 24px; text-align: center; }
        #FormInput:focus, #FormInputCenter:focus { border: 1px solid #3B82F6; }
        
        QCheckBox { color: #E2E8F0; font-size: 9pt; spacing: 5px; }
        QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; border: 1px solid #475569; background: #1E293B; }
        QCheckBox::indicator:checked { background: #3B82F6; border: 1px solid #3B82F6; }
        
        #ConsoleBox { background-color: #090D16; border: 1px solid #334155; border-radius: 6px; color: #38BDF8; font-family: Consolas, monospace; font-size: 8.5pt; }
        
        QPushButton { font-weight: bold; border-radius: 6px; padding: 4px 8px; height: 28px; font-size: 9pt; }
        #PrimaryButton { background-color: #3B82F6; color: white; }
        #PrimaryButton:hover { background-color: #2563EB; }
        
        #SuccessButton { background-color: #10B981; color: white; }
        #SuccessButton:hover { background-color: #059669; }
        
        #DangerButton { background-color: #EF4444; color: white; }
        #DangerButton:hover { background-color: #DC2626; }
        
        #SecondaryButton { background-color: #475569; color: white; }
        #SecondaryButton:hover { background-color: #334155; }
    """)
    
    window = ModernNegaranPyQtApp()
    window.show()
    sys.exit(app.exec())