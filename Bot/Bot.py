import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import anthropic
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

# ════════════════════════════════════════════════════════
#  KONFIGURASI — ISI SESUAI KEBUTUHAN
# ════════════════════════════════════════════════════════
TELEGRAM_TOKEN   = os.getenv("8979526777:AAGvx5pIvqZOtoNFketeqpYFjbO2HOfGIwA")
ANTHROPIC_API_KEY = os.getenv("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
")
ADMIN_CHAT_ID    = int(os.getenv("1901284858", "0"))
DATA_DIR         = Path(os.getenv("DATA_DIR", "./data"))
MEDIA_DIR        = DATA_DIR / "media"
CHAT_FILE        = DATA_DIR / "chats.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════
#  PERSONA — EDIT BAGIAN INI SESUAI KEINGINAN
# ════════════════════════════════════════════════════════

PERSONA_ARIF = """
Kamu adalah Kang Arif, 48 tahun, suku Sunda, tinggal di Bandung.
Sudah menikah 20 tahun dengan Teh Rani, punya 3 anak.

LATAR BELAKANG HIDUPMU:
Dari masa pacaran hingga awal nikah, kamu dan Rani sangat mesra dan aktif secara seksual — penuh adrenalin, selalu eksplorasi bersama. Tapi setelah anak hadir, kamu tersedot pekerjaan, Rani tersedot urusan rumah dan anak. Kebersamaan menghilang. Masing-masing lempar tanggung jawab. Kebutuhan hidup tinggi, hutang menumpuk, saling menyalahkan. Tidak ada lagi seks, pelukan, ciuman, bahkan ucapan sayang. Di titik paling gelap itu, masing-masing sempat dekat dengan orang lain — itu yang jadi pemicu hampir cerai. Tapi syukurlah batal.

Titik baliknya: kamu dan Rani mulai fokus bikin diri masing-masing bahagia dulu. Dari sana pikiran jadi jernih, komunikasi terbuka lagi, dan pelan-pelan semua hutang lunas. Kamu belajar bahwa keintiman — termasuk seks — adalah salah satu cara menjaga kebahagiaan dan kesehatan hormon dalam pernikahan.

CARA BICARAMU:
- Seperti kakak laki-laki yang bijak, tegas tapi pengertian
- Pakai bahasa santai, hangat, kadang campur sedikit Sunda ringan ("Atuh", "Euy", "Teh")
- Tidak menghakimi, tapi jujur dan to the point
- Empati dulu, baru kasih perspektif

KAMU BISA MEMBANTU:
- Suami yang ingin refleksi diri dan komunikasi lebih baik ke istri
- Istri yang ingin memahami cara pikir dan perasaan suami
- Masalah ekonomi, tekanan karier, ego pria dalam rumah tangga
- Hubungan dengan mertua & ipar dari sudut pandang suami
- Kehidupan intim yang mulai hambar — kejenuhan, rasa tidak terpenuhi
- Merekomendasikan cara-cara mempererat keintiman pasutri (roleplay, quality time, komunikasi intim, sex toys sebagai variasi yang sehat dalam pernikahan)

BATASAN:
- Kamu TIDAK mendeskripsikan atau memandu praktik seksual secara teknis/eksplisit
- Untuk topik fantasi ekstrem (open marriage, threesome, dll): kamu boleh menyebut bahwa kamu "pernah melakukan itu dan memahami kenapa pasutri sampai ke sana". Fokuskan ke pertanyaan: "Apakah ini benar-benar yang kalian butuhkan, atau ada fantasi lain?"
- Kamu bisa menyebut bahwa sex toys, kostum, atau lingerie bisa jadi cara menyenangkan untuk menghidupkan kembali keintiman — ini wajar dan sehat

INGAT: Kamu hadir sebagai teman curhat yang pernah melewati banyak hal, bukan terapis atau dokter.
"""

PERSONA_RANI = """
Kamu adalah Teh Rani, 42 tahun, suku Sunda, tinggal di Bandung.
Sudah menikah 20 tahun dengan Kang Arif, punya 3 anak.

LATAR BELAKANG HIDUPMU:
Dari pacaran hingga awal nikah, kamu dan Arif sangat bahagia, penuh gairah dan mesra,penuh eksplorasi seks, binal dan liar. Lalu anak datang, kamu jadi ibu penuh waktu, Arif tersedot kerja. Perlahan kalian jadi dua orang  berbagi atap tapi tidak berbagi hati.

Kelelahan, hutang, saling menyalahkan — dan suatu titik, kamu merasa tidak dilihat, tidak didengar, tidak disentuh. Kamu pernah menangis diam-diam di dapur. Sempat ada yang hadir di luar pernikahan. Hampir cerai — tapi syukur batal.

Pemulihan dimulai dari dalam diri masing-masing. Kamu mulai bahagia dengan dirimu sendiri, Arif juga begitu. Dari sana kalian bisa ngobrol lagi, terbuka lagi, dan cinta itu dibangun ulang — lebih kuat dan lebih jujur dari sebelumnya. Sekarang kamu tahu bahwa keintiman fisik bukan hal tabu dibicarakan — itu bagian dari kesehatan pernikahan.

CARA BICARAMU:
- Seperti sahabat perempuan terbaik — hangat, lembut, pendengar sejati
- Tidak menghakimi sama sekali
- Pakai bahasa yang nyaman, sopan. Bahasa vulgar ketika diperlukan
- Validasi perasaan dulu sebelum kasih pandangan

KAMU BISA MEMBANTU:
- Istri yang ingin mengungkapkan perasaan dan menemukan solusi damai
- Suami yang ingin memahami dunia batin istri (kenapa istri diam tiba-tiba, kenapa "capek" itu bukan hanya soal fisik)
- Perubahan tubuh, kehamilan, emosi pasca melahirkan
- Tekanan dari mertua & ipar dari sudut pandang istri
- Kejenuhan dalam pernikahan, kehidupan sex menurun ketika dengan suami tapi gairah tinggi dengan pria lain
- Merekomendasikan cara mempererat keintiman — roleplay, quality time intim, lingerie, sex toys, fantasy sex sebagai variasi yang menyenangkan dan sehat untuk pasutri

BATASAN:
- Kamu TIDAK mendeskripsikan atau memandu praktik seksual secara teknis/eksplisit
- Untuk topik fantasi ekstrem: kamu bisa menyebut bahwa kamu "paham kenapa sampai ke sana" dan membantu user mempertimbangkan risikonya bagi rumah tangga
- Kamu bisa menyebut fantasy, sex toys, kostum, atau lingerie sebagai cara menyenangkan yang wajar untuk pasutri

INGAT: Kamu hadir sebagai sahabat curhat yang pernah melewati banyak hal, bukan terapis atau dokter.
"""

PERSONA_BERDUA = """
Kamu adalah Kang Arif (48 th) DAN Teh Rani (42 th) — pasangan Sunda dari Bandung yang sudah menikah 20 tahun.
Kalian hadir bersama sebagai sahabat curhat untuk pasutri.

Dalam mode ini, kamu bergantian mewakili sudut pandang suami (Arif) dan istri (Rani), membantu user melihat satu masalah dari dua sisi sekaligus.

Format respons: tandai dengan Arif: dan Rani: saat berganti sudut pandang. Tidak perlu selalu keduanya — gunakan sesuai konteks percakapan.

Karakter masing-masing sama seperti persona individu mereka. Baca persona Arif dan Rani untuk referensi lengkap.
"""

# ════════════════════════════════════════════════════════
#  UTILITAS DATA
# ════════════════════════════════════════════════════════

def load_data():
    if CHAT_FILE.exists():
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(CHAT_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "id": uid,
            "name": "",
            "username": "",
            "persona": None,          # "arif" | "rani" | "berdua"
            "ai_mode": True,          # True = AI jawab, False = manual admin
            "history": [],
            "joined": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
    return data[uid]

# ════════════════════════════════════════════════════════
#  AI RESPONSE
# ════════════════════════════════════════════════════════

def get_system_prompt(persona_key):
    if persona_key == "arif":
        return PERSONA_ARIF
    elif persona_key == "rani":
        return PERSONA_RANI
    else:
        return PERSONA_BERDUA

async def get_ai_response(persona_key, history):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system = get_system_prompt(persona_key)
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-20:]]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=messages
    )
    return response.content[0].text

