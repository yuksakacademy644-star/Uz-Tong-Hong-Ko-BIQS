import asyncio
import logging
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


def get_main_keyboard(lang: str = 'ru', user_id: int = None):
    url = WEBAPP_URL
    is_admin = database.is_admin_or_superadmin(user_id) if user_id else False
    user = database.get_user(user_id) if user_id else None
    role = user.get("role", "worker") if user else "worker"

    if lang == 'uz':
        kb = [[KeyboardButton("🚀 BIQS Mini App-ni ochish", web_app=WebAppInfo(url=url))]]
        middle_row = []
        if is_admin:
            middle_row.append(KeyboardButton("⚙️ Admin paneli"))
        if role == 'master' or is_admin:
            middle_row.append(KeyboardButton("👥 Mening sexim (Xodimlarim)"))
        if middle_row:
            kb.append(middle_row)
        kb.append([KeyboardButton("👨‍💼 Yaratuvchi"), KeyboardButton("🆘 Texnik yordam")])
    else:
        kb = [[KeyboardButton("🚀 Открыть BIQS Mini App", web_app=WebAppInfo(url=url))]]
        middle_row = []
        if is_admin:
            middle_row.append(KeyboardButton("⚙️ Панель Администратора"))
        if role == 'master' or is_admin:
            middle_row.append(KeyboardButton("👥 Мой цех (Сотрудники)"))
        if middle_row:
            kb.append(middle_row)
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

