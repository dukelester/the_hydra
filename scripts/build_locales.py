"""Write locale .po/.mo files for H.Y.D.R.A. chrome, privacy, and next steps."""

from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALE_DIR = ROOT / "locale"

# msgid -> {lang: msgstr}. English uses msgid as msgstr.
CATALOG = {
    "H.Y.D.R.A. is an evidence-first civic accountability platform: Human-centered Yield, Data, Rights and Accountability.": {
        "sw": "H.Y.D.R.A. ni rekodi ya kiraia inayotegemea ushahidi: Mavuno yanayomlenga binadamu, Data, Haki na Uwajibikaji.",
        "fr": "H.Y.D.R.A. est un registre civique fondé sur les preuves : rendement centré sur l’humain, données, droits et redevabilité.",
        "ar": "هيدرا سجل مدني مبني على الأدلة: عائد يضع الناس أولاً، وبيانات، وحقوق، ومساءلة.",
        "pt": "H.Y.D.R.A. é um registo cívico baseado em evidências: rendimento centrado nas pessoas, dados, direitos e responsabilização.",
    },
    "Skip to content": {
        "sw": "Nenda kwenye maudhui",
        "fr": "Aller au contenu",
        "ar": "تخطٍ إلى المحتوى",
        "pt": "Saltar para o conteúdo",
    },
    "Follow the money": {
        "sw": "Fuata pesa",
        "fr": "Suivre l’argent",
        "ar": "تابع المال",
        "pt": "Siga o dinheiro",
    },
    "Search projects": {
        "sw": "Tafuta miradi",
        "fr": "Rechercher des projets",
        "ar": "ابحث في المشاريع",
        "pt": "Pesquisar projetos",
    },
    "Search thousands of projects…": {
        "sw": "Tafuta maelfu ya miradi…",
        "fr": "Recherchez des milliers de projets…",
        "ar": "ابحث في آلاف المشاريع…",
        "pt": "Pesquise milhares de projetos…",
    },
    "Searching…": {
        "sw": "Inatafuta…",
        "fr": "Recherche…",
        "ar": "جارٍ البحث…",
        "pt": "A pesquisar…",
    },
    "Main": {"sw": "Kuu", "fr": "Principal", "ar": "رئيسي", "pt": "Principal"},
    "Explore": {"sw": "Chunguza", "fr": "Explorer", "ar": "استكشف", "pt": "Explorar"},
    "Projects": {"sw": "Miradi", "fr": "Projets", "ar": "المشاريع", "pt": "Projetos"},
    "Public works and budgets": {
        "sw": "Kazi za umma na bajeti",
        "fr": "Travaux publics et budgets",
        "ar": "أعمال عامة وميزانيات",
        "pt": "Obras públicas e orçamentos",
    },
    "Institutions": {"sw": "Taasisi", "fr": "Institutions", "ar": "المؤسسات", "pt": "Instituições"},
    "Departments and agencies": {
        "sw": "Idara na mashirika",
        "fr": "Ministères et agences",
        "ar": "وزارات وهيئات",
        "pt": "Departamentos e agências",
    },
    "Documents": {"sw": "Nyaraka", "fr": "Documents", "ar": "الوثائق", "pt": "Documentos"},
    "Source files and evidence": {
        "sw": "Faili za chanzo na ushahidi",
        "fr": "Fichiers sources et preuves",
        "ar": "ملفات المصدر والأدلة",
        "pt": "Ficheiros-fonte e evidências",
    },
    "Policies": {"sw": "Sera", "fr": "Politiques", "ar": "السياسات", "pt": "Políticas"},
    "Public rules and plans": {
        "sw": "Kanuni na mipango ya umma",
        "fr": "Règles et plans publics",
        "ar": "قواعد وخطط عامة",
        "pt": "Regras e planos públicos",
    },
    "Search": {"sw": "Tafuta", "fr": "Recherche", "ar": "بحث", "pt": "Pesquisar"},
    "Ranked civic search": {
        "sw": "Utafutaji wa kiraia uliopangwa",
        "fr": "Recherche civique classée",
        "ar": "بحث مدني مرتّب",
        "pt": "Pesquisa cívica ordenada",
    },
    "Compare": {"sw": "Linganisha", "fr": "Comparer", "ar": "قارن", "pt": "Comparar"},
    "Projects, counties, rankings": {
        "sw": "Miradi, kaunti, orodha",
        "fr": "Projets, comtés, classements",
        "ar": "مشاريع، مقاطعات، ترتيب",
        "pt": "Projetos, condados, classificações",
    },
    "County report": {"sw": "Ripoti ya kaunti", "fr": "Rapport du comté", "ar": "تقرير المقاطعة", "pt": "Relatório do condado"},
    "Allocation and delivery charts": {
        "sw": "Chati za mgao na utekelezaji",
        "fr": "Graphiques d’allocation et d’exécution",
        "ar": "رسوم التخصيص والتنفيذ",
        "pt": "Gráficos de alocação e execução",
    },
    "Track my county": {"sw": "Fuatilia kaunti yangu", "fr": "Suivre mon comté", "ar": "تابع مقاطعتي", "pt": "Acompanhar o meu condado"},
    "Up to 4 areas": {"sw": "Hadi maeneo 4", "fr": "Jusqu’à 4 zones", "ar": "حتى 4 مناطق", "pt": "Até 4 áreas"},
    "Features": {"sw": "Vipengele", "fr": "Fonctionnalités", "ar": "الميزات", "pt": "Funcionalidades"},
    "About Hydra": {"sw": "Kuhusu Hydra", "fr": "À propos d’Hydra", "ar": "عن هيدرا", "pt": "Sobre a Hydra"},
    "How it works": {"sw": "Jinsi inavyofanya kazi", "fr": "Comment ça marche", "ar": "كيف يعمل", "pt": "Como funciona"},
    "Dashboard": {"sw": "Dashibodi", "fr": "Tableau de bord", "ar": "لوحة التحكم", "pt": "Painel"},
    "Create account": {"sw": "Fungua akaunti", "fr": "Créer un compte", "ar": "إنشاء حساب", "pt": "Criar conta"},
    "Log in": {"sw": "Ingia", "fr": "Connexion", "ar": "تسجيل الدخول", "pt": "Entrar"},
    "Account menu for": {"sw": "Menyu ya akaunti ya", "fr": "Menu du compte pour", "ar": "قائمة الحساب لـ", "pt": "Menu da conta de"},
    "Profile": {"sw": "Wasifu", "fr": "Profil", "ar": "الملف", "pt": "Perfil"},
    "Investigations": {"sw": "Uchunguzi", "fr": "Enquêtes", "ar": "التحقيقات", "pt": "Investigações"},
    "Reports": {"sw": "Ripoti", "fr": "Rapports", "ar": "التقارير", "pt": "Relatórios"},
    "Admin dashboard": {"sw": "Dashibodi ya wafanyakazi", "fr": "Tableau de bord staff", "ar": "لوحة الإدارة", "pt": "Painel da equipa"},
    "Log out": {"sw": "Toka", "fr": "Déconnexion", "ar": "تسجيل الخروج", "pt": "Sair"},
    "Menu": {"sw": "Menyu", "fr": "Menu", "ar": "القائمة", "pt": "Menu"},
    "Mobile": {"sw": "Simu", "fr": "Mobile", "ar": "الجوال", "pt": "Telemóvel"},
    "Search projects…": {
        "sw": "Tafuta miradi…",
        "fr": "Rechercher des projets…",
        "ar": "ابحث في المشاريع…",
        "pt": "Pesquisar projetos…",
    },
    "Follow the money. Find the evidence. Take action. An evidence-first civic platform for public projects, budgets, and citizen observations.": {
        "sw": "Fuata pesa. Pata ushahidi. Chukua hatua. Jukwaa la kiraia linalotegemea ushahidi kwa miradi ya umma, bajeti, na maoni ya wananchi.",
        "fr": "Suivez l’argent. Trouvez les preuves. Agissez. Une plateforme civique fondée sur les preuves pour les projets publics, les budgets et les observations citoyennes.",
        "ar": "تابع المال. اعثر على الدليل. اتخذ خطوة. منصة مدنية مبنية على الأدلة للمشاريع العامة والميزانيات وملاحظات المواطنين.",
        "pt": "Siga o dinheiro. Encontre a evidência. Aja. Uma plataforma cívica baseada em evidências para projetos públicos, orçamentos e observações cidadãs.",
    },
    "Investigate a project": {
        "sw": "Chunguza mradi",
        "fr": "Enquêter sur un projet",
        "ar": "حقّق في مشروع",
        "pt": "Investigar um projeto",
    },
    "Follow": {"sw": "Fuata", "fr": "Suivre", "ar": "تابع", "pt": "Seguir"},
    "Learn": {"sw": "Jifunze", "fr": "Comprendre", "ar": "تعرّف", "pt": "Saber mais"},
    "Account": {"sw": "Akaunti", "fr": "Compte", "ar": "الحساب", "pt": "Conta"},
    "Terms of use": {"sw": "Masharti ya matumizi", "fr": "Conditions d’utilisation", "ar": "شروط الاستخدام", "pt": "Termos de utilização"},
    "Privacy": {"sw": "Faragha", "fr": "Confidentialité", "ar": "الخصوصية", "pt": "Privacidade"},
    "Evidence and source documents are the source of truth. H.Y.D.R.A. does not determine guilt, corruption, or fraud.": {
        "sw": "Ushahidi na nyaraka za chanzo ndizo ukweli. H.Y.D.R.A. haiamui hatia, ufisadi, wala ulaghai.",
        "fr": "Les preuves et documents sources font foi. H.Y.D.R.A. ne statue pas sur la culpabilité, la corruption ou la fraude.",
        "ar": "الأدلة ووثائق المصدر هي مرجع الحقيقة. هيدرا لا تقرر الذنب أو الفساد أو الاحتيال.",
        "pt": "As evidências e os documentos-fonte são a verdade. A H.Y.D.R.A. não determina culpa, corrupção ou fraude.",
    },
    "Language": {"sw": "Lugha", "fr": "Langue", "ar": "اللغة", "pt": "Idioma"},
    "Apply": {"sw": "Tumia", "fr": "Appliquer", "ar": "تطبيق", "pt": "Aplicar"},
    "Use less data": {"sw": "Tumia data kidogo", "fr": "Utiliser moins de données", "ar": "استخدم بيانات أقل", "pt": "Usar menos dados"},
    "Use full pages": {"sw": "Tumia kurasa kamili", "fr": "Utiliser les pages complètes", "ar": "استخدم الصفحات الكاملة", "pt": "Usar páginas completas"},
    "Your information": {"sw": "Taarifa zako", "fr": "Vos informations", "ar": "معلوماتك", "pt": "Os seus dados"},
    "Observations can include sensitive civic, health, or education facts. H.Y.D.R.A. keeps identity and data as small as the work requires, and it does not treat an observation as a finding of guilt.": {
        "sw": "Maoni yanaweza kujumuisha mambo nyeti ya kiraia, afya, au elimu. H.Y.D.R.A. huhifadhi utambulisho na data kwa kiasi kinachohitajika tu, na haichukulii maoni kama uamuzi wa hatia.",
        "fr": "Une observation peut contenir des faits civiques, sanitaires ou éducatifs sensibles. H.Y.D.R.A. limite l’identité et les données au nécessaire, et ne traite pas une observation comme une déclaration de culpabilité.",
        "ar": "قد تتضمن الملاحظات معلومات مدنية أو صحية أو تعليمية حسّاسة. هيدرا تقلّل الهوية والبيانات إلى ما تحتاجه المهمة، ولا تعامل الملاحظة كحكم بالذنب.",
        "pt": "As observações podem incluir factos cívicos, de saúde ou educação sensíveis. A H.Y.D.R.A. guarda identidade e dados só o necessário, e não trata uma observação como um veredito de culpa.",
    },
    "What you can do without an account": {
        "sw": "Unachoweza kufanya bila akaunti",
        "fr": "Sans compte",
        "ar": "ما يمكنك فعله دون حساب",
        "pt": "O que pode fazer sem conta",
    },
    "You can search, read projects, and submit a citizen observation without signing in. Guest observations are stored as anonymous. The same browser session can open the observation you just sent; another person cannot.": {
        "sw": "Unaweza kutafuta, kusoma miradi, na kuwasilisha maoni ya mwananchi bila kuingia. Maoni ya mgeni huhifadhiwa kama yasiyo na jina. Kipindi kile kile cha kivinjari kinaweza kufungua maoni uliyotuma; mtu mwingine hawezi.",
        "fr": "Vous pouvez chercher, lire les projets et envoyer une observation sans compte. Les observations invitées sont anonymes. La même session de navigateur peut rouvrir celle que vous venez d’envoyer ; une autre personne ne le peut pas.",
        "ar": "يمكنك البحث وقراءة المشاريع وإرسال ملاحظة مواطن دون تسجيل الدخول. ملاحظات الزائر تُحفظ دون اسم. جلسة المتصفح نفسها يمكنها فتح الملاحظة التي أرسلتها؛ شخص آخر لا يستطيع.",
        "pt": "Pode pesquisar, ler projetos e enviar uma observação cidadã sem conta. Observações de convidado ficam anónimas. A mesma sessão do navegador pode abrir a que acabou de enviar; outra pessoa não pode.",
    },
    "What an account stores": {
        "sw": "Akaunti huhifadhi nini",
        "fr": "Ce qu’un compte conserve",
        "ar": "ماذا يخزّن الحساب",
        "pt": "O que uma conta guarda",
    },
    "An account keeps investigations, reports, tracked projects, favourites, and area watches with you. Username is required. Email is optional, and is only needed to reset a forgotten password. Display name, affiliation, and area are optional profile fields — not a public score.": {
        "sw": "Akaunti huhifadhi uchunguzi, ripoti, miradi inayofuatiliwa, vipendwa, na maeneo unayotazama. Jina la mtumiaji linahitajika. Barua pepe ni hiari, na inahitajika tu kuweka upya nenosiri. Jina la kuonyesha, uhusiano, na eneo ni sehemu za wasifu — si alama ya umma.",
        "fr": "Un compte conserve enquêtes, rapports, projets suivis, favoris et zones. Le nom d’utilisateur est obligatoire. L’e-mail est facultatif, utile seulement pour réinitialiser un mot de passe. Nom affiché, affiliation et zone sont optionnels — pas un score public.",
        "ar": "الحساب يحفظ التحقيقات والتقارير والمشاريع المتابعة والمفضّلة والمناطق. اسم المستخدم مطلوب. البريد اختياري ويُستخدم فقط لإعادة كلمة المرور. الاسم المعروض والجهة والمنطقة حقول اختيارية — وليست درجة عامة.",
        "pt": "Uma conta guarda investigações, relatórios, projetos seguidos, favoritos e áreas. O nome de utilizador é obrigatório. O e-mail é opcional e só serve para repor a palavra-passe. Nome visível, afiliação e área são opcionais — não são uma pontuação pública.",
    },
    "Anonymous observations": {
        "sw": "Maoni yasiyo na jina",
        "fr": "Observations anonymes",
        "ar": "ملاحظات دون اسم",
        "pt": "Observações anónimas",
    },
    "If you are signed in, you can choose not to show your account name on an observation. The record still stays in your list so you can find it later. Do not put other people’s private details in the text or in uploads.": {
        "sw": "Ukiwa umeingia, unaweza kuficha jina la akaunti kwenye maoni. Rekodi bado inabaki kwenye orodha yako. Usiweke taarifa binafsi za watu wengine kwenye maandishi au faili.",
        "fr": "Connecté, vous pouvez masquer le nom du compte sur une observation. L’enregistrement reste dans votre liste. N’ajoutez pas les données privées d’autrui dans le texte ou les fichiers.",
        "ar": "إن كنت مسجّلاً يمكنك إخفاء اسم حسابك على الملاحظة. السجل يبقى في قائمتك. لا تضع بيانات خاصة بآخرين في النص أو الملفات.",
        "pt": "Com sessão iniciada, pode ocultar o nome da conta numa observação. O registo fica na sua lista. Não coloque dados privados de outras pessoas no texto ou nos ficheiros.",
    },
    "Files you upload": {
        "sw": "Faili unazopakia",
        "fr": "Fichiers envoyés",
        "ar": "الملفات التي ترفعها",
        "pt": "Ficheiros que envia",
    },
    "Photos and documents are stored on disk so staff can review them. Upload only what supports the observation. Remove faces, house numbers, and identity documents that are not needed.": {
        "sw": "Picha na nyaraka huhifadhiwa diski ili wafanyakazi wapitie. Pakia tu kinachounga mkono maoni. Ondoa nyuso, namba za nyumba, na vitambulisho visivyohitajika.",
        "fr": "Photos et documents sont stockés pour relecture. N’envoyez que ce qui appuie l’observation. Retirez visages, numéros de maison et pièces d’identité inutiles.",
        "ar": "تُحفظ الصور والوثائق على القرص للمراجعة. ارفع فقط ما يدعم الملاحظة. احذف الوجوه وأرقام المنازل ووثائق الهوية غير اللازمة.",
        "pt": "Fotos e documentos ficam no disco para revisão. Envie só o que apoia a observação. Remova rostos, números de casa e documentos de identidade desnecessários.",
    },
    "How we protect the session": {
        "sw": "Jinsi tunavyolinda kipindi",
        "fr": "Protection de la session",
        "ar": "كيف نحمي الجلسة",
        "pt": "Como protegemos a sessão",
    },
    "Session cookies are HTTP-only. Pages do not send your referrer to other sites. The public record does not publish a guilt, corruption, or trust score against a person or a county.": {
        "sw": "Vidakuzi vya kipindi ni HTTP-only. Kurasa hazitumi referrer kwenda tovuti nyingine. Rekodi ya umma haichapishi alama ya hatia, ufisadi, au uaminifu dhidi ya mtu au kaunti.",
        "fr": "Les cookies de session sont HTTP-only. Les pages n’envoient pas le referrer vers d’autres sites. Le registre public ne publie pas de score de culpabilité, corruption ou confiance contre une personne ou un comté.",
        "ar": "كوكيز الجلسة HTTP-only. الصفحات لا ترسل المُحيل إلى مواقع أخرى. السجل العام لا ينشر درجة ذنب أو فساد أو ثقة ضد شخص أو مقاطعة.",
        "pt": "Os cookies de sessão são HTTP-only. As páginas não enviam o referrer a outros sítios. O registo público não publica uma pontuação de culpa, corrupção ou confiança contra uma pessoa ou um condado.",
    },
    "Language and access": {
        "sw": "Lugha na ufikiaji",
        "fr": "Langue et accès",
        "ar": "اللغة والوصول",
        "pt": "Idioma e acesso",
    },
    "Choose English, Kiswahili, French, Arabic, or Portuguese in the footer. Use less data to skip web fonts and heavy previews on a slow connection.": {
        "sw": "Chagua Kiingereza, Kiswahili, Kifaransa, Kiarabu, au Kireno kwenye kijachini. Tumia data kidogo ili kuruka fonti za mtandao na hakikisho zito kwenye mtandao wa polepole.",
        "fr": "Choisissez l’anglais, le kiswahili, le français, l’arabe ou le portugais en pied de page. « Moins de données » évite les polices web et les aperçus lourds sur une connexion lente.",
        "ar": "اختر الإنجليزية أو السواحيلية أو الفرنسية أو العربية أو البرتغالية من التذييل. استخدم بيانات أقل لتجاوز خطوط الويب والمعاينات الثقيلة على اتصال بطيء.",
        "pt": "Escolha inglês, suaíli, francês, árabe ou português no rodapé. Use menos dados para saltar fontes web e pré-visualizações pesadas numa ligação lenta.",
    },
    "After the file": {"sw": "Baada ya faili", "fr": "Après le dossier", "ar": "بعد الملف", "pt": "Depois do ficheiro"},
    "What you can do next": {
        "sw": "Unachoweza kufanya baadaye",
        "fr": "Que faire ensuite",
        "ar": "ماذا يمكنك أن تفعل بعد ذلك",
        "pt": "O que pode fazer a seguir",
    },
    "Finding the record is only the start. These steps are written for Kenya first. They are not legal advice, and they do not decide guilt.": {
        "sw": "Kupata rekodi ni mwanzo tu. Hatua hizi zimeandikwa kwa Kenya kwanza. Si ushauri wa kisheria, wala haziamui hatia.",
        "fr": "Trouver le dossier n’est que le début. Ces étapes sont rédigées d’abord pour le Kenya. Ce n’est pas un conseil juridique et cela ne statue pas sur la culpabilité.",
        "ar": "العثور على السجل مجرد بداية. هذه الخطوات كُتبت لكينيا أولاً. ليست استشارة قانونية ولا تقرر الذنب.",
        "pt": "Encontrar o registo é só o começo. Estes passos foram escritos primeiro para o Quénia. Não são aconselhamento jurídico e não decidem culpa.",
    },
    "your county": {"sw": "kaunti yako", "fr": "votre comté", "ar": "مقاطعتك", "pt": "o seu condado"},
    "the responsible office": {
        "sw": "ofisi husika",
        "fr": "le service responsable",
        "ar": "المكتب المسؤول",
        "pt": "o serviço responsável",
    },
    "1 · The file": {"sw": "1 · Faili", "fr": "1 · Le dossier", "ar": "1 · الملف", "pt": "1 · O ficheiro"},
    "Read what is missing": {
        "sw": "Soma kilichokosekana",
        "fr": "Lire ce qui manque",
        "ar": "اقرأ ما ينقص",
        "pt": "Leia o que falta",
    },
    "This page lists claims, sources, and gaps. If a stage says evidence is unavailable, that is the starting point — not a finding of wrongdoing.": {
        "sw": "Ukurasa huu unaorodhesha madai, vyanzo, na pengo. Ikiwa hatua inasema ushahidi haupatikani, hapo ndipo unapoanza — si uamuzi wa kosa.",
        "fr": "Cette page liste revendications, sources et lacunes. Si une étape dit que la preuve est indisponible, c’est le point de départ — pas une constatation de faute.",
        "ar": "هذه الصفحة تسرد الادعاءات والمصادر والفجوات. إن قالت مرحلة إن الدليل غير متاح، فهذه نقطة البداية — وليست حكماً بخطأ.",
        "pt": "Esta página lista alegações, fontes e lacunas. Se uma etapa diz que a evidência está indisponível, esse é o ponto de partida — não um achado de irregularidade.",
    },
    "Read the timeline, budget, and source documents. Note what the file actually supports before you act.": {
        "sw": "Soma ratiba, bajeti, na nyaraka. Kumbuka kile faili inasaidia kabla ya kuchukua hatua.",
        "fr": "Lisez le calendrier, le budget et les documents. Notez ce que le dossier étaye réellement avant d’agir.",
        "ar": "اقرأ الجدول الزمني والميزانية ووثائق المصدر. سجّل ما يدعمه الملف فعلاً قبل أن تتصرف.",
        "pt": "Leia o calendário, o orçamento e os documentos. Note o que o ficheiro realmente sustenta antes de agir.",
    },
    "2 · The office": {"sw": "2 · Ofisi", "fr": "2 · Le service", "ar": "2 · المكتب", "pt": "2 · O serviço"},
    "Ask %(institution)s": {
        "sw": "Andikia %(institution)s",
        "fr": "Écrire à %(institution)s",
        "ar": "اسأل %(institution)s",
        "pt": "Peça a %(institution)s",
    },
    "Write to the implementing office and ask for the missing pages: budget vote, tender, contract, or completion certificate. Name the project and the financial year. Keep a copy of what you send.": {
        "sw": "Andikia ofisi inayotekeleza uombe kurasa zinazokosekana: kura ya bajeti, zabuni, mkataba, au cheti cha kukamilika. Taja mradi na mwaka wa fedha. Weka nakala ya ulichotuma.",
        "fr": "Écrivez au service d’exécution et demandez les pages manquantes : vote budgétaire, appel d’offres, contrat ou certificat d’achèvement. Nommez le projet et l’exercice. Conservez une copie.",
        "ar": "اكتب إلى جهة التنفيذ واطلب الصفحات الناقصة: اعتماد الميزانية أو المناقصة أو العقد أو شهادة الإنجاز. سمِّ المشروع والسنة المالية. احتفظ بنسخة مما ترسل.",
        "pt": "Escreva ao serviço executor e peça as páginas em falta: voto orçamental, concurso, contrato ou certificado de conclusão. Nomeie o projeto e o ano financeiro. Guarde cópia do que enviar.",
    },
    "3 · The law": {"sw": "3 · Sheria", "fr": "3 · La loi", "ar": "3 · القانون", "pt": "3 · A lei"},
    "Request information in writing": {
        "sw": "Omba taarifa kwa maandishi",
        "fr": "Demander l’information par écrit",
        "ar": "اطلب المعلومات كتابةً",
        "pt": "Peça informação por escrito",
    },
    "In Kenya, the Access to Information Act, 2016 lets you ask a public body for records. Say what you need, why it is a public project file, and where to send the reply. If there is no useful answer, the Commission on Administrative Justice (Office of the Ombudsman) is the national oversight office for access to information.": {
        "sw": "Nchini Kenya, Sheria ya Upatikanaji wa Taarifa, 2016 inakuruhusu kuomba rekodi kutoka kwa chombo cha umma. Sema unachohitaji, kwa nini ni faili ya mradi wa umma, na wapi kujibu. Bila jibu la maana, Tume ya Haki za Utawala (Ofisi ya Ombudsman) ndiyo ofisi ya kitaifa ya usimamizi wa upatikanaji wa taarifa.",
        "fr": "Au Kenya, la loi de 2016 sur l’accès à l’information permet de demander des dossiers à un organisme public. Précisez ce dont vous avez besoin, pourquoi il s’agit d’un projet public, et où répondre. Sans réponse utile, la Commission de la justice administrative (médiateur) est l’organe national de contrôle de l’accès à l’information.",
        "ar": "في كينيا يتيح قانون الوصول إلى المعلومات لعام 2016 أن تطلب سجلات من هيئة عامة. بيّن ما تحتاجه ولماذا هو ملف مشروع عام وأين يُرسل الرد. إن لم يأتِ جواب مفيد، فاللجنة المعنية بالعدالة الإدارية (ديوان المظالم) هي جهة الرقابة الوطنية للوصول إلى المعلومات.",
        "pt": "No Quénia, a Lei de Acesso à Informação de 2016 permite pedir registos a um organismo público. Diga o que precisa, porque é um ficheiro de projeto público e onde responder. Sem resposta útil, a Comissão de Justiça Administrativa (Provedor) é o órgão nacional de acesso à informação.",
    },
    "County: %(county)s": {
        "sw": "Kaunti: %(county)s",
        "fr": "Comté : %(county)s",
        "ar": "المقاطعة: %(county)s",
        "pt": "Condado: %(county)s",
    },
    "4 · What you saw": {"sw": "4 · Ulichoona", "fr": "4 · Ce que vous avez vu", "ar": "4 · ما رأيته", "pt": "4 · O que viu"},
    "Record a citizen observation": {
        "sw": "Andika maoni ya mwananchi",
        "fr": "Enregistrer une observation citoyenne",
        "ar": "سجّل ملاحظة مواطن",
        "pt": "Registar uma observação cidadã",
    },
    "If you visited the site, write what you saw, when, and where. You can submit without an account. Do not include other people’s private details. An observation is not a finding.": {
        "sw": "Ukienda kwenye eneo, andika ulichoona, lini, na wapi. Unaweza kuwasilisha bila akaunti. Usiweke taarifa binafsi za watu wengine. Maoni si uamuzi.",
        "fr": "Si vous êtes allé sur place, écrivez ce que vous avez vu, quand et où. Vous pouvez envoyer sans compte. N’incluez pas les données privées d’autrui. Une observation n’est pas une constatation.",
        "ar": "إن زرت الموقع فاكتب ما رأيته ومتى وأين. يمكنك الإرسال دون حساب. لا تدرج بيانات خاصة بآخرين. الملاحظة ليست حكماً.",
        "pt": "Se visitou o local, escreva o que viu, quando e onde. Pode enviar sem conta. Não inclua dados privados de outras pessoas. Uma observação não é um achado.",
    },
    "5 · A structured file": {
        "sw": "5 · Faili iliyopangwa",
        "fr": "5 · Un dossier structuré",
        "ar": "5 · ملف منظّم",
        "pt": "5 · Um ficheiro estruturado",
    },
    "Generate a private report": {
        "sw": "Tengeneza ripoti ya faragha",
        "fr": "Générer un rapport privé",
        "ar": "أنشئ تقريراً خاصاً",
        "pt": "Gerar um relatório privado",
    },
    "A report puts official information and your observation in separate columns. Keep it private until you choose to share it with an oversight office, a journalist, or the county assembly. It does not determine guilt.": {
        "sw": "Ripoti huweka taarifa rasmi na maoni yako kwenye safu tofauti. Iweke faragha hadi uchague kushiriki na ofisi ya usimamizi, mwandishi, au bunge la kaunti. Haiamui hatia.",
        "fr": "Un rapport sépare l’information officielle et votre observation. Gardez-le privé jusqu’à ce que vous le partagiez avec un organe de contrôle, un journaliste ou l’assemblée du comté. Il ne statue pas sur la culpabilité.",
        "ar": "يضع التقرير المعلومات الرسمية وملاحظتك في عمودين منفصلين. أبقه خاصاً حتى تختار مشاركته مع جهة رقابة أو صحفي أو مجلس المقاطعة. لا يقرر الذنب.",
        "pt": "Um relatório coloca a informação oficial e a sua observação em colunas separadas. Mantenha-o privado até o partilhar com um órgão de fiscalização, um jornalista ou a assembleia do condado. Não determina culpa.",
    },
}


