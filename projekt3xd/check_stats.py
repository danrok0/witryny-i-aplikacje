import json

# Sprawdź statystyki tras
with open('test_trails_gdansk.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"📊 Pobrano {len(data)} tras dla Gdańska")

lengths = [t['length_km'] for t in data]
print(f"📏 Długości: min={min(lengths):.1f}km, max={max(lengths):.1f}km, średnia={sum(lengths)/len(lengths):.1f}km")

diffs = [t['difficulty'] for t in data]
print(f"⚡ Trudności: 1={diffs.count(1)}, 2={diffs.count(2)}, 3={diffs.count(3)}")

terrains = [t['terrain_type'] for t in data]
terrain_counts = {}
for t in terrains:
    terrain_counts[t] = terrain_counts.get(t, 0) + 1

print(f"🏔️ Typy terenu:")
for terrain, count in terrain_counts.items():
    print(f"   {terrain}: {count}") 