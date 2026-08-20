import asyncio
import logging
from datetime import datetime
from telegram import (

    Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    MenuButtonWebApp
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.request import HTTPXRequest

import config
import database

# Enable Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation States
WAITING_FOR_INVITE_CODE, WAITING_FOR_FULL_NAME, WAITING_FOR_BROADCAST = range(1, 4)

# Default WebApp URL — always use production Render URL (never localhost / tunnel)
WEBAPP_URL = getattr(config, "PRODUCTION_URL", "https://uz-tong-hong-ko-biqs.onrender.com")
_bot_application = None
_bot_loop = None

async def update_chat_menu_button(bot, url: str):
    if not url or not url.startswith("https://"):
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🚀 BIQS Mini App",
                web_app=WebAppInfo(url=url)
            )
        )
        logger.info(f"[BOT] Telegram Chat Menu Button updated to: {url}")
    except Exception as e:
        logger.warning(f"[BOT WARN] Could not update chat menu button: {e}")

def set_webapp_url(url: str):
    global WEBAPP_URL
    WEBAPP_URL = url
    print(f"[BOT] Updated WebApp URL to: {WEBAPP_URL}")
    if _bot_application and _bot_loop and _bot_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(
                update_chat_menu_button(_bot_application.bot, url),
                _bot_loop
            )
        except Exception as e:
            logger.warning(f"[BOT WARN] Failed to schedule menu button update: {e}")


MANAGEMENT_ROLES = ('nachalnik', 'master', 'brigadir', 'quality', 'director')


