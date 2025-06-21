import random
from .tile import Tile, TerrainType

class CityMap:
    """
    Klasa reprezentująca mapę miasta.
    Zawiera siatkę kafelków (tiles) z różnymi typami terenu.
    """
    def __init__(self, width: int = 50, height: int = 50):
        """
        Konstruktor - inicjalizuje nową mapę miasta.
        
        Args:
            width (int): szerokość mapy w kafelkach (domyślnie 50)
            height (int): wysokość mapy w kafelkach (domyślnie 50)
        """
        self.width = width  # szerokość mapy
        self.height = height  # wysokość mapy
        self.grid = self._create_grid()  # tworzy siatkę kafelków (wywołuje metodę _create_grid)
        self.selected_tile = None  # aktualnie zaznaczony kafelek (na początku żaden)
        
    def _create_grid(self) -> list[list[Tile]]:
        """
        Tworzy dwuwymiarową siatkę kafelków z losowym terenem.
        
        Returns:
            list[list[Tile]]: dwuwymiarowa lista kafelków
            
        Uwaga: podkreślnik (_) na początku nazwy oznacza, że to metoda prywatna
        (używana tylko wewnątrz klasy)
        """
        grid = []  # pusta lista, która będzie zawierać wszystkie rzędy kafelków
        
        # Najpierw wypełnij wszystko trawą
        # Zewnętrzna pętla - dla każdej kolumny (x)
        for x in range(self.width):  # range(50) tworzy liczby od 0 do 49
            row = []  # nowy rząd kafelków
            # Wewnętrzna pętla - dla każdego rzędu (y)
            for y in range(self.height):
                # Dodaj nowy kafelek z trawą na pozycji (x, y)
                row.append(Tile(x, y, TerrainType.GRASS))
            # Dodaj ukończony rząd do głównej siatki
            grid.append(row)
        
        # Dodaj naturalne elementy terenu (góry, wodę, piasek)
        self._add_natural_features(grid)
        
        return grid  # zwróć gotową siatkę
    
    def _add_natural_features(self, grid: list[list[Tile]]):
        """
        Dodaje naturalne elementy do mapy (woda, góry, piasek).
        
        Args:
            grid: dwuwymiarowa lista kafelków do modyfikacji
            
        Ta metoda nie zwraca nic (void), ale modyfikuje przekazaną siatkę
        """
        # Dodaj zbiorniki wodne
        # Parametry: typ terenu, liczba klastrów, maksymalny rozmiar, prawdopodobieństwo rozprzestrzeniania
        self._add_terrain_clusters(grid, TerrainType.WATER, 5, 10, 0.7)
        
        # Dodaj góry
        self._add_terrain_clusters(grid, TerrainType.MOUNTAIN, 3, 5, 0.6)
        
        # Dodaj obszary piaszczyste
        self._add_terrain_clusters(grid, TerrainType.SAND, 4, 8, 0.5)
    
    def _add_terrain_clusters(self, grid: list[list[Tile]], terrain_type: TerrainType, 
                            num_clusters: int, max_size: int, spread_prob: float):
        """
        Dodaje klastry (skupiska) określonego typu terenu.
        
        Args:
            grid: siatka kafelków
            terrain_type: typ terenu do dodania (WATER, MOUNTAIN, SAND)
            num_clusters: ile klastrów utworzyć
            max_size: maksymalny rozmiar każdego klastra
            spread_prob: prawdopodobieństwo rozprzestrzenienia (0.0-1.0)
        """
        # Pętla tworząca określoną liczbę klastrów
        for _ in range(num_clusters):  # _ oznacza, że nie używamy zmiennej iteracji
            # Wybierz losowy punkt początkowy
            start_x = random.randint(0, self.width - 1)  # losowa liczba między 0 a width-1
            start_y = random.randint(0, self.height - 1)  # losowa liczba między 0 a height-1
            
            # Utwórz klaster rozpoczynający się od tego punktu
            self._grow_cluster(grid, start_x, start_y, terrain_type, max_size, spread_prob)
    
    def _grow_cluster(self, grid: list[list[Tile]], x: int, y: int, 
                     terrain_type: TerrainType, max_size: int, spread_prob: float):
        """
        Rozrasta klaster terenu z punktu początkowego (algorytm rekurencyjny).
        
        Args:
            grid: siatka kafelków
            x, y: współrzędne aktualnego kafelka
            terrain_type: typ terenu do umieszczenia
            max_size: ile jeszcze kafelków można dodać (zmniejsza się z każdym wywołaniem)
            spread_prob: prawdopodobieństwo rozprzestrzenienia na sąsiednie kafelki
            
        
        Funkcja kończy działanie gdy max_size osiągnie 0 lub brak miejsca na rozrost.
        """
        # Warunek końca rekurencji - jeśli nie można już dodać więcej kafelków
        if max_size <= 0:
            return  # zakończ funkcję (nie rób nic więcej)
            
        # Zmieniaj tylko kafelki z trawą (nie nadpisuj innych typów terenu)
        if grid[x][y].terrain_type != TerrainType.GRASS:
            return  # zakończ jeśli to nie trawa
            
        # Zmień kafelek na nowy typ terenu
        grid[x][y] = Tile(x, y, terrain_type)
        
        # Spróbuj rozprzestrzenić się we wszystkich kierunkach (góra, dół, lewo, prawo)
        # Lista krotek (tuple) reprezentujących przesunięcia: (delta_x, delta_y)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy  # nowe współrzędne po przesunięciu
            
            # Sprawdź czy nowe współrzędne są w granicach mapy
            # AND (operator and) - wszystkie warunki muszą być spełnione
            if (0 <= nx < self.width and 0 <= ny < self.height and 
                random.random() < spread_prob):  # random.random() zwraca liczbę 0.0-1.0
                
                # Rekurencyjne wywołanie - funkcja wywołuje samą siebie z nowymi parametrami
                self._grow_cluster(grid, nx, ny, terrain_type, max_size - 1, spread_prob)
    
    def get_tile(self, x: int, y: int) -> Tile | None:
        """
        Zwraca kafelek na podanych współrzędnych lub None jeśli poza granicami.
        
        Args:
            x, y: współrzędne kafelka
            
        Returns:
            Tile | None: kafelek lub None (pipe | oznacza "lub" - union type)
        """
        # Sprawdź czy współrzędne są w dozwolonych granicach
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]  # zwróć kafelek z siatki
        return None  # zwróć None jeśli poza granicami
    
    def select_tile(self, x: int, y: int) -> None:
        """
        Zaznacza kafelek na podanych współrzędnych.
        
        Args:
            x, y: współrzędne kafelka do zaznaczenia
            
        Returns:
            None: funkcja nic nie zwraca, tylko modyfikuje stan obiektu
        """
        tile = self.get_tile(x, y)  # pobierz kafelek (lub None)
        if tile:  # jeśli kafelek istnieje (nie jest None)
            self.selected_tile = tile  # ustaw go jako zaznaczony
    
    def deselect_tile(self) -> None:
        """
        Odznacza aktualnie zaznaczony kafelek.
        
        Returns:
            None: funkcja nic nie zwraca
        """
        self.selected_tile = None  # ustaw zaznaczony kafelek na None (brak zaznaczenia)
            
    def get_selected_tile(self) -> Tile | None:
        """
        Zwraca aktualnie zaznaczony kafelek.
        
        Returns:
            Tile | None: zaznaczony kafelek lub None jeśli nic nie jest zaznaczone
        """
        return self.selected_tile  # po prostu zwróć wartość atrybutu
