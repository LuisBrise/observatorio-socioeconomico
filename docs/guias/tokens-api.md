# Tokens de API (INEGI y Banxico)

## ¿Son información delicada?

**Moderadamente.** Son gratuitos, solo dan acceso de lectura a datos públicos y no tienen
relación con dinero. Pero están ligados a tu correo: si alguien los obtiene, puede agotar tu
cuota de consultas o hacer que el proveedor los revoque. Trátalos como contraseñas de bajo riesgo:

- **Nunca** los subas al repositorio (el archivo `.env` está en `.gitignore`).
- **Nunca** los pegues en chats, issues, PR ni capturas de pantalla.
- Si se filtran, genera uno nuevo; el anterior deja de importar.

## Cómo obtenerlos

| Proveedor | Dónde | Cómo |
|---|---|---|
| **INEGI** (API del Banco de Indicadores) | <https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify> | Escribe tu correo, acepta los términos y recibirás el token por correo. |
| **Banxico** (API del SIE) | <https://www.banxico.org.mx/SieAPIRest/service/v1/token> | Llena el formulario (correo y aceptación de términos); el token aparece en pantalla. Cópialo de inmediato. |

## Dónde guardarlos (en tres lugares, según dónde corra el sistema)

1. **En tu computadora (Ubuntu).** Copia `.env.example` a `.env` en la raíz del repositorio y
   llena los valores:

   ```bash
   cp .env.example .env
   nano .env        # INEGI_TOKEN=...  BANXICO_TOKEN=...
   chmod 600 .env   # solo tu usuario puede leerlo
   ```

2. **En GitHub Actions** (actualizaciones automáticas): en el repositorio,
   *Settings → Secrets and variables → Actions → New repository secret*, con los nombres
   `INEGI_TOKEN` y `BANXICO_TOKEN`. Los flujos de trabajo ya los leen con esos nombres.

3. **En las sesiones en la nube de Claude Code**: en la configuración del entorno (menú del
   entorno en la barra de título de la sesión → *Edit*), como variables de entorno con los mismos
   nombres. Una sesión nueva las toma automáticamente.

El código solo lee los tokens desde variables de entorno; el manifiesto de cada descarga
registra `env:INEGI_TOKEN` (el *nombre* de la variable), nunca el valor.
