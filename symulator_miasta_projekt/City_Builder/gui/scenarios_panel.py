"""
Panel scenariuszy i trybów gry dla City Builder.
Pozwala na wybór różnych scenariuszy, kampanii i wyzwań.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QGroupBox, QScrollArea, QFrame, QProgressBar,
                           QComboBox, QTextEdit, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from core.scenarios import ScenarioManager, ScenarioType, DifficultyLevel
from typing import Optional, Dict

class ScenarioCard(QFrame):
    """Karta pojedynczego scenariusza"""
    
    scenario_selected = pyqtSignal(str)  # scenario_id
    
    def __init__(self, scenario_data: Dict, parent=None):
        super().__init__(parent)
        self.scenario_data = scenario_data
        self.init_ui()
        
    def init_ui(self):
        """Inicjalizuje kartę scenariusza"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #e6f3ff;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Tytuł scenariusza
        title_label = QLabel(self.scenario_data['title'])
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Typ i trudność
        info_layout = QHBoxLayout()
        type_label = QLabel(f"Typ: {self.scenario_data['type'].title()}")
        difficulty_label = QLabel(f"Trudność: {self.scenario_data['difficulty'].title()}")
        info_layout.addWidget(type_label)
        info_layout.addWidget(difficulty_label)
        layout.addLayout(info_layout)
        
        # Opis
        desc_label = QLabel(self.scenario_data['description'])
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(80)
        layout.addWidget(desc_label)
        
        # Status i przycisk
        if self.scenario_data['completed']:
            status_label = QLabel("✅ Ukończony")
            status_label.setStyleSheet("color: green; font-weight: bold;")
        elif not self.scenario_data['unlocked']:
            status_label = QLabel("🔒 Zablokowany")
            status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            status_label = QLabel("🎮 Dostępny")
            status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(status_label)
        
        # Przycisk uruchomienia
        if self.scenario_data['unlocked']:
            self.start_btn = QPushButton("▶️ Rozpocznij")
            self.start_btn.clicked.connect(self.select_scenario)
        else:
            self.start_btn = QPushButton("🔒 Zablokowany")
            self.start_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn)
        self.setLayout(layout)
        
        # Kliknięcie w kartę też wybiera scenariusz
        self.mousePressEvent = self.card_clicked
        
    def card_clicked(self, event):
        """Obsługuje kliknięcie w kartę"""
        if self.scenario_data['unlocked']:
            self.select_scenario()
            
    def select_scenario(self):
        """Wybiera scenariusz"""
        self.scenario_selected.emit(self.scenario_data['id'])

