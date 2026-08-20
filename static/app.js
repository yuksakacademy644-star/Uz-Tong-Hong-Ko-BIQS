// СП Уз Тонг Хонг Ко BIQS Telegram Mini App JavaScript Engine

// Telegram WebApp SDK Initialization
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
    tg.ready();
    tg.expand();
}

// Global State
let currentLang = 'ru'; // 'ru' or 'uz'
let userTelegramId = 0; // Default to 0 (unauthorized)
let userInfo = null;
let biqsElements = [];
let quizQuestions = [];

let currentQuestionIndex = 0;
let quizScore = 0;
let quizMistakes = [];
let quizTimerInterval = null;
let timeRemaining = 600; // 10 minutes in seconds
let userAnswers = [];

// Internationalization Dictionary (i18n)
const i18n = {
    ru: {
        nav_elements: "Стандарты (30)",
        nav_quiz: "Тестирование",
        nav_leaderboard: "Рейтинг",
        nav_my_team: "Мой цех",
        elements_title: "30 Элементов Качества BIQS",
        elements_subtitle: "Официальные стандарты качества СП Уз Тонг Хонг Ко",
        search_placeholder: "Поиск элемента BIQS...",
        quiz_welcome_title: "Тестирование на знание BIQS",
        quiz_welcome_desc: "Пройдите официальное тестирование из 10 вопросов на знание 30 элементов качества BIQS СП Уз Тонг Хонг Ко!",
        quiz_time_limit: "10 Минут",
        quiz_time_label: "Время",
        quiz_questions_label: "Количество",
        quiz_pass_label: "Проходной балл",
        start_test_btn: "Начать Тест",
        question: "Вопрос",
        explanation: "Пояснение:",
        next_question: "Следующий вопрос",
        try_again: "Пройти снова",
        view_leaderboard: "Посмотреть рейтинг",
        promo_title: "Высокий результат!",
        promo_desc: "Вы отлично знаете стандарты качества BIQS СП Уз Тонг Хонг Ко!",
        leaderboard_title: "Рейтинг Специалистов",
        leaderboard_subtitle: "Лучшие сотрудники завода по результатам тестов BIQS",
        sector_stats_title: "Статистика по участкам и линиям",
        filter_all_sectors: "🌐 Все участки и линии (Все цеха)",
        no_tests_yet: "Ещё не проходил",
        my_stats_title: "Моя статистика",
        best_result: "Лучший результат",
        tests_passed: "Пройдено тестов",
        avg_result: "Средний балл",
        rank_worker: "Рабочий",
        rank_nachalnik: "Начальник цеха",
        rank_master: "Мастер участка",
        rank_brigadier: "Бригадир",
        rank_quality: "Инженер по качеству",
        rank_director: "Руководство",
        rank_admin: "Администратор",
        rank_office_candidate: "Эксперт BIQS ⭐"
    },
    uz: {
        nav_elements: "Standartlar (30)",
        nav_quiz: "Test Sinov",
        nav_leaderboard: "Reyting",
        nav_my_team: "Mening Sexim",
        elements_title: "30 ta BIQS Sifat Elementlari",
        elements_subtitle: "Uz Tong Hong Ko korxonasining rasmiy sifat standartlari",
        search_placeholder: "BIQS elementini qidirish...",
        quiz_welcome_title: "BIQS bo'yicha bilimni sinash",
        quiz_welcome_desc: "Uz Tong Hong Ko korxonasining 30 ta BIQS sifat elementlari bo'yicha 10 ta savoldan iborat rasmiy testdan o'ting!",
        quiz_time_limit: "10 Daqiqa",
        quiz_time_label: "Vaqt",
        quiz_questions_label: "Soni",
        quiz_pass_label: "O'tish balii",
        start_test_btn: "Testni Boshlash",
        question: "Savol",
        explanation: "Izoh:",
        next_question: "Keyingi savol",
        try_again: "Qayta topshirish",
        view_leaderboard: "Reytingni ko'rish",
        promo_title: "Yuqori natija!",
        promo_desc: "Siz Uz Tong Hong Ko BIQS sifat standartlarini mukammal bilasiz!",
        leaderboard_title: "Mutaxassislar Reytingi",
        leaderboard_subtitle: "BIQS test natijalari bo'yicha zavodning eng yaxshi xodimlari",
        sector_stats_title: "Bo'limlar va liniyalar statistikasi",
        filter_all_sectors: "🌐 Barcha bo'lim va liniyalar",
        no_tests_yet: "Hali topshirmagan",
        my_stats_title: "Mening statistikaim",

        best_result: "Eng yaxshi natija",
        tests_passed: "Topshirilgan testlar",
        avg_result: "O'rtacha ball",
        rank_worker: "Ishchi",
        rank_nachalnik: "Sex Boshlig'i",
        rank_master: "Master (Usta)",
        rank_brigadier: "Brigadir",
        rank_quality: "Sifat nazorati",
        rank_director: "Rahbariyat",
        rank_admin: "Administrator",
        rank_office_candidate: "BIQS Eksperti ⭐"
    }

};

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
    // Extract Telegram User Data
    const isLocalhost = window.location.hostname === 'localhost' || 
                        window.location.hostname === '127.0.0.1' || 
                        window.location.hostname.startsWith('192.168.');
                        
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        userTelegramId = tg.initDataUnsafe.user.id;
    } else if (isLocalhost) {
        userTelegramId = 5543183063; // Fallback to Admin ID ONLY for browser dev testing
    } else {
        userTelegramId = 0; // Force 0 on production if not inside Telegram
    }

    initTabs();
    initLanguage();
    fetchUserInfo();
    fetchElements();
    fetchQuestions();
    fetchLeaderboard();

    // Event listeners
    document.getElementById("langToggleBtn").addEventListener("click", toggleLanguage);
    document.getElementById("elementSearchInput").addEventListener("input", filterElements);
    document.getElementById("startQuizBtn").addEventListener("click", startQuiz);
    document.getElementById("nextQuestionBtn").addEventListener("click", nextQuestion);
    document.getElementById("restartQuizBtn").addEventListener("click", resetQuiz);
    document.getElementById("goLeaderboardBtn").addEventListener("click", () => switchTab("leaderboardTab"));
    if (document.getElementById("sectorFilterSelect")) {
        document.getElementById("sectorFilterSelect").addEventListener("change", (e) => fetchLeaderboard(e.target.value));
    }
    document.getElementById("createCodeForm").addEventListener("submit", handleCreateCode);
    if (document.getElementById("addAdminForm")) {
        document.getElementById("addAdminForm").addEventListener("submit", handleAddAdmin);
    }

});

