import os
from pathlib import Path
from datetime import date as date_type, datetime, timezone
from dotenv import load_dotenv
import httpx

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand, BotCommandScopeChat,
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
    ConversationHandler, CallbackQueryHandler
)

# Load .env from the project root (two levels up from this file)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_BASE = (os.getenv("SCHOOLGUARD_API_URL") or "http://localhost:8000").rstrip("/")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ─── Per-language bot command menus ─────────────────────────────────────────
BOT_COMMANDS = {
    "en": [
        BotCommand("start",    "Open main menu & dashboard"),
        BotCommand("link",     "Link your SchoolGuard account"),
        BotCommand("children", "View your linked children"),
        BotCommand("status",   "View today's attendance status"),
        BotCommand("language", "Change language / ቋንቋ ቀይር"),
        BotCommand("help",     "Get help & instructions"),
    ],
    "am": [
        BotCommand("start",    "ዋናውን ምናሌ ክፈቱ"),
        BotCommand("link",     "የ SchoolGuard መለያዎን ያስተሳስሩ"),
        BotCommand("children", "ልጆቻቸውን ይመልከቱ"),
        BotCommand("status",   "የዛሬ የመገኘት ሁኔታ ይመልከቱ"),
        BotCommand("language", "ቋንቋ ቀይሩ / Change language"),
        BotCommand("help",     "እርዳታ ያግኙ"),
    ],
}

ASK_LANGUAGE, ASK_PHONE, ASK_PASSWORD = range(3)
SESSION_TIMEOUT_MINUTES = 15
CONVERSATION_TIMEOUT_SECONDS = SESSION_TIMEOUT_MINUTES * 60