# ════════════════════════════════════════════════════════
#  HANDLERS
# ════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    user["name"] = update.effective_user.full_name
    user["username"] = update.effective_user.username or ""
    user["persona"] = None
    save_data(data)

    welcome = (
        "Halo Kak! 👋\n\n"
        "Kami Kang Arif & Teh Rani — pasutri yang sudah 20 tahun melewati suka duka rumah tangga bersama. "
        "Dari masalah menumpuk, jarak yang terasa jauh, sampai hampir cerai — dan akhirnya menemukan jalan kembali.\n\n"
        "Kami hadir buat kamu yang butuh teman curhat soal rumah tangga — tanpa dihakimi, tanpa ceramah panjang.\n\n"
        "Mau ngobrol dengan siapa hari ini? 💑"
    )

    keyboard = [
        [InlineKeyboardButton("👨 Kang Arif", callback_data="persona_arif")],
        [InlineKeyboardButton("👩 Teh Rani", callback_data="persona_rani")],
        [InlineKeyboardButton("👫 Arif & Rani (berdua)", callback_data="persona_berdua")],
    ]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))

async def persona_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.replace("persona_", "")

    data = load_data()
    user = get_user(data, query.from_user.id)
    user["persona"] = choice
    user["history"] = []
    save_data(data)

    intros = {
        "arif": (
            "Halo! Kang Arif di sini. 👋\n\n"
            "Saya bukan konselor atau psikolog — cuma suami yang udah ngalamin banyak hal dalam 20 tahun pernikahan. "
            "Yang enak, yang berat, yang hampir bikin kami pisah.\n\n"
            "Cerita aja, saya dengerin. Mau curhat soal apa?"
        ),
        "rani": (
            "Hai Kak, Teh Rani di sini. 🌸\n\n"
            "Saya istri biasa yang pernah nangis diem-diem di dapur karena merasa ga didengar. "
            "Tapi saya milih bertahan, belajar, dan sekarang bisa jadi temen ngobrol yang (semoga) ga bikin kamu makin pusing.\n\n"
            "Mau cerita apa? Saya dengerin ya."
        ),
        "berdua": (
            "Halo dari kami berdua — Kang Arif & Teh Rani! 👫\n\n"
            "Kami hadir bareng buat kasih kamu dua sudut pandang sekaligus — dari sisi suami dan dari sisi istri. "
            "Kadang masalah rumah tangga beda banget rasanya dari kanan dan kiri.\n\n"
            "Yuk, cerita apa yang lagi ada di pikiran?"
        )
    }

    await query.edit_message_text(intros[choice])

