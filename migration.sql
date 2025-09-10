CREATE TABLE IF NOT EXISTS lumibot_pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    titre TEXT,
    description TEXT,
    horodatage DATETIME DEFAULT CURRENT_TIMESTAMP,
    FULLTEXT(titre, description)
)