# ─── Bilingual Strings ────────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "btn_children":   "👶 My Children",
        "btn_status":     "📊 Today's Status",
        "btn_link":       "🔗 Link My Account",
        "btn_help":       "ℹ️ Help",
        "btn_language":   "🌐 Language",
        "btn_english":    "🇬🇧 English",
        "btn_amharic":    "🇪🇹 አማርኛ",
        "btn_share_phone":"📱 Share My Phone Number",
        "btn_cancel":     "❌ Cancel",
        "select_language": (
            "🌐 *Please select your language:*\n\n"
            "Please choose your preferred language:"
        ),
        "language_set": "✅ Language set to *English*.",
        "session_expired": (
            "⏳ *Session Expired*\n\n"
            "Your session has expired due to {minutes} minutes of inactivity.\n"
            "Please tap a menu button to continue."
        ),
        "welcome_linked": (
            "🛡️ *SchoolGuard Dashboard*\n\n"
            "Hello *{name}*! 👋\n"
            "Your Telegram account is connected to SchoolGuard.\n\n"
            "You will receive automatic alerts for morning arrivals and afternoon departures.\n\n"
            "Use the buttons below to check attendance or view your linked students."
        ),
        "welcome_new": (
            "🛡️ *Welcome to SchoolGuard Assistant*\n\n"
            "Receive instant real-time gate notifications when your child arrives or departs from school.\n\n"
            "👇 *Getting Started:*\n"
            "Tap *🔗 Link My Account* below or send /link to connect your parent account."
        ),
        "not_linked": (
            "⚠️ *Account Not Linked*\n\n"
            "Your Telegram account is not linked to SchoolGuard yet.\n"
            "Tap *🔗 Link My Account* below or send /link to connect."
        ),
        "already_linked": (
            "ℹ️ *Already Connected!*\n\n"
            "Your Telegram account is already linked to *{name}* ({ident}).\n\n"
            "To re-link to a different account, tap *📱 Share My Phone Number* or type your phone number (or send /cancel):"
        ),
        "ask_phone": (
            "🔗 *Link Your SchoolGuard Account*\n\n"
            "Please tap *📱 Share My Phone Number* below or type your registered phone number "
            "(e.g. `0911223344` or `+251911223344`):\n\n_(or type /cancel to abort)_"
        ),
        "phone_received": (
            "📱 Account identifier received: `{phone}`\n\n"
            "🔑 Now enter your SchoolGuard *password*:\n_(or type /cancel or /start to abort)_"
        ),
        "invalid_phone": (
            "⚠️ Please enter a valid registered phone number (e.g. `0911223344` or `+251911223344`) "
            "or tap *📱 Share My Phone Number* below.\n\n_(or tap ❌ Cancel or /start to exit)_"
        ),
        "link_success": (
            "✅ *Account Linked Successfully!*\n\n"
            "Welcome, *{name}*! 🎉\n"
            "Your Telegram is now connected to SchoolGuard. "
            "You will automatically receive push notifications for your children's gate arrivals and departures."
        ),
        "link_failed_auth": (
            "❌ *Authentication Failed:*\n{detail}\n\n"
            "Please make sure your phone number was entered correctly, "
            "and try again by tapping *🔗 Link My Account* or sending /link."
        ),
        "link_failed_other": "❌ Could not link account: {detail}",
        "server_error": "⚠️ Cannot reach the SchoolGuard server. Please make sure the backend server is running.",
        "cancelled": "Action cancelled.",
        "no_children": (
            "👤 *Parent Account:* {name}\n\n"
            "No students are currently linked to your profile.\n"
            "Please contact your school administrator to link your student(s)."
        ),
        "children_header": "👶 *Linked Students for {name}:*\n",
        "no_attendance": "👤 *Parent Account:* {name}\n\nNo student records are linked to your profile.",
        "attendance_header": "📊 *Attendance Status — {date}*\n",
        "not_recorded_yet": "   Status: ⏳ *Not recorded yet*\n",
        "not_departed": "Not departed",
        "not_arrived": "Not recorded",
        "link_timeout": "⏳ Account linking session timed out. Tap *🔗 Link My Account* or send /link to try again.",
        "help_text": (
            "ℹ️ *SchoolGuard Bot Instructions*\n\n"
            "• *🔗 /link* — Connect your parent account using phone & password\n"
            "• *👶 /children* — View your linked children and classes\n"
            "• *📊 /status* — Check today's arrival and departure status\n"
            "• *🛡️ /start* — Reopen the main interactive keyboard menu\n"
            "• *🌐 /language* — Change your language preference\n"
            "• *❌ /cancel* — Cancel the current operation\n\n"
            "For assistance or account setup, please reach out to your school office."
        ),
        "unknown": "Please select an option from the menu buttons below, or send /help for instructions.",
    },
    "am": {
        "btn_children":   "👶 ልጆቼ",
        "btn_status":     "📊 የዛሬ ሁኔታ",
        "btn_link":       "🔗 መለያዬን አስተሳሰር",
        "btn_help":       "ℹ️ እርዳታ",
        "btn_language":   "🌐 ቋንቋ",
        "btn_english":    "🇬🇧 English",
        "btn_amharic":    "🇪🇹 አማርኛ",
        "btn_share_phone":"📱 ስልክ ቁጥሬን አጋራ",
        "btn_cancel":     "❌ ሰርዝ",
        "select_language": (
            "🌐 *ቋንቋ ይምረጡ:*\n\n"
            "እባክዎ የሚፈልጉትን ቋንቋ ይምረጡ:"
        ),
        "language_set": "✅ ቋንቋው አማርኛ ሆኗል።",
        "session_expired": (
            "⏳ *ክፍለ ጊዜ ጊዜው አልፏል*\n\n"
            "ለ {minutes} ደቂቃ ምንም እንቅስቃሴ ስለሌለ ክፍለ ጊዜዎ ጊዜው አልፏል።\n"
            "እባክዎ ለመቀጠል ከምናሌ ቁልፍ ይምረጡ።"
        ),
        "welcome_linked": (
            "🛡️ *የ SchoolGuard ዳሽቦርድ*\n\n"
            "ሰላም *{name}*! 👋\n"
            "የቴሌግራም መለያዎ ከ SchoolGuard ጋር ተሳስሯል።\n\n"
            "ልጅዎ ሲደርስ ወይም ሲወጣ ራስ-ሰር ማሳወቂያ ይደርስዎታል።\n\n"
            "ዛሬን ሁኔታ ለማየት ከዚህ በታች ያሉ ቁልፎችን ይጠቀሙ።"
        ),
        "welcome_new": (
            "🛡️ *እንኳን ወደ SchoolGuard ደህና መጡ*\n\n"
            "ልጅዎ ወደ ትምህርት ቤት ሲደርስ ወይም ሲወጣ ወዲያውኑ ማሳወቂያ ይቀበሉ።\n\n"
            "👇 *ለመጀመር:*\n"
            "ታቹ *🔗 መለያዬን አስተሳሰር* ይጫኑ ወይም /link ይላኩ።"
        ),
        "not_linked": (
            "⚠️ *መለያ አልተሳሰረም*\n\n"
            "የቴሌግራም መለያዎ ከ SchoolGuard ጋር ገና አልተሳሰረም።\n"
            "*🔗 መለያዬን አስተሳሰር* ይጫኑ ወይም /link ያስገቡ።"
        ),
        "already_linked": (
            "ℹ️ *አስቀድሞ ተሳስሯል!*\n\n"
            "የቴሌግራም መለያዎ ቀድሞ ከ *{name}* ({ident}) ጋር ተሳስሯል።\n\n"
            "ወደ ሌላ መለያ ለመሳሰር *📱 ስልክ ቁጥሬን አጋራ* ይጫኑ (ወይም /cancel ይላኩ):"
        ),
        "ask_phone": (
            "🔗 *የ SchoolGuard መለያዎን ያስተሳስሩ*\n\n"
            "*📱 ስልክ ቁጥሬን አጋራ* ይጫኑ ወይም "
            "የተመዘገቡበት ስልክ ቁጥር ያስገቡ "
            "(ምሳ: `0911223344` ወይም `+251911223344`):\n\n_(ለመሰረዝ /cancel ያስገቡ)_"
        ),
        "phone_received": (
            "📱 መለያ ቁጥር ደርሷል: `{phone}`\n\n"
            "🔑 አሁን የ SchoolGuard *ይለፍ ቃልዎን* ያስገቡ:\n_(ለመሰረዝ /cancel ወይም /start ያስገቡ)_"
        ),
        "invalid_phone": (
            "⚠️ እባክዎ ትክክለኛ ስልክ ቁጥር ያስገቡ (ምሳ: `0911223344`) "
            "ወይም *📱 ስልክ ቁጥሬን አጋራ* ይጫኑ።\n\n_(ወይም ❌ ሰርዝ ወይም /start ይጫኑ)_"
        ),
        "link_success": (
            "✅ *መለያ በተሳካ ሁኔታ ተሳስሯል!*\n\n"
            "እንኳን ደህና መጡ, *{name}*! 🎉\n"
            "ልጆቻቸው ሲደርሱ ወይም ሲወጡ ራስ-ሰር ማሳወቂያ ይደርስዎታል።"
        ),
        "link_failed_auth": (
            "❌ *ማረጋገጫ አልተሳካም:*\n{detail}\n\n"
            "ስልክ ቁጥርዎ ትክክል መሆኑን ያረጋግጡ፣ "
            "*🔗 መለያዬን አስተሳሰር* ይጫኑ ወይም /link ያስገቡ።"
        ),
        "link_failed_other": "❌ መለያ ሊሳሰር አልቻለም: {detail}",
        "server_error": "⚠️ የ SchoolGuard አገልጋይ ሊደረስ አልቻለም። አገልጋዩ እየሄደ መሆኑን ያረጋግጡ።",
        "cancelled": "ድርጊቱ ተሰርዟል።",
        "no_children": (
            "👤 *የወላጅ መለያ:* {name}\n\n"
            "አሁን ምንም ተማሪ ከፕሮፋይልዎ ጋር አልተሳሰረም።\n"
            "ተማሪዎን ለማሳሰር የትምህርት ቤቱን አስተዳዳሪ ያነጋግሩ።"
        ),
        "children_header": "👶 *{name} የተሳሰሩ ተማሪዎች:*\n",
        "no_attendance": "👤 *የወላጅ መለያ:* {name}\n\nምንም የተማሪ መዝገብ ከፕሮፋይልዎ ጋር አልተሳሰረም።",
        "attendance_header": "📊 *የዛሬ የመገኘት ሁኔታ — {date}*\n",
        "not_recorded_yet": "   ሁኔታ: ⏳ *ገና አልተመዘገበም*\n",
        "not_departed": "ገና አልወጣም",
        "not_arrived": "አልተመዘገበም",
        "link_timeout": "⏳ የመለያ ማስተሳሰር ክፍለ ጊዜ ጊዜው አልፏል። *🔗 መለያዬን አስተሳሰር* ይጫኑ ወይም /link ያስገቡ።",
        "help_text": (
            "ℹ️ *የ SchoolGuard ቦት መመሪያ*\n\n"
            "• *🔗 /link* — ስልክ ቁጥርና ይለፍ ቃል በመጠቀም የወላጅ መለያ ያስተሳስሩ\n"
            "• *👶 /children* — የተሳሰሩ ልጆቻቸውን እና ክፍሎቻቸውን ይመልከቱ\n"
            "• *📊 /status* — የዛሬ የምጫ እና የወጪ ሁኔታ ይመልከቱ\n"
            "• *🛡️ /start* — ዋናውን ምናሌ ዳግም ክፈቱ\n"
            "• *🌐 /language* — ቋንቋ ቀይሩ\n"
            "• *❌ /cancel* — አሁን ያለውን ተግባር ሰርዙ\n\n"
            "ለእርዳታ ወይም የመለያ ማዋቀሪያ፣ ከትምህርት ቤቱ ቢሮ ጋር ያነጋግሩ።"
        ),
        "unknown": "እባክዎ ከምናሌ ቁልፎቹ ይምረጡ፣ ወይም /help ይላኩ።",
    }
}


