from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QGroupBox, QProgressBar, QScrollArea, QFrame,
                           QComboBox, QSpinBox, QMessageBox, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from core.finance import FinanceManager, LoanType
from typing import Optional, Dict

class FinancePanel(QWidget):
    """
    Panel systemu finansowego miasta - zarządzanie pożyczkami i ratingiem kredytowym.
    
    Funkcje:
    - Wyświetlanie aktualnego ratingu kredytowego
    - Lista aktywnych pożyczek
    - Składanie wniosków o nowe pożyczki
    - Analiza ryzyka bankructwa
    - Porady finansowe
    """
    
    loan_requested = pyqtSignal(str, float)  # typ_pożyczki, kwota
    
    def __init__(self, finance_manager: FinanceManager, parent=None):
        super().__init__(parent)
        self.finance_manager = finance_manager
        self.init_ui()
        
    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout()
        
        # Sekcja ratingu kredytowego
        self.create_credit_rating_section(layout)
        
        # Sekcja aktywnych pożyczek
        self.create_active_loans_section(layout)
        
        # Sekcja nowych pożyczek
        self.create_new_loan_section(layout)
        
        # Sekcja porad finansowych
        self.create_advice_section(layout)
        
        self.setLayout(layout)
        self.setWindowTitle("System Finansowy Miasta")
        self.resize(800, 600)
        
    def create_credit_rating_section(self, layout):
        """Tworzy sekcję z ratingiem kredytowym"""
        group = QGroupBox("📊 Rating Kredytowy")
        group_layout = QVBoxLayout()
        
        # Rating i punkty
        self.rating_label = QLabel("Rating: AAA")
        self.rating_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        group_layout.addWidget(self.rating_label)
        
        self.score_label = QLabel("Punkty: 750 / 850")
        group_layout.addWidget(self.score_label)
        
        # Pasek postębu ratingu
        self.rating_progress = QProgressBar()
        self.rating_progress.setRange(300, 850)
        self.rating_progress.setValue(750)
        group_layout.addWidget(self.rating_progress)
        
        # Ryzyko bankructwa
        self.bankruptcy_risk_label = QLabel("Ryzyko bankructwa: Niskie (5%)")
        group_layout.addWidget(self.bankruptcy_risk_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_active_loans_section(self, layout):
        """Tworzy sekcję z aktywnymi pożyczkami"""
        group = QGroupBox("💳 Aktywne Pożyczki")
        group_layout = QVBoxLayout()
        
        # Tabela pożyczek
        self.loans_table = QTableWidget()
        self.loans_table.setColumnCount(6)
        self.loans_table.setHorizontalHeaderLabels([
            "Typ", "Kwota główna", "Pozostało", "Rata", "Tury", "Oprocentowanie"
        ])
        group_layout.addWidget(self.loans_table)
        
        # Podsumowanie zadłużenia
        self.total_debt_label = QLabel("Całkowite zadłużenie: $0")
        self.monthly_payment_label = QLabel("Miesięczne raty: $0")
        group_layout.addWidget(self.total_debt_label)
        group_layout.addWidget(self.monthly_payment_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_new_loan_section(self, layout):
        """Tworzy sekcję składania wniosków o pożyczki"""
        group = QGroupBox("🏦 Nowa Pożyczka")
        group_layout = QVBoxLayout()
        
        # Typ pożyczki
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Typ pożyczki:"))
        self.loan_type_combo = QComboBox()
        self.loan_type_combo.addItems([
            "Standardowa", "Awaryjna", "Rozwojowa", "Infrastrukturalna"
        ])
        self.loan_type_combo.currentTextChanged.connect(self.update_loan_preview)
        type_layout.addWidget(self.loan_type_combo)
        group_layout.addLayout(type_layout)
        
        # Kwota pożyczki
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Kwota ($):"))
        self.loan_amount_spin = QSpinBox()
        self.loan_amount_spin.setRange(1000, 1000000)
        self.loan_amount_spin.setValue(10000)
        self.loan_amount_spin.setSingleStep(1000)
        self.loan_amount_spin.valueChanged.connect(self.update_loan_preview)
        amount_layout.addWidget(self.loan_amount_spin)
        group_layout.addLayout(amount_layout)
        
        # Podgląd oferty
        self.loan_preview_label = QLabel("Wybierz parametry aby zobaczyć ofertę")
        group_layout.addWidget(self.loan_preview_label)
        
        # Przycisk składania wniosku
        self.apply_loan_btn = QPushButton("📝 Złóż wniosek o pożyczkę")
        self.apply_loan_btn.clicked.connect(self.apply_for_loan)
        group_layout.addWidget(self.apply_loan_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_advice_section(self, layout):
        """Tworzy sekcję z poradami finansowymi"""
        group = QGroupBox("💡 Porady Finansowe")
        group_layout = QVBoxLayout()
        
        # Obszar przewijania dla porad
        scroll_area = QScrollArea()
        self.advice_widget = QWidget()
        self.advice_layout = QVBoxLayout(self.advice_widget)
        scroll_area.setWidget(self.advice_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        
        group_layout.addWidget(scroll_area)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def update_loan_preview(self):
        """Aktualizuje podgląd oferty pożyczki"""
        try:
            # Mapowanie typów z GUI na enums
            type_mapping = {
                "Standardowa": LoanType.STANDARD,
                "Awaryjna": LoanType.EMERGENCY,
                "Rozwojowa": LoanType.DEVELOPMENT,
                "Infrastrukturalna": LoanType.INFRASTRUCTURE
            }
            
            loan_type = type_mapping[self.loan_type_combo.currentText()]
            amount = self.loan_amount_spin.value()
            
            # Tutaj potrzebujemy dostępu do economy i population_manager
            # W prawdziwej implementacji przekazałbyś je przez konstruktor
            offer = self.finance_manager.get_loan_offer(loan_type, amount, None, None)
            
            if offer:
                preview_text = f"""
                <b>Oferta pożyczki:</b><br>
                • Kwota: ${offer['amount']:,.0f}<br>
                • Oprocentowanie: {offer['interest_rate']*100:.1f}%<br>
                • Okres: {offer['duration_turns']} tur<br>
                • Miesięczna rata: ${offer['monthly_payment']:,.0f}<br>
                • Całkowite odsetki: ${offer['total_interest']:,.0f}<br>
                • Szansa na zatwierdzenie: {offer['approval_chance']*100:.0f}%
                """
                self.loan_preview_label.setText(preview_text)
                self.apply_loan_btn.setEnabled(True)
            else:
                self.loan_preview_label.setText("❌ Nie można uzyskać tej pożyczki")
                self.apply_loan_btn.setEnabled(False)
                
        except Exception as e:
            self.loan_preview_label.setText(f"Błąd: {str(e)}")
            self.apply_loan_btn.setEnabled(False)
    
    def apply_for_loan(self):
        """Składa wniosek o pożyczkę"""
        type_mapping = {
            "Standardowa": "standard",
            "Awaryjna": "emergency", 
            "Rozwojowa": "development",
            "Infrastrukturalna": "infrastructure"
        }
        
        loan_type = type_mapping[self.loan_type_combo.currentText()]
        amount = self.loan_amount_spin.value()
        
        # Wyślij sygnał do głównego okna
        self.loan_requested.emit(loan_type, amount)
        
    def update_display(self, economy=None, population_manager=None):
        """Aktualizuje wyświetlane informacje"""
        if economy and population_manager:
            # Aktualizuj rating kredytowy
            score = self.finance_manager.calculate_credit_score(economy, population_manager)
            rating = self.finance_manager.credit_rating.value.upper()
            
            self.rating_label.setText(f"Rating: {rating}")
            self.score_label.setText(f"Punkty: {score} / 850")
            self.rating_progress.setValue(score)
            
            # Aktualizuj ryzyko bankructwa
            risk = self.finance_manager.calculate_bankruptcy_risk(economy)
            risk_text = "Niskie" if risk < 0.3 else "Średnie" if risk < 0.7 else "Wysokie"
            self.bankruptcy_risk_label.setText(f"Ryzyko bankructwa: {risk_text} ({risk*100:.0f}%)")
            
            # Aktualizuj porady finansowe
            self.update_financial_advice(economy, population_manager)
        
        # Aktualizuj tabelę pożyczek
        self.update_loans_table()
        
    def update_loans_table(self):
        """Aktualizuje tabelę aktywnych pożyczek"""
        loans = self.finance_manager.active_loans
        self.loans_table.setRowCount(len(loans))
        
        total_debt = 0
        total_monthly = 0
        
        for i, loan in enumerate(loans):
            self.loans_table.setItem(i, 0, QTableWidgetItem(loan.loan_type.value.title()))
            self.loans_table.setItem(i, 1, QTableWidgetItem(f"${loan.principal_amount:,.0f}"))
            self.loans_table.setItem(i, 2, QTableWidgetItem(f"${loan.remaining_amount:,.0f}"))
            self.loans_table.setItem(i, 3, QTableWidgetItem(f"${loan.monthly_payment:,.0f}"))
            self.loans_table.setItem(i, 4, QTableWidgetItem(str(loan.turns_remaining)))
            self.loans_table.setItem(i, 5, QTableWidgetItem(f"{loan.interest_rate*100:.1f}%"))
            
            total_debt += loan.remaining_amount
            total_monthly += loan.monthly_payment
            
        self.total_debt_label.setText(f"Całkowite zadłużenie: ${total_debt:,.0f}")
        self.monthly_payment_label.setText(f"Miesięczne raty: ${total_monthly:,.0f}")
        
    def update_financial_advice(self, economy, population_manager):
        """Aktualizuje porady finansowe"""
        # Wyczyść poprzednie porady
        for i in reversed(range(self.advice_layout.count())):
            self.advice_layout.itemAt(i).widget().setParent(None)
            
        # Pobierz nowe porady
        advice_list = self.finance_manager.get_financial_advice(economy, population_manager)
        
        for advice in advice_list:
            label = QLabel(advice)
            label.setWordWrap(True)
            label.setStyleSheet("padding: 5px; border-bottom: 1px solid #ccc;")
            self.advice_layout.addWidget(label) 