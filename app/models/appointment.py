from app.models.tenant import db

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True) # Puede ser nulo si la humana anota a alguien rápido
    nombre_visitante = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.String(20), nullable=False) # Guardaremos 'YYYY-MM-DD'
    hora = db.Column(db.String(10), nullable=False)  # Guardaremos 'HH:MM'
    estado = db.Column(db.String(20), default='programada') # programada, asistió, cancelada

    def __repr__(self):
        return f'<Appointment {self.nombre_visitante} - {self.fecha} {self.hora}>'