# ─── Core Helpers ─────────────────────────────────────────────────────────────

def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")


def tr(context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    lang = get_lang(context)
    text = STRINGS[lang].get(key, STRINGS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def get_main_menu(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    lang = get_lang(context)
    s = STRINGS[lang]
    return ReplyKeyboardMarkup(
        [[s["btn_children"], s["btn_status"]],
         [s["btn_link"],     s["btn_help"]],
         [s["btn_language"]]],
        resize_keyboard=True
    )


def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(STRINGS["en"]["btn_english"], callback_data="lang_en"),
            InlineKeyboardButton(STRINGS["en"]["btn_amharic"], callback_data="lang_am"),
        ]
    ])


def touch_activity(context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_activity"] = datetime.now(timezone.utc).timestamp()


def is_session_expired(context: ContextTypes.DEFAULT_TYPE) -> bool:
    last = context.user_data.get("last_activity")
    if last is None:
        return False
    return (datetime.now(timezone.utc).timestamp() - last) > (SESSION_TIMEOUT_MINUTES * 60)


async def handle_session_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if is_session_expired(context):
        lang_key = "lang" in context.user_data and context.user_data["lang"]
        context.user_data.clear()
        if lang_key:
            context.user_data["lang"] = lang_key
        await update.message.reply_text(
            tr(context, "session_expired", minutes=SESSION_TIMEOUT_MINUTES),
            parse_mode="Markdown",
            reply_markup=get_main_menu(context)
        )
        return True
    return False


def _matches_any_lang(text: str, key: str) -> bool:
    t_low = text.strip().lower()
    for s in STRINGS.values():
        if key in s and s[key].strip().lower() == t_low:
            return True
    return False


def _is_cancel(text: str)   -> bool: return _matches_any_lang(text, "btn_cancel")   or text.lower() in {"/cancel", "cancel"}
def _is_start(text: str)    -> bool: return text.lower() in {"/start", "start", "menu", "main menu", "open main menu"}
def _is_children(text: str) -> bool: return _matches_any_lang(text, "btn_children") or text.lower() in {"/children", "children", "my children", "students"}
def _is_status(text: str)   -> bool: return _matches_any_lang(text, "btn_status")   or text.lower() in {"/status", "status", "today's status"}
def _is_help(text: str)     -> bool: return _matches_any_lang(text, "btn_help")     or text.lower() in {"/help", "help", "instructions"}
def _is_link(text: str)     -> bool: return _matches_any_lang(text, "btn_link")     or text.lower() in {"/link", "link my account", "link account"}
def _is_language(text: str) -> bool: return _matches_any_lang(text, "btn_language") or text.lower() in {"/language", "language", "ቋንቋ"}
def _is_lang_choice(text: str) -> bool: return text.strip() in {STRINGS["en"]["btn_english"], STRINGS["en"]["btn_amharic"]}


def get_linked_parent(tg_id: int):
    """Fetch User record if this Telegram user is already linked."""
    try:
        try:
            from backend.app.database import SessionLocal
            from backend.app.models import User
        except ModuleNotFoundError:
            from app.database import SessionLocal
            from app.models import User
        db = SessionLocal()
        try:
            return db.query(User).filter(User.telegram_id == tg_id).first()
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching parent by Telegram ID: {e}")
        return None


def update_user_language(tg_id: int, lang: str):
    """Save user language preference to the database."""
    try:
        try:
            from backend.app.database import SessionLocal
            from backend.app.models import User
        except ModuleNotFoundError:
            from app.database import SessionLocal
            from app.models import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == tg_id).first()
            if user:
                user.language = lang
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Error updating user language in DB: {e}")


