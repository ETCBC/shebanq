#!/usr/bin/env python
#-*- coding:utf-8 -*-

booklangs = dict(
    la=(u'latin', u'Latina'),
    en=(u'english', u'English'),
    fr=(u'french', u'François'),
    de=(u'german', u'Deutsch'),
    nl=(u'dutch', u'Nederlands'),
    el=(u'greek', u'Ελληνικά'),
    he=(u'hebrew', u'עברית'),
    ru=(u'russian', u'Русский'),
    es=(u'spanish', u'Español'),
    ko=(u'korean', u'한국어'),
)
booknames = dict(
    la=tuple(u'''
            Genesis
            Exodus
            Leviticus
            Numeri
            Deuteronomium
            Josua
            Judices
            Samuel_I
            Samuel_II
            Reges_I
            Reges_II
            Jesaia
            Jeremia
            Ezechiel
            Hosea
            Joel
            Amos
            Obadia
            Jona
            Micha
            Nahum
            Habakuk
            Zephania
            Haggai
            Sacharia
            Maleachi
            Psalmi
            Iob
            Proverbia
            Ruth
            Canticum
            Ecclesiastes
            Threni
            Esther
            Daniel
            Esra
            Nehemia
            Chronica_I
            Chronica_II
    '''.strip().split()),
    en=tuple(u'''
            Genesis
            Exodus
            Leviticus
            Numbers
            Deuteronomy
            Joshua
            Judges
            1_Samuel
            2_Samuel
            1_Kings
            2_Kings
            Isaiah
            Jeremiah
            Ezekiel
            Hosea
            Joel
            Amos
            Obadiah
            Jonah
            Micah
            Nahum
            Habakkuk
            Zephaniah
            Haggai
            Zechariah
            Malachi
            Psalms
            Job
            Proverbs
            Ruth
            Song_of_songs
            Ecclesiastes
            Lamentations
            Esther
            Daniel
            Ezra
            Nehemiah
            1_Chronicles
            2_Chronicles
    '''.strip().split()),
    nl=tuple(u'''
            Genesis
            Exodus
            Leviticus
            Numeri
            Deuteronomium
            Jozua
            Richteren
            1_Samuel
            2_Samuel
            1_Koningen
            2_Koningen
            Jesaja
            Jeremia
            Ezechiel
            Hosea
            Joël
            Amos
            Obadja
            Jona
            Micha
            Nahum
            Habakuk
            Zefanja
            Haggaï
            Zacharia
            Maleachi
            Psalmen
            Job
            Spreuken
            Ruth
            Hooglied
            Prediker
            Klaagliederen
            Esther
            Daniel
            Ezra
            Nehemia
            1_Kronieken
            2_Kronieken
        '''.strip().split()),
    de=tuple(u'''
            Genesis
            Exodus
            Levitikus
            Numeri
            Deuteronomium
            Josua
            Richter
            1_Samuel
            2_Samuel
            1_Könige
            2_Könige
            Jesaja
            Jeremia
            Ezechiel
            Hosea
            Joel
            Amos
            Obadja
            Jona
            Micha
            Nahum
            Habakuk
            Zefanja
            Haggai
            Sacharja
            Maleachi
            Psalmen
            Ijob
            Sprichwörter
            Rut
            Hoheslied
            Kohelet
            Klagelieder
            Ester
            Daniel
            Esra
            Nehemia
            1_Chronik
            2_Chronik
        '''.strip().split()),
    fr=tuple(u'''
            Genèse
            Exode
            Lévitique
            Nombres
            Deutéronome
            Josué
            Juges
            1_Samuel
            2_Samuel
            1_Rois
            2_Rois
            Isaïe
            Jérémie
            Ézéchiel
            Osée
            Joël
            Amos
            Abdias
            Jonas
            Michée
            Nahoum
            Habaquq
            Sophonie
            Aggée
            Zacharie
            Malachie
            Psaumes
            Job
            Proverbes
            Ruth
            Cantique_des_Cantiques
            Ecclésiaste
            Lamentations
            Esther
            Daniel
            Esdras
            Néhémie
            1_Chroniques
            2_Chroniques
        '''.strip().split()),
    el=tuple(u'''
            Γένεση
            Έξοδος
            Λευιτικό
            Αριθμοί
            Δευτερονόμιο
            Ιησούς
            Κριταί
            Σαμουήλ_A'                    
            Σαμουήλ_Β'
            Βασιλείς_A'
            Βασιλείς_Β'
            Ησαΐας
            Ιερεμίας
            Ιεζεκιήλ
            Ωσηέ
            Ιωήλ
            Αμώς
            Οβδιού
            Ιωνάς
            Μιχαίας
            Ναούμ
            Αβακκούμ
            Σοφονίας
            Αγγαίος
            Ζαχαρίας
            Μαλαχίας
            Ψαλμοί
            Ιώβ
            Παροιμίαι
            Ρουθ
            Άσμα_Ασμάτων
            Εκκλησιαστής
            Θρήνοι
            Εσθήρ
            Δανιήλ
            Έσδρας
            Νεεμίας
            Χρονικά_Α'
            Χρονικά_Β'
        '''.strip().split()),
    he=tuple(u'''
            בראשית
            שמות
            ויקרא
            במדבר
            דברים
            יהושע
            שופטים
            שמואל_א
            שמואל_ב
            מלכים_א
            מלכים_ב
            ישעיהו
            ירמיהו
            יחזקאל
            הושע
            יואל
            עמוס
            עובדיה
            יונה
            מיכה
            נחום
            חבקוק
            צפניה
            חגי
            זכריה
            מלאכי
            תהילים
            איוב
            משלי
            רות
            שיר_השירים
            קהלת
            איכה
            אסתר
            דניאל
            עזרא
            נחמיה
            דברי_הימים_א
            דברי_הימים_ב
        '''.strip().split()),
    ru=tuple(u'''
            Бытия
            Исход
            Левит
            Числа
            Второзаконие
            ИисусНавин
            КнигаСудей
            1-я_Царств
            2-я_Царств
            3-я_Царств
            4-я_Царств
            Исаия
            Иеремия
            Иезекииль
            Осия
            Иоиль
            Амос
            Авдия
            Иона
            Михей
            Наум
            Аввакум
            Софония
            Аггей
            Захария
            Малахия
            Псалтирь
            Иов
            Притчи
            Руфь
            ПесниПесней
            Екклесиаст
            ПлачИеремии
            Есфирь
            Даниил
            Ездра
            Неемия
            1-я_Паралипоменон
            2-я_Паралипоменон
    '''.strip().split()),
    es=tuple(u'''
            Génesis
            Éxodo
            Levítico
            Números
            Deuteronomio
            Josué
            Jueces
            1_Samuel
            2_Samuel
            1_Reyes
            2_Reyes
            Isaías
            Jeremías
            Ezequiel
            Oseas
            Joel
            Amós
            Abdías
            Jonás
            Miqueas
            Nahúm
            Habacuc
            Sofonías
            Hageo
            Zacarías
            Malaquías
            Salmos
            Job
            Proverbios
            Rut
            Cantares
            Eclesiastés
            Lamentaciones
            Ester
            Daniel
            Esdras
            Nehemías
            1_Crónicas
            2_Crónicas
    '''.strip().split()),
    ko=tuple(u'''
            창세기
            탈출기
            레위기
            민수기
            신명기
            여호수아
            재판관기
            사무엘_첫째
            사무엘_둘째
             열왕기_첫째
            열왕기_둘째
            이사야
            예레미야
            에스겔
            호세아
            요엘
            아모스
            오바댜
            요나
            미가
            나훔
            하박국
            스바냐
            학개
            스가랴
            말라기
            시편
            욥
            잠언
            룻
            솔로몬의_노래
            전도서
            애가
            에스더
            다니엘
            에스라
            느헤미야
            역대기_첫째
            역대기_둘째
    '''.strip().split()),
)
