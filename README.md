# Negaran RDP Telework Manager

A powerful Windows desktop application for managing Remote Desktop (RDP) 
connections, user accounts, Windows Firewall rules, and building standalone 
client portals for remote workers.

Built with **Python 3** and **PyQt6**, currently used in production by an 
Iranian company to manage **20+ remote employees**, with plans to scale 
further.

---

## ✨ Features

### 👤 User Management
- Create Windows users automatically with pre-configured settings
- Apply Persian (fa-IR) and English (en-US) keyboard layouts per user
- Set region, date format (yyyy/MM/dd), and locale to Iran
- Grant Administrators and/or Remote Desktop Users group membership
- Set passwords to never expire
- Auto-save credentials log to the desktop
- Optional encrypted credential caching (XOR + Base64)

### 🌐 Network & Firewall
- Change the RDP port (e.g. 3389 → 4111) with a single click
- Automatically update Windows Firewall rules (TCP + UDP)
- Restart Terminal Services (TermService) safely
- Check if a port is actively listening
- Fetch public/static IP address and copy it to clipboard

### 📄 RDP File Generator
- Generate custom `.rdp` connection files
- Smart sizing and resource redirection (drives, clipboard, printers)
- Integration with **Holoo ERP** — auto-launch Holoo.exe on connect
- One-click test launch via `mstsc`

### 🛡️ RDP Wrapper Support
- Install / uninstall RDP Wrapper service
- Open RDPConf and RDPCheck utilities
- Replace `rdpwrap.ini` manually
- Auto-download the latest `rdpwrap.ini` from online sources
- Built-in diagnostics console

### 📦 Client Portal Builder
- Select a reference `.rdp` file
- Auto-generate a standalone Windows **EXE** portal via PyInstaller
- Portal prompts the end user for their username & password
- Credentials are injected into the RDP session using `cmdkey`
- Perfect for non-technical remote employees

### 🌍 Bilingual Interface
- Full **Persian (RTL)** and **English (LTR)** UI
- Switchable with a single click

---

## 🖥️ Requirements

- Windows 10 / 11
- Python 3.10+
- Administrator privileges (the app requests elevation automatically)

### Python Dependencies

```bash
pip install PyQt6
```

---

## 🚀 Installation

```bash
git clone https://github.com/lor-dll/RDP-Telework-Manager.git
cd RDP-Telework-Manager
pip install -r requirements.txt
python Negaran.py
```

> The application will automatically request Administrator privileges 
> on launch.

---

## 🧩 Usage Overview

| Tab | Purpose |
|-----|---------|
| 👤 User Setup | Create and configure Windows users for remote work |
| 🌐 Network | Change RDP port & update Windows Firewall |
| 📄 RDP Gen | Build custom `.rdp` files with Holoo integration |
| 🛡️ RDP Wrapper | Install & manage RDP Wrapper for multi-session |
| 📦 Client Portal | Build a standalone EXE for end users |

---

## 📸 Screenshots

*(Add screenshots here — they significantly boost repository credibility.)*

---

## 🔐 Security Notes

- This tool is designed for **legitimate business use** in controlled 
  environments where IT administrators manage remote access.
- Credential caching uses XOR + Base64 obfuscation. Do not rely on it 
  as strong encryption.
- Always follow your organization's security policies.

---

## 🤝 Contributing

Pull requests, issues, and feature suggestions are welcome.
If you find a bug, please open an issue with steps to reproduce it.

---

## 📜 License

This project is licensed under the **MIT License** — see the 
[LICENSE](LICENSE) file for details.

---

## 👤 Author

**Meysam** ([@lor-dll](https://github.com/lor-dll))

---

## ⭐ Support

If this project helped you, please give it a ⭐ on GitHub!
