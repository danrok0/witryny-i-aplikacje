from enum import Enum
import os

class TerrainType(Enum):
    """
    Wyliczenie (Enum) typów terenu dostępnych w grze.
    
    Enum to specjalny typ w Pythonie, który pozwala na tworzenie stałych nazwanych.
    Każdy element ma nazwę (np. GRASS) i wartość (np. "grass").
    """
    GRASS = "grass"      # trawa - podstawowy typ terenu
    WATER = "water"      # woda - nie można budować
    MOUNTAIN = "mountain"  # góry - nie można budować
    SAND = "sand"        # piasek - specjalny typ terenu
    ROAD = "road"        # droga - infrastruktura transportowa
    SIDEWALK = "sidewalk"  # chodnik - infrastruktura dla pieszych

class BuildingType(Enum):
    """
    Wyliczenie typów budynków dostępnych w grze.
    
    Budynki są podzielone na kategorie:
    - Infrastruktura (drogi, chodniki)
    - Mieszkaniowe (domy, apartamenty)
    - Komercyjne (sklepy, centra handlowe)
    - Przemysłowe (fabryki, magazyny)
    - Usługi publiczne (szpitale, szkoły)
    - Użyteczność publiczna (elektrownie)
    - Rekreacja (parki, stadiony)
    """
    # Infrastruktura
    ROAD = "road"              # prosta droga
    ROAD_CURVE = "road_curve"  # zakręt drogi
    SIDEWALK = "sidewalk"      # chodnik
    
    # Budynki mieszkalne
    HOUSE = "house"            # dom jednorodzinny
    RESIDENTIAL = "residential"  # blok mieszkalny
    APARTMENT = "apartment"    # wieżowiec mieszkalny
    
    # Budynki komercyjne
    COMMERCIAL = "commercial"  # budynek komercyjny
    SHOP = "shop"             # sklep
    MALL = "mall"             # centrum handlowe
    
    # Budynki przemysłowe
    INDUSTRIAL = "industrial"  # budynek przemysłowy
    FACTORY = "factory"       # fabryka
    WAREHOUSE = "warehouse"   # magazyn
    
    # Usługi publiczne
    CITY_HALL = "city_hall"           # ratusz
    HOSPITAL = "hospital"             # szpital
    SCHOOL = "school"                 # szkoła
    UNIVERSITY = "university"         # uniwersytet
    POLICE = "police"                 # posterunek policji
    FIRE_STATION = "fire_station"     # straż pożarna
    
    # Usługi użyteczności publicznej
    POWER_PLANT = "power_plant"           # elektrownia
    WATER_TREATMENT = "water_treatment"   # oczyszczalnia wody
    
    # Rekreacja i rozrywka
    PARK = "park"            # park
    STADIUM = "stadium"      # stadion

