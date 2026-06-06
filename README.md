# Ataque DHCP Starvation

> **Estudiante:** Emmanuel Báez Ramírez
> **Matrícula:** 2022-0375
> **Video ilustrativo:** https://youtu.be/uSBldC9d_8k
> **Playlist (Práctica 1):** https://www.youtube.com/playlist?list=PLp7pfUFf22-zekAmQ7hncCvmJHZe7lLHk

---

# Objetivo del laboratorio.
Demostrar de forma controlada un ataque DHCP Starvation contra el servidor DHCP de la red, agotando por completo su pool de direcciones para impedir que los clientes legítimos obtengan IP, e implementar y verificar la contramedida que lo mitiga.

# Objetivo del script.
Agotar el pool de direcciones del servidor DHCP (R1) enviando una gran cantidad de mensajes DISCOVER, cada uno con una dirección MAC de origen falsa y aleatoria. El servidor interpreta cada DISCOVER como un cliente nuevo y le reserva una dirección, hasta que se queda sin direcciones disponibles. A partir de ese momento, ningún cliente legítimo puede obtener IP: es una Denegación de Servicio sobre el DHCP.

# Parámetros usados.
Comando de ejecución:

    sudo python3 ./dhcp_starvation.py -i eth1 -d 0.05

- `-i eth1` : interfaz de red del atacante.
- `-d 0.05` : retardo entre cada DISCOVER en segundos.
- `-c`      : número de DISCOVER a enviar (opcional, 0 = infinito).

Elementos internos del script:
- Generación de una MAC de origen aleatoria por cada paquete.
- Encapsulado `Ether / IP / UDP / BOOTP / DHCP` con `message-type = discover`.
- `xid` aleatorio por petición.
- `flags = 0x8000` (broadcast) para forzar la respuesta del servidor.

# Requisitos para utilizar la herramienta.
- Python3
- Scapy
- Permisos root
- Estar en la misma red por medio de LAN
- Un servidor DHCP activo en la red (R1) con un pool que agotar.

# Documentación del funcionamiento del script.
En un bucle, el script genera por cada iteración una dirección MAC aleatoria y construye un mensaje DHCP DISCOVER con esa MAC como origen y como identificador de cliente (`chaddr`). Los DISCOVER se envían en broadcast al servidor. Como cada uno aparenta provenir de un cliente distinto, el servidor reserva una dirección IP para cada MAC falsa, consumiendo su pool. El retardo (`-d`) controla la velocidad del ataque. El script imprime cada DISCOVER enviado con su MAC falsa, y corre hasta detenerse con Ctrl+C.

# Documentación de la Red.
Topología en VLAN 130 / 10.3.75.128/25.

| Dispositivo | Interfaz | VLAN | Dirección IP | Rol |
|-------------|----------|------|--------------|-----|
| R1 (c3725) | Fa0/0 | 130 | 10.3.75.129 | Gateway / Servidor DHCP |
| SW1 (vIOS-L2) | — | 130 | — | Switch de acceso |
| Kali (atacante) | eth1 -> Gi0/2 | 130 | 10.3.75.132 | Atacante |
| PC1 (VPCS) | -> Gi0/1 | 130 | 10.3.75.130 | Víctima |
| Rocky Linux (auxiliar) | ens160 -> Cloud1 (VMnet1) -> Gi1/0 | 130 | 10.3.75.131 (DHCP) | Máquina auxiliar (cliente legítimo de prueba) |

Imágenes usadas:
- `vios_l2-adventerprisek9-m.vmdk.SSA.152-4.0.55.E` (switch SW1)
- `c3725-adventerprisek9-mz.124-15.T14` (router R1)

El pool DHCP de R1 reparte el rango 10.3.75.130 - 10.3.75.254.

> **Nota:** la máquina auxiliar Rocky Linux se conecta a la topología a través de un nodo Cloud1 (adaptador VMware VMnet1) enlazado a Gi1/0 del switch. Se utiliza como cliente legítimo para evidenciar el impacto del ataque: al agotarse el pool, no logra obtener dirección IP.

# Capturas de pantalla.
- Topología (nombre y matrícula)

![Topologia](capturas/starv_topologia.png)

- Ejecución del ataque (DISCOVER con MACs falsas)

![Ejecucion](capturas/starv_ejecucion.png)

- Inundación de DISCOVER capturada en Wireshark

![Avalancha DISCOVER](capturas/starv_wireshark.png)

- Impacto: un cliente legítimo (Rocky) no puede obtener IP por pool agotado

![Rocky sin IP - pool agotado](capturas/starv_impacto_rocky.png)

![R1 base de datos bloqueada](capturas/starv_r1_locked.png)

# Documentación de contra-medidas.
La mitigación es Port Security, que limita cuántas direcciones MAC puede aprender el puerto del atacante. Como cada DISCOVER usa una MAC distinta, el switch detecta el exceso y bloquea el puerto. Se complementa con el rate-limit de DHCP Snooping.

    SW1# configure terminal
    SW1(config)# interface GigabitEthernet0/2
    SW1(config-if)# switchport port-security
    SW1(config-if)# switchport port-security maximum 2
    SW1(config-if)# switchport port-security violation shutdown
    SW1(config-if)# exit

Opcional, límite de tasa con DHCP Snooping:

    SW1(config)# ip dhcp snooping
    SW1(config)# ip dhcp snooping vlan 130
    SW1(config)# interface GigabitEthernet0/2
    SW1(config-if)# ip dhcp snooping limit rate 5

Verificación:

    SW1# show port-security interface GigabitEthernet0/2
    SW1# show interfaces status

Al intentar inundar con miles de MACs distintas, el puerto Gi0/2 entra en estado err-disabled (secure-shutdown): el atacante queda aislado y el pool del servidor permanece disponible para los clientes legítimos.

Otras buenas prácticas:
- DHCP Snooping para validar el origen de los mensajes DHCP.
- Monitoreo de la ocupación del pool del servidor DHCP.
