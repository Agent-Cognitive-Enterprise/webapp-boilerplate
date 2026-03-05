import {
    SETUP_SUPPORTED_LOCALES,
    normalizeLocale,
    resolveSetupLocale,
} from "./setupLocaleMeta";
import type {SetupLocale} from "./setupLocaleMeta";

export {SETUP_SUPPORTED_LOCALES, normalizeLocale, resolveSetupLocale};

export type SetupCopy = {
    title: string;
    subtitle: string;
    initialSetupToken: string;
    siteName: string;
    supportedLocales: string;
    defaultLocale: string;
    adminEmail: string;
    adminPassword: string;
    localesHint: string;
    clickLocaleHint: string;
    initialize: string;
    initializing: string;
    alreadyConfiguredTitle: string;
    alreadyConfiguredDescription: string;
    goToLogin: string;
    optionalEmailSettings: string;
    optionalEmailSettingsHint: string;
    smtpHost: string;
    smtpPort: string;
    smtpUsername: string;
    smtpPassword: string;
    smtpFromEmail: string;
    smtpUseStartTls: string;
    authBaseUrls: string;
    authFrontendBaseUrl: string;
    authBackendBaseUrl: string;
    authBaseUrlsHint: string;
    checkEmailSettings: string;
    checkingEmailSettings: string;
    emailSettingsCheckFailed: string;
    checkingSetupStatus: string;
    backendOfflineTitle: string;
    backendOfflineDescription: string;
    validation: {
        setupTokenRequired: string;
        siteNameRequired: string;
        defaultLocaleRequired: string;
        supportedLocalesRequired: string;
        supportedMustIncludeDefault: string;
        adminEmailRequired: string;
        invalidEmail: string;
        adminPasswordRequired: string;
        passwordMinLength: string;
        smtpHostRequired: string;
        smtpPortInvalid: string;
        smtpFromEmailInvalid: string;
    };
    genericError: string;
};

const ENGLISH_COPY: SetupCopy = {
    title: "First-Run Setup",
    subtitle: "Complete this one-time setup to initialize your application.",
    initialSetupToken: "Initial setup token",
    siteName: "Site name",
    supportedLocales: "Supported locales",
    defaultLocale: "Default locale",
    adminEmail: "Admin email",
    adminPassword: "Admin password",
    localesHint: "Loaded from initial locale files. You can edit this list later in Admin settings.",
    clickLocaleHint: "Click a locale chip to switch setup language.",
    initialize: "Initialize application",
    initializing: "Initializing...",
    alreadyConfiguredTitle: "Application Already Configured",
    alreadyConfiguredDescription: "Setup is disabled because initialization has already been completed.",
    goToLogin: "Go to login",
    optionalEmailSettings: "Optional email settings",
    optionalEmailSettingsHint: "If configured, newly registered users must verify their email before login.",
    smtpHost: "SMTP host",
    smtpPort: "SMTP port",
    smtpUsername: "SMTP username",
    smtpPassword: "SMTP password",
    smtpFromEmail: "SMTP from email",
    smtpUseStartTls: "Use STARTTLS",
    authBaseUrls: "Authentication base URLs",
    authFrontendBaseUrl: "Frontend base URL",
    authBackendBaseUrl: "Backend base URL",
    authBaseUrlsHint: "Used in verification and reset links sent by email.",
    checkEmailSettings: "Check email settings",
    checkingEmailSettings: "Checking...",
    emailSettingsCheckFailed: "Email settings check failed",
    checkingSetupStatus: "Checking setup status...",
    backendOfflineTitle: "Backend is offline",
    backendOfflineDescription: "Cannot reach backend service. Start backend and refresh this page.",
    validation: {
        setupTokenRequired: "Setup token is required.",
        siteNameRequired: "Site name is required.",
        defaultLocaleRequired: "Default locale is required.",
        supportedLocalesRequired: "At least one supported locale is required.",
        supportedMustIncludeDefault: "Supported locales must include the default locale.",
        adminEmailRequired: "Admin email is required.",
        invalidEmail: "Enter a valid email address.",
        adminPasswordRequired: "Admin password is required.",
        passwordMinLength: "Password must be at least 8 characters.",
        smtpHostRequired: "SMTP host is required when email is configured.",
        smtpPortInvalid: "SMTP port must be a valid number.",
        smtpFromEmailInvalid: "SMTP from email must be a valid email address.",
    },
    genericError: "Setup failed. Check your values and try again.",
};

