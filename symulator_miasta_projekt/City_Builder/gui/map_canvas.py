import os  # operacje na plikach i ścieżkach
import time  # pomiar czasu dla optymalizacji wydajności
import random  # losowe operacje dla czyszczenia cache
from copy import deepcopy  # głębokie kopiowanie obiektów budynków
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QFrame  # widgety graficzne PyQt6
from PyQt6.QtCore import pyqtSignal, Qt, QRectF, QPointF, QTimer  # podstawowe klasy PyQt6
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QTransform, QImage, QIcon, QMouseEvent, QWheelEvent  # grafika i zdarzenia

from core.city_map import CityMap  # mapa miasta z kafelkami
from core.tile import Building, TerrainType  # budynki i typy terenu

class MapCanvas(QGraphicsView):
    """
    Kanwa mapy miasta - główny widget do wyświetlania i edycji mapy.
    
    Dziedziczy po QGraphicsView (PyQt6) - widget do wyświetlania scen graficznych.
    
    Funkcje:
    - Wyświetlanie mapy miasta z kafelkami i budynkami
    - Obsługa kliknięć myszy na kafelki
    - Podgląd budynków przed postawieniem
    - Rotacja budynków klawiszem R
    - Zoom i przewijanie mapy
    - Cache obrazków dla wydajności
    - System sygnałów PyQt6 do komunikacji z innymi komponentami
    """
    
    # Sygnały PyQt6 - mechanizm komunikacji między widgetami
    tile_clicked = pyqtSignal(int, int)                    # emitowany przy kliknięciu kafelka
    building_placed = pyqtSignal(int, int, Building)       # emitowany przy postawieniu budynku
    building_sell_requested = pyqtSignal(int, int, Building)  # emitowany przy żądaniu sprzedaży
    
    def __init__(self, city_map: CityMap):
        """
        Konstruktor MapCanvas.
        
        Args:
            city_map: obiekt CityMap do wyświetlenia
        """
        super().__init__()
        
        self.city_map = city_map  # mapa miasta do wyświetlenia
        self.tile_size = 32       # rozmiar jednego kafelka w pikselach
        
        # Cache'owanie obrazków dla wydajności
        self.image_cache = {}     # cache dla podstawowych obrazków
        self.scaled_image_cache = {}  # cache dla przeskalowanych obrazów
        
        # Stan wyboru budynku i podglądu
        self.selected_building = None      # aktualnie wybrany budynek do postawienia
        self.preview_rotation = 0          # rotacja podglądu budynku
        self.resources = 0                 # aktualna ilość zasobów gracza
        
        # Śledzenie pozycji myszy dla podglądu
        self.hover_tile_x = -1    # współrzędna X kafla pod myszą
        self.hover_tile_y = -1    # współrzędna Y kafla pod myszą
        
        # Śledzenie elementów podglądu do czyszczenia
        self._preview_items = []
        
        # Konfiguracja widoku graficznego
        self.scene = QGraphicsScene()  # scena graficzna PyQt6
        self.setScene(self.scene)      # ustaw scenę dla tego widoku
        
        # Włącz śledzenie myszy dla efektów najechania
        self.setMouseTracking(True)    # śledź ruch myszy nawet bez kliknięcia
        
        # Początkowe rysowanie mapy
        self.draw_map()               # narysuj mapę po inicjalizacji
        
        # Ustaw politykę fokusa aby odbierać zdarzenia klawiatury (potrzebne dla klawisza R)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()  # ustaw fokus na start
        
        # Śledzenie najechania myszą
        self._last_update_time = 0     # czas ostatniej aktualizacji
        self._last_rotate_time = 0     # czas ostatniej rotacji budynku
        
        # Ustawienia wyświetlania
        self.zoom_factor = 1.0         # współczynnik powiększenia
        
        # Konfiguracja pasków przewijania i renderowania
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)   # zawsze pokaż poziomy pasek
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)     # zawsze pokaż pionowy pasek
        self.setRenderHint(QPainter.RenderHint.Antialiasing)                      # wygładzanie krawędzi
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)             # płynne skalowanie obrazów
        self.setFrameStyle(QFrame.Shape.NoFrame)                                  # bez ramki
        
        # Włącz śledzenie myszy dla efektów hover (najechania)
        self.setMouseTracking(True)
        
        # Optymalizacja dla renderowania podglądu
        self._last_hover_x = -1        # ostatnia pozycja myszy x
        self._last_hover_y = -1        # ostatnia pozycja myszy y
        self._cleanup_counter = 0      # licznik dla okresowego czyszczenia
    
    def get_tile_image(self, tile_path: str) -> QPixmap:
        """
        Ładuje i cache'uje obrazek kafla dla wydajności.
        
        Args:
            tile_path (str): ścieżka do pliku obrazka
            
        Returns:
            QPixmap: załadowany i przeskalowany obrazek
        """
        # Sprawdź czy obrazek jest już w cache
        if tile_path in self.image_cache:
            return self.image_cache[tile_path]
        
        # Pobierz ścieżkę bezwzględną do pliku
        abs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), tile_path)
        
        # Załaduj nowy obrazek
        if os.path.exists(abs_path):
            pixmap = QPixmap(abs_path)
            if not pixmap.isNull():
                # Przeskaluj do rozmiaru kafla z zachowaniem proporcji
                scaled_pixmap = pixmap.scaled(
                    self.tile_size, self.tile_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Zapisz w cache
                self.image_cache[tile_path] = scaled_pixmap
                return scaled_pixmap
        
        # Fallback - stwórz kolorowy prostokąt jeśli obrazek się nie załadował
        fallback_pixmap = QPixmap(self.tile_size, self.tile_size)
        fallback_pixmap.fill(QColor(255, 0, 255))  # magenta oznacza brak obrazka
        self.image_cache[tile_path] = fallback_pixmap
        return fallback_pixmap

    def get_scaled_image(self, tile_path: str, width: int, height: int) -> QPixmap:
        """
        Ładuje i cache'uje przeskalowany obrazek dla wielokafelkowych budynków.
        
        Args:
            tile_path: ścieżka do pliku obrazka
            width: docelowa szerokość w pikselach
            height: docelowa wysokość w pikselach
            
        Returns:
            QPixmap: przeskalowany obrazek
        """
        cache_key = f"{tile_path}_{width}x{height}"
        
        # Sprawdź cache
        if cache_key in self.scaled_image_cache:
            return self.scaled_image_cache[cache_key]
        
        # Pobierz ścieżkę bezwzględną do pliku
        abs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), tile_path)
        
        # Załaduj i przeskaluj obrazek
        if os.path.exists(abs_path):
            pixmap = QPixmap(abs_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    width, height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Zapisz w cache
                self.scaled_image_cache[cache_key] = scaled_pixmap
                return scaled_pixmap
        
        # Fallback - zastępczy obrazek w przypadku błędu
        fallback_pixmap = QPixmap(width, height)
        fallback_pixmap.fill(QColor(255, 0, 255))  # magenta oznacza błąd ładowania
        self.scaled_image_cache[cache_key] = fallback_pixmap
        return fallback_pixmap
    
    def select_building(self, building: Building | None):
        """
        Wybiera budynek do postawienia na mapie.
        
        Args:
            building (Building | None): budynek do wybrania lub None aby anulować wybór
            
        Union type (Building | None) oznacza że parametr może być budynkiem lub None.
        """
        # Odznacz zaznaczony kafelek przy wyborze budynku
        self.city_map.deselect_tile()
        
        self.selected_building = building
        self.preview_rotation = 0  # resetuj rotację podglądu przy nowym budynku
        
        if building:
            # Zmień kursor na krzyżyk gdy budynek jest wybrany
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setFocus()  # ustaw fokus żeby klawisz R działał od razu
        else:
            # Przywróć normalny kursor
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        # Natychmiastowe pełne przerysowanie mapy
        self.draw_map()
    
    def rotate_building(self):
        """
        Obraca podgląd wybranego budynku o 90 stopni.
        
        Rotacja działa tylko na podglądzie - nie modyfikuje oryginalnego budynku
        dopóki nie zostanie postawiony na mapie.
        """
        if not self.selected_building:
            return  # wyjdź jeśli nie ma wybranego budynku
            
        current_time = time.time()
        
        # Ogranicz częstotliwość rotacji aby zapobiec artefaktom wizualnym
        if current_time - self._last_rotate_time < 0.2:  # maksymalnie 5 rotacji na sekundę
            return
        
        # Obrót o 90 stopni, modulo 360 (0, 90, 180, 270, 0, ...)
        self.preview_rotation = (self.preview_rotation + 90) % 360
        
        # Pełne przerysowanie zamiast inkrementalnej aktualizacji
        self.draw_map()
        
        self._last_rotate_time = current_time  # zapisz czas ostatniej rotacji
    
    def can_build(self, x: int, y: int) -> bool:
        """Sprawdza czy budynek może zostać postawiony na podanych współrzędnych"""
        if not self.selected_building:
            return False
        
        # Sprawdź czy mamy wystarczające zasoby (szybkie sprawdzenie)
        if self.resources < self.selected_building.cost:
            return False
        
        # Sprawdź czy budynek mieści się w granicach mapy
        building_width, building_height = self.selected_building.get_building_size()
        if (x < 0 or y < 0 or 
            x + building_width > self.city_map.width or 
            y + building_height > self.city_map.height):
            return False
        
        # Sprawdź kolizje - optymalizowane sprawdzanie
        for dx in range(building_width):
            for dy in range(building_height):
                tile_x, tile_y = x + dx, y + dy
                tile = self.city_map.get_tile(tile_x, tile_y)
                
                if not tile or tile.is_occupied:
                    return False
                
                # Sprawdź kompatybilność terenu - blokuj budowanie na wodzie i górach
                if tile.terrain_type in [TerrainType.WATER, TerrainType.MOUNTAIN]:
                    return False
        
        return True
    
    def place_building(self, x: int, y: int):
        """Umieszcza wybrany budynek na podanych współrzędnych"""
        if not self.selected_building:
            return
            
        if not self.can_build(x, y):
            return
        
        # Utwórz kopię budynku aby zachować stan rotacji
        building_copy = deepcopy(self.selected_building)
        building_copy.rotation = self.preview_rotation  # Ustaw rotację z podglądu
        
        # Wyślij sygnał aby GameEngine obsłużył faktyczne umieszczenie
        self.building_placed.emit(x, y, building_copy)

        # Natychmiastowe pełne przerysowanie
        self.draw_map()
    
    def draw_map(self):
        """Rysuje mapę miasta ze wszystkimi kafelkami, budynkami i nakładkami"""
        # --- CAŁKOWITE CZYSZCZENIE PRZED RYSOWANIEM ---
        
        # Wyczyść scenę całkowicie i zresetuj wszystkie elementy
        self.scene.clear()
        self._preview_items.clear()  # Zresetuj śledzenie podglądu
        
        # Cache często używanych wartości
        tile_size = self.tile_size
        map_width = self.city_map.width
        map_height = self.city_map.height
        
        # Wstępnie oblicz prostokąt sceny
        scene_width = map_width * tile_size
        scene_height = map_height * tile_size
        
        for x in range(map_width):
            for y in range(map_height):
                tile = self.city_map.get_tile(x, y)
                if not tile:
                    continue
                
                # Oblicz pozycję raz
                pos_x = x * tile_size
                pos_y = y * tile_size
                rect = QRectF(pos_x, pos_y, tile_size, tile_size)
                
                # Rysuj teren jako pierwszy (poziom Z 0)
                terrain_image_path = tile.get_image_path()
                if terrain_image_path:
                    # Rysuj obrazek terenu
                    terrain_pixmap = self.get_tile_image(terrain_image_path)
                    terrain_item = self.scene.addPixmap(terrain_pixmap)
                    terrain_item.setPos(pos_x, pos_y)
                    terrain_item.setZValue(0)
                else:
                    # Fallback do kolorowego prostokąta dla terenu
                    terrain_color = tile.get_color()
                    terrain_brush = QBrush(QColor(terrain_color))
                    terrain_rect = self.scene.addRect(rect, QPen(Qt.GlobalColor.black, 1), terrain_brush)
                    terrain_rect.setZValue(0)
                
                # Rysuj budynek jeśli jest obecny (poziom Z 1)
                if tile.building:
                    # Sprawdź czy to główny kafel budynku czy pomocniczy
                    is_main_tile = getattr(tile, 'is_main_tile', True)
                    
                    if is_main_tile:
                        # Rysuj pełny budynek tylko na głównym kaflu
                        building_path = tile.building.get_image_path()
                        building_width, building_height = tile.building.get_building_size()
                        
                        if building_path:
                            # Spróbuj załadować obrazek budynku
                            if building_width > 1 or building_height > 1:
                                # Dla większych budynków użyj cache'owanego przeskalowanego obrazu
                                scaled_width = building_width * tile_size
                                scaled_height = building_height * tile_size
                                building_pixmap = self.get_scaled_image(building_path, scaled_width, scaled_height)
                            else:
                                # Dla budynków 1x1 użyj standardowej metody
                                building_pixmap = self.get_tile_image(building_path)
                            
                            # Zastosuj rotację jeśli budynek ma rotację
                            if hasattr(tile.building, 'rotation') and tile.building.rotation != 0:
                                transform = QTransform()
                                transform.translate(building_pixmap.width()/2, building_pixmap.height()/2)
                                transform.rotate(tile.building.rotation)
                                transform.translate(-building_pixmap.width()/2, -building_pixmap.height()/2)
                                building_pixmap = building_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
                            
                            building_item = self.scene.addPixmap(building_pixmap)
                            building_item.setPos(pos_x, pos_y)
                            building_item.setZValue(1)
                            
                            # Dodaj ramkę wokół całego budynku - taka sama jak siatka trawy
                            building_outline_width = building_width * tile_size
                            building_outline_height = building_height * tile_size
                            building_outline_rect = QRectF(pos_x, pos_y, building_outline_width, building_outline_height)
                            outline_pen = QPen(Qt.GlobalColor.black, 1)  # Taka sama ramka jak siatka
                            building_outline = self.scene.addRect(building_outline_rect, outline_pen, QBrush(Qt.BrushStyle.NoBrush))
                            building_outline.setZValue(1.1)  # Nad budynkiem
                        else:
                            # Fallback do kolorowego prostokąta dla głównego kafla
                            scaled_width = building_width * tile_size
                            scaled_height = building_height * tile_size
                            
                            building_rect = QRectF(pos_x, pos_y, scaled_width, scaled_height)
                            color = QColor(tile.building.get_color())
                            brush = QBrush(color)
                            pen = QPen(Qt.GlobalColor.black, 1)  # Taka sama ramka jak siatka
                            building_rect_item = self.scene.addRect(building_rect, pen, brush)
                            building_rect_item.setZValue(1)
                    else:
                        # Pomocniczy kafel - tylko subtelne ciemniejsze tło bez linii
                        bg_color = QColor(60, 80, 60, 80)  # Jeszcze bardziej przezroczyste ciemno-zielone tło
                        brush = QBrush(bg_color)
                        pen = QPen(Qt.GlobalColor.transparent)  # Przezroczysta ramka (praktycznie niewidoczna)
                        rect_item = self.scene.addRect(rect, pen, brush)
                        rect_item.setZValue(0.05)  # Jeszcze niższy Z-index, prawie niewidoczne
                
                # Pokaż podgląd tylko dla kafla pod myszą z wybranym budynkiem
                if (self.selected_building and 
                    x == self.hover_tile_x and y == self.hover_tile_y and
                    self.hover_tile_x >= 0 and self.hover_tile_y >= 0):
                    
                    self._draw_building_preview(pos_x, pos_y, rect)
                
                # Dodaj ramkę kafla (poziom Z 2) - tylko dla pustych kafelków
                if not tile.building:
                    # Rysuj ramkę siatki dla pustych kafelków - taka sama jak dla budynków
                    border_pen = QPen(Qt.GlobalColor.black, 1)  # Jednolita grubość ramki
                    border_rect = self.scene.addRect(rect, border_pen, QBrush(Qt.BrushStyle.NoBrush))
                    border_rect.setZValue(0.5)  # Pod budynkami
                
                # Dodaj podświetlenia (poziom Z 3)
                self._draw_tile_highlights(x, y, rect)
        
        # Ustaw prostokąt sceny raz na końcu
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
    
    def _draw_building_preview(self, pos_x: float, pos_y: float, rect: QRectF):
        """Rysuje podgląd budynku na pozycji pod myszą"""
        building_path = self.selected_building.get_image_path()
        
        # Pobierz rozmiar budynku z uwzględnieniem rotacji
        building_width, building_height = self.selected_building.get_building_size()
        
        if building_path:
            # Zawsze używaj obrazków w podglądzie - tak jak będą wyglądać po postawieniu
            if building_width > 1 or building_height > 1:
                # Dla większych budynków użyj przeskalowanego obrazu
                scaled_width = building_width * self.tile_size
                scaled_height = building_height * self.tile_size
                preview_pixmap = self.get_scaled_image(building_path, scaled_width, scaled_height)
            else:
                # Dla budynków 1x1 użyj standardowego obrazu
                preview_pixmap = self.get_tile_image(building_path)
            
            # Zastosuj podgląd rotacji używając preview_rotation
            if self.preview_rotation != 0:
                transform = QTransform()
                transform.translate(preview_pixmap.width()/2, preview_pixmap.height()/2)
                transform.rotate(self.preview_rotation)
                transform.translate(-preview_pixmap.width()/2, -preview_pixmap.height()/2)
                preview_pixmap = preview_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            # Dodaj półprzezroczysty podgląd
            preview_item = self.scene.addPixmap(preview_pixmap)
            preview_item.setPos(pos_x, pos_y)
            preview_item.setOpacity(0.7)  # Półprzezroczysty podgląd
            preview_item.setZValue(1.5)  # Między budynkiem a ramką
            
            # Dodaj subtelną białą ramkę tylko wokół całego budynku
            if building_width > 1 or building_height > 1:
                preview_width = building_width * self.tile_size
                preview_height = building_height * self.tile_size
                outline_rect = QRectF(pos_x, pos_y, preview_width, preview_height)
                outline_pen = QPen(Qt.GlobalColor.white, 2)  # Biała ramka
                outline_item = self.scene.addRect(outline_rect, outline_pen, QBrush(Qt.BrushStyle.NoBrush))
                outline_item.setZValue(1.6)  # Nad obrazkiem
        else:
            # Fallback dla budynków bez obrazków - użyj kolorowych prostokątów
            preview_width = building_width * self.tile_size
            preview_height = building_height * self.tile_size
            preview_rect = QRectF(pos_x, pos_y, preview_width, preview_height)
            
            color = QColor(self.selected_building.get_color())
            color.setAlpha(120)  # Półprzezroczyste
            brush = QBrush(color)
            pen = QPen(Qt.GlobalColor.white, 3)  # Biała gruba ramka dla widoczności
            preview_rect_item = self.scene.addRect(preview_rect, pen, brush)
            preview_rect_item.setZValue(1.5)
            
            # Dodaj tekst z nazwą i rozmiarem budynku
            from PyQt6.QtWidgets import QGraphicsTextItem
            from PyQt6.QtGui import QFont
            
            text_content = f"{self.selected_building.name}\n{building_width}x{building_height}"
            size_text = QGraphicsTextItem(text_content)
            size_text.setDefaultTextColor(Qt.GlobalColor.white)
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            size_text.setFont(font)
            
            # Wyśrodkuj tekst w prostokącie
            text_rect = size_text.boundingRect()
            text_x = pos_x + (preview_width - text_rect.width()) / 2
            text_y = pos_y + (preview_height - text_rect.height()) / 2
            size_text.setPos(text_x, text_y)
            size_text.setZValue(2.0)
            self.scene.addItem(size_text)
        
        # Dodaj wskaźnik rotacji dla obracalnych budynków
        if self.preview_rotation != 0:
            self._draw_rotation_arrow(pos_x, pos_y)
    
    def _draw_rotation_arrow(self, pos_x: float, pos_y: float):
        """Rysuje wskaźnik strzałki rotacji"""
        arrow_size = 8
        arrow_pixmap = QPixmap(arrow_size * 2, arrow_size * 2)
        arrow_pixmap.fill(Qt.GlobalColor.transparent)
        
        arrow_painter = QPainter(arrow_pixmap)
        arrow_painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
        arrow_painter.setBrush(QBrush(Qt.GlobalColor.yellow))
        
        # Rysuj strzałkę wskazującą w prawo (będzie obrócona)
        arrow_points = [
            QPointF(arrow_size * 0.5, arrow_size),
            QPointF(arrow_size * 1.5, arrow_size),
            QPointF(arrow_size * 1.8, arrow_size * 1.3),
        ]
        arrow_painter.drawPolygon(arrow_points)
        arrow_painter.end()
        
        # Obróć strzałkę aby pasowała do rotacji budynku
        if self.preview_rotation != 0:
            arrow_transform = QTransform()
            arrow_transform.translate(arrow_size, arrow_size)
            arrow_transform.rotate(self.preview_rotation)
            arrow_transform.translate(-arrow_size, -arrow_size)
            arrow_pixmap = arrow_pixmap.transformed(arrow_transform, Qt.TransformationMode.SmoothTransformation)
        
        arrow_item = self.scene.addPixmap(arrow_pixmap)
        arrow_item.setPos(pos_x + self.tile_size - arrow_size * 2, pos_y)
        arrow_item.setZValue(2.5)  # Na wierzchu wszystkiego
    
    def _draw_tile_highlights(self, x: int, y: int, rect: QRectF):
        """Rysuje podświetlenia kafelków dla zaznaczenia i najechania"""
        tile = self.city_map.get_tile(x, y)
        highlight_needed = False
        highlight_color = Qt.GlobalColor.yellow
        
        # Sprawdź czy to kafel pod myszą z wybranym budynkiem
        if (self.selected_building and 
            x == self.hover_tile_x and y == self.hover_tile_y and
            self.hover_tile_x >= 0 and self.hover_tile_y >= 0):
            highlight_needed = True
            if self.can_build(x, y):
                highlight_color = Qt.GlobalColor.green  # Zielony dla możliwości budowy
            else:
                highlight_color = Qt.GlobalColor.red    # Czerwony dla braku możliwości budowy
        
        # Sprawdź czy to zaznaczony kafel (tylko gdy nie mamy wybranego budynku)
        elif tile == self.city_map.get_selected_tile() and not self.selected_building:
            highlight_needed = True
            highlight_color = Qt.GlobalColor.yellow  # Żółty dla zaznaczonego
        
        if highlight_needed:
            highlight_pen = QPen(highlight_color, 3)
            highlight_rect = self.scene.addRect(rect, highlight_pen, QBrush(Qt.BrushStyle.NoBrush))
            highlight_rect.setZValue(3)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Obsługuje zdarzenia kliknięć myszy"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Konwertuj pozycję kliknięcia na współrzędne sceny
            scene_pos = self.mapToScene(event.pos())
            
            # Oblicz współrzędne kafla
            tile_x = int(scene_pos.x() // self.tile_size)
            tile_y = int(scene_pos.y() // self.tile_size)
            
            # Sprawdź czy współrzędne są w granicach mapy
            if (0 <= tile_x < self.city_map.width and 0 <= tile_y < self.city_map.height):
                if self.selected_building:
                    # Spróbuj postawić budynek
                    self.place_building(tile_x, tile_y)
                    # Odznacz zaznaczenie kafla przy stawianiu budynku
                    self.city_map.deselect_tile()
                else:
                    # Przełącz zaznaczenie kafla (tylko gdy nie mamy wybranego budynku)
                    current_selection = self.city_map.get_selected_tile()
                    tile = self.city_map.get_tile(tile_x, tile_y)
                    
                    if current_selection == tile:
                        # Jeśli kliknięto ten sam kafel, odznacz go
                        self.city_map.deselect_tile()
                    else:
                        # Zaznacz nowy kafel
                        self.city_map.select_tile(tile_x, tile_y)
                        self.tile_clicked.emit(tile_x, tile_y)
                
                # Przerysuj mapę
                self.draw_map()
        
        elif event.button() == Qt.MouseButton.RightButton:
            # Sprzedaż budynku po PPM
            scene_pos = self.mapToScene(event.pos())
            tile_x = int(scene_pos.x() // self.tile_size)
            tile_y = int(scene_pos.y() // self.tile_size)
            tile = self.city_map.get_tile(tile_x, tile_y)
            if tile and tile.building:
                self.building_sell_requested.emit(tile_x, tile_y, tile.building)
            else:
                # Jeśli nie ma wybranego budynku, odznacz kafel po prawym kliknięciu
                if self.city_map.get_selected_tile() is not None:
                    self.city_map.deselect_tile()
                    self.draw_map()
    
    def keyPressEvent(self, event):
        """Obsługuje zdarzenia naciśnięć klawiszy"""
        if event.key() == Qt.Key.Key_R and self.selected_building:
            self.rotate_building()
        elif event.key() == Qt.Key.Key_Escape:
            # Klawisz Escape odznacza budynek i kafel
            if self.selected_building:
                self.selected_building = None
                self.preview_rotation = 0
                self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Również odznacz zaznaczony kafel
            if self.city_map.get_selected_tile():
                self.city_map.deselect_tile()
                
            # Pełne przerysowanie po zmianie stanu
            self.draw_map()
        else:
            super().keyPressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Obsługuje zdarzenia ruchu myszy dla podglądu najechania"""
        # Ograniczaj aktualizacje aby poprawić wydajność i zapobiec szybkiemu tworzeniu/usuwaniu obiektów
        current_time = time.time()
        if current_time - self._last_update_time < 0.15:  # Zwiększone z 0.1 na 0.15 dla stabilności
            super().mouseMoveEvent(event)
            return
        
        # Konwertuj pozycję myszy na współrzędne sceny
        scene_pos = self.mapToScene(event.pos())
        
        # Oblicz współrzędne kafla
        new_hover_x = int(scene_pos.x() // self.tile_size)
        new_hover_y = int(scene_pos.y() // self.tile_size)
        
        # Aktualizuj pozycję najechania jeśli się zmieniła i jest w granicach
        if (new_hover_x != self.hover_tile_x or new_hover_y != self.hover_tile_y):
            # Sprawdź czy współrzędne są w granicach mapy
            if (0 <= new_hover_x < self.city_map.width and 
                0 <= new_hover_y < self.city_map.height):
                
                self.hover_tile_x = new_hover_x
                self.hover_tile_y = new_hover_y
                
                # Przerysuj tylko jeśli mamy wybrany budynek
                if self.selected_building:
                    # Rozwiązanie radykalne: pełne przerysowanie mapy za każdym razem
                    # Eliminuje wszystkie artefakty kosztem wydajności
                    self.draw_map()
                    self._last_update_time = current_time
        
        super().mouseMoveEvent(event)
    
    def _cleanup_artifacts(self):
        """Wyczyść pozostałe artefakty podglądu"""
        # Pobierz wszystkie elementy z wartością Z wskazującą że mogą być elementami podglądu
        try:
            all_items = self.scene.items()
        except:
            return  # Scena może być nieprawidłowa
        
        artifacts_removed = 0
        
        for item in all_items:
            try:
                # Sprawdź czy element jest prawidłowy przed dostępem do właściwości
                if not hasattr(item, 'zValue'):
                    continue
                    
                z_value = item.zValue()
                # Usuń elementy które wyglądają jak artefakty podglądu (wartość Z 1.5, 2.5, lub 3)
                if z_value in [1.5, 2.5, 3.0] and item not in self._preview_items:
                    # Podwójnie sprawdź czy element jest nadal prawidłowy
                    if hasattr(item, 'scene') and item.scene() == self.scene:
                        self.scene.removeItem(item)
                        artifacts_removed += 1
            except (RuntimeError, AttributeError):
                # Element już usunięty lub nieprawidłowy - pomiń go
                continue
        
        # Ogranicz czyszczenie artefaktów aby zapobiec problemom wydajności
        if artifacts_removed > 10:
            print(f"Wyczyszczono {artifacts_removed} artefaktów podglądu")
    
    def _cleanup_all_previews(self):
        """Wyczyść wszystkie elementy podglądu bezpiecznie"""
        try:
            # Zrób kopię listy aby uniknąć modyfikacji podczas iteracji
            current_items = self._preview_items.copy()
            self._preview_items = []  # Wyczyść oryginalną listę najpierw
            
            for item in current_items:
                try:
                    if item and hasattr(item, 'scene') and item.scene() == self.scene:
                        self.scene.removeItem(item)
                except (RuntimeError, AttributeError):
                    pass  # Element może być już usunięty
            
            # Również uruchom czyszczenie artefaktów
            self._cleanup_artifacts()
            
            # Wymuś pełne przerysowanie co kilka operacji aby zresetować scenę
            if random.random() < 0.2:  # 20% szansy na pełne przerysowanie
                self.draw_map()
                
        except Exception as e:
            print(f"Błąd w czyszczeniu: {e}")  # Informacje debugowe
    
    def update_preview_only(self):
        """Aktualizuje tylko podgląd budynku bez przerysowywania całej mapy"""
        # Bezpieczeństwo najpierw - wyczyść wszystkie istniejące podglądy przed dodaniem nowych
        self._cleanup_all_previews_immediate()
        
        # Dodaj nowy podgląd jeśli mamy wybrany budynek i prawidłową pozycję najechania
        if (self.selected_building and 
            self.hover_tile_x >= 0 and self.hover_tile_y >= 0 and
            self.hover_tile_x < self.city_map.width and 
            self.hover_tile_y < self.city_map.height):
            
            pos_x = self.hover_tile_x * self.tile_size
            pos_y = self.hover_tile_y * self.tile_size
            rect = QRectF(pos_x, pos_y, self.tile_size, self.tile_size)
            
            # Rysuj podgląd budynku
            building_path = self.selected_building.get_image_path()
            if building_path:
                preview_pixmap = self.get_tile_image(building_path)
                
                # Zastosuj podgląd rotacji
                if self.preview_rotation != 0:
                    transform = QTransform()
                    transform.translate(self.tile_size/2, self.tile_size/2)
                    transform.rotate(self.preview_rotation)
                    transform.translate(-self.tile_size/2, -self.tile_size/2)
                    preview_pixmap = preview_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
                
                # Dodaj półprzezroczysty podgląd
                preview_item = self.scene.addPixmap(preview_pixmap)
                preview_item.setPos(pos_x, pos_y)
                preview_item.setOpacity(0.7)
                preview_item.setZValue(1.5)
                self._preview_items.append(preview_item)
                
                # Dodaj wskaźnik rotacji
                if self.preview_rotation != 0:
                    arrow_item = self._create_rotation_arrow(pos_x, pos_y)
                    if arrow_item:
                        self._preview_items.append(arrow_item)
            else:
                # Kolorowy podgląd
                color = QColor(self.selected_building.get_color())
                color.setAlpha(180)
                brush = QBrush(color)
                pen = QPen(Qt.GlobalColor.black, 1)
                preview_rect = self.scene.addRect(rect, pen, brush)
                preview_rect.setZValue(1.5)
                self._preview_items.append(preview_rect)
                
                # Dodaj tekst rotacji
                if self.preview_rotation != 0:
                    text_item = self._create_rotation_text(pos_x, pos_y)
                    if text_item:
                        self._preview_items.append(text_item)
            
            # Dodaj podświetlenie
            highlight_color = Qt.GlobalColor.green if self.can_build(self.hover_tile_x, self.hover_tile_y) else Qt.GlobalColor.red
            highlight_pen = QPen(highlight_color, 3)
            highlight_rect = self.scene.addRect(rect, highlight_pen, QBrush(Qt.BrushStyle.NoBrush))
            highlight_rect.setZValue(3)
            self._preview_items.append(highlight_rect)
    
    def _cleanup_all_previews_immediate(self):
        """Wyczyść wszystkie elementy podglądu natychmiast (wersja bez opóźnienia)"""
        try:
            # Upewnij się że nie operujemy na usuniętej scenie
            if not self.scene:
                self._preview_items = []
                return
                
            # Zrób kopię aby uniknąć modyfikacji podczas iteracji
            current_items = self._preview_items.copy()
            self._preview_items = []  # Wyczyść listę najpierw
            
            for item in current_items:
                try:
                    if item and hasattr(item, 'scene') and item.scene() == self.scene:
                        self.scene.removeItem(item)
                except (RuntimeError, AttributeError):
                    pass  # Element może być już usunięty
                    
        except Exception as e:
            print(f"Błąd w natychmiastowym czyszczeniu: {e}")
    
    def _create_rotation_arrow(self, pos_x: float, pos_y: float):
        """Tworzy strzałkę rotacji i zwraca element graficzny"""
        arrow_size = 8
        arrow_pixmap = QPixmap(arrow_size * 2, arrow_size * 2)
        arrow_pixmap.fill(Qt.GlobalColor.transparent)
        
        arrow_painter = QPainter(arrow_pixmap)
        arrow_painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
        arrow_painter.setBrush(QBrush(Qt.GlobalColor.yellow))
        
        arrow_points = [
            QPointF(arrow_size * 0.5, arrow_size),
            QPointF(arrow_size * 1.5, arrow_size),
            QPointF(arrow_size * 1.8, arrow_size * 1.3),
        ]
        arrow_painter.drawPolygon(arrow_points)
        arrow_painter.end()
        
        # Obróć strzałkę
        if self.preview_rotation != 0:
            arrow_transform = QTransform()
            arrow_transform.translate(arrow_size, arrow_size)
            arrow_transform.rotate(self.preview_rotation)
            arrow_transform.translate(-arrow_size, -arrow_size)
            arrow_pixmap = arrow_pixmap.transformed(arrow_transform, Qt.TransformationMode.SmoothTransformation)
        
        arrow_item = self.scene.addPixmap(arrow_pixmap)
        arrow_item.setPos(pos_x + self.tile_size - arrow_size * 2, pos_y)
        arrow_item.setZValue(2.5)
        return arrow_item
    
    def _create_rotation_text(self, pos_x: float, pos_y: float):
        """Tworzy tekst rotacji i zwraca element graficzny"""
        from PyQt6.QtWidgets import QGraphicsTextItem
        from PyQt6.QtGui import QFont
        
        rotation_text = QGraphicsTextItem(f"{self.preview_rotation}°")
        rotation_text.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        rotation_text.setFont(font)
        rotation_text.setPos(pos_x + 2, pos_y + 2)
        rotation_text.setZValue(2.5)
        self.scene.addItem(rotation_text)
        return rotation_text

    def wheelEvent(self, event: QWheelEvent):
        """Obsługuje zdarzenia kółka myszy dla powiększania"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Współczynnik powiększenia
            zoom_in = event.angleDelta().y() > 0
            factor = 1.1 if zoom_in else 0.9
            
            # Zastosuj powiększenie
            self.scale(factor, factor)
            self.zoom_factor *= factor
        else:
            # Normalne przewijanie
            super().wheelEvent(event) 