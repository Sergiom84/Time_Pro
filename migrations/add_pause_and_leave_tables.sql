-- Migración para añadir tablas de pausas de trabajo y solicitudes de imputaciones
-- Fecha: 2025-11-03

-- Crear tabla para pausas de trabajo
CREATE TABLE IF NOT EXISTS work_pause (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    time_record_id INTEGER NOT NULL,
    pause_type VARCHAR(50) NOT NULL CHECK (pause_type IN ('Descanso', 'Hora del almuerzo', 'Asuntos médicos', 'Desplazamientos', 'Otros')),
    pause_start TIMESTAMP NOT NULL,
    pause_end TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_work_pause_user
        FOREIGN KEY (user_id)
        REFERENCES "user"(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_work_pause_time_record
        FOREIGN KEY (time_record_id)
        REFERENCES time_record(id)
        ON DELETE CASCADE
);

-- Crear tabla para solicitudes de vacaciones/bajas/ausencias
CREATE TABLE IF NOT EXISTS leave_request (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('Vacaciones', 'Baja médica', 'Ausencia justificada', 'Ausencia injustificada', 'Permiso especial')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'Pendiente' CHECK (status IN ('Pendiente', 'Aprobado', 'Rechazado', 'Cancelado')),
    approved_by INTEGER,
    approval_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_leave_request_user
        FOREIGN KEY (user_id)
        REFERENCES "user"(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_leave_request_approver
        FOREIGN KEY (approved_by)
        REFERENCES "user"(id)
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_work_pause_user_id ON work_pause(user_id);
CREATE INDEX idx_work_pause_time_record_id ON work_pause(time_record_id);
CREATE INDEX idx_work_pause_pause_end ON work_pause(pause_end);
CREATE INDEX idx_work_pause_date ON work_pause(pause_start);

CREATE INDEX idx_leave_request_user_id ON leave_request(user_id);
CREATE INDEX idx_leave_request_status ON leave_request(status);
CREATE INDEX idx_leave_request_dates ON leave_request(start_date, end_date);
CREATE INDEX idx_leave_request_created_at ON leave_request(created_at);

-- Trigger para actualizar updated_at en leave_request
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leave_request_updated_at
    BEFORE UPDATE ON leave_request
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentación
COMMENT ON TABLE work_pause IS 'Registra las pausas/descansos durante la jornada laboral';
COMMENT ON TABLE leave_request IS 'Registra las solicitudes de vacaciones, bajas y ausencias de los empleados';

COMMENT ON COLUMN work_pause.pause_type IS 'Tipo de pausa: Descanso, Almuerzo, Médico, Desplazamiento, Otros';
COMMENT ON COLUMN leave_request.status IS 'Estado de la solicitud: Pendiente, Aprobado, Rechazado, Cancelado';
COMMENT ON COLUMN leave_request.approved_by IS 'ID del administrador que aprobó/rechazó la solicitud';