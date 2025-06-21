#!/usr/bin/env python3
"""
Skrypt do uruchamiania testów jednostkowych City Builder
"""
import sys
import os
import subprocess
from pathlib import Path

# Sprawdź czy pytest jest zainstalowany
try:
    import pytest
except ImportError:
    print("❌ pytest nie jest zainstalowany!")
    print("Zainstaluj wymagania: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Główna funkcja uruchamiająca testy"""
    
    # Przejdź do katalogu projektu
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🧪 Uruchamianie testów jednostkowych City Builder...")
    print("=" * 60)
    
    # Argumenty dla pytest
    pytest_args = [
        "-v",                    # verbose output
        "--tb=short",           # krótkie traceback
        "--color=yes",          # kolorowe output
        "tests/",               # katalog z testami
    ]
    
    # Dodaj dodatkowe argumenty z linii poleceń
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    
    try:
        # Uruchom testy
        result = pytest.main(pytest_args)
        
        print("\n" + "=" * 60)
        if result == 0:
            print("✅ Wszystkie testy przeszły pomyślnie!")
        else:
            print("❌ Niektóre testy nie przeszły.")
            
        return result
        
    except Exception as e:
        print(f"❌ Błąd podczas uruchamiania testów: {e}")
        return 1

def run_specific_test(test_name):
    """Uruchom konkretny test"""
    print(f"🧪 Uruchamianie testu: {test_name}")
    
    pytest_args = [
        "-v",
        "--tb=short", 
        "--color=yes",
        f"tests/{test_name}"
    ]
    
    return pytest.main(pytest_args)

def run_coverage():
    """Uruchom testy z pokryciem kodu"""
    try:
        import coverage
    except ImportError:
        print("❌ coverage nie jest zainstalowany!")
        print("Zainstaluj: pip install coverage")
        return 1
    
    print("📊 Uruchamianie testów z analizą pokrycia kodu...")
    
    # Uruchom coverage
    cmd = [
        sys.executable, "-m", "coverage", "run", 
        "--source=core,gui", 
        "-m", "pytest", "tests/", "-v"
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        # Pokaż raport
        subprocess.run([sys.executable, "-m", "coverage", "report"])
        subprocess.run([sys.executable, "-m", "coverage", "html"])
        print("\n📊 Raport HTML wygenerowany w htmlcov/index.html")
    
    return result.returncode

if __name__ == "__main__":
    # Sprawdź argumenty
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--coverage":
            sys.exit(run_coverage())
        elif arg.startswith("test_"):
            sys.exit(run_specific_test(arg))
        elif arg == "--help":
            print("Użycie:")
            print("  python run_tests.py                 # Uruchom wszystkie testy")
            print("  python run_tests.py --coverage      # Testy z pokryciem kodu")
            print("  python run_tests.py test_engine.py  # Konkretny plik testów")
            print("  python run_tests.py --help          # Ta pomoc")
            sys.exit(0)
    
    sys.exit(main()) 