// Tab Navigation
function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    const activePane = document.getElementById(tabId);

    if (activeBtn) activeBtn.classList.add("active");
    if (activePane) activePane.classList.add("active");

    if (tabId === "leaderboardTab") fetchLeaderboard();
    if (tabId === "myTeamTab") fetchMyTeamData();
    if (tabId === "adminTab") fetchAdminData();
}

// Language Switching
function initLanguage() {
    updateLanguageUI();
}

function toggleLanguage() {
    currentLang = currentLang === 'ru' ? 'uz' : 'ru';
    updateLanguageUI();
    renderElements();
    renderLeaderboard();
    if (quizQuestions.length > 0) renderQuestion();
}

function updateLanguageUI() {
    document.getElementById("currentLangFlag").textContent = currentLang === 'ru' ? '🇷🇺' : '🇺🇿';
    document.getElementById("currentLangCode").textContent = currentLang.toUpperCase();

    // Translate DOM elements with data-i18n attributes
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (i18n[currentLang][key]) {
            el.textContent = i18n[currentLang][key];
        }
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (i18n[currentLang][key]) {
            el.placeholder = i18n[currentLang][key];
        }
    });
}

// User Info Fetching
async function fetchUserInfo() {
    try {
        const res = await fetch(`/api/user_info?telegram_id=${userTelegramId}`);
        if (res.ok) {
            userInfo = await res.json();
            
            if (userInfo.error === "not_registered") {
                if (userInfo.is_admin) {
                    userInfo = {
                        full_name: "Администратор",
                        shop_name: "Управление",
                        phone: "Admin",
                        role: "superadmin",
                        is_admin: true,
                        language: "ru"
                    };
                } else {
                    document.getElementById("unregisteredOverlay").classList.remove("hidden");
                    document.getElementById("app").style.display = "none";
                    return;
                }
            }

            document.getElementById("userFullName").textContent = userInfo.full_name || "Сотрудник Уз Тонг Хонг Ко";
            document.getElementById("shopNameText").textContent = userInfo.shop_name || "Цех #1";
            document.getElementById("masterNameText").textContent = userInfo.phone || "-";

            // Update Badge role text
            const rankText = document.getElementById("rankBadgeText");
            if (rankText) {
                let roleKey = 'rank_worker';
                if (userInfo.role === 'nachalnik') roleKey = 'rank_nachalnik';
                else if (userInfo.role === 'master') roleKey = 'rank_master';
                else if (userInfo.role === 'brigadier') roleKey = 'rank_brigadier';
                else if (userInfo.role === 'quality') roleKey = 'rank_quality';
                else if (userInfo.role === 'director') roleKey = 'rank_director';
                else if (userInfo.is_admin || userInfo.role === 'admin' || userInfo.role === 'superadmin') roleKey = 'rank_admin';
                
                rankText.textContent = i18n[currentLang][roleKey] || userInfo.role;
            }

            if (userInfo.language) {
                currentLang = userInfo.language;
                updateLanguageUI();
            }

            // If Nachalnik, Master, Brigadier, Quality, Director, or Admin, show My Team Tab
            const canViewTeam = ['nachalnik', 'master', 'brigadier', 'quality', 'director', 'admin', 'superadmin'].includes(userInfo.role) || userInfo.is_admin;
            if (canViewTeam) {
                const teamBtn = document.getElementById("myTeamTabBtn");

                if (teamBtn) teamBtn.classList.remove("hidden");
            }

            // If Admin, show Admin Tab
            if (userInfo.is_admin) {
                const adminBtn = document.getElementById("adminTabBtn");
                if (adminBtn) adminBtn.classList.remove("hidden");
            }
        }
    } catch (e) {
        console.warn("Using offline user fallback context", e);
    }
}

