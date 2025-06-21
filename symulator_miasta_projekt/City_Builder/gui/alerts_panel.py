from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QListWidget, QListWidgetItem, QComboBox, 
                           QCheckBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import List, Dict
import time

class AlertsPanel(QWidget):
    """Panel do wyświetlania i zarządzania alertami miasta"""
    
    def __init__(self, game_engine=None):
        super().__init__()
        self.game_engine = game_engine
        self.setWindowTitle("🚨 Alerty Miasta")
        self.setGeometry(150, 150, 800, 600)
        self.setMinimumSize(700, 500)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_alerts)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
        self.setup_ui()
        self.apply_styles()
        
        if self.game_engine:
            self.refresh_alerts()
    
    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🚨 Alerty Miasta")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Odśwież")
        self.refresh_btn.clicked.connect(self.refresh_alerts)
        header_layout.addWidget(self.refresh_btn)
        
        # Clear all button
        self.clear_btn = QPushButton("🗑️ Wyczyść wszystkie")
        self.clear_btn.clicked.connect(self.clear_all_alerts)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Priority filter
        filter_layout.addWidget(QLabel("Filtr priorytetów:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["Wszystkie", "Krytyczne", "Ostrzeżenia", "Informacje"])
        self.priority_filter.currentTextChanged.connect(self.filter_alerts)
        filter_layout.addWidget(self.priority_filter)
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-przewijanie do najnowszych")
        self.auto_scroll_cb.setChecked(True)
        filter_layout.addWidget(self.auto_scroll_cb)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # Stats panel
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_alerts_label = QLabel("Wszystkich: 0")
        self.critical_alerts_label = QLabel("🚨 Krytycznych: 0")
        self.warning_alerts_label = QLabel("⚠️ Ostrzeżeń: 0")
        self.info_alerts_label = QLabel("ℹ️ Informacji: 0")
        
        stats_layout.addWidget(self.total_alerts_label)
        stats_layout.addWidget(self.critical_alerts_label)
        stats_layout.addWidget(self.warning_alerts_label)
        stats_layout.addWidget(self.info_alerts_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
        
        # Alerts list
        self.alerts_list = QListWidget()
        self.alerts_list.setAlternatingRowColors(True)
        self.alerts_list.setWordWrap(True)
        layout.addWidget(self.alerts_list)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("Gotowy")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
    
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
            
            QPushButton:pressed {
                background-color: #2980b9;
            }
            
            QListWidget {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }
            
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border-radius: 3px;
                border: 1px solid transparent;
            }
            
            QListWidget::item:selected {
                background-color: #3498db;
                border-color: #2980b9;
            }
            
            QComboBox {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border-color: #3498db;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #2c3e50;
                border-radius: 3px;
                background-color: #34495e;
            }
            
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border-color: #2ecc71;
            }
            
            QFrame {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 4px;
                margin: 5px;
                padding: 5px;
            }
            
            QLabel {
                padding: 2px;
            }
        """)
    
    def refresh_alerts(self):
        """Odświeża listę alertów"""
        if not self.game_engine:
            return
        
        try:
            # Get all alerts from game engine
            all_alerts = getattr(self.game_engine, 'alerts', [])
            
            # Update stats
            self.update_stats(all_alerts)
            
            # Filter and display alerts
            self.filter_alerts()
            
            self.status_label.setText(f"Ostatnia aktualizacja: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.status_label.setText(f"Błąd odświeżania: {str(e)}")
    
    def update_stats(self, alerts: List[Dict]):
        """Aktualizuje statystyki alertów"""
        total = len(alerts)
        critical = len([a for a in alerts if a.get('priority') == 'critical'])
        warning = len([a for a in alerts if a.get('priority') == 'warning'])
        info = len([a for a in alerts if a.get('priority') == 'info'])
        
        self.total_alerts_label.setText(f"Wszystkich: {total}")
        self.critical_alerts_label.setText(f"🚨 Krytycznych: {critical}")
        self.warning_alerts_label.setText(f"⚠️ Ostrzeżeń: {warning}")
        self.info_alerts_label.setText(f"ℹ️ Informacji: {info}")
    
    def filter_alerts(self):
        """Filtruje alerty według wybranego priorytetu"""
        if not self.game_engine:
            return
        
        self.alerts_list.clear()
        
        all_alerts = getattr(self.game_engine, 'alerts', [])
        filter_priority = self.priority_filter.currentText()
        
        # Apply filter
        if filter_priority == "Wszystkie":
            filtered_alerts = all_alerts
        elif filter_priority == "Krytyczne":
            filtered_alerts = [a for a in all_alerts if a.get('priority') == 'critical']
        elif filter_priority == "Ostrzeżenia":
            filtered_alerts = [a for a in all_alerts if a.get('priority') == 'warning']
        elif filter_priority == "Informacje":
            filtered_alerts = [a for a in all_alerts if a.get('priority') == 'info']
        else:
            filtered_alerts = all_alerts
        
        # Sort by timestamp (newest first)
        filtered_alerts.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Add alerts to list
        for alert in filtered_alerts:
            self.add_alert_to_list(alert)
        
        # Auto-scroll to top if enabled
        if self.auto_scroll_cb.isChecked() and filtered_alerts:
            self.alerts_list.scrollToTop()
    
    def add_alert_to_list(self, alert: Dict):
        """Dodaje alert do listy"""
        # Format timestamp
        timestamp = alert.get('timestamp', time.time())
        time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
        
        # Get priority info
        priority = alert.get('priority', 'info')
        priority_icons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'achievement': '🏆'
        }
        
        priority_icon = priority_icons.get(priority, 'ℹ️')
        
        # Format message
        message = alert.get('message', 'Brak wiadomości')
        turn = alert.get('turn', 0)
        
        # Create display text
        display_text = f"{priority_icon} [{time_str}] Tura {turn}: {message}"
        
        # Create list item
        item = QListWidgetItem(display_text)
        
        # Set item colors based on priority
        if priority == 'critical':
            item.setBackground(QColor(231, 76, 60, 50))  # Red background
        elif priority == 'warning':
            item.setBackground(QColor(243, 156, 18, 50))  # Orange background
        elif priority == 'achievement':
            item.setBackground(QColor(241, 196, 15, 50))  # Gold background
        else:
            item.setBackground(QColor(52, 73, 94, 50))  # Default background
        
        # Add tooltip with full information
        tooltip = f"Priorytet: {priority.title()}\nTura: {turn}\nCzas: {time_str}\n\nWiadomość:\n{message}"
        item.setToolTip(tooltip)
        
        self.alerts_list.addItem(item)
    
    def clear_all_alerts(self):
        """Czyści wszystkie alerty"""
        if not self.game_engine:
            return
        
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, 
            'Wyczyść alerty', 
            'Czy na pewno chcesz wyczyścić wszystkie alerty?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.game_engine.clear_alerts()
            self.refresh_alerts()
            self.status_label.setText("Wszystkie alerty zostały wyczyszczone")
    
    def closeEvent(self, event):
        """Zatrzymuje timer przy zamykaniu panelu"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)

    def generate_alerts(self) -> List[Dict]:
        """Generuje alerty na podstawie stanu gry"""
        alerts = []
        
        if not self.game_engine:
            return []
        
        # Pobierz dane ekonomiczne
        money = self.game_engine.economy.get_resource_amount('money')
        population = self.game_engine.population.get_total_population() if hasattr(self.game_engine, 'population') else 0
        satisfaction = self.game_engine.population.get_average_satisfaction() if hasattr(self.game_engine, 'population') else 50
        
        # Oblicz dochody i wydatki
        buildings = self.game_engine.get_all_buildings() if hasattr(self.game_engine, 'get_all_buildings') else []
        income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population) if buildings else 0
        expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population) if buildings else 0
        net_income = income - expenses
        
        # Alerty finansowe
        if money < 0:
            alerts.append({
                'type': 'critical',
                'title': '💸 Dług publiczny!',
                'message': f'Miasto ma dług ${abs(money):,.0f}. Ryzyko bankructwa!',
                'timestamp': time.time(),
                'priority': 1
            })
        elif money < 2000:
            alerts.append({
                'type': 'warning', 
                'title': '⚠️ Niski budżet',
                'message': f'Pozostało tylko ${money:,.0f}. Zwiększ dochody lub zmniejsz wydatki.',
                'timestamp': time.time(),
                'priority': 2
            })
        
        # Analiza dochodów vs wydatków
        if net_income < -500:
            alerts.append({
                'type': 'critical',
                'title': '📉 Deficyt budżetowy!',
                'message': f'Wydatki (${expenses:,.0f}) znacznie przewyższają dochody (${income:,.0f}). Deficyt: ${abs(net_income):,.0f}/turę',
                'timestamp': time.time(),
                'priority': 1
            })
        elif net_income < 0:
            alerts.append({
                'type': 'warning',
                'title': '⚖️ Ujemny bilans',
                'message': f'Dochody: ${income:,.0f}, Wydatki: ${expenses:,.0f}. Strata: ${abs(net_income):,.0f}/turę',
                'timestamp': time.time(),
                'priority': 2
            })
        elif net_income > 2000:
            alerts.append({
                'type': 'info',
                'title': '💰 Nadwyżka budżetowa',
                'message': f'Zysk: ${net_income:,.0f}/turę. Rozważ inwestycje rozwojowe.',
                'timestamp': time.time(),
                'priority': 3
            })
        
        # Alerty społeczne
        if satisfaction < 30:
            alerts.append({
                'type': 'critical',
                'title': '😡 Bardzo niezadowoleni mieszkańcy!',
                'message': f'Zadowolenie: {satisfaction:.1f}%. Ryzyko protestów i emigracji!',
                'timestamp': time.time(),
                'priority': 1
            })
        elif satisfaction < 50:
            alerts.append({
                'type': 'warning',
                'title': '😐 Niezadowoleni mieszkańcy',
                'message': f'Zadowolenie: {satisfaction:.1f}%. Popraw usługi miejskie.',
                'timestamp': time.time(),
                'priority': 2
            })
        
        # Alerty podatków
        total_tax_rate = sum(self.game_engine.economy.tax_rates.values())
        if total_tax_rate > 0.4:  # Ponad 40% łączne podatki
            alerts.append({
                'type': 'warning',
                'title': '📊 Wysokie podatki',
                'message': f'Łączne stawki podatkowe: {total_tax_rate:.1%}. Mogą obniżyć zadowolenie.',
                'timestamp': time.time(),
                'priority': 2
            })
        
        # Porady ekonomiczne
        if net_income < 0 and total_tax_rate < 0.2:  # Niskie podatki przy deficycie
            alerts.append({
                'type': 'info',
                'title': '💡 Porada: Podatki',
                'message': 'Przy deficycie rozważ zwiększenie podatków. Obecne stawki są niskie.',
                'timestamp': time.time(),
                'priority': 3
            })
        
        if expenses > income * 1.5:  # Wydatki > 150% dochodów
            alerts.append({
                'type': 'warning',
                'title': '💡 Porada: Wydatki',
                'message': 'Wydatki są bardzo wysokie. Sprawdź koszty utrzymania budynków.',
                'timestamp': time.time(),
                'priority': 2
            })
        
        # Alerty o zmianach dochodów
        if hasattr(self.game_engine.economy, 'get_income_change_alerts'):
            income_alerts = self.game_engine.economy.get_income_change_alerts()
            for alert_msg in income_alerts[-3:]:  # Ostatnie 3 alerty
                priority = 'warning' if ('spadły' in alert_msg or 'wzrosły' in alert_msg) else 'info'
                alerts.append({
                    'type': priority,
                    'title': '📊 Zmiana dochodów',
                    'message': alert_msg,
                    'timestamp': time.time(),
                    'priority': 2 if priority == 'warning' else 3
                })
        
        # Informacje o ostatnich wydarzeniach
        if hasattr(self.game_engine, 'alerts') and self.game_engine.alerts:
            recent_events = self.game_engine.alerts[-3:]  # Ostatnie 3 wydarzenia
            for event in recent_events:
                if isinstance(event, str):
                    alerts.append({
                        'type': 'info',
                        'title': '📰 Ostatnie wydarzenie',
                        'message': event,
                        'timestamp': time.time(),
                        'priority': 3
                    })
        
        return sorted(alerts, key=lambda x: x['priority']) 