def get_main_keyboard(lang: str = 'ru', user_id: int = None):
    is_admin = database.is_admin_or_superadmin(user_id) if user_id else False
    user = database.get_user(user_id) if user_id else None
    role = user.get("role", "worker") if user else "worker"
    is_mgmt = role in MANAGEMENT_ROLES or is_admin

    kb = []
    if lang == 'uz':
        kb.append([KeyboardButton("📊 Mening statistikam")])
        if is_mgmt:
            kb.append([KeyboardButton("👥 Mening jamoam (xodimlar)")])
        if role == 'worker':
            kb.append([KeyboardButton("🏢 Mening rahbarlarim")])
        kb.append([KeyboardButton("👨‍💼 Yaratuvchi"), KeyboardButton("🆘 Texnik yordam")])
    else:
        kb.append([KeyboardButton("📊 Моя статистика")])
        if is_mgmt:
            kb.append([KeyboardButton("👥 Моя команда (сотрудники)")])
        if role == 'worker':
            kb.append([KeyboardButton("🏢 Моё руководство")])
        kb.append([KeyboardButton("👨‍💼 Создатель"), KeyboardButton("🆘 Техподдержка")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def get_webapp_inline_keyboard(lang: str = 'ru'):
    url = WEBAPP_URL
    if lang == 'uz':
        btn_text = "🚀 Test va o'quv platformasini ochish (Mini App)"
    else:
        btn_text = "🚀 Открыть платформу обучения (Mini App)"

    keyboard = [
        [InlineKeyboardButton(btn_text, web_app=WebAppInfo(url=url))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data="set_lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский язык", callback_data="set_lang_ru")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start Command Handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = database.get_user(user.id)
    is_admin = user.id in config.ADMIN_IDS or (db_user and db_user.get("role") in ("admin", "superadmin"))

    # ✅ Force-update this specific user's Telegram Chat Menu Button to Production URL
    try:
        await context.bot.set_chat_menu_button(
            chat_id=user.id,
            menu_button=MenuButtonWebApp(
                text="🚀 BIQS Mini App",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
    except Exception as e:
        logger.warning(f"[BOT WARN] Could not update menu button for user {user.id}: {e}")

    # ✅ Admin / Creator auto-bypass: Never ask Administrator for invite code!
    if not db_user and user.id in config.ADMIN_IDS:
        database.create_user(
            telegram_id=user.id,
            full_name=user.full_name or user.first_name,
            username=user.username or "",
            phone="",
            invite_code="ADMIN",
            shop_name="Администрация",
            language="ru",
            role="superadmin"
        )
        db_user = database.get_user(user.id)

    if db_user:
        lang = db_user.get("language", "ru")

        if lang == 'uz':
            text = (
                f"Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
                f"O'quv platformasi va BIQS testini ochish uchun pastdagi tugmani bosing 👇"
            )
        else:
            text = (
                f"Добро пожаловать, <b>{user.first_name}</b>!\n\n"
                f"Для открытия платформы обучения BIQS нажмите кнопку ниже 👇"
            )
        
        await update.message.reply_html(
            text,
            reply_markup=get_main_keyboard(lang, user.id)
        )
        return ConversationHandler.END
    else:
        context.user_data["full_name"] = user.full_name or user.first_name
        context.user_data["username"] = user.username or ""
        
        msg_text = (
            "Assalomu alaykum, botimizga xush kelibsiz! 👋\n"
            "Ushbu bot xodimlarimiz BIQS sifat standartlarini bilishlari uchun yaratilgan.\n\n"
            "🔑 <b>Administratorning kirish kodini kiriting:</b>"
        )
        await update.message.reply_html(msg_text, reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_INVITE_CODE

# Invite Code Verification
async def process_invite_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_text = update.message.text.strip().upper()
    code_data = database.get_invite_code(code_text)

    if not code_data:
        await update.message.reply_html(
            "❌ <b>Xato kirish kodi!</b>\n"
            "Iltimos, kodni tekshirib qayta kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_FOR_INVITE_CODE

    context.user_data["invite_code"] = code_text
    context.user_data["shop_name"] = code_data["shop_name"]
    context.user_data["target_role"] = code_data.get("target_role", "worker")
    
    await update.message.reply_html(
        "✅ <b>Kod qabul qilindi!</b>\n\n"
        "👤 Iltimos, <b>Ism va Familiyangizni</b> kiriting:"
    )
    return WAITING_FOR_FULL_NAME

async def process_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    
    text = "🌐 <b>Tilni tanlang / Выберите язык интерфейса:</b>"
    await update.message.reply_html(text, reply_markup=get_language_inline_keyboard())
    return ConversationHandler.END

# Language Callback Handler
async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = 'uz' if query.data == "set_lang_uz" else 'ru'
    user_id = query.from_user.id

    db_user = database.get_user(user_id)

    if db_user:
        database.update_user_language(user_id, lang)
    else:
        full_name = context.user_data.get("full_name", query.from_user.full_name)
        username = context.user_data.get("username", query.from_user.username)
        phone = context.user_data.get("phone", "")
        invite_code = context.user_data.get("invite_code", "UZTH-BIQS2026")
        shop_name = context.user_data.get("shop_name", "Сотрудник Уз Тонг Хонг Ко")
        target_role = context.user_data.get("target_role", "worker")

        database.create_user(
            telegram_id=user_id,
            full_name=full_name,
            username=username,
            phone=phone,
            invite_code=invite_code,
            shop_name=shop_name,
            language=lang,
            role=target_role
        )

    if lang == 'uz':
        confirm_text = (
            f"Assalomu alaykum, botimizga xush kelibsiz!\n\n"
            f"🚀 Platformani ochish uchun pastdagi menyudan foydalaning."
        )
    else:
        confirm_text = (
            f"Добро пожаловать в наш бот!\n\n"
            f"🚀 Для открытия платформы используйте меню ниже."
        )

    try:
        await query.message.delete()
    except:
        pass

    await context.bot.send_message(
        chat_id=user_id,
        text=confirm_text,
        reply_markup=get_main_keyboard(lang, user_id)
    )

ROLE_LABELS = {
    'nachalnik': ('🏭 Начальник цеха', '🏭 Sex boshlig\'i'),
    'master':    ('👨‍🔧 Мастер участка', '👨‍🔧 Master (Usta)'),
    'brigadir':  ('👷 Бригадир',         '👷 Brigadir'),
    'worker':    ('👤 Рабочий',          '👤 Ishchi'),
    'quality':   ('🛡️ Контроль качества','🛡️ Sifat nazorati'),
    'director':  ('👑 Руководство',     '👑 Rahbariyat'),
    'admin':     ('⚙️ Администратор',   '⚙️ Administrator'),
    'superadmin':('⚡ Суперадминистратор','⚡ Superadmin'),
}


# Team Monitoring Handler (nachalnik / master / brigadir / admin)
async def my_team_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    if not db_user:
        await update.message.reply_text("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    lang = db_user.get("language", "uz")
    role = db_user.get("role", "worker")
    shop_name = db_user.get("shop_name", "СП Уз Тонг Хонг Ко")
    is_admin = database.is_admin_or_superadmin(user_id)

    if role not in MANAGEMENT_ROLES and not is_admin:
        txt = ("⚠️ Bu bo'lim faqat rahbarlar uchun mo'ljallangan." if lang == 'uz'
               else "⚠️ Этот раздел доступен только для руководства.")
        await update.message.reply_text(txt)
        return

    workers = database.get_subordinates(user_id)
    
    import json as _json

    def _format_member(idx, w, lang):
        r = w.get('role', 'worker')
        lbl = ROLE_LABELS.get(r, ('👤', '👤'))[0 if lang == 'ru' else 1]
        badge = " 🌟" if w['best_score'] >= 80 else ""
        line = f"{idx}. <b>{w['full_name']}</b> — <i>{lbl}</i>{badge}\n"
        line += f"   🎯 {'Лучший результат' if lang=='ru' else 'Eng yaxshi natija'}: <b>{round(w['best_score'])}%</b> | "
        line += f"📝 {'Попыток' if lang=='ru' else 'Testlar'}: {w['tests_completed']}\n"
        if w.get('latest_mistakes'):
            try:
                ml = _json.loads(w['latest_mistakes'])
                ms = ", ".join(ml) if isinstance(ml, list) else str(w['latest_mistakes'])
            except:
                ms = str(w['latest_mistakes'])
            if ms:
                line += f"   ⚠️ {'Посл. ошибки' if lang=='ru' else 'Oxirgi xatolar'}: <i>{ms}</i>\n"
        return line + "\n"

    title_ru = f"👥 <b>МОЯ КОМАНДА — {shop_name}</b>"
    title_uz = f"👥 <b>MENING JAMOAM — {shop_name}</b>"

    if lang == 'uz':
        if not workers:
            msg = f"🏭 <b>{shop_name}</b> bo'yicha hali hech kim ro'yxatdan o'tmagan."
        else:
            msg = title_uz + f"\n\n📊 <b>Jami:</b> {len(workers)} ta\n\n"
            for idx, w in enumerate(workers, 1):
                msg += _format_member(idx, w, 'uz')
    else:
        if not workers:
            msg = f"🏭 По <b>{shop_name}</b> пока нет зарегистрированных участников."
        else:
            msg = title_ru + f"\n\n📊 <b>Всего:</b> {len(workers)}\n\n"
            for idx, w in enumerate(workers, 1):
                msg += _format_member(idx, w, 'ru')

    # Send in chunks if too long
    if len(msg) <= 4000:
        await update.message.reply_html(msg, reply_markup=get_main_keyboard(lang, user_id))
    else:
        chunks = [msg[i:i+3800] for i in range(0, len(msg), 3800)]
        for i, chunk in enumerate(chunks):
            await update.message.reply_html(chunk, reply_markup=get_main_keyboard(lang, user_id) if i == len(chunks)-1 else None)

def format_sector_stats_text(lang: str = 'ru') -> str:
    stats = database.get_shop_statistics()
    if not stats:
        return ("🏢 По участкам пока нет данных." if lang == 'ru' else "🏢 Bo'limlar bo'yicha hali ma'lumot yo'q.")
    
    if lang == 'uz':
        txt = "🏭 <b>BO'LIMLAR VA LINIYALAR STATISTIKASI:</b>\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        for idx, s in enumerate(stats, 1):
            avg = s.get("avg_score", 0)
            badge = "🟢" if avg >= 80 else ("🟡" if avg >= 60 else "🔴")
            txt += f"{idx}. 🏢 <b>{s['shop_name']}</b> — <b>{avg}%</b> {badge}\n"
            txt += f"   👥 Xodimlar: <b>{s['total_workers']}</b> ta | 📝 Topshirgan: {s['tested_workers']} ta\n"
            txt += f"   ⭐ BIQS Mutaxassislari: <b>{s['expert_count']}</b> ta\n\n"
    else:
        txt = "🏭 <b>СВОДКА ПО УЧАСТКАМ И ЛИНИЯМ:</b>\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        for idx, s in enumerate(stats, 1):
            avg = s.get("avg_score", 0)
            badge = "🟢" if avg >= 80 else ("🟡" if avg >= 60 else "🔴")
            txt += f"{idx}. 🏢 <b>{s['shop_name']}</b> — <b>{avg}%</b> {badge}\n"
            txt += f"   👥 Сотрудников: <b>{s['total_workers']}</b> | 📝 Прошли тест: {s['tested_workers']}\n"
            txt += f"   ⭐ Экспертов BIQS: <b>{s['expert_count']}</b>\n\n"
    return txt

async def sectors_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    lang = db_user.get("language", "ru") if db_user else "ru"
    txt = format_sector_stats_text(lang)
    await update.message.reply_html(txt, reply_markup=get_webapp_inline_keyboard(lang))

# Statistics Handler — available to ALL registered users
async def show_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    if not db_user:
        await update.message.reply_text("Avval /start orqali ro'yxatdan o'ting. / Сначала пройдите регистрацию через /start.")
        return
    lang = db_user.get("language", "ru")
    role = db_user.get("role", "worker")
    shop = db_user.get("shop_name", "—")
    is_admin = database.is_admin_or_superadmin(user_id)

    stats = database.get_user_stats(user_id)
    best_score = round(stats.get("best_score") or 0)
    tests_count = stats.get("tests_count", 0)
    avg_score = round(stats.get("avg_score") or 0)
    is_expert = best_score >= 80

    role_lbl_ru, role_lbl_uz = ROLE_LABELS.get(role, ("👤 Сотрудник", "👤 Xodim"))

    if lang == 'uz':
        status_str = "🌟 <b>STATUS: BIQS Mutaxassisi!</b>" if is_expert else "💼 <b>STATUS: Faol xodim</b>"
        text = (
            f"📊 <b>SIZNING STATISTIKANGIZ</b>\n"
            f"🏭 СП Уз Тонг Хонг Ко\n\n"
            f"👤 <b>F.I.Sh:</b> {db_user.get('full_name', update.effective_user.full_name)}\n"
            f"🏢 <b>Bo'lim:</b> {shop}\n"
            f"🎖 <b>Lavozim:</b> {role_lbl_uz}\n\n"
            f"🎯 <b>Eng yaxshi natija:</b> {best_score}%\n"
            f"📈 <b>O'rtacha natija:</b> {avg_score}%\n"
            f"📝 <b>Topshirilgan testlar:</b> {tests_count} ta\n\n"
            f"{status_str}\n\n"
            f"💡 <i>80%+ ball — BIQS Mutaxassisi unvoni!</i>"
        )
    else:
        status_str = "🌟 <b>СТАТУС: Эксперт BIQS!</b>" if is_expert else "💼 <b>СТАТУС: Активный сотрудник</b>"
        text = (
            f"📊 <b>ВАША СТАТИСТИКА</b>\n"
            f"🏭 СП Уз Тонг Хонг Ко\n\n"
            f"👤 <b>ФИО:</b> {db_user.get('full_name', update.effective_user.full_name)}\n"
            f"🏢 <b>Участок:</b> {shop}\n"
            f"🎖 <b>Должность:</b> {role_lbl_ru}\n\n"
            f"🎯 <b>Лучший результат:</b> {best_score}%\n"
            f"📈 <b>Средний результат:</b> {avg_score}%\n"
            f"📝 <b>Пройдено тестов:</b> {tests_count}\n\n"
            f"{status_str}\n\n"
            f"💡 <i>80%+ баллов — статус Эксперта BIQS!</i>"
        )

    # For management & admins, append full sector breakdown overview
    if role in MANAGEMENT_ROLES or is_admin:
        text += "\n\n" + format_sector_stats_text(lang)

    await update.message.reply_html(text, reply_markup=get_webapp_inline_keyboard(lang))


# My Management Handler — workers see their bosses (NO admin/superadmin shown)
async def my_management_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    if not db_user:
        await update.message.reply_text("Avval /start orqali ro'yxatdan o'ting.")
        return
    lang = db_user.get("language", "ru")
    management = database.get_management_chain(user_id)
    if not management:
        txt = ("🏢 Sizning sexingizda rahbarlar ro'yxatdan o'tmagan." if lang == 'uz'
               else "🏢 В вашем цехе руководство ещё не зарегистрировано.")
        await update.message.reply_html(txt)
        return
    if lang == 'uz':
        msg = "🏢 <b>MENING RAHBARLARIM:</b>\n\n"
        for m in management:
            lbl = ROLE_LABELS.get(m['role'], ('👤','👤'))[1]
            msg += f"• {lbl}: <b>{m['full_name']}</b>\n"
    else:
        msg = "🏢 <b>МОЁ РУКОВОДСТВО:</b>\n\n"
        for m in management:
            lbl = ROLE_LABELS.get(m['role'], ('👤','👤'))[0]
            msg += f"• {lbl}: <b>{m['full_name']}</b>\n"
    await update.message.reply_html(msg, reply_markup=get_main_keyboard(lang, user_id))

# Change Language Handler
async def change_lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌐 <b>Выберите язык интерфейса / Tilni tanlang:</b>"
    await update.message.reply_html(text, reply_markup=get_language_inline_keyboard())

async def log_if_not_admin(user_id: int, command: str, bot=None) -> bool:
    """Log attack and immediately send full user profile to all superadmins."""
    if not database.is_admin_or_superadmin(user_id):
        db_user = database.get_user(user_id)
        if db_user:
            database.log_attack(user_id, f"Попытка доступа к {command}")
            # Send instant alert with full profile
            if bot:
                info = database.get_attack_full_info(user_id)
                if info:
                    alert = (
                        f"🚨 <b>ПОПЫТКА ВЗЛОМА / HUJUM URINISHI!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 <b>ФИО:</b> {info.get('full_name','—')}\n"
                        f"📱 <b>Username:</b> @{info.get('username') or '—'}\n"
                        f"📞 <b>Телефон:</b> {info.get('phone') or '—'}\n"
                        f"🆔 <b>TG ID:</b> <code>{info.get('telegram_id')}</code>\n"
                        f"🏭 <b>Участок/Цех:</b> {info.get('shop_name','—')}\n"
                        f"👨‍💼 <b>Мастер/Нач.:</b> {info.get('master_name') or '—'}\n"
                        f"🎖 <b>Роль:</b> {info.get('role','—')}\n"
                        f"🔑 <b>Код входа:</b> <code>{info.get('invite_code','—')}</code>\n"
                        f"📅 <b>Регистрация:</b> {str(info.get('registered_at','—'))[:10]}\n\n"
                        f"⚠️ <b>Команда:</b> <code>{command}</code>\n"
                        f"🔢 <b>Всего попыток:</b> {info.get('total_attacks',1)}\n"
                        f"🕒 <b>Последняя:</b> {str(info.get('last_attack','—'))[:19]}"
                    )
                    import config as _cfg
                    for admin_id in _cfg.ADMIN_IDS:
                        try:
                            await bot.send_message(chat_id=admin_id, text=alert, parse_mode="HTML")
                        except:
                            pass
        return True
    return False

# Handler for legacy '⚙️ Панель Администратора' button press (removes old keyboard)
async def remove_old_admin_btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    lang = db_user.get("language", "ru") if db_user else "ru"
    
    text = (
        "ℹ️ <b>Admin paneli Mini App ilovasi ichiga ko'chirildi.</b>\n"
        "<i>Eski tugma menyudan o'chirildi. Yangi menyudan foydalaning 👇</i>"
    ) if lang == 'uz' else (
        "ℹ️ <b>Панель администратора находится внутри Mini App.</b>\n"
        "<i>Старая кнопка удалена из меню. Используйте новое меню ниже 👇</i>"
    )
    await update.message.reply_html(text, reply_markup=get_main_keyboard(lang, user_id))

# Admin Panel Handler (/admin)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.is_admin_or_superadmin(user_id):
        await log_if_not_admin(user_id, "/admin")
        return

    codes = database.get_all_invite_codes()
    workers = database.get_all_workers_admin()
    experts = [w for w in workers if w["best_score"] >= 80]
    admins = database.get_all_admins()
    management = database.get_all_management()
    nachalniki = [m for m in management if m['role'] == 'nachalnik']
    masters = [m for m in management if m['role'] == 'master']
    brigadiry = [m for m in management if m['role'] == 'brigadir']

    text = (
        f"⚙️ <b>ПАНЕЛЬ АДМИНИСТРАТОРА — УЗ ТОНГ ХОНГ КО</b>\n\n"
        f"👥 <b>Всего сотрудников:</b> {len(workers)}\n"
        f"🌟 <b>Экспертов BIQS (80%+):</b> {len(experts)}\n"
        f"🔑 <b>Кодов приглашения:</b> {len(codes)}\n\n"
        f"🏭 <b>Нач. цеха:</b> {len(nachalniki)} | "
        f"👨‍🔧 <b>Мастеров:</b> {len(masters)} | "
        f"👷 <b>Бригадиров:</b> {len(brigadiry)}\n\n"
        f"📌 <b>Команды создания кодов:</b>\n"
        f"• <code>/newcode KOD nachalnik 1-Tsex</code> — Нач. цеха\n"
        f"• <code>/newcode KOD master 1-Tsex</code> — Мастер\n"
        f"• <code>/newcode KOD brigadir 1-Tsex</code> — Бригадир\n"
        f"• <code>/newcode KOD worker 1-Tsex</code> — Рабочий\n"
        f"• <code>/addadmin ID [PERMS]</code> — Назначить IT-админа\n"
    )
    keyboard = [
        [
            InlineKeyboardButton("🔑 Создать код", callback_data="admin_create_code_prompt"),
            InlineKeyboardButton("👔 Управление", callback_data="admin_manage_admins")
        ],
        [
            InlineKeyboardButton("🛡 Атаки", callback_data="admin_attack_summary")
        ],
        [
            InlineKeyboardButton("📢 Объявления", callback_data="admin_broadcast_prompt")
        ]
    ]
    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))


# Founder Button Handler
async def founder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👨‍💼 <b>Kamolov Abdulaziz Sherzodbekovich</b>\n\n"
        "Xalqaro darajali muhandis & IT-tadbirkor\n"
    )
    try:
        with open("static/founder.png", "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=text, parse_mode="HTML", protect_content=True)
    except Exception as e:
        await update.message.reply_html(text, protect_content=True)

# Force Keyboard Update for ALL users (admin only — run once)
async def update_keyboards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.is_admin_or_superadmin(user_id):
        await log_if_not_admin(user_id, "/update_kb")
        return

    workers = database.get_all_workers_admin()
    await update.message.reply_text(f"⏳ Updating keyboards for {len(workers)} users...")

    success = 0
    for w in workers:
        try:
            lang = w.get("language", "ru")
            msg_text = (
                "🔄 <b>Menyu yangilandi!</b> / <b>Меню обновлено!</b>\n"
                "<i>Eski tugmalar o'chirildi. Pastdagi yangi menyudan foydalaning 👇\n"
                "Старые кнопки удалены. Используйте новое меню ниже 👇</i>"
            )
            await context.bot.send_message(
                chat_id=w["telegram_id"],
                text=msg_text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard(lang, w["telegram_id"])
            )
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(f"✅ Done! Keyboards updated for {success}/{len(workers)} users.")

# Tech Support Handler
async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    lang = db_user.get("language", "uz") if db_user else "uz"
    msg_text = update.message.text or ""

    if "Texnik yordam" in msg_text or lang == 'uz':
        text = (
            "🆘 <b>Texnik Yordam — СП Уз Тонг Хонг Ко</b>\n\n"
            "📞 <b>Telefon:</b> <code>+998507775152</code>\n\n"
            "⚠️ <b>Diqqat!</b>\n"
            "<i>Iltimos, mayda savollar uchun qo'ng'iroq qilmang.\n"
            "Faqat haqiqiy va jiddiy muammolar bo'lganda murojaat qiling.</i>\n\n"
            "🕐 Ish vaqti: <b>08:00 – 19:00</b>"
        )
    else:
        text = (
            "🆘 <b>Техническая поддержка — СП Уз Тонг Хонг Ко</b>\n\n"
            "📞 <b>Телефон:</b> <code>+998507775152</code>\n\n"
            "⚠️ <b>Внимание!</b>\n"
            "<i>Пожалуйста, не звоните по мелочам.\n"
            "Обращайтесь только при реальных и серьёзных вопросах.</i>\n\n"
            "🕐 Рабочее время: <b>08:00 – 19:00</b>"
        )

    await update.message.reply_html(text)

# Admin Command: /newcode
async def newcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "create_codes"):
        await update.message.reply_html("⚠️ <b>Ruxsat berilmadi!</b> Sizda kod yaratish huquqi yo'q.")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_html(
            "⚠️ <b>Kod yaratish / Создание кода:</b>\n"
            "<code>/newcode &lt;KOD&gt; &lt;ROL&gt; &lt;TSEX_NOMI&gt;</code>\n\n"
            "<i>Rollar / Роли:</i>\n"
            "• <code>nachalnik</code> — 🏭 Начальник цеха\n"
            "• <code>master</code>    — 👨‍🔧 Мастер\n"
            "• <code>brigadir</code>  — 👷 Бригадир\n"
            "• <code>quality</code>   — 🛡️ Контроль качества\n"
            "• <code>director</code>  — 👑 Руководство\n"
            "• <code>worker</code>    — 🎯 Рабочий\n\n"
            "<i>Misollar:</i>\n"
            "• <code>/newcode BOSS1 nachalnik 1-Tsex</code>\n"
            "• <code>/newcode MST1 master 1-Tsex</code>\n"
            "• <code>/newcode BRG1 brigadir 1-Tsex</code>\n"
            "• <code>/newcode QL1 quality 1-Tsex</code>\n"
            "• <code>/newcode DIR1 director Rahbariyat</code>\n"
            "• <code>/newcode WRK1 worker 1-Tsex</code>"
        )
        return

    code = args[0].upper()
    target_role = "worker"
    shop_startIndex = 1

    VALID_ROLES = {
        "nachalnik": "nachalnik", "начальник": "nachalnik", "nachalnic": "nachalnik",
        "master": "master", "мастер": "master", "boshliq": "master", "usta": "master",
        "brigadir": "brigadir", "бригадир": "brigadir",
        "quality": "quality", "качество": "quality", "sifat": "quality",
        "director": "director", "директор": "director", "rahbar": "director",
        "worker": "worker", "xodim": "worker", "работник": "worker", "ishchi": "worker",
    }
    if len(args) > 1 and args[1].lower() in VALID_ROLES:
        target_role = VALID_ROLES[args[1].lower()]
        shop_startIndex = 2

    shop_name = " ".join(args[shop_startIndex:]) if len(args) > shop_startIndex else "СП Уз Тонг Хонг Ко"
    master_name = "Руководство"

    database.add_invite_code(code, shop_name, master_name, user_id, target_role=target_role)

    role_labels = {
        'nachalnik': '🏭 Начальник цеха',
        'master':    '👨‍🔧 Мастер',
        'brigadir':  '👷 Бригадир',
        'quality':   '🛡️ Контроль качества',
        'director':  '👑 Руководство',
        'worker':    '🎯 Рабочий',
    }
    role_badge = role_labels.get(target_role, target_role)

    await update.message.reply_html(
        f"✅ <b>Kod yaratildi! / Код создан!</b>\n\n"
        f"🔑 <b>Kod:</b> <code>{code}</code>\n"
        f"🎖 <b>Rol/Роль:</b> {role_badge}\n"
        f"🏭 <b>Tsex/Цех:</b> <code>{shop_name}</code>"
    )

# Admin Command: /addadmin
async def addadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "manage_admins"):
        await update.message.reply_html("⚠️ <b>Ruxsat berilmadi!</b> Sizda admin tayinlash huquqi yo'q.")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_html(
            "⚠️ <b>Формат команды / Admin tayinlash:</b>\n"
            "<code>/addadmin &lt;TG_ID yoki @username&gt; [huquqlar]</code>\n\n"
            "<i>Misollar:</i>\n"
            "• <code>/addadmin 5543183063 create_codes,view_workers,broadcast</code>\n"
            "• <code>/addadmin @username all</code>\n\n"
            "📌 <b>Mavjud huquqlar (Permissions):</b>\n"
            "• <code>create_codes</code> — Kod yaratish\n"
            "• <code>view_workers</code> — Xodimlarni ko'rish\n"
            "• <code>view_attacks</code> — Xavfsizlik loglari\n"
            "• <code>broadcast</code> — E'lon yuborish\n"
            "• <code>manage_admins</code> — Adminlarni boshqarish\n"
            "• <code>all</code> — Barcha huquqlar"
        )
        return

    target_identifier = args[0]
    target_user = database.get_user_by_username_or_id(target_identifier)

    if not target_user:
        await update.message.reply_html(
            f"❌ <b>Foydalanuvchi topilmadi!</b>\n"
            f"Foydalanuvchi <code>{target_identifier}</code> botdan avval ro'yxatdan o'tgan bo'lishi kerak."
        )
        return

    perms = args[1] if len(args) > 1 else "create_codes,view_workers,broadcast"
    if perms.lower() == "all":
        perm_list = ["create_codes", "view_workers", "view_attacks", "broadcast", "manage_admins"]
    else:
        perm_list = [p.strip() for p in perms.split(",") if p.strip()]

    database.set_user_role_and_permissions(target_user["telegram_id"], "admin", perm_list)

    await update.message.reply_html(
        f"✅ <b>Foydalanuvchiga ADMIN huquqi berildi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {target_user['full_name']} (ID: <code>{target_user['telegram_id']}</code>)\n"
        f"🔑 <b>Roli:</b> <code>ADMIN</code>\n"
        f"🛡 <b>Huquqlari:</b> <code>{', '.join(perm_list)}</code>"
    )

# Admin Command: /deleteuser
async def deleteuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.is_admin_or_superadmin(user_id):
        await log_if_not_admin(user_id, "/deleteuser")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_html(
            "⚠️ <b>Foydalanish / Использование:</b>\n"
            "<code>/deleteuser &lt;TG_ID yoki @username&gt;</code>\n\n"
            "<i>Misollar / Примеры:</i>\n"
            "• <code>/deleteuser 5543183063</code>\n"
            "• <code>/deleteuser @username</code>\n\n"
            "⚠️ Bu buyruq foydalanuvchini va uning barcha test natijalarini o'chiradi!\n"
            "<i>Эта команда удаляет пользователя и все его результаты тестов!</i>"
        )
        return

    target = database.get_user_by_username_or_id(args[0])
    if not target:
        await update.message.reply_html(
            f"❌ <b>Foydalanuvchi topilmadi!</b>\n"
            f"<code>{args[0]}</code> — bunday foydalanuvchi ro'yxatdan o'tmagan.\n\n"
            f"<i>Пользователь не найден в базе.</i>"
        )
        return

    target_id = target["telegram_id"]
    target_name = target.get("full_name", "—")
    target_role = target.get("role", "worker")

    # Prevent deleting superadmins from config
    import config as _cfg
    if target_id in _cfg.ADMIN_IDS:
        await update.message.reply_html(
            "🚫 <b>Asosiy superadminni o'chirib bo'lmaydi!</b>\n"
            "<i>Нельзя удалить главного суперадминистратора!</i>"
        )
        return

    deleted = database.delete_user(target_id)
    if deleted:
        await update.message.reply_html(
            f"✅ <b>Foydalanuvchi o'chirildi!</b>\n\n"
            f"👤 <b>Ism:</b> {target_name}\n"
            f"🆔 <b>TG ID:</b> <code>{target_id}</code>\n"
            f"🔑 <b>Roli:</b> <code>{target_role}</code>\n\n"
            f"<i>Пользователь и все его данные удалены из базы.</i>"
        )
    else:
        await update.message.reply_html("❌ O'chirishda xatolik yuz berdi. / Ошибка при удалении.")

# Admin Command: /workers
async def workers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "view_workers"):
        await update.message.reply_html("⚠️ Sizda xodimlarni ko'rish huquqi yo'q.")
        return

    workers = database.get_all_workers_admin()
    if not workers:
        await update.message.reply_text("Сотрудники пока не зарегистрированы.")
        return

    msg = "📋 <b>СПИСОК СОТРУДНИКОВ И РЕЗУЛЬТАТЫ:</b>\n\n"
    for idx, w in enumerate(workers, 1):
        is_top = w["best_score"] >= 80
        badge = " 🌟 <b>ЭКСПЕРТ BIQS</b>" if is_top else ""
        msg += f"{idx}. <b>{w['full_name']}</b> ({w.get('shop_name') or 'Sex'}){badge}\n"
        msg += f"   🎯 Natija: <b>{round(w['best_score'])}%</b> | {w['tests_completed']} попыток\n\n"

    await update.message.reply_html(msg)

async def admin_create_code_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🔑 <b>KOD YARATISH / СОЗДАНИЕ КОДА</b>\n\n"
        "Buyruq orqali yaratishingiz mumkin:\n\n"
        "• 🎯 <b>Xodim kodi (Код работника):</b>\n"
        "<code>/newcode WORKER1 worker 1-Sekh</code>\n\n"
        "• 👨‍💼 <b>Boshliq kodi (Код начальника):</b>\n"
        "<code>/newcode CHIEF1 master 1-Sekh</code>"
    )
    await query.message.reply_html(text)

async def admin_manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admins = database.get_all_admins()
    
    msg = "👔 <b>TAYINLANGAN ADMINLAR RO'YXATI (СПИСОК АДМИНИСТРАТОРОВ):</b>\n\n"
    for idx, a in enumerate(admins, 1):
        perm_str = a.get("permissions") or "all"
        role_title = "👑 SUPERADMIN (Owner)" if a.get("role") == "superadmin" or a["telegram_id"] in config.ADMIN_IDS else "🛡 ADMIN"
        msg += f"{idx}. <b>{a.get('full_name') or 'Admin'}</b> — {role_title}\n"
        msg += f"   🆔 ID: <code>{a['telegram_id']}</code> | 👤 @{a.get('username') or 'yoq'}\n"
        msg += f"   🔑 Huquqlar: <code>{perm_str}</code>\n\n"
        
    msg += "➕ Yangi admin tayinlash uchun: <code>/addadmin ID_YOKI_USERNAME huquqlar</code>"
    await query.message.reply_html(msg)

async def admin_view_workers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    msg_target = query.message if query else update.effective_message
    if query:
        await query.answer()
    workers = database.get_all_workers_admin()
    if not workers:
        await msg_target.reply_text("Сотрудники пока не зарегистрированы.")
        return

    msg = "📋 <b>СПИСОК СОТРУДНИКОВ И РЕЗУЛЬТАТЫ:</b>\n\n"
    for idx, w in enumerate(workers, 1):
        is_top = w["best_score"] >= 80
        badge = " 🌟 <b>ЭКСПЕРТ BIQS</b>" if is_top else ""
        msg += f"{idx}. <b>{w['full_name']}</b> ({w.get('shop_name') or 'Sex'}){badge}\n"
        msg += f"   🎯 Natija: <b>{round(w['best_score'])}%</b> | {w['tests_completed']} попыток\n\n"

    await msg_target.reply_html(msg)


async def admin_attack_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not database.check_user_permission(query.from_user.id, "view_attacks"):
        await query.message.reply_text("⚠️ Sizda ushbu bo'limni ko'rish huquqi yo'q.")
        return
    attacks = database.get_attacks_summary()
    if not attacks:
        await query.message.reply_text("🛡 Атак не обнаружено.")
        return
    msg = "🛡 <b>Сводка по атакам:</b>\n\n"
    for a in attacks:
        msg += f"👤 {a['full_name']} ({a['shop_name']} / {a['master_name']}) — <b>{a['attack_count']}</b> попыток\n"
    await query.message.reply_html(msg)

async def admin_attack_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not database.check_user_permission(query.from_user.id, "view_attacks"):
        await query.message.reply_text("⚠️ Sizda ushbu bo'limni ko'rish huquqi yo'q.")
        return
    attacks = database.get_attacks_detailed()
    if not attacks:
        await query.message.reply_text("🔍 Детальных атак не обнаружено.")
        return
    msg = "🔍 <b>Детальный лог атак (последние 50):</b>\n\n"
    for a in attacks:
        time_str = a['attack_time']
        msg += f"⚠️ <b>{a['attempt_details']}</b>\n"
        msg += f"👤 <b>Имя:</b> {a['full_name']}\n"
        msg += f"🏭 <b>Цех:</b> {a['shop_name']}\n"
        msg += f"👨‍🏫 <b>Мастер:</b> {a['master_name']}\n"
        msg += f"🆔 <b>TG ID:</b> <code>{a['telegram_id']}</code>\n"
        if a['username']:
            msg += f"🔗 <b>Username:</b> @{a['username']}\n"
        if a['phone']:
            msg += f"📱 <b>Телефон:</b> {a['phone']}\n"
        msg += f"🕒 <i>{time_str}</i>\n"
        msg += "〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
        if len(msg) > 3500:
            await query.message.reply_html(msg)
            msg = ""
    if msg:
        await query.message.reply_html(msg)

async def admin_broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not database.check_user_permission(query.from_user.id, "broadcast"):
        await query.message.reply_text("⚠️ Sizda e'lon yuborish huquqi yo'q.")
        return
    await query.message.reply_html(
        "📢 <b>Рассылка объявлений / E'lon yuborish</b>\n\n"
        "Отправьте текст объявления, которое будет разослано всем зарегистрированным сотрудникам.\n"
        "<i>Для отмены нажмите /cancel</i>"
    )
    return WAITING_FOR_BROADCAST

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "broadcast"):
        return ConversationHandler.END
    text = update.message.text
    workers = database.get_all_workers_admin()
    await update.message.reply_text("⏳ Начинаю рассылку...")
    success_count = 0
    for w in workers:
        try:
            await context.bot.send_message(
                chat_id=w["telegram_id"],
                text=f"📢 <b>Объявление от Администрации:</b>\n\n{text}",
                parse_mode="HTML"
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"✅ Рассылка завершена! Успешно доставлено: {success_count} пользователям.")
    return ConversationHandler.END

async def notify_admins_about_security_violation(bot, user_id: int, text: str, violation_type: str, matched_pattern: str):
    """Sends immediate high-priority Telegram message to all Admins when security protection is triggered."""
    user = database.get_user(user_id) or {}
    full_name = user.get("full_name", "Неизвестный пользователь")
    username = f"@{user.get('username')}" if user.get("username") else "отсутствует"
    shop_name = user.get("shop_name", "Не указан")
    master_name = user.get("master_name", "Не указан")
    role = user.get("role", "worker")
    phone = user.get("phone", "—")
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_detail = f"[{violation_type}] Промпт: '{text}' (совпадение: '{matched_pattern}')"
    database.log_attack(user_id, log_detail)

    alert_text = (
        "🚨 <b>ВНИМАНИЕ! ПОПЫТКА НЕСАНКЦИОНИРОВАННОГО ДОСТУПА / НАРУШЕНИЯ</b> 🚨\n\n"
        "⚠️ <b>Обнаружено нарушение правил безопасности бота!</b>\n\n"
        f"🛑 <b>Тип нарушения:</b> <code>{violation_type}</code>\n"
        f"🎯 <b>Совпадение:</b> <code>{matched_pattern}</code>\n\n"
        f"📝 <b>Текст сообщения:</b>\n<code>{text[:500]}</code>\n\n"
        "👤 <b>ПРОФИЛЬ НАРУШИТЕЛЯ:</b>\n"
        f"• <b>ФИО:</b> {full_name}\n"
        f"• <b>Username:</b> {username}\n"
        f"• <b>TG ID:</b> <code>{user_id}</code>\n"
        f"• <b>Цех / Участок:</b> {shop_name}\n"
        f"• <b>Мастер / Руководитель:</b> {master_name}\n"
        f"• <b>Роль:</b> <code>{role}</code>\n"
        f"• <b>Телефон:</b> {phone}\n"
        f"🕒 <b>Время:</b> <code>{time_str}</code>\n\n"
        "<i>⚠️ Пользователю отправлено предупреждение. Нарушение зафиксировано в журнале атак.</i>"
    )

    admins = database.get_all_admins()
    admin_ids = set(config.ADMIN_IDS)
    for a in admins:
        admin_ids.add(a["telegram_id"])

    for aid in admin_ids:
        try:
            await bot.send_message(
                chat_id=aid,
                text=alert_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"[SECURITY ALERT] Could not notify admin {aid}: {e}")

async def security_inspection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware that inspects incoming text messages for profanity, links, or malicious prompts.
    """
    if not update or not update.effective_message or not update.effective_message.text:
        return False

    user_id = update.effective_user.id
    text = update.effective_message.text

    is_violation, violation_type, matched_pattern = database.check_security_violations(text, user_id)
    if is_violation:
        await notify_admins_about_security_violation(context.bot, user_id, text, violation_type, matched_pattern)
        
        warn_msg = (
            "🚨 <b>XAVFSIZLIK OGOHLANTIRISHI / ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ</b> 🚨\n\n"
            "⚠️ <b>Nesanobjectlashtirilgan habar, havola yoki taqiqlangan promt aniqlandi!</b>\n"
            "<i>Обнаружено несанкционированное сообщение, ссылка или запрещенный промпт!</i>\n\n"
            "📋 Sizning profilingiz va habaringiz <b>Administratorga (Xavfsizlik xizmati)</b> yuborildi.\n"
            "<i>Ваш профиль и текст сообщения отправлены администратору.</i>"
        )
        await update.effective_message.reply_html(warn_msg)
        return True

    return False

async def addbanned_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "view_attacks"):
        await update.message.reply_html("⚠️ Sizda taqiqlangan промптларни бошқариш huquqi yo'q.")
        return

    args = context.args
    if not args:
        await update.message.reply_html(
            "⚠️ <b>Формат команды / Использование:</b>\n"
            "<code>/addbanned &lt;промпт или матерное слово или ссылка&gt;</code>\n\n"
            "<i>Пример:</i> <code>/addbanned bad_word_here</code>"
        )
        return

    pattern = " ".join(args)
    success = database.add_banned_prompt(pattern)
    if success:
        await update.message.reply_html(f"✅ <b>Промпт/слово добавлено в защиту!</b>\n<code>{pattern}</code>")
    else:
        await update.message.reply_html(f"⚠️ Этот промпт уже существует в базе защиты!")

async def bannedlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "view_attacks"):
        await update.message.reply_html("⚠️ Sizda ушбу бўлимни кўриш huquqi yo'q.")
        return

    banned = database.get_all_banned_prompts()
    if not banned:
        await update.message.reply_text("📋 Защитный список пока пуст.")
        return

    msg = "🛡 <b>СПИСОК ВИРУСНЫХ ПРОМПТОВ И ПРАВИЛ ЗАЩИТЫ:</b>\n\n"
    for b in banned:
        msg += f"• <code>{b['pattern']}</code> [<i>{b['category']}</i>] (ID: {b['id']})\n"

    msg += "\n➕ Добавить: <code>/addbanned &lt;промпт&gt;</code>\n➖ Удалить: <code>/delbanned &lt;ID&gt;</code>"
    if len(msg) > 3500:
        await update.message.reply_html(msg[:3500] + "\n...")
    else:
        await update.message.reply_html(msg)

async def delbanned_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.check_user_permission(user_id, "view_attacks"):
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_html("⚠️ <b>Укажите ID правила:</b> <code>/delbanned 5</code>")
        return

    pid = int(args[0])
    deleted = database.delete_banned_prompt(pid)
    if deleted:
        await update.message.reply_html(f"✅ Правило #{pid} удалено из защиты!")
    else:
        await update.message.reply_html(f"❌ Правило с ID #{pid} не найдено.")

async def admin_broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Рассылка отменена.")
    return ConversationHandler.END

def create_bot_app(webhook_mode: bool = False):
    request = HTTPXRequest(connection_pool_size=8, connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0)

    async def post_init_callback(app: Application):
        global _bot_application, _bot_loop
        _bot_application = app
        _bot_loop = asyncio.get_running_loop()
        if not webhook_mode:
            try:
                await app.bot.delete_webhook(drop_pending_updates=False)
                logger.info("[BOT] Webhook deleted. Polling mode activated.")
            except Exception as e:
                logger.warning(f"[BOT WARN] Could not delete webhook: {e}")
        else:
            logger.info("[BOT] Webhook mode initialized (delete_webhook skipped).")
        await update_chat_menu_button(app.bot, WEBAPP_URL)

    builder = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .request(request)
        .post_init(post_init_callback)
    )
    if webhook_mode:
        builder = builder.updater(None)
    application = builder.build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAITING_FOR_INVITE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_invite_code)],
            WAITING_FOR_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_full_name)],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    application.add_handler(conv_handler)
    
    admin_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_prompt, pattern="^admin_broadcast_prompt$")],
        states={
            WAITING_FOR_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", admin_broadcast_cancel)],
    )
    application.add_handler(admin_broadcast_handler)

    application.add_handler(CallbackQueryHandler(set_language_callback, pattern="^set_lang_"))
    application.add_handler(CallbackQueryHandler(admin_create_code_prompt, pattern="^admin_create_code_prompt$"))
    application.add_handler(CallbackQueryHandler(admin_manage_admins, pattern="^admin_manage_admins$"))
    application.add_handler(CallbackQueryHandler(admin_view_workers, pattern="^admin_view_workers$"))
    application.add_handler(CallbackQueryHandler(admin_attack_summary, pattern="^admin_attack_summary$"))
    application.add_handler(CallbackQueryHandler(admin_attack_detailed, pattern="^admin_attack_detailed$"))

    application.add_handler(MessageHandler(filters.Regex("^(🚀 Test va o'quv platformasi|🚀 Платформа обучения|🚀 BIQS Mini App-ni ochish|🚀 Открыть BIQS Mini App)$"), start_command))
    application.add_handler(MessageHandler(filters.Regex("^(📊 Mening statistikam|📊 Моя статистика)$"), show_stats_handler))
    application.add_handler(MessageHandler(filters.Regex("^(👥 Mening jamoam .xodimlar.|👥 Моя команда .сотрудники.)$"), my_team_handler))
    application.add_handler(MessageHandler(filters.Regex("^(🏢 Mening rahbarlarim|🏢 Моё руководство)$"), my_management_handler))
    application.add_handler(MessageHandler(filters.Regex("^(👥 Mening sexim .Xodimlarim.|👥 Мой цех .Сотрудники.)$"), my_team_handler))
    application.add_handler(MessageHandler(filters.Regex("^(⚙️ Admin paneli|⚙️ Панель Администратора)$"), remove_old_admin_btn_handler))
    application.add_handler(MessageHandler(filters.Regex("^(👨‍💼 Создатель|👨‍💼 Yaratuvchi|👨‍💼 Asoschi)$"), founder_handler))
    application.add_handler(MessageHandler(filters.Regex("^(🆘 Техподдержка|🆘 Texnik yordam)$"), support_handler))
    
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(f"⚠️ Ошибка бота:\n{context.error}")
            except:
                pass
                
    application.add_error_handler(error_handler)

    # Security Inspection Fallback Handler
    async def global_fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await security_inspection_handler(update, context)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_text))

    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("newcode", newcode_command))
    application.add_handler(CommandHandler("addadmin", addadmin_command))
    application.add_handler(CommandHandler("workers", workers_command))
    application.add_handler(CommandHandler("stats", show_stats_handler))
    application.add_handler(CommandHandler("deleteuser", deleteuser_command))
    application.add_handler(CommandHandler("myteam", my_team_handler))
    application.add_handler(CommandHandler("sectors", sectors_stats_handler))
    application.add_handler(CommandHandler("lines", sectors_stats_handler))
    application.add_handler(CommandHandler("addbanned", addbanned_command))
    application.add_handler(CommandHandler("bannedlist", bannedlist_command))
    application.add_handler(CommandHandler("delbanned", delbanned_command))
    application.add_handler(CommandHandler("update_kb", update_keyboards_command))



    return application

if __name__ == "__main__":
    app = create_bot_app()
    print("Starting Telegram Bot Polling...")
    app.run_polling()
