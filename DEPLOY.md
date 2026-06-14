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
| Cualquier OTRO regalo (ataque) | `{"event":"attack","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}","coins":{coins}}` |
| Regalo pistola de dinero | `{"event":"money_gun","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo gafas de sol (poción) | `{"event":"potion","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |
| Regalo galaxia (CARAMELORARO) | `{"event":"rare_candy","username":"{username}","nickname":"{nickname}","imgprofile":"{imgprofile}"}` |

**Cómo funciona el combate:**
- El comentario asigna el Pokémon. La capibara mete al usuario a luchar o a la cola si antes escribió un Pokémon válido. Si ese usuario ya está luchando, la capibara hace 30 de daño al rival.
- Un regalo = ataque, y el daño = sus monedas (`{coins}`). **Solo cuentan los regalos de los 2 que están luchando** (el de arriba daña al de abajo y viceversa); los espectadores no hacen daño.
- La pistola de dinero tiene su propio disparador/webhook (`event:"money_gun"`). Pone al usuario primero en la cola si no está luchando. Si ese usuario ya está luchando, hace `500` de daño al rival.
- Las gafas de sol tienen su propio disparador/webhook (`event:"potion"`). Solo funcionan si el usuario está luchando y curan el 50% de la vida máxima de su Pokémon; no hacen daño al rival.
- La galaxia tiene su propio disparador/webhook (`event:"rare_candy"`). Al empezar cada combate aparece un contador de 20 segundos para usar CARAMELORARO; si el luchador lo usa en ese tiempo, sube 10 niveles y gana la vida máxima correspondiente. Fuera de ese contador no tiene efecto.
- Cada personaje empieza en **Nv1 con 100 HP**. Al ganar sube de nivel y gana **+50 HP** máx.
- Los luchadores ya no pierden vida por inactividad. Puedes debilitar manualmente al luchador de arriba o abajo desde el panel de control del overlay.
- Si durante 60 segundos solo hay un luchador humano y nadie entra a retarle, aparece **TEAM ROCKET** en el hueco libre con el mismo nivel. Ataca a los 15s, 30s y 60s quitando el 10%, 50% y 100% de la vida máxima del rival.

> ⚠️ Importante: en el webhook de **ataque**, configura el disparador para **excluir la capibara**. La capibara ya se gestiona con el webhook `fight`: entra/cola si el usuario no está luchando, y hace 30 de daño si ya está luchando.
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
