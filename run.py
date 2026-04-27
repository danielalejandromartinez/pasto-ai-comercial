import os
import logging
from flask import Flask, render_template, request, redirect, jsonify
from sqlalchemy import func # Herramienta para sumar y contar rápido
from dotenv import load_dotenv # Importamos la herramienta del escondite secreto
from app.models.tenant import db, Tenant
from app.models.lead import Lead
from app.models.feature import TenantFeature
from app.models.service import Service
from app.models.appointment import Appointment
from app.agents.comercial import AgenteComercial

# --- CARGAR EL ESCONDITE SECRETO ---
load_dotenv()

# --- CONFIGURACIÓN DE SENSORES NASA (Logging) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NASA_CONTROL")

app = Flask(__name__)

# --- INICIALIZAR EL SISTEMA DE ANGELA ---
# Ahora Angela busca su llave en el archivo .env automáticamente
API_KEY = os.getenv("OPENAI_API_KEY")
angela = AgenteComercial(api_key=API_KEY)

# --- CONFIGURACIÓN DE LA BIBLIOTECA (Base de Datos) ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pasto_ai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- RUTAS DEL SISTEMA ---

@app.route('/superadmin')
def admin_panel():
    todos_los_tenants = Tenant.query.all()
    return render_template('super_admin.html', clientes=todos_los_tenants)

@app.route('/dashboard/<int:tenant_id>')
def client_dashboard(tenant_id):
    empresa = Tenant.query.get_or_404(tenant_id)
    prospectos_empresa = Lead.query.filter_by(tenant_id=tenant_id).all()
    servicios_empresa = Service.query.filter_by(tenant_id=tenant_id).all()
    citas_empresa = Appointment.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('client_dashboard.html', 
                           tenant=empresa, 
                           prospectos=prospectos_empresa, 
                           servicios=servicios_empresa,
                           citas=citas_empresa)

# --- NUEVA RUTA: DASHBOARD EJECUTIVO (Power BI Style) ---
@app.route('/executive/<int:tenant_id>')
def executive_dashboard(tenant_id):
    empresa = Tenant.query.get_or_404(tenant_id)
    
    # 1. Sumamos todo el dinero de los leads (Pipeline)
    dinero_total = db.session.query(func.sum(Lead.valor_estimated)).filter(Lead.tenant_id == tenant_id).scalar() or 0
    
    # 2. Contamos total de clientes
    total_leads = Lead.query.filter_by(tenant_id=tenant_id).count()
    
    # 3. Contamos total de citas
    total_citas = Appointment.query.filter_by(tenant_id=tenant_id).count()
    
    # 4. Agrupamos por tipo de evento para la gráfica
    eventos_stats = db.session.query(Lead.tipo_evento, func.count(Lead.id)).filter(Lead.tenant_id == tenant_id).group_by(Lead.tipo_evento).all()
    
    metricas = {
        "dinero": "{:,.0f}".format(dinero_total),
        "leads": total_leads,
        "citas": total_citas,
        "distribucion": dict(eventos_stats)
    }
    
    return render_template('executive_dashboard.html', tenant=empresa, kpis=metricas)

@app.route('/preguntar/<int:tenant_id>', methods=['POST'])
def preguntar(tenant_id):
    datos = request.get_json()
    mensaje_usuario = datos.get('mensaje')
    respuesta_final = angela.ejecutar_loop(mensaje_usuario, tenant_id=tenant_id)
    return jsonify({"respuesta": respuesta_final})

@app.route('/superadmin/crear_tenant', methods=['POST'])
def crear_tenant():
    nombre = request.form.get('nombre')
    industria = request.form.get('industria')
    plan = request.form.get('plan')
    nuevo_tenant = Tenant(nombre_empresa=nombre, industry_type=industria, plan=plan)
    db.session.add(nuevo_tenant)
    db.session.flush()
    feature_ws = TenantFeature(tenant_id=nuevo_tenant.id, module_name='whatsapp', is_enabled=False)
    db.session.add(feature_ws)
    db.session.commit()
    return redirect('/superadmin')

@app.route('/superadmin/toggle_whatsapp/<int:tenant_id>')
def toggle_whatsapp(tenant_id):
    feature = TenantFeature.query.filter_by(tenant_id=tenant_id, module_name='whatsapp').first()
    if feature:
        feature.is_enabled = not feature.is_enabled
        db.session.commit()
    return redirect('/superadmin')

@app.route('/chat/<int:tenant_id>')
def ver_chat(tenant_id):
    empresa = Tenant.query.get_or_404(tenant_id)
    return render_template('chat.html', tenant=empresa)

# --- RUTAS DE CONFIGURACIÓN DEL CLIENTE ---

@app.route('/dashboard/<int:tenant_id>/add_service', methods=['POST'])
def add_service(tenant_id):
    nombre = request.form.get('nombre_servicio')
    precio = request.form.get('precio')
    nuevo_servicio = Service(tenant_id=tenant_id, nombre_servicio=nombre, precio_por_persona=float(precio))
    db.session.add(nuevo_servicio)
    db.session.commit()
    return redirect(f'/dashboard/{tenant_id}')

@app.route('/dashboard/<int:tenant_id>/add_appointment', methods=['POST'])
def add_appointment(tenant_id):
    nombre_v = request.form.get('nombre')
    fecha_v = request.form.get('fecha')
    hora_v = request.form.get('hora')
    nueva_cita = Appointment(tenant_id=tenant_id, nombre_visitante=nombre_v, fecha=fecha_v, hora=hora_v)
    db.session.add(nueva_cita)
    db.session.commit()
    return redirect(f'/dashboard/{tenant_id}')

# --- ENCENDER LOS SISTEMAS ---
with app.app_context():
    db.create_all()
    logger.info("🛰️  [SISTEMA]: Base de datos lista. Todos los sistemas en línea.")

if __name__ == '__main__':
    app.run(debug=True)