def sync_parent_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ensure context.user_data['lang'] matches the parent's persisted DB language if not set."""
    if "lang" not in context.user_data and update and update.effective_user:
        parent = get_linked_parent(update.effective_user.id)
        if parent and getattr(parent, "language", None):
            context.user_data["lang"] = parent.language


def get_parent_children(parent_id: int):
    """Retrieve all linked students for this parent."""
    try:
        try:
            from backend.app.database import SessionLocal
            from backend.app.models import ParentStudent, Student, ClassRoom
        except ModuleNotFoundError:
            from app.database import SessionLocal
            from app.models import ParentStudent, Student, ClassRoom
        db = SessionLocal()
        try:
            links = db.query(ParentStudent).filter(ParentStudent.parent_id == parent_id).all()
            children = []
            for link in links:
                st = db.get(Student, link.student_id)
                if st:
                    cls_name = ""
                    if st.class_id:
                        c = db.get(ClassRoom, st.class_id)
                        cls_name = c.class_name if c else ""
                    children.append({"student": st, "class_name": cls_name, "relationship": link.relationship_type})
            return children
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching children: {e}")
        return []


def get_children_today_attendance(parent_id: int):
    """Retrieve today's attendance logs for all linked students."""
    try:
        try:
            from backend.app.database import SessionLocal
            from backend.app.models import ParentStudent, Student, Attendance
        except ModuleNotFoundError:
            from app.database import SessionLocal
            from app.models import ParentStudent, Student, Attendance
        db = SessionLocal()
        try:
            links = db.query(ParentStudent).filter(ParentStudent.parent_id == parent_id).all()
            results = []
            today = date_type.today()
            for link in links:
                st = db.get(Student, link.student_id)
                if not st:
                    continue
                att = db.query(Attendance).filter(
                    Attendance.student_id == st.id,
                    Attendance.attendance_date == today
                ).first()
                results.append({"student": st, "attendance": att})
            return results
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching attendance: {e}")
        return []


