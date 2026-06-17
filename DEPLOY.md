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
| Regalo sombrero con bigote (150 carga) | `{"event":"potion","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo galaxia (500 carga) | `{"event":"level_galaxy","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |

Opcional, si quieres mantener un webhook genérico para otros regalos:

| Disparador                     | POST Body |
|--------------------------------|-----------|
| Cualquier otro regalo con monedas | `{"event":"attack","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}","coins":{coins}}` |

**Cómo funciona el combate:**
- El comentario asigna el Pokémon. Cualquier regalo puede meter al usuario a luchar o a la cola si antes escribió un Pokémon válido. Si ese usuario ya está luchando y está en su fase activa, el regalo suma carga.
- El servidor filtra los eventos de chat: solo reenvía al overlay comentarios que parezcan un Pokémon válido, incluyendo errores leves como `picachu` por `Pikachu`.
- Cuando hay 2 luchadores empieza uno al azar con **Carga tu ataque**. Durante `15` segundos visibles + `5` ocultos acumula regalos como poder de ataque.
- Después el rival entra en **Carga tu defensa** y debe acumular al menos ese objetivo (`0/30`, `0/100`, etc.). Si llega al objetivo, esquiva la onda y pasa a cargar su ataque. Si no llega, recibe como daño la diferencia entre ataque y defensa.
- Rosquilla vale `30`, Super GG vale `100`, Manifestando/Rayo vale `500`, sombrero con bigote vale `150`, galaxia vale `500`, pistola de dinero vale `500`. El webhook genérico `event:"attack"` usa `{coins}` como puntos de carga.
- La pistola de dinero tiene su propio disparador/webhook (`event:"money_gun"`). Pone al usuario primero en la cola si no está luchando. Si ese usuario ya está luchando, suma `500` de carga en su fase activa.
- En el panel del overlay hay un interruptor para permitir que cualquier regalo normal meta al usuario en batalla/cola si ya eligió Pokémon. Está activado por defecto; si lo apagas, solo entra con capibara.
- La vida vuelve a mostrarse como `HP actual / HP máximo`. Nv1 = `10 HP`, Nv2 = `20 HP`, Nv3 = `40 HP`, Nv4 = `50 HP`; desde Nv5 sube de `50` en `50`.
- Si ves que al llegar a `0` tarda unos segundos en cambiar, es el margen oculto de `5` segundos para contar regalos que lleguen con retraso.
- Si alguien no carga ningún ataque en su fase de ataque, pierde la mitad de su vida. Si le pasa dos turnos de ataque seguidos, se debilita.
- Cuando empieza el combate, suena en bucle `assets/battle-music.mp3` como música de fondo a volumen bajo.
- Puedes debilitar manualmente al luchador de arriba o abajo desde el panel de control del overlay.
- **TEAM ROCKET** ya no aparece solo. Puedes sacarlo manualmente desde el panel: entra si hay hueco libre, o se pone en cola si los dos huecos están ocupados. Juega dentro del sistema de turnos como un rival NPC.

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
