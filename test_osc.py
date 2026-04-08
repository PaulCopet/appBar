from pythonosc import udp_client
import time

def test_vdj_osc():
    # Creamos un cliente apuntando al puerto
    client = udp_client.SimpleUDPClient("127.0.0.1", 8001)
    
    # Algunos comandos VDJ esperan un '1' o 1.0 (float) simulando 
    # que un boton fue presionado (valor maximo de boton MIDI/OSC)
    
    print(">> Enviando comandos OSC a VirtualDJ...")
    client.send_message("/vdj/deck/1/play", 1.0)
    
    time.sleep(1)
    
    # Enviamos una query simple al action 'play' para ver si al menos no crashea
    client.send_message("/vdj/deck/1/play", 1)
    print(">> [OK] Paquetes disparados.")

if __name__ == "__main__":
    test_vdj_osc()