# ─── Language Selection ───────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — show inline language buttons, then main menu."""
    touch_activity(context)
    if "lang" not in context.user_data:
        await update.message.reply_text(
            STRINGS["en"]["select_language"],
            parse_mode="Markdown",
            reply_markup=get_language_inline_keyboard()
        )
        # Do NOT return a conversation state — inline buttons use CallbackQueryHandler
        return ConversationHandler.END
    return await show_main_menu(update, context)


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command — show inline language buttons."""
    touch_activity(context)
    context.user_data.pop("lang", None)
    await update.message.reply_text(
        STRINGS["en"]["select_language"],
        parse_mode="Markdown",
        reply_markup=get_language_inline_keyboard()
    )
    return ConversationHandler.END


async def got_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text-based language selection (fallback for reply keyboard)."""
    touch_activity(context)
    text = (update.message.text or "").strip()
    if text == STRINGS["en"]["btn_amharic"]:
        context.user_data["lang"] = "am"
    else:
        context.user_data["lang"] = "en"

    tg_user = update.effective_user
    if tg_user:
        update_user_language(tg_user.id, context.user_data["lang"])

    await update.message.reply_text(
        tr(context, "language_set"),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return await show_main_menu(update, context)


async def got_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline language button press (callback query)."""
    query = update.callback_query
    await query.answer()
    touch_activity(context)
    lang = "am" if query.data == "lang_am" else "en"
    context.user_data["lang"] = lang

    tg_user = update.effective_user
    if tg_user:
        update_user_language(tg_user.id, lang)

    # Update the Menu button commands for this specific chat
    try:
        await context.bot.set_my_commands(
            BOT_COMMANDS[lang],
            scope=BotCommandScopeChat(chat_id=query.message.chat_id)
        )
    except Exception as e:
        print(f"Could not set per-chat commands: {e}")

    # Edit the message to show confirmation
    await query.edit_message_text(
        tr(context, "language_set"),
        parse_mode="Markdown"
    )
    # Show main menu
    parent = get_linked_parent(tg_user.id) if tg_user else None
    msg = tr(context, "welcome_linked", name=parent.full_name) if parent else tr(context, "welcome_new")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=msg,
        parse_mode="Markdown",
        reply_markup=get_main_menu(context)
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the main menu for the current user."""
    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None
    if parent:
        msg = tr(context, "welcome_linked", name=parent.full_name)
    else:
        msg = tr(context, "welcome_new")
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu(context))
    return ConversationHandler.END