class Building:
    """
    Klasa reprezentująca pojedynczy budynek w grze.
    
    Każdy budynek ma:
    - Nazwę (wyświetlaną w grze)
    - Typ (określający jego funkcję)
    - Koszt budowy
    - Efekty na miasto (np. zwiększenie populacji)
    - Warunki odblokowania (opcjonalne)
    - Rotację (obrót w stopniach)
    - Rozmiar (ile kafelków zajmuje: 1x1, 2x2, 3x3 itp.)
    """
    def __init__(self, name: str, building_type: BuildingType, cost: int, effects: dict, 
                 unlock_condition: dict = None, size: tuple = (1, 1)):
        """
        Konstruktor budynku.
        
        Args:
            name (str): nazwa budynku wyświetlana w grze
            building_type (BuildingType): typ budynku z wyliczenia
            cost (int): koszt budowy w pieniądzach
            effects (dict): słownik efektów (np. {'population': 10, 'happiness': 5})
            unlock_condition (dict): warunki odblokowania (np. {'population': 200})
            size (tuple): rozmiar budynku jako (szerokość, wysokość) w kafelkach
        """
        self.name = name                    # nazwa budynku
        self.building_type = building_type  # typ budynku
        self.cost = cost                    # koszt budowy
        self.effects = effects              # efekty budynku na miasto
        self.rotation = 0                   # rotacja: 0, 90, 180, 270 stopni
        self.size = size                    # rozmiar budynku (szerokość, wysokość)
        # Operator "or" zwraca pierwszy element jeśli nie jest None/pustý, w przeciwnym razie drugi
        self.unlock_condition = unlock_condition or {}  # warunki odblokowania (domyślnie brak)

    def get_image_path(self) -> str | None:
        """
        Zwraca ścieżkę do obrazka budynku lub None jeśli używa koloru.
        
        Returns:
            str | None: ścieżka do pliku PNG lub None
            
        Uwaga: operator | oznacza "union type" - funkcja może zwrócić str LUB None
        """
        # os.path.join łączy elementy ścieżki w sposób niezależny od systemu operacyjnego
        base_path = os.path.join("assets", "tiles")  # bazowa ścieżka do obrazków
        
        # Słownik mapujący typy budynków na nazwy plików
        images = {
            # Infrastruktura
            BuildingType.ROAD: "prostadroga.png",
            BuildingType.ROAD_CURVE: "drogazakręt.png", 
            BuildingType.SIDEWALK: "chodnik.png",
            
            # Budynki mieszkalne
            BuildingType.HOUSE: "domek1.png",
            BuildingType.RESIDENTIAL: "blok.png",
            BuildingType.APARTMENT: "wiezowiec.png",
            
            # Budynki komercyjne
            BuildingType.COMMERCIAL: "targowisko.png",
            BuildingType.MALL: "centumhandlowe.png",
            
            # Budynki przemysłowe
            BuildingType.FACTORY: "fabryka.png",
            BuildingType.POWER_PLANT: "elektrownia.png",
            
            # Usługi publiczne
            BuildingType.CITY_HALL: "burmistrzbudynek.png",
            BuildingType.HOSPITAL: "szpital.png",
            BuildingType.SCHOOL: "szkoła.png",
            BuildingType.UNIVERSITY: "uniwersytet.png",
            BuildingType.POLICE: "komisariat_policji.png",
            BuildingType.FIRE_STATION: "straz_pozarna.png",
            
            # Rekreacja
            BuildingType.PARK: "park.png",
            BuildingType.STADIUM: "stadion.png"
        }
        
        # Sprawdź czy dla tego typu budynku jest obrazek
        if self.building_type in images:
            # Zwróć pełną ścieżkę do obrazka
            return os.path.join(base_path, images[self.building_type])
        return None  # brak obrazka - użyj koloru

    def get_color(self) -> str:
        """
        Zwraca kolor budynku jeśli nie ma dostępnego obrazka.
        
        Returns:
            str: kolor w formacie hex (np. "#FF0000" dla czerwonego)
            
        Kolory hex: # + 6 cyfr/liter (RRGGBB gdzie RR=czerwony, GG=zielony, BB=niebieski)
        Każda para to wartość od 00 do FF (0-255 w systemie dziesiętnym)
        """
        # Słownik mapujący typy budynków na kolory
        colors = {
            # Infrastruktura
            BuildingType.ROAD: "#808080",         # szary
            BuildingType.ROAD_CURVE: "#808080",   # szary
            BuildingType.SIDEWALK: "#DEB887",     # beżowy (Burly Wood)
            
            # Budynki mieszkalne
            BuildingType.HOUSE: "#90EE90",        # jasnozielony
            BuildingType.RESIDENTIAL: "#FFB6C1",  # jasnoróżowy
            BuildingType.APARTMENT: "#FFA0B4",    # ciemniejszy różowy
            
            # Budynki komercyjne
            BuildingType.COMMERCIAL: "#FFD700",   # złoty
            BuildingType.SHOP: "#FFA500",         # pomarańczowy
            BuildingType.MALL: "#FFD700",         # złoty
            
            # Budynki przemysłowe
            BuildingType.INDUSTRIAL: "#8B4513",   # brązowy
            BuildingType.FACTORY: "#A0522D",      # sienna (brązowy)
            BuildingType.WAREHOUSE: "#D2691E",    # czekoladowy
            
            # Usługi publiczne
            BuildingType.CITY_HALL: "#4169E1",    # królewski niebieski
            BuildingType.HOSPITAL: "#FF6347",     # pomidorowy
            BuildingType.SCHOOL: "#32CD32",       # limonkowy
            BuildingType.UNIVERSITY: "#228B22",   # leśny zielony
            BuildingType.POLICE: "#0000FF",       # niebieski
            BuildingType.FIRE_STATION: "#DC143C", # karmazynowy
            
            # Usługi użyteczności publicznej
            BuildingType.POWER_PLANT: "#FFFF00",  # żółty
            BuildingType.WATER_TREATMENT: "#00CED1", # ciemna turkusowa
            
            # Rekreacja
            BuildingType.PARK: "#7CFC00",         # trawiasty zielony
            BuildingType.STADIUM: "#9370DB",      # średni fioletowy
        }
        # dict.get(klucz, domyślna_wartość) - zwraca wartość lub domyślną jeśli klucz nie istnieje
        return colors.get(self.building_type, "#808080")  # domyślnie szary

    def rotate(self):
        """
        Obraca budynek o 90 stopni zgodnie z ruchem wskazówek zegara.
        
        Używa operatora modulo (%) aby wartość rotacji była zawsze między 0-359 stopni.
        Przykład: jeśli rotation = 270, to (270 + 90) % 360 = 0
        """
        self.rotation = (self.rotation + 90) % 360

    def get_building_size(self) -> tuple:
        """
        Zwraca rozmiar budynku z uwzględnieniem rotacji.
        
        Returns:
            tuple: (szerokość, wysokość) w kafelkach
            
        Uwaga: Przy rotacji o 90° lub 270° szerokość i wysokość są zamieniane miejscami
        """
        width, height = self.size
        
        # Jeśli budynek jest obrócony o 90° lub 270°, zamień szerokość z wysokością
        if self.rotation == 90 or self.rotation == 270:
            return (height, width)
        else:
            return (width, height)

    def get_occupied_tiles(self, start_x: int, start_y: int) -> list:
        """
        Zwraca listę wszystkich kafelków zajętych przez budynek.
        
        Args:
            start_x, start_y: współrzędne lewego górnego rogu budynku
            
        Returns:
            list: lista tupli (x, y) wszystkich zajętych kafelków
        """
        width, height = self.get_building_size()
        occupied_tiles = []
        
        for dx in range(width):
            for dy in range(height):
                occupied_tiles.append((start_x + dx, start_y + dy))
        
        return occupied_tiles

