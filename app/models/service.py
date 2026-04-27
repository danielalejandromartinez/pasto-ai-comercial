from app.models.tenant import db

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False) # ¿De quién es este precio?
    nombre_servicio = db.Column(db.String(100), nullable=False) # Ejemplo: 'Boda Premium'
    precio_por_persona = db.Column(db.Float, nullable=False)    # Ejemplo: 150000.0
    
    def __repr__(self):
        return f'<Service {self.nombre_servicio} - ${self.precio_por_persona}>'