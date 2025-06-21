"""
Panel GUI dla systemu handlu międzymiastowego
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                           QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit,
                           QGroupBox, QProgressBar, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from core.trade import TradeGoodType, RelationshipStatus
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class TradePanel(QWidget):
    """Panel zarządzania handlem międzymiastowym"""
    
    offer_accepted = pyqtSignal(str)  # offer_id
    contract_created = pyqtSignal(str, object, int, float, int, bool)  # city_id, good_type, quantity, price, duration, is_buying
    
    def __init__(self, game_engine=None):
        super().__init__()
        self.game_engine = game_engine
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)
        
        # Tytuł
        title = QLabel("🏪 Handel Międzymiastowy")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Zakładki
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Zakładka: Oferty handlowe
        self.offers_tab = self.create_offers_tab()
        self.tabs.addTab(self.offers_tab, "📦 Oferty")
        
        # Zakładka: Kontrakty
        self.contracts_tab = self.create_contracts_tab()
        self.tabs.addTab(self.contracts_tab, "📋 Kontrakty")
        
        # Zakładka: Miasta handlowe
        self.cities_tab = self.create_cities_tab()
        self.tabs.addTab(self.cities_tab, "🏙️ Miasta")
        
        # Zakładka: Statystyki
        self.stats_tab = self.create_stats_tab()
        self.tabs.addTab(self.stats_tab, "📊 Statystyki")
        
        # Przycisk odświeżania
        refresh_btn = QPushButton("🔄 Odśwież")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
    
    def create_offers_tab(self):
        """Tworzy zakładkę z ofertami handlowymi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtry
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtruj według towaru:"))
        
        self.good_filter = QComboBox()
        self.good_filter.addItem("Wszystkie", None)
        for good_type in TradeGoodType:
            self.good_filter.addItem(good_type.value.title(), good_type)
        self.good_filter.currentTextChanged.connect(self.filter_offers)
        filter_layout.addWidget(self.good_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tabela ofert
        self.offers_table = QTableWidget()
        self.offers_table.setColumnCount(7)
        self.offers_table.setHorizontalHeaderLabels([
            "Miasto", "Towar", "Ilość", "Cena/szt", "Wartość", "Typ", "Wygasa"
        ])
        self.offers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.offers_table)
        
        # Przyciski akcji
        action_layout = QHBoxLayout()
        
        self.accept_offer_btn = QPushButton("✅ Akceptuj ofertę")
        self.accept_offer_btn.clicked.connect(self.accept_selected_offer)
        self.accept_offer_btn.setEnabled(False)
        action_layout.addWidget(self.accept_offer_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Połącz sygnał wyboru
        self.offers_table.itemSelectionChanged.connect(self.on_offer_selection_changed)
        
        return widget
    
    def create_contracts_tab(self):
        """Tworzy zakładkę z kontraktami"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aktywne kontrakty
        contracts_group = QGroupBox("Aktywne kontrakty")
        contracts_layout = QVBoxLayout(contracts_group)
        
        self.contracts_table = QTableWidget()
        self.contracts_table.setColumnCount(7)
        self.contracts_table.setHorizontalHeaderLabels([
            "Miasto", "Towar", "Ilość/turę", "Cena/szt", "Pozostało tur", "Typ", "Wartość"
        ])
        contracts_layout.addWidget(self.contracts_table)
        
        layout.addWidget(contracts_group)
        
        # Tworzenie nowego kontraktu
        new_contract_group = QGroupBox("Nowy kontrakt")
        new_contract_layout = QVBoxLayout(new_contract_group)
        
        # Formularz kontraktu
        form_layout = QHBoxLayout()
        
        form_layout.addWidget(QLabel("Miasto:"))
        self.contract_city = QComboBox()
        form_layout.addWidget(self.contract_city)
        
        form_layout.addWidget(QLabel("Towar:"))
        self.contract_good = QComboBox()
        for good_type in TradeGoodType:
            self.contract_good.addItem(good_type.value.title(), good_type)
        form_layout.addWidget(self.contract_good)
        
        form_layout.addWidget(QLabel("Ilość/turę:"))
        self.contract_quantity = QSpinBox()
        self.contract_quantity.setRange(1, 1000)
        self.contract_quantity.setValue(50)
        form_layout.addWidget(self.contract_quantity)
        
        form_layout.addWidget(QLabel("Cena/szt:"))
        self.contract_price = QDoubleSpinBox()
        self.contract_price.setRange(0.1, 1000.0)
        self.contract_price.setValue(10.0)
        form_layout.addWidget(self.contract_price)
        
        form_layout.addWidget(QLabel("Czas trwania:"))
        self.contract_duration = QSpinBox()
        self.contract_duration.setRange(5, 100)
        self.contract_duration.setValue(20)
        self.contract_duration.setSuffix(" tur")
        form_layout.addWidget(self.contract_duration)
        
        form_layout.addWidget(QLabel("Typ:"))
        self.contract_type = QComboBox()
        self.contract_type.addItem("Kupujemy", True)
        self.contract_type.addItem("Sprzedajemy", False)
        form_layout.addWidget(self.contract_type)
        
        new_contract_layout.addLayout(form_layout)
        
        # Przycisk tworzenia kontraktu
        create_contract_btn = QPushButton("📋 Utwórz kontrakt")
        create_contract_btn.clicked.connect(self.create_contract)
        new_contract_layout.addWidget(create_contract_btn)
        
        layout.addWidget(new_contract_group)
        
        return widget
    
    def create_cities_tab(self):
        """Tworzy zakładkę z miastami handlowymi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area dla miast
        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.cities_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return widget
    
    def create_stats_tab(self):
        """Tworzy zakładkę ze statystykami"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statystyki ogólne
        stats_group = QGroupBox("Statystyki handlowe")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_labels = {}
        stats_info = [
            ("total_trades", "Łączna liczba transakcji:"),
            ("total_value", "Łączna wartość handlu:"),
            ("active_contracts", "Aktywne kontrakty:"),
            ("active_offers", "Dostępne oferty:")
        ]
        
        for key, label in stats_info:
            label_widget = QLabel(f"{label} 0")
            self.stats_labels[key] = label_widget
            stats_layout.addWidget(label_widget)
        
        layout.addWidget(stats_group)
        
        # Wykres handlu
        self.trade_chart = self.create_trade_chart()
        layout.addWidget(self.trade_chart)
        
        return widget
    
    def create_trade_chart(self):
        """Tworzy wykres statystyk handlowych"""
        figure = Figure(figsize=(8, 4))
        canvas = FigureCanvas(figure)
        
        self.trade_figure = figure
        self.trade_canvas = canvas
        
        return canvas
    
    def create_city_widget(self, city):
        """Tworzy widget dla pojedynczego miasta"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout(frame)
        
        # Nagłówek miasta
        header_layout = QHBoxLayout()
        
        city_name = QLabel(f"🏙️ {city.name}")
        city_name.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(city_name)
        
        # Status relacji
        status_color = {
            RelationshipStatus.HOSTILE: "red",
            RelationshipStatus.UNFRIENDLY: "orange", 
            RelationshipStatus.NEUTRAL: "gray",
            RelationshipStatus.FRIENDLY: "lightgreen",
            RelationshipStatus.ALLIED: "green"
        }
        
        status_label = QLabel(city.relationship.value.title())
        status_label.setStyleSheet(f"color: {status_color[city.relationship]}; font-weight: bold;")
        header_layout.addWidget(status_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Informacje o mieście
        info_layout = QVBoxLayout()
        
        specialization_label = QLabel(f"Specjalizacja: {city.specialization.value.title()}")
        info_layout.addWidget(specialization_label)
        
        points_label = QLabel(f"Punkty relacji: {city.relationship_points}/100")
        info_layout.addWidget(points_label)
        
        # Pasek postępu relacji
        progress_bar = QProgressBar()
        progress_bar.setRange(-100, 100)
        progress_bar.setValue(city.relationship_points)
        info_layout.addWidget(progress_bar)
        
        volume_label = QLabel(f"Wolumen handlu: ${city.trade_volume:,.0f}")
        info_layout.addWidget(volume_label)
        
        layout.addLayout(info_layout)
        
        return frame
    
    def refresh_data(self):
        """Odświeża wszystkie dane w panelu"""
        if not self.game_engine:
            return
        
        self.refresh_offers()
        self.refresh_contracts()
        self.refresh_cities()
        self.refresh_stats()
    
    def refresh_offers(self):
        """Odświeża tabelę ofert"""
        if not self.game_engine:
            return
        
        offers = self.game_engine.get_trade_offers()
        self.offers_table.setRowCount(len(offers))
        
        for row, offer in enumerate(offers):
            city = self.game_engine.get_trading_cities()[offer.city_id]
            
            self.offers_table.setItem(row, 0, QTableWidgetItem(city.name))
            self.offers_table.setItem(row, 1, QTableWidgetItem(offer.good_type.value.title()))
            self.offers_table.setItem(row, 2, QTableWidgetItem(str(offer.quantity)))
            self.offers_table.setItem(row, 3, QTableWidgetItem(f"${offer.price_per_unit:.2f}"))
            
            total_value = offer.quantity * offer.price_per_unit
            self.offers_table.setItem(row, 4, QTableWidgetItem(f"${total_value:,.0f}"))
            
            offer_type = "Kupuje" if offer.is_buying else "Sprzedaje"
            self.offers_table.setItem(row, 5, QTableWidgetItem(offer_type))
            
            turns_left = offer.expires_turn - self.game_engine.turn
            self.offers_table.setItem(row, 6, QTableWidgetItem(f"{turns_left} tur"))
            
            # Przechowaj ID oferty
            self.offers_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, offer.id)
    
    def refresh_contracts(self):
        """Odświeża tabelę kontraktów"""
        if not self.game_engine:
            return
        
        contracts = self.game_engine.trade_manager.active_contracts
        self.contracts_table.setRowCount(len(contracts))
        
        for row, contract in enumerate(contracts):
            city = self.game_engine.get_trading_cities()[contract.city_id]
            
            self.contracts_table.setItem(row, 0, QTableWidgetItem(city.name))
            self.contracts_table.setItem(row, 1, QTableWidgetItem(contract.good_type.value.title()))
            self.contracts_table.setItem(row, 2, QTableWidgetItem(str(contract.quantity_per_turn)))
            self.contracts_table.setItem(row, 3, QTableWidgetItem(f"${contract.price_per_unit:.2f}"))
            self.contracts_table.setItem(row, 4, QTableWidgetItem(str(contract.remaining_turns)))
            
            contract_type = "Kupujemy" if contract.is_buying else "Sprzedajemy"
            self.contracts_table.setItem(row, 5, QTableWidgetItem(contract_type))
            
            total_value = contract.quantity_per_turn * contract.price_per_unit * contract.remaining_turns
            self.contracts_table.setItem(row, 6, QTableWidgetItem(f"${total_value:,.0f}"))
        
        # Odśwież listę miast w formularzu
        self.contract_city.clear()
        for city_id, city in self.game_engine.get_trading_cities().items():
            self.contract_city.addItem(city.name, city_id)
    
    def refresh_cities(self):
        """Odświeża listę miast"""
        if not self.game_engine:
            return
        
        # Wyczyść poprzednie widgety
        for i in reversed(range(self.cities_layout.count())):
            item = self.cities_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
        
        # Dodaj widgety miast
        for city in self.game_engine.get_trading_cities().values():
            city_widget = self.create_city_widget(city)
            self.cities_layout.addWidget(city_widget)
        
        self.cities_layout.addStretch()
    
    def refresh_stats(self):
        """Odświeża statystyki"""
        if not self.game_engine:
            return
        
        stats = self.game_engine.get_trade_statistics()
        
        # Aktualizuj etykiety
        self.stats_labels["total_trades"].setText(f"Łączna liczba transakcji: {stats['total_trades']}")
        self.stats_labels["total_value"].setText(f"Łączna wartość handlu: ${stats['total_value']:,.0f}")
        self.stats_labels["active_contracts"].setText(f"Aktywne kontrakty: {stats['active_contracts']}")
        self.stats_labels["active_offers"].setText(f"Dostępne oferty: {stats['active_offers']}")
        
        # Aktualizuj wykres
        self.update_trade_chart(stats)
    
    def update_trade_chart(self, stats):
        """Aktualizuje wykres handlowy"""
        self.trade_figure.clear()
        
        if not stats['city_stats']:
            return
        
        # Wykres handlu według miast
        ax = self.trade_figure.add_subplot(111)
        
        cities = list(stats['city_stats'].keys())
        values = [stats['city_stats'][city]['value'] for city in cities]
        
        bars = ax.bar(cities, values, color='skyblue')
        ax.set_title('Handel według miast')
        ax.set_ylabel('Wartość ($)')
        
        # Obróć etykiety osi X
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.trade_figure.tight_layout()
        self.trade_canvas.draw()
    
    def filter_offers(self):
        """Filtruje oferty według wybranego towaru"""
        self.refresh_offers()
    
    def on_offer_selection_changed(self):
        """Obsługuje zmianę wyboru oferty"""
        selected_rows = self.offers_table.selectionModel().selectedRows()
        self.accept_offer_btn.setEnabled(len(selected_rows) > 0)
    
    def accept_selected_offer(self):
        """Akceptuje wybraną ofertę"""
        selected_rows = self.offers_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        offer_id = self.offers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if offer_id:
            self.offer_accepted.emit(offer_id)
    
    def create_contract(self):
        """Tworzy nowy kontrakt"""
        city_id = self.contract_city.currentData()
        good_type = self.contract_good.currentData()
        quantity = self.contract_quantity.value()
        price = self.contract_price.value()
        duration = self.contract_duration.value()
        is_buying = self.contract_type.currentData()
        
        if city_id and good_type:
            self.contract_created.emit(city_id, good_type, quantity, price, duration, is_buying) 