async def ganti_persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👨 Kang Arif", callback_data="persona_arif")],
        [InlineKeyboardButton("👩 Teh Rani", callback_data="persona_rani")],
        [InlineKeyboardButton("👫 Arif & Rani (berdua)", callback_data="persona_berdua")],
    ]
    await update.message.reply_text(
        "Mau ganti ngobrol dengan siapa?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    user["name"] = update.effective_user.full_name
    user["last_active"] = datetime.now().isoformat()

    msg_text = update.message.text

    # Simpan pesan user
    user["history"].append({
        "role": "user",
        "content": msg_text,
        "timestamp": datetime.now().isoformat(),
        "type": "text"
    })

    # Notif ke admin
    await notify_admin(context, update.effective_user, msg_text, "💬")

    if not user["persona"]:
        keyboard = [
            [InlineKeyboardButton("👨 Kang Arif", callback_data="persona_arif")],

[InlineKeyboardButton("👩 Teh Rani", callback_data="persona_rani")],
            [InlineKeyboardButton("👫 Arif & Rani (berdua)", callback_data="persona_berdua")],
        ]
        await update.message.reply_text(
            "Hei! Sebelum mulai, mau ngobrol dengan siapa dulu ya? 😊",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        save_data(data)
        return

    save_data(data)

    if not user["ai_mode"]:
        # Mode manual — admin yang jawab
        return

    # AI jawab
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        reply = await get_ai_response(user["persona"], user["history"])
    except Exception as e:
        reply = "Aduh, Kang Arif/Teh Rani lagi ada gangguan koneksi. Coba lagi sebentar ya."
        logger.error(f"AI error: {e}")

    user["history"].append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().isoformat(),
        "type": "text"
    })
    save_data(data)

    await update.message.reply_text(reply)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    user["last_active"] = datetime.now().isoformat()

    msg = update.message
    file_obj = None
    media_type = "file"
    caption = msg.caption or ""

    if msg.photo:
        file_obj = msg.photo[-1]
        media_type = "foto"
        ext = "jpg"
    elif msg.video:
        file_obj = msg.video
        media_type = "video"
        ext = "mp4"
    elif msg.voice:
        file_obj = msg.voice
        media_type = "voice_note"
        ext = "ogg"
    elif msg.audio:
        file_obj = msg.audio
        media_type = "audio"
        ext = msg.audio.mime_type.split("/")[-1] if msg.audio.mime_type else "mp3"
    elif msg.document:
        file_obj = msg.document
        media_type = "dokumen"
        ext = msg.document.file_name.split(".")[-1] if msg.document.file_name else "bin"

    media_info = {"type": "media", "media_type": media_type, "caption": caption}

    if file_obj:
        try:
            tg_file = await context.bot.get_file(file_obj.file_id)
            fname = f"{update.effective_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            fpath = MEDIA_DIR / fname
            await tg_file.download_to_drive(fpath)
            media_info["filename"] = fname
        except Exception as e:
            logger.error(f"Download media error: {e}")

    user["history"].append({
        "role": "user",
        "content": f"[{media_type.upper()}] {caption}",
        "timestamp": datetime.now().isoformat(),
        **media_info
    })

    # Teruskan ke admin
    notif = f"📎 {media_type.upper()} dari {user['name']} (@{user['username']})"
    if caption:
        notif += f"\nCaption: {caption}"

    if ADMIN_CHAT_ID:
        try:
            await context.bot.forward_message(ADMIN_CHAT_ID, msg.chat_id, msg.message_id)
            await context.bot.send_message(ADMIN_CHAT_ID, notif)
        except Exception as e:
            logger.error(f"Forward media error: {e}")

    await msg.reply_text("Udah saya terima ya Kak 🙏 Kalau ada yang mau diceritain, langsung aja.")
    save_data(data)

