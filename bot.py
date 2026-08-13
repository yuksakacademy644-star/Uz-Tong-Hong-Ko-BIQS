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


def get_main_keyboard(lang: str = 'ru'):
    url = WEBAPP_URL
    if lang == 'uz':
        kb = [
            [KeyboardButton("🚀 BIQS Mini App-ni ochish", web_app=WebAppInfo(url=url))],
            [KeyboardButton("🆘 Texnik yordam")]
        ]
    else:
        kb = [
            [KeyboardButton("🚀 Открыть BIQS Mini App", web_app=WebAppInfo(url=url))],
            [KeyboardButton("🆘 Техподдержка")]
        ]
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
    is_admin = user.id in config.ADMIN_IDS

    # ✅ Admin / Creator auto-bypass: Never ask Administrator for invite code!
    if not db_user and is_admin:
        database.create_user(
            telegram_id=user.id,
            full_name=user.full_name or user.first_name,
            username=user.username or "",
            phone="",
            invite_code="ADMIN",
            shop_name="Администрация",
            language="ru"
        )
        db_user = database.get_user(user.id)

    if db_user:
        lang = db_user.get("language", "ru")
        shop = db_user.get("shop_name", "Цех")
        master = db_user.get("master_name", "Мастер")

        if lang == 'uz':
            text = (
                f"Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
                f"🏭 <b>Sizning sexingiz:</b> {shop}\n"
                f"👨‍🏫 <b>Sizning ustangiz:</b> {master}\n\n"
                f"O'quv platformasi va BIQS testini ochish uchun pastdagi tugmani bosing 👇"
            )
        else:
            text = (
                f"Добро пожаловать, <b>{user.first_name}</b>!\n\n"
                f"🏭 <b>Ваш цех:</b> {shop}\n"
                f"👨‍🏫 <b>Ваш мастер:</b> {master}\n\n"
                f"Для открытия платформы обучения BIQS нажмите кнопку ниже 👇"
            )
        
        await update.message.reply_html(
            text,
            reply_markup=get_main_keyboard(lang)
        )
        return ConversationHandler.END
    else:
        context.user_data["full_name"] = user.full_name or user.first_name
        context.user_data["username"] = user.username or ""
        
        msg_text = (
            "Ассалому алейкум, добро пожаловать в наш бот! 👋\n"
            "Этот бот создан, чтобы наши работники знали стандарты по качеству BIQS.\n\n"
            "🔑 <b>Введите код приглашения от администратора:</b>\n"
            "<i>(Administratorning kirish kodini kiriting:)</i>"
        )
        await update.message.reply_html(msg_text, reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_INVITE_CODE

# Invite Code Verification
async def process_invite_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_text = update.message.text.strip().upper()
    code_data = database.get_invite_code(code_text)

    if not code_data:
        await update.message.reply_html(
            "❌ <b>Неверный код приглашения!</b>\n"
            "Пожалуйста, проверьте код и введите его снова:\n\n"
            "<i>Xato kirish kodi! Qayta kiriting:</i>",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_FOR_INVITE_CODE

    context.user_data["invite_code"] = code_text
    context.user_data["shop_name"] = code_data["shop_name"]
    
    await update.message.reply_html(
        "✅ <b>Код принят!</b>\n\n"
        "👤 Пожалуйста, введите ваше <b>Имя и Фамилию</b>:\n"
        "<i>(Iltimos, Ism va Familiyangizni kiriting:)</i>"
    )
    return WAITING_FOR_FULL_NAME

async def process_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    
    text = "🌐 <b>Выберите язык интерфейса / Tilni tanlang:</b>"
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

        database.create_user(
            telegram_id=user_id,
            full_name=full_name,
            username=username,
            phone=phone,
            invite_code=invite_code,
            shop_name=shop_name,
            language=lang
        )

    if lang == 'uz':
        confirm_text = (
            f"Ассалому алейкум, добро пожаловать в наш бот!\n"
            f"Assalomu alaykum, botimizga xush kelibsiz!\n\n"
            f"🚀 Platformani ochish uchun pastdagi menyudan foydalaning."
        )
    else:
        confirm_text = (
            f"Ассалому алейкум, добро пожаловать в наш бот!\n"
            f"Assalomu alaykum, botimizga xush kelibsiz!\n\n"
            f"🚀 Для открытия платформы используйте меню ниже."
        )

    # Delete the inline language selection message to clean up the chat
    try:
        await query.message.delete()
    except:
        pass

    # Send final welcome text with bottom menu reply keyboard
    await context.bot.send_message(
        chat_id=user_id,
        text=confirm_text,
        reply_markup=get_main_keyboard(lang)
    )

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
    if user_id not in config.ADMIN_IDS:
        db_user = database.get_user(user_id)
        if db_user:
            database.log_attack(user_id, f"Попытка доступа к {command}")
        return True
    return False

# Admin Panel Handler (/admin)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await log_if_not_admin(user_id, "/admin"):
        return

    codes = database.get_all_invite_codes()
    workers = database.get_all_workers_admin()
    experts = [w for w in workers if w["best_score"] >= 80]

    shop_stats = database.get_shop_statistics()
    best_shop = shop_stats[0] if shop_stats else None
    worst_shop = sorted(shop_stats, key=lambda x: x["total_mistakes"], reverse=True)[0] if shop_stats else None

    stats_msg = "📊 <b>Статистика по линиям (цехам):</b>\n"
    if best_shop:
        stats_msg += f"🏆 <b>Лучшая линия:</b> {best_shop['shop_name']} ({best_shop['master_name']}) — Ср. балл: {round(best_shop['avg_score'] or 0)}%\n"
    if worst_shop:
        stats_msg += f"⚠️ <b>Линия с ошибками:</b> {worst_shop['shop_name']} ({worst_shop['master_name']}) — Ошибок: {worst_shop['total_mistakes'] or 0}\n"

    text = (
        f"⚙️ <b>ПАНЕЛЬ АДМИНИСТРАТОРА UZ TONG HONG KO</b>\n\n"
        f"👥 <b>Всего сотрудников в системе:</b> {len(workers)}\n"
        f"🌟 <b>Экспертов BIQS (80%+):</b> {len(experts)}\n"
        f"🔑 <b>Активных кодов приглашения:</b> {len(codes)}\n\n"
        f"{stats_msg}\n"
        f"📌 <b>Команды Администратора:</b>\n"
        f"• <code>/newcode KOD SHOP MASTER</code> — Создать код\n"
        f"• <code>/workers</code> — Показать список сотрудников\n"
    )
    keyboard = [
        [InlineKeyboardButton("🛡 Атака", callback_data="admin_attack_summary")],
        [InlineKeyboardButton("🔍 Атака детально", callback_data="admin_attack_detailed")],
        [InlineKeyboardButton("📢 Объявления", callback_data="admin_broadcast_prompt")]
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
            await update.message.reply_photo(photo=photo, caption=text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_html(text)

# Force Keyboard Update for ALL users (admin only — run once)
async def update_keyboards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await log_if_not_admin(user_id, "/update_kb"):
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
                reply_markup=get_main_keyboard(lang)
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
    lang = db_user.get("language", "ru") if db_user else "ru"

    if lang == 'uz':
        text = (
            "🆘 <b>Texnik Yordam — СП Уз Тонг Хонг Ко</b>\n\n"
            "📞 <b>Telefon:</b> <code>+998507775152</code>\n\n"
            "⚠️ <b>Diqqat!</b>\n"
            "<i>Iltimos, mayda savollar uchun qo'ng'iroq qilmang.\n"
            "Faqat haqiqiy va jiddiy muammolar bo'lganda murojaat qiling.</i>\n\n"
            "🕐 Ish vaqti: <b>Dushanba – Juma, 09:00 – 18:00</b>"
        )
    else:
        text = (
            "🆘 <b>Техническая поддержка — СП Уз Тонг Хонг Ко</b>\n\n"
            "📞 <b>Телефон:</b> <code>+998507775152</code>\n\n"
            "⚠️ <b>Внимание!</b>\n"
            "<i>Пожалуйста, не звоните по мелочам.\n"
            "Обращайтесь только при реальных и серьёзных вопросах.</i>\n\n"
            "🕐 Рабочее время: <b>Пн – Пт, 09:00 – 18:00</b>"
        )

    await update.message.reply_html(text)

# Admin Command: /newcode
async def newcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await log_if_not_admin(user_id, "/newcode"):
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_html(
            "⚠️ <b>Формат команды:</b>\n"
            "<code>/newcode &lt;КОД&gt; &lt;ЦЕХ&gt; &lt;МАСТЕР&gt;</code>\n\n"
            "<i>Пример:</i> <code>/newcode UZTH-SHOP4 4-Цех Мастер_Алиев</code>"
        )
        return

    code = args[0].upper()
    shop_name = args[1]
    master_name = " ".join(args[2:])

    database.add_invite_code(code, shop_name, master_name, user_id)

    await update.message.reply_html(
        f"✅ <b>Код успешно создан!</b>\n\n"
        f"🔑 <b>Код:</b> <code>{code}</code>\n"
        f"🏭 <b>Цех:</b> {shop_name}\n"
        f"👨‍🏫 <b>Мастер:</b> {master_name}"
    )

# Admin Command: /workers
async def workers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await log_if_not_admin(user_id, "/workers"):
        return

    workers = database.get_all_workers_admin()
    if not workers:
        await update.message.reply_text("Сотрудники пока не зарегистрированы.")
        return

    msg = "📋 <b>СПИСОК СОТРУДНИКОВ И РЕЗУЛЬТАТЫ:</b>\n\n"
    for idx, w in enumerate(workers, 1):
        is_top = w["best_score"] >= 80
        badge = " 🌟 <b>ЭКСПЕРТ BIQS</b>" if is_top else ""
        msg += f"{idx}. <b>{w['full_name']}</b>{badge}\n"
        msg += f"   🏭 {w['shop_name']} ({w['master_name']})\n"
        msg += f"   🎯 Natija: <b>{round(w['best_score'])}%</b> | {w['tests_completed']} попыток\n\n"

    await update.message.reply_html(msg)

async def admin_attack_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await log_if_not_admin(query.from_user.id, "Кнопка 'Атака' (Сводка)"):
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
    if await log_if_not_admin(query.from_user.id, "Кнопка 'Атака детально'"):
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
    if await log_if_not_admin(query.from_user.id, "Кнопка 'Объявления'"):
        return
    await query.message.reply_html(
        "📢 <b>Рассылка объявлений</b>\n\n"
        "Отправьте текст объявления, которое будет разослано всем зарегистрированным сотрудникам.\n"
        "<i>Для отмены нажмите /cancel</i>"
    )
    return WAITING_FOR_BROADCAST

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await log_if_not_admin(user_id, "Отправка объявления"):
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
        # Webhook mode: Updater is NOT needed — Telegram pushes updates directly.
        # This also avoids the Python 3.14 __slots__ bug in PTB 20.6's Updater.
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
    application.add_handler(CallbackQueryHandler(admin_attack_summary, pattern="^admin_attack_summary$"))
    application.add_handler(CallbackQueryHandler(admin_attack_detailed, pattern="^admin_attack_detailed$"))

    # Clean handlers — only Mini App & Tech Support buttons allowed
    application.add_handler(MessageHandler(filters.Regex("^(🚀 Test va o'quv platformasi|🚀 Платформа обучения|🚀 BIQS Mini App-ni ochish|🚀 Открыть BIQS Mini App)$"), start_command))
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
    application.add_handler(CommandHandler("workers", workers_command))
    application.add_handler(CommandHandler("update_kb", update_keyboards_command))

    return application

if __name__ == "__main__":
    app = create_bot_app()
    print("Starting Telegram Bot Polling...")
    app.run_polling()
