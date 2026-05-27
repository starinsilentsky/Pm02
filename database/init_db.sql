-- ============================================================
--  Мем-музей | Скрипт инициализации базы данных
--  СУБД: PostgreSQL 15+
--  Включает: DDL, данные, 5 обязательных запросов
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
--  ТАБЛИЦЫ
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username         VARCHAR(50)  UNIQUE NOT NULL,
    email            VARCHAR(255) UNIQUE NOT NULL,
    hashed_password  VARCHAR(255),
    oauth_provider   VARCHAR(20),
    oauth_id         VARCHAR(100),
    display_name     VARCHAR(100),
    avatar_url       VARCHAR(500),
    bio              TEXT,
    role             VARCHAR(20)  DEFAULT 'visitor',
    is_active        BOOLEAN      DEFAULT TRUE,
    is_verified      BOOLEAN      DEFAULT FALSE,
    contributions_count INTEGER   DEFAULT 0,
    votes_count      INTEGER      DEFAULT 0,
    created_at       TIMESTAMP    DEFAULT NOW(),
    last_login       TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eras (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name             VARCHAR(100) UNIQUE NOT NULL,
    slug             VARCHAR(100) UNIQUE NOT NULL,
    start_year       INTEGER NOT NULL,
    end_year         INTEGER,
    description      TEXT,
    cultural_context TEXT,
    key_events       JSONB        DEFAULT '[]',
    cover_image      VARCHAR(500),
    timeline_data    JSONB        DEFAULT '{}',
    color            VARCHAR(7)   DEFAULT '#FF6B6B',
    created_at       TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    type        VARCHAR(50)  DEFAULT 'platform',
    platform    VARCHAR(50),
    description TEXT,
    url         VARCHAR(500),
    meta        JSONB        DEFAULT '{}',
    era_id      UUID         REFERENCES eras(id) ON DELETE SET NULL,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tags (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(50)  UNIQUE NOT NULL,
    slug        VARCHAR(50)  UNIQUE NOT NULL,
    category    VARCHAR(50)  DEFAULT 'general',
    description TEXT,
    color       VARCHAR(7)   DEFAULT '#4ECDC4',
    usage_count INTEGER      DEFAULT 0,
    is_nsfw     BOOLEAN      DEFAULT FALSE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memes (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title             VARCHAR(255) NOT NULL,
    slug              VARCHAR(255) UNIQUE NOT NULL,
    image_url         VARCHAR(500) NOT NULL,
    thumbnail_url     VARCHAR(500),
    video_url         VARCHAR(500),
    format            VARCHAR(20)  DEFAULT 'image',
    description       TEXT,
    origin_story      TEXT,
    cultural_context  TEXT,
    year              INTEGER NOT NULL,
    era_id            UUID NOT NULL REFERENCES eras(id)    ON DELETE CASCADE,
    source_id         UUID         REFERENCES sources(id)  ON DELETE SET NULL,
    original_platform VARCHAR(100),
    original_url      VARCHAR(500),
    status            VARCHAR(20)  DEFAULT 'published',
    is_rare           BOOLEAN      DEFAULT FALSE,
    is_nsfw           BOOLEAN      DEFAULT FALSE,
    views_count       INTEGER      DEFAULT 0,
    likes_count       INTEGER      DEFAULT 0,
    meta              JSONB        DEFAULT '{}',
    seo_title         VARCHAR(255),
    seo_description   TEXT,
    created_at        TIMESTAMP    DEFAULT NOW(),
    updated_at        TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memes_year    ON memes(year);
CREATE INDEX IF NOT EXISTS idx_memes_era_id  ON memes(era_id);
CREATE INDEX IF NOT EXISTS idx_memes_is_rare ON memes(is_rare);
CREATE INDEX IF NOT EXISTS idx_memes_status  ON memes(status);

-- M:N мемы ↔ теги
CREATE TABLE IF NOT EXISTS meme_tag_association (
    meme_id UUID REFERENCES memes(id) ON DELETE CASCADE,
    tag_id  UUID REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (meme_id, tag_id)
);

-- Самосвязь M:N — похожие мемы
CREATE TABLE IF NOT EXISTS similar_memes (
    meme_id         UUID REFERENCES memes(id) ON DELETE CASCADE,
    similar_meme_id UUID REFERENCES memes(id) ON DELETE CASCADE,
    similarity_score INTEGER DEFAULT 0,
    PRIMARY KEY (meme_id, similar_meme_id)
);

CREATE TABLE IF NOT EXISTS articles (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title            VARCHAR(255) NOT NULL,
    slug             VARCHAR(255) UNIQUE NOT NULL,
    type             VARCHAR(50)  DEFAULT 'article',
    content          TEXT,
    excerpt          TEXT,
    cover_image      VARCHAR(500),
    video_url        VARCHAR(500),
    author_id        UUID         REFERENCES users(id)  ON DELETE SET NULL,
    era_id           UUID         REFERENCES eras(id)   ON DELETE SET NULL,
    analyzed_meme_id UUID         REFERENCES memes(id)  ON DELETE SET NULL,
    status           VARCHAR(20)  DEFAULT 'draft',
    published_at     TIMESTAMP,
    views_count      INTEGER      DEFAULT 0,
    read_time        INTEGER      DEFAULT 0,
    meta             JSONB        DEFAULT '{}',
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS article_tags (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    tag        VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS era_map_points (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    era_id      UUID REFERENCES eras(id) ON DELETE CASCADE,
    lat         NUMERIC(9,6) NOT NULL,
    lng         NUMERIC(9,6) NOT NULL,
    title       VARCHAR(255),
    description TEXT,
    type        VARCHAR(50) DEFAULT 'meme_origin'
);

CREATE TABLE IF NOT EXISTS meme_suggestions (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES users(id) ON DELETE CASCADE,
    title          VARCHAR(255) NOT NULL,
    description    TEXT,
    image_url      VARCHAR(500),
    year           INTEGER,
    source_url     VARCHAR(500),
    status         VARCHAR(20)  DEFAULT 'pending',
    moderator_note TEXT,
    created_at     TIMESTAMP    DEFAULT NOW()
);

-- ============================================================
--  НАЧАЛЬНЫЕ ДАННЫЕ
-- ============================================================

INSERT INTO users (username, email, hashed_password, display_name, role) VALUES
('admin',           'admin@memorium.ru',      'hashed_password_here', 'Администратор',      'admin'),
('meme_researcher', 'researcher@memorium.ru', 'hashed_password_here', 'Исследователь мемов','researcher')
ON CONFLICT (username) DO NOTHING;

INSERT INTO eras (name, slug, start_year, end_year, description, cultural_context, color) VALUES
('Классическая эпоха', 'classic-era',  2000, 2009,
 'Зарождение интернет-мемов. Первые LOLcats, демотиваторы и вирусные картинки.',
 'Появление форумов, 4chan, зарождение мемной культуры', '#FF6B6B'),
('Эпоха расцвета',    'golden-era',   2010, 2019,
 'Расцвет социальных сетей. Мемы становятся языком поколения.',
 'Vine, Instagram, мемы-реакции, Grumpy Cat, Терстон', '#4ECDC4'),
('TikTok-эра',        'tiktok-era',   2020, NULL,
 'Тикток, ИИ-мемы, абсурдный юмор. Коты снова в топе.',
 'TikTok, нейросети, вирусные тренды, Шлепа, Мистер Фреш', '#A87CE8')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO sources (name, slug, type, platform, era_id) VALUES
('4chan',  '4chan',  'platform', 'Форум',   (SELECT id FROM eras WHERE slug='classic-era')),
('Reddit', 'reddit', 'platform', 'Соцсеть', (SELECT id FROM eras WHERE slug='golden-era')),
('TikTok', 'tiktok', 'platform', 'Соцсеть', (SELECT id FROM eras WHERE slug='tiktok-era'))
ON CONFLICT (slug) DO NOTHING;

INSERT INTO tags (name, slug, category, color) VALUES
('ИИ',       'ai',       'technology', '#FF6B6B'),
('хоррор',   'horror',   'genre',      '#6B5B95'),
('радость',  'joy',      'emotion',    '#F7C948'),
('грусть',   'sadness',  'emotion',    '#88B04B'),
('классика', 'classic',  'category',   '#FF6B6B'),
('вирусный', 'viral',    'category',   '#4ECDC4'),
('танцы',    'dance',    'action',     '#F7C948'),
('абсурд',   'absurd',   'genre',      '#FF9900')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO memes (title, slug, image_url, description, origin_story, year, era_id, source_id, format, is_rare) VALUES
('Every time you..., God kills a kitten', 'god-kills-kitten',
 '/images/Every_time_u_write_bad_code_god_kills_a_kitten.jpg',
 'Картинка с котёнком, за которым гонятся два маскота Domo',
 'Создана пользователем сайта Fark в 2002 году, стала интернет-мемом',
 2002, (SELECT id FROM eras WHERE slug='classic-era'), (SELECT id FROM sources WHERE slug='4chan'), 'image', FALSE),

('Lolcat', 'lolcat', '/images/Lolcat.jpg',
 'Кот со смешной подписью с намеренными грамматическими ошибками',
 'Зародился на 4chan в 2006 году, популярность принёс сайт icanhascheezburger.com',
 2006, (SELECT id FROM eras WHERE slug='classic-era'), (SELECT id FROM sources WHERE slug='4chan'), 'image', FALSE),

('Longcat', 'longcat', '/images/Longcat.jpg',
 'Белый кот, туловище которого растянуто в десятки раз в фотошопе',
 'Придуман японцами на имиджборде Futaba в 2006 году, оригинальное имя — Nobiiru',
 2006, (SELECT id FROM eras WHERE slug='classic-era'), (SELECT id FROM sources WHERE slug='4chan'), 'image', FALSE),

('Ceiling Cat (Потолкот)', 'ceiling-cat', '/images/Ceiling_Cat.jpg',
 'Рыжая полосатая кошка, выглядывающая из-за потолка',
 'Классический лолкот, символ игривого духа интернета',
 2006, (SELECT id FROM eras WHERE slug='classic-era'), (SELECT id FROM sources WHERE slug='4chan'), 'image', FALSE),

('Погладь кота (манул)', 'pet-the-cat', '/images/Pet_the_cat.jpg',
 'Манул с недружелюбным выражением морды',
 'Стал символом Рунета в 2008 году, демотиватор с призывом погладить',
 2008, (SELECT id FROM eras WHERE slug='classic-era'), NULL, 'image', FALSE),

('Happy Happy Happy Cat', 'happy-cat', '/images/Happy_happy_happy_cat.jpg',
 'Кот, танцующий на задних лапах под песню My Happy Song',
 'Оригинальное видео загружено на YouTube в ноябре 2015 года',
 2015, (SELECT id FROM eras WHERE slug='golden-era'), NULL, 'video', FALSE),

('Кот Thurston (Терстон)', 'thurston-the-cat', '/images/Cat_Thurston.jpg',
 'Кот с необычным мяуканьем, звезда Vine',
 'Родился в 2007 году в Северной Дакоте, спасён из приюта. Умер от рака 8 сентября 2022 года',
 2013, (SELECT id FROM eras WHERE slug='golden-era'), (SELECT id FROM sources WHERE slug='reddit'), 'video', FALSE),

('Кричащий кот', 'screaming-cat', '/images/Cat_is_screaming.jpg',
 'Кот лежит на спине и истошно орёт, повышая тон до визга',
 'Видео с ветеринарной клиники, где коту ректально измеряют температуру',
 2010, (SELECT id FROM eras WHERE slug='golden-era'), NULL, 'video', FALSE),

('Кот пилит ногти', 'cat-filing-claws', '/images/Cat_is_sharpening_its_claws.jpg',
 'Чёрный кот изящно подпиливает когти пилочкой',
 'Анимация появилась в Twitter в 2015 году, символ самодовольства',
 2015, (SELECT id FROM eras WHERE slug='golden-era'), (SELECT id FROM sources WHERE slug='reddit'), 'image', FALSE),

('Grumpy Cat (Барбара)', 'grumpy-cat', '/images/Grumpy_Cat.jpg',
 'Серая кошка с сердитым выражением морды',
 'Прославилась в 2012 году благодаря своей естественной мимике',
 2012, (SELECT id FROM eras WHERE slug='golden-era'), NULL, 'image', FALSE),

('Кот Максвелл', 'maxwell-the-cat', '/images/Maxwell_the_cat.jpg',
 'Черно-белый кот, крутящийся вокруг своей оси',
 '3D-модель из игры Garry''s Mod, создана по фото кошки Джесс',
 2017, (SELECT id FROM eras WHERE slug='golden-era'), (SELECT id FROM sources WHERE slug='reddit'), 'image', FALSE),

('Бу, испугался? Не бойся, я друг', 'boo-are-you-scared', '/images/Boo_Are_you_scared.jpg',
 'Кукольный кот Mr Whiskers, оживлённый нейросетями',
 'Из шоу TV Funhouse, стал вирусным в октябре 2024 года',
 2024, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Кот спрашивает «А?»', 'bender-the-cat', '/images/Huh.jpg',
 'Черно-белый кот Бендер с недоуменным выражением',
 'Австралийский кот, стал вирусным в феврале 2022 года после добавления звука «А?»',
 2022, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Мистер Фреш', 'mr-fresh', '/images/Mr_Fresh.jpg',
 'Рыжий кот, требующий только свежий корм',
 'Из приложения Hello Street Cat. За его голову назначали награду, позже спасён',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'image', TRUE),

('Crunchy cat', 'crunchy-cat', '/images/Crunchy_cat.jpg',
 'Кошка Луна с заразительным хрустом корма',
 'Стала популярной в конце 2023 года',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Vibing cat', 'vibing-cat', '/images/Vibing_cat.jpg',
 'Белый кот ритмично качает головой в такт музыке',
 'Оригинальное видео появилось в TikTok в апреле 2020 года',
 2020, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Уставший кот (Clap cat)', 'tired-cat', '/images/Tired_cat.jpg',
 'Тёмно-серый кот лежит на спине, высунув язык',
 'Стал вирусным в конце 2023 года, символ тотальной усталости',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Sad banana cat', 'sad-banana-cat', '/images/Sad_banana_cat.jpg',
 'Кот в костюме банана, грустный и плачущий',
 'Создан пользователем Sin Achilles в 2023 году, стал лицом грусти',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), NULL, 'image', FALSE),

('Голодный кот Персик', 'hungry-cat-peach', '/images/hungry_cat.jpg',
 'Бело-рыжий кот стучит миской по полу, требуя еды',
 'Видео выложила хозяйка весной 2023 года',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Dancing cat (Avril Lavigne)', 'dancing-cat', '/images/Dancing_cat.jpg',
 'Черно-белая пушистая кошка танцует под песню Girlfriend',
 'Опубликовано в китайском TikTok в октябре 2023 года',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Спорящие коты', 'arguing-cats', '/images/Arguing_cats.jpg',
 'Рыжий и серый кот эмоционально спорят друг с другом',
 'Рыжий кот из аккаунта Remorino Cat (февраль 2023)',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Кот бьёт другого кота', 'cat-hitting-cat', '/images/Cat_is_hitting_another_cat.jpg',
 'Рыжий кот бьёт лапой рыже-белого кота на столе',
 'Стал вирусным в ноябре 2023 года',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Кот за рулём (Луи)', 'cat-driving', '/images/Cat_is_driving.jpg',
 'Бело-серый кот Луи сидит за рулём и поворачивает руль',
 'Видео опубликовала хозяйка в феврале 2023 года',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Cat zoning out', 'cat-zoning-out', '/images/Cat_zoning_out.jpg',
 'Чёрный кот неподвижно смотрит на другого кота, уйдя в мысли',
 'Оригинальное видео из TikTok, март 2023 года',
 2023, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Кота тошнит', 'cat-is-sick', '/images/Cat_is_sick.jpg',
 'Белый кот с рвотными позывами, таращит глаза и высовывает язык',
 'Видео из TikTok, сентябрь 2021 года, реакция на йогурт',
 2021, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Dramatic kitten', 'dramatic-kitten', '/images/Dramatic_kitten.jpg',
 'Серый котёнок держится лапками за голову и кричит',
 'Стал вирусным в TikTok в конце 2021 года, символ отчаяния',
 2021, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Кот танцует тектоник', 'tectonic-cat', '/images/Cat_is_dancing_tectonics.jpg',
 'Кот танцует тектоник, оживлённый нейросетью',
 'Тренд из Китая, начало 2024 года',
 2024, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'video', FALSE),

('Wet Cat', 'wet-cat', '/images/Wet_Cat.jpg',
 'Мокрый серый кот с печальным взглядом',
 'Точное происхождение неизвестно, сопровождается трагичной музыкой',
 2022, (SELECT id FROM eras WHERE slug='tiktok-era'), NULL, 'video', FALSE),

('Pop cat', 'pop-cat', '/images/Pop_cat.jpg',
 'Белый кот открывает рот со звуком pop-pop-pop',
 'Пришёл от кота Овсянка в Twitter, октябрь 2020 года',
 2020, (SELECT id FROM eras WHERE slug='tiktok-era'), (SELECT id FROM sources WHERE slug='tiktok'), 'image', FALSE),

('Кот Степан', 'stepan-the-cat', '/images/Stepan_the_cat.jpg',
 'Рыжий кот из Харькова с бокалом вина',
 'Стал известен после публикации Бритни Спирс в ноябре 2021 года',
 2021, (SELECT id FROM eras WHERE slug='tiktok-era'), NULL, 'image', FALSE),

('Шлепа (Гоша)', 'big-floppa', '/images/Big_Floppa.png',
 'Каракал Гоша с крупными ушами',
 'Родился в Киевском питомнике в 2017 году, мемы с 2020 года',
 2020, (SELECT id FROM eras WHERE slug='tiktok-era'), NULL, 'image', FALSE)
ON CONFLICT (slug) DO NOTHING;

-- Теги для мемов
INSERT INTO meme_tag_association (meme_id, tag_id) VALUES
((SELECT id FROM memes WHERE slug='god-kills-kitten'), (SELECT id FROM tags WHERE slug='classic')),
((SELECT id FROM memes WHERE slug='god-kills-kitten'), (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='lolcat'),           (SELECT id FROM tags WHERE slug='classic')),
((SELECT id FROM memes WHERE slug='lolcat'),           (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='longcat'),          (SELECT id FROM tags WHERE slug='classic')),
((SELECT id FROM memes WHERE slug='ceiling-cat'),      (SELECT id FROM tags WHERE slug='classic')),
((SELECT id FROM memes WHERE slug='pet-the-cat'),      (SELECT id FROM tags WHERE slug='classic')),
((SELECT id FROM memes WHERE slug='pet-the-cat'),      (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='happy-cat'),        (SELECT id FROM tags WHERE slug='joy')),
((SELECT id FROM memes WHERE slug='thurston-the-cat'), (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='thurston-the-cat'), (SELECT id FROM tags WHERE slug='sadness')),
((SELECT id FROM memes WHERE slug='screaming-cat'),    (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='cat-filing-claws'), (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='grumpy-cat'),       (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='maxwell-the-cat'),  (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='boo-are-you-scared'),(SELECT id FROM tags WHERE slug='ai')),
((SELECT id FROM memes WHERE slug='boo-are-you-scared'),(SELECT id FROM tags WHERE slug='horror')),
((SELECT id FROM memes WHERE slug='bender-the-cat'),   (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='mr-fresh'),         (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='vibing-cat'),       (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='tired-cat'),        (SELECT id FROM tags WHERE slug='sadness')),
((SELECT id FROM memes WHERE slug='tired-cat'),        (SELECT id FROM tags WHERE slug='viral')),
((SELECT id FROM memes WHERE slug='sad-banana-cat'),   (SELECT id FROM tags WHERE slug='sadness')),
((SELECT id FROM memes WHERE slug='dancing-cat'),      (SELECT id FROM tags WHERE slug='joy')),
((SELECT id FROM memes WHERE slug='dancing-cat'),      (SELECT id FROM tags WHERE slug='dance')),
((SELECT id FROM memes WHERE slug='tectonic-cat'),     (SELECT id FROM tags WHERE slug='ai')),
((SELECT id FROM memes WHERE slug='tectonic-cat'),     (SELECT id FROM tags WHERE slug='dance')),
((SELECT id FROM memes WHERE slug='dramatic-kitten'),  (SELECT id FROM tags WHERE slug='sadness')),
((SELECT id FROM memes WHERE slug='dramatic-kitten'),  (SELECT id FROM tags WHERE slug='viral'))
ON CONFLICT DO NOTHING;

-- Статья
INSERT INTO articles (title, slug, type, content, excerpt, author_id, era_id, status, published_at)
VALUES (
    'Разбор мема: кот спрашивает «А?»',
    'bender-cat-analysis',
    'article',
    'Полный разбор истории кота Бендера...',
    'Почему чёрно-белый кот стал символом недоумения',
    (SELECT id FROM users WHERE username='meme_researcher'),
    (SELECT id FROM eras WHERE slug='tiktok-era'),
    'published',
    NOW()
) ON CONFLICT (slug) DO NOTHING;

-- Предложение мема от пользователя
INSERT INTO meme_suggestions (user_id, title, description, year, source_url, status) VALUES (
    (SELECT id FROM users WHERE username='meme_researcher'),
    'Новый вирусный кот',
    'Забавный кот из нового тиктока',
    2024,
    'https://tiktok.com/@newcat',
    'pending'
);

-- ============================================================
--  ОБЯЗАТЕЛЬНЫЕ ЗАПРОСЫ (Задание ПМ02)
-- ============================================================

-- 1. SELECT с условием (WHERE)
--    Все мемы начиная с 2020 года с указанием редкости
SELECT title, year, format, is_rare
FROM memes
WHERE year >= 2020
ORDER BY year;

-- 2. INSERT — добавление нового тега
INSERT INTO tags (name, slug, category, color, usage_count)
VALUES ('ностальгия', 'nostalgia', 'emotion', '#C5A3FF', 0);

-- 3. UPDATE — увеличить счётчик просмотров конкретного мема
UPDATE memes
SET views_count = views_count + 1,
    updated_at  = NOW()
WHERE slug = 'bender-the-cat';

-- 4. DELETE — удалить необработанные предложения без привязки к пользователю
DELETE FROM meme_suggestions
WHERE status = 'pending'
  AND user_id IS NULL;

-- 5. SELECT с JOIN — мемы с названием эпохи и источника
SELECT
    m.title        AS мем,
    m.year         AS год,
    m.format       AS формат,
    e.name         AS эпоха,
    s.name         AS источник
FROM memes m
JOIN eras e    ON m.era_id    = e.id
LEFT JOIN sources s ON m.source_id = s.id
ORDER BY m.year, m.title;
