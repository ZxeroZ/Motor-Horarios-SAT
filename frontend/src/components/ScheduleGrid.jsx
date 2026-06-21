import { useMemo, useState, useCallback } from 'react';

const DIA_MAP = { "Lunes": 1, "Martes": 2, "Miercoles": 3, "Miércoles": 3, "Jueves": 4, "Viernes": 5, "Sabado": 6, "Sábado": 6, "Domingo": 7 };
const TURNO_MAP = { "Mañana": 1, "Manana": 1, "Tarde": 2 };
const REVERSE_DIA = { 1: "Lunes", 2: "Martes", 3: "Miercoles", 4: "Jueves", 5: "Viernes", 6: "Sabado", 7: "Domingo" };
const REVERSE_TURNO = { 1: "Mañana", 2: "Tarde" };

export default function ScheduleGrid({ result, selectedSeccion, setSelectedSeccion, seccionesOptions, seccionInfo, cursoNombre, profNombre, onMoveAssignment, editMode }) {
  const [dragged, setDragged] = useState(null);
  const [overCell, setOverCell] = useState(null);

  const matrixData = useMemo(() => {
    if (!result?.asignaciones || !selectedSeccion) return null;
    
    const ordenDias = ["Lunes", "Martes", "Miercoles", "Miércoles", "Jueves", "Viernes", "Sabado", "Sábado", "Domingo"];
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
        const absSlot = a.turno === "Tarde" || a.turno === "Tarde" ? currSlot + 6 : currSlot;
        if (mat[absSlot] && mat[absSlot][a.dia] !== undefined) {
          mat[absSlot][a.dia] = { ...a, is_start: i === 0 };
        }
      }
    });
    
    return { mat, exactDias, SLOTS, turnosUsados };
  }, [result, selectedSeccion]);

  const getCourseColor = (cursoId) => {
    const num = parseInt(String(cursoId).replace(/\D/g, '')) || 0;
    return `course-c${num % 18}`;
  };

  const findAssignmentAt = useCallback((slot, dia) => {
    if (!matrixData) return null;
    const clase = matrixData.mat[slot]?.[dia];
    if (!clase || !clase.is_start) return null;
    const dur = clase.horas || 1;
    for (let i = 0; i < dur; i++) {
      const absSlot = clase.turno === "Tarde" ? (clase.slot_inicio + 1 + i + 6) : (clase.slot_inicio + 1 + i);
      if (absSlot === slot && clase.dia === dia) return clase;
    }
    return clase.is_start ? clase : null;
  }, [matrixData]);

  const handleDragStart = useCallback((e, slot, dia) => {
    const clase = findAssignmentAt(slot, dia);
    if (!clase) { e.preventDefault(); return; }
    const localSlot = slot > 6 ? slot - 6 : slot;
    setDragged({
      slot, dia,
      seccionId: clase.seccion_id,
      cursoId: clase.curso_id,
      profesorId: clase.profesor_id,
      diaOrigen: clase.dia,
      turnoOrigen: clase.turno,
      slotInicio: localSlot - 1,
      horas: 1
    });
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', JSON.stringify({ slot, dia }));
    requestAnimationFrame(() => { e.target.classList.add('dragging'); });
  }, [findAssignmentAt]);

  const handleDragEnd = useCallback((e) => {
    e.target.classList.remove('dragging');
    setDragged(null);
    setOverCell(null);
  }, []);

  const handleDragOver = useCallback((e, slot, dia) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragged && (slot !== dragged.slot || dia !== dragged.dia)) {
      setOverCell({ slot, dia });
    }
  }, [dragged]);

  const handleDragLeave = useCallback(() => { setOverCell(null); }, []);

  const handleDrop = useCallback((e, slot, dia) => {
    e.preventDefault();
    setOverCell(null);
    if (!dragged) return;
    if (slot === dragged.slot && dia === dragged.dia) return;

    const turnoOrigen = dragged.turnoOrigen;
    const turnoDestino = slot > 6 ? "Tarde" : "Mañana";
    if (turnoOrigen !== turnoDestino) {
      setDragged(null);
      return;
    }

    const slotInicioDestino = slot > 6 ? slot - 7 : slot - 1;

    const numBlocks = matrixData?.SLOTS?.length || 6;
    const maxBlocksDestino = numBlocks - slotInicioDestino;

    if (onMoveAssignment) {
      onMoveAssignment({
        seccionId: dragged.seccionId,
        cursoId: dragged.cursoId,
        profesorId: dragged.profesorId,
        diaOrigen: dragged.diaOrigen,
        turnoOrigen: dragged.turnoOrigen,
        slotOrigen: dragged.slotInicio,
        horasOrigen: dragged.horas,
        diaDestino: dia,
        turnoDestino,
        slotDestino: slotInicioDestino,
        horasDestino: Math.min(dragged.horas, maxBlocksDestino),
        maxBlocksDestino,
        diaOrigenId: DIA_MAP[dragged.diaOrigen] || 1,
        turnoOrigenId: TURNO_MAP[dragged.turnoOrigen] || 1,
        diaDestinoId: DIA_MAP[dia] || 1,
        turnoDestinoId: TURNO_MAP[turnoDestino] || 1
      });
    }
    setDragged(null);
  }, [dragged, matrixData, onMoveAssignment]);

  if (!matrixData) return null;

  return (
    <div style={{background: 'var(--bg-card)', padding: '2rem', borderRadius: 'var(--border-radius-lg)', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border-color)'}}>
      <div className="schedule-stats-panel">
        {result.version > 0 && (
          <div className="stat-card">
            <span className="stat-label">Versión</span>
            <span className="stat-value" style={{color: 'var(--accent)', fontWeight: '700', fontSize: '1.1rem'}}>v{result.version}</span>
          </div>
        )}
        <div className="stat-card">
          <span className="stat-label">Estado</span>
          <span className={`stat-value status-${result.estado?.toLowerCase()}`}>{result.estado}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Clases</span>
          <span className="stat-value">{result.asignaciones?.length || 0}</span>
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
        <h2>{result.nombre || 'Malla Horaria'}</h2>
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
                const isOver = overCell?.slot === slot && overCell?.dia === dia;
                const isOrigin = dragged?.slot === slot && dragged?.dia === dia;
                return (
                  <td
                    key={`${slot}-${dia}`}
                    className={[
                      clase ? "filled-cell" : "",
                      isOver ? "drop-target" : "",
                      isOrigin ? "drop-origin" : ""
                    ].filter(Boolean).join(' ')}
                    onDragOver={(e) => handleDragOver(e, slot, dia)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, slot, dia)}
                  >
                    {clase ? (
                      <div
                        className={`class-card ${getCourseColor(clase.curso_id)} ${clase.curso_id === 'TUT1' ? 'tutoria-card' : ''}`}
                        draggable={editMode ? "true" : "false"}
                        onDragStart={(e) => { if (!editMode) { e.preventDefault(); return; } handleDragStart(e, slot, dia); }}
                        onDragEnd={handleDragEnd}
                      >
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
      <div className="drag-hint">
        <span className="material-icons-outlined" style={{fontSize: '0.9rem', verticalAlign: 'middle'}}>info</span>
        {editMode ? 'Arrastrá una clase a otra celda para moverla' : 'Activá el Modo Edición para poder mover bloques'}
      </div>
    </div>
  );
}
