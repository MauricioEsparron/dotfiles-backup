# Solución: Error "Session 103" de Spotify en CachyOS/Arch (Flatpak)

## Síntomas

- Al intentar iniciar sesión en Spotify Desktop, aparece la pantalla de error genérica: *"Algo salió mal / Se produjo un error al iniciar sesión"*.
- Por debajo aparece un aviso rojo: *"A firewall may be blocking Spotify... (Error code: session:103)"*.
- El código QR para login desde el celular **no carga**.
- Desactivar el firewall completamente **no soluciona nada**.
- El mensaje de error es engañoso: a pesar de mencionar firewall/proxy, en este caso **no tiene que ver con ninguno de los dos**.

## Entorno donde ocurrió

- CachyOS (basado en Arch)
- Spotify instalado vía **Flatpak** (`flathub com.spotify.Client`), no AUR ni paquete nativo
- NetworkManager con conexión cableada

## Proceso de descarte (por si a alguien le sirve el camino, no solo el resultado)

Se descartaron, en este orden, sin que ninguno resolviera el problema:

1. **Firewall (UFW)** — probado con reglas específicas para loopback y también completamente desactivado. Sin cambios.
2. **IPv6 sin conectividad real** — el sistema resolvía el dominio de Spotify solo a una IP IPv6, pero el ISP no soportaba IPv6 (`ping -6` daba "red inaccesible"). Se deshabilitó IPv6 en la conexión de red (`nmcli connection modify <conexión> ipv6.method disabled`). Ayudó a eliminar una causa potencial, pero no resolvió el error por sí solo.
3. **Variables de entorno de proxy** (`env | grep -i proxy`) — no había ninguna configurada.
4. **Permisos del sandbox de Flatpak** (`flatpak info --show-permissions com.spotify.Client`) — ya tenía `shared=network` activo, no era un tema de sandboxing de red.
5. **Actualizar el Flatpak** (`flatpak update com.spotify.Client`) — ya estaba en la última versión disponible.

## Lo que finalmente funcionó: reinstalación limpia del Flatpak

El problema eran datos de configuración/caché corruptos dentro del sandbox de Flatpak (`~/.var/app/com.spotify.Client/`), probablemente de una sesión o token de autenticación previo dañado.

```bash
# 1. Desinstalar el Flatpak
flatpak uninstall com.spotify.Client

# 2. Borrar TODOS los datos residuales (config, caché, data)
rm -rf ~/.var/app/com.spotify.Client

# 3. Reinstalar desde cero
flatpak install flathub com.spotify.Client

# 4. Ejecutar
flatpak run com.spotify.Client
```

Después de esto, el login (tanto por navegador como por QR) funcionó sin problema.

## Notas adicionales

- Existe al menos un [hilo oficial sin resolver en la comunidad de Spotify](https://community.spotify.com/t5/Desktop-Windows/Can-t-solve-the-error-session-103/td-p/7406353) con el mismo código de error, lo que sugiere que puede tener más de una causa raíz (no solo datos corruptos locales). Si el reset de Flatpak no funciona en tu caso, probablemente sea un problema del lado de Spotify y no de tu configuración.
- Si tampoco tienes IPv6 funcional con tu ISP, vale la pena descartar eso primero — es un problema común en redes residenciales que puede causar fallos de conexión silenciosos en varias apps, no solo Spotify.

## Resumen rápido (TL;DR)

Si te aparece el error `session:103` en Spotify Flatpak y el firewall NO es el problema:

```bash
flatpak uninstall com.spotify.Client
rm -rf ~/.var/app/com.spotify.Client
flatpak install flathub com.spotify.Client
```
