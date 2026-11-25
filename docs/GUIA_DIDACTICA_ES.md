# Guía didáctica: laboratorio de FTP

**Nivel:** iniciación · **Duración estimada:** 60–90 min · **Requisitos:** Python 3.8+, un equipo Linux o Windows y permiso para usar la red local.

> El objetivo de esta guía es **entender el protocolo FTP**, no atacar sistemas. Todo se hace contra un servidor que tú controlas. FTP envía credenciales en texto plano: úsalo solo en tu laboratorio aislado.

## Objetivos de aprendizaje

Al terminar serás capaz de:

1. Explicar la diferencia entre el canal de control y el canal de datos de FTP.
2. Distinguir los modos **activo** (PORT) y **pasivo** (PASV) y entender por qué el pasivo funciona mejor detrás de NAT/firewall.
3. Usar un cliente FTP por línea de comandos para navegar, subir y descargar archivos.
4. Observar con `debug` el intercambio de comandos y respuestas (códigos `220`, `230`, `150`, `226`, `530`…).
5. Comparar FTP con FTPS y comprender por qué el cifrado importa.
6. Aplicar buenas prácticas: usuario dedicado, sin anónimo, contraseña propia, nada de exposición a Internet.

---

## Ejercicio 0 — Preparar el laboratorio

En el equipo que hará de **servidor**:

```bash
python3 -m pip install -r requirements-dev.txt
mkdir -p laboratorio_ftp
python3 lab_server.py --root ./laboratorio_ftp --user profe --password 'ClaveLab_123' --allow-write --port 2121
```

En Windows sustituye `python3` por `py`.

El servidor escucha en `127.0.0.1:2121`. Para conectarte **desde otro equipo de tu red**, usa `--allow-lan` y la IP local del servidor. Anota esa IP (`ip addr` en Linux, `ipconfig` en Windows).

**Pregunta:** ¿por qué el servidor, por defecto, solo escucha en `127.0.0.1`? *(Respuesta: para que no pueda acceder nadie más; `127.0.0.1` es el propio equipo.)*

---

## Ejercicio 1 — Primera conexión

Desde el equipo cliente:

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user profe --password 'ClaveLab_123'
```

Dentro del cliente prueba:

```
pwd
ls
status
help
```

Observa el prompt: muestra el directorio actual del servidor.

**Preguntas:**
- ¿Qué dice `status` sobre TLS? ¿Y sobre el modo pasivo?
- Si pones una contraseña incorrecta, ¿qué código de error aparece? (`530 Not logged in.`)

---

## Ejercicio 2 — Navegar y transferir

```
mkdir Ejercicio2
cd Ejercicio2
ls
put README.md copia.md
ls
get copia.md descargado.md
size copia.md
```

Ahora verifica en tu sistema de archivos que `descargado.md` existe y tiene el mismo tamaño.

**Reto:** crea un archivo local de texto con una sola línea, súbelo, cámbiale el nombre con `rename` y descárgalo otra vez.

**Concepto:** el modo `binary` envía los bytes tal cual; el modo `ascii` convierte finales de línea. Por eso las imágenes o archivos comprimidos **siempre** en binario. Nuestro cliente usa binario por defecto en `get`/`put`.

---

## Ejercicio 3 — Ver el protocolo por dentro

Conecta con depuración:

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user profe --password 'ClaveLab_123' --debug 1
```

o dentro de la sesión: `debug 1`. Luego haz `pwd`, `ls` y `quit`.

Verás líneas como:

```
> USER profe
< 331 Password required
> PASS ...
< 230 User logged in, proceed
> PWD
< 257 "/" is the current directory
```

Identifica estos códigos:

| Código | Significado |
|---|---|
| `220` | Servidor listo |
| `331` | Necesita contraseña |
| `230` | Login correcto |
| `257` | Ruta actual |
| `150` | Conexión de datos abierta |
| `226` | Transferencia completada |
| `530` | No autorizado |
| `550` | Archivo no encontrado o acción no permitida |

**Pregunta:** ¿en qué comandos aparece una conexión de datos nueva? *(En `LIST` y en `RETR`/`STOR`.)*

---

## Ejercicio 4 — Activo vs pasivo

1. Con el modo **pasivo** (por defecto) haz `ls`. Funciona.
2. Escribe `active` y vuelve a hacer `ls`.

El modo activo require que el cliente abra un puerto y que el servidor se conecte a él; un firewall o NAT suele bloquearlo. El modo pasivo es el que se usa habitualmente hoy.

**Pregunta:** ¿por qué el modo pasivo simplifica las cosas detrás de un router doméstico? *(Porque el cliente inicia las dos conexiones hacia el servidor.)*

---

## Ejercicio 5 — FTPS

Genera un certificado auto-firmado en el equipo servidor:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 30 -subj '/CN=localhost'
python3 lab_server.py --tls --cert cert.pem --key key.pem --port 2121 --allow-write
```

Conecta desde el cliente:

```bash
python3 ftp_lab.py --host 127.0.0.1 --user profe --password 'ClaveLab_123' --secure --no-verify-ssl --debug 1
```

Busca `AUTH TLS` y `PBSZ`/`PROT` en el volcado. Compara con el ejercicio 3: la contraseña ya no viaja en claro.

**Pregunta:** ¿por qué `--no-verify-ssl` es aceptable aquí pero no en producción? *(Porque el certificado es propio y auto-firmado; en producción habría que validar la cadena de confianza.)*

---

## Ejercicio 6 — Registro y análisis

```bash
python3 ftp_lab.py --host 127.0.0.1 --user profe --password 'ClaveLab_123' --log sesion.log --command pwd --command ls
cat sesion.log
```

El registro guarda **comandos y resultados**, nunca la contraseña. Úsalo para documentar tus prácticas.

---

## Ejercicio 7 — Endurecimiento (checklist)

Marca lo que aplica a tu servidor de prácticas:

- [ ] Usuario dedicado, no `anonymous`.
- [ ] Contraseña larga y propia del laboratorio.
- [ ] Raíz limitada a un directorio (`--root`).
- [ ] Solo lectura salvo que se necesite escritura (_quita_ `--allow-write`).
- [ ] Escucha en `127.0.0.1` salvo que haga falta LAN.
- [ ] FTPS (`--tls`) si vas a practicar cifrado.
- [ ] Nada de reenvío de puertos ni exposición a Internet.
- [ ] Para un servicio real, prefiere **SFTP** (SSH) sobre FTP.

---

## Reglas de oro

1. **Solo tu equipo o con permiso por escrito.**
2. No escanear ni probar credenciales en redes ajenas.
3. No guardar contraseñas reales en `profiles.ini`.
4. Apaga el servidor cuando termines (Ctrl+C).
5. Si algo sale mal, para y pregunta a tu profesor o mentor.

## Siguiente paso

Lee el apartado de espejo bidireccional en el [README](../README.md) y practica `git push` / `git pull` para ver cómo se sincronizan GitHub y GitLab.
