from app.models.tenant import db
from datetime import datetime

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    
    # --- NUEVOS CAJONES PARA EL DASHBOARD DE DINERO ---
    tipo_evento = db.Column(db.String(100))        # Ej: 'Boda Real'
    invitados = db.Column(db.Integer, default=0)    # Ej: 50
    valor_estimated = db.Column(db.Float, default=0.0) # Ej: 7500000.0
    
    estado = db.Column(db.String(50), default='nuevo') # nuevo, cotizado, cerrado, perdido
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Lead {self.nombre} - Valor: ${self.valor_estimated}>'