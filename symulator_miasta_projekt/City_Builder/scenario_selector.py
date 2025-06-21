#!/usr/bin/env python3
"""
Aplikacja wyboru scenariusza dla City Builder.
Uruchamia się przed główną grą i pozwala wybrać tryb gry.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Dodaj ścieżkę do modułów
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.scenarios import ScenarioManager
from gui.scenarios_panel import ScenariosPanel

class ScenarioSelectorDialog(QDialog):
    """Dialog wyboru scenariusza na początku gry"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_scenario = None
        self.scenario_manager = ScenarioManager()
        self.init_ui()
        
    def init_ui(self):
        """Inicjalizuje interfejs"""
        self.setWindowTitle("City Builder - Wybór Trybu Gry")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Nagłówek
        title_label = QLabel("🏙️ City Builder")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Wybierz tryb gry")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Szybkie przyciski dla popularnych trybów
        quick_buttons_layout = QHBoxLayout()
        
        sandbox_btn = QPushButton("🏖️ Tryb Piaskownicy\n(Nieograniczone zasoby)")
        sandbox_btn.setMinimumHeight(80)
        sandbox_btn.clicked.connect(lambda: self.select_scenario("sandbox"))
        quick_buttons_layout.addWidget(sandbox_btn)
        
        campaign_btn = QPushButton("📜 Kampania\n(Pierwsze kroki)")
        campaign_btn.setMinimumHeight(80)
        campaign_btn.clicked.connect(lambda: self.select_scenario("campaign_01_tutorial"))
        quick_buttons_layout.addWidget(campaign_btn)
        
        custom_btn = QPushButton("⚙️ Więcej opcji\n(Wszystkie scenariusze)")
        custom_btn.setMinimumHeight(80)
        custom_btn.clicked.connect(self.show_all_scenarios)
        quick_buttons_layout.addWidget(custom_btn)
        
        layout.addLayout(quick_buttons_layout)
        
        # Opis wybranego trybu
        self.description_label = QLabel("Wybierz tryb gry aby zobaczyć opis")
        self.description_label.setWordWrap(True)
        self.description_label.setMinimumHeight(100)
        self.description_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.description_label)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Rozpocznij Grę")
        self.start_btn.setEnabled(False)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.start_btn)
        
        cancel_btn = QPushButton("❌ Anuluj")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
    def select_scenario(self, scenario_id: str):
        """Wybiera scenariusz"""
        self.selected_scenario = scenario_id
        self.start_btn.setEnabled(True)
        
        # Pobierz szczegóły scenariusza
        details = self.scenario_manager.get_scenario_details(scenario_id)
        if details:
            description = f"""
            <b>{details['title']}</b><br><br>
            {details['description']}<br><br>
            <b>Typ:</b> {details['type'].title()}<br>
            <b>Trudność:</b> {details['difficulty'].title()}<br>
            <b>Pieniądze startowe:</b> ${details['starting_conditions']['money']:,}
            """
            self.description_label.setText(description)
        
    def show_all_scenarios(self):
        """Pokazuje panel ze wszystkimi scenariuszami"""
        scenarios_panel = ScenariosPanel(self.scenario_manager, self)
        scenarios_panel.scenario_started.connect(self.on_scenario_selected)
        scenarios_panel.exec()
        
    def on_scenario_selected(self, scenario_id: str):
        """Obsługuje wybór scenariusza z panelu"""
        self.selected_scenario = scenario_id
        self.accept()

def run_scenario_selector():
    """Uruchamia selektor scenariuszy"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = ScenarioSelectorDialog()
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted and dialog.selected_scenario:
        return dialog.selected_scenario
    else:
        return None

if __name__ == "__main__":
    scenario_id = run_scenario_selector()
    if scenario_id:
        print(f"Wybrany scenariusz: {scenario_id}")
        # Tutaj można uruchomić główną grę z wybranym scenariuszem
        import subprocess
        import sys
        subprocess.run([sys.executable, "Main.py", "--scenario", scenario_id])
    else:
        print("Anulowano wybór scenariusza") 