# Guía didáctica: llaboratoriu de FTP

**Nivel:** principiante · **Duración envalorada:** 60–90 min · **Requisitos:** Python 3.8+, un equipu Linux o Windows y permisu pa usar la to red llocal.

> L'oxetivu d'esta guía ye **entender el protocolu FTP**, non atacar sistemes. Too se fai contra un servidor que tu controles. El FTP clásicu unvia l'usuariu y la contraseña en testu planu: usa la guía solo nel to llaboratoriu.

## Oxetivos d'aprendizaxe

Al rematar vas ser capaz de:

1. Esplicar la diferencia ente'l **canal de control** y el **canal de datos** de FTP.
2. Estremar los modos **activu** (PORT) y **pasivu** (PASV) y entender por qué'l pasivu funciona meyor detrás de NAT/firewall.
3. Usar un veceru FTP de llinia de comandos pa navegar, xubir y baxar archivos.
4. Ver con `debug` l'intercambiu de comandos y respuestes (códigos `220`, `230`, `150`, `226`, `530`...).
5. Comparar FTP con FTPS y comprender por qué importa'l cifráu.
6. Aplicar bones práutiques: usuariu dedicáu, ensin anónimu, contraseña propia, nada d'esposición a Internet.

---

## Exerciciu 0 — Preparar el llaboratoriu

Nel equipu que va facer de **servidor**:

```bash
python3 -m pip install -r requirements-dev.txt
mkdir -p llaboratorio_ftp
python3 lab_server.py --root ./llaboratorio_ftp --user profe --password 'ClaveLab_123' --allow-write --port 2121
```

En Windows sustitúi `python3` por `py`.

El servidor escucha en `127.0.0.1:2121`. Pa conectate **dende otru equipu de la to red llocal**, usa `--allow-lan` y anota la IP llocal del servidor (`ip addr` en Linux, `ipconfig` en Windows).

**Pregunta:** ¿por qué'l servidor escucha por defectu solo en `127.0.0.1`? *(Respuesta: pa que naide más pueda acceder; `127.0.0.1` ye'l propiu equipu.)*

---

## Exerciciu 1 — Primer conexión

Dende l'equipu **veceru**:

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user profe --password 'ClaveLab_123'
```

Dientro del veceru prueba:

```
pwd
ls
status
help
```

El *prompt* amuesa'l direutoriu actual del servidor.

**Preguntes:**
- ¿Qué diz `status` sobre TLS? ¿Y sobre'l modo pasivu?
- Si pones una contraseña incorreuta, ¿qué códigu d'error apaez? (`530 Not logged in.`)

---

## Exerciciu 2 — Navegar y tresferir

```
mkdir Exerciciu2
cd Exerciciu2
ls
put README.md copia.md
ls
get copia.md baxao.md
size copia.md
```

Comprueba nel to sistema de ficheros que `baxao.md` esiste y tien el mesmu tamañu.

**Retu:** crea un archivu local de testu con una sola llinia, xúbelo, camúdalu'l nome con `rename` y báxalo otra vegada.

**Conceptu:** el modo `binary` unvia los bytes tal cual; el modo `ascii` convierte los finales de llinia. Por eso les imáxenes o los archivos comprimíos **siempres** en binariu. El nuesu veceru usa binariu por defectu en `get`/`put`.

---

## Exerciciu 3 — Ver el protocolu per dientro

Conecta con depuración:

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user profe --password 'ClaveLab_123' --debug 1
```

O escribe `debug 1` dientro de la sesión y dempués `pwd`, `ls` y `quit`.

Verás llinies como:

```
> USER profe
< 331 Password required
> PASS ...
< 230 User logged in, proceed
> PWD
< 257 "/" is the current directory
```

Identifica estos códigos:

| Códigu | Significáu |
|---|---|
| `220` | Servidor llistu |
| `331` | Ríquese contraseña |
| `230` | Entrada correuta |
| `257` | Ruta actual |
| `150` | Conexión de datos abierta |
| `226` | Tresferencia rematada |
| `530` | Non autorizáu |
| `550` | Archivu non topáu o aición non permitida |

**Pregunta:** ¿en qué comandos s'abre una conexión de datos nueva? *(En `LIST` y en `RETR`/`STOR`.)*

---

## Exerciciu 4 — Actvu vs pasivu

1. En modo **pasivu** (por defectu) fai `ls`. Funciona.
2. Escribe `active` y fai `ls` otra vegada.

El modo activu rique que'l veceru abra un puertu y que'l servidor se conecte a él; un firewall o NAT suel bloquialo. El modo pasivu ye'l que s'usa davezu güei.

**Pregunta:** ¿por qué'l modo pasivu simplifica les coses detrás d'un router domésticu? *(Porque'l veceru entama les dos conexiones escontra'l servidor.)*

---

## Exerciciu 5 — FTPS

Xenera un certificáu auto-firmáu nel equipu servidor:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 30 -subj '/CN=localhost'
python3 lab_server.py --tls --cert cert.pem --key key.pem --port 2121 --allow-write
```

Conecta dende'l veceru:

```bash
python3 ftp_lab.py --host 127.0.0.1 --user profe --password 'ClaveLab_123' --secure --no-verify-ssl --debug 1
```

Busca `AUTH TLS` y `PBSZ`/`PROT` nel volcáu. Compara col exerciciu 3: la contraseña yá non viaxa en claru.

**Pregunta:** ¿por qué `--no-verify-ssl` ye aceutable equí pero non en producción? *(Porque'l certificáu ye nuesu y auto-firmáu; en producción hai que validar la cadena de confianza.)*

---

## Exerciciu 6 — Rexistru y análisis

```bash
python3 ftp_lab.py --host 127.0.0.1 --user profe --password 'ClaveLab_123' --log sesion.log --command pwd --command ls
cat sesion.log
```

El rexistru guarda **comandos y resultaos**, nunca la contraseña. Úsalu pa documentar les tos práutiques.

---

## Exerciciu 7 — Endurecimientu (checklist)

- [ ] Usuariu dedicáu, non `anonymous`.
- [ ] Contraseña llarga y propia del llaboratoriu.
- [ ] Raíz llindada a un direutoriu (`--root`).
- [ ] Solo llectura sacantes que se precise escritura (quita `--allow-write`).
- [ ] Escucha en `127.0.0.1` sacantes que faga falta LAN.
- [ ] FTPS (`--tls`) si vas prauticar cifráu.
- [ ] Nada de reenvíu de puertos nin esposición a Internet.
- [ ] Pa un serviciu real, prefiere **SFTP** (SSH) sobre FTP.

---

## Regles d'oru

1. **Solo'l to equipu o con permisu espreso.**
2. Non escanear nin probar credenciales en redes ayenes.
3. Non guardar contraseñes reales en `profiles.ini`.
4. Apaga'l servidor cuando termines (Ctrl+C).
5. Si daqué sale mal, para y pregunta al to profesor o mentor.

## Pasu siguiente

Llei l'apartáu d'espeyu bidireccional nel [README](../README.md) y prautica `git push` / `git pull` pa ver cómo se sincronizen GitHub y GitLab.
