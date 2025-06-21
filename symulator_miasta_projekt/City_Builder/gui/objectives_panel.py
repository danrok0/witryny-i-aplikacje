from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QScrollArea, QFrame, QPushButton, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from core.objectives import ObjectiveManager, ObjectiveStatus

class ObjectiveWidget(QFrame):
    """Widget reprezentujący pojedynczy cel"""
    
    def __init__(self, objective, parent=None):
        super().__init__(parent)
        self.objective = objective
        self.init_ui()
    
    def init_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        
        # Tytuł celu
        title_label = QLabel(self.objective.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        
        # Kolor tytułu w zależności od statusu
        if self.objective.status == ObjectiveStatus.COMPLETED:
            title_label.setStyleSheet("color: green;")
        elif self.objective.status == ObjectiveStatus.FAILED:
            title_label.setStyleSheet("color: red;")
        elif self.objective.status == ObjectiveStatus.ACTIVE:
            title_label.setStyleSheet("color: blue;")
        else:
            title_label.setStyleSheet("color: gray;")
        
        layout.addWidget(title_label)
        
        # Opis celu
        desc_label = QLabel(self.objective.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(desc_label)
        
        # Pasek postępu
        if self.objective.status == ObjectiveStatus.ACTIVE:
            progress_layout = QHBoxLayout()
            
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(int(self.objective.target_value))
            progress_bar.setValue(int(self.objective.current_value))
            progress_bar.setFormat(f"{int(self.objective.current_value)}/{int(self.objective.target_value)}")
            
            progress_layout.addWidget(progress_bar)
            
            # Procent ukończenia
            if self.objective.target_value > 0:
                percentage = (self.objective.current_value / self.objective.target_value) * 100
                percent_label = QLabel(f"{percentage:.1f}%")
                percent_label.setMinimumWidth(50)
                progress_layout.addWidget(percent_label)
            
            layout.addLayout(progress_layout)
        
        # Status i limit czasu
        status_layout = QHBoxLayout()
        
        status_label = QLabel(f"Status: {self.objective.status.value}")
        status_layout.addWidget(status_label)
        
        if self.objective.turns_remaining is not None:
            time_label = QLabel(f"Pozostało tur: {self.objective.turns_remaining}")
            time_label.setStyleSheet("color: orange; font-weight: bold;")
            status_layout.addWidget(time_label)
        
        layout.addLayout(status_layout)
        
        # Nagrody
        if self.objective.reward_money > 0 or self.objective.reward_satisfaction > 0:
            reward_text = "Nagroda: "
            rewards = []
            if self.objective.reward_money > 0:
                rewards.append(f"${self.objective.reward_money}")
            if self.objective.reward_satisfaction > 0:
                rewards.append(f"+{self.objective.reward_satisfaction}% zadowolenia")
            
            reward_text += ", ".join(rewards)
            
            reward_label = QLabel(reward_text)
            reward_label.setStyleSheet("color: #2e8b57; font-weight: bold; font-size: 9px;")
            layout.addWidget(reward_label)
        
        self.setLayout(layout)
        
        # Stylowanie ramki w zależności od statusu
        if self.objective.status == ObjectiveStatus.COMPLETED:
            self.setStyleSheet("QFrame { border: 2px solid green; background-color: #f0fff0; }")
        elif self.objective.status == ObjectiveStatus.FAILED:
            self.setStyleSheet("QFrame { border: 2px solid red; background-color: #fff0f0; }")
        elif self.objective.status == ObjectiveStatus.ACTIVE:
            self.setStyleSheet("QFrame { border: 2px solid blue; background-color: #f0f8ff; }")
        else:
            self.setStyleSheet("QFrame { border: 1px solid gray; background-color: #f5f5f5; }")

class ObjectivesPanel(QWidget):
    """Panel główny dla systemu celów"""
    
    objective_completed = pyqtSignal(str)  # Signal emitowany gdy cel zostanie ukończony
    
    def __init__(self, objective_manager: ObjectiveManager, parent=None):
        super().__init__(parent)
        self.objective_manager = objective_manager
        self.objective_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tytuł panelu
        title_label = QLabel("🎯 Cele i Misje")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Podsumowanie postępu
        self.summary_label = QLabel()
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setStyleSheet("background-color: #e6f3ff; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.summary_label)
        
        # Zakładki dla różnych typów celów
        self.tab_widget = QTabWidget()
        
        # Zakładka aktywnych celów
        self.active_tab = QWidget()
        self.active_scroll = QScrollArea()
        self.active_scroll.setWidgetResizable(True)
        self.active_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.active_content = QWidget()
        self.active_layout = QVBoxLayout(self.active_content)
        self.active_scroll.setWidget(self.active_content)
        
        active_tab_layout = QVBoxLayout(self.active_tab)
        active_tab_layout.addWidget(self.active_scroll)
        
        # Zakładka ukończonych celów
        self.completed_tab = QWidget()
        self.completed_scroll = QScrollArea()
        self.completed_scroll.setWidgetResizable(True)
        self.completed_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.completed_content = QWidget()
        self.completed_layout = QVBoxLayout(self.completed_content)
        self.completed_scroll.setWidget(self.completed_content)
        
        completed_tab_layout = QVBoxLayout(self.completed_tab)
        completed_tab_layout.addWidget(self.completed_scroll)
        
        # Dodaj zakładki
        self.tab_widget.addTab(self.active_tab, "Aktywne")
        self.tab_widget.addTab(self.completed_tab, "Ukończone")
        
        layout.addWidget(self.tab_widget)
        
        # Przycisk odświeżania
        refresh_btn = QPushButton("🔄 Odśwież")
        refresh_btn.clicked.connect(self.refresh_objectives)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        self.setWindowTitle("Cele i Misje")
        self.resize(400, 600)
        
        # Początkowe załadowanie celów
        self.refresh_objectives()
    
    def refresh_objectives(self):
        """Odświeża wyświetlanie wszystkich celów"""
        # Wyczyść istniejące widgety
        self.clear_layout(self.active_layout)
        self.clear_layout(self.completed_layout)
        self.objective_widgets.clear()
        
        # Aktywne cele
        active_objectives = self.objective_manager.get_active_objectives()
        if active_objectives:
            for objective in active_objectives:
                widget = ObjectiveWidget(objective)
                self.objective_widgets[objective.id] = widget
                self.active_layout.addWidget(widget)
        else:
            no_active_label = QLabel("Brak aktywnych celów")
            no_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_active_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            self.active_layout.addWidget(no_active_label)
        
        # Dodaj spacer na końcu
        self.active_layout.addStretch()
        
        # Ukończone cele
        completed_objectives = self.objective_manager.get_completed_objectives()
        if completed_objectives:
            for objective in completed_objectives:
                widget = ObjectiveWidget(objective)
                self.completed_layout.addWidget(widget)
        else:
            no_completed_label = QLabel("Brak ukończonych celów")
            no_completed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_completed_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            self.completed_layout.addWidget(no_completed_label)
        
        # Dodaj spacer na końcu
        self.completed_layout.addStretch()
        
        # Aktualizuj podsumowanie
        self.update_summary()
    
    def clear_layout(self, layout):
        """Czyści wszystkie widgety z layoutu"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_summary(self):
        """Aktualizuje podsumowanie postępu"""
        summary = self.objective_manager.get_objectives_summary()
        
        summary_text = (
            f"📊 Postęp: {summary['completed']}/{summary['total']} celów ukończonych "
            f"({summary['completion_rate']*100:.1f}%)\n"
            f"🎯 Aktywne: {summary['active']} | "
            f"✅ Ukończone: {summary['completed']} | "
            f"❌ Nieudane: {summary['failed']}"
        )
        
        self.summary_label.setText(summary_text)
    
    def update_objectives(self, game_state):
        """Aktualizuje cele na podstawie stanu gry"""
        # Sprawdź czy jakieś cele zostały ukończone
        old_completed = set(self.objective_manager.completed_objectives)
        
        # Aktualizuj cele
        self.objective_manager.update_objectives(game_state)
        
        # Sprawdź nowe ukończenia
        new_completed = set(self.objective_manager.completed_objectives)
        newly_completed = new_completed - old_completed
        
        # Emituj sygnały dla nowo ukończonych celów
        for obj_id in newly_completed:
            self.objective_completed.emit(obj_id)
        
        # Odśwież widgety tylko jeśli są zmiany
        if newly_completed or self.should_refresh_widgets():
            self.refresh_objectives()
        else:
            # Tylko aktualizuj istniejące widgety
            self.update_existing_widgets()
    
    def should_refresh_widgets(self):
        """Sprawdza czy należy odświeżyć widgety"""
        # Sprawdź czy liczba aktywnych celów się zmieniła
        current_active = len(self.objective_manager.get_active_objectives())
        displayed_active = len([w for w in self.objective_widgets.values() 
                               if w.objective.status == ObjectiveStatus.ACTIVE])
        
        return current_active != displayed_active
    
    def update_existing_widgets(self):
        """Aktualizuje istniejące widgety bez pełnego odświeżania"""
        for obj_id, widget in self.objective_widgets.items():
            if obj_id in self.objective_manager.objectives:
                # Aktualizuj dane w widgecie
                widget.objective = self.objective_manager.objectives[obj_id]
                # Można dodać tutaj bardziej szczegółową aktualizację widgetu
        
        # Aktualizuj podsumowanie
        self.update_summary() 