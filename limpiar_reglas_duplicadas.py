"""
Script para limpiar reglas duplicadas en configs/reglas/global/personalizadas.json
Mantiene solo la primera regla de cada patrón similar
"""
import json
import os

ruta = 'configs/reglas/global/personalizadas.json'

with open(ruta, 'r', encoding='utf-8') as f:
    data = json.load(f)

reglas = data.get('reglas', [])
print(f"Reglas antes: {len(reglas)}")

# Mostrar todas las reglas
for i, r in enumerate(reglas):
    print(f"\n{i+1}. ID: {r.get('id')}")
    print(f"   Patron: {r.get('patron_detectado')}")
    print(f"   Regex: {r.get('regex_sugerido')}")
    print(f"   Tipo: {r.get('tipo', 'N/A')}")

print("\n¿Querés limpiar duplicados? (s/n): ", end='')
respuesta = input()

if respuesta.lower() == 's':
    # Mantener solo reglas con patrones únicos
    patrones_vistos = set()
    reglas_limpias = []
    
    for regla in reglas:
        patron = regla.get('patron_detectado', '').lower()[:30]  # Primeros 30 chars
        if patron not in patrones_vistos:
            patrones_vistos.add(patron)
            reglas_limpias.append(regla)
        else:
            print(f"⚠️ Eliminando duplicado: {regla.get('patron_detectado')}")
    
    data['reglas'] = reglas_limpias
    
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Reglas después: {len(reglas_limpias)}")
else:
    print("Cancelado.")
