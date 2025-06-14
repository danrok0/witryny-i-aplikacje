"""
DatabaseAdmin - Narzędzia administracyjne dla bazy danych
Etap 4: Integracja z bazą danych
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .database_manager import DatabaseManager


logger = logging.getLogger(__name__)

class DatabaseAdmin:
    """
    Klasa do zarządzania bazą danych - statystyki, backup, czyszczenie.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        logger.info("Inicjalizacja DatabaseAdmin")
    
    def display_database_statistics(self) -> None:
        """Wyświetla szczegółowe statystyki bazy danych."""
        try:
            print("\n" + "="*60)
            print("📊 STATYSTYKI BAZY DANYCH")
            print("="*60)
            
            stats = self.db_manager.get_database_stats()
            
            print(f"📁 Rozmiar bazy danych: {stats.get('database_size_mb', 0)} MB")
            print(f"🏔️  Liczba tras: {stats.get('routes_count', 0)}")
            print(f"🌤️  Rekordy pogodowe: {stats.get('weather_records', 0)}")
            print(f"📝 Recenzje: {stats.get('reviews_count', 0)}")
            print(f"👤 Preferencje użytkowników: {stats.get('user_preferences', 0)}")
            
            if stats.get('popular_regions'):
                print(f"\n🗺️  NAJPOPULARNIEJSZE REGIONY:")
                for region in stats['popular_regions'][:5]:
                    print(f"   • {region['region']}: {region['count']} tras")
            
            if stats.get('difficulty_distribution'):
                print(f"\n⚡ ROZKŁAD TRUDNOŚCI:")
                difficulty_names = {1: "Łatwe", 2: "Średnie", 3: "Trudne", 4: "Bardzo trudne", 5: "Ekstremalne"}
                for diff in stats['difficulty_distribution']:
                    name = difficulty_names.get(diff['difficulty'], f"Poziom {diff['difficulty']}")
                    print(f"   • {name}: {diff['count']} tras")
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Błąd wyświetlania statystyk: {e}")
            print(f"❌ Błąd pobierania statystyk: {e}")
    
    def check_database_integrity(self) -> bool:
        """Sprawdza integralność bazy danych i wyświetla raport."""
        try:
            print("\n🔍 SPRAWDZANIE INTEGRALNOŚCI BAZY DANYCH...")
            
            # Sprawdź integralność SQLite
            integrity_ok = self.db_manager.check_database_integrity()
            
            if integrity_ok:
                print("✅ Integralność bazy danych: OK")
                
                # Dodatkowe sprawdzenia
                issues = []
                
                # Sprawdź trasy bez współrzędnych
                routes_without_coords = self.db_manager.execute_query("""
                    SELECT COUNT(*) as count FROM routes 
                    WHERE start_lat IS NULL OR start_lon IS NULL 
                    OR end_lat IS NULL OR end_lon IS NULL
                """)
                
                if routes_without_coords and routes_without_coords[0]['count'] > 0:
                    issues.append(f"⚠️  {routes_without_coords[0]['count']} tras bez współrzędnych")
                
                # Sprawdź dane pogodowe bez daty
                weather_without_date = self.db_manager.execute_query("""
                    SELECT COUNT(*) as count FROM weather_data 
                    WHERE date IS NULL
                """)
                
                if weather_without_date and weather_without_date[0]['count'] > 0:
                    issues.append(f"⚠️  {weather_without_date[0]['count']} rekordów pogodowych bez daty")
                
                # Sprawdź trasy bez nazwy
                routes_without_name = self.db_manager.execute_query("""
                    SELECT COUNT(*) as count FROM routes 
                    WHERE name IS NULL OR name = ''
                """)
                
                if routes_without_name and routes_without_name[0]['count'] > 0:
                    issues.append(f"⚠️  {routes_without_name[0]['count']} tras bez nazwy")
                
                if issues:
                    print("\n🔧 ZNALEZIONE PROBLEMY:")
                    for issue in issues:
                        print(f"   {issue}")
                    print("\n💡 Zalecenie: Rozważ czyszczenie niepełnych danych")
                else:
                    print("✅ Nie znaleziono problemów z danymi")
                
                return True
            else:
                print("❌ Integralność bazy danych: BŁĄD")
                return False
                
        except Exception as e:
            logger.error(f"Błąd sprawdzania integralności: {e}")
            print(f"❌ Błąd sprawdzania integralności: {e}")
            return False
    
    def create_backup(self, backup_name: str = None) -> bool:
        """Tworzy kopię zapasową bazy danych."""
        try:
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db"
            
            backup_path = os.path.join("data", "backups", backup_name)
            
            # Upewnij się, że katalog backups istnieje
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            print(f"\n💾 Tworzenie kopii zapasowej...")
            print(f"📁 Lokalizacja: {backup_path}")
            
            success = self.db_manager.backup_database(backup_path)
            
            if success:
                # Sprawdź rozmiar kopii zapasowej
                backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
                print(f"✅ Kopia zapasowa utworzona pomyślnie")
                print(f"📊 Rozmiar kopii: {backup_size:.2f} MB")
                return True
            else:
                print("❌ Błąd tworzenia kopii zapasowej")
                return False
                
        except Exception as e:
            logger.error(f"Błąd tworzenia kopii zapasowej: {e}")
            print(f"❌ Błąd tworzenia kopii zapasowej: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Wyświetla listę dostępnych kopii zapasowych."""
        try:
            backup_dir = os.path.join("data", "backups")
            
            if not os.path.exists(backup_dir):
                print("📁 Brak katalogu z kopiami zapasowymi")
                return []
            
            backups = []
            
            for filename in os.listdir(backup_dir):
                # Sprawdź czy to plik (nie katalog) i czy ma odpowiedni rozmiar
                filepath = os.path.join(backup_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    
                    # Sprawdź czy plik ma rozsądny rozmiar (większy niż 1KB)
                    if stat.st_size > 1024:
                        backup_info = {
                            'filename': filename,
                            'filepath': filepath,
                            'size_mb': round(stat.st_size / (1024 * 1024), 2),
                            'created': datetime.fromtimestamp(stat.st_ctime),
                            'modified': datetime.fromtimestamp(stat.st_mtime)
                        }
                        backups.append(backup_info)
            
            # Sortuj po dacie utworzenia (najnowsze pierwsze)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            if backups:
                print(f"\n💾 DOSTĘPNE KOPIE ZAPASOWE ({len(backups)}):")
                print("-" * 80)
                for i, backup in enumerate(backups, 1):
                    created_str = backup['created'].strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{i:2d}. {backup['filename']}")
                    print(f"    📅 Utworzono: {created_str}")
                    print(f"    📊 Rozmiar: {backup['size_mb']} MB")
                    print()
            else:
                print("📁 Brak kopii zapasowych")
            
            return backups
            
        except Exception as e:
            logger.error(f"Błąd listowania kopii zapasowych: {e}")
            print(f"❌ Błąd listowania kopii zapasowych: {e}")
            return []
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Przywraca bazę danych z kopii zapasowej."""
        try:
            backup_path = os.path.join("data", "backups", backup_filename)
            
            if not os.path.exists(backup_path):
                print(f"❌ Plik kopii zapasowej nie istnieje: {backup_filename}")
                return False
            
            print(f"\n🔄 Przywracanie bazy danych z kopii zapasowej...")
            print(f"📁 Źródło: {backup_path}")
            
            # Ostrzeżenie
            response = input("⚠️  UWAGA: Ta operacja zastąpi obecną bazę danych. Kontynuować? (tak/nie): ")
            if response.lower() not in ['tak', 't', 'yes', 'y']:
                print("❌ Operacja anulowana")
                return False
            
            success = self.db_manager.restore_database(backup_path)
            
            if success:
                print("✅ Baza danych przywrócona pomyślnie")
                return True
            else:
                print("❌ Błąd przywracania bazy danych")
                return False
                
        except Exception as e:
            logger.error(f"Błąd przywracania kopii zapasowej: {e}")
            print(f"❌ Błąd przywracania kopii zapasowej: {e}")
            return False
    
    def clean_old_data(self, days_old: int = 30) -> bool:
        """Czyści stare dane z bazy danych."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
            
            print(f"\n🧹 CZYSZCZENIE STARYCH DANYCH (starsze niż {days_old} dni)")
            print(f"📅 Data graniczna: {cutoff_date}")
            
            # Sprawdź ile danych zostanie usuniętych
            old_weather_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM weather_data WHERE date < ?", 
                (cutoff_date,)
            )
            
            if old_weather_count and old_weather_count[0]['count'] > 0:
                count = old_weather_count[0]['count']
                response = input(f"⚠️  Zostanie usuniętych {count} rekordów pogodowych. Kontynuować? (tak/nie): ")
                
                if response.lower() in ['tak', 't', 'yes', 'y']:
                    # Usuń stare dane pogodowe
                    query = "DELETE FROM weather_data WHERE date < ?"
                    deleted_count = self.db_manager.execute_update(query, (cutoff_date,))
                    print(f"✅ Usunięto {deleted_count} starych rekordów pogodowych")
                    
                    # Optymalizuj bazę danych
                    print("🔧 Optymalizacja bazy danych...")
                    self.db_manager.vacuum_database()
                    
                    return True
                else:
                    print("❌ Operacja anulowana")
                    return False
            else:
                print("ℹ️  Brak starych danych do usunięcia")
                return True
                
        except Exception as e:
            logger.error(f"Błąd czyszczenia starych danych: {e}")
            print(f"❌ Błąd czyszczenia starych danych: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """Optymalizuje bazę danych (VACUUM)."""
        try:
            print("\n🔧 OPTYMALIZACJA BAZY DANYCH...")
            
            # Sprawdź rozmiar przed optymalizacją
            size_before = 0
            if os.path.exists(self.db_manager.db_path):
                size_before = os.path.getsize(self.db_manager.db_path) / (1024 * 1024)
            
            print(f"📊 Rozmiar przed optymalizacją: {size_before:.2f} MB")
            
            success = self.db_manager.vacuum_database()
            
            if success:
                # Sprawdź rozmiar po optymalizacji
                size_after = 0
                if os.path.exists(self.db_manager.db_path):
                    size_after = os.path.getsize(self.db_manager.db_path) / (1024 * 1024)
                
                saved_space = size_before - size_after
                
                print(f"📊 Rozmiar po optymalizacji: {size_after:.2f} MB")
                if saved_space > 0:
                    print(f"💾 Zaoszczędzono: {saved_space:.2f} MB")
                
                print("✅ Optymalizacja zakończona pomyślnie")
                return True
            else:
                print("❌ Błąd optymalizacji bazy danych")
                return False
                
        except Exception as e:
            logger.error(f"Błąd optymalizacji bazy danych: {e}")
            print(f"❌ Błąd optymalizacji bazy danych: {e}")
            return False
    
    def export_database_report(self, output_file: str = None) -> bool:
        """Eksportuje szczegółowy raport bazy danych do pliku."""
        try:
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"database_report_{timestamp}.txt"
            
            print(f"\n📄 GENEROWANIE RAPORTU BAZY DANYCH...")
            print(f"📁 Plik wyjściowy: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("RAPORT BAZY DANYCH SYSTEMU REKOMENDACJI TRAS\n")
                f.write("=" * 60 + "\n")
                f.write(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Podstawowe statystyki
                stats = self.db_manager.get_database_stats()
                f.write("PODSTAWOWE STATYSTYKI:\n")
                f.write(f"- Rozmiar bazy danych: {stats.get('database_size_mb', 0)} MB\n")
                f.write(f"- Liczba tras: {stats.get('routes_count', 0)}\n")
                f.write(f"- Rekordy pogodowe: {stats.get('weather_records', 0)}\n")
                f.write(f"- Recenzje: {stats.get('reviews_count', 0)}\n")
                f.write(f"- Preferencje użytkowników: {stats.get('user_preferences', 0)}\n\n")
                
                # Najpopularniejsze regiony
                if stats.get('popular_regions'):
                    f.write("NAJPOPULARNIEJSZE REGIONY:\n")
                    for region in stats['popular_regions']:
                        f.write(f"- {region['region']}: {region['count']} tras\n")
                    f.write("\n")
                
                # Rozkład trudności
                if stats.get('difficulty_distribution'):
                    f.write("ROZKŁAD TRUDNOŚCI:\n")
                    difficulty_names = {1: "Łatwe", 2: "Średnie", 3: "Trudne", 4: "Bardzo trudne", 5: "Ekstremalne"}
                    for diff in stats['difficulty_distribution']:
                        name = difficulty_names.get(diff['difficulty'], f"Poziom {diff['difficulty']}")
                        f.write(f"- {name}: {diff['count']} tras\n")
                    f.write("\n")
                
                f.write("=" * 60 + "\n")
                f.write("Raport wygenerowany przez DatabaseAdmin\n")
            
            print(f"✅ Raport zapisany: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd eksportu raportu: {e}")
            print(f"❌ Błąd eksportu raportu: {e}")
            return False
    
 