// Fetch 30 BIQS Elements
async function fetchElements() {
    try {
        const res = await fetch('/api/elements');
        biqsElements = await res.json();
        renderElements();
    } catch (e) {
        console.error("Error fetching elements", e);
    }
}

function renderElements(filterText = "") {
    const grid = document.getElementById("elementsGrid");
    grid.innerHTML = "";

    const filtered = biqsElements.filter(el => {
        const title = currentLang === 'ru' ? el.title_ru : el.title_uz;
        const desc = currentLang === 'ru' ? el.desc_ru : el.desc_uz;
        const text = `${el.code} ${title} ${desc}`.toLowerCase();
        return text.includes(filterText.toLowerCase());
    });

    if (filtered.length === 0) {
        grid.innerHTML = `<div class="no-results" style="text-align:center; padding: 20px; color: var(--text-muted);">Элементы не найдены</div>`;
        return;
    }

    filtered.forEach(el => {
        const card = document.createElement("div");
        card.className = "element-card";
        
        const title = currentLang === 'ru' ? el.title_ru : el.title_uz;
        const desc = currentLang === 'ru' ? el.desc_ru : el.desc_uz;

        card.innerHTML = `
            <div class="element-header">
                <span class="element-code-badge">${el.code}</span>
                <span class="element-icon-symbol">${el.icon || '🛡️'}</span>
            </div>
            <h4 class="element-title">${title}</h4>
            <p class="element-desc">${desc}</p>
        `;

        grid.appendChild(card);
    });
}

function filterElements(e) {
    renderElements(e.target.value);
}

// Fetch Quiz Questions
async function fetchQuestions() {
    try {
        const res = await fetch('/api/quiz');
        quizQuestions = await res.json();
    } catch (e) {
        console.error("Error fetching quiz questions", e);
    }
}

// Interactive Quiz System
function startQuiz() {
    currentQuestionIndex = 0;
    quizScore = 0;
    userAnswers = [];
    quizMistakes = [];
    timeRemaining = 600;

    document.getElementById("quizStartScreen").classList.add("hidden");
    document.getElementById("quizResultScreen").classList.add("hidden");
    document.getElementById("quizActiveScreen").classList.remove("hidden");

    startTimer();
    renderQuestion();
}

