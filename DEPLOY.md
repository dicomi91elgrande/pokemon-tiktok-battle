# Desplegar el overlay en Render (URL pública gratis)

TikTok Studio no acepta `localhost` como fuente, así que subimos el servidor a
Render para tener una URL pública fija tipo `https://tu-app.onrender.com`.

> ⚠️ **Plan gratuito:** el servicio "duerme" tras 15 min sin tráfico. La primera
> carga tras dormir tarda **~30-60s** en despertar. Abre el overlay **un minuto
> antes** de empezar el directo para que ya esté despierto.

---

## Paso 1 — Subir esta carpeta a GitHub

Necesitas una cuenta en GitHub. Desde esta carpeta (`pokemon-tiktok-battle`):

```bash
git init
git add .
git commit -m "Pokemon TikTok Battle"
git branch -M main
# crea un repo vacío en github.com y copia su URL:
git remote add origin https://github.com/TU_USUARIO/pokemon-tiktok-battle.git
git push -u origin main
```

## Paso 2 — Crear el servicio en Render

1. Entra en https://render.com y regístrate (puedes usar tu cuenta de GitHub).
2. **New +** → **Web Service**.
3. Conecta tu repositorio `pokemon-tiktok-battle`.
4. Configura:
   - **Language / Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python server.py`
   - **Instance Type:** **Free**
5. **Create Web Service** y espera a que ponga *"Live"*. Te dará una URL como
   `https://pokemon-tiktok-battle.onrender.com`.

> Alternativa en 1 clic: **New + → Blueprint** y selecciona el repo (usa el
> `render.yaml` incluido).

## Paso 3 — Configurar OBS / TikTok Studio

Añade una fuente de **Navegador** con esta URL (el `?obs=1` oculta el panel):

```
https://TU-APP.onrender.com/?obs=1
```

Tamaño recomendado: 720 x 480 (o escálalo). Marca fondo transparente si la fuente
lo permite.

## Paso 4 — Configurar TikFinity / Interactive

Crea estas acciones **Comandos WebHook**, método **POST**, todas con esta URL:

```
https://TU-APP.onrender.com/webhook
```

POST Body de cada una:

| Disparador                     | POST Body |
|--------------------------------|-----------|
| Mensaje de chat (elige Pokémon) | `{"event":"comment","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}","comment":"{comment}"}` |
| Regalo 🦦 Capibara (entrar)     | `{"event":"fight","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo 🍩 Rosquilla (ataque simple) | `{"event":"attack_simple","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo 🏆 Super GG (ataque intermedio) | `{"event":"attack_mid","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo 🔮 Manifestando (ataque potente) | `{"event":"attack_strong","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo pistola de dinero | `{"event":"money_gun","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo sombrero con bigote (poción +150 HP) | `{"event":"potion","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo galaxia (+5 niveles) | `{"event":"level_galaxy","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |

Opcional, si quieres mantener un webhook genérico para otros regalos:

| Disparador                     | POST Body |
|--------------------------------|-----------|
| Cualquier otro regalo con monedas | `{"event":"attack","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}","coins":{coins}}` |

**Cómo funciona el combate:**
- El comentario asigna el Pokémon. La capibara mete al usuario a luchar o a la cola si antes escribió un Pokémon válido. Si ese usuario ya está luchando, la capibara hace 30 de daño al rival.
- El servidor filtra los eventos de chat: solo reenvía al overlay comentarios que parezcan un Pokémon válido, incluyendo errores leves como `picachu` por `Pikachu`.
- Cuando hay 2 luchadores empieza una **puja de 20 segundos**. Durante esa puja, los regalos de ataque deciden quién empieza: Rosquilla vale `1`, Super GG vale `50`, Manifestando vale `200` y pistola de dinero vale `500`.
- Después de la puja, el combate va por **turnos de 30 segundos**. Solo puede atacar el jugador cuyo turno está activo. Si no ataca a tiempo una vez, pierde el `30%` de su vida máxima y pasa el turno; si vuelve a perder su siguiente turno seguido, se debilita.
- Los ataques específicos hacen daño aleatorio: Rosquilla `10-20`, Super GG `20-100`, Manifestando `100-300`.
- Cada nivel por encima de Nv1 aumenta el daño final del ataque un `20%`.
- El webhook genérico `event:"attack"` usa `{coins}` como daño/puja, pero es opcional si ya usas los 3 ataques específicos.
- La pistola de dinero tiene su propio disparador/webhook (`event:"money_gun"`). Pone al usuario primero en la cola si no está luchando. Si ese usuario ya está luchando, cuenta como puja/ataque de `500`.
- El sombrero con bigote (`event:"potion"`) solo funciona en el turno del luchador y cura `150 HP`; al usarlo pasa el turno.
- La galaxia (`event:"level_galaxy"`) solo funciona en el turno del luchador, sube `5` niveles, aumenta la vida máxima correspondiente y restaura toda la vida; al usarla pasa el turno.
- En el panel del overlay hay un interruptor para permitir que cualquier regalo normal meta al usuario en batalla/cola si ya eligió Pokémon. Si está apagado, solo entra con capibara.
- Cada personaje empieza en **Nv1 con 100 HP**. Al ganar sube de nivel, gana **+50 HP** máx. y vuelve a curarse al **100%**.
- Cuando empieza la puja/combate, suena en bucle `assets/battle-music.mp3` como música de fondo a volumen bajo.
- Puedes debilitar manualmente al luchador de arriba o abajo desde el panel de control del overlay.
- Si durante 60 segundos solo hay un luchador humano y nadie entra a retarle, aparece **TEAM ROCKET** en el hueco libre con el mismo nivel. Ahora juega dentro del sistema de turnos como un rival NPC.

> ⚠️ Importante: si usas también el webhook genérico `event:"attack"`, configura ese disparador para **excluir** capibara, pistola de dinero, sombrero con bigote, galaxia, rosquilla, Super GG y Manifestando. Cada uno de esos regalos ya tiene su propio webhook.
> Nota: `{coins}` va **sin comillas** (es un número).

## Paso 5 (opcional) — Proteger el webhook con un token

Para que nadie que descubra tu URL pueda enviar eventos falsos:

1. En Render → tu servicio → **Environment** → añade `HOOK_TOKEN` = un secreto largo.
2. En TikFinity, cambia la URL del webhook a:
   `https://TU-APP.onrender.com/webhook?token=TU_SECRETO`

Si no defines `HOOK_TOKEN`, el webhook funciona sin token (más simple para empezar).

---

## Probar en local (sin Render)

```bash
python server.py
```

Abre `http://localhost:3000/` (con panel simulador) o `http://localhost:3000/?obs=1`
(overlay limpio). El panel de la derecha simula los eventos de TikFinity.