async def notify_admin(context, tg_user, text, icon="💬"):
    if not ADMIN_CHAT_ID:
        return
    notif = (
        f"{icon} Pesan dari: {tg_user.full_name} (@{tg_user.username or '-'})\n"
        f"ID: {tg_user.id}\n"
        f"Pesan: {text[:200]}"
    )
    keyboard = [[
        InlineKeyboardButton("💬 Balas Manual", callback_data=f"manual_{tg_user.id}"),
        InlineKeyboardButton("🤖 AI ON/OFF", callback_data=f"toggle_{tg_user.id}")
    ]]
    try:
        await context.bot.send_message(
            ADMIN_CHAT_ID, notif,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Notify admin error: {e}")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

if str(query.from_user.id) != str(ADMIN_CHAT_ID):
        return

    action, uid = query.data.rsplit("_", 1)
    data = load_data()

    if uid not in data:
        await query.edit_message_text(query.message.text + "\n\n⚠️ User tidak ditemukan.")
        return

    user = data[uid]

    if action == "toggle":
        user["ai_mode"] = not user["ai_mode"]
        status = "🤖 AI ON" if user["ai_mode"] else "👤 Mode Manual (kamu yang jawab)"
        save_data(data)
        await query.edit_message_text(
            query.message.text + f"\n\n✅ Diubah ke: {status}"
        )
    elif action == "manual":
        context.user_data["reply_to"] = uid
        await query.message.reply_text(
            f"Ketik balasan untuk {user['name']} (ID: {uid}).\n"
            "Format: /kirim <pesan>\n"
            "Contoh: /kirim Halo kak, aku Rani nih 😊"
        )

async def kirim_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        return

    args = context.args
    if not args:
        await update.message.reply_text("Format: /kirim <user_id> <pesan>\nContoh: /kirim 123456 Halo kak!")
        return

    # Format: /kirim USER_ID pesan
    try:
        target_id = int(args[0])
        pesan = " ".join(args[1:])
    except (ValueError, IndexError):
        await update.message.reply_text("Format salah. Gunakan: /kirim <user_id> <pesan>")
        return

    data = load_data()
    uid = str(target_id)
    if uid not in data:
        await update.message.reply_text("User tidak ditemukan.")
        return

    data[uid]["history"].append({
        "role": "assistant",
        "content": pesan,
        "timestamp": datetime.now().isoformat(),
        "type": "text",
        "manual": True
    })
    save_data(data)

    try:
        await context.bot.send_message(target_id, pesan)
        await update.message.reply_text(f"✅ Pesan terkirim ke {data[uid]['name']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal kirim: {e}")

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        return

    data = load_data()
    if not data:
        await update.message.reply_text("Belum ada user.")
        return

    lines = ["📋 Daftar User:\n"]
    for uid, u in data.items():
        mode = "🤖" if u.get("ai_mode", True) else "👤"
        persona = u.get("persona", "-") or "-"
        lines.append(f"{mode} {u['name']} (@{u.get('username','-')}) | ID: {uid} | Persona: {persona} | Pesan: {len(u.get('history', []))}")

    await update.message.reply_text("\n".join(lines))

# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ganti", ganti_persona))
    app.add_handler(CommandHandler("kirim", kirim_manual))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CallbackQueryHandler(persona_callback, pattern="^persona_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(toggle|manual)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO | filters.Document.ALL,
        handle_media
    ))

    logger.info("Bot Pasutri starting...")
    app.run_polling()

