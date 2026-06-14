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

## Paso 4 — Configurar TikFinity

Crea 3 acciones **Comandos WebHook**, método **POST**, URL:

```
https://TU-APP.onrender.com/webhook
```

POST Body de cada una:

| Disparador                     | POST Body |
|--------------------------------|-----------|
| Mensaje de chat (elige Pokémon) | `{"event":"comment","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}","comment":"{comment}"}` |
| Regalo 🦦 Capibara (entrar)     | `{"event":"fight","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Cualquier OTRO regalo (ataque) | `{"event":"attack","username":"{username}","coins":{coins}}` |

**Cómo funciona el combate:**
- El comentario asigna el Pokémon (aleatorio si no escribió uno válido). La capibara mete al usuario a luchar o a la cola.
- Un regalo = ataque, y el daño = sus monedas (`{coins}`). **Solo cuentan los regalos de los 2 que están luchando** (el de arriba daña al de abajo y viceversa); los espectadores no hacen daño.
- Cada personaje empieza en **Nv1 con 100 HP**. Al ganar sube de nivel y gana **+50 HP** máx.
- Si un luchador deja de atacar, su personaje pierde vida: **10s → −10%, 30s → −50%, 60s → −100%** (se debilita). Con un solo luchador esto no ocurre.

> ⚠️ Importante: en el webhook de **ataque**, configura el disparador para **excluir la capibara** (si no, la capibara contaría también como ataque). Lo más limpio: usa la capibara solo para "entrar" y el resto de regalos para atacar.
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