function startTimer() {
    clearInterval(quizTimerInterval);
    updateTimerDisplay();

    quizTimerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining <= 0) {
            clearInterval(quizTimerInterval);
            finishQuiz();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const mins = Math.floor(timeRemaining / 60);
    const secs = timeRemaining % 60;
    document.getElementById("timerText").textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function renderQuestion() {
    if (currentQuestionIndex >= quizQuestions.length) {
        finishQuiz();
        return;
    }

    const q = quizQuestions[currentQuestionIndex];
    document.getElementById("currentQuestionNum").textContent = currentQuestionIndex + 1;
    document.getElementById("totalQuestionsNum").textContent = quizQuestions.length;

    const progressPercent = ((currentQuestionIndex + 1) / quizQuestions.length) * 100;
    document.getElementById("quizProgressFill").style.width = `${progressPercent}%`;

    const questionText = currentLang === 'ru' ? q.question_ru : q.question_uz;
    const options = currentLang === 'ru' ? q.options_ru : q.options_uz;

    document.getElementById("questionText").textContent = questionText;
    document.getElementById("explanationBox").classList.add("hidden");
    document.getElementById("nextQuestionBtn").classList.add("hidden");

    const optionsList = document.getElementById("optionsList");
    optionsList.innerHTML = "";

    options.forEach((opt, idx) => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.innerHTML = `<span>${opt}</span> <i class="fa-regular fa-circle"></i>`;
        btn.addEventListener("click", () => selectOption(idx, q.correct, btn));
        optionsList.appendChild(btn);
    });
}

function selectOption(selectedIndex, correctIndex, selectedBtn) {
    const allBtns = document.querySelectorAll(".option-btn");
    allBtns.forEach(btn => btn.disabled = true);

    const q = quizQuestions[currentQuestionIndex];
    const isCorrect = selectedIndex === correctIndex;

    if (isCorrect) {
        quizScore++;
        selectedBtn.classList.add("correct");
        selectedBtn.querySelector("i").className = "fa-solid fa-circle-check";
    } else {
        selectedBtn.classList.add("wrong");
        selectedBtn.querySelector("i").className = "fa-solid fa-circle-xmark";
        // Highlight correct option
        allBtns[correctIndex].classList.add("correct");
        allBtns[correctIndex].querySelector("i").className = "fa-solid fa-circle-check";
        
        // Track mistake
        const explanationPrefix = q.explanation_ru.split(':')[0]; // Extracts "BIQS-XX"
        quizMistakes.push(explanationPrefix);
    }

    // Show explanation
    const explanationText = currentLang === 'ru' ? q.explanation_ru : q.explanation_uz;
    document.getElementById("explanationText").textContent = explanationText;
    document.getElementById("explanationBox").classList.remove("hidden");

    // Show Next Button
    document.getElementById("nextQuestionBtn").classList.remove("hidden");
}

function nextQuestion() {
    currentQuestionIndex++;
    if (currentQuestionIndex < quizQuestions.length) {
        renderQuestion();
    } else {
        finishQuiz();
    }
}

async function finishQuiz() {
    clearInterval(quizTimerInterval);

    document.getElementById("quizActiveScreen").classList.add("hidden");
    document.getElementById("quizResultScreen").classList.remove("hidden");

    const percentage = Math.round((quizScore / quizQuestions.length) * 100);
    const timeTaken = 600 - timeRemaining;

    document.getElementById("resultScorePercent").textContent = `${percentage}%`;
    document.getElementById("resultScoreRatio").textContent = `${quizScore} / ${quizQuestions.length}`;

    const promoBanner = document.getElementById("promotionBanner");

    if (percentage >= 80) {
        document.getElementById("resultTitle").textContent = currentLang === 'ru' ? "Отличный результат!" : "Ajoyib Natija!";
        document.getElementById("resultMessage").textContent = currentLang === 'ru' 
            ? "Вы превосходно знаете стандарты BIQS СП Уз Тонг Хонг Ко." 
            : "Siz Uz Tong Hong Ko BIQS standartlarini mukammal bilasiz.";
        promoBanner.classList.remove("hidden");
    } else {
        document.getElementById("resultTitle").textContent = currentLang === 'ru' ? "Тест завершен" : "Test Yakunlandi";
        document.getElementById("resultMessage").textContent = currentLang === 'ru' 
            ? "Рекомендуем изучить 30 элементов BIQS и пройти тест снова." 
            : "30 ta BIQS elementlarini qayta o'rganib, testni takroran topshirishingizni maslahat beramiz.";
        promoBanner.classList.add("hidden");
    }

    // Submit result to server
    try {
        await fetch('/api/quiz/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_telegram_id: userTelegramId,
                score: quizScore,
                total_questions: quizQuestions.length,
                percentage: percentage,
                time_taken_seconds: timeTaken,
                mistakes: quizMistakes
            })
        });

        fetchUserInfo();
    } catch (e) {
        console.error("Error submitting test results", e);
    }
}