def _escape_po(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def write_po(path: Path, language: str, catalog: dict[str, dict[str, str]]) -> None:
    lines = [
        'msgid ""',
        'msgstr ""',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Language: %s\\n"' % language,
        "",
    ]
    messages = {}
    for msgid, translations in catalog.items():
        messages[msgid] = msgid if language == "en" else translations[language]
    for msgid, msgstr in messages.items():
        lines.append('msgid "%s"' % _escape_po(msgid))
        lines.append('msgstr "%s"' % _escape_po(msgstr))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_mo(path: Path, catalog: dict[str, str]) -> None:
    items = sorted(catalog.items())
    keys = [key.encode("utf-8") for key, _ in items]
    vals = [value.encode("utf-8") for _, value in items]
    key_offsets = []
    val_offsets = []
    offset = 28 + 16 * len(items)
    for key in keys:
        key_offsets.append(offset)
        offset += len(key) + 1
    for val in vals:
        val_offsets.append(offset)
        offset += len(val) + 1
    output = bytearray()
    output += struct.pack("<Iiiiiii", 0x950412DE, 0, len(items), 28, 28 + 8 * len(items), 0, 0)
    for length, off in zip((len(k) for k in keys), key_offsets):
        output += struct.pack("<II", length, off)
    for length, off in zip((len(v) for v in vals), val_offsets):
        output += struct.pack("<II", length, off)
    for key in keys:
        output += key + b"\0"
    for val in vals:
        output += val + b"\0"
    path.write_bytes(output)


def main() -> None:
    for language in ("en", "sw", "fr", "ar", "pt"):
        directory = LOCALE_DIR / language / "LC_MESSAGES"
        directory.mkdir(parents=True, exist_ok=True)
        messages = {"": "Content-Type: text/plain; charset=UTF-8\nLanguage: %s\n" % language}
        messages.update(
            {
                msgid: msgid if language == "en" else translations[language]
                for msgid, translations in CATALOG.items()
            }
        )
        write_po(directory / "django.po", language, CATALOG)
        write_mo(directory / "django.mo", messages)
        print("wrote", directory / "django.mo")


if __name__ == "__main__":
    main()