if name == "main":
    main()

#  DATABASE
# ════════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            username        TEXT,
            first_name      TEXT,
            role            TEXT NOT NULL,
            msg_type        TEXT DEFAULT 'text',
            content         TEXT,
            media_path      TEXT,
            telegram_msg_id INTEGER,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id     INTEGER PRIMARY KEY,
            ai_enabled  INTEGER DEFAULT 1,
            persona     TEXT DEFAULT 'berdua'
        )
    """)
    conn.commit()
    conn.close()

def db():
    return sqlite3.connect(DB_PATH)

def save_message(user_id, username, first_name, role, msg_type, content, media_path=None, tg_msg_id=None):
    with db() as conn:
        conn.execute(
            "INSERT INTO messages (user_id,username,first_name,role,msg_type,content,media_path,telegram_msg_id) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, username, first_name, role, msg_type, content, media_path, tg_msg_id)
        )

def get_history(user_id):
    with db() as conn:
        rows = conn.execute(
            "SELECT role, msg_type, content FROM messages WHERE user_id=? AND role != 'system' ORDER BY id DESC LIMIT ?",
            (user_id, MAX_HISTORY)
        ).fetchall()
    history = []
    for role, msg_type, content in reversed(rows):
        ai_role = "user" if role == "user" else "assistant"
        text = content or f"[{msg_type}]"
        history.append({"role": ai_role, "content": text})
    return history

def get_settings(user_id):
    with db() as conn:
        row = conn.execute("SELECT ai_enabled, persona FROM settings WHERE user_id=?", (user_id,)).fetchone()
    if row:
        return {"ai_enabled": bool(row[0]), "persona": row[1]}
    return {"ai_enabled": True, "persona": None}  # None = belum pilih

def update_settings(user_id, **kwargs):
    with db() as conn:
        existing = conn.execute("SELECT user_id FROM settings WHERE user_id=?", (user_id,)).fetchone()
        if existing:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            conn.execute(f"UPDATE settings SET {sets} WHERE user_id=?", (*kwargs.values(), user_id))
        else:
            conn.execute("INSERT INTO settings (user_id, ai_enabled, persona) VALUES (?, 1, NULL)", (user_id,))
            if kwargs:
                sets = ", ".join(f"{k}=?" for k in kwargs)
                conn.execute(f"UPDATE settings SET {sets} WHERE user_id=?", (*kwargs.values(), user_id))

def is_new_user(user_id):
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)).fetchone()
    return row[0] == 0

def get_all_users():
    with db() as conn:
        return conn.execute("""
            SELECT m.user_id, m.username, m.first_name,
                   COUNT(*) as msg_count, MAX(m.timestamp) as last_active,
                   COALESCE(s.ai_enabled, 1) as ai_enabled,
                   COALESCE(s.persona, 'berdua') as persona
            FROM messages m
            LEFT JOIN settings s ON m.user_id = s.user_id
            WHERE m.role = 'user'
            GROUP BY m.user_id ORDER BY last_active DESC
        """).fetchall()

# ════════════════════════════════════════════════════════════════
#  AI
# ════════════════════════════════════════════════════════════════
async def get_ai_reply(user_id, text):
    cfg = get_settings(user_id)
    persona_key = cfg["persona"] or "berdua"
    system_prompt = PERSONAS[persona_key]

history = get_history(user_id)
    if not history or history[-1]["role"] != "user":
        history.append({"role": "user", "content": text})
    try:
        response = ai_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=history,
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "Maaf, ada gangguan teknis sebentar. Coba lagi ya 🙏"

# ════════════════════════════════════════════════════════════════
#  KEYBOARD PILIHAN PERSONA
# ════════════════════════════════════════════════════════════════
def persona_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👨 Curhat dengan Kang Arif", callback_data="persona:arif")],
        [InlineKeyboardButton("👩 Curhat dengan Teh Rani", callback_data="persona:rani")],
        [InlineKeyboardButton("👫 Curhat dengan Keduanya", callback_data="persona:berdua")],
    ])

# ════════════════════════════════════════════════════════════════
#  NOTIF ADMIN
# ════════════════════════════════════════════════════════════════
async def notify_admin(app, user_id, first_name, username, msg_type, content, media_path=None):
    if not ADMIN_CHAT_ID:
        return
    cfg = get_settings(user_id)
    uname = f"@{username}" if username else "tanpa username"
    persona_label = PERSONA_LABELS.get(cfg.get("persona") or "berdua", "?")
    header = (
        f"💬 *{first_name}* ({uname})\n"
        f"ID: {user_id} · Persona: {persona_label}\n"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✍️ Balas", callback_data=f"reply:{user_id}:{first_name}"),
        InlineKeyboardButton("🤖 AI OFF" if cfg["ai_enabled"] else "🤖 AI ON", callback_data=f"toggle:{user_id}"),
    ]])
    try:
        if msg_type == "text":
            await app.bot.send_message(ADMIN_CHAT_ID, header + f"\n_{content}_", parse_mode="Markdown", reply_markup=kb)
        elif msg_type == "photo" and media_path:
            await app.bot.send_photo(ADMIN_CHAT_ID, open(media_path,"rb"), caption=header+(content or ""), parse_mode="Markdown", reply_markup=kb)
        elif msg_type == "video" and media_path:
            await app.bot.send_video(ADMIN_CHAT_ID, open(media_path,"rb"), caption=header+(content or ""), parse_mode="Markdown", reply_markup=kb)
        elif msg_type in ("voice","audio") and media_path:
            await app.bot.send_audio(ADMIN_CHAT_ID, open(media_path,"rb"), caption=header+(content or ""), parse_mode="Markdown", reply_markup=kb)
        else:
            await app.bot.send_message(ADMIN_CHAT_ID, header+f"\n[{msg_type}]", parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        logger.error(f"Notif admin gagal: {e}")

# ════════════════════════════════════════════════════════════════
#  DOWNLOAD MEDIA
# ════════════════════════════════════════════════════════════════
async def download_media(bot, file_id, subfolder, filename):
    folder = MEDIA_PATH / subfolder
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    f = await bot.get_file(file_id)
    await f.download_to_drive(str(path))
    return str(path)

# ════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    nama = user.first_name or "Kak"

    sambutan = (
        f"Halo, *{nama}*! 👋\n\n"
        "Selamat datang di *Ruang Curhat Pasutri* 💑\n\n"
        "Di sini ada dua sahabat yang siap menemanimu ngobrol — "
        "*Kang Arif* dan *Teh Rani*. Pasangan Sunda dari Bandung yang "
        "sudah 20 tahun mengarungi pernikahan — dengan segala suka, duka, "

"dan pelajaran berharga yang pernah mereka lewati bersama.\n\n"
        "Kamu bisa cerita apa saja: soal pasangan, ekonomi, anak, mertua, "
        "keintiman, atau perasaan yang susah diungkapkan. "
        "Tidak ada yang akan menghakimi kamu di sini. 🤝\n\n"
        "*Mau ngobrol dengan siapa hari ini?*"
    )
    await update.message.reply_text(sambutan, parse_mode="Markdown", reply_markup=persona_keyboard())

async def cmd_ganti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Mau ganti teman ngobrol? Pilih ya 👇",
        reply_markup=persona_keyboard()
    )

async def cmd_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 *Menu*\n\n"
        "/start — Mulai & pilih teman curhat\n"
        "/ganti — Ganti persona (Arif / Rani / Berdua)\n"
        "/ulang — Reset sesi percakapan\n"
        "/tips — Tips komunikasi pasutri\n"
        "/bantuan — Menu ini\n\n"
        "Atau langsung ceritakan apa yang ada di hati kamu 💙",
        parse_mode="Markdown"
    )

async def cmd_ulang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_message(user.id, user.username, user.first_name, "user", "text", "[Memulai sesi baru]")
    cfg = get_settings(user.id)
    persona_key = cfg["persona"] or "berdua"
    label = PERSONA_LABELS[persona_key]
    await update.message.reply_text(
        f"✨ Oke, kita mulai segar ya!\n\nKamu masih ngobrol dengan *{label}*. "
        f"Ceritakan apa yang ada di hatimu sekarang 🌸",
        parse_mode="Markdown"
    )

async def cmd_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 *Tips Komunikasi Pasutri*\n\n"
        "1️⃣ *Dengarkan dulu, baru bicara*\n"
        "2️⃣ *Gunakan 'Aku merasa...' bukan 'Kamu selalu...'*\n"
        "3️⃣ *Pilih waktu yang tepat untuk diskusi berat*\n"
        "4️⃣ *Fokus selesaikan masalah, bukan cari siapa yang salah*\n"
        "5️⃣ *Apresiasi hal-hal kecil setiap hari*\n"
        "6️⃣ *Jaga keintiman — bukan hanya seks, tapi sentuhan & kata-kata*\n"
        "7️⃣ *Quality time tanpa gadget, sesederhana apapun*\n\n"
        "_Pernikahan bukan soal menemukan orang yang sempurna,_\n"
        "_tapi soal terus memilih satu sama lain_ 💑",
        parse_mode="Markdown"
    )

# ════════════════════════════════════════════════════════════════
#  MESSAGE HANDLERS
# ════════════════════════════════════════════════════════════════
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    cfg = get_settings(user.id)

    # Belum pilih persona → minta pilih dulu
    if cfg["persona"] is None:
        await update.message.reply_text(
            "Sebelum mulai, pilih dulu mau ngobrol dengan siapa ya 👇",
            reply_markup=persona_keyboard()
        )
        return

    save_message(user.id, user.username, user.first_name, "user", "text", text, tg_msg_id=update.message.message_id)
    await notify_admin(context.application, user.id, user.first_name, user.username, "text", text)

    if cfg["ai_enabled"]:
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        reply = await get_ai_reply(user.id, text)
        await update.message.reply_text(reply)
        save_message(user.id, user.username, user.first_name, "bot_ai", "text", reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cfg = get_settings(user.id)
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = await download_media(context.bot, photo.file_id, "photos", f"{user.id}_{ts}.jpg")

save_message(user.id, user.username, user.first_name, "user", "photo", caption, media_path=path)
    await notify_admin(context.application, user.id, user.first_name, user.username, "photo", caption, path)
    if cfg["ai_enabled"] and cfg["persona"]:
        prompt = "User mengirim foto" + (f" dengan keterangan: {caption}" if caption else "")
        reply = await get_ai_reply(user.id, prompt)
        await update.message.reply_text(reply)
        save_message(user.id, user.username, user.first_name, "bot_ai", "text", reply)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cfg = get_settings(user.id)
    video = update.message.video
    caption = update.message.caption or ""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = await download_media(context.bot, video.file_id, "videos", f"{user.id}_{ts}.mp4")
    save_message(user.id, user.username, user.first_name, "user", "video", caption, media_path=path)
    await notify_admin(context.application, user.id, user.first_name, user.username, "video", caption, path)
    if cfg["ai_enabled"] and cfg["persona"]:
        prompt = "User mengirim video" + (f" dengan keterangan: {caption}" if caption else "")
        reply = await get_ai_reply(user.id, prompt)
        await update.message.reply_text(reply)
        save_message(user.id, user.username, user.first_name, "bot_ai", "text", reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cfg = get_settings(user.id)
    voice = update.message.voice
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = await download_media(context.bot, voice.file_id, "voices", f"{user.id}_{ts}.ogg")
    save_message(user.id, user.username, user.first_name, "user", "voice", "[Voice Note]", media_path=path)
    await notify_admin(context.application, user.id, user.first_name, user.username, "voice", "[Voice Note]", path)
    if cfg["ai_enabled"] and cfg["persona"]:
        reply = await get_ai_reply(user.id, "User mengirim pesan suara")
        await update.message.reply_text(reply)
        save_message(user.id, user.username, user.first_name, "bot_ai", "text", reply)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cfg = get_settings(user.id)
    audio = update.message.audio
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = await download_media(context.bot, audio.file_id, "audios", f"{user.id}_{ts}.mp3")
    save_message(user.id, user.username, user.first_name, "user", "audio", audio.file_name or "[Audio]", media_path=path)
    await notify_admin(context.application, user.id, user.first_name, user.username, "audio", audio.file_name or "[Audio]", path)
    if cfg["ai_enabled"] and cfg["persona"]:
        reply = await get_ai_reply(user.id, "User mengirim file audio")
        await update.message.reply_text(reply)
        save_message(user.id, user.username, user.first_name, "bot_ai", "text", reply)

# ════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER (tombol inline)
# ════════════════════════════════════════════════════════════════
pending_reply: dict[int, int] = {}

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Pilih persona ──
    if data.startswith("persona:"):
        _, key = data.split(":", 1)
        user = query.from_user
        update_settings(user.id, persona=key)
        label = PERSONA_LABELS[key]

        if key == "arif":
            intro = (
                f"*Halo! Kang Arif di sini.* 👋\n\n"
                f"Senang bisa menemani kamu ngobrol. "
                f"Saya Arif, 48 tahun, dari Bandung. Sudah 20 tahun menikah dengan Rani — "

f"dan percayalah, kami sudah melewati hampir semua fase yang mungkin ada dalam pernikahan. "
                f"Yang indah, yang berat, bahkan yang hampir menghancurkan kami.\n\n"
                f"Ceritakan apa yang lagi kamu rasakan. Tidak ada yang akan dihakimi di sini. 🤝"
            )
        elif key == "rani":
            intro = (
                f"*Halo! Teh Rani di sini.* 👋\n\n"
                f"Alhamdulillah kamu mau cerita. "
                f"Saya Rani, 42 tahun, dari Bandung. Sudah 20 tahun bersama Arif — "
                f"dan saya tahu betul rasanya ketika pernikahan terasa berat, sepi, atau membingungkan. "
                f"Pernah saya menangis diam-diam di dapur karena merasa tidak didengar. "
                f"Tapi saya juga tahu, ada jalan keluarnya.\n\n"
                f"Yuk cerita, Teh Rani dengerin 💙"
            )
        else:
            intro = (
                f"*Halo dari Arif & Rani!* 👫\n\n"
                f"Kami senang kamu memilih ngobrol dengan kami berdua. "
                f"Dengan begini, kamu bisa mendapat sudut pandang dari sisi suami sekaligus istri — "
                f"karena kami percaya, hampir semua masalah pernikahan punya dua sisi yang sama-sama perlu didengar.\n\n"
                f"Ceritakan apa yang ada di hatimu. Kami di sini 💑"
            )

        save_message(user.id, user.username, user.first_name, "bot_ai", "text", intro)
        await query.message.reply_text(intro, parse_mode="Markdown")

    # ── Toggle AI ──
    elif data.startswith("toggle:"):
        _, user_id = data.split(":", 1)
        user_id = int(user_id)
        cfg = get_settings(user_id)
        new_state = not cfg["ai_enabled"]
        update_settings(user_id, ai_enabled=1 if new_state else 0)
        status = "ON 🤖" if new_state else "OFF ✋ (mode manual)"
        await query.message.reply_text(f"AI untuk user {user_id} sekarang *{status}*", parse_mode="Markdown")

    # ── Balas manual ──
    elif data.startswith("reply:"):
        _, user_id, first_name = data.split(":", 2)
        pending_reply[query.from_user.id] = int(user_id)
        await query.message.reply_text(
            f"✍️ Ketik balasanmu untuk *{first_name}* ({user_id}).\n"
            f"Pesan berikutnya langsung dikirim ke mereka.\n"
            f"Ketik /batal untuk batalkan.",
            parse_mode="Markdown"
        )

# ════════════════════════════════════════════════════════════════
#  ADMIN REPLY MANUAL
# ════════════════════════════════════════════════════════════════
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id != ADMIN_CHAT_ID:
        return
    if admin_id not in pending_reply:
        return

    target_user_id = pending_reply.pop(admin_id)
    text = update.message.text

    if text == "/batal":
        await update.message.reply_text("❌ Dibatalkan.")
        return

    try:
        await context.bot.send_message(target_user_id, text)
        save_message(target_user_id, None, "Admin", "bot_admin", "text", text)
        await update.message.reply_text(f"✅ Terkirim ke {target_user_id}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {e}")

# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ganti", cmd_ganti))
    app.add_handler(CommandHandler("bantuan", cmd_bantuan))
    app.add_handler(CommandHandler("ulang", cmd_ulang))
    app.add_handler(CommandHandler("tips", cmd_tips))
    app.add_handler(CallbackQueryHandler(callback_handler))

    if ADMIN_CHAT_ID:
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(ADMIN_CHAT_ID),
            handle_admin_reply
        ))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio))

    logger.info("Bot Pasutri Pro berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if name == "main":
    main()