class Tile:
    """
    Klasa reprezentująca pojedynczy kafelek (płytkę) na mapie miasta.
    
    Każdy kafelek ma:
    - Współrzędne (x, y) na mapie
    - Typ terenu (trawa, woda, góry itp.)
    - Opcjonalny budynek
    - Status zajętości
    - Informację czy to główny kafel budynku (dla budynków wielokafelkowych)
    """
    def __init__(self, x: int, y: int, terrain_type: TerrainType = TerrainType.GRASS):
        """
        Konstruktor kafelka.
        
        Args:
            x (int): współrzędna X na mapie
            y (int): współrzędna Y na mapie
            terrain_type (TerrainType): typ terenu (domyślnie trawa)
        """
        self.x = x                          # pozycja X na mapie
        self.y = y                          # pozycja Y na mapie
        self.terrain_type = terrain_type    # typ terenu
        self.building = None                # budynek na kafelku (None = brak)
        self.is_occupied = False            # czy kafelek jest zajęty
        self.is_main_tile = True            # czy to główny kafel budynku (dla budynków >1x1)
        
    def get_image_path(self) -> str | None:
        """
        Zwraca ścieżkę do obrazka terenu lub None jeśli używa koloru.
        
        Returns:
            str | None: ścieżka do pliku PNG lub None
        """
        base_path = os.path.join("assets", "tiles")  # ścieżka do obrazków
        
        # Słownik mapujący typy terenu na pliki obrazków
        images = {
            TerrainType.GRASS: "grassnew.png",    # nowa tekstura trawy
            TerrainType.SIDEWALK: "chodnik.png"   # tekstura chodnika
        }
        
        # Sprawdź czy dla tego terenu jest obrazek
        if self.terrain_type in images:
            return os.path.join(base_path, images[self.terrain_type])
        return None  # brak obrazka - użyj koloru
    
    def get_color(self) -> str:
        """
        Zwraca kolor dla typu terenu (używany gdy brak obrazka).
        
        Returns:
            str: kolor w formacie hex
        """
        # Słownik kolorów dla różnych typów terenu
        colors = {
            TerrainType.GRASS: "#90EE90",    # jasnozielony (trawa)
            TerrainType.WATER: "#4169E1",    # królewski niebieski (woda)
            TerrainType.MOUNTAIN: "#4A4A4A", # ciemnoszary (góry)
            TerrainType.SAND: "#F4A460",     # piaskowożółty (piasek)
            TerrainType.ROAD: "#808080",     # szary (droga)
            TerrainType.SIDEWALK: "#DEB887"  # beżowy (chodnik)
        }
        # Zwróć kolor lub biały jako domyślny
        return colors.get(self.terrain_type, "#FFFFFF")
    
    def __str__(self) -> str:
        """
        Zwraca tekstową reprezentację kafelka (używane do debugowania).
        
        Returns:
            str: opis kafelka w formacie "Tile(x, y) - typ_terenu"
            
        Uwaga: __str__ to specjalna metoda Pythona nazywana "magic method".
        Jest automatycznie wywoływana gdy obiekt jest konwertowany na string.
        """
        return f"Tile({self.x}, {self.y}) - {self.terrain_type.value}" 