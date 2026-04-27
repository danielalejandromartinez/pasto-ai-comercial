from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    industry_type = db.Column(db.String(50), nullable=False) # Ejemplo: 'eventos'
    plan = db.Column(db.String(20), default='basico')        # Plan de pago
    status = db.Column(db.String(20), default='activo')      # Si pagó o no
    # Esto es como decirle a la empresa: "Mira, aquí están tus interruptores"
    features = db.relationship('TenantFeature', backref='tenant', lazy=True)
    
    def __repr__(self):
        return f'<Tenant {self.nombre_empresa}>'