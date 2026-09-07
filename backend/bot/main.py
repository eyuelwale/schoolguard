import os
from pathlib import Path
from datetime import date as date_type
from dotenv import load_dotenv
import httpx

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand, KeyboardButton
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
)

# Load .env from the project root (two levels up from this file)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_BASE = (os.getenv("SCHOOLGUARD_API_URL") or "http://localhost:8000").rstrip("/")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Conversation states
ASK_PHONE, ASK_PASSWORD = range(2)

WELCOME = (
    "🛡️ *Welcome to SchoolGuard Assistant*\n\n"
    "Receive instant real-time gate notifications when your child arrives or departs from school.\n\n"
    "👇 *Getting Started:*\n"
    "Tap *🔗 Link My Account* below or send /link to connect your parent account."
)

MAIN_MENU = ReplyKeyboardMarkup(
    [["👶 My Children", "📊 Today's Status"],
     ["🔗 Link My Account", "ℹ️ Help"]],
    resize_keyboard=True
)


def get_linked_parent(tg_id: int):
    """Fetch User record if this Telegram user is already linked."""
    try:
        from backend.app.database import SessionLocal
        from backend.app.models import User
        db = SessionLocal()
        try:
            return db.query(User).filter(User.telegram_id == tg_id).first()
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching parent by Telegram ID: {e}")
        return None


