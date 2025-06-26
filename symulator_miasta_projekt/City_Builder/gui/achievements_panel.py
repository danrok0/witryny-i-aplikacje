"""
Panel GUI dla systemu osiągnięć w City Builder.

Implementuje graficzny interfejs użytkownika do wyświetlania i zarządzania osiągnięciami.
Zawiera zakładki z różnymi kategoriami, statystykami i wykresami postępu.
"""

# === IMPORTY PYQT6 ===
# Komponenty interfejsu użytkownika
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QScrollArea, QLabel, QProgressBar, QFrame, QGridLayout,
                           QPushButton, QTextEdit, QGroupBox, QComboBox)
# Główne klasy Qt
from PyQt6.QtCore import Qt, pyqtSignal               # Podstawowe funkcje Qt
from PyQt6.QtGui import QFont, QColor, QPalette       # Style i kolory

# === IMPORTY SYSTEMU OSIĄGNIĘĆ ===
from core.achievements import AchievementCategory, AchievementRarity  # Enums osiągnięć

# === IMPORTY MATPLOTLIB DO WYKRESÓW ===
import matplotlib.pyplot as plt                                      # Podstawowa biblioteka wykresów
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # Integracja z Qt
from matplotlib.figure import Figure                                 # Klasa figury matplotlib

class AchievementWidget(QFrame):
    """
    Widget wyświetlający pojedyncze osiągnięcie w interfejsie.
    
    Dziedziczy po QFrame aby mieć ramkę wokół osiągnięcia.
    Pokazuje ikonę, nazwę, opis, punkty i status osiągnięcia.
    """
    
    def __init__(self, achievement):
        """
        Konstruktor widgetu osiągnięcia.
        
        Args:
            achievement: Obiekt Achievement do wyświetlenia
        """
        super().__init__()                  # Wywołaj konstruktor klasy bazowej QFrame
        self.achievement = achievement      # Zapisz referencję do osiągnięcia
        self.init_ui()                     # Zainicjalizuj interfejs użytkownika
    
    def init_ui(self):
        """
        Inicjalizuje interfejs użytkownika widgetu osiągnięcia.
        
        Tworzy wszystkie komponenty: ramkę, layout, etykiety, ikonę, etc.
        Ustawia odpowiedni styl w zależności od tego czy osiągnięcie jest odblokowane.
        """
        # === USTAWIENIA PODSTAWOWE RAMKI ===
        self.setFrameStyle(QFrame.Shape.Box)    # Ustaw styl ramki jako prostokąt
        self.setFixedSize(300, 120)             # Stały rozmiar: szerokość 300px, wysokość 120px
        
        # === STYLE ZALEŻNE OD STANU OSIĄGNIĘCIA ===
        # Jeśli osiągnięcie jest odblokowane - kolor zielony (sukces)
        if self.achievement.is_unlocked:
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e8;     /* Jasno zielone tło */
                    border: 2px solid #4CAF50;     /* Zielona ramka */
                    border-radius: 8px;            /* Zaokrąglone rogi */
                }
            """)
        else:
            # Jeśli osiągnięcie nie jest odblokowane - kolor szary (nieaktywne)
            self.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;     /* Jasno szare tło */
                    border: 2px solid #cccccc;     /* Szara ramka */
                    border-radius: 8px;            /* Zaokrąglone rogi */
                }
            """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Nagłówek z ikoną i nazwą
        header_layout = QHBoxLayout()
        
        # Ikona
        icon_label = QLabel(self.achievement.icon)
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Nazwa i punkty
        name_layout = QVBoxLayout()
        
        name_label = QLabel(self.achievement.name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        name_layout.addWidget(name_label)
        
        points_label = QLabel(f"{self.achievement.points} pkt")
        points_label.setFont(QFont("Arial", 10))
        points_label.setStyleSheet("color: #666666;")
        name_layout.addWidget(points_label)
        
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        # Status
        if self.achievement.is_unlocked:
            status_label = QLabel("✅")
            status_label.setFont(QFont("Arial", 16))
        else:
            status_label = QLabel("🔒")
            status_label.setFont(QFont("Arial", 16))
        
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # Opis
        desc_label = QLabel(self.achievement.description)
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555555;")
        layout.addWidget(desc_label)
        
        # Pasek postępu (jeśli nie ukończone)
        if not self.achievement.is_unlocked and self.achievement.progress > 0:
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(self.achievement.progress * 100))
            progress_bar.setFixedHeight(8)
            layout.addWidget(progress_bar)
        
        # Data odblokowania
        if self.achievement.is_unlocked and self.achievement.unlock_date:
            date_label = QLabel(f"Odblokowano: {self.achievement.unlock_date.strftime('%d.%m.%Y')}")
            date_label.setFont(QFont("Arial", 8))
            date_label.setStyleSheet("color: #888888;")
            layout.addWidget(date_label)
        
        # Rzadkość
        rarity_colors = {
            AchievementRarity.COMMON: "#808080",
            AchievementRarity.UNCOMMON: "#1eff00", 
            AchievementRarity.RARE: "#0070dd",
            AchievementRarity.EPIC: "#a335ee",
            AchievementRarity.LEGENDARY: "#ff8000"
        }
        
        rarity_label = QLabel(self.achievement.rarity.value.title())
        rarity_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        rarity_label.setStyleSheet(f"color: {rarity_colors[self.achievement.rarity]};")
        layout.addWidget(rarity_label)

