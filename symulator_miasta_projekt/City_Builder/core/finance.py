"""
System finansowy i zarządzania kredytami dla City Builder.
Implementuje pożyczki, rating kredytowy, raporty finansowe i analizę ryzyka bankructwa.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import random
import math
from datetime import datetime, timedelta
import logging

class LoanType(Enum):
    """
    Typy pożyczek dostępnych w grze.
    
    Każdy typ ma różne warunki, oprocentowanie i wymagania:
    - STANDARD: podstawowa pożyczka z przeciętnym oprocentowaniem
    - EMERGENCY: szybka pożyczka w kryzysie, wyższe oprocentowanie
    - DEVELOPMENT: na rozwój miasta, niższe oprocentowanie, dłuższy okres
    - INFRASTRUCTURE: na infrastrukturę, specjalne warunki
    """
    STANDARD = "standard"
    EMERGENCY = "emergency"
    DEVELOPMENT = "development"
    INFRASTRUCTURE = "infrastructure"

class CreditRating(Enum):
    """
    Rating kredytowy miasta - ocena zdolności do spłaty długów.
    
    Wpływa na:
    - Dostępność pożyczek
    - Oprocentowanie (lepszy rating = niższe odsetki)
    - Maksymalne kwoty pożyczek
    - Warunki negocjacji
    
    Skala od najlepszego do najgorszego:
    """
    EXCELLENT = "excellent"  # AAA - najlepszy rating, najniższe oprocentowanie
    GOOD = "good"           # AA - dobry rating
    FAIR = "fair"           # A - przeciętny rating
    POOR = "poor"           # BBB - słaby rating, wyższe oprocentowanie
    BAD = "bad"             # BB i niżej - bardzo słaby rating, trudno dostać pożyczkę

@dataclass
class Loan:
    """
    Reprezentuje pożyczkę zaciągniętą przez miasto.
    
    @dataclass automatycznie generuje __init__, __repr__ i inne metody
    Zawiera wszystkie informacje o pożyczce i jej spłacie.
    """
    id: str  # unikalny identyfikator pożyczki
    loan_type: LoanType  # typ pożyczki
    principal_amount: float  # kwota główna (bez odsetek)
    interest_rate: float  # roczna stopa procentowa (np. 0.05 = 5%)
    remaining_amount: float  # pozostała kwota do spłaty
    monthly_payment: float  # miesięczna rata
    turns_remaining: int  # pozostałe tury do spłaty
    taken_turn: int  # tura, w której zaciągnięto pożyczkę
    credit_rating_at_time: CreditRating  # rating w momencie zaciągania
    collateral: Optional[str] = None  # zabezpieczenie (opcjonalne)
    
    def calculate_total_interest(self) -> float:
        """
        Oblicza całkowite odsetki do zapłacenia za pożyczkę.
        
        Returns:
            float: łączna kwota odsetek
            
        Wzór: (miesięczna_rata × liczba_rat) - kwota_główna = odsetki
        """
        total_payments = self.monthly_payment * (self.turns_remaining + 1)
        return total_payments - self.principal_amount

class FinancialReport:
    """
    Raport finansowy miasta za jedną turę.
    Zawiera wszystkie kluczowe wskaźniki finansowe.
    """
    
    def __init__(self, turn: int, data: Dict):
        """
        Tworzy raport finansowy.
        
        Args:
            turn: numer tury
            data: słownik z danymi finansowymi (dochody, wydatki, aktywa, etc.)
        """
        self.turn = turn
        self.timestamp = datetime.now()
        self.income = data.get('income', 0)  # dochody z podatków
        self.expenses = data.get('expenses', 0)  # wydatki operacyjne
        self.net_income = self.income - self.expenses
        self.assets = data.get('assets', 0)  # aktywa (gotówka + wartość budynków)
        self.liabilities = data.get('liabilities', 0)  # zobowiązania (pożyczki)
        self.equity = self.assets - self.liabilities
        self.cash = data.get('cash', 0)  # gotówka
        self.cash_flow = data.get('cash_flow', 0)  # przepływ gotówki (dochody - wydatki)
        self.debt_to_equity_ratio = self.liabilities / max(self.equity, 1)
        self.liquidity_ratio = self.cash / max(self.expenses, 1)

class FinanceManager:
    """
    Zarządca systemu finansowego miasta.
    
    Odpowiada za:
    - Obliczanie ratingu kredytowego
    - Zarządzanie pożyczkami
    - Generowanie raportów finansowych
    - Analizę ryzyka bankructwa
    - Porady finansowe dla gracza
    """
    
    def __init__(self):
        """
        Inicjalizuje system finansowy z pustymi listami i domyślnymi wartościami.
        """
        self.active_loans: List[Loan] = []  # aktywne pożyczki
        self.loan_history: List[Loan] = []  # historia spłaconych pożyczek
        self.financial_reports: List[FinancialReport] = []  # historia raportów
        self.credit_score = 750  # punkty kredytowe (300-850, jak w rzeczywistości)
        self.credit_rating = CreditRating.GOOD  # aktualny rating
        self.bankruptcy_risk = 0.0  # ryzyko bankructwa (0.0-1.0)
        self.logger = logging.getLogger('finance')
        
        # Statystyki
        self.total_borrowed = 0  # łączna kwota zaciągniętych pożyczek
        self.total_repaid = 0  # łączna kwota spłaconych pożyczek
        self.missed_payments = 0  # liczba niespłaconych rat
        self.successful_payments = 0  # liczba terminowych spłat
        
        # Ustawienia pożyczek
        self.base_interest_rates = {
            LoanType.STANDARD: 0.05,      # 5%
            LoanType.EMERGENCY: 0.12,     # 12%
            LoanType.DEVELOPMENT: 0.07,   # 7%
            LoanType.INFRASTRUCTURE: 0.04  # 4%
        }
        
        # Limity pożyczek
        self.loan_limits = {
            LoanType.STANDARD: 50000,
            LoanType.EMERGENCY: 20000,
            LoanType.DEVELOPMENT: 100000,
            LoanType.INFRASTRUCTURE: 200000
        }
    
    def calculate_credit_score(self, economy, population_manager) -> int:
        """
        Oblicza punkty kredytowe miasta na podstawie sytuacji finansowej.
        
        Args:
            economy: obiekt zarządzający ekonomią miasta
            population_manager: zarządca populacji
            
        Returns:
            int: punkty kredytowe (300-850)
            
        Uwzględnia:
        - Stosunek długu do dochodów
        - Historię płatności
        - Stabilność finansową
        - Poziom zadłużenia
        """
        base_score = 500  # bazowa punktacja
        
        # Czynnik 1: Historia płatności (35% wpływ na score)
        if self.successful_payments + self.missed_payments > 0:
            payment_ratio = self.successful_payments / (self.successful_payments + self.missed_payments)
            payment_score = payment_ratio * 300  # max 300 punktów za płatności
        else:
            payment_score = 200  # domyślna wartość dla nowych miast
        
        # Czynnik 2: Poziom zadłużenia (30% wpływ)
        money = economy.get_resource_amount('money')
        total_debt = sum(loan.remaining_amount for loan in self.active_loans)
        
        if money > 0:
            debt_to_cash_ratio = total_debt / money
            if debt_to_cash_ratio < 0.3:  # dług < 30% gotówki
                debt_score = 150
            elif debt_to_cash_ratio < 0.7:  # dług < 70% gotówki
                debt_score = 100
            elif debt_to_cash_ratio < 1.5:  # dług < 150% gotówki
                debt_score = 50
            else:
                debt_score = 0  # wysokie zadłużenie
        else:
            debt_score = 0 if total_debt > 0 else 100
        
        # Czynnik 3: Stabilność dochodów (20% wpływ)
        if len(self.financial_reports) >= 5:
            recent_incomes = [report.income for report in self.financial_reports[-5:]]
            income_stability = 1.0 - (max(recent_incomes) - min(recent_incomes)) / max(max(recent_incomes), 1)
            stability_score = income_stability * 100
        else:
            stability_score = 50  # średnia wartość dla nowych miast
        
        # Czynnik 4: Długość historii kredytowej (15% wpływ)
        credit_history_length = len(self.loan_history) + len(self.active_loans)
        if credit_history_length >= 10:
            history_score = 100
        elif credit_history_length >= 5:
            history_score = 75
        elif credit_history_length >= 2:
            history_score = 50
        else:
            history_score = 25
        
        # Zsumuj wszystkie składniki
        total_score = base_score + payment_score + debt_score + stability_score + history_score
        
        # Ogranicz do zakresu 300-850
        self.credit_score = max(300, min(850, int(total_score)))
        self._update_credit_rating()
        
        return self.credit_score
    
    def _update_credit_rating(self):
        """
        Aktualizuje rating kredytowy na podstawie punktów.
        
        Metoda prywatna - konwertuje liczbowe punkty na kategorię ratingu.
        Używana wewnętrznie po obliczeniu credit_score.
        """
        if self.credit_score >= 800:
            self.credit_rating = CreditRating.EXCELLENT
        elif self.credit_score >= 740:
            self.credit_rating = CreditRating.GOOD
        elif self.credit_score >= 670:
            self.credit_rating = CreditRating.FAIR
        elif self.credit_score >= 580:
            self.credit_rating = CreditRating.POOR
        else:
            self.credit_rating = CreditRating.BAD
    
    def get_loan_offer(self, loan_type: LoanType, amount: float, 
                      economy, population_manager) -> Optional[Dict]:
        """
        Generuje ofertę pożyczki dla miasta.
        
        Args:
            loan_type: typ żądanej pożyczki
            amount: kwota pożyczki
            economy: system ekonomiczny miasta
            population_manager: zarządca populacji
            
        Returns:
            Optional[Dict]: oferta pożyczki lub None jeśli odrzucona
            
        Proces:
        1. Sprawdza zdolność kredytową
        2. Oblicza oprocentowanie na podstawie ratingu
        3. Określa warunki spłaty
        4. Kalkuluje szansę na zatwierdzenie
        """
        # Sprawdź maksymalną kwotę dla danego ratingu
        max_amounts = {
            CreditRating.EXCELLENT: 10000000,  # 10M
            CreditRating.GOOD: 5000000,        # 5M
            CreditRating.FAIR: 2000000,        # 2M
            CreditRating.POOR: 500000,         # 500K
            CreditRating.BAD: 100000           # 100K
        }
        
        max_amount = max_amounts[self.credit_rating]
        if amount > max_amount:
            return None  # kwota przekracza limit dla tego ratingu
        
        # Bazowe oprocentowanie dla różnych typów pożyczek
        base_rates = {
            LoanType.STANDARD: 0.08,      # 8% rocznie
            LoanType.EMERGENCY: 0.15,     # 15% rocznie (droższe, ale szybkie)
            LoanType.DEVELOPMENT: 0.06,   # 6% rocznie (preferencyjne dla rozwoju)
            LoanType.INFRASTRUCTURE: 0.05 # 5% rocznie (najniższe dla infrastruktury)
        }
        
        # Modyfikatory oprocentowania na podstawie ratingu
        rating_modifiers = {
            CreditRating.EXCELLENT: 0.7,  # 30% zniżka
            CreditRating.GOOD: 0.85,      # 15% zniżka
            CreditRating.FAIR: 1.0,       # standardowa stawka
            CreditRating.POOR: 1.3,       # 30% podwyżka
            CreditRating.BAD: 1.8         # 80% podwyżka
        }
        
        base_rate = base_rates[loan_type]
        rating_modifier = rating_modifiers[self.credit_rating]
        final_rate = base_rate * rating_modifier
        
        # Okres spłaty w zależności od typu pożyczki
        duration_turns = {
            LoanType.STANDARD: 24,        # 2 lata
            LoanType.EMERGENCY: 12,       # 1 rok
            LoanType.DEVELOPMENT: 60,     # 5 lat
            LoanType.INFRASTRUCTURE: 120  # 10 lat
        }[loan_type]
        
        # Oblicz miesięczną ratę (wzór na ratę kredytu)
        monthly_payment = self._calculate_monthly_payment(amount, final_rate, duration_turns)
        
        # Oblicz szansę na zatwierdzenie
        approval_chance = self._calculate_approval_chance()
        
        return {
            'loan_type': loan_type,
            'amount': amount,
            'interest_rate': final_rate,
            'duration_turns': duration_turns,
            'monthly_payment': monthly_payment,
            'total_interest': (monthly_payment * duration_turns) - amount,
            'approval_chance': approval_chance,
            'credit_rating': self.credit_rating
        }
    
    def _calculate_monthly_payment(self, principal: float, annual_rate: float, turns: int) -> float:
        """
        Oblicza miesięczną ratę pożyczki według wzoru na ratę kredytu.
        
        Args:
            principal: kwota główna pożyczki
            annual_rate: roczna stopa procentowa (np. 0.08 = 8%)
            turns: liczba rat (tur)
            
        Returns:
            float: miesięczna rata
            
        Używa wzoru na ratę kredytu:
        PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
        gdzie P=kwota, r=oprocentowanie miesięczne, n=liczba rat
        """
        if annual_rate == 0:
            return principal / turns  # brak odsetek
        
        monthly_rate = annual_rate / 12  # zamień roczną stopę na miesięczną
        # Wzór na ratę kredytu (annuity formula)
        payment = principal * (monthly_rate * (1 + monthly_rate) ** turns) / ((1 + monthly_rate) ** turns - 1)
        return payment
    
    def _calculate_approval_chance(self) -> float:
        """
        Oblicza szansę na zatwierdzenie pożyczki na podstawie ratingu i historii.
        
        Returns:
            float: szansa na zatwierdzenie (0.0-1.0)
            
        Uwzględnia:
        - Rating kredytowy (główny czynnik)
        - Liczbę aktywnych pożyczek (każda kolejna zmniejsza szansę)
        - Historię płatności
        """
        # Bazowa szansa na podstawie ratingu
        base_chance = {
            CreditRating.EXCELLENT: 0.95,  # 95% szansy
            CreditRating.GOOD: 0.85,       # 85% szansy
            CreditRating.FAIR: 0.70,       # 70% szansy
            CreditRating.POOR: 0.45,       # 45% szansy
            CreditRating.BAD: 0.20         # 20% szansy
        }
        
        chance = base_chance[self.credit_rating]
        
        # Zmniejsz szansę za każdą aktywną pożyczkę (banki nie lubią wysokiego zadłużenia)
        chance -= len(self.active_loans) * 0.1
        
        # Ogranicz do zakresu 0.1-0.95 (zawsze jest minimalna szansa)
        return max(0.1, min(0.95, chance))
    
    def take_loan(self, loan_offer: Dict, turn: int) -> Tuple[bool, str]:
        """Zaciąga pożyczkę"""
        approval_chance = loan_offer['approval_chance']
        
        if random.random() > approval_chance:
            return False, "Wniosek o pożyczkę został odrzucony"
        
        loan = Loan(
            id=f"loan_{turn}_{len(self.active_loans)}",
            loan_type=loan_offer['loan_type'],
            principal_amount=loan_offer['amount'],
            interest_rate=loan_offer['interest_rate'],
            remaining_amount=loan_offer['amount'],
            monthly_payment=loan_offer['monthly_payment'],
            turns_remaining=loan_offer['duration_turns'],
            taken_turn=turn,
            credit_rating_at_time=self.credit_rating
        )
        
        self.active_loans.append(loan)
        return True, f"Pożyczka na kwotę ${loan_offer['amount']:,.0f} została zatwierdzona"
    
    def process_loan_payments(self, economy, turn: int) -> Dict:
        """Przetwarza spłaty pożyczek"""
        total_payment = 0
        completed_loans = []
        payment_details = []
        
        for loan in self.active_loans:
            if loan.turns_remaining > 0:
                # Sprawdź czy można dokonać spłaty
                if economy.can_afford(loan.monthly_payment):
                    economy.spend_money(loan.monthly_payment)
                    
                    # Oblicz część kapitałową i odsetkową
                    interest_portion = loan.remaining_amount * (loan.interest_rate / 12)
                    principal_portion = loan.monthly_payment - interest_portion
                    
                    loan.remaining_amount -= principal_portion
                    loan.turns_remaining -= 1
                    total_payment += loan.monthly_payment
                    
                    payment_details.append({
                        'loan_id': loan.id,
                        'payment': loan.monthly_payment,
                        'principal': principal_portion,
                        'interest': interest_portion,
                        'remaining': loan.remaining_amount
                    })
                    
                    if loan.turns_remaining == 0:
                        completed_loans.append(loan)
                        self.loan_history.append(loan)
                else:
                    # Brak środków na spłatę - kara
                    self.credit_score -= 10
                    payment_details.append({
                        'loan_id': loan.id,
                        'payment': 0,
                        'missed': True,
                        'penalty': loan.monthly_payment * 0.05
                    })
        
        # Usuń spłacone pożyczki
        for loan in completed_loans:
            self.active_loans.remove(loan)
        
        return {
            'total_payment': total_payment,
            'completed_loans': len(completed_loans),
            'payment_details': payment_details,
            'active_loans_count': len(self.active_loans)
        }
    
    def generate_financial_report(self, turn: int, economy, population_manager, 
                                buildings: List) -> FinancialReport:
        """Generuje raport finansowy"""
        
        # Oblicz aktywa
        money = economy.get_resource_amount('money')
        building_value = sum(getattr(building, 'cost', 0) * 0.8 for building in buildings)  # 80% wartości
        total_assets = money + building_value
        
        # Oblicz zobowiązania
        total_liabilities = sum(loan.remaining_amount for loan in self.active_loans)
        
        # Oblicz dochody i wydatki
        income = economy.calculate_taxes(buildings, population_manager)
        expenses = economy.calculate_expenses(buildings, population_manager)
        loan_payments = sum(loan.monthly_payment for loan in self.active_loans)
        total_expenses = expenses + loan_payments
        
        report_data = {
            'income': income,
            'expenses': total_expenses,
            'assets': total_assets,
            'liabilities': total_liabilities,
            'cash': money,
            'cash_flow': income - total_expenses
        }
        
        report = FinancialReport(turn, report_data)
        self.financial_reports.append(report)
        
        # Zachowaj tylko ostatnie 100 raportów
        if len(self.financial_reports) > 100:
            self.financial_reports.pop(0)
        
        return report
    
    def calculate_bankruptcy_risk(self, economy) -> float:
        """Oblicza ryzyko bankructwa"""
        money = economy.get_resource_amount('money')
        total_debt = sum(loan.remaining_amount for loan in self.active_loans)
        monthly_obligations = sum(loan.monthly_payment for loan in self.active_loans)
        
        risk_factors = []
        
        # Czynnik 1: Stosunek długu do gotówki
        if money > 0:
            debt_to_cash = total_debt / money
            risk_factors.append(min(1.0, debt_to_cash / 5))  # Ryzyko rośnie gdy dług > 5x gotówka
        else:
            risk_factors.append(1.0)
        
        # Czynnik 2: Zdolność do spłaty miesięcznych zobowiązań
        if money > 0:
            months_coverage = money / max(monthly_obligations, 1)
            risk_factors.append(max(0, 1 - months_coverage / 6))  # Ryzyko gdy < 6 miesięcy pokrycia
        else:
            risk_factors.append(1.0)
        
        # Czynnik 3: Trend finansowy
        if len(self.financial_reports) >= 3:
            recent_reports = self.financial_reports[-3:]
            cash_flow_trend = [r.cash_flow for r in recent_reports]
            if all(cf < 0 for cf in cash_flow_trend):
                risk_factors.append(0.8)  # Wysokie ryzyko przy ciągłych stratach
            elif cash_flow_trend[-1] < cash_flow_trend[0]:
                risk_factors.append(0.4)  # Średnie ryzyko przy pogarszającym się trendzie
            else:
                risk_factors.append(0.1)  # Niskie ryzyko przy poprawie
        
        # Czynnik 4: Rating kredytowy
        rating_risk = {
            CreditRating.EXCELLENT: 0.05,
            CreditRating.GOOD: 0.1,
            CreditRating.FAIR: 0.2,
            CreditRating.POOR: 0.4,
            CreditRating.BAD: 0.7
        }
        risk_factors.append(rating_risk[self.credit_rating])
        
        # Oblicz średnie ważone ryzyko
        self.bankruptcy_risk = sum(risk_factors) / len(risk_factors)
        return self.bankruptcy_risk
    
    def get_financial_advice(self, economy, population_manager) -> List[str]:
        """Generuje porady finansowe"""
        advice = []
        
        money = economy.get_resource_amount('money')
        total_debt = sum(loan.remaining_amount for loan in self.active_loans)
        monthly_obligations = sum(loan.monthly_payment for loan in self.active_loans)
        
        # Analiza gotówki
        if money < monthly_obligations * 3:
            advice.append("⚠️ Niski poziom gotówki. Rozważ zwiększenie podatków lub ograniczenie wydatków.")
        
        # Analiza zadłużenia
        if total_debt > money * 2:
            advice.append("💳 Wysokie zadłużenie. Skup się na spłacie pożyczek przed nowymi inwestycjami.")
        
        # Analiza ratingu
        if self.credit_rating in [CreditRating.POOR, CreditRating.BAD]:
            advice.append("📉 Niski rating kredytowy. Popraw sytuację finansową przed zaciąganiem nowych pożyczek.")
        
        # Analiza trendów
        if len(self.financial_reports) >= 5:
            recent_cash_flows = [r.cash_flow for r in self.financial_reports[-5:]]
            if all(cf < 0 for cf in recent_cash_flows):
                advice.append("📊 Ciągłe straty. Przeanalizuj źródła dochodów i koszty.")
        
        # Pozytywne porady
        if self.credit_rating == CreditRating.EXCELLENT and money > 100000:
            advice.append("✅ Doskonała sytuacja finansowa. Rozważ inwestycje rozwojowe.")
        
        if not self.active_loans and money > 50000:
            advice.append("💰 Brak zadłużenia i dobra sytuacja finansowa. Czas na ekspansję!")
        
        return advice if advice else ["✅ Sytuacja finansowa jest stabilna."]
    
    def export_financial_data(self) -> Dict:
        """Eksportuje dane finansowe do analizy"""
        return {
            'credit_score': self.credit_score,
            'credit_rating': self.credit_rating.value,
            'bankruptcy_risk': self.bankruptcy_risk,
            'active_loans': [{
                'id': loan.id,
                'type': loan.loan_type.value,
                'amount': loan.principal_amount,
                'remaining': loan.remaining_amount,
                'payment': loan.monthly_payment,
                'turns_left': loan.turns_remaining,
                'interest_rate': loan.interest_rate
            } for loan in self.active_loans],
            'financial_history': [{
                'turn': report.turn,
                'income': report.income,
                'expenses': report.expenses,
                'net_income': report.net_income,
                'assets': report.assets,
                'liabilities': report.liabilities,
                'cash_flow': report.cash_flow
            } for report in self.financial_reports[-20:]]  # Ostatnie 20 raportów
        }
    
    def save_to_dict(self) -> Dict:
        """Zapisuje stan do słownika"""
        return {
            'credit_score': self.credit_score,
            'credit_rating': self.credit_rating.value,
            'bankruptcy_risk': self.bankruptcy_risk,
            'active_loans': [{
                'id': loan.id,
                'loan_type': loan.loan_type.value,
                'principal_amount': loan.principal_amount,
                'interest_rate': loan.interest_rate,
                'remaining_amount': loan.remaining_amount,
                'monthly_payment': loan.monthly_payment,
                'turns_remaining': loan.turns_remaining,
                'taken_turn': loan.taken_turn,
                'credit_rating_at_time': loan.credit_rating_at_time.value
            } for loan in self.active_loans]
        }
    
    def load_from_dict(self, data: Dict):
        """Wczytuje stan ze słownika"""
        self.credit_score = data.get('credit_score', 750)
        self.credit_rating = CreditRating(data.get('credit_rating', 'good'))
        self.bankruptcy_risk = data.get('bankruptcy_risk', 0.0)
        
        # Wczytaj pożyczki
        self.active_loans = []
        for loan_data in data.get('active_loans', []):
            loan = Loan(
                id=loan_data['id'],
                loan_type=LoanType(loan_data['loan_type']),
                principal_amount=loan_data['principal_amount'],
                interest_rate=loan_data['interest_rate'],
                remaining_amount=loan_data['remaining_amount'],
                monthly_payment=loan_data['monthly_payment'],
                turns_remaining=loan_data['turns_remaining'],
                taken_turn=loan_data['taken_turn'],
                credit_rating_at_time=CreditRating(loan_data['credit_rating_at_time'])
            )
            self.active_loans.append(loan) 