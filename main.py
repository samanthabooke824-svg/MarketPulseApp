import flet as ft
import asyncio
import json
import os
import datetime
import random
import google.generativeai as genai
from telethon import TelegramClient, events

# ==========================================
# 1. CONFIGURATION (Tsy miova)
# ==========================================
api_id = 36037312
api_hash = 'fe89bd6924f29086e7c400384e1211a6'
GEMINI_API_KEYS = ['AIzaSyBw2y5ZFv7mSiEQn8XTah2udYyCXPGn3xA'] # Ataovy ato ny anao rehetra

SOURCE_CHANNELS = [-1002807324858, -1001903141856, -1003706344371]
DESTINATION_CHANNEL = -1003734019434

genai.configure(api_key=GEMINI_API_KEYS[0])
model = genai.GenerativeModel('gemini-2.5-flash')

# Database
active_signals = {}
pending_signals = {}
mt5_data = {"balance": 10000.0, "profit": 0.0, "equity": 10000.0} # SIMULATION MT5

# ==========================================
# 2. LOGIC (Bot & AI - Nohakelezina)
# ==========================================
async def parse_message_with_ai(text=None):
    prompt = """Forex Parser. Reply ONLY with raw JSON: {"category": "SIGNAL", "asset": "XAUUSD", "direction": "BUY", "entry": 2000.0, "sl": 1990.0, "tps": [2010.0]}"""
    try:
        response = await asyncio.to_thread(model.generate_content, [prompt, text])
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except:
        return {"category": "NONE"}

# ==========================================
# 3. INTERFACE ANDROID (FLET)
# ==========================================
async def main(page: ft.Page):
    page.title = "MarketPulse Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = "auto"
    page.window_width = 400 # Habean'ny finday raha sokafana amin'ny PC

    # --- UI ELEMENTS ---
    lbl_status = ft.Text("Telegram: Disconnected 🔴", color=ft.colors.RED_400, weight="bold")
    
    # Metrics Cards
    def create_metric_card(title, value, val_color):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(title, size=12, color=ft.colors.GREY_400),
                    ft.Text(value, size=20, color=val_color, weight="bold"),
                ]),
                padding=10,
                width=110,
                bgcolor=ft.colors.BLUE_GREY_900
            )
        )

    val_bal = ft.Text("$10,000.00", size=18, color=ft.colors.WHITE, weight="bold")
    val_pnl = ft.Text("$0.00", size=18, color=ft.colors.GREEN_400, weight="bold")
    
    metrics_row = ft.Row([
        create_metric_card("BALANCE", "$10,000", ft.colors.WHITE),
        create_metric_card("LIVE PNL", "+$0.00", ft.colors.GREEN_400),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # Lists ho an'ny Signals
    pending_list = ft.Column()
    active_list = ft.Column()

    def update_ui():
        # Eto no manavao ny écran (UI) isaky ny misy signal vaovao
        pending_list.controls.clear()
        if not pending_signals:
            pending_list.controls.append(ft.Text("Tsy misy pending signal...", color=ft.colors.GREY_500))
        else:
            for sig_id, data in pending_signals.items():
                card = ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"{data.get('asset', 'UNKNOWN')}", weight="bold", size=16),
                        ft.Text(f"Direction: {data.get('direction', 'BUY')}", color=ft.colors.BLUE_200),
                        ft.Text(f"Entry: {data.get('entry')} | SL: {data.get('sl')}"),
                        ft.Row([
                            ft.ElevatedButton("SEND 🚀", bgcolor=ft.colors.GREEN_700, color="white"),
                            ft.ElevatedButton("CANCEL 🚫", bgcolor=ft.colors.RED_700, color="white"),
                        ])
                    ]), padding=10
                ))
                pending_list.controls.append(card)

        page.update()

    # Layout an'ny App
    page.add(
        ft.SafeArea(
            ft.Column([
                ft.Text("MarketPulse Analytics", size=24, weight="bold", color=ft.colors.CYAN_400),
                lbl_status,
                ft.Divider(),
                metrics_row,
                ft.Divider(),
                ft.Text("PENDING SIGNALS", weight="bold", color=ft.colors.ORANGE_400),
                pending_list,
                ft.Divider(),
                ft.Text("ACTIVE SIGNALS", weight="bold", color=ft.colors.GREEN_400),
                active_list,
            ])
        )
    )

    update_ui()

    # ==========================================
    # 4. TELETHON BACKGROUND TASK
    # ==========================================
    client = TelegramClient('mobile_session', api_id, api_hash)

    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def source_handler(event):
        text_data = event.text or ""
        # Antsoy ny AI
        ai_data = await parse_message_with_ai(text=text_data)
        
        if ai_data.get("category") == "SIGNAL":
            sig_id = str(event.id)
            pending_signals[sig_id] = ai_data
            
            # Mampandre ny UI fa misy zavatra vaovao
            update_ui()
            # Fampandrenesana tsotra finday (Toast)
            page.snack_bar = ft.SnackBar(ft.Text(f"Signal vaovao: {ai_data.get('asset')}"))
            page.snack_bar.open = True
            page.update()

    # Mampifandray ny Telegram
    await client.start()
    lbl_status.value = "Telegram: Connected 🟢"
    lbl_status.color = ft.colors.GREEN_400
    page.update()
    
    # Mihazona ilay application handeha foana
    await client.run_until_disconnected()

# Mandefa ilay application ho toy ny application finday/desktop
ft.app(target=main)