# ─── Link Account Flow ────────────────────────────────────────────────────────

async def link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate account link conversation using phone number."""
    touch_activity(context)
    if await handle_session_expiry(update, context):
        return ConversationHandler.END

    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(tr(context, "btn_share_phone"), request_contact=True)],
         [tr(context, "btn_cancel")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    if parent:
        ident_str = parent.phone or parent.email or ""
        await update.message.reply_text(
            tr(context, "already_linked", name=parent.full_name, ident=ident_str),
            parse_mode="Markdown",
            reply_markup=contact_keyboard
        )
    else:
        await update.message.reply_text(
            tr(context, "ask_phone"),
            parse_mode="Markdown",
            reply_markup=contact_keyboard
        )
    return ASK_PHONE


async def link_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update and update.effective_message:
        await update.effective_message.reply_text(
            tr(context, "link_timeout"),
            parse_mode="Markdown",
            reply_markup=get_main_menu(context)
        )
    return ConversationHandler.END


async def got_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive phone number (contact share or typed)."""
    touch_activity(context)
    if await handle_session_expiry(update, context):
        return ConversationHandler.END

    if update.message.contact:
        phone = update.message.contact.phone_number.strip()
    elif update.message.text:
        text = update.message.text.strip()
        if _is_cancel(text):
            return await cancel(update, context)
        if _is_start(text):
            context.user_data.pop("phone", None)
            return await show_main_menu(update, context)
        if _is_children(text):
            context.user_data.pop("phone", None)
            await children_command(update, context)
            return ConversationHandler.END
        if _is_status(text):
            context.user_data.pop("phone", None)
            await status_command(update, context)
            return ConversationHandler.END
        if _is_help(text):
            context.user_data.pop("phone", None)
            await help_command(update, context)
            return ConversationHandler.END
        if _is_link(text):
            return await link_start(update, context)

        cleaned_digits = "".join(c for c in text if c.isdigit())
        if len(cleaned_digits) < 7 and "@" not in text:
            await update.message.reply_text(
                tr(context, "invalid_phone"),
                parse_mode="Markdown"
            )
            return ASK_PHONE
        phone = text
    else:
        await update.message.reply_text(tr(context, "invalid_phone"), parse_mode="Markdown")
        return ASK_PHONE

    context.user_data["phone"] = phone
    await update.message.reply_text(
        tr(context, "phone_received", phone=phone),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_PASSWORD


async def got_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive password and attempt to authenticate + link."""
    touch_activity(context)
    if await handle_session_expiry(update, context):
        return ConversationHandler.END

    password = (update.message.text or "").strip()
    tg_user = update.effective_user

    if _is_cancel(password):
        return await cancel(update, context)
    if _is_start(password):
        context.user_data.pop("phone", None)
        return await show_main_menu(update, context)
    if _is_children(password):
        context.user_data.pop("phone", None)
        await children_command(update, context)
        return ConversationHandler.END
    if _is_status(password):
        context.user_data.pop("phone", None)
        await status_command(update, context)
        return ConversationHandler.END
    if _is_help(password):
        context.user_data.pop("phone", None)
        await help_command(update, context)
        return ConversationHandler.END
    if _is_link(password):
        return await link_start(update, context)

    phone = context.user_data.get("phone", "")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Login using phone number & password
            login_resp = await client.post(
                f"{API_BASE}/api/auth/login",
                json={"email": phone, "password": password}
            )
            if login_resp.status_code != 200:
                detail = login_resp.json().get("detail", "Invalid phone number or password")
                await update.message.reply_text(
                    tr(context, "link_failed_auth", detail=detail),
                    parse_mode="Markdown",
                    reply_markup=get_main_menu(context)
                )
                context.user_data.clear()
                return ConversationHandler.END

            token = login_resp.json()["access_token"]
            chosen_lang = context.user_data.get("lang", "en")

            # Step 2: Link their Telegram ID
            link_resp = await client.post(
                f"{API_BASE}/api/telegram/link-self",
                json={
                    "telegram_id": tg_user.id,
                    "telegram_username": tg_user.username,
                    "language": chosen_lang
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            if link_resp.status_code == 200:
                update_user_language(tg_user.id, chosen_lang)
                await update.message.reply_text(
                    tr(context, "link_success", name=tg_user.first_name),
                    parse_mode="Markdown",
                    reply_markup=get_main_menu(context)
                )
            else:
                detail = link_resp.json().get("detail", "Unknown error")
                await update.message.reply_text(
                    tr(context, "link_failed_other", detail=detail),
                    reply_markup=get_main_menu(context)
                )

    except httpx.ConnectError:
        await update.message.reply_text(
            tr(context, "server_error"),
            reply_markup=get_main_menu(context)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_main_menu(context))

    saved_lang = context.user_data.get("lang", "en")
    context.user_data.clear()
    context.user_data["lang"] = saved_lang
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_activity(context)
    context.user_data.pop("phone", None)
    await update.message.reply_text(tr(context, "cancelled"), reply_markup=get_main_menu(context))
    return ConversationHandler.END


# ─── Main Menu Commands ───────────────────────────────────────────────────────

async def children_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View linked students."""
    touch_activity(context)
    sync_parent_language(update, context)
    if await handle_session_expiry(update, context):
        return

    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    if not parent:
        await update.message.reply_text(
            tr(context, "not_linked"), parse_mode="Markdown", reply_markup=get_main_menu(context)
        )
        return

    children = get_parent_children(parent.id)
    if not children:
        await update.message.reply_text(
            tr(context, "no_children", name=parent.full_name),
            parse_mode="Markdown",
            reply_markup=get_main_menu(context)
        )
        return

    lang = get_lang(context)
    lines = [tr(context, "children_header", name=parent.full_name)]
    for item in children:
        st = item["student"]
        cls_label = "ክፍል" if lang == "am" else "Class"
        cls_str = f" | {cls_label}: *{item['class_name']}*" if item["class_name"] else ""
        lines.append(f"• 👤 *{st.notification_name}* (Code: `{st.student_code}`){cls_str}")

    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=get_main_menu(context)
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View today's attendance status."""
    touch_activity(context)
    sync_parent_language(update, context)
    if await handle_session_expiry(update, context):
        return

    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    if not parent:
        await update.message.reply_text(
            tr(context, "not_linked"), parse_mode="Markdown", reply_markup=get_main_menu(context)
        )
        return

    records = get_children_today_attendance(parent.id)
    if not records:
        await update.message.reply_text(
            tr(context, "no_attendance", name=parent.full_name),
            parse_mode="Markdown",
            reply_markup=get_main_menu(context)
        )
        return

    lang = get_lang(context)
    status_map = {
        "PRESENT": "ተገኝቷል" if lang == "am" else "PRESENT",
        "LATE": "አርፍዷል" if lang == "am" else "LATE",
        "ABSENT": "አልተገኘም" if lang == "am" else "ABSENT",
        "EXCUSED": "ፈቃድ የተሰጠው" if lang == "am" else "EXCUSED",
    }
    lbl_status = "ሁኔታ" if lang == "am" else "Status"
    lbl_arr = "የተገኘበት/የተገኘችበት ሰዓት" if lang == "am" else "Arrival"
    lbl_dep = "የወጣበት/የወጣችበት ሰዓት" if lang == "am" else "Departure"

    today_str = date_type.today().strftime("%d/%m/%Y")
    lines = [tr(context, "attendance_header", date=today_str)]
    for item in records:
        st = item["student"]
        att = item["attendance"]
        name = st.notification_name
        if not att:
            lines.append(
                f"👶 *{name}* (Code: `{st.student_code}`)\n"
                + tr(context, "not_recorded_yet")
            )
        else:
            status_emoji = (
                "✅" if att.status == "PRESENT"
                else "⚠️" if att.status == "LATE"
                else "❌" if att.status == "ABSENT"
                else "ℹ️"
            )
            arr = att.arrival_time.strftime("%I:%M %p") if att.arrival_time else tr(context, "not_arrived")
            dep = att.departure_time.strftime("%I:%M %p") if att.departure_time else tr(context, "not_departed")
            st_text = status_map.get(att.status, att.status)
            lines.append(
                f"👶 *{name}* (Code: `{st.student_code}`)\n"
                f"   {lbl_status}: {status_emoji} *{st_text}*\n"
                f"   🕒 {lbl_arr}: {arr}\n"
                f"   🕒 {lbl_dep}: {dep}\n"
            )

    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=get_main_menu(context)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_activity(context)
    await update.message.reply_text(
        tr(context, "help_text"), parse_mode="Markdown", reply_markup=get_main_menu(context)
    )


# ─── Unknown / Catch-all Handler ─────────────────────────────────────────────

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all free-text messages to the correct handler."""
    touch_activity(context)
    if await handle_session_expiry(update, context):
        return

    text = (update.message.text or "").strip()

    if _is_lang_choice(text):
        return await got_language(update, context)
    elif _is_language(text):
        return await language_command(update, context)
    elif _is_children(text):
        return await children_command(update, context)
    elif _is_status(text):
        return await status_command(update, context)
    elif _is_help(text):
        return await help_command(update, context)
    elif _is_link(text):
        return await link_start(update, context)
    elif _is_start(text):
        return await show_main_menu(update, context)
    elif _is_cancel(text):
        await update.message.reply_text(tr(context, "cancelled"), reply_markup=get_main_menu(context))
    else:
        await update.message.reply_text(
            tr(context, "unknown"), reply_markup=get_main_menu(context)
        )


# ─── Bot Commands Registration ────────────────────────────────────────────────

async def post_init(application: Application):
    """Registers the bot commands for both English (default) and Amharic."""
    try:
        # Default (English) commands — shown to users whose language isn't overridden
        await application.bot.set_my_commands(BOT_COMMANDS["en"])
        # Amharic commands — shown when Telegram app language is Amharic
        await application.bot.set_my_commands(BOT_COMMANDS["am"], language_code="am")
        print("Telegram bot commands & menu button registered successfully (EN + AM).")
    except Exception as e:
        print(f"Notice: could not set bot commands yet ({e})")


# ─── Main ─────────────────────────────────────────────────────────────────────

def build_bot_app(token: str = None) -> Application:
    tok = token or BOT_TOKEN
    if not tok:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    application = Application.builder().token(tok).request(request).post_init(post_init).build()

    # ── Language selection conversation (triggered by /start or /language) ──
    lang_conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("language", language_command),
        ],
        states={
            ASK_LANGUAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_language),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )

    # ── Link account conversation ──
    link_conv = ConversationHandler(
        entry_points=[
            CommandHandler("link", link_start),
            MessageHandler(
                filters.Regex(r"(?i).*(link\s*my\s*account|link\s*account|link\s*your\s*account|መለያዬን አስተሳሰር).*"),
                link_start
            ),
        ],
        states={
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, got_phone),
                CommandHandler("start", show_main_menu),
                CommandHandler("link", link_start),
                CommandHandler("children", children_command),
                CommandHandler("status", status_command),
                CommandHandler("help", help_command),
                CommandHandler("language", language_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone),
            ],
            ASK_PASSWORD: [
                CommandHandler("start", show_main_menu),
                CommandHandler("link", link_start),
                CommandHandler("children", children_command),
                CommandHandler("status", status_command),
                CommandHandler("help", help_command),
                CommandHandler("language", language_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_password),
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, link_timeout)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", show_main_menu),
            MessageHandler(filters.Regex(r"(?i)^(cancel|❌ cancel|ሰርዝ|❌ ሰርዝ)$"), cancel),
        ],
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )

    application.add_handler(CallbackQueryHandler(got_language_callback, pattern="^lang_(en|am)$"))
    application.add_handler(lang_conv)
    application.add_handler(link_conv)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("children", children_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    return application


async def start_bot_polling(application: Application):
    """Initializes and runs bot polling inside an async loop."""
    print("Telegram Bot: Initializing polling worker in cloud background...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(bootstrap_retries=5)
    print("Telegram Bot: Polling worker successfully running in background.")


async def stop_bot_polling(application: Application):
    """Gracefully shuts down the bot polling."""
    print("Telegram Bot: Shutting down polling worker...")
    try:
        if application.updater and application.updater.running:
            await application.updater.stop()
        if application.running:
            await application.stop()
        await application.shutdown()
        print("Telegram Bot: Shut down cleanly.")
    except Exception as e:
        print(f"Telegram Bot: Error during shutdown: {e}")


def main():
    app = build_bot_app()
    print(f"SchoolGuard Telegram bot running (polling)... API base: {API_BASE}")
    app.run_polling(bootstrap_retries=5)


if __name__ == "__main__":
    main()

