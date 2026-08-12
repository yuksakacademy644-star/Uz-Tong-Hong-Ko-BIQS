def get_biqs_questions():\n    return [
    {
        "id": 1,
        "question_uz": "Nomuvofiq (brak) mahsulot aniqlanganda har bir ish joyida nima bo'lishi va nima qilinishi shart (BIQS-01)?",
        "question_ru": "Что должно быть на каждом рабочем месте при обнаружении дефектной продукции (BIQS-01)?",
        "options_uz": [
            "Mahsulotni yashirib qo'yish",
            "Maxsus qizil rangli idish (Red Tag), yorliq va mahsulotni ajratish",
            "Keyingi operatsiyaga o'tkazib yuborish",
            "Faqat smena oxirida aytish"
        ],
        "options_ru": [
            "Спрятать деталь",
            "Красная зона (Red Tag), ярлык и немедленная изоляция брака",
            "Передать на следующую операцию",
            "Сообщить только в конце смены"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-01: Har bir ish joyida qizil idish va yorliq bo'lishi hamda nuqson darhol ajratilishi shart!",
        "explanation_ru": "BIQS-01: Брак немедленно изолируется в красную зону (Red Tag) с оформлением ярлыка."
    },
    {
        "id": 2,
        "question_uz": "Ko'p pog'onali audit (LA - Layered Audit) bo'yicha haftalik hisobot kimga taqdim etiladi (BIQS-02)?",
        "question_ru": "Кому предоставляется еженедельный отчет по многоуровневому аудиту LA (BIQS-02)?",
        "options_uz": [
            "Omborchiga",
            "Yuqori rahbariyatga",
            "Hech kimga",
            "Qo'shni tsexga"
        ],
        "options_ru": [
            "Кладовщику",
            "Высшему руководству завода",
            "Никому",
            "Соседнему цеху"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-02: LA monitoringi haftalik hisobot shaklida yuqori rahbariyatga taqdim etiladi.",
        "explanation_ru": "BIQS-02: Ведется мониторинг листов LA с еженедельным докладом высшему руководству."
    },
    {
        "id": 3,
        "question_uz": "PFMEA qachon qayta ko'rib chiqiladi va uning maqsadi nima (BIQS-03)?",
        "question_ru": "С какой целью проводится пересмотр PFMEA (BIQS-03)?",
        "options_uz": [
            "Oylik maoshni hisoblash uchun",
            "Xatarlar ballini (Risk Score) tushirish va choralarni belgilash",
            "Xomashyo buyurtma qilish uchun",
            "Bino tozaligini tekshirish uchun"
        ],
        "options_ru": [
            "Для расчета зарплаты",
            "Для снижения балла риска и назначения корректирующих мер",
            "Для заказа сырья",
            "Для проверки чистоты"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-03: PFMEA orqali jarayon xatarlari baholanib, risk balli pasaytirilishi kerak.",
        "explanation_ru": "BIQS-03: PFMEA используется для анализа рисков и снижения балла вероятности дефекта."
    },
    {
        "id": 4,
        "question_uz": "Iste'molchidan kelgan e'tirozlar (GCA, DRR, Reklamatsiya) qaysi hujjatda ko'rib chiqilishi shart (BIQS-04)?",
        "question_ru": "Где обязательно должны рассматриваться претензии клиентов (GCA, DRR) (BIQS-04)?",
        "options_uz": [
            "Faqat majlis bayonnomasida",
            "PFMEA xatarlar tahlilida",
            "Kasaba uyushmasida",
            "Hech qayerda"
        ],
        "options_ru": [
            "Только в протоколе собрания",
            "В анализе рисков PFMEA",
            "В профсоюзе",
            "Нигде"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-04: Iste'molchi e'tirozlari albatta PFMEA xatarlariga kiritilib tahlil qilinishi shart.",
        "explanation_ru": "BIQS-04: Все претензии потребителей должны быть включены в структуру рисков PFMEA."
    },
    {
        "id": 5,
        "question_uz": "Bypass Management (Aylanib o'tish) jarayoni qachon qo'llaniladi (BIQS-05)?",
        "question_ru": "При каких условиях применяется процесс Bypass Management (BIQS-05)?",
        "options_uz": [
            "Datchik buzilganda sir tutib ishlash uchun",
            "Ruxsatsiz ishlash uchun",
            "Standart yo'riqnoma asosida 100% qo'shimcha nazorat o'rnatish orqali",
            "Faqat tunda"
        ],
        "options_ru": [
            "Для скрытой работы при поломке датчика",
            "Для работы без разрешения",
            "По стандарту с введением 100% дополнительного контроля",
            "Только ночью"
        ],
        "correct": 2,
        "explanation_uz": "BIQS-05: Bypass faqat standart yo'riqnoma va qo'shimcha nazorat ostida bajariladi.",
        "explanation_ru": "BIQS-05: Процесс Bypass требует специальных инструкций и 100% контроля."
    },
    {
        "id": 6,
        "question_uz": "Xatolardan xoli qilishning (Poka-Yoke) 2-pog'onasi nimani nazarda tutadi (BIQS-06)?",
        "question_ru": "Что подразумевает 2-й уровень защиты от ошибок в BIQS-06?",
        "options_uz": [
            "Faqat vizual ko'zdan kechirish",
            "Markerlardan foydalanish",
            "Tekshiruv instrumentlari (Check Fix/Torque) orqali parametrni qayd etish",
            "TPM auditi"
        ],
        "options_ru": [
            "Только визуальный осмотр",
            "Использование маркеров",
            "Инструментальный контроль параметров (Check Fix/Torque)",
            "Аудит TPM"
        ],
        "correct": 2,
        "explanation_uz": "BIQS-06: 2-pog'ona bu maxsus o'lchov instrumentlari (Torque, Check Fix) orqali sifatni kafolatlash.",
        "explanation_ru": "BIQS-06: 2-й уровень — это замер параметров приборами (Torque/Check Fix)."
    },
    {
        "id": 7,
        "question_uz": "O'lchov asboblari va jihozlarning to'g'riligini tasdiqlovchi hujjat (BIQS-07)?",
        "question_ru": "Что подтверждает точность измерительных приборов (BIQS-07)?",
        "options_uz": [
            "Buxgalteriya schyoti",
            "Yaroqlilik yorlig'i va MSA tahlili (poverka)",
            "Zavod pasporti",
            "Buyruq"
        ],
        "options_ru": [
            "Счет-фактура",
            "Ярлык поверки и анализ MSA",
            "Паспорт завода",
            "Приказ"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-07: Barcha o'lchov vositalari poverkadan o'tganligi (yorliq) va MSA tahlili bo'lishi shart.",
        "explanation_ru": "BIQS-07: Все приборы должны иметь бирку о поверке и проходить анализ MSA."
    },
    {
        "id": 8,
        "question_uz": "Limitdan oshgan sifat muammolari qaysi jarayonga olib chiqiladi (BIQS-08)?",
        "question_ru": "На какой процесс выносятся проблемы качества, превысившие лимит (BIQS-08)?",
        "options_uz": [
            "Fast Response (Tezkor munosabat)",
            "Bayram tadbiri",
            "Kadrlar bo'limiga",
            "E'tiborsiz qoldiriladi"
        ],
        "options_ru": [
            "Fast Response (Оперативное реагирование)",
            "Праздничное мероприятие",
            "В отдел кадров",
            "Игнорируются"
        ],
        "correct": 0,
        "explanation_uz": "BIQS-08: Katta muammolar zudlik bilan Fast Response yig'ilishida ko'rib chiqiladi.",
        "explanation_ru": "BIQS-08: Крупные дефекты незамедлительно выносятся на стенд Fast Response."
    },
    {
        "id": 9,
        "question_uz": "PPSR jarayonining asosiy maqsadi nima (BIQS-09)?",
        "question_ru": "Какова главная цель процесса PPSR (BIQS-09)?",
        "options_uz": [
            "Ishchilarni ishdan bo'shatish",
            "Muammolarni yashirish",
            "Jamoani jalb etgan holda muammoni hujjatlashtirish va bartaraf etish (Eskalatsiya)",
            "Faqat rahbariyatni jazolash"
        ],
        "options_ru": [
            "Увольнение рабочих",
            "Скрытие проблем",
            "Командное решение проблем с документацией и эскалацией",
            "Только наказание руководства"
        ],
        "correct": 2,
        "explanation_uz": "BIQS-09: PPSR orqali muammolar jamoaviy hal qilinadi va eskalatsiya qilinadi.",
        "explanation_ru": "BIQS-09: Процесс PPSR направлен на командное устранение причин дефекта."
    },
    {
        "id": 10,
        "question_uz": "Sifat tekshiruvi hujjatlashtirilishining asosiy talabi nima (BIQS-10)?",
        "question_ru": "Каково главное требование к документированию проверок качества (BIQS-10)?",
        "options_uz": [
            "Istalgan daftarga yozish",
            "Belgilangan talab darajasida hujjatlashtirish va muammoda chora ko'rish",
            "Faqat yodda saqlash",
            "Kompyuterga yozib qo'yish"
        ],
        "options_ru": [
            "Запись в любую тетрадь",
            "Документирование по стандартам с принятием мер при отклонениях",
            "Только запоминание",
            "Запись в блокнот"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-10: Barcha sifat tekshiruvlari rasmiy tasdiqlangan hujjatlarga qayd qilinishi kerak.",
        "explanation_ru": "BIQS-10: Результаты проверок фиксируются в официальных бланках."
    },
    {
        "id": 11,
        "question_uz": "Standartlashtirilgan ish (SOS/JES) o'z ichiga nimalarni qamrab oladi (BIQS-11)?",
        "question_ru": "Что охватывает стандартизированная работа (SOS/JES) (BIQS-11)?",
        "options_uz": [
            "Faqat operatsiya vaqtini",
            "Xavfsizlik, sifat, operatsiya elementlari va vaqt talablarini",
            "Ishchining yoshini",
            "Faqat tushlik vaqtini"
        ],
        "options_ru": [
            "Только время операции",
            "Требования безопасности, качества, элементы работы и времени",
            "Возраст рабочего",
            "Только время обеда"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-11: SOS va JES kartalari xavfsizlik, sifat va vaqt bo'yicha aniq ketma-ketlikni belgilaydi.",
        "explanation_ru": "BIQS-11: Карты SOS/JES определяют безопасную, качественную и эффективную последовательность действий."
    },
    {
        "id": 12,
        "question_uz": "4M o'zgarishlar nazorati (4M Control) qaysi omillarni o'z ichiga oladi (BIQS-12)?",
        "question_ru": "Какие 4 фактора входят в управление изменениями 4M (BIQS-12)?",
        "options_uz": [
            "Odam, Jihoz(Mashina), Material, Jarayon",
            "Meva, Mashina, Maosh, Maktab",
            "Oila, Oshxona, Olov, Odob",
            "Faqat Odam va Maosh"
        ],
        "options_ru": [
            "Человек, Оборудование, Материал, Процесс (Method)",
            "Машина, Масло, Мотор, Мастер",
            "Офис, Отдел, Отчет, Отпуск",
            "Только Человек и Зарплата"
        ],
        "correct": 0,
        "explanation_uz": "BIQS-12: 4M — Odam (Man), Mashina (Machine), Material (Material), Jarayon (Method) o'zgarishlaridir.",
        "explanation_ru": "BIQS-12: 4M включает контроль изменений по Человеку, Оборудованию, Материалу и Процессу."
    },
    {
        "id": 13,
        "question_uz": "Sifat tekshiruv vositalarining yetarliligi va ulardan foydalanish qaysi elementda ko'rib chiqiladi (BIQS-13)?",
        "question_ru": "В каком элементе рассматривается достаточность и эффективность средств контроля (BIQS-13)?",
        "options_uz": [
            "BIQS-01",
            "BIQS-30",
            "BIQS-13",
            "BIQS-27"
        ],
        "options_ru": [
            "BIQS-01",
            "BIQS-30",
            "BIQS-13",
            "BIQS-27"
        ],
        "correct": 2,
        "explanation_uz": "BIQS-13: Sifatni tekshirish vositalari (shtangensirkul, shablonlar) yetarli va samarali bo'lishi kerak.",
        "explanation_ru": "BIQS-13: Оценка эффективности средств контроля и умения рабочих ими пользоваться."
    },
    {
        "id": 14,
        "question_uz": "Jarayon yoki detaldagi o'zgarishlarda qaysi blanka to'ldiriladi (BIQS-14)?",
        "question_ru": "Какой бланк заполняется при любых изменениях деталей или процессов на участке (BIQS-14)?",
        "options_uz": [
            "PTR blankasi va Breakpoint (ajratish nuqtasi) qayd etiladi",
            "Tabel varog'i",
            "Hech qanday blanka",
            "Ta'til arizasi"
        ],
        "options_ru": [
            "Заполняется бланк PTR и фиксируются точки Breakpoint",
            "Табель учета времени",
            "Никакие бланки",
            "Заявление на отпуск"
        ],
        "correct": 0,
        "explanation_uz": "BIQS-14: Har bir o'zgarishda PTR to'ldirilib, 4M doskasida Breakpoint qayd etiladi.",
        "explanation_ru": "BIQS-14: Изменения требуют оформления PTR и фиксации точек Breakpoint."
    },
    {
        "id": 15,
        "question_uz": "Ishlab chiqarishda favqulodda muammo aniqlanganda xabardor qilish tizimi (BIQS-15)?",
        "question_ru": "Как называется система оперативного оповещения о проблемах на линии (BIQS-15)?",
        "options_uz": [
            "FIFO tizimi",
            "ANDON tizimi (Xabar/chaqiruv)",
            "LPA auditi",
            "5S standarti"
        ],
        "options_ru": [
            "Система FIFO",
            "Система ANDON (Оповещение/Вызов)",
            "Аудит LPA",
            "Стандарт 5S"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-15: ANDON tizimi — muammo yuzaga kelganda liniyani to'xtatib ustani chaqirishni ta'minlaydi.",
        "explanation_ru": "BIQS-15: ANDON — это свето-звуковая система вызова мастера при проблемах."
    },
    {
        "id": 16,
        "question_uz": "Muammo limitdan oshganda kimlarga xabar berilishi kerak (BIQS-16)?",
        "question_ru": "Кому сообщается о проблеме при превышении лимитов эскалации (BIQS-16)?",
        "options_uz": [
            "Hech kimga",
            "Eskalatsiya jarayoni asosida yuqori rahbariyatga va barcha daxldorlarga",
            "Faqat xaridorga",
            "Faqat omborchiga"
        ],
        "options_ru": [
            "Никому",
            "Высшему руководству и ответственным лицам согласно процессу эскалации",
            "Только покупателю",
            "Только кладовщику"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-16: Muammo mezonidan oshsa, belgilangan tartibda rahbarlarga (eskalatsiya) xabar qilinadi.",
        "explanation_ru": "BIQS-16: Регламент эскалации требует вызова руководителей при превышении лимитов брака."
    },
    {
        "id": 17,
        "question_uz": "Vizual boshqaruv (Visual Management) standarti nima uchun kerak (BIQS-17)?",
        "question_ru": "Для чего нужны стандарты визуального менеджмента (BIQS-17)?",
        "options_uz": [
            "Sexni bezatish uchun",
            "NG va OK holatlarini yaqqol farqlash va ishni osonlashtirish uchun",
            "Devorlarni yashirish uchun",
            "Faqat komissiya uchun"
        ],
        "options_ru": [
            "Для украшения цеха",
            "Для наглядного разделения состояний OK и NG и упрощения работы",
            "Чтобы скрыть стены",
            "Только для комиссии"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-17: Vizual boshqaruv orqali ish joyidagi har qanday og'ish va nosozlik bir qarashda ko'rinadi.",
        "explanation_ru": "BIQS-17: Визуальный менеджмент позволяет с первого взгляда отличить норму (OK) от отклонения (NG)."
    },
    {
        "id": 18,
        "question_uz": "Sifat ko'rgazmali qo'llanmalari va o'zgarishlar qanday yetkaziladi (BIQS-18)?",
        "question_ru": "Как должны доводиться до сотрудников визуальные инструкции и изменения (BIQS-18)?",
        "options_uz": [
            "Xodimga qulay joyga o'rnatilib, samarali tarzda o'qitiladi",
            "Faqat direktor xonasida saqlanadi",
            "Guruhlarga WhatsApp orqali jo'natiladi",
            "Faqat og'zaki aytiladi"
        ],
        "options_ru": [
            "Устанавливаются в удобном месте на линии с проведением обучения",
            "Хранятся в кабинете директора",
            "Рассылаются в WhatsApp",
            "Только устно"
        ],
        "correct": 0,
        "explanation_uz": "BIQS-18: Barcha yo'riqnomalar ish joyida vizual ko'rinishda osilgan va xodim o'qitilgan bo'lishi shart.",
        "explanation_ru": "BIQS-18: Инструкции должны висеть прямо перед глазами оператора."
    },
    {
        "id": 19,
        "question_uz": "Jarayon nazorati uchun qaysi hujjatlar bir-biriga mos bo'lishi shart (BIQS-19)?",
        "question_ru": "Какие документы контроля процесса должны полностью соответствовать друг другу (BIQS-19)?",
        "options_uz": [
            "Faqat kadrlar ro'yxati",
            "Sifat boshqaruv rejasi (CP), Flowchart, FMEA, SOS/JES",
            "Oylik maosh jadvali",
            "Menyu va retsept"
        ],
        "options_ru": [
            "Только штатное расписание",
            "План контроля (CP), Flowchart, FMEA, SOS/JES",
            "График отпусков",
            "Меню в столовой"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-19: Texnologik jarayondagi barcha asosiy sifat hujjatlari (CP, FMEA, SOS) bir-biriga 100% mos kelishi kerak.",
        "explanation_ru": "BIQS-19: CP, FMEA и SOS — это связка документов, которые должны быть синхронизированы."
    },
    {
        "id": 20,
        "question_uz": "Ish joyida xodimning amaliy harakatlari qaysi hujjatga mosligini tekshirish kerak (BIQS-20)?",
        "question_ru": "Соответствие каким документам нужно проверять при оценке работы оператора на линии (BIQS-20)?",
        "options_uz": [
            "Shartnomaga",
            "SOS/JES, CheckList va Control Plan (CP) hujjatlariga",
            "Internet qoidalariga",
            "Do'stlarining maslahatiga"
        ],
        "options_ru": [
            "Договору",
            "Инструкциям SOS/JES, чек-листам и Плану контроля (CP)",
            "Правилам из интернета",
            "Советам коллег"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-20: Operator ishni faqat SOS va CheckList hujjatlariga asosan xatosiz bajarishi shart.",
        "explanation_ru": "BIQS-20: Выполнение операций проверяется на строгое соответствие SOS и чек-листам."
    },
    {
        "id": 21,
        "question_uz": "Kritik va xavfli texnologik nuqtalar (QCOS Torque/Weld) qanday nazorat qilinadi (BIQS-21)?",
        "question_ru": "Как контролируются критические и опасные точки техпроцесса (QCOS Torque/Weld) (BIQS-21)?",
        "options_uz": [
            "Belgilangan vaqtda SPC tahlil o'tkaziladi va qattiq nazorat qilinadi",
            "O'lchanmaydi",
            "Koz bilan chamalab qo'yiladi",
            "Yilda bir marta tekshiriladi"
        ],
        "options_ru": [
            "Проводится регулярный замер и анализ SPC (стат. контроль)",
            "Не измеряются",
            "Оцениваются на глаз",
            "Проверяются раз в год"
        ],
        "correct": 0,
        "explanation_uz": "BIQS-21: Payvand choki, qotirish momenti kabi kritik nuqtalar maxsus SPC orqali kuzatib boriladi.",
        "explanation_ru": "BIQS-21: Моменты затяжки и точки сварки критически важны для безопасности."
    },
    {
        "id": 22,
        "question_uz": "Ta'mirlash (Rework) operatsiyalari qay tartibda amalga oshiriladi (BIQS-22)?",
        "question_ru": "В каком порядке выполняются операции доработки/ремонта деталей (Rework) (BIQS-22)?",
        "options_uz": [
            "Istalgan joyda",
            "Alohida joyda, maxsus SOS/JES va malakali xodim (Flexibility chart) tomonidan",
            "Konveyer ustida to'xtatmay",
            "Sirtdan bo'yab qo'yish orqali"
        ],
        "options_ru": [
            "В любом месте",
            "В изолированной зоне обученным персоналом по специальной инструкции SOS",
            "Прямо на конвейере без остановки",
            "Скрытием дефекта"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-22: Rework (qayta ishlash) faqat ruxsat etilgan xodim tomonidan va alohida sektorda bajariladi.",
        "explanation_ru": "BIQS-22: Доработка деталей выполняется только обученным персоналом в специальной зоне."
    },
    {
        "id": 23,
        "question_uz": "Sifat muammolari haqida boshqa tsexlarga qanday xabar beriladi (BIQS-23)?",
        "question_ru": "Как смежные участки оповещаются о проблемах качества (BIQS-23)?",
        "options_uz": [
            "Hech qanday",
            "Oldinga va orqaga zudlik bilan Quality Alert (Sifat haqida ogohlantirish) orqali",
            "Faqat direktor orqali",
            "Ovoz karnayi orqali baqirib"
        ],
        "options_ru": [
            "Никак",
            "Двусторонним оперативным оповещением Quality Alert (Тревога по качеству)",
            "Только через директора",
            "Через громкоговоритель"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-23: Nuqson topilganda uni manbayi va qabul qiluvchisi Quality Alert (Containment) bilan ogohlantiriladi.",
        "explanation_ru": "BIQS-23: Quality Alert гарантирует, что брак не уйдет к клиенту и поставщик узнает о дефекте."
    },
    {
        "id": 24,
        "question_uz": "Xodimlarning operatsiyalarni bajarish malakasi (Flexibility chart) qanday ta'minlanadi (BIQS-24)?",
        "question_ru": "Как обеспечивается и контролируется квалификация рабочих (Flexibility chart) (BIQS-24)?",
        "options_uz": [
            "Hamma hamma ishni qiladi",
            "Maxsus JIT o'qitish va Flexibility chart orqali ruxsat berilganidan keyin",
            "Diplomga qarab",
            "Ustaning xohishiga qarab"
        ],
        "options_ru": [
            "Все делают всё",
            "Через обучение JIT и допуск согласно матрице квалификации (Flexibility chart)",
            "По наличию диплома",
            "По желанию мастера"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-24: Har bir xodim faqat o'ziga o'rgatilgan (JIT) va matritsada tasdiqlangan ishni bajara oladi.",
        "explanation_ru": "BIQS-24: Матрица навыков подтверждает, что рабочий обучен стандарту."
    },
    {
        "id": 25,
        "question_uz": "Ish joyida mahsulotni chang va kirdan himoya qilish tartibi qaysi elementga kiradi (BIQS-25)?",
        "question_ru": "К какому элементу относится защита продукции и рабочего места от пыли и загрязнений (BIQS-25)?",
        "options_uz": [
            "BIQS-25 (Tozalik va ifloslanishdan himoya)",
            "BIQS-10",
            "BIQS-01",
            "BIQS-30"
        ],
        "options_ru": [
            "BIQS-25 (Чистота и защита от загрязнений)",
            "BIQS-10",
            "BIQS-01",
            "BIQS-30"
        ],
        "correct": 0,
        "explanation_uz": "BIQS-25: Ish joyida detalga chang tushmasligi uchun tozalik standarti qat'iy ta'minlanishi zarur.",
        "explanation_ru": "BIQS-25: Поддержание идеальной чистоты для предотвращения дефектов внешнего вида."
    },
    {
        "id": 26,
        "question_uz": "Uskunalar sifatli ishlashi uchun nima profilaktika qilinadi (BIQS-26)?",
        "question_ru": "Какая профилактика применяется для безотказной работы оборудования (BIQS-26)?",
        "options_uz": [
            "Uskuna buzilgandagina tuzatiladi",
            "TPM (kundalik texnik xizmat) va PPR (rejali ta'mir) hujjatlari asosida nazorat qilinadi",
            "Ochib yopib turiladi",
            "Hech narsa qilinmaydi"
        ],
        "options_ru": [
            "Станок чинят только после поломки",
            "Контролируется через чек-листы TPM и графики планового ремонта (ППР)",
            "Просто выключают",
            "Ничего не делается"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-26: TPM operator tomonidan, PPR mexaniklar tomonidan vaqtida bajarilishi uskunani asraydi.",
        "explanation_ru": "BIQS-26: Регулярное обслуживание TPM/ППР предотвращает внезапные простои и брак."
    },
    {
        "id": 27,
        "question_uz": "FIFO qoidasi nima uchun muhim (BIQS-27)?",
        "question_ru": "Для чего критически важно соблюдение правила FIFO (BIQS-27)?",
        "options_uz": [
            "Chiroyli ko'rinish uchun",
            "Birinchi kelgan material birinchi ishlatilishi va eskirib qolmasligi uchun",
            "Omborchini qiynash uchun",
            "Oson olish uchun"
        ],
        "options_ru": [
            "Для красоты",
            "Чтобы материал, поступивший первым, расходовался первым и не портился",
            "Чтобы загрузить кладовщика",
            "Для удобства"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-27: FIFO (First-In, First-Out) zaxiralar yaroqlilik muddatini nazorat qilish kafolatidir.",
        "explanation_ru": "BIQS-27: FIFO предотвращает старение и порчу компонентов на складе."
    },
    {
        "id": 28,
        "question_uz": "Mahsulotlar qanday idish (tara) larda yetkazilishi shart (BIQS-28)?",
        "question_ru": "В какой таре должна поставляться и храниться продукция (BIQS-28)?",
        "options_uz": [
            "Karton qutilarda",
            "Istalgan topilgan idishda",
            "Faqat tasdiqlangan, maxsus yorliqli (birka) konteyner va taralarda (Min/Max bo'yicha)",
            "Yerda yoyib"
        ],
        "options_ru": [
            "В картонных коробках",
            "В любой доступной таре",
            "Только в утвержденной специализированной таре с бирками (по Min/Max)",
            "Навалом на полу"
        ],
        "correct": 2,
        "explanation_uz": "BIQS-28: Noto'g'ri tara mahsulot sifatiga zarar yetkazadi, shuning uchun faqat tasdiqlangan taralar ruxsat etiladi.",
        "explanation_ru": "BIQS-28: Использование нестандартной тары ведет к повреждению деталей."
    },
    {
        "id": 29,
        "question_uz": "Ta'minotchilardan (SUB) kelayotgan ehtiyot qismlar qanday nazorat qilinadi (BIQS-29)?",
        "question_ru": "Как контролируются компоненты, поступающие от субпоставщиков (BIQS-29)?",
        "options_uz": [
            "Tekshirilmaydi",
            "Kirish nazorati (IQC), sifat yorlig'i va BIQS 1-13 auditi orqali",
            "Faqat tarozi orqali",
            "Rangi orqali"
        ],
        "options_ru": [
            "Никак не проверяются",
            "Через входной контроль (IQC), маркировку и аудит по BIQS 1-13",
            "Только взвешиванием",
            "На глаз по цвету"
        ],
        "correct": 1,
        "explanation_uz": "BIQS-29: Kirib kelayotgan qismlar sifatli bo'lmas ekan, yakuniy mahsulot ham sifatli bo'lmaydi.",
        "explanation_ru": "BIQS-29: Строгий входной контроль IQC отсеивает брак от поставщиков."
    },
    {
        "id": 30,
        "question_uz": "Mehnat xavfsizligi va GMS PI qoidalari qaysi BIQS standartida yozilgan (BIQS-30)?",
        "question_ru": "В каком стандарте BIQS описаны требования безопасности и GMS PI (BIQS-30)?",
        "options_uz": [
            "BIQS-02",
            "BIQS-15",
            "BIQS-30 (Xavfsizlik SCOS)",
            "BIQS-12"
        ],
        "options_ru": [
            "BIQS-02",
            "BIQS-15",
            "BIQS-30 (Безопасность SCOS)",
            "BIQS-12"
        ],
        "correct": 2,
        "explanation_uz": "BIQS-30: Xavfsizlik har doim birinchi o'rinda! SCOS qoidalariga hamma amal qilishi shart.",
        "explanation_ru": "BIQS-30: Безопасность на первом месте. Выполнение инструкций SCOS обязательно для всех."
    }
]\n