class ScenarioDetailsDialog(QDialog):
    """Dialog ze szczegółami scenariusza"""
    
    def __init__(self, scenario_details: Dict, parent=None):
        super().__init__(parent)
        self.scenario_details = scenario_details
        self.init_ui()
        
    def init_ui(self):
        """Inicjalizuje dialog szczegółów"""
        self.setWindowTitle(f"Szczegóły: {self.scenario_details['title']}")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Tytuł i podstawowe info
        title_label = QLabel(self.scenario_details['title'])
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        info_text = f"""
        <b>Typ:</b> {self.scenario_details['type'].title()}<br>
        <b>Trudność:</b> {self.scenario_details['difficulty'].title()}<br>
        <b>Opis:</b> {self.scenario_details['description']}
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Warunki początkowe
        starting_group = QGroupBox("🏁 Warunki Początkowe")
        starting_layout = QVBoxLayout()
        starting_conditions = self.scenario_details['starting_conditions']
        starting_text = f"""
        • Pieniądze: ${starting_conditions['money']:,}<br>
        • Populacja: {starting_conditions['population']}<br>
        • Budynki: {len(starting_conditions['buildings'])}<br>
        • Technologie: {len(starting_conditions['technologies'])}
        """
        starting_layout.addWidget(QLabel(starting_text))
        starting_group.setLayout(starting_layout)
        layout.addWidget(starting_group)
        
        # Cele scenariusza
        objectives_group = QGroupBox("🎯 Cele do Osiągnięcia")
        objectives_layout = QVBoxLayout()
        
        for obj in self.scenario_details['objectives']:
            obj_text = f"• {obj['title']}: {obj['description']}"
            if obj['optional']:
                obj_text += " (opcjonalny)"
            obj_label = QLabel(obj_text)
            obj_label.setWordWrap(True)
            objectives_layout.addWidget(obj_label)
            
        objectives_group.setLayout(objectives_layout)
        layout.addWidget(objectives_group)
        
        # Modyfikatory i ograniczenia
        if any([self.scenario_details['modifiers']['cost_multiplier'] != 1.0,
                self.scenario_details['modifiers']['income_multiplier'] != 1.0]):
            modifiers_group = QGroupBox("⚖️ Modyfikatory")
            modifiers_layout = QVBoxLayout()
            
            mods = self.scenario_details['modifiers']
            if mods['cost_multiplier'] != 1.0:
                cost_text = f"Koszty budowy: {mods['cost_multiplier']*100:.0f}%"
                modifiers_layout.addWidget(QLabel(cost_text))
            if mods['income_multiplier'] != 1.0:
                income_text = f"Dochody: {mods['income_multiplier']*100:.0f}%"
                modifiers_layout.addWidget(QLabel(income_text))
                
            modifiers_group.setLayout(modifiers_layout)
            layout.addWidget(modifiers_group)
        
        # Nagrody
        rewards_group = QGroupBox("🏆 Nagrody za Ukończenie")
        rewards_layout = QVBoxLayout()
        rewards = self.scenario_details['rewards']
        
        if rewards['money'] > 0:
            rewards_layout.addWidget(QLabel(f"• Pieniądze: ${rewards['money']:,}"))
        if rewards['reputation'] > 0:
            rewards_layout.addWidget(QLabel(f"• Reputacja: +{rewards['reputation']}"))
        if rewards['unlocks']['scenario']:
            rewards_layout.addWidget(QLabel(f"• Odblokuje scenariusz: {rewards['unlocks']['scenario']}"))
        if rewards['unlocks']['building']:
            rewards_layout.addWidget(QLabel(f"• Odblokuje budynek: {rewards['unlocks']['building']}"))
        if rewards['unlocks']['technology']:
            rewards_layout.addWidget(QLabel(f"• Odblokuje technologię: {rewards['unlocks']['technology']}"))
            
        rewards_group.setLayout(rewards_layout)
        layout.addWidget(rewards_group)
        
        # Przyciski
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

class ScenariosPanel(QWidget):
    """Panel wyboru scenariuszy i trybów gry"""
    
    scenario_started = pyqtSignal(str)  # scenario_id
    
    def __init__(self, scenario_manager: ScenarioManager, parent=None):
        super().__init__(parent)
        self.scenario_manager = scenario_manager
        self.init_ui()
        self.update_display()
        
    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout()
        
        # Nagłówek
        header_label = QLabel("🎮 Wybierz Scenariusz Gry")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Filtry
        self.create_filters_section(layout)
        
        # Lista scenariuszy
        self.create_scenarios_section(layout)
        
        self.setLayout(layout)
        self.setWindowTitle("Scenariusze Gry")
        self.resize(1000, 700)
        
    def create_filters_section(self, layout):
        """Tworzy sekcję filtrów"""
        filters_group = QGroupBox("🔍 Filtry")
        filters_layout = QHBoxLayout()
        
        # Filtr typu
        filters_layout.addWidget(QLabel("Typ:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Wszystkie", "Piaskownica", "Kampania", "Wyzwanie", "Przetrwanie"])
        self.type_filter.currentTextChanged.connect(self.filter_scenarios)
        filters_layout.addWidget(self.type_filter)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
    def create_scenarios_section(self, layout):
        """Tworzy sekcję z kartami scenariuszy"""
        scenarios_group = QGroupBox("📋 Dostępne Scenariusze")
        scenarios_layout = QVBoxLayout()
        
        # Scroll area dla kart
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(400)
        
        scenarios_layout.addWidget(self.scroll_area)
        scenarios_group.setLayout(scenarios_layout)
        layout.addWidget(scenarios_group)
        
    def update_display(self):
        """Aktualizuje wyświetlane scenariusze"""
        self.filter_scenarios()
        
    def filter_scenarios(self):
        """Filtruje i wyświetla scenariusze"""
        # Wyczyść poprzednie karty
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
            
        # Pobierz wszystkie scenariusze
        all_scenarios = self.scenario_manager.get_available_scenarios()
        
        # Organizuj karty w rzędy (3 karty na rząd)
        current_row = None
        cards_in_row = 0
        
        for scenario in all_scenarios:
            # Utwórz nowy rząd jeśli trzeba
            if cards_in_row == 0:
                current_row = QHBoxLayout()
                cards_in_row = 0
                
            # Utwórz kartę scenariusza
            card = ScenarioCard(scenario)
            card.scenario_selected.connect(self.start_scenario)
            current_row.addWidget(card)
            cards_in_row += 1
            
            # Dodaj rząd do layoutu gdy zapełniony
            if cards_in_row == 3:
                self.scroll_layout.addLayout(current_row)
                cards_in_row = 0
                
        # Dodaj ostatni niepełny rząd
        if current_row and cards_in_row > 0:
            current_row.addStretch()
            self.scroll_layout.addLayout(current_row)
            
        # Dodaj spacer na końcu
        self.scroll_layout.addStretch()
        
    def start_scenario(self, scenario_id: str):
        """Uruchamia wybrany scenariusz"""
        success, message = self.scenario_manager.start_scenario(scenario_id)
        if success:
            self.scenario_started.emit(scenario_id)
            self.close()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Błąd", f"Nie można uruchomić scenariusza:\n{message}") 