# Master / Chief Team Monitoring Handler
async def my_team_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    if not db_user:
        await update.message.reply_text("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return
    
    lang = db_user.get("language", "uz")
    shop_name = db_user.get("shop_name", "СП Уз Тонг Хонг Ко")
    role = db_user.get("role", "worker")
    is_admin = database.is_admin_or_superadmin(user_id)
    
    if role != 'master' and not is_admin:
        await update.message.reply_text("⚠️ Bu bo'lim faqat sex boshliqlari (masterlar) va adminlar uchun mo'ljallangan.")
        return

    workers = database.get_shop_workers(shop_name)
    
    if lang == 'uz':
        if not workers:
            msg = f"🏭 <b>{shop_name}</b> sexi bo'yicha hali birorta ham xodim ro'yxatdan o'tmagan."
        else:
            msg = f"👥 <b>MENING SEXIM (XODIMLARIM) — {shop_name}</b>\n\n"
            msg += f"📊 <b>Jami xodimlar soni:</b> {len(workers)} ta\n\n"
            for idx, w in enumerate(workers, 1):
                badge = " 🌟 BIQS Mutaxassisi" if w['best_score'] >= 80 else ""
                msg += f"{idx}. <b>{w['full_name']}</b>{badge}\n"
                msg += f"   🎯 Eng yaxshi natija: <b>{round(w['best_score'])}%</b> | 📝 Testlar: {w['tests_completed']} marta\n"
                if w.get('latest_mistakes'):
                    import json
                    try:
                        m_list = json.loads(w['latest_mistakes'])
                        m_str = ", ".join(m_list) if isinstance(m_list, list) else str(w['latest_mistakes'])
                    except:
                        m_str = str(w['latest_mistakes'])
                    if m_str:
                        msg += f"   ⚠️ Oxirgi xatolari: <i>{m_str}</i>\n"
                msg += "\n"
    else:
        if not workers:
            msg = f"🏭 По цеху/сектору <b>{shop_name}</b> пока нет зарегистрированных работников."
        else:
            msg = f"👥 <b>МОЙ ЦЕХ (СОТРУДНИКИ) — {shop_name}</b>\n\n"
            msg += f"📊 <b>Всего сотрудников:</b> {len(workers)}\n\n"
            for idx, w in enumerate(workers, 1):
                badge = " 🌟 Эксперт BIQS" if w['best_score'] >= 80 else ""
                msg += f"{idx}. <b>{w['full_name']}</b>{badge}\n"
                msg += f"   🎯 Лучший результат: <b>{round(w['best_score'])}%</b> | 📝 Попыток: {w['tests_completed']}\n"
                if w.get('latest_mistakes'):
                    import json
                    try:
                        m_list = json.loads(w['latest_mistakes'])
                        m_str = ", ".join(m_list) if isinstance(m_list, list) else str(w['latest_mistakes'])
                    except:
                        m_str = str(w['latest_mistakes'])
                    if m_str:
                        msg += f"   ⚠️ Последние ошибки: <i>{m_str}</i>\n"
                msg += "\n"

    await update.message.reply_html(msg, reply_markup=get_main_keyboard(lang, user_id))

# Statistics Button Handler
async def show_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = database.get_user(user_id)
    lang = db_user.get("language", "ru") if db_user else "ru"

    stats = database.get_user_stats(user_id)
    best_score = round(stats.get("best_score") or 0)
    tests_count = stats.get("tests_count", 0)

    is_expert = best_score >= 80

    if lang == 'uz':
        status_str = "🌟 <b>STATUS: BIQS Mutaxassisi!</b>" if is_expert else "💼 <b>STATUS: Faol xodim</b>"
        text = (
            f"📊 <b>Sizning Natijalaringiz (Uz Tong Hong Ko):</b>\n\n"
            f"👤 <b>F.I.Sh:</b> {update.effective_user.full_name}\n"
            f"🎯 <b>Eng yaxshi natija:</b> {best_score}%\n"
            f"📝 <b>Topshirilgan testlar:</b> {tests_count} ta\n"
            f"{status_str}\n\n"
            f"💡 <i>80% va undan yuqori ball to'plagan xodimlar Uz Tong Hong Ko zavodining faxriy BIQS Mutaxassisi unvoniga ega bo'ladilar!</i>"
        )
    else:
        status_str = "🌟 <b>СТАТУС: Эксперт BIQS!</b>" if is_expert else "💼 <b>СТАТУС: Активный сотрудник</b>"
        text = (
            f"📊 <b>Ваша статистика (Уз Тонг Хонг Ко):</b>\n\n"
            f"👤 <b>ФИО:</b> {update.effective_user.full_name}\n"
            f"🎯 <b>Лучший результат:</b> {best_score}%\n"
            f"📝 <b>Пройдено тестов:</b> {tests_count}\n"
            f"{status_str}\n\n"
            f"💡 <i>Сотрудники, набравшие 80%+ баллов, получают почетный статус Эксперта BIQS СП Уз Тонг Хонг Ко!</i>"
        )

    await update.message.reply_html(text, reply_markup=get_webapp_inline_keyboard(lang))

# Change Language Handler
async def change_lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌐 <b>Выберите язык интерфейса / Tilni tanlang:</b>"
    await update.message.reply_html(text, reply_markup=get_language_inline_keyboard())

async def log_if_not_admin(user_id: int, command: str) -> bool:
    if not database.is_admin_or_superadmin(user_id):
        db_user = database.get_user(user_id)
        if db_user:
            database.log_attack(user_id, f"Попытка доступа к {command}")
        return True
    return False

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

    text = (
        f"⚙️ <b>ПАНЕЛЬ АДМИНИСТРАТОРА UZ TONG HONG KO</b>\n\n"
        f"👥 <b>Всего сотрудников:</b> {len(workers)}\n"
        f"🌟 <b>Экспертов BIQS (80%+):</b> {len(experts)}\n"
        f"🔑 <b>Активных кодов приглашения:</b> {len(codes)}\n"
        f"👔 <b>Назначенных админов:</b> {len(admins)}\n\n"
        f"📌 <b>Основные команды:</b>\n"
        f"• <code>/newcode KOD [ROLE] SHOP</code> — Создать код (role: worker/master)\n"
        f"• <code>/addadmin ID_OR_USERNAME [PERMS]</code> — Назначить админа\n"
        f"• <code>/workers</code> — Список всех работников\n"
        f"• <code>/myteam</code> — Просмотр работников своего цеха\n"
    )
    keyboard = [
        [
            InlineKeyboardButton("🔑 Создать код", callback_data="admin_create_code_prompt"),
            InlineKeyboardButton("👔 Админы", callback_data="admin_manage_admins")
        ],
        [
            InlineKeyboardButton("👥 Сотрудники", callback_data="admin_view_workers"),
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
            "⚠️ <b>Формат команды / Kod yaratish formati:</b>\n"
            "<code>/newcode &lt;KOD&gt; [worker|master] [SEX_NOMI]</code>\n\n"
            "<i>Misollar (Примеры):</i>\n"
            "• <b>Работник:</b> <code>/newcode WORKER1 worker 1-Sekh (Payvandlash)</code>\n"
            "• <b>Начальник:</b> <code>/newcode CHIEF1 master 1-Sekh (Payvandlash)</code>"
        )
        return

    code = args[0].upper()
    target_role = "worker"
    shop_startIndex = 1

    if len(args) > 1 and args[1].lower() in ["worker", "master", "xodim", "boshliq", "мастер", "работник"]:
        val = args[1].lower()
        if val in ["master", "boshliq", "мастер"]:
            target_role = "master"
        else:
            target_role = "worker"
        shop_startIndex = 2

    shop_name = " ".join(args[shop_startIndex:]) if len(args) > shop_startIndex else "СП Уз Тонг Хонг Ко"
    master_name = "Руководство"

    database.add_invite_code(code, shop_name, master_name, user_id, target_role=target_role)

    role_badge = "👨‍💼 Boshliq / Master" if target_role == 'master' else "🎯 Xodim / Worker"

    await update.message.reply_html(
        f"✅ <b>Kod muvaffaqiyatli yaratildi! / Код создан!</b>\n\n"
        f"🔑 <b>Kod:</b> <code>{code}</code>\n"
        f"👤 <b>Roli:</b> <code>{role_badge}</code>\n"
        f"🏭 <b>Sex/Sektor:</b> <code>{shop_name}</code>"
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
    await query.answer()
    workers = database.get_all_workers_admin()
    if not workers:
        await query.message.reply_text("Сотрудники пока не зарегистрированы.")
        return

    msg = "📋 <b>СПИСОК СОТРУДНИКОВ И РЕЗУЛЬТАТЫ:</b>\n\n"
    for idx, w in enumerate(workers, 1):
        is_top = w["best_score"] >= 80
        badge = " 🌟 <b>ЭКСПЕРТ BIQS</b>" if is_top else ""
        msg += f"{idx}. <b>{w['full_name']}</b> ({w.get('shop_name') or 'Sex'}){badge}\n"
        msg += f"   🎯 Natija: <b>{round(w['best_score'])}%</b> | {w['tests_completed']} попыток\n\n"

    await update.message.reply_html(msg)

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
    application.add_handler(MessageHandler(filters.Regex("^(👥 Mening sexim \(Xodimlarim\)|👥 Мой цех \(Сотрудники\))$"), my_team_handler))
    application.add_handler(MessageHandler(filters.Regex("^(⚙️ Admin paneli|⚙️ Панель Администратора)$"), admin_command))
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

    async def global_fallback_text(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        if isinstance(update, Update) and update.effective_message and update.effective_message.chat.type == "private":
            await update.effective_message.reply_html(
                "🔄 <b>Menyu yangilandi / Меню обновлено</b>\n"
                "Eski tugmalar o'chirildi. Iltimos, /start buyrug'ini yuboring.\n"
                "<i>Старые кнопки удалены. Пожалуйста, отправьте команду /start.</i>",
                reply_markup=ReplyKeyboardRemove()
            )

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_text))

    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("newcode", newcode_command))
    application.add_handler(CommandHandler("addadmin", addadmin_command))
    application.add_handler(CommandHandler("workers", workers_command))
    application.add_handler(CommandHandler("myteam", my_team_handler))
    application.add_handler(CommandHandler("update_kb", update_keyboards_command))

    return application

if __name__ == "__main__":
    app = create_bot_app()
    print("Starting Telegram Bot Polling...")
    app.run_polling()
