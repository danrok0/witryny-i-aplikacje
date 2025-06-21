import sqlite3  # moduł do pracy z bazą danych SQLite

class Database:
    """
    Klasa do zarządzania bazą danych SQLite dla gry City Builder.
    
    Odpowiada za:
    - Tworzenie i zarządzanie tabelami w bazie danych
    - Zapisywanie i ładowanie stanu gry
    - Przechowywanie historii rozgrywki
    - Zapisywanie statystyk gry
    
    SQLite to lekka baza danych przechowywana w pojedynczym pliku.
    Nie wymaga instalacji serwera - idealnie nadaje się do gier.
    """
    
    def __init__(self, db_name="city_builder.db"):
        """
        Konstruktor - tworzy połączenie z bazą danych.
        
        Args:
            db_name (str): nazwa pliku bazy danych (domyślnie "city_builder.db")
        """
        self.db_name = db_name                      # nazwa pliku bazy danych
        self.conn = sqlite3.connect(db_name)        # nawiąż połączenie z bazą (utworzy plik jeśli nie istnieje)
        self.cursor = self.conn.cursor()            # utwórz kursor do wykonywania zapytań SQL
        self.create_tables()                        # utwórz tabele jeśli nie istnieją

    def create_tables(self):
        """
        Tworzy wszystkie potrzebne tabele w bazie danych.
        
        Używa składni "CREATE TABLE IF NOT EXISTS" - tworzy tabelę tylko jeśli nie istnieje.
        To zapobiega błędom przy ponownym uruchomieniu aplikacji.
        """
        
        # Tabela przechowująca aktualny stan gry
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY,         -- automatyczny klucz główny (auto-increment)
                population INTEGER,             -- liczba mieszkańców
                money INTEGER,                  -- ilość pieniędzy w skarbcu miasta
                satisfaction INTEGER,           -- poziom zadowolenia mieszkańców (0-100)
                resources TEXT                  -- zasoby miasta (zapisane jako JSON string)
            )
        ''')

        # Tabela przechowująca historię rozgrywki (dla wykresów i analiz)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,         -- automatyczny klucz główny
                turn INTEGER,                   -- numer tury gry
                population INTEGER,             -- liczba mieszkańców w tej turze
                money INTEGER,                  -- ilość pieniędzy w tej turze
                satisfaction INTEGER,           -- zadowolenie mieszkańców w tej turze
                resources TEXT                  -- stan zasobów w tej turze (JSON)
            )
        ''')

        # Tabela przechowująca różne statystyki gry
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY,         -- automatyczny klucz główny
                name TEXT,                      -- nazwa statystyki (np. "buildings_built", "events_triggered")
                value INTEGER                   -- wartość statystyki
            )
        ''')

        self.conn.commit()  # zatwierdź zmiany w bazie danych (zapisz na dysk)

    def save_game_state(self, population, money, satisfaction, resources):
        """
        Zapisuje aktualny stan gry do bazy danych.
        
        Args:
            population (int): liczba mieszkańców
            money (int): ilość pieniędzy
            satisfaction (int): poziom zadowolenia mieszkańców
            resources (str): zasoby miasta jako string JSON
        """
        # INSERT INTO - dodaje nowy rekord do tabeli
        # Znaki ? to placeholdery - zapobiegają SQL injection attacks
        self.cursor.execute('''
            INSERT INTO game_state (population, money, satisfaction, resources)
            VALUES (?, ?, ?, ?)
        ''', (population, money, satisfaction, resources))
        self.conn.commit()  # zatwierdź zapis

    def load_game_state(self):
        """
        Ładuje najnowszy stan gry z bazy danych.
        
        Returns:
            tuple | None: krotka z danymi gry lub None jeśli brak zapisów
        """
        # SELECT - pobiera dane z tabeli
        # ORDER BY id DESC - sortuje według ID malejąco (najnowsze pierwsze)
        # LIMIT 1 - pobiera tylko jeden (najnowszy) rekord
        self.cursor.execute('SELECT * FROM game_state ORDER BY id DESC LIMIT 1')
        return self.cursor.fetchone()  # zwraca jeden rekord jako krotkę lub None

    def save_history(self, turn, population, money, satisfaction, resources):
        """
        Zapisuje stan gry w historii (dla każdej tury).
        
        Args:
            turn (int): numer tury
            population (int): liczba mieszkańców
            money (int): ilość pieniędzy
            satisfaction (int): poziom zadowolenia
            resources (str): zasoby jako JSON string
        """
        self.cursor.execute('''
            INSERT INTO history (turn, population, money, satisfaction, resources)
            VALUES (?, ?, ?, ?, ?)
        ''', (turn, population, money, satisfaction, resources))
        self.conn.commit()

    def load_history(self):
        """
        Ładuje całą historię gry z bazy danych.
        
        Returns:
            list[tuple]: lista krotek zawierających dane z każdej tury
        """
        # ORDER BY turn - sortuje według numeru tury (od najstarszej)
        self.cursor.execute('SELECT * FROM history ORDER BY turn')
        return self.cursor.fetchall()  # zwraca wszystkie rekordy jako listę krotek

    def save_statistics(self, name, value):
        """
        Zapisuje statystykę gry do bazy danych.
        
        Args:
            name (str): nazwa statystyki
            value (int): wartość statystyki
        """
        self.cursor.execute('''
            INSERT INTO statistics (name, value)
            VALUES (?, ?)
        ''', (name, value))
        self.conn.commit()

    def load_statistics(self):
        """
        Ładuje wszystkie statystyki z bazy danych.
        
        Returns:
            list[tuple]: lista krotek (id, name, value) ze statystykami
        """
        self.cursor.execute('SELECT * FROM statistics')
        return self.cursor.fetchall()

    def close(self):
        """
        Zamyka połączenie z bazą danych.
        
        WAŻNE: Zawsze należy zamknąć połączenie gdy skończy się praca z bazą.
        To zwalnia zasoby i zapewnia, że wszystkie dane zostały zapisane.
        """
        self.conn.close() 