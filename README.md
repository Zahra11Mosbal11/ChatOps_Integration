
# ChatOps Network Monitor Telegram Bot

A lightweight, asynchronous Telegram bot for real-time network monitoring and diagnostics. Built for DevSecOps workflows, it lets you check device reachability, run traceroutes, and receive instant downtime or high-latency alerts directly in chat.

<img width="2361" height="1555" alt="Screenshot 2026-06-14 at 09 41 44" src="https://github.com/user-attachments/assets/eaa92266-7fe1-4a91-8517-62592cb0e76c" />
<img width="2361" height="1560" alt="Screenshot 2026-06-14 at 09 44 56" src="https://github.com/user-attachments/assets/2e232646-a0f7-429a-91a3-5eab36b46f75" />

---

## ✨ Features

* **On-Demand Ping**: Check ICMP reachability for any custom IP or hostname.
* **Bulk Status Check**: View the UP/DOWN status of all core network devices simultaneously.
* **Async Traceroute**: Run dynamic path diagnostics without freezing the bot.
* **Automated Alerts**: Background tasks scan your network every 60 seconds and alert a designated chat if a device drops or latency spikes (>150ms).
* **Non-Blocking Architecture**: Fully powered by Python's `asyncio` for smooth performance.

---

## 🛠️ Tech Stack

* **Python 3.10+**
* **python-telegram-bot** (with `job-queue`)
* **ping3** (ICMP operations)
* **python-dotenv** (Environment security)

---

##  Quick Start

### 1. Installation

```bash
git clone https://github.com/Zahra11Mosbal11/ChatOps_Integration.git
cd ChatOps_Integration

python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

```

### 2. Configuration

Create a `.env` file in the root directory:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
ALERT_CHAT_ID=your_alert_telegram_chat_id_here

```

> *Get a bot token by messaging [@BotFather](https://t.me/BotFather) on Telegram.*

### 3. Run the Bot

```bash
python main.py

```

*(Note: If you get an ICMP permission error on macOS/Linux, run using `sudo venv/bin/python main.py`)*

---

##  Bot Commands

* `/start` - Welcome message and command guide.
* `/status` - Health check summary of all core infrastructure.
* `/check <IP>` - Ping check and response time for a specific host.
* `/routes <IP>` - Asynchronous traceroute path diagnostics.

---

##  Project Structure

```text
ChatOps_Integration/
├── main.py             # Bot initialization, handlers, and background tasks
├── network_utils.py    # Core network logic (Ping, Traceroute, Health checks)
├── requirements.txt    # Project dependencies
├── .env.example        # Environment template
└── README.md           # Documentation

```