function resetQuiz() {
    startQuiz();
}

// Fetch Leaderboard & Sector Stats
async function fetchLeaderboard(selectedShop = 'all') {
    try {
        const url = selectedShop && selectedShop !== 'all' 
            ? `/api/leaderboard?user_telegram_id=${userTelegramId}&shop_name=${encodeURIComponent(selectedShop)}`
            : `/api/leaderboard?user_telegram_id=${userTelegramId}`;
        const res = await fetch(url);
        const data = await res.json();
        
        // Render stats summary
        if (data.my_stats) {
            document.getElementById("myBestScore").textContent = `${Math.round(data.my_stats.best_score || 0)}%`;
            document.getElementById("myTestsCount").textContent = data.my_stats.tests_count || 0;
            document.getElementById("myAvgScore").textContent = `${Math.round(data.my_stats.avg_score || 0)}%`;
        }

        if (data.sector_stats) {
            renderSectorStats(data.sector_stats);
            populateSectorFilterSelect(data.sector_stats, selectedShop);
        }

        renderLeaderboard(data.leaderboard || []);
    } catch (e) {
        console.error("Error fetching leaderboard", e);
    }
}

function renderSectorStats(sectors = []) {
    const grid = document.getElementById("sectorStatsGrid");
    if (!grid) return;
    grid.innerHTML = "";

    if (sectors.length === 0) {
        grid.innerHTML = `<div style="font-size:11px; color:var(--text-muted);">Участки пока не зарегистрированы</div>`;
        return;
    }

    sectors.forEach(s => {
        const avg = s.avg_score || 0;
        let colorStyle = avg >= 80 ? 'color:#10b981;' : (avg >= 60 ? 'color:#f59e0b;' : 'color:#ef4444;');
        const card = document.createElement("div");
        card.style.cssText = "background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:8px 10px; cursor:pointer; transition:all 0.2s ease;";
        card.onmouseover = () => { card.style.borderColor = 'var(--accent-blue)'; card.style.background = 'rgba(0,136,204,0.08)'; };
        card.onmouseout = () => { card.style.borderColor = 'var(--border-color)'; card.style.background = 'rgba(255,255,255,0.03)'; };
        card.onclick = () => {
            const select = document.getElementById("sectorFilterSelect");
            if (select) {
                select.value = s.shop_name;
                fetchLeaderboard(s.shop_name);
            }
        };

        card.innerHTML = `
            <div style="font-size:11px; font-weight:700; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${s.shop_name}">
                <i class="fa-solid fa-industry" style="color:var(--accent-blue);"></i> ${s.shop_name}
            </div>
            <div style="font-family:var(--font-heading); font-size:16px; font-weight:800; ${colorStyle} margin:2px 0;">
                ${avg}%
            </div>
            <div style="font-size:9px; color:var(--text-muted);">
                👥 ${s.total_workers} xod | 📝 ${s.tested_workers} test
            </div>
        `;
        grid.appendChild(card);
    });
}

function populateSectorFilterSelect(sectors = [], currentSelected = 'all') {
    const select = document.getElementById("sectorFilterSelect");
    if (!select) return;
    select.innerHTML = `<option value="all">${i18n[currentLang]?.filter_all_sectors || '🌐 Все участки и линии (Все цеха)'}</option>`;
    sectors.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.shop_name;
        opt.textContent = `🏭 ${s.shop_name} (${s.avg_score}% | ${s.total_workers} xod)`;
        select.appendChild(opt);
    });
    select.value = currentSelected;
}

