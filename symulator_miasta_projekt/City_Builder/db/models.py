"""
Modele ORM dla bazy danych City Builder
Implementuje wszystkie tabele z wykorzystaniem SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Dict, List, Optional
import json

Base = declarative_base()

class GameState(Base):
    """Model stanu gry"""
    __tablename__ = 'game_states'
    
    id = Column(Integer, primary_key=True)
    save_name = Column(String(100), nullable=False)
    population = Column(Integer, default=0)
    money = Column(Float, default=10000.0)
    satisfaction = Column(Float, default=50.0)
    turn = Column(Integer, default=0)
    difficulty = Column(String(20), default='Normal')
    city_level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    buildings = relationship("Building", back_populates="game_state")
    technologies = relationship("ResearchedTechnology", back_populates="game_state")
    loans = relationship("Loan", back_populates="game_state")
    diplomatic_relations = relationship("DiplomaticRelation", back_populates="game_state")

class Building(Base):
    """Model budynku na mapie"""
    __tablename__ = 'buildings'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    building_type = Column(String(50), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    rotation = Column(Integer, default=0)
    level = Column(Integer, default=1)
    condition = Column(Float, default=100.0)  # Stan techniczny 0-100%
    built_turn = Column(Integer, default=0)
    
    # Relationships
    game_state = relationship("GameState", back_populates="buildings")

class ResearchedTechnology(Base):
    """Model zbadanych technologii"""
    __tablename__ = 'researched_technologies'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    technology_id = Column(String(50), nullable=False)
    research_progress = Column(Integer, default=0)
    completed_turn = Column(Integer, nullable=True)
    investment_amount = Column(Float, default=0.0)
    
    # Relationships
    game_state = relationship("GameState", back_populates="technologies")

class HistoryRecord(Base):
    """Model rekordów historycznych"""
    __tablename__ = 'history_records'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    turn = Column(Integer, nullable=False)
    population = Column(Integer, default=0)
    money = Column(Float, default=0.0)
    satisfaction = Column(Float, default=0.0)
    unemployment_rate = Column(Float, default=0.0)
    income = Column(Float, default=0.0)
    expenses = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Statistic(Base):
    """Model statystyk gry"""
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    category = Column(String(50), default='general')
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    """Model wydarzeń w grze"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    event_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    decision_made = Column(String(100))
    effects_json = Column(Text)  # JSON z efektami
    occurred_turn = Column(Integer, nullable=False)
    resolved = Column(Boolean, default=False)

class Loan(Base):
    """Model pożyczek"""
    __tablename__ = 'loans'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)  # Oprocentowanie roczne
    remaining_amount = Column(Float, nullable=False)
    monthly_payment = Column(Float, nullable=False)
    turns_remaining = Column(Integer, nullable=False)
    taken_turn = Column(Integer, nullable=False)
    loan_type = Column(String(50), default='standard')  # standard, emergency, development
    
    # Relationships
    game_state = relationship("GameState", back_populates="loans")

class DiplomaticRelation(Base):
    """Model relacji dyplomatycznych"""
    __tablename__ = 'diplomatic_relations'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    city_name = Column(String(100), nullable=False)
    relationship_status = Column(String(50), default='neutral')  # hostile, neutral, friendly, allied
    relationship_points = Column(Integer, default=0)
    trade_volume = Column(Float, default=0.0)
    last_interaction_turn = Column(Integer, default=0)
    at_war = Column(Boolean, default=False)
    alliance_expires_turn = Column(Integer, nullable=True)
    
    # Relationships
    game_state = relationship("GameState", back_populates="diplomatic_relations")

class Mission(Base):
    """Model misji dyplomatycznych"""
    __tablename__ = 'missions'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    target_city = Column(String(100), nullable=False)
    mission_type = Column(String(50), nullable=False)  # trade, alliance, peace, spy
    status = Column(String(50), default='active')  # active, completed, failed
    cost = Column(Float, default=0.0)
    duration_turns = Column(Integer, default=5)
    remaining_turns = Column(Integer, default=5)
    success_chance = Column(Float, default=0.5)
    rewards_json = Column(Text)  # JSON z nagrodami
    started_turn = Column(Integer, nullable=False)

