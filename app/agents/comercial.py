import logging
from openai import OpenAI
from app.models.lead import Lead
from app.models.tenant import db
from app.models.service import Service
from app.models.appointment import Appointment

# Sensores de la NASA para la terminal
logger = logging.getLogger("NASA_CONTROL")

class AgenteComercial:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        logger.info("🚀 [SISTEMA]: Angela ha despertado con superpoderes matemáticos.")

    def ejecutar_loop(self, mensaje_usuario, tenant_id):
        print("\n" + "🛰️" + "—"*40)
        logger.info("📡 [INICIO DE MISIÓN]: Nuevo mensaje comercial detectado.")

        # --- PASO 1: OBSERVAR (Hecho) ---

        # --- PASO 2: INTERPRETAR (Angela extrae datos, ahora incluyendo INVITADOS) ---
        logger.info("🧠 [PASO 2 - INTERPRETAR]: Angela traduce la intención y busca números...")
        reporte_ia = self.interpretar_intencion(mensaje_usuario)
        logger.info(f"📊 [DATOS EXTRAÍDOS]:\n{reporte_ia}")

        # Limpiamos los datos para que el sistema los pueda usar
        datos = self.limpiar_reporte(reporte_ia)
        
        # --- PASO 3: RAZONAR (El Sistema busca precios y hace cuentas) ---
        logger.info(f"⚖️  [PASO 3 - RAZONAR]: Buscando precio para '{datos['evento']}'...")
        
        precio_unidad = self.consultar_precios(tenant_id, datos['evento'])
        valor_total = 0
        
        if precio_unidad and datos['invitados'] > 0:
            valor_total = precio_unidad * datos['invitados']
            logger.info(f"💰 [SISTEMA]: CUENTA: {datos['invitados']} pers x ${precio_unidad} = ${valor_total}")

        # --- PASO 4: PLANIFICAR (Decidir qué orden darle a Angela) ---
        if valor_total > 0:
            instruccion_del_sistema = f"Confirma que el presupuesto estimado para {datos['invitados']} personas es de ${valor_total}. Invítalo a agendar una visita."
        elif datos['nombre'] != "Desconocido" and datos['evento'] == "Desconocido":
            instruccion_del_sistema = f"Saluda a {datos['nombre']} y pregunta qué tipo de evento busca y para cuántas personas."
        else:
            instruccion_del_sistema = self.obtener_regla_negocio(reporte_ia)
        
        # --- PASO 4.5: GUARDAR O ACTUALIZAR LEAD (Guardamos el DINERO) ---
        if datos['nombre'] != "Desconocido":
            self.guardar_lead_en_db(datos, tenant_id, valor_total)

        # --- PASO 4.6: GUARDAR CITA (Si detectó fecha) ---
        if datos['fecha'] != "Desconocido" and datos['hora'] != "Desconocido":
            self.guardar_cita_en_db(reporte_ia, tenant_id)
            instruccion_del_sistema = f"Confirma que la cita quedó lista para el {datos['fecha']} a las {datos['hora']}."

        logger.info(f"📝 [PASO 4]: Orden final -> {instruccion_del_sistema}")

        # --- PASO 5: EJECUTAR ---
        logger.info("🗣️  [PASO 5 - EJECUTAR]: Angela redacta la respuesta final...")
        respuesta_final = self.redactar_respuesta(mensaje_usuario, instruccion_del_sistema)

        # --- PASO 6: VERIFICAR ---
        logger.info("✅ [PASO 6 - VERIFICAR]: Misión cumplida con éxito.")
        print("🛰️" + "—"*40 + "\n")
        
        return respuesta_final

    def interpretar_intencion(self, texto):
        prompt = f"""
        Analiza el siguiente mensaje y responde ÚNICAMENTE en este formato:
        INTENCION: [SALUDO, COTIZACION, AGENDAMIENTO, o PREGUNTA]
        NOMBRE: [Nombre detectado o 'Desconocido']
        EVENTO: [Tipo de evento o 'Desconocido']
        INVITADOS: [Número de personas o 0]
        FECHA: [Fecha en formato AAAA-MM-DD o 'Desconocido']
        HORA: [Hora en formato HH:MM o 'Desconocido']
        
        Mensaje: '{texto}'
        """
        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return respuesta.choices[0].message.content

    def limpiar_reporte(self, reporte):
        # Esta función convierte el texto de Angela en una tablita limpia para el sistema
        res = {"nombre": "Desconocido", "evento": "Desconocido", "invitados": 0, "fecha": "Desconocido", "hora": "Desconocido"}
        lineas = reporte.split("\n")
        for l in lineas:
            if "NOMBRE:" in l: res["nombre"] = l.replace("NOMBRE:", "").strip()
            if "EVENTO:" in l: res["evento"] = l.replace("EVENTO:", "").strip()
            if "INVITADOS:" in l: 
                try: res["invitados"] = int(''.join(filter(str.isdigit, l)))
                except: res["invitados"] = 0
            if "FECHA:" in l: res["fecha"] = l.replace("FECHA:", "").strip()
            if "HORA:" in l: res["hora"] = l.replace("HORA:", "").strip()
        return res

    def obtener_regla_negocio(self, intencion):
        if "COTIZACION" in intencion.upper():
            return "Dile que somos expertos en eventos premium y pídele el tipo de evento y número de invitados."
        if "AGENDAMIENTO" in intencion.upper():
            return "Dile que te encantaría recibirlo, y pídele que te diga qué día y a qué hora le gustaría venir."
        return "Saluda amablemente, di que eres Angela y pregunta en qué puedes ayudar."

    def redactar_respuesta(self, mensaje_u, orden):
        prompt_final = f"Eres Angela, asistente de Pasto.AI. SIGUE ESTA ORDEN DEL JEFE: {orden}"
        envio = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt_final}, {"role": "user", "content": mensaje_u}]
        )
        return envio.choices[0].message.content
    
    def guardar_lead_en_db(self, datos, tenant_id, valor):
        try:
            nombre = datos["nombre"]
            # Buscamos si el cliente ya existe para actualizarlo en lugar de crear uno nuevo
            prospecto = Lead.query.filter_by(tenant_id=tenant_id, nombre=nombre).first()
            
            if not prospecto:
                prospecto = Lead(tenant_id=tenant_id, nombre=nombre)
                db.session.add(prospecto)
            
            # Actualizamos sus bolsillos con la nueva info
            if datos["evento"] != "Desconocido": prospecto.tipo_evento = datos["evento"]
            if datos["invitados"] > 0: prospecto.invitados = datos["invitados"]
            if valor > 0: prospecto.valor_estimated = valor
            
            prospecto.estado = "Cotizado" if valor > 0 else "Interesado"
            
            db.session.commit()
            logger.info(f"✨ [SISTEMA]: Lead '{nombre}' actualizado (Valor: ${valor})")
        except Exception as e:
            logger.error(f"❌ [SISTEMA]: Error al guardar lead: {e}")

    def guardar_cita_en_db(self, reporte_angela, tenant_id):
        try:
            datos = self.limpiar_reporte(reporte_angela)
            nueva_cita = Appointment(
                tenant_id=tenant_id, 
                nombre_visitante=datos["nombre"], 
                fecha=datos["fecha"], 
                hora=datos["hora"]
            )
            db.session.add(nueva_cita)
            db.session.commit()
            logger.info(f"✨ [SISTEMA]: Cita guardada para {datos['nombre']}")
        except Exception as e:
            logger.error(f"❌ [SISTEMA]: Error al guardar cita: {e}")

    def consultar_precios(self, tenant_id, tipo_evento):
        if tipo_evento == "Desconocido": return None
        servicio = Service.query.filter(
            Service.tenant_id == tenant_id,
            Service.nombre_servicio.ilike(f"%{tipo_evento}%")
        ).first()
        return servicio.precio_por_persona if servicio else None