function renderLeaderboard(leaders = []) {
    const container = document.getElementById("leaderboardList");
    container.innerHTML = "";

    if (leaders.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:20px; color: var(--text-muted);">Рейтинг пока пуст. Будьте первым!</div>`;
        return;
    }

    leaders.forEach((item, idx) => {
        const rank = idx + 1;
        const div = document.createElement("div");
        div.className = `leader-item ${rank <= 3 ? 'top-' + rank : ''}`;

        const hasTakenTest = (item.total_attempts || 0) > 0;
        const isOfficeEligible = hasTakenTest && item.best_score >= 80;

        const role = item.role || 'worker';
        let roleBadge = '';
        if (role === 'nachalnik') {
            roleBadge = `<span class="leader-role-badge master"><i class="fa-solid fa-industry"></i> ${currentLang === 'ru' ? 'Начальник цеха' : 'Sex boshlig\'i'}</span>`;
        } else if (role === 'master') {
            roleBadge = `<span class="leader-role-badge master"><i class="fa-solid fa-user-tie"></i> ${currentLang === 'ru' ? 'Мастер участка' : 'Master (Usta)'}</span>`;
        } else if (role === 'brigadier') {
            roleBadge = `<span class="leader-role-badge brigadier"><i class="fa-solid fa-users-gear"></i> ${currentLang === 'ru' ? 'Бригадир' : 'Brigadir'}</span>`;
        } else if (role === 'quality') {
            roleBadge = `<span class="leader-role-badge quality"><i class="fa-solid fa-shield-halved"></i> ${currentLang === 'ru' ? 'Качество' : 'Sifat nazorati'}</span>`;
        } else if (role === 'director') {
            roleBadge = `<span class="leader-role-badge director"><i class="fa-solid fa-crown"></i> ${currentLang === 'ru' ? 'Руководство' : 'Rahbariyat'}</span>`;
        } else if (role === 'admin' || role === 'superadmin') {
            roleBadge = `<span class="leader-role-badge admin"><i class="fa-solid fa-user-shield"></i> Admin</span>`;
        }


        const scoreText = hasTakenTest ? `${Math.round(item.best_score)}%` : '0%';
        const attemptsText = hasTakenTest 
            ? `${item.total_attempts} ${currentLang === 'ru' ? 'попыток' : 'urinish'}`
            : `<span style="color:var(--text-muted);">${i18n[currentLang]?.no_tests_yet || 'Ещё не проходил'}</span>`;

        div.innerHTML = `
            <div class="leader-rank">${rank}</div>
            <div class="leader-info">
                <div class="leader-name">${item.full_name || 'Сотрудник'} ${roleBadge}</div>
                <div class="leader-shop"><i class="fa-solid fa-industry"></i> ${item.shop_name}</div>
                ${isOfficeEligible ? `<div class="office-eligible-badge"><i class="fa-solid fa-star"></i> ${i18n[currentLang].rank_office_candidate}</div>` : ''}
            </div>
            <div class="leader-score">
                <div class="leader-score-value" style="${hasTakenTest ? '' : 'color:var(--text-muted);'}">${scoreText}</div>
                <div style="font-size:10px; color:var(--text-muted);">${attemptsText}</div>
            </div>
        `;

        container.appendChild(div);
    });
}


