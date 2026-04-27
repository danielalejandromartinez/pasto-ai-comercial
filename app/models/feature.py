from app.models.tenant import db

class TenantFeature(db.Model):
    __tablename__ = 'tenant_features'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    module_name = db.Column(db.String(50), nullable=False) # Ejemplo: 'whatsapp', 'dashboard'
    is_enabled = db.Column(db.Boolean, default=False)