def get_parent_children(parent_id: int):
    """Retrieve all linked students for this parent."""
    try:
        from backend.app.database import SessionLocal
        from backend.app.models import ParentStudent, Student, ClassRoom
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
        from backend.app.database import SessionLocal
        from backend.app.models import ParentStudent, Student, Attendance
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start or 'Open main menu'."""
    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    if parent:
        msg = (
            f"🛡️ *SchoolGuard Dashboard*\n\n"
            f"Hello *{parent.full_name}*! 👋\n"
            f"Your Telegram account is connected to SchoolGuard.\n\n"
            f"You will receive automatic alerts for morning arrivals and afternoon departures.\n\n"
            f"Use the buttons below to check attendance or view your linked students."
        )
    else:
        msg = WELCOME

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=MAIN_MENU)


#  Link Account flow 
async def link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate account link conversation using phone number."""
    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Share My Phone Number", request_contact=True)],
         ["❌ Cancel"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    if parent:
        ident_str = parent.phone or parent.email or ""
        await update.message.reply_text(
            f"ℹ️ *Already Connected!*\n\n"
            f"Your Telegram account is already linked to *{parent.full_name}* ({ident_str}).\n\n"
            f"If you want to re-link to a different account, tap *📱 Share My Phone Number* below or type your registered *phone number* (or send /cancel):",
            parse_mode="Markdown",
            reply_markup=contact_keyboard
        )
    else:
        await update.message.reply_text(
            "🔗 *Link Your SchoolGuard Account*\n\n"
            "Please tap *📱 Share My Phone Number* below or type your registered *phone number* (e.g. `0911223344` or `+251911223344`):\n\n"
            "_(or type /cancel to abort)_",
            parse_mode="Markdown",
            reply_markup=contact_keyboard
        )
    return ASK_PHONE


async def cancel_and_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await start(update, context)
    return ConversationHandler.END


async def cancel_and_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    return await link_start(update, context)


async def cancel_and_children(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await children_command(update, context)
    return ConversationHandler.END


async def cancel_and_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await status_command(update, context)
    return ConversationHandler.END


async def cancel_and_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await help_command(update, context)
    return ConversationHandler.END


async def link_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⏳ Account linking session timed out. Tap *🔗 Link My Account* or send /link to try again.",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    return ConversationHandler.END


async def got_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number.strip()
    elif update.message.text:
        text = update.message.text.strip()
        if text.lower() in {"/cancel", "❌ cancel", "cancel"}:
            return await cancel(update, context)
        if text.lower() in {"/start", "start", "menu", "open menu", "main menu"}:
            return await cancel_and_start(update, context)
        if any(k in text.lower() for k in ["children", "my children", "students"]):
            return await cancel_and_children(update, context)
        if any(k in text.lower() for k in ["status", "today's status", "today"]):
            return await cancel_and_status(update, context)
        if any(k in text.lower() for k in ["help", "instructions"]):
            return await cancel_and_help(update, context)
        if any(k in text.lower() for k in ["link my account", "link account", "/link"]):
            return await cancel_and_link(update, context)

        cleaned_digits = "".join(c for c in text if c.isdigit())
        if len(cleaned_digits) < 7 and "@" not in text:
            await update.message.reply_text(
                "⚠️ Please enter a valid registered phone number (e.g. `0911223344` or `+251911223344`) or tap *📱 Share My Phone Number* below.\n\n"
                "_(or tap ❌ Cancel or /start to exit)_",
                parse_mode="Markdown"
            )
            return ASK_PHONE
        phone = text
    else:
        await update.message.reply_text("Please share your contact or type your phone number:")
        return ASK_PHONE

    context.user_data["phone"] = phone
    await update.message.reply_text(
        f"📱 Account identifier received: `{phone}`\n\n"
        f"🔑 Now enter your SchoolGuard *password*:\n"
        f"_(or type /cancel or /start to abort)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_PASSWORD


async def got_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = (update.message.text or "").strip()
    tg_user = update.effective_user

    if password.lower() in {"/cancel", "❌ cancel", "cancel"}:
        return await cancel(update, context)
    if password.lower() in {"/start", "start", "menu", "open menu", "main menu"}:
        return await cancel_and_start(update, context)
    if any(k in password.lower() for k in ["children", "my children", "students"]):
        return await cancel_and_children(update, context)
    if any(k in password.lower() for k in ["status", "today's status", "today"]):
        return await cancel_and_status(update, context)
    if any(k in password.lower() for k in ["help", "instructions"]):
        return await cancel_and_help(update, context)
    if any(k in password.lower() for k in ["link my account", "link account", "/link"]):
        return await cancel_and_link(update, context)

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
                    f"❌ *Authentication Failed:*\n{detail}\n\n"
                    f"Please make sure your phone number was entered correctly, and try again by tapping *🔗 Link My Account* or sending /link.",
                    parse_mode="Markdown",
                    reply_markup=MAIN_MENU
                )
                context.user_data.clear()
                return ConversationHandler.END

            token = login_resp.json()["access_token"]

            # Step 2: Link their Telegram ID
            link_resp = await client.post(
                f"{API_BASE}/api/telegram/link-self",
                json={"telegram_id": tg_user.id, "telegram_username": tg_user.username},
                headers={"Authorization": f"Bearer {token}"}
            )
            if link_resp.status_code == 200:
                await update.message.reply_text(
                    f"✅ *Account Linked Successfully!*\n\n"
                    f"Welcome, *{tg_user.first_name}*! 🎉\n"
                    f"Your Telegram is now connected to SchoolGuard. You will automatically receive push notifications for your children's gate arrivals and departures.",
                    parse_mode="Markdown",
                    reply_markup=MAIN_MENU
                )
            else:
                detail = link_resp.json().get("detail", "Unknown error")
                await update.message.reply_text(
                    f"❌ Could not link account: {detail}",
                    reply_markup=MAIN_MENU
                )

    except httpx.ConnectError:
        await update.message.reply_text(
            "⚠️ Cannot reach the SchoolGuard server. Please make sure the backend server is running.",
            reply_markup=MAIN_MENU
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=MAIN_MENU)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Action cancelled.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def children_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View linked students."""
    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    if not parent:
        await update.message.reply_text(
            "⚠️ *Account Not Linked*\n\n"
            "Your Telegram account is not linked to SchoolGuard yet.\n"
            "Tap *🔗 Link My Account* below or send /link to connect.",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    children = get_parent_children(parent.id)
    if not children:
        await update.message.reply_text(
            f"👤 *Parent Account:* {parent.full_name}\n\n"
            "No students are currently linked to your profile.\n"
            "Please contact your school administrator to link your student(s).",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    lines = [f"👶 *Linked Students for {parent.full_name}:*\n"]
    for item in children:
        st = item["student"]
        cls_str = f" | Class: *{item['class_name']}*" if item["class_name"] else ""
        lines.append(f"• 👤 *{st.notification_name}* (Code: `{st.student_code}`){cls_str}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=MAIN_MENU)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View today's attendance status."""
    tg_user = update.effective_user
    parent = get_linked_parent(tg_user.id) if tg_user else None

    if not parent:
        await update.message.reply_text(
            "⚠️ *Account Not Linked*\n\n"
            "Your Telegram account is not linked yet.\n"
            "Tap *🔗 Link My Account* below or send /link to connect.",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    records = get_children_today_attendance(parent.id)
    if not records:
        await update.message.reply_text(
            f"👤 *Parent Account:* {parent.full_name}\n\n"
            "No student records are linked to your profile.",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    today_str = date_type.today().strftime("%Y-%m-%d")
    lines = [f"📊 *Attendance Status — {today_str}*\n"]
    for item in records:
        st = item["student"]
        att = item["attendance"]
        name = st.notification_name
        if not att:
            lines.append(f"👶 *{name}* (Code: `{st.student_code}`)\n   Status: ⏳ *Not recorded yet*\n")
        else:
            status_emoji = "✅" if att.status == "PRESENT" else "⚠️" if att.status == "LATE" else "❌" if att.status == "ABSENT" else "ℹ️"
            arr = att.arrival_time.strftime("%I:%M %p") if att.arrival_time else "Not recorded"
            dep = att.departure_time.strftime("%I:%M %p") if att.departure_time else "Not departed"
            lines.append(
                f"👶 *{name}* (Code: `{st.student_code}`)\n"
                f"   Status: {status_emoji} *{att.status}*\n"
                f"   Arrival: 🕒 {arr}\n"
                f"   Departure: 🕒 {dep}\n"
            )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=MAIN_MENU)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *SchoolGuard Bot Instructions*\n\n"
        "• *🔗 /link* — Connect your parent account using phone & password\n"
        "• *👶 /children* — View your linked children and classes\n"
        "• *📊 /status* — Check today's arrival and departure status\n"
        "• *🛡️ /start* — Reopen the main interactive keyboard menu\n"
        "• *❌ /cancel* — Cancel the current operation\n\n"
        "For assistance or account setup, please reach out to your school office.",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # Route matching for various button/menu texts
    if any(k in text.lower() for k in ["link my account", "link account", "connect account"]):
        return await link_start(update, context)
    elif any(k in text.lower() for k in ["children", "my children", "students"]):
        return await children_command(update, context)
    elif any(k in text.lower() for k in ["status", "today's status", "today"]):
        return await status_command(update, context)
    elif any(k in text.lower() for k in ["help", "instructions"]):
        return await help_command(update, context)
    elif any(k in text.lower() for k in ["menu", "start", "main menu", "open menu"]):
        return await start(update, context)
    else:
        await update.message.reply_text(
            "Please select an option from the menu buttons below, or send /help for instructions.",
            reply_markup=MAIN_MENU
        )


async def post_init(application: Application):
    """Registers the bot commands so the Telegram app displays the persistent blue Menu button."""
    commands = [
        BotCommand("start", "Open main menu & dashboard"),
        BotCommand("link", "Link your SchoolGuard account"),
        BotCommand("children", "View your linked children"),
        BotCommand("status", "View today's attendance status"),
        BotCommand("help", "Get help & instructions"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        print("Telegram bot commands & menu button registered successfully.")
    except Exception as e:
        print(f"Notice: could not set bot commands yet ({e})")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing in .env")

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = Application.builder().token(BOT_TOKEN).request(request).post_init(post_init).build()

    # Conversation handler for the link flow
    link_conv = ConversationHandler(
        entry_points=[
            CommandHandler("link", link_start),
            MessageHandler(filters.Regex(r"(?i).*(link\s*my\s*account|link\s*account|link\s*your\s*account).*"), link_start),
        ],
        states={
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, got_phone),
                CommandHandler("start", cancel_and_start),
                CommandHandler("link", link_start),
                CommandHandler("children", cancel_and_children),
                CommandHandler("status", cancel_and_status),
                CommandHandler("help", cancel_and_help),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone),
            ],
            ASK_PASSWORD: [
                CommandHandler("start", cancel_and_start),
                CommandHandler("link", link_start),
                CommandHandler("children", cancel_and_children),
                CommandHandler("status", cancel_and_status),
                CommandHandler("help", cancel_and_help),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_password),
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, link_timeout)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", cancel_and_start),
            CommandHandler("link", link_start),
            CommandHandler("children", cancel_and_children),
            CommandHandler("status", cancel_and_status),
            CommandHandler("help", cancel_and_help),
            MessageHandler(filters.Regex(r"(?i)^(cancel|❌ cancel)$"), cancel),
            MessageHandler(filters.Regex(r"(?i).*(my\s*children|children|students).*"), cancel_and_children),
            MessageHandler(filters.Regex(r"(?i).*(today's\s*status|status).*"), cancel_and_status),
            MessageHandler(filters.Regex(r"(?i).*(help|instructions).*"), cancel_and_help),
            MessageHandler(filters.Regex(r"(?i).*(open\s*main\s*menu|main\s*menu|menu).*"), cancel_and_start),
            MessageHandler(filters.Regex(r"(?i).*(link\s*my\s*account|link\s*account|link\s*your\s*account).*"), link_start),
        ],
        conversation_timeout=300,
    )

    app.add_handler(link_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("children", children_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.Regex(r"(?i).*(my\s*children|children|students).*"), children_command))
    app.add_handler(MessageHandler(filters.Regex(r"(?i).*(today's\s*status|status).*"), status_command))
    app.add_handler(MessageHandler(filters.Regex(r"(?i).*(help|instructions).*"), help_command))
    app.add_handler(MessageHandler(filters.Regex(r"(?i).*(open\s*main\s*menu|main\s*menu|menu).*"), start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print(f"SchoolGuard Telegram bot running (polling)... API base: {API_BASE}")
    app.run_polling(bootstrap_retries=5)


if __name__ == "__main__":
    main()