class Achievement(Base):
    """Model osiągnięć gracza"""
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    achievement_id = Column(String(100), nullable=False)
    unlocked_turn = Column(Integer, nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

class TradeContract(Base):
    """Model kontraktów handlowych"""
    __tablename__ = 'trade_contracts'
    
    id = Column(Integer, primary_key=True)
    game_state_id = Column(Integer, ForeignKey('game_states.id'))
    partner_city = Column(String(100), nullable=False)
    good_type = Column(String(50), nullable=False)
    quantity_per_turn = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    duration_turns = Column(Integer, nullable=False)
    remaining_turns = Column(Integer, nullable=False)
    is_buying = Column(Boolean, nullable=False)
    total_value = Column(Float, default=0.0)
    signed_turn = Column(Integer, nullable=False)

class DatabaseManager:
    """Menedżer bazy danych z ORM"""
    
    def __init__(self, db_url: str = "sqlite:///city_builder.db"):
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Tworzy wszystkie tabele"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Zwraca sesję bazy danych"""
        return self.SessionLocal()
    
    def migrate_schema(self):
        """Wykonuje migracje schematu"""
        # Sprawdź czy istnieją nowe kolumny i dodaj je
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        
        # Przykład migracji - dodanie nowych kolumn
        existing_tables = inspector.get_table_names()
        
        if 'game_states' in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('game_states')]
            if 'city_level' not in columns:
                self.engine.execute('ALTER TABLE game_states ADD COLUMN city_level INTEGER DEFAULT 1')
            if 'difficulty' not in columns:
                self.engine.execute('ALTER TABLE game_states ADD COLUMN difficulty VARCHAR(20) DEFAULT "Normal"')
    
    # CRUD Operations
    def save_game_state(self, game_data: Dict) -> int:
        """Zapisuje stan gry"""
        session = self.get_session()
        try:
            game_state = GameState(
                save_name=game_data.get('save_name', 'Autosave'),
                population=game_data.get('population', 0),
                money=game_data.get('money', 10000),
                satisfaction=game_data.get('satisfaction', 50),
                turn=game_data.get('turn', 0),
                difficulty=game_data.get('difficulty', 'Normal'),
                city_level=game_data.get('city_level', 1)
            )
            session.add(game_state)
            session.commit()
            return game_state.id
        finally:
            session.close()
    
    def load_game_state(self, game_id: int) -> Optional[Dict]:
        """Wczytuje stan gry"""
        session = self.get_session()
        try:
            game_state = session.query(GameState).filter(GameState.id == game_id).first()
            if game_state:
                return {
                    'id': game_state.id,
                    'save_name': game_state.save_name,
                    'population': game_state.population,
                    'money': game_state.money,
                    'satisfaction': game_state.satisfaction,
                    'turn': game_state.turn,
                    'difficulty': game_state.difficulty,
                    'city_level': game_state.city_level,
                    'created_at': game_state.created_at,
                    'updated_at': game_state.updated_at
                }
            return None
        finally:
            session.close()
    
    def save_building(self, game_state_id: int, building_data: Dict):
        """Zapisuje budynek"""
        session = self.get_session()
        try:
            building = Building(
                game_state_id=game_state_id,
                building_type=building_data['type'],
                x=building_data['x'],
                y=building_data['y'],
                rotation=building_data.get('rotation', 0),
                level=building_data.get('level', 1),
                condition=building_data.get('condition', 100.0),
                built_turn=building_data.get('built_turn', 0)
            )
            session.add(building)
            session.commit()
        finally:
            session.close()
    
    def save_loan(self, game_state_id: int, loan_data: Dict):
        """Zapisuje pożyczkę"""
        session = self.get_session()
        try:
            loan = Loan(
                game_state_id=game_state_id,
                amount=loan_data['amount'],
                interest_rate=loan_data['interest_rate'],
                remaining_amount=loan_data['remaining_amount'],
                monthly_payment=loan_data['monthly_payment'],
                turns_remaining=loan_data['turns_remaining'],
                taken_turn=loan_data['taken_turn'],
                loan_type=loan_data.get('loan_type', 'standard')
            )
            session.add(loan)
            session.commit()
        finally:
            session.close()
    
    def get_active_loans(self, game_state_id: int) -> List[Dict]:
        """Pobiera aktywne pożyczki"""
        session = self.get_session()
        try:
            loans = session.query(Loan).filter(
                Loan.game_state_id == game_state_id,
                Loan.turns_remaining > 0
            ).all()
            
            return [{
                'id': loan.id,
                'amount': loan.amount,
                'interest_rate': loan.interest_rate,
                'remaining_amount': loan.remaining_amount,
                'monthly_payment': loan.monthly_payment,
                'turns_remaining': loan.turns_remaining,
                'loan_type': loan.loan_type
            } for loan in loans]
        finally:
            session.close()
    
    def save_diplomatic_relation(self, game_state_id: int, relation_data: Dict):
        """Zapisuje relację dyplomatyczną"""
        session = self.get_session()
        try:
            # Sprawdź czy relacja już istnieje
            existing = session.query(DiplomaticRelation).filter(
                DiplomaticRelation.game_state_id == game_state_id,
                DiplomaticRelation.city_name == relation_data['city_name']
            ).first()
            
            if existing:
                # Aktualizuj istniejącą
                existing.relationship_status = relation_data['relationship_status']
                existing.relationship_points = relation_data['relationship_points']
                existing.trade_volume = relation_data.get('trade_volume', 0.0)
                existing.at_war = relation_data.get('at_war', False)
                existing.alliance_expires_turn = relation_data.get('alliance_expires_turn')
            else:
                # Utwórz nową
                relation = DiplomaticRelation(
                    game_state_id=game_state_id,
                    city_name=relation_data['city_name'],
                    relationship_status=relation_data['relationship_status'],
                    relationship_points=relation_data['relationship_points'],
                    trade_volume=relation_data.get('trade_volume', 0.0),
                    at_war=relation_data.get('at_war', False),
                    alliance_expires_turn=relation_data.get('alliance_expires_turn')
                )
                session.add(relation)
            
            session.commit()
        finally:
            session.close()
    
    def get_diplomatic_relations(self, game_state_id: int) -> List[Dict]:
        """Pobiera relacje dyplomatyczne"""
        session = self.get_session()
        try:
            relations = session.query(DiplomaticRelation).filter(
                DiplomaticRelation.game_state_id == game_state_id
            ).all()
            
            return [{
                'city_name': rel.city_name,
                'relationship_status': rel.relationship_status,
                'relationship_points': rel.relationship_points,
                'trade_volume': rel.trade_volume,
                'at_war': rel.at_war,
                'alliance_expires_turn': rel.alliance_expires_turn
            } for rel in relations]
        finally:
            session.close()
    
    def close(self):
        """Zamyka połączenie z bazą danych"""
        self.engine.dispose()


