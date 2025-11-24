"""
Script de prueba para el cliente GoAnywhere
"""
from modules.consolidador_t25.goanywhere import GoAnywhereWebClient
import getpass

def test_conexion():
    print("="*70)
    print("PRUEBA DE CONEXIÓN GOANYWHERE")
    print("="*70)
    
    # Crear cliente
    cliente = GoAnywhereWebClient()
    
    print(f"\n📡 Servidor: {cliente.host}")
    print(f"🔌 Puerto: {cliente.port}")
    print(f"👤 Usuario: {cliente.username}")
    
    # Solicitar contraseña
    password = getpass.getpass("\n🔑 Ingresa la contraseña: ")
    
    print("\n⏳ Conectando...")
    resultado = cliente.connect(password)
    
    if resultado['success']:
        print(f"✅ {resultado['mensaje']}")
        print(f"📁 Directorio actual: {resultado['directorio_actual']}")
        
        # Probar listar directorio
        print("\n📋 Listando archivos del directorio actual...")
        listado = cliente.list_directory()
        
        if listado['success']:
            print(f"✅ Total de items: {listado['total_items']}")
            print("\nPrimeros 10 items:")
            print("-" * 70)
            
            for i, item in enumerate(listado['items'][:10], 1):
                icono = "📁" if item['es_directorio'] else "📄"
                print(f"{i}. {icono} {item['nombre']}")
                print(f"   Tamaño: {item['tamano']:,} bytes | Modificado: {item['fecha_modificacion']}")
            
            print("-" * 70)
        else:
            print(f"❌ Error al listar: {listado['error']}")
        
        # Desconectar
        print("\n🔌 Desconectando...")
        cliente.disconnect()
        print("✅ Desconectado")
        
    else:
        print(f"❌ Error de conexión: {resultado['error']}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_conexion()