class AchievementsPanel(QWidget):
    """Panel zarządzania osiągnięciami"""
    
    def __init__(self, game_engine=None):
        super().__init__()
        self.game_engine = game_engine
        self.setMinimumSize(900, 700)
        self.init_ui()
    
    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)
        
        # Tytuł
        title = QLabel("🏆 Osiągnięcia")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Statystyki ogólne
        stats_layout = self.create_stats_section()
        layout.addLayout(stats_layout)
        
        # Zakładki
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Zakładka: Wszystkie osiągnięcia
        self.all_tab = self.create_all_achievements_tab()
        self.tabs.addTab(self.all_tab, "🎯 Wszystkie")
        
        # Zakładki według kategorii
        for category in AchievementCategory:
            tab = self.create_category_tab(category)
            icon = self.get_category_icon(category)
            self.tabs.addTab(tab, f"{icon} {category.value.title()}")
        
        # Zakładka: Statystyki
        self.stats_tab = self.create_statistics_tab()
        self.tabs.addTab(self.stats_tab, "📊 Statystyki")
        
        # Przycisk odświeżania
        refresh_btn = QPushButton("🔄 Odśwież")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
    
    def create_stats_section(self):
        """Tworzy sekcję ze statystykami ogólnymi"""
        layout = QHBoxLayout()
        
        # Postęp ogólny
        progress_group = QGroupBox("Postęp ogólny")
        progress_layout = QVBoxLayout(progress_group)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        progress_layout.addWidget(self.overall_progress)
        
        self.progress_label = QLabel("0 / 0 osiągnięć (0%)")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Punkty
        points_group = QGroupBox("Punkty osiągnięć")
        points_layout = QVBoxLayout(points_group)
        
        self.points_label = QLabel("0 punktów")
        self.points_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.points_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        points_layout.addWidget(self.points_label)
        
        layout.addWidget(points_group)
        
        # Ostatnie osiągnięcia
        recent_group = QGroupBox("Ostatnie osiągnięcia")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_achievements = QTextEdit()
        self.recent_achievements.setMaximumHeight(80)
        self.recent_achievements.setReadOnly(True)
        recent_layout.addWidget(self.recent_achievements)
        
        layout.addWidget(recent_group)
        
        return layout
    
    def create_all_achievements_tab(self):
        """Tworzy zakładkę ze wszystkimi osiągnięciami"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtry
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filtruj:"))
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Wszystkie", "all")
        self.status_filter.addItem("Odblokowane", "unlocked")
        self.status_filter.addItem("Zablokowane", "locked")
        self.status_filter.currentTextChanged.connect(self.filter_achievements)
        filter_layout.addWidget(self.status_filter)
        
        self.rarity_filter = QComboBox()
        self.rarity_filter.addItem("Wszystkie rzadkości", None)
        for rarity in AchievementRarity:
            self.rarity_filter.addItem(rarity.value.title(), rarity)
        self.rarity_filter.currentTextChanged.connect(self.filter_achievements)
        filter_layout.addWidget(self.rarity_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Scroll area dla osiągnięć
        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.all_achievements_layout = QGridLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return widget
    
    def create_category_tab(self, category):
        """Tworzy zakładkę dla konkretnej kategorii"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Opis kategorii
        desc_label = QLabel(self.get_category_description(category))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(desc_label)
        
        # Scroll area dla osiągnięć kategorii
        scroll = QScrollArea()
        scroll_widget = QWidget()
        category_layout = QGridLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Przechowaj layout dla późniejszego użycia
        setattr(self, f"{category.value}_layout", category_layout)
        
        return widget
    
    def create_statistics_tab(self):
        """Tworzy zakładkę ze statystykami"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Wykres postępu według kategorii
        self.category_chart = self.create_category_chart()
        layout.addWidget(self.category_chart)
        
        # Wykres według rzadkości
        self.rarity_chart = self.create_rarity_chart()
        layout.addWidget(self.rarity_chart)
        
        return widget
    
    def create_category_chart(self):
        """Tworzy wykres postępu według kategorii"""
        figure = Figure(figsize=(8, 4))
        canvas = FigureCanvas(figure)
        
        self.category_figure = figure
        self.category_canvas = canvas
        
        return canvas
    
    def create_rarity_chart(self):
        """Tworzy wykres według rzadkości"""
        figure = Figure(figsize=(8, 4))
        canvas = FigureCanvas(figure)
        
        self.rarity_figure = figure
        self.rarity_canvas = canvas
        
        return canvas
    
    def get_category_icon(self, category):
        """Zwraca ikonę dla kategorii"""
        icons = {
            AchievementCategory.POPULATION: "👥",
            AchievementCategory.ECONOMY: "💰",
            AchievementCategory.CONSTRUCTION: "🏗️",
            AchievementCategory.TECHNOLOGY: "🔬",
            AchievementCategory.ENVIRONMENT: "🌱",
            AchievementCategory.TRADE: "🤝",
            AchievementCategory.SPECIAL: "⭐",
            AchievementCategory.MILESTONE: "🎯"
        }
        return icons.get(category, "🏆")
    
    def get_category_description(self, category):
        """Zwraca opis kategorii"""
        descriptions = {
            AchievementCategory.POPULATION: "Osiągnięcia związane z rozwojem populacji i demografią miasta.",
            AchievementCategory.ECONOMY: "Osiągnięcia dotyczące zarządzania finansami i ekonomią miasta.",
            AchievementCategory.CONSTRUCTION: "Osiągnięcia za budowanie i rozwijanie infrastruktury.",
            AchievementCategory.TECHNOLOGY: "Osiągnięcia związane z badaniami i rozwojem technologicznym.",
            AchievementCategory.ENVIRONMENT: "Osiągnięcia za dbanie o środowisko i ekologię.",
            AchievementCategory.TRADE: "Osiągnięcia dotyczące handlu międzymiastowego i dyplomacji.",
            AchievementCategory.SPECIAL: "Specjalne osiągnięcia za wyjątkowe wyczyny.",
            AchievementCategory.MILESTONE: "Kamienie milowe w rozwoju miasta."
        }
        return descriptions.get(category, "")
    
    def refresh_data(self):
        """Odświeża wszystkie dane w panelu"""
        if not self.game_engine:
            return
        
        self.refresh_stats()
        self.refresh_achievements()
        self.refresh_charts()
    
    def refresh_stats(self):
        """Odświeża statystyki ogólne"""
        if not self.game_engine:
            return
        
        stats = self.game_engine.get_achievement_statistics()
        
        # Postęp ogólny
        total = stats['total_achievements']
        unlocked = stats['unlocked_achievements']
        percentage = stats['completion_percentage']
        
        self.overall_progress.setValue(int(percentage))
        self.progress_label.setText(f"{unlocked} / {total} osiągnięć ({percentage:.1f}%)")
        
        # Punkty
        self.points_label.setText(f"{stats['total_points']} punktów")
        
        # Ostatnie osiągnięcia
        recent_text = ""
        for achievement in stats['recent_unlocks'][:5]:
            recent_text += f"🏆 {achievement['name']} ({achievement['points']} pkt)\n"
        
        if not recent_text:
            recent_text = "Brak ostatnich osiągnięć"
        
        self.recent_achievements.setText(recent_text)
    
    def refresh_achievements(self):
        """Odświeża listę osiągnięć"""
        if not self.game_engine:
            return
        
        # Wyczyść poprzednie widgety
        self.clear_achievement_layouts()
        
        # Pobierz wszystkie osiągnięcia
        all_achievements = self.game_engine.get_all_achievements()
        
        # Dodaj do zakładki "Wszystkie"
        self.populate_achievements_grid(self.all_achievements_layout, all_achievements)
        
        # Dodaj do zakładek kategorii
        for category in AchievementCategory:
            category_achievements = self.game_engine.get_achievements_by_category(category)
            layout = getattr(self, f"{category.value}_layout")
            self.populate_achievements_grid(layout, category_achievements)
    
    def clear_achievement_layouts(self):
        """Czyści wszystkie layouty osiągnięć"""
        # Wyczyść layout "Wszystkie"
        self.clear_grid_layout(self.all_achievements_layout)
        
        # Wyczyść layouty kategorii
        for category in AchievementCategory:
            layout = getattr(self, f"{category.value}_layout")
            self.clear_grid_layout(layout)
    
    def clear_grid_layout(self, layout):
        """Czyści grid layout"""
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
    
    def populate_achievements_grid(self, layout, achievements):
        """Wypełnia grid layout osiągnięciami"""
        columns = 3
        for i, achievement in enumerate(achievements):
            if not achievement.hidden or achievement.is_unlocked:
                widget = AchievementWidget(achievement)
                row = i // columns
                col = i % columns
                layout.addWidget(widget, row, col)
    
    def refresh_charts(self):
        """Odświeża wykresy statystyk"""
        if not self.game_engine:
            return
        
        stats = self.game_engine.get_achievement_statistics()
        
        # Wykres kategorii
        self.update_category_chart(stats['category_stats'])
        
        # Wykres rzadkości
        self.update_rarity_chart(stats['rarity_stats'])
    
    def update_category_chart(self, category_stats):
        """Aktualizuje wykres kategorii"""
        self.category_figure.clear()
        
        if not category_stats:
            return
        
        ax = self.category_figure.add_subplot(111)
        
        categories = list(category_stats.keys())
        percentages = [category_stats[cat]['percentage'] for cat in categories]
        
        bars = ax.bar(categories, percentages, color='lightblue')
        ax.set_title('Postęp według kategorii')
        ax.set_ylabel('Procent ukończenia (%)')
        ax.set_ylim(0, 100)
        
        # Dodaj wartości na słupkach
        for bar, percentage in zip(bars, percentages):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{percentage:.1f}%', ha='center', va='bottom')
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        self.category_figure.tight_layout()
        self.category_canvas.draw()
    
    def update_rarity_chart(self, rarity_stats):
        """Aktualizuje wykres rzadkości"""
        self.rarity_figure.clear()
        
        if not rarity_stats:
            return
        
        ax = self.rarity_figure.add_subplot(111)
        
        rarities = list(rarity_stats.keys())
        unlocked = [rarity_stats[rarity]['unlocked'] for rarity in rarities]
        total = [rarity_stats[rarity]['total'] for rarity in rarities]
        
        x = range(len(rarities))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], total, width, label='Łącznie', color='lightgray')
        bars2 = ax.bar([i + width/2 for i in x], unlocked, width, label='Odblokowane', color='gold')
        
        ax.set_title('Osiągnięcia według rzadkości')
        ax.set_ylabel('Liczba osiągnięć')
        ax.set_xticks(x)
        ax.set_xticklabels([r.title() for r in rarities])
        ax.legend()
        
        self.rarity_figure.tight_layout()
        self.rarity_canvas.draw()
    
    def filter_achievements(self):
        """Filtruje osiągnięcia według wybranych kryteriów"""
        # Ta funkcja może być rozszerzona o rzeczywiste filtrowanie
        self.refresh_achievements() 