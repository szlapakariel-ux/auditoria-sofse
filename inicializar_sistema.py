from gestor_tandas import GestorTandas
import os

def inicializar():
    print("="*60)
    print("INICIALIZACION DEL SISTEMA")
    print("="*60)
    gestor = GestorTandas()
    archivo = 'lote_revision_historico.json'
    if not os.path.exists(archivo):
        print("\nERROR: No se encontro el archivo")
        return
    print("\nImportando mensajes...")
    try:
        gestor.importar_desde_validador(archivo)
        total = len(gestor.mensajes)
        pendientes = len([m for m in gestor.mensajes if m['estado'] == 'PENDIENTE'])
        print(f"\nTotal: {total}")
        print(f"Pendientes: {pendientes}")
        print("\nPOR LINEA:")
        for linea, cant in gestor.contar_pendientes_por_linea().items():
            print(f"  {linea}: {cant}")
        print("\nSistema listo!")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == '__main__':
    inicializar()
