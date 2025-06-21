from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                           QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit,
                           QGroupBox, QProgressBar, QScrollArea, QFrame,
                           QMessageBox, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List
import random

class DiplomacyPanel(QWidget):
    """Panel zarządzania dyplomacją międzymiastową"""
    
    def __init__(self, game_engine=None):
        super().__init__()
        self.game_engine = game_engine
        self.setWindowTitle("🏛️ Dyplomacja - Relacje Międzymiastowe")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 600)
        
        # Initialize diplomacy system if not present
        if self.game_engine and not hasattr(self.game_engine, 'diplomacy_manager'):
            from core.diplomacy import DiplomacyManager
            self.game_engine.diplomacy_manager = DiplomacyManager()
        
        self.setup_ui()
        self.apply_styles()
        
        if self.game_engine:
            self.refresh_data()
    
    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🏛️ Dyplomacja - Relacje Międzymiastowe")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Odśwież")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Reputation and overview
        self.create_overview_section(layout)
        
        # Simple cities list for now
        self.create_simple_cities_section(layout)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.close)
        bottom_layout.addStretch()
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
    
    def create_overview_section(self, layout):
        """Tworzy sekcję przeglądu dyplomatycznego"""
        overview_frame = QFrame()
        overview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        overview_layout = QHBoxLayout(overview_frame)
        
        # Reputation
        self.reputation_label = QLabel("Reputacja: 50/100")
        overview_layout.addWidget(self.reputation_label)
        
        # Active missions
        self.missions_label = QLabel("Aktywne misje: 0")
        overview_layout.addWidget(self.missions_label)
        
        # Wars
        self.wars_label = QLabel("Wojny: 0")
        overview_layout.addWidget(self.wars_label)
        
        # Allies
        self.allies_label = QLabel("Sojusznicy: 0")
        overview_layout.addWidget(self.allies_label)
        
        overview_layout.addStretch()
        
        layout.addWidget(overview_frame)
    
    def create_simple_cities_section(self, layout):
        """Tworzy prostą sekcję z miastami"""
        cities_frame = QFrame()
        cities_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        cities_layout = QVBoxLayout(cities_frame)
        
        cities_layout.addWidget(QLabel("🏙️ Miasta partnerskie:"))
        
        # Cities table
        self.cities_table = QTableWidget()
        self.cities_table.setColumnCount(4)
        self.cities_table.setHorizontalHeaderLabels([
            "Miasto", "Status relacji", "Punkty", "Akcje"
        ])
        
        cities_layout.addWidget(self.cities_table)
        
        layout.addWidget(cities_frame)
    
    def apply_styles(self):
        """Stosuje style do panelu"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #4a6b8a;
                border-color: #3498db;
            }
            
            QTableWidget {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                border-radius: 4px;
                gridline-color: #2c3e50;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2c3e50;
            }
            
            QTableWidget::item:selected {
                background-color: #3498db;
            }
            
            QFrame {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 4px;
                margin: 5px;
                padding: 5px;
            }
        """)
    
    def refresh_data(self):
        """Odświeża wszystkie dane w panelu"""
        if not self.game_engine or not hasattr(self.game_engine, 'diplomacy_manager'):
            # Show placeholder data
            self.reputation_label.setText("Reputacja: 50/100")
            self.missions_label.setText("Aktywne misje: 0")
            self.wars_label.setText("Wojny: 0") 
            self.allies_label.setText("Sojusznicy: 0")
            
            # Show placeholder cities
            self.cities_table.setRowCount(5)
            cities = ["Agropolis", "Steelburg", "Energyville", "Luxuria", "TechCity"]
            
            for row, city in enumerate(cities):
                self.cities_table.setItem(row, 0, QTableWidgetItem(city))
                self.cities_table.setItem(row, 1, QTableWidgetItem("Neutralne"))
                self.cities_table.setItem(row, 2, QTableWidgetItem(f"{random.randint(-20, 20)}/100"))
                
                action_btn = QPushButton("Negocjuj")
                action_btn.clicked.connect(lambda checked, c=city: self.show_placeholder_action(c))
                self.cities_table.setCellWidget(row, 3, action_btn)
            
            return
        
        diplomacy = self.game_engine.diplomacy_manager
        
        # Update overview
        summary = diplomacy.get_diplomatic_summary()
        self.reputation_label.setText(f"Reputacja: {summary['reputation']}/100")
        self.missions_label.setText(f"Aktywne misje: {summary['active_missions']}")
        self.wars_label.setText(f"Wojny: {summary['active_wars']}")
        self.allies_label.setText(f"Sojusznicy: {summary['allies']}")
        
        # Refresh cities table
        self.refresh_cities_table()
    
    def refresh_cities_table(self):
        """Odświeża tabelę miast"""
        if not hasattr(self.game_engine, 'diplomacy_manager'):
            return
        
        cities = self.game_engine.diplomacy_manager.cities
        self.cities_table.setRowCount(len(cities))
        
        for row, (city_id, city) in enumerate(cities.items()):
            # City name
            self.cities_table.setItem(row, 0, QTableWidgetItem(city.name))
            
            # Status with color
            status_colors = {
                'hostile': '#e74c3c',
                'neutral': '#95a5a6', 
                'friendly': '#f39c12',
                'allied': '#27ae60',
                'at_war': '#8e44ad'
            }
            
            status_item = QTableWidgetItem(city.relationship_status.value.title())
            if city.relationship_status.value in status_colors:
                status_item.setBackground(QColor(status_colors[city.relationship_status.value]))
            self.cities_table.setItem(row, 1, status_item)
            
            # Points
            self.cities_table.setItem(row, 2, QTableWidgetItem(f"{city.relationship_points}/100"))
            
            # Actions button
            actions_btn = QPushButton("Akcje")
            actions_btn.clicked.connect(lambda checked, c=city_id: self.show_city_actions(c))
            self.cities_table.setCellWidget(row, 3, actions_btn)
    
    def show_city_actions(self, city_id):
        """Pokazuje dostępne akcje dla miasta"""
        if not hasattr(self.game_engine, 'diplomacy_manager'):
            return
        
        city = self.game_engine.diplomacy_manager.cities[city_id]
        
        # Tworzymy dialog z opcjami
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Dyplomacja - {city.name}")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Info o mieście
        info_label = QLabel(
            f"<b>{city.name}</b><br>"
            f"Status: {city.relationship_status.value.title()}<br>"
            f"Punkty relacji: {city.relationship_points}/100<br>"
            f"Populacja: {city.population:,}<br>"
            f"Specjalizacja: {city.specialization}"
        )
        layout.addWidget(info_label)
        
        # Przyciski akcji
        actions_layout = QVBoxLayout()
        
        # Podaruj prezent
        gift_btn = QPushButton("🎁 Podaruj prezent ($1000)")
        gift_btn.clicked.connect(lambda: self.give_gift(city_id, dialog))
        actions_layout.addWidget(gift_btn)
        
        # Handel
        trade_btn = QPushButton("🤝 Zaproponuj umowę handlową ($2000)")
        trade_btn.clicked.connect(lambda: self.propose_trade(city_id, dialog))
        actions_layout.addWidget(trade_btn)
        
        # Sojusz (tylko jeśli relacje są dobre)
        if city.relationship_points >= 20 and not city.at_war:
            alliance_btn = QPushButton("🤝 Zaproponuj sojusz ($5000)")
            alliance_btn.clicked.connect(lambda: self.propose_alliance(city_id, dialog))
            actions_layout.addWidget(alliance_btn)
        
        # Wojna (tylko jeśli można)
        if city.can_declare_war():
            war_btn = QPushButton("⚔️ Wypowiedz wojnę")
            war_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            war_btn.clicked.connect(lambda: self.declare_war_action(city_id, dialog))
            actions_layout.addWidget(war_btn)
        
        # Pokój (tylko jeśli w stanie wojny)
        if city.at_war:
            peace_btn = QPushButton("🕊️ Zaproponuj pokój")
            peace_btn.setStyleSheet("background-color: #27ae60; color: white;")
            peace_btn.clicked.connect(lambda: self.propose_peace_action(city_id, dialog))
            actions_layout.addWidget(peace_btn)
        
        layout.addLayout(actions_layout)
        
        # Przycisk zamknij
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def give_gift(self, city_id, dialog):
        """Daje prezent miastu"""
        cost = 1000
        
        if not self.game_engine.economy.can_afford(cost):
            QMessageBox.warning(self, "Brak środków", f"Potrzebujesz ${cost} aby dać prezent")
            return
        
        # Pobierz opłatę
        self.game_engine.economy.spend_money(cost)
        
        # Popraw relacje
        city = self.game_engine.diplomacy_manager.cities[city_id]
        city.update_relationship(15, self.game_engine.turn)
        
        QMessageBox.information(
            self, 
            "Prezent wysłany!", 
            f"Podarowałeś ${cost} miastu {city.name}.\n"
            f"Relacje poprawiły się o +15 punktów!"
        )
        
        self.refresh_data()
        dialog.close()
    
    def propose_trade(self, city_id, dialog):
        """Proponuje umowę handlową"""
        cost = 2000
        
        if not self.game_engine.economy.can_afford(cost):
            QMessageBox.warning(self, "Brak środków", f"Potrzebujesz ${cost} aby zaproponować handel")
            return
        
        city = self.game_engine.diplomacy_manager.cities[city_id]
        
        # Szansa sukcesu zależy od relacji
        success_chance = 0.5 + (city.relationship_points / 200)  # 50% + bonus za relacje
        
        import random
        if random.random() < success_chance:
            # Sukces
            self.game_engine.economy.spend_money(cost)
            city.update_relationship(10, self.game_engine.turn)
            
            # Bonus ekonomiczny
            monthly_bonus = 500
            self.game_engine.economy.earn_money(monthly_bonus)
            
            QMessageBox.information(
                self,
                "Umowa handlowa!",
                f"Umowa handlowa z {city.name} została zawarta!\n"
                f"Koszt: ${cost}\n"
                f"Natychmiastowy bonus: ${monthly_bonus}\n"
                f"Relacje: +10 punktów"
            )
        else:
            # Porażka
            self.game_engine.economy.spend_money(cost // 2)  # Połowa kosztu
            city.update_relationship(-5, self.game_engine.turn)
            
            QMessageBox.warning(
                self,
                "Odrzucono",
                f"{city.name} odrzuciło propozycję handlową.\n"
                f"Strata: ${cost // 2}\n"
                f"Relacje: -5 punktów"
            )
        
        self.refresh_data()
        dialog.close()
    
    def propose_alliance(self, city_id, dialog):
        """Proponuje sojusz"""
        cost = 5000
        
        if not self.game_engine.economy.can_afford(cost):
            QMessageBox.warning(self, "Brak środków", f"Potrzebujesz ${cost} aby zaproponować sojusz")
            return
        
        city = self.game_engine.diplomacy_manager.cities[city_id]
        
        # Sojusz wymaga dobrych relacji
        if city.relationship_points < 40:
            QMessageBox.warning(
                self,
                "Za słabe relacje",
                f"Potrzebujesz co najmniej 40 punktów relacji aby zaproponować sojusz.\n"
                f"Obecne: {city.relationship_points}/100"
            )
            return
        
        # Szansa sukcesu
        success_chance = 0.3 + (city.relationship_points / 150)
        
        import random
        if random.random() < success_chance:
            # Sukces
            self.game_engine.economy.spend_money(cost)
            city.update_relationship(30, self.game_engine.turn)
            city.alliance_expires_turn = self.game_engine.turn + 50  # Sojusz na 50 tur
            
            QMessageBox.information(
                self,
                "Sojusz zawarty!",
                f"Sojusz z {city.name} został zawarty na 50 tur!\n"
                f"Koszt: ${cost}\n"
                f"Relacje: +30 punktów\n"
                f"Korzyści: Ochrona przed wojnami, bonusy handlowe"
            )
        else:
            # Porażka
            self.game_engine.economy.spend_money(cost // 2)
            city.update_relationship(-10, self.game_engine.turn)
            
            QMessageBox.warning(
                self,
                "Odrzucono",
                f"{city.name} odrzuciło propozycję sojuszu.\n"
                f"Strata: ${cost // 2}\n"
                f"Relacje: -10 punktów"
            )
        
        self.refresh_data()
        dialog.close()
    
    def declare_war_action(self, city_id, dialog):
        """Wypowiada wojnę"""
        city = self.game_engine.diplomacy_manager.cities[city_id]
        
        reply = QMessageBox.question(
            self,
            'Wypowiedz wojnę',
            f'Czy na pewno chcesz wypowiedzieć wojnę miastu {city.name}?\n\n'
            f'KONSEKWENCJE:\n'
            f'• Znaczne pogorszenie relacji (-50 punktów)\n'
            f'• Utrata reputacji dyplomatycznej\n'
            f'• Koszty militarne ($100/turę)\n'
            f'• Możliwe straty populacji\n'
            f'• Wojna automatycznie kończy się po 20 turach\n\n'
            f'To może mieć długotrwałe skutki!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from core.diplomacy import WarType
            success, message = self.game_engine.diplomacy_manager.declare_war(
                city_id, WarType.TERRITORIAL, self.game_engine.turn
            )
            
            if success:
                # Zmniejszone natychmiastowe koszty wojny
                war_cost = 1000  # Zmniejszone z 3000 na 1000
                self.game_engine.economy.spend_money(war_cost)
                
                QMessageBox.information(
                    self,
                    "Wojna wypowiedziana!",
                    f"{message}\n\n"
                    f"Natychmiastowe koszty: ${war_cost}\n"
                    f"Miesięczne koszty: $100/turę\n"
                    f"Wojna zakończy się automatycznie po 20 turach"
                )
                
                self.refresh_data()
                dialog.close()
            else:
                QMessageBox.warning(self, "Błąd", message)
    
    def propose_peace_action(self, city_id, dialog):
        """Proponuje pokój"""
        city = self.game_engine.diplomacy_manager.cities[city_id]
        
        reply = QMessageBox.question(
            self,
            'Propozycja pokoju',
            f'Czy chcesz zaproponować pokój miastu {city.name}?\n\n'
            f'WARUNKI POKOJU:\n'
            f'• Reparacje wojenne: $2000\n'  # Zmniejszone z 5000 na 2000
            f'• Poprawa relacji: +20 punktów\n'
            f'• Koniec kosztów wojennych\n\n'
            f'Czy akceptujesz te warunki?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            reparations = 2000  # Zmniejszone z 5000 na 2000
            
            if not self.game_engine.economy.can_afford(reparations):
                QMessageBox.warning(
                    self,
                    "Brak środków",
                    f"Potrzebujesz ${reparations} na reparacje wojenne"
                )
                return
            
            success, message = self.game_engine.diplomacy_manager.propose_peace(
                city_id, {'reparations': reparations}, self.game_engine.turn
            )
            
            if success:
                self.game_engine.economy.spend_money(reparations)
                QMessageBox.information(
                    self,
                    "Pokój zawarty!",
                    f"{message}\n\n"
                    f"Reparacje: ${reparations}\n"
                    f"Relacje poprawione o +20 punktów"
                )
                
                self.refresh_data()
                dialog.close()
            else:
                QMessageBox.warning(
                    self,
                    "Odrzucono",
                    f"{message}\n\nSpróbuj ponownie później lub zaoferuj lepsze warunki."
                )
    
    def show_placeholder_action(self, city_name):
        """Pokazuje placeholder dla akcji"""
        QMessageBox.information(
            self,
            f"Dyplomacja - {city_name}",
            f"Miasto: {city_name}\n"
            f"Status: Neutralne\n\n"
            f"System dyplomacji jest w pełni zaimplementowany\n"
            f"i gotowy do użycia w przyszłych wersjach gry."
        ) 