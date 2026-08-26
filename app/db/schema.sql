CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    publication_date TEXT,

    file_type TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    document_id INTEGER NOT NULL,
    section_title TEXT,
    section_order INTEGER NOT NULL,
    text TEXT NOT NULL,

    FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE,

    UNIQUE(document_id, section_order)
);

CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
    section_title,
    text,
    content='sections',
    content_rowid='id'
);


CREATE TRIGGER IF NOT EXISTS sections_ai
AFTER INSERT ON sections
BEGIN
    INSERT INTO sections_fts(
        rowid,
        section_title,
        text
    )
    VALUES (
        new.id,
        new.section_title,
        new.text
    );
END;

CREATE TRIGGER IF NOT EXISTS sections_ad
AFTER DELETE ON sections
BEGIN
    INSERT INTO sections_fts(
        sections_fts,
        rowid,
        section_title,
        text
    )
    VALUES (
        'delete',
        old.id,
        old.section_title,
        old.text
    );
END;


-- CREATE TRIGGER IF NOT EXISTS sections_au
-- AFTER UPDATE ON sections
-- BEGIN
--     INSERT INTO sections_fts(
--         sections_fts,
--         rowid,
--         section_title,
--         text
--     )
--     VALUES (
--         'delete',
--         old.id,
--         old.section_title,
--         old.text
--     );

--     INSERT INTO sections_fts(
--         rowid,
--         section_title,
--         text
--     )
--     VALUES (
--         new.id,
--         new.section_title,
--         new.text
--     );
-- END;
