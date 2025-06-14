-- Schema bazy danych dla Systemu Rekomendacji Tras Turystycznych
-- Etap 4: Integracja z bazą danych SQLite

-- Tabela tras turystycznych
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    region TEXT,
    start_lat REAL NOT NULL,
    start_lon REAL NOT NULL,
    end_lat REAL NOT NULL,
    end_lon REAL NOT NULL,
    length_km REAL,
    elevation_gain INTEGER,
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    terrain_type TEXT,
    tags TEXT,
    description TEXT,
    category TEXT DEFAULT 'sportowa',
    estimated_time REAL,
    user_rating REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela danych pogodowych
CREATE TABLE IF NOT EXISTS weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    location_lat REAL NOT NULL,
    location_lon REAL NOT NULL,
    avg_temp REAL,
    min_temp REAL,
    max_temp REAL,
    precipitation REAL,
    sunshine_hours REAL,
    cloud_cover INTEGER,
    wind_speed REAL,
    humidity INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, location_lat, location_lon)
);

-- Tabela preferencji użytkownika
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT DEFAULT 'default',
    preferred_temp_min REAL DEFAULT 15.0,
    preferred_temp_max REAL DEFAULT 25.0,
    max_precipitation REAL DEFAULT 5.0,
    max_difficulty INTEGER DEFAULT 3,
    max_length_km REAL DEFAULT 20.0,
    preferred_terrain_types TEXT DEFAULT 'górski,leśny',
    preferred_categories TEXT DEFAULT 'sportowa,widokowa',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela recenzji tras
CREATE TABLE IF NOT EXISTS route_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    review_text TEXT NOT NULL,
    rating REAL CHECK (rating BETWEEN 1.0 AND 5.0),
    sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    season TEXT,
    aspects TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

-- Tabela historii rekomendacji
CREATE TABLE IF NOT EXISTS recommendation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT DEFAULT 'default',
    search_criteria TEXT,
    recommended_routes TEXT,
    search_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indeksy dla wydajności
CREATE INDEX IF NOT EXISTS idx_routes_region ON routes(region);
CREATE INDEX IF NOT EXISTS idx_routes_difficulty ON routes(difficulty);
CREATE INDEX IF NOT EXISTS idx_routes_category ON routes(category);
CREATE INDEX IF NOT EXISTS idx_routes_terrain ON routes(terrain_type);
CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date);
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data(location_lat, location_lon);
CREATE INDEX IF NOT EXISTS idx_reviews_route ON route_reviews(route_id);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON route_reviews(sentiment);

-- Triggery do automatycznej aktualizacji timestamp
CREATE TRIGGER IF NOT EXISTS update_routes_timestamp 
    AFTER UPDATE ON routes
    FOR EACH ROW
    BEGIN
        UPDATE routes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_preferences_timestamp 
    AFTER UPDATE ON user_preferences
    FOR EACH ROW
    BEGIN
        UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END; 