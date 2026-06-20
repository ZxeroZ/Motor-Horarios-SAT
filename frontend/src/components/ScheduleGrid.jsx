import { useMemo } from 'react';

export default function ScheduleGrid({ result, selectedSeccion, setSelectedSeccion, seccionesOptions, seccionInfo, cursoNombre, profNombre }) {
  const matrixData = useMemo(() => {
    if (!result?.asignaciones || !selectedSeccion) return null;
    
    const ordenDias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    const secAsig = result.asignaciones.filter(a => a.seccion_id === selectedSeccion);
    const exactDias = Array.from(new Set(secAsig.map(a => a.dia)))
      .sort((a, b) => ordenDias.indexOf(a) - ordenDias.indexOf(b));
    
    const turnosUsados = new Set(secAsig.map(a => a.turno));
    const SLOTS = turnosUsados.has("Mañana") && turnosUsados.has("Tarde")
      ? [1,2,3,4,5,6,7,8,9,10,11,12]
      : turnosUsados.has("Tarde") ? [7,8,9,10,11,12] : [1,2,3,4,5,6];
    
    const mat = {};
    SLOTS.forEach(slot => {
      mat[slot] = {};
      exactDias.forEach(dia => { mat[slot][dia] = null; });
    });

    secAsig.forEach(a => {
      const start = (a.slot_inicio !== undefined ? a.slot_inicio + 1 : 1);
      const dur = a.horas || 1;
      for (let i = 0; i < dur; i++) {
        const currSlot = start + i;
        const absSlot = a.turno === "Tarde" ? currSlot + 6 : currSlot;
        if (mat[absSlot] && mat[absSlot][a.dia] !== undefined) {
          mat[absSlot][a.dia] = { ...a, is_start: i === 0 };
        }
      }
    });
    
    return { mat, exactDias, SLOTS, turnosUsados };
  }, [result, selectedSeccion]);

  const getCourseColor = (cursoId) => {
    const num = parseInt(cursoId.replace("CUR_", "")) || 0;
    return `course-c${num % 18}`;
  };

  if (!matrixData) return null;

  return (
    <div style={{background: 'var(--bg-card)', padding: '2rem', borderRadius: 'var(--border-radius-lg)', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border-color)'}}>
      <div className="schedule-stats-panel">
        <div className="stat-card">
          <span className="stat-label">Estado</span>
          <span className={`stat-value status-${result.estado?.toLowerCase()}`}>{result.estado}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Tiempo</span>
          <span className="stat-value">{result.estadisticas?.tiempo_segundos?.toFixed(2)}s</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Ramas</span>
          <span className="stat-value">{result.estadisticas?.ramas_exploradas || 0}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Conflictos</span>
          <span className="stat-value">{result.estadisticas?.conflictos || 0}</span>
        </div>
      </div>
      <div className="schedule-header">
        <h2>Malla Horaria</h2>
        <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
          <span style={{color: 'var(--text-muted)', fontSize:'0.9rem'}}>Turno: <b>{Array.from(matrixData.turnosUsados).join(" + ")}</b></span>
          <select className="schedule-select" value={selectedSeccion} onChange={(e) => setSelectedSeccion(e.target.value)}>
            {seccionesOptions.map(sec => (
              <option key={sec} value={sec}>{seccionInfo[sec] || sec}</option>
            ))}
          </select>
        </div>
      </div>
      <table className="calendar-grid">
        <thead>
          <tr><th>Hora</th>{matrixData.exactDias.map(d => <th key={d}>{d}</th>)}</tr>
        </thead>
        <tbody>
          {matrixData.SLOTS.map(slot => {
            const shift = slot > 6 ? "Tarde" : "Mañana";
            const localSlot = slot > 6 ? slot - 6 : slot;
            return (
            <tr key={slot}>
              <td style={{background: 'var(--bg-panel-light)', borderRadius: '12px', textAlign: 'center', minWidth: '80px'}}>
                Bloque {localSlot}<br/><small style={{color: 'var(--text-muted)'}}>{shift}</small>
              </td>
              {matrixData.exactDias.map(dia => {
                const clase = matrixData.mat[slot][dia];
                return (
                  <td key={`${slot}-${dia}`} className={clase ? "filled-cell" : ""}>
                    {clase ? (
                      <div className={`class-card ${getCourseColor(clase.curso_id)} ${clase.curso_id === 'TUT1' ? 'tutoria-card' : ''}`}>
                        <strong className="course-name">{cursoNombre[clase.curso_id] || clase.curso_id}</strong>
                        <span className="prof-name">{profNombre[clase.profesor_id] || clase.profesor_id}</span>
                      </div>
                    ) : <span className="empty-text">—</span>}
                  </td>
                )
              })}
            </tr>
          )})}
        </tbody>
      </table>
    </div>
  );
}
