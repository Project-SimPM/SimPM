(() => {
  const THEME_KEY = 'simpm-poster-theme';
  const LANG_KEY = 'simpm-poster-lang';
  const rootEl = document.documentElement;

  const translations = {
    en: {
      'doc.title': 'SimPM — Simulation Tool in Project Management (Interactive Poster)',
      'doc.description': 'Interactive research poster for SimPM: a process-based discrete-event simulation library for project and construction management in Python.',

      'header.exhibition': 'Research Exhibition Poster',
      'header.university': 'K. N. Toosi University of Technology',
      'header.title': 'SimPM — Simulation Tool in Project Management',
      'header.subtitle':
        'SimPM is a <b>process-based discrete-event simulation</b> library for modeling projects and\n          construction operations in <b>Python</b>—with built-in <b>logging</b>, schedule-friendly\n          <b>probability distributions</b>, and optional <b>Dash dashboards</b>.',

      'badge.python': 'Python',
      'badge.des': 'Process-based DES',
      'badge.dist': 'Schedule distributions',
      'badge.logs': 'Tabular logging',
      'badge.dashboard': 'Optional dashboards',

      'nav.overview': 'Overview',
      'nav.blocks': 'Building Blocks',
      'nav.workflow': 'Workflow',
      'nav.modeling': 'Modeling',
      'nav.engine': 'Engine',
      'nav.outputs': 'Outputs',
      'nav.examples': 'Examples',

      'overview.title': 'Overview',
      'overview.subtitle': 'A project-focused discrete-event simulation toolkit for studying duration risk, bottlenecks, and resource plans.',
      'overview.what.title': 'What it does',
      'overview.what.li1': 'Model activities as <b>processes</b> (generator functions) that request resources and do work.',
      'overview.what.li2': 'Represent crews/equipment as <b>resources</b> with capacity, priorities, and (optionally) preemption.',
      'overview.what.li3': 'Use <b>distributions</b> (triangular, beta, empirical, …) for realistic task durations.',
      'overview.what.li4': 'Produce <b>tables</b> for schedules, queues, waiting times, and utilization—plus optional dashboards.',
      'overview.poster.title': 'Interactive poster',
      'overview.poster.li1': 'Click any figure (diagram/code) to zoom and read the caption.',
      'overview.poster.li2': 'Use the sticky navigation to jump between panels.',
      'overview.poster.li3': 'All figures are generated (Mermaid) to stay lightweight.',

      'blocks.title': 'Building blocks',
      'blocks.subtitle': 'SimPM maps core DES ideas to practical project-management objects.',
      'blocks.list.title': 'Core objects',
      'blocks.list.li1': '<b>Environment</b>: simulation clock + event scheduler (e.g., <span class="inlineCode">env.now</span>).',
      'blocks.list.li2': '<b>Entity</b>: a work item (task, truck, activity) with attributes and a schedule.',
      'blocks.list.li3': '<b>Resource</b>: crew/equipment/workspace capacity with queueing and logging.',
      'blocks.list.li4': '<b>Distributions</b>: duration uncertainty passed directly to <span class="inlineCode">Entity.do</span>.',
      'blocks.figures.title': 'Figures',

      'workflow.title': 'Workflow',
      'workflow.subtitle': 'Write a model in Python → run the environment → analyze logs → (optionally) open a dashboard.',
      'workflow.tip': 'Tip: switch themes to see the Mermaid figures re-render.',

      'modeling.title': 'Modeling: activities, resources, distributions',
      'modeling.subtitle': 'Model logic using <span class="inlineCode">get</span>/<span class="inlineCode">do</span>/<span class="inlineCode">put</span>; add priority or preemption when needed.',
      'modeling.patterns.title': 'Common patterns',
      'modeling.patterns.li1': '<b>Resource contention</b>: entities queue when capacity is unavailable.',
      'modeling.patterns.li2': '<b>Priorities</b>: urgent tasks jump ahead in the queue.',
      'modeling.patterns.li3': '<b>Preemption</b>: high-priority work can interrupt lower-priority usage.',
      'modeling.figures.title': 'Figures',

      'engine.title': 'Engine: process-based DES',
      'engine.subtitle': 'Processes yield actions; the environment advances time from event to event.',
      'engine.why.title': 'Why DES',
      'engine.why.li1': 'Efficiently represents queues and limited crews without stepping through every second.',
      'engine.why.li2': 'Supports stochastic durations for schedule risk and Monte Carlo experiments.',
      'engine.why.li3': 'Produces explicit waiting/working intervals, enabling bottleneck analysis.',
      'engine.figures.title': 'Figures',

      'outputs.title': 'Outputs: logs and dashboards',
      'outputs.subtitle': 'SimPM produces pandas-friendly tables for schedules and resource performance; dashboards are optional.',

      'examples.title': 'Examples',
      'examples.subtitle': 'Minimal activity, distributions, and dashboard mode.',
      'examples.install.title': 'Install',
      'examples.install.tip': 'Use the extra to enable Plotly Dash dashboards.',
      'examples.figures.title': 'Code figures',

      'footer.built': 'Built for offline exhibition display. Use the sticky navigation for fast jumps.',

      'lightbox.title': 'Figure',
      'lightbox.close': 'Close (Esc)',

      'theme.light': 'Light',
      'theme.dark': 'Dark',
      'theme.toLight': 'Switch to light theme',
      'theme.toDark': 'Switch to dark theme',

      'lang.en': 'EN',
      'lang.fa': 'FA',
      'lang.toEnglish': 'Switch to English',
      'lang.toPersian': 'Switch to Persian'
    },
    fa: {
      'doc.title': 'SimPM — ابزار شبیه\u000cسازی در مدیریت پروژه (پوستر تعاملی)'.replaceAll('\u000c', '\u200c'),
      'doc.description': 'پوستر پژوهشی تعاملی برای SimPM: یک کتابخانهٔ شبیه\u000cسازی گسسته\u000cرویداد مبتنی بر فرایند برای مدیریت پروژه و ساخت در پایتون.'.replaceAll('\u000c', '\u200c'),

      'header.exhibition': 'پوستر نمایشگاه پژوهشی',
      'header.university': 'دانشگاه صنعتی خواجه نصیرالدین طوسی',
      'header.title': 'SimPM — ابزار شبیه\u000cسازی در مدیریت پروژه'.replaceAll('\u000c', '\u200c'),
      'header.subtitle':
        'SimPM یک کتابخانهٔ <b>شبیه\u000cسازی گسسته\u000cرویداد مبتنی بر فرایند</b> برای مدل\u000cسازی پروژه\u000cها و عملیات ساخت در <b>Python</b> است؛\n          با <b>ثبت رخدادها</b>، <b>توزیع\u000cهای احتمالی مناسب برنامه\u000cزمان\u000cبندی</b> و <b>داشبوردهای Dash</b> (اختیاری).'.replaceAll('\u000c', '\u200c'),

      'badge.python': 'Python',
      'badge.des': 'DES مبتنی بر فرایند'.replaceAll('\u000c', '\u200c'),
      'badge.dist': 'توزیع\u000cهای زمانی'.replaceAll('\u000c', '\u200c'),
      'badge.logs': 'ثبت جدولی'.replaceAll('\u000c', '\u200c'),
      'badge.dashboard': 'داشبورد (اختیاری)'.replaceAll('\u000c', '\u200c'),

      'nav.overview': 'مرور',
      'nav.blocks': 'اجزای اصلی',
      'nav.workflow': 'گردش\u000cکار'.replaceAll('\u000c', '\u200c'),
      'nav.modeling': 'مدل\u000cسازی'.replaceAll('\u000c', '\u200c'),
      'nav.engine': 'موتور',
      'nav.outputs': 'خروجی\u000cها'.replaceAll('\u000c', '\u200c'),
      'nav.examples': 'مثال\u000cها'.replaceAll('\u000c', '\u200c'),

      'overview.title': 'مرور',
      'overview.subtitle': 'یک ابزار شبیه\u000cسازی گسسته\u000cرویداد با تمرکز بر پروژه برای مطالعه ریسک زمان\u000cبندی، گلوگاه\u000cها و برنامه منابع.'.replaceAll('\u000c', '\u200c'),
      'overview.what.title': 'چه کاری انجام می\u000cدهد'.replaceAll('\u000c', '\u200c'),
      'overview.what.li1': 'فعالیت\u000cها را به\u000cصورت <b>فرایند</b> (تابع\u000cهای مولد) مدل می\u000cکند که منابع را درخواست کرده و کار انجام می\u000cدهند.'.replaceAll('\u000c', '\u200c'),
      'overview.what.li2': 'اکیپ\u000cها/تجهیزات را به\u000cصورت <b>منبع</b> با ظرفیت، اولویت و (در صورت نیاز) پیش\u000cدستی مدل می\u000cکند.'.replaceAll('\u000c', '\u200c'),
      'overview.what.li3': 'برای مدت\u000cزمان فعالیت\u000cها از <b>توزیع\u000cهای احتمالی</b> (مثلثی، بتا، تجربی و …) استفاده می\u000cکند.'.replaceAll('\u000c', '\u200c'),
      'overview.what.li4': 'برای برنامه، صف، زمان انتظار و بهره\u000cبرداری <b>جدول\u000cهای تحلیلی</b> تولید می\u000cکند؛ به\u000cهمراه داشبورد اختیاری.'.replaceAll('\u000c', '\u200c'),
      'overview.poster.title': 'پوستر تعاملی'.replaceAll('\u000c', '\u200c'),
      'overview.poster.li1': 'روی هر شکل (نمودار/کد) کلیک کنید تا بزرگ\u000cنمایی شود و توضیح آن را بخوانید.'.replaceAll('\u000c', '\u200c'),
      'overview.poster.li2': 'از ناوبری چسبان برای جابه\u000cجایی سریع بین بخش\u000cها استفاده کنید.'.replaceAll('\u000c', '\u200c'),
      'overview.poster.li3': 'برای سبک بودن، شکل\u000cها با Mermaid تولید می\u000cشوند.'.replaceAll('\u000c', '\u200c'),

      'blocks.title': 'اجزای اصلی',
      'blocks.subtitle': 'SimPM مفاهیم DES را به اشیای عملی در مدیریت پروژه تبدیل می\u000cکند.'.replaceAll('\u000c', '\u200c'),
      'blocks.list.title': 'اشیای کلیدی',
      'blocks.list.li1': '<b>Environment</b>: ساعت شبیه\u000cسازی و زمان\u000cبند رخدادها (مثل <span class="inlineCode">env.now</span>).'.replaceAll('\u000c', '\u200c'),
      'blocks.list.li2': '<b>Entity</b>: یک قلم کار (فعالیت، کامیون، بسته کاری) با ویژگی\u000cها و برنامه.'.replaceAll('\u000c', '\u200c'),
      'blocks.list.li3': '<b>Resource</b>: ظرفیت اکیپ/تجهیزات/فضا با صف و ثبت رخداد.'.replaceAll('\u000c', '\u200c'),
      'blocks.list.li4': '<b>Distributions</b>: عدم قطعیت مدت\u000cزمان که مستقیم به <span class="inlineCode">Entity.do</span> داده می\u000cشود.'.replaceAll('\u000c', '\u200c'),
      'blocks.figures.title': 'شکل\u000cها'.replaceAll('\u000c', '\u200c'),

      'workflow.title': 'گردش\u000cکار'.replaceAll('\u000c', '\u200c'),
      'workflow.subtitle': 'مدل\u000cسازی در پایتون → اجرای محیط → تحلیل لاگ\u000cها → (اختیاری) داشبورد.'.replaceAll('\u000c', '\u200c'),
      'workflow.tip': 'نکته: با تغییر تم، شکل\u000cهای Mermaid دوباره رندر می\u000cشوند.'.replaceAll('\u000c', '\u200c'),

      'modeling.title': 'مدل\u000cسازی: فعالیت\u000cها، منابع، توزیع\u000cها'.replaceAll('\u000c', '\u200c'),
      'modeling.subtitle': 'منطق را با <span class="inlineCode">get</span>/<span class="inlineCode">do</span>/<span class="inlineCode">put</span> بنویسید؛ در صورت نیاز اولویت/پیش\u000cدستی اضافه کنید.'.replaceAll('\u000c', '\u200c'),
      'modeling.patterns.title': 'الگوهای رایج',
      'modeling.patterns.li1': '<b>رقابت منابع</b>: وقتی ظرفیت آزاد نیست، موجودیت\u000cها در صف می\u000cمانند.'.replaceAll('\u000c', '\u200c'),
      'modeling.patterns.li2': '<b>اولویت</b>: کارهای فوری در صف جلوتر قرار می\u000cگیرند.'.replaceAll('\u000c', '\u200c'),
      'modeling.patterns.li3': '<b>پیش\u000cدستی</b>: کار با اولویت بالا می\u000cتواند استفادهٔ با اولویت پایین را قطع کند.'.replaceAll('\u000c', '\u200c'),
      'modeling.figures.title': 'شکل\u000cها'.replaceAll('\u000c', '\u200c'),

      'engine.title': 'موتور: DES مبتنی بر فرایند'.replaceAll('\u000c', '\u200c'),
      'engine.subtitle': 'فرایندها عمل\u000cها را yield می\u000cکنند و محیط زمان را از رخداد به رخداد جلو می\u000cبرد.'.replaceAll('\u000c', '\u200c'),
      'engine.why.title': 'چرا DES'.replaceAll('\u000c', '\u200c'),
      'engine.why.li1': 'صف\u000cها و اکیپ\u000cهای محدود را بدون شبیه\u000cسازی هر ثانیه مدل می\u000cکند.'.replaceAll('\u000c', '\u200c'),
      'engine.why.li2': 'برای تحلیل ریسک و مونت\u000cکارلو از مدت\u000cزمان\u000cهای تصادفی پشتیبانی می\u000cکند.'.replaceAll('\u000c', '\u200c'),
      'engine.why.li3': 'بازه\u000cهای انتظار/کار را صریح تولید می\u000cکند و تحلیل گلوگاه را ممکن می\u000cسازد.'.replaceAll('\u000c', '\u200c'),
      'engine.figures.title': 'شکل\u000cها'.replaceAll('\u000c', '\u200c'),

      'outputs.title': 'خروجی\u000cها: لاگ\u000cها و داشبورد'.replaceAll('\u000c', '\u200c'),
      'outputs.subtitle': 'SimPM جدول\u000cهای سازگار با pandas برای برنامه و عملکرد منابع تولید می\u000cکند؛ داشبورد اختیاری است.'.replaceAll('\u000c', '\u200c'),

      'examples.title': 'مثال\u000cها'.replaceAll('\u000c', '\u200c'),
      'examples.subtitle': 'فعالیت حداقلی، توزیع\u000cها و حالت داشبورد.'.replaceAll('\u000c', '\u200c'),
      'examples.install.title': 'نصب',
      'examples.install.tip': 'برای فعال شدن داشبورد، افزونهٔ dash را نصب کنید.'.replaceAll('\u000c', '\u200c'),
      'examples.figures.title': 'شکل\u000cهای کد'.replaceAll('\u000c', '\u200c'),

      'footer.built': 'برای نمایش آفلاین ساخته شده است. از ناوبری چسبان برای پرش سریع استفاده کنید.'.replaceAll('\u000c', '\u200c'),

      'lightbox.title': 'شکل',
      'lightbox.close': 'بستن (Esc)',

      'theme.light': 'روشن'.replaceAll('\u000c', '\u200c'),
      'theme.dark': 'تیره'.replaceAll('\u000c', '\u200c'),
      'theme.toLight': 'تغییر به حالت روشن'.replaceAll('\u000c', '\u200c'),
      'theme.toDark': 'تغییر به حالت تیره'.replaceAll('\u000c', '\u200c'),

      'lang.en': 'EN',
      'lang.fa': 'FA',
      'lang.toEnglish': 'تغییر به انگلیسی'.replaceAll('\u000c', '\u200c'),
      'lang.toPersian': 'تغییر به فارسی'.replaceAll('\u000c', '\u200c')
    }
  };

  function getCurrentLang() {
    const lang = rootEl.dataset.lang;
    return (lang === 'fa' || lang === 'en') ? lang : 'en';
  }

  function normalizeHalfSpaces(text) {
    return String(text).replaceAll('\u000c', '\u200c');
  }

  function t(key) {
    const lang = getCurrentLang();
    const value = translations[lang]?.[key] ?? translations.en[key] ?? '';
    return normalizeHalfSpaces(value);
  }

  function getStoredTheme() {
    try {
      const value = localStorage.getItem(THEME_KEY);
      return (value === 'light' || value === 'dark') ? value : null;
    } catch {
      return null;
    }
  }

  function getSystemTheme() {
    try {
      return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
    } catch {
      return 'dark';
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // ignore
    }
  }

  function applyHighlightTheme(theme) {
    const isDark = theme === 'dark';
    const darkLink = document.getElementById('hljs-dark');
    const lightLink = document.getElementById('hljs-light');
    if (darkLink) darkLink.disabled = !isDark;
    if (lightLink) lightLink.disabled = isDark;
  }

  function applyTheme(theme) {
    rootEl.dataset.theme = theme;
    applyHighlightTheme(theme);

    const btn = document.getElementById('themeToggle');
    if (btn) {
      const isDark = theme === 'dark';
      btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      btn.textContent = isDark ? t('theme.dark') : t('theme.light');
      btn.title = isDark ? t('theme.toLight') : t('theme.toDark');
    }
  }

  function getStoredLang() {
    try {
      const value = localStorage.getItem(LANG_KEY);
      return (value === 'en' || value === 'fa') ? value : null;
    } catch {
      return null;
    }
  }

  function setStoredLang(lang) {
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch {
      // ignore
    }
  }

  function updateDocumentStrings() {
    document.title = t('doc.title');
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', t('doc.description'));
  }

  function applyI18nToDom() {
    for (const el of document.querySelectorAll('[data-i18n]')) {
      const key = el.getAttribute('data-i18n');
      if (!key) continue;
      el.textContent = t(key);
    }
    for (const el of document.querySelectorAll('[data-i18n-html]')) {
      const key = el.getAttribute('data-i18n-html');
      if (!key) continue;
      el.innerHTML = t(key);
    }
  }

  function updateLangButton() {
    const btn = document.getElementById('langToggle');
    if (!btn) return;
    const lang = getCurrentLang();
    btn.setAttribute('aria-pressed', lang === 'fa' ? 'true' : 'false');
    btn.textContent = lang === 'fa' ? t('lang.fa') : t('lang.en');
    btn.title = lang === 'fa' ? t('lang.toEnglish') : t('lang.toPersian');
  }

  function applyLanguage(lang) {
    const safe = (lang === 'fa' || lang === 'en') ? lang : 'en';
    rootEl.dataset.lang = safe;
    rootEl.lang = safe;
    rootEl.dir = safe === 'fa' ? 'rtl' : 'ltr';
    updateDocumentStrings();
    applyI18nToDom();
    updateLangButton();
    applyTheme((rootEl.dataset.theme === 'light' || rootEl.dataset.theme === 'dark') ? rootEl.dataset.theme : 'dark');
  }

  // Mermaid helpers
  function getMermaidTheme() {
    const theme = (rootEl.dataset.theme === 'light') ? 'light' : 'dark';
    // Mermaid themes: 'default'|'dark'|'neutral'|'forest'|'base'
    return theme === 'dark' ? 'dark' : 'default';
  }

  function initMermaid() {
    if (!window.mermaid) return;
    try {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
        theme: getMermaidTheme()
      });
    } catch {
      // ignore
    }
  }

  let mermaidCounter = 0;

  async function renderMermaidToSvg(diagramText) {
    if (!window.mermaid) {
      return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 120"><rect width="600" height="120" fill="transparent"/><text x="10" y="60" fill="currentColor" font-family="system-ui" font-size="14">Mermaid failed to load.</text></svg>';
    }

    mermaidCounter += 1;
    const id = `m-${Date.now()}-${mermaidCounter}`;

    // Ensure theme tracks current UI
    try {
      window.mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', theme: getMermaidTheme() });
    } catch {
      // ignore
    }

    const { svg } = await window.mermaid.render(id, diagramText);
    return svg;
  }

  function svgToElement(svgString) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(svgString, 'image/svg+xml');
    return doc.documentElement;
  }

  function safeSerializeSvg(svgEl) {
    // Drop potentially problematic <script> tags if any.
    for (const s of svgEl.querySelectorAll('script')) s.remove();
    const serializer = new XMLSerializer();
    return serializer.serializeToString(svgEl);
  }

  function normalizeSvgForThumb(svgString) {
    const svgEl = svgToElement(svgString);
    svgEl.removeAttribute('width');
    svgEl.removeAttribute('height');
    svgEl.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svgEl.style.width = '100%';
    svgEl.style.height = '100%';
    return safeSerializeSvg(svgEl);
  }

  function normalizeSvgForLightbox(svgString) {
    const svgEl = svgToElement(svgString);
    svgEl.removeAttribute('width');
    svgEl.removeAttribute('height');
    svgEl.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svgEl.style.width = '100%';
    svgEl.style.height = 'auto';
    return safeSerializeSvg(svgEl);
  }

  // Figure definitions
  const figures = {
    blocks: [
      {
        kind: 'mermaid',
        caption: {
          en: 'Core modeling objects: Environment, Entity, Resource, and Distributions.',
          fa: 'اشیای اصلی مدل\u000cسازی: Environment، Entity، Resource و Distributions.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `classDiagram\n  direction LR\n  class Environment {\n    +now\n    +process(generator)\n    +run(until)\n    +create_entities(name, n, log)\n  }\n  class Entity {\n    +get(resource, amount, priority)\n    +do(name, duration_or_dist)\n    +put(resource, amount)\n    +schedule()\n  }\n  class Resource {\n    +capacity\n    +queue\n    +status_log()\n    +waiting_time()\n    +average_utilization()\n  }\n  class dist {\n    +triang(min, mode, max)\n    +beta(params)\n    +norm(mu, sigma)\n    +empirical(data)\n  }\n  Environment --> Entity : hosts\n  Environment --> Resource : owns\n  Entity --> Resource : requests/releases\n  Entity --> dist : samples\n`,
          fa: `classDiagram\n  direction LR\n  class Environment {\n    +now\n    +process(generator)\n    +run(until)\n    +create_entities(name, n, log)\n  }\n  class Entity {\n    +get(resource, amount, priority)\n    +do(name, duration_or_dist)\n    +put(resource, amount)\n    +schedule()\n  }\n  class Resource {\n    +capacity\n    +queue\n    +status_log()\n    +waiting_time()\n    +average_utilization()\n  }\n  class dist {\n    +triang(min, mode, max)\n    +beta(params)\n    +norm(mu, sigma)\n    +empirical(data)\n  }\n  Environment --> Entity : محیط\n  Environment --> Resource : منبع\n  Entity --> Resource : درخواست/آزادسازی\n  Entity --> dist : نمونه\u000cگیری\n`.replaceAll('\u000c', '\u200c')
        }
      },
      {
        kind: 'mermaid',
        caption: {
          en: 'The standard activity pattern: request → work → release.',
          fa: 'الگوی استاندارد فعالیت: درخواست → کار → آزادسازی.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart LR\n  A[Entity] -->|get resource| B{Resource available?}\n  B -- Yes --> C[do work for duration]\n  B -- No --> Q[Queue] --> B\n  C -->|release resource| D[Done]\n`,
          fa: `flowchart LR\n  A[موجودیت] -->|گرفتن منبع| B{ظرفیت آزاد است؟}\n  B -- بله --> C[انجام کار]\n  B -- خیر --> Q[صف] --> B\n  C -->|آزادسازی منبع| D[پایان]\n`.replaceAll('\u000c', '\u200c')
        }
      }
    ],

    workflow: [
      {
        kind: 'mermaid',
        caption: {
          en: 'End-to-end workflow: define model → run → analyze logs → optional dashboard.',
          fa: 'گردش\u000cکار انتها\u000cبه\u000cانتها: تعریف مدل → اجرا → تحلیل لاگ\u000cها → داشبورد (اختیاری).'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart LR\n  M[Model in Python <br/> Environment + Resources + Processes] --> R[Run via simpm.run]\n  R --> L[Logs: schedule, queues, utilization]\n  L --> A[Analyze with pandas or plots]\n  R -->|dashboard=True| D[Dash dashboard after run]\n`,
          fa: `flowchart LR\n  M[مدل در پایتون <br/> محیط + منابع + فرایندها] --> R[اجرا با simpm.run]\n  R --> L[لاگ\u000cها: برنامه، صف، بهره\u000cبرداری]\n  L --> A[تحلیل با pandas یا نمودار]\n  R -->|dashboard=True| D[داشبورد Dash پس از اجرا]\n`.replaceAll('\u000c', '\u200c')
        }
      },
      {
        kind: 'mermaid',
        caption: {
          en: 'Process interaction (conceptual): the environment advances time between events.',
          fa: 'تعامل فرایندها (مفهومی): محیط زمان را بین رخدادها جلو می\u000cبرد.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `sequenceDiagram\n  participant Env as Environment\n  participant Ent as Entity\n  participant Res as Resource\n  Ent->>Env: env.process(job())\n  Env-->>Ent: start (t=0)\n  Ent->>Res: get(1)\n  Res-->>Ent: granted or queued\n  Ent->>Env: do("work", dist)\n  Env-->>Ent: resume at t += sampled_duration\n  Ent->>Res: put(1)\n  Res-->>Ent: released\n`,
          fa: `sequenceDiagram\n  participant Env as Environment\n  participant Ent as Entity\n  participant Res as Resource\n  Ent->>Env: env.process(job())\n  Env-->>Ent: شروع (t=0)\n  Ent->>Res: get(1)\n  Res-->>Ent: تخصیص/صف\n  Ent->>Env: do("کار", dist)\n  Env-->>Ent: ادامه در t += مدت\u000cزمان\n  Ent->>Res: put(1)\n  Res-->>Ent: آزادسازی\n`.replaceAll('\u000c', '\u200c')
        }
      }
    ],

    modeling: [
      {
        kind: 'mermaid',
        caption: {
          en: 'Resource contention: multiple entities competing for one crew.',
          fa: 'رقابت منابع: چند موجودیت برای یک اکیپ رقابت می\u000cکنند.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart TB\n  subgraph Crew[Resource: crew capacity 1]\n    C((Crew))\n  end\n  E1[Entity A] -->|request| C\n  E2[Entity B] -->|request| C\n  E3[Entity C] -->|request| C\n  C -->|grants one| W1[do work]\n  C -->|queues others| Q[Queue]\n  W1 -->|release| C\n  Q -->|next granted| W2[do work]\n  W2 -->|release| C\n`,
          fa: `flowchart TB\n  subgraph Crew[منبع: ظرفیت اکیپ ۱]\n    C((اکیپ))\n  end\n  E1[موجودیت A] -->|درخواست| C\n  E2[موجودیت B] -->|درخواست| C\n  E3[موجودیت C] -->|درخواست| C\n  C -->|تخصیص به یکی| W1[انجام کار]\n  C -->|صف برای بقیه| Q[صف]\n  W1 -->|آزادسازی| C\n  Q -->|نفر بعد| W2[انجام کار]\n  W2 -->|آزادسازی| C\n`.replaceAll('\u000c', '\u200c')
        }
      },
      {
        kind: 'mermaid',
        caption: {
          en: 'Priority + preemption idea: urgent work can jump the queue (and optionally interrupt).',
          fa: 'ایدهٔ اولویت و پیش\u000cدستی: کار فوری می\u000cتواند جلو بیفتد (و گاهی قطع کند).'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart LR\n  Q[(Queue)] -->|PriorityResource| G{Grant next}\n  L[Low priority job] --> Q\n  H[High priority job] --> Q\n  G --> R[Use resource]\n  R -->|PreemptiveResource| P[Interrupt low user]\n`,
          fa: `flowchart LR\n  Q[(صف)] -->|PriorityResource| G{تخصیص بعدی}\n  L[کار با اولویت پایین] --> Q\n  H[کار با اولویت بالا] --> Q\n  G --> R[استفاده از منبع]\n  R -->|PreemptiveResource| P[قطعِ کار کم\u000cاولویت]\n`.replaceAll('\u000c', '\u200c')
        }
      }
    ],

    engine: [
      {
        kind: 'mermaid',
        caption: {
          en: 'DES time advancement: jump from event to event, not every second.',
          fa: 'پیشروی زمان در DES: پرش از رخداد به رخداد، نه هر ثانیه.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart TB\n  S[Start t=0] --> E{Next event time?}\n  E -->|pop earliest| T[Advance env.now]\n  T --> P[Resume affected processes]\n  P --> L[Log state changes]\n  L --> E\n`,
          fa: `flowchart TB\n  S[شروع t=0] --> E{رخداد بعدی؟}\n  E -->|کوچک\u000cترین زمان| T[env.now را جلو ببر]\n  T --> P[ادامهٔ فرایندهای مرتبط]\n  P --> L[ثبت تغییرات وضعیت]\n  L --> E\n`.replaceAll('\u000c', '\u200c')
        }
      },
      {
        kind: 'mermaid',
        caption: {
          en: 'Activity intervals: each do() creates a working interval; each wait in queue is an idle interval.',
          fa: 'بازه\u000cهای فعالیت: هر do() یک بازهٔ کار می\u000cسازد و هر صف یک بازهٔ انتظار.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `gantt\n  title Entity timeline (conceptual)\n  dateFormat YYYY-MM-DD\n  axisFormat %m/%d\n  section Job\n  Wait for crew   :a1, 2025-01-01, 3d\n  Work            :a2, after a1, 6d\n  Wait again      :a3, after a2, 2d\n  Work            :a4, after a3, 4d\n`,
          fa: `gantt\n  title خط زمان موجودیت (مفهومی)\n  dateFormat YYYY-MM-DD\n  axisFormat %m/%d\n  section کار\n  انتظار برای اکیپ :a1, 2025-01-01, 3d\n  اجرا            :a2, after a1, 6d\n  انتظار مجدد     :a3, after a2, 2d\n  اجرا            :a4, after a3, 4d\n`.replaceAll('\u000c', '\u200c')
        }
      }
    ],

    outputs: [
      {
        kind: 'mermaid',
        caption: {
          en: 'What gets logged: schedules (entity), queue/utilization (resource), and summary measures.',
          fa: 'چه چیزی ثبت می\u000cشود: برنامهٔ موجودیت، صف/بهره\u000cبرداری منبع، و شاخص\u000cهای خلاصه.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart LR\n  E[Entity log] --> S[schedule table: start/finish per activity]\n  R[Resource log] --> U[status_log table: queue length + allocation]\n  R --> W[waiting_time table: per request]\n  R --> V[average_utilization metric]\n`,
          fa: `flowchart LR\n  E[لاگ موجودیت] --> S[جدول schedule: شروع/پایان فعالیت]\n  R[لاگ منبع] --> U[جدول status_log: طول صف و تخصیص]\n  R --> W[جدول waiting_time: برای هر درخواست]\n  R --> V[شاخص average_utilization]\n`.replaceAll('\u000c', '\u200c')
        }
      },
      {
        kind: 'mermaid',
        caption: {
          en: 'Dashboard mode: run headless or start a post-run dashboard with one flag.',
          fa: 'حالت داشبورد: اجرای بدون UI یا داشبورد پس از اجرا با یک گزینه.'.replaceAll('\u000c', '\u200c')
        },
        mermaid: {
          en: `flowchart TB\n  A[simpm.run env, dashboard=False] --> B[Headless run]\n  A2[simpm.run env, dashboard=True] --> C[Run completes]\n  C --> D[Build dashboard data]\n  D --> E[Open Dash app]\n`,
          fa: `flowchart TB\n  A[simpm.run env، dashboard=False] --> B[اجرای بدون داشبورد]\n  A2[simpm.run env، dashboard=True] --> C[پایان اجرا]\n  C --> D[تولید داده داشبورد]\n  D --> E[اجرای برنامه Dash]\n`.replaceAll('\u000c', '\u200c')
        }
      }
    ],

    examples: [
      {
        kind: 'code',
        caption: {
          en: 'Minimal example: one activity requests a crew, works, and releases.',
          fa: 'مثال حداقلی: یک فعالیت اکیپ را می\u000cگیرد، کار می\u000cکند و آزاد می\u000cکند.'.replaceAll('\u000c', '\u200c')
        },
        code: `import simpm\nfrom simpm.des import Environment, Resource, Entity\nfrom simpm.dist import norm\n\nenv = Environment(\"Single activity\")\ncrew = Resource(env, name=\"Crew\", capacity=1)\nactivity = Entity(env, \"Activity\", log=True)\n\ndef activity_process(entity, resource):\n    yield entity.get(resource, 1)\n    yield entity.do(\"work\", norm(10, 2))\n    yield entity.put(resource, 1)\n\nenv.process(activity_process(activity, crew))\nsimpm.run(env, dashboard=False)\nprint(activity.schedule())\n`
      },
      {
        kind: 'code',
        caption: {
          en: 'Monte Carlo sketch: run many scenarios to estimate completion-time distribution.',
          fa: 'طرح مونت\u000cکارلو: اجرای سناریوهای متعدد برای برآورد توزیع زمان اتمام.'.replaceAll('\u000c', '\u200c')
        },
        code: `import numpy as np\nimport simpm\nimport simpm.des as des\nfrom simpm.dist import triang\n\ndef run_once(seed):\n    np.random.seed(seed)\n    env = des.Environment(\"MC\")\n    crew = des.Resource(env, \"Crew\", capacity=1)\n    job = env.create_entities(\"job\", 1, log=True)[0]\n\n    def p(e):\n        yield e.get(crew, 1)\n        yield e.do(\"work\", triang(8, 10, 16))\n        yield e.put(crew, 1)\n\n    env.process(p(job))\n    simpm.run(env, dashboard=False)\n    return env.now\n\nT = [run_once(i) for i in range(200)]\nprint(np.percentile(T, [10, 50, 90]))\n`
      },
      {
        kind: 'code',
        caption: {
          en: 'Dashboard mode: run the same model and open a post-run dashboard.',
          fa: 'حالت داشبورد: همان مدل را اجرا کنید و داشبورد پس از اجرا را ببینید.'.replaceAll('\u000c', '\u200c')
        },
        code: `import simpm\nimport simpm.des as des\n\nenv = des.Environment(\"With dashboard\")\ncrew = des.Resource(env, \"Crew\", capacity=1, log=True)\njob = env.create_entities(\"job\", 1, log=True)[0]\n\ndef p(e):\n    yield e.get(crew, 1)\n    yield e.do(\"work\", 5)\n    yield e.put(crew, 1)\n\nenv.process(p(job))\n# Requires: pip install simpm[dash]\nsimpm.run(env, dashboard=True, host=\"127.0.0.1\", port=8050)\n`
      }
    ]
  };

  const $ = (sel, root = document) => root.querySelector(sel);

  function getCaption(item) {
    const lang = getCurrentLang();
    const cap = item?.caption;
    if (!cap) return '';
    const value = (typeof cap === 'string') ? cap : (cap[lang] ?? cap.en ?? '');
    return normalizeHalfSpaces(value);
  }

  function getMermaidText(item) {
    const txt = item?.mermaid;
    if (!txt) return '';
    // Keep diagrams English in all language modes.
    const value = (typeof txt === 'string') ? txt : (txt.en ?? txt.fa ?? '');
    return normalizeHalfSpaces(value);
  }

  function escapeHtml(text) {
    return String(text)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function highlightCodeBlocks(root = document) {
    if (!window.hljs) return;
    // Ensure Python language is registered (defensive; should already be registered by the language bundle).
    try {
      if (window.hljs.listLanguages && !window.hljs.listLanguages().includes('python')) {
        if (window.hljsPython) window.hljs.registerLanguage('python', window.hljsPython);
      }
    } catch {
      // ignore
    }

    const blocks = (root instanceof Element ? root : document).querySelectorAll('code.language-python');
    blocks.forEach((el) => {
      if (el.dataset && el.dataset.highlighted) delete el.dataset.highlighted;
      if (!el.classList.contains('hljs')) el.classList.add('hljs');
      window.hljs.highlightElement(el);
    });
  }

  // Lightbox
  const lightbox = $('#lightbox');
  const lbImg = $('#lightboxImg');
  const lbSvg = $('#lightboxSvg');
  const lbCode = $('#lightboxCode');
  let lbCodeInner = $('#lightboxCodeInner');
  const lbTitle = $('#lightboxTitle');
  const lbCaption = $('#lightboxCaption');
  const lbClose = $('#lightboxClose');

  function openLightbox({ kind, title, caption, svg, code, imgSrc }) {
    if (!lightbox || !lbTitle || !lbCaption || !lbImg || !lbSvg || !lbCode) return;

    lbTitle.textContent = title || caption || t('lightbox.title');
    lbCaption.textContent = caption || '';

    // Reset
    lbImg.style.display = 'none';
    lbSvg.style.display = 'none';
    lbCode.style.display = 'none';
    lbSvg.setAttribute('aria-hidden', 'true');
    lbCode.setAttribute('aria-hidden', 'true');
    lbImg.src = '';
    lbSvg.innerHTML = '';
    if (lbCodeInner) lbCodeInner.textContent = '';
    lbSvg.removeAttribute('dir');

    if (kind === 'img' && imgSrc) {
      lbImg.style.display = '';
      lbImg.src = imgSrc;
      lbImg.alt = caption || '';
    } else if (kind === 'mermaid' && svg) {
      lbSvg.style.display = '';
      lbSvg.setAttribute('aria-hidden', 'false');
      if (getCurrentLang() === 'fa') lbSvg.setAttribute('dir', 'ltr');
      lbSvg.innerHTML = normalizeSvgForLightbox(svg);
    } else if (kind === 'code' && code) {
      lbCode.style.display = '';
      lbCode.setAttribute('aria-hidden', 'false');
      lbCode.setAttribute('dir', 'ltr');
      // Ensure inner code element exists
      if (!lbCodeInner) {
        lbCodeInner = document.createElement('code');
        lbCodeInner.id = 'lightboxCodeInner';
        lbCodeInner.className = 'language-python';
        lbCode.innerHTML = '';
        lbCode.appendChild(lbCodeInner);
      }
      lbCodeInner.classList.add('language-python');
      lbCodeInner.textContent = code;
      highlightCodeBlocks(lbCode);
    }

    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.setAttribute('aria-hidden', 'true');
    if (lbImg) lbImg.src = '';
    if (lbSvg) lbSvg.innerHTML = '';
    if (lbCodeInner) lbCodeInner.textContent = '';
    document.body.style.overflow = '';
  }

  lbClose?.addEventListener('click', closeLightbox);
  lightbox?.addEventListener('click', (e) => {
    if (e.target === lightbox) closeLightbox();
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
  });

  async function renderFigureGrid(targetId, items) {
    const target = document.getElementById(targetId);
    if (!target) return;

    const frag = document.createDocumentFragment();

    for (const item of items) {
      const caption = getCaption(item);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'figureBtn';

      if (item.kind === 'code') {
        const code = String(item.code ?? '');
        const previewLines = code.split('\n').slice(0, 10).join('\n');
        btn.innerHTML = `
          <pre class="codeThumb"><code class="language-python">${escapeHtml(previewLines)}</code></pre>
          <div class="cap">${escapeHtml(caption)}</div>
        `.trim();
        btn.addEventListener('click', () => openLightbox({ kind: 'code', title: caption, caption, code }));
        highlightCodeBlocks(btn);
      } else if (item.kind === 'mermaid') {
        const mermaidText = getMermaidText(item);
        let svg = '';
        try {
          svg = await renderMermaidToSvg(mermaidText);
        } catch {
          svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 120"><rect width="600" height="120" fill="transparent"/><text x="10" y="60" fill="currentColor" font-family="system-ui" font-size="14">Diagram render failed.</text></svg>';
        }

        const thumbSvg = normalizeSvgForThumb(svg);
        btn.innerHTML = `
          <div class="thumb">${thumbSvg}</div>
          <div class="cap">${escapeHtml(caption)}</div>
        `.trim();
        if (getCurrentLang() === 'fa') btn.querySelector('.thumb')?.setAttribute('dir', 'ltr');
        btn.addEventListener('click', () => openLightbox({ kind: 'mermaid', title: caption, caption, svg }));
      }

      frag.appendChild(btn);
    }

    target.innerHTML = '';
    target.appendChild(frag);
  }

  async function renderAllFigureGrids() {
    await renderFigureGrid('blocksGrid', figures.blocks);
    await renderFigureGrid('workflowGrid', figures.workflow);
    await renderFigureGrid('modelingGrid', figures.modeling);
    await renderFigureGrid('engineGrid', figures.engine);
    await renderFigureGrid('outputsGrid', figures.outputs);
    await renderFigureGrid('examplesGrid', figures.examples);
    highlightCodeBlocks();
  }

  function initLanguageToggle() {
    const stored = getStoredLang();
    const initial = (rootEl.dataset.lang === 'fa' || rootEl.dataset.lang === 'en')
      ? rootEl.dataset.lang
      : (stored ?? 'en');

    applyLanguage(initial);

    const btn = document.getElementById('langToggle');
    btn?.addEventListener('click', async () => {
      const next = getCurrentLang() === 'fa' ? 'en' : 'fa';
      setStoredLang(next);
      closeLightbox();
      applyLanguage(next);
      await renderAllFigureGrids();
    });
  }

  function initThemeToggle() {
    const stored = getStoredTheme();
    const initial = (rootEl.dataset.theme === 'light' || rootEl.dataset.theme === 'dark')
      ? rootEl.dataset.theme
      : (stored ?? getSystemTheme());

    applyTheme(initial);

    const btn = document.getElementById('themeToggle');
    btn?.addEventListener('click', async () => {
      const current = (rootEl.dataset.theme === 'light') ? 'light' : 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      closeLightbox();
      applyTheme(next);
      setStoredTheme(next);
      initMermaid();
      await renderAllFigureGrids();
    });

    // Follow system changes only if user has not picked a theme.
    if (!stored && window.matchMedia) {
      try {
        const media = window.matchMedia('(prefers-color-scheme: dark)');
        media.addEventListener('change', async () => {
          const stillNoStored = !getStoredTheme();
          if (stillNoStored) {
            applyTheme(getSystemTheme());
            initMermaid();
            await renderAllFigureGrids();
          }
        });
      } catch {
        // ignore
      }
    }
  }

  // Boot
  initLanguageToggle();
  initThemeToggle();
  initMermaid();

  // Render after initial i18n/theme are applied
  renderAllFigureGrids();
})();