const SETUP_COPY_BY_LOCALE: Record<SetupLocale, Partial<SetupCopy>> = {
    en: {},
    es: {
        title: "Configuración inicial",
        subtitle: "Completa esta configuración única para inicializar tu aplicación.",
        initialSetupToken: "Token de configuración inicial",
        siteName: "Nombre del sitio",
        supportedLocales: "Idiomas compatibles",
        defaultLocale: "Idioma predeterminado",
        adminEmail: "Correo del administrador",
        adminPassword: "Contraseña del administrador",
        localesHint: "Se cargan desde los archivos de idioma iniciales. Puedes editar esta lista luego en Configuración de administrador.",
        clickLocaleHint: "Haz clic en un idioma para cambiar el idioma de la configuración.",
        initialize: "Inicializar aplicación",
        initializing: "Inicializando...",
        alreadyConfiguredTitle: "Aplicación ya configurada",
        alreadyConfiguredDescription: "La configuración está deshabilitada porque la inicialización ya se completó.",
        goToLogin: "Ir a iniciar sesión",
    },
    fr: {
        title: "Configuration initiale",
        subtitle: "Terminez cette configuration unique pour initialiser votre application.",
        initialSetupToken: "Jeton de configuration initiale",
        siteName: "Nom du site",
        supportedLocales: "Langues prises en charge",
        defaultLocale: "Langue par défaut",
        adminEmail: "E-mail administrateur",
        adminPassword: "Mot de passe administrateur",
        localesHint: "Chargé depuis les fichiers de langue initiaux. Vous pourrez modifier cette liste plus tard dans les paramètres admin.",
        clickLocaleHint: "Cliquez sur une langue pour changer la langue de configuration.",
        initialize: "Initialiser l'application",
        initializing: "Initialisation...",
        alreadyConfiguredTitle: "Application déjà configurée",
        alreadyConfiguredDescription: "La configuration est désactivée car l'initialisation est déjà terminée.",
        goToLogin: "Aller à la connexion",
    },
    de: {
        title: "Ersteinrichtung",
        subtitle: "Schließe diese einmalige Einrichtung ab, um die Anwendung zu initialisieren.",
        initialSetupToken: "Initiales Setup-Token",
        siteName: "Seitenname",
        supportedLocales: "Unterstützte Sprachen",
        defaultLocale: "Standardsprache",
        adminEmail: "Admin-E-Mail",
        adminPassword: "Admin-Passwort",
        localesHint: "Aus den anfänglichen Sprachdateien geladen. Diese Liste kann später in den Admin-Einstellungen bearbeitet werden.",
        clickLocaleHint: "Klicke auf eine Sprache, um die Sprache der Einrichtung zu wechseln.",
        initialize: "Anwendung initialisieren",
        initializing: "Initialisiere...",
        alreadyConfiguredTitle: "Anwendung bereits konfiguriert",
        alreadyConfiguredDescription: "Die Einrichtung ist deaktiviert, da die Initialisierung bereits abgeschlossen ist.",
        goToLogin: "Zum Login",
    },
    "pt-BR": {
        title: "Configuração inicial",
        subtitle: "Conclua esta configuração única para inicializar o aplicativo.",
        initialSetupToken: "Token inicial de configuração",
        siteName: "Nome do site",
        supportedLocales: "Idiomas suportados",
        defaultLocale: "Idioma padrão",
        adminEmail: "E-mail do administrador",
        adminPassword: "Senha do administrador",
        localesHint: "Carregado a partir dos arquivos de idioma iniciais. Você pode editar esta lista depois em Configurações de administrador.",
        clickLocaleHint: "Clique em um idioma para trocar o idioma da configuração.",
        initialize: "Inicializar aplicativo",
        initializing: "Inicializando...",
        alreadyConfiguredTitle: "Aplicativo já configurado",
        alreadyConfiguredDescription: "A configuração está desativada porque a inicialização já foi concluída.",
        goToLogin: "Ir para login",
    },
    "zh-CN": {
        title: "首次运行设置",
        subtitle: "完成此一次性设置以初始化应用。",
        initialSetupToken: "初始设置令牌",
        siteName: "站点名称",
        supportedLocales: "支持的语言",
        defaultLocale: "默认语言",
        adminEmail: "管理员邮箱",
        adminPassword: "管理员密码",
        localesHint: "已从初始语言文件加载。你可以稍后在管理员设置中编辑此列表。",
        clickLocaleHint: "点击语言标签以切换设置语言。",
        initialize: "初始化应用",
        initializing: "正在初始化...",
        alreadyConfiguredTitle: "应用已配置",
        alreadyConfiguredDescription: "设置已禁用，因为初始化已完成。",
        goToLogin: "前往登录",
    },
    ja: {
        title: "初期セットアップ",
        subtitle: "この一回限りのセットアップを完了してアプリを初期化してください。",
        initialSetupToken: "初期セットアップトークン",
        siteName: "サイト名",
        supportedLocales: "対応ロケール",
        defaultLocale: "デフォルトロケール",
        adminEmail: "管理者メール",
        adminPassword: "管理者パスワード",
        localesHint: "初期ロケールファイルから読み込まれます。この一覧は後で管理者設定で編集できます。",
        clickLocaleHint: "ロケールチップをクリックしてセットアップ言語を切り替えてください。",
        initialize: "アプリを初期化",
        initializing: "初期化中...",
        alreadyConfiguredTitle: "アプリは設定済みです",
        alreadyConfiguredDescription: "初期化が完了しているためセットアップは無効です。",
        goToLogin: "ログインへ",
    },
    ko: {
        title: "초기 설정",
        subtitle: "앱을 초기화하려면 이 1회성 설정을 완료하세요.",
        initialSetupToken: "초기 설정 토큰",
        siteName: "사이트 이름",
        supportedLocales: "지원 로케일",
        defaultLocale: "기본 로케일",
        adminEmail: "관리자 이메일",
        adminPassword: "관리자 비밀번호",
        localesHint: "초기 로케일 파일에서 불러옵니다. 이 목록은 나중에 관리자 설정에서 수정할 수 있습니다.",
        clickLocaleHint: "로케일 칩을 클릭해 설정 언어를 변경하세요.",
        initialize: "앱 초기화",
        initializing: "초기화 중...",
        alreadyConfiguredTitle: "앱이 이미 구성되었습니다",
        alreadyConfiguredDescription: "초기화가 완료되어 설정이 비활성화되었습니다.",
        goToLogin: "로그인으로 이동",
    },
    ar: {
        title: "إعداد التشغيل الأول",
        subtitle: "أكمل هذا الإعداد لمرة واحدة لتهيئة التطبيق.",
        initialSetupToken: "رمز الإعداد الأولي",
        siteName: "اسم الموقع",
        supportedLocales: "اللغات المدعومة",
        defaultLocale: "اللغة الافتراضية",
        adminEmail: "بريد المدير",
        adminPassword: "كلمة مرور المدير",
        localesHint: "تم تحميلها من ملفات اللغة الأولية. يمكنك تعديل هذه القائمة لاحقًا من إعدادات المسؤول.",
        clickLocaleHint: "انقر على شارة اللغة لتبديل لغة الإعداد.",
        initialize: "تهيئة التطبيق",
        initializing: "جارٍ التهيئة...",
        alreadyConfiguredTitle: "تم إعداد التطبيق بالفعل",
        alreadyConfiguredDescription: "تم تعطيل الإعداد لأن التهيئة اكتملت بالفعل.",
        goToLogin: "الذهاب إلى تسجيل الدخول",
    },
    hi: {
        title: "पहली बार सेटअप",
        subtitle: "एप्लिकेशन प्रारंभ करने के लिए यह एकबारगी सेटअप पूरा करें।",
        initialSetupToken: "प्रारंभिक सेटअप टोकन",
        siteName: "साइट नाम",
        supportedLocales: "समर्थित लोकैल",
        defaultLocale: "डिफ़ॉल्ट लोकैल",
        adminEmail: "एडमिन ईमेल",
        adminPassword: "एडमिन पासवर्ड",
        localesHint: "यह सूची प्रारंभिक लोकैल फ़ाइलों से लोड होती है। आप इसे बाद में एडमिन सेटिंग्स में बदल सकते हैं।",
        clickLocaleHint: "सेटअप भाषा बदलने के लिए लोकैल चिप पर क्लिक करें।",
        initialize: "एप्लिकेशन प्रारंभ करें",
        initializing: "प्रारंभ हो रहा है...",
        alreadyConfiguredTitle: "एप्लिकेशन पहले से कॉन्फ़िगर है",
        alreadyConfiguredDescription: "इनिशियलाइज़ेशन पूरा होने के कारण सेटअप बंद है।",
        goToLogin: "लॉगिन पर जाएँ",
    },
    ru: {
        title: "Первоначальная настройка",
        subtitle: "Завершите эту одноразовую настройку для инициализации приложения.",
        initialSetupToken: "Токен первоначальной настройки",
        siteName: "Название сайта",
        supportedLocales: "Поддерживаемые локали",
        defaultLocale: "Локаль по умолчанию",
        adminEmail: "Email администратора",
        adminPassword: "Пароль администратора",
        localesHint: "Список загружается из начальных файлов локалей. Позже его можно изменить в настройках администратора.",
        clickLocaleHint: "Нажмите на локаль, чтобы переключить язык настройки.",
        initialize: "Инициализировать приложение",
        initializing: "Инициализация...",
        alreadyConfiguredTitle: "Приложение уже настроено",
        alreadyConfiguredDescription: "Настройка отключена, так как инициализация уже выполнена.",
        goToLogin: "Перейти ко входу",
    },
};

export function getSetupCopy(locale: string): SetupCopy {
    const resolved = resolveSetupLocale(locale) ?? "en";
    const copy = SETUP_COPY_BY_LOCALE[resolved];

    return {
        ...ENGLISH_COPY,
        ...copy,
        validation: {
            ...ENGLISH_COPY.validation,
            ...(copy.validation ?? {}),
        },
    };
}