// Fetch My Team Data (Master / Chief Shop Monitoring)
async function fetchMyTeamData() {
    const container = document.getElementById("myTeamWorkersList");
    if (!container) return;

    try {
        const res = await fetch(`/api/my_team?telegram_id=${userTelegramId}`);
        if (!res.ok) {
            container.innerHTML = `<p style="color:var(--accent-red); padding:15px;">Доступ запрещен или цех не найден</p>`;
            return;
        }

        const data = await res.json();
        document.getElementById("myTeamShopTitle").textContent = `${data.shop_name} — Xodimlari`;
        
        const workers = data.workers || [];
        if (workers.length === 0) {
            container.innerHTML = `<p style="color:var(--text-muted); padding:15px;">Ushbu sexda hali xodimlar ro'yxatdan o'tmagan</p>`;
            return;
        }

        let html = `
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>ФИО / Xodim</th>
                        <th>Телефон</th>
                        <th>Natija (%)</th>
                        <th>Xatolar (Mistakes)</th>
                    </tr>
                </thead>
                <tbody>
        `;

        workers.forEach(w => {
            const isTop = w.best_score >= 80;
            let mistakesText = "";
            try {
                const parsed = w.latest_mistakes ? JSON.parse(w.latest_mistakes) : [];
                mistakesText = parsed.length > 0 ? parsed.join(', ') : 'Xato yo\'q';
            } catch(e) { mistakesText = w.latest_mistakes || '-'; }

            html += `
                <tr>
                    <td>
                        <strong>${w.full_name}</strong>
                        ${isTop ? ' ⭐ <span style="color:var(--accent-gold); font-size:10px;">EXPERT</span>' : ''}
                    </td>
                    <td><small style="color:var(--text-muted);">${w.phone || '-'}</small></td>
                    <td style="color:${isTop ? 'var(--accent-green)' : 'var(--text-primary)'}; font-weight:700;">
                        ${Math.round(w.best_score)}%
                    </td>
                    <td>
                        <span style="color:${mistakesText.includes('BIQS') ? 'var(--accent-red)' : 'var(--text-muted)'}; font-size:11px;">
                            ${mistakesText}
                        </span>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        container.innerHTML = html;
    } catch (e) {
        console.error("Error fetching my team data", e);
        container.innerHTML = `<p style="color:var(--accent-red); padding:15px;">Ошибка загрузки данных цеха</p>`;
    }
}

// Fetch Admin Data
async function fetchAdminData() {
    try {
        const resCodes = await fetch('/api/admin/codes');
        const codes = await resCodes.json();
        renderActiveCodes(codes);

        const resWorkers = await fetch('/api/admin/workers');
        const workers = await resWorkers.json();
        renderAdminWorkers(workers);

        const resAdmins = await fetch(`/api/admin/admins?telegram_id=${userTelegramId}`);
        if (resAdmins.ok) {
            const admins = await resAdmins.json();
            renderAdminAdmins(admins);
        }
    } catch (e) {
        console.error("Admin data fetch error", e);
    }
}

function renderAdminAdmins(admins) {
    const container = document.getElementById("adminAdminsList");
    if (!container) return;

    if (!admins || admins.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted);">Назначенных администраторов нет</p>`;
        return;
    }

    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>ФИО (ID)</th>
                    <th>Роль</th>
                    <th>Права доступа</th>
                </tr>
            </thead>
            <tbody>
    `;

    admins.forEach(a => {
        html += `
            <tr>
                <td><strong>${a.full_name}</strong><br><small style="color:var(--text-muted);">${a.telegram_id}</small></td>
                <td><span class="element-code-badge" style="background:var(--accent-purple); color:#fff;">${a.role || 'admin'}</span></td>
                <td><small style="color:var(--accent-blue);">${a.permissions || 'all'}</small></td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderActiveCodes(codes) {
    const container = document.getElementById("activeCodesList");
    if (!codes || codes.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted);">Нет активных кодов</p>`;
        return;
    }

    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Код</th>
                    <th>Роль</th>
                    <th>Участок</th>
                    <th>Использован</th>
                </tr>
            </thead>
            <tbody>
    `;

    codes.forEach(c => {
        const roleLabels = {
            'nachalnik': { label: '🏭 Nachalnik', color: 'var(--accent-gold)' },
            'master':    { label: '👨‍🔧 Master',    color: 'var(--accent-purple)' },
            'brigadir':  { label: '👷 Brigadir',   color: 'var(--accent-blue)' },
            'quality':   { label: '🛡️ Quality',    color: '#34d399' },
            'director':  { label: '👑 Director',   color: '#fbbf24' },
            'worker':    { label: '🎯 Worker',     color: 'rgba(255,255,255,0.4)' },
        };
        const roleInfo = roleLabels[c.target_role] || roleLabels['worker'];
        html += `
            <tr>
                <td>
                    <strong style="color:var(--accent-blue); cursor:pointer; user-select:all;" 
                            onclick="navigator.clipboard.writeText('${c.code}'); alert('✅ Код скопирован: ${c.code}');">
                        ${c.code} <i class="fa-regular fa-copy" style="margin-left:5px;"></i>
                    </strong>
                </td>
                <td>
                    <span style="font-size:10px; padding:2px 6px; border-radius:4px; background:${roleInfo.color}22; color:${roleInfo.color}; border:1px solid ${roleInfo.color}44;">
                        ${roleInfo.label}
                    </span>
                </td>
                <td>${c.shop_name}</td>
                <td>${c.used_count} раз</td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderAdminWorkers(workers) {
    const container = document.getElementById("adminWorkersList");
    if (!workers || workers.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted);">Сотрудники не зарегистрированы</p>`;
        return;
    }

    // Group workers by shop_name
    const groups = {};
    workers.forEach(w => {
        const shop = w.shop_name || "Без цеха";
        if (!groups[shop]) {
            groups[shop] = [];
        }
        groups[shop].push(w);
    });

    let html = "";

    // Generate HTML tables for each shop group separately
    Object.keys(groups).sort().forEach(shopName => {
        const shopWorkers = groups[shopName];
        html += `
            <div class="shop-group-section" style="margin-bottom: 25px;">
                <h4 style="color: var(--accent-blue); font-size: 15px; margin: 15px 0 10px 0; border-bottom: 2px solid rgba(255,255,255,0.05); padding-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <span><i class="fa-solid fa-industry" style="margin-right:8px;"></i> ${shopName}</span>
                    <span style="font-size:11px; background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:10px; color:var(--text-secondary); font-weight:normal;">${shopWorkers.length} xodim</span>
                </h4>
                <div class="admin-table-container">
                    <table class="admin-table">
                        <thead>
                            <tr>
                                <th>ФИО</th>
                                <th>Тел</th>
                                <th>Балл (Ошибки)</th>
                                <th>Код</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        shopWorkers.forEach(w => {
            const isTop = w.best_score >= 80;
            let mistakesText = "";
            try {
                const parsed = w.latest_mistakes ? JSON.parse(w.latest_mistakes) : [];
                mistakesText = parsed.length > 0 ? parsed.join(', ') : '';
            } catch(e) { 
                mistakesText = w.latest_mistakes || ''; 
            }

            html += `
                <tr>
                    <td>
                        <strong>${w.full_name}</strong>
                        ${isTop ? ' ⭐ <span style="color:var(--accent-gold); font-size:10px;">В ОФИС</span>' : ''}
                    </td>
                    <td><small style="color:var(--text-muted);">${w.phone || '-'}</small></td>
                    <td style="color:${isTop ? 'var(--accent-green)' : 'var(--text-primary)'}; font-weight:700;">
                        ${Math.round(w.best_score)}%
                        ${mistakesText ? `<br><small style="color:var(--accent-red); font-weight:normal; font-size:10px;">${mistakesText}</small>` : ''}
                    </td>
                    <td><code style="background:rgba(255,255,255,0.1); padding:2px 4px; border-radius:4px;">${w.invite_code}</code></td>
                </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

async function handleCreateCode(e) {
    e.preventDefault();
    const code = document.getElementById("newCodeInput").value.trim();
    const shop = document.getElementById("newShopInput").value.trim();
    const targetRoleSelect = document.getElementById("newTargetRoleSelect");
    const targetRole = targetRoleSelect ? targetRoleSelect.value : "worker";

    if (!code || !shop) return;

    const roleDisplayNames = {
        'nachalnik': '🏭 Начальник цеха (Nachalnik)',
        'master':    '👨‍🔧 Мастер (Master)',
        'brigadir':  '👷 Бригадир (Brigadir)',
        'quality':   '🛡️ Контроль качества (Quality)',
        'director':  '👑 Руководство (Director)',
        'worker':    '🎯 Работник (Worker)',
    };
    const roleLabel = roleDisplayNames[targetRole] || targetRole;

    try {
        const res = await fetch('/api/admin/create_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                shop_name: shop,
                master_name: "Admin",
                created_by: userTelegramId,
                target_role: targetRole
            })
        });

        if (res.ok) {
            alert(`✅ Код ${code}\nРоль: ${roleLabel}\nЦех: ${shop}\n\nКод успешно создан!`);
            document.getElementById("createCodeForm").reset();
            fetchAdminData();
        }
    } catch (err) {
        alert("Ошибка при создании кода");
    }
}

async function handleAddAdmin(e) {
    e.preventDefault();
    const identifier = document.getElementById("adminIdentifierInput").value.trim();
    if (!identifier) return;

    const checkedPerms = Array.from(document.querySelectorAll('input[name="perm"]:checked')).map(el => el.value);

    try {
        const res = await fetch('/api/admin/add_admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                identifier: identifier,
                permissions: checkedPerms,
                added_by: userTelegramId
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert(`✅ Пользователь ${data.user} назначен Администратором!`);
            document.getElementById("addAdminForm").reset();
            fetchAdminData();
        } else {
            alert(`❌ Ошибка: ${data.detail || "Пользователь не найден"}`);
        }
    } catch (err) {
        alert("Ошибка при выче назначения администратора");
    }
}
