# Monitor de Transparencia · Datos Abiertos de la Municipalidad de Córdoba

Una herramienta ciudadana que vigila el portal de datos abiertos de la Municipalidad
de Córdoba: revisa qué tan actualizado está cada conjunto de datos, detecta páginas
caídas y links rotos, y deja que cualquier vecino reclame una actualización o pida
información que no está. Todo con evidencia fechada y pública.

**Qué hace, sin vueltas:**
- Una **página pública** donde la gente busca un tema y recibe el dato + su estado.
- Un **monitor que corre solo** todos los días y vuelve a medir el portal.
- Un **histórico fechado**: cada corrida queda guardada como prueba.
- **Reclamos y pedidos reales**: cada uno se vuelve un registro público en este repositorio.

No cuesta nada (todo gratis) y no necesita servidor propio.

---

## Cómo ponerlo en marcha (paso a paso, sin saber programar)

### 1. Crear la cuenta y el repositorio
1. Entrá a **github.com** y creá una cuenta (gratis).
2. Arriba a la derecha, **+ → New repository**.
3. Ponele un nombre (ej. `transparencia-cordoba`), marcá **Public**, y creá.

### 2. Subir los archivos
1. En el repositorio nuevo: **Add file → Upload files**.
2. Arrastrá **todo el contenido de esta carpeta** (el `index.html`, el `template.html`,
   la carpeta `scripts`, la carpeta `data` y la carpeta `.github`).
3. Abajo, **Commit changes**.

> Si la carpeta `.github` no aparece al arrastrar, subila aparte: es la que hace que el
> monitor corra solo.

### 3. Activar la página pública (GitHub Pages)
1. En el repositorio: **Settings → Pages**.
2. En *Source*, elegí **Deploy from a branch**, rama **main**, carpeta **/ (root)**.
3. Guardá. En un par de minutos tu página queda online en una dirección tipo
   `https://TU-USUARIO.github.io/transparencia-cordoba`.

### 4. Conectar los reclamos y pedidos (para que se guarden de verdad)
1. Abrí el archivo **`template.html`** (clic en él → ✏️ editar).
2. Buscá arriba la línea que dice `const REPO="";`
3. Poné entre las comillas **tu usuario y el nombre del repo**, así:
   `const REPO="tu-usuario/transparencia-cordoba";`
4. **Commit changes**.
5. Creá las dos etiquetas que usan los pedidos: **Issues → Labels → New label**,
   creá `reclamo` y `pedido-informacion`.

### 5. Encender el monitor
1. Andá a la pestaña **Actions**. Si pide habilitarlo, aceptá.
2. Elegí **Monitor de Transparencia → Run workflow**.
3. Esto hace la primera corrida real: trae los datos del día, **chequea también las
   descargas** (cosa que el prototipo no podía) y reconstruye la página con tu `REPO` ya
   conectado. De ahí en más corre solo **todos los días a las 8 de la mañana**.

¡Listo! Ya tenés la página pública, el monitor automático, el histórico y los pedidos.

---

## Cómo funciona por dentro (para cuando quieras tocar algo)

| Archivo | Qué es |
|---|---|
| `index.html` | La página pública. La **reconstruye el monitor** en cada corrida; no la edites a mano. |
| `template.html` | El molde de la página. Acá se edita el diseño, los textos y la línea `REPO`. |
| `scripts/monitor.py` | El monitor: lee el portal, mide todo y arma la página. |
| `.github/workflows/monitor.yml` | El reloj: dice cuándo corre el monitor (por defecto, diario 08:00). |
| `data/datos_tablero.json` | Los datos que muestra la página hoy. |
| `data/historial/` | Un archivo por día = la evidencia fechada. **Esto es el corazón legal del proyecto.** |

**Cambiar cada cuánto corre:** editá la línea `cron` en `monitor.yml`. `"0 11 * * *"` es
todos los días a las 11 UTC (08:00 en Córdoba).

**Ajustar qué se considera "vencido":** los umbrales por periodicidad están en
`scripts/monitor.py`, en `UMBRALES`. Quedan documentados junto a los datos.

---

## Para tener en cuenta (con honestidad)

- **Los reclamos y pedidos usan los Issues de GitHub.** Eso los hace públicos, fechados y
  auditables (ideal para transparencia), pero hoy **el vecino necesita una cuenta de
  GitHub** para enviarlos o apoyarlos. Es una barrera para el público general. Si más
  adelante querés que cualquiera participe sin cuenta, se le agrega un formulario
  (por ejemplo Google Forms o un servicio similar) que vuelque a este mismo registro.
- **Los apoyos a un pedido** son los 👍 que ese pedido recibe como Issue. Son reales: no
  hay números inventados.
- **Si una verificación no llega a un archivo** por un problema de red, el monitor lo marca
  como *no verificado*, nunca como *roto*. Acusar en falso es lo único que puede voltear la
  credibilidad de una herramienta de transparencia.
- **Sobre el acceso a la información pública:** los pedidos de la sección 2 se apoyan en el
  derecho de acceso a la información, que en Argentina y en la ciudad de Córdoba tiene
  respaldo normativo. Conviene confirmar el mecanismo formal exacto del municipio para
  encuadrarlos bien.

Fuente de los datos: portal de Gobierno Abierto de la Municipalidad de Córdoba.
