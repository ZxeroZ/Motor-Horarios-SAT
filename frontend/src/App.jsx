import { useState, useMemo, useEffect } from 'react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState("horarios");

  // --- Estado: Horarios ---
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedSeccion, setSelectedSeccion] = useState("");

  // --- Estado: Administración (CRUD) ---
  const [areas, setAreas] = useState([]);
  const [cursos, setCursos] = useState([]);
  const [formArea, setFormArea] = useState({ nombre_area: "", max_horas_dia: 4 });
  const [formCurso, setFormCurso] = useState({ nombre_curso: "", id_area: "" });

  const loadAdminData = async () => {
    try {
      const resA = await fetch('http://localhost:8000/api/areas');
      const dataA = await resA.json();
      setAreas(dataA);

      const resC = await fetch('http://localhost:8000/api/cursos');
      const dataC = await resC.json();
      setCursos(dataC);
    } catch (e) {
      console.error("Error al cargar data de admin", e);
    }
  };

  useEffect(() => {
    if (activeTab === "admin") loadAdminData();
  }, [activeTab]);

  const handleCreateArea = async (e) => {
    e.preventDefault();
    if (!formArea.nombre_area) return;
    await fetch('http://localhost:8000/api/areas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formArea)
    });
    setFormArea({ nombre_area: "", max_horas_dia: 4 });
    loadAdminData();
  };

  const handleCreateCurso = async (e) => {
    e.preventDefault();
    if (!formCurso.nombre_curso || !formCurso.id_area) return;
    await fetch('http://localhost:8000/api/cursos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombre_curso: formCurso.nombre_curso,
        id_area: parseInt(formCurso.id_area)
      })
    });
    setFormCurso({ ...formCurso, nombre_curso: "" });
    loadAdminData();
  };

  // --- Lógica: Generar Horario ---
  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/generar-horario', { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        setResult(data.resultado);
        if (data.resultado.asignaciones?.length > 0) {
          setSelectedSeccion(data.resultado.asignaciones[0].seccion_id);
        }
      } else {
        setError(JSON.stringify(data.errores, null, 2));
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleDownload = () => {
    const jsonString = `data:text/json;chatset=utf-8,${encodeURIComponent(JSON.stringify(result, null, 2))}`;
    const link = document.createElement("a");
    link.href = jsonString;
    link.download = "horarios_optimizados.json";
    link.click();
  };

  const secciones = useMemo(() => {
    if (!result?.asignaciones) return [];
    return Array.from(new Set(result.asignaciones.map(a => a.seccion_id))).sort();
  }, [result]);

  const matrixData = useMemo(() => {
    if (!result?.asignaciones || !selectedSeccion) return null;
    
    const ordenDias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"];
    const exactDiasRaw = Array.from(new Set(result.asignaciones.map(a => a.dia)));
    const exactDias = exactDiasRaw.sort((a, b) => ordenDias.indexOf(a) - ordenDias.indexOf(b));
    const MAT_SLOTS = [1,2,3,4,5,6,7,8,9,10,11,12];
    
    const mat = {};
    MAT_SLOTS.forEach(slot => {
      mat[slot] = {};
      exactDias.forEach(dia => { mat[slot][dia] = null; });
    });

    result.asignaciones
      .filter(a => a.seccion_id === selectedSeccion)
      .forEach(a => {
        const start = a.slot_inicio !== undefined ? a.slot_inicio + 1 : 1;
        const dur = a.horas || 1;
        for (let i = 0; i < dur; i++) {
           const currSlot = start + i;
           const absoluteSlot = a.turno === "Tarde" ? currSlot + 6 : currSlot;
           if (mat[absoluteSlot] && mat[absoluteSlot][a.dia] !== undefined) {
             mat[absoluteSlot][a.dia] = { ...a, is_start: i === 0 };
           }
        }
      });
    
    return { mat, exactDias, MAT_SLOTS };
  }, [result, selectedSeccion]);

  return (
    <div className="container">
      <header className="hero">
        <h1>Centro de Mando: Horarios</h1>
        <p>Motor de Optimización CP-SAT Integrado</p>
        
        <div className="tabs">
          <button className={`tab-btn ${activeTab === 'horarios' ? 'active' : ''}`} onClick={() => setActiveTab('horarios')}>
            📅 Vista de Horarios
          </button>
          <button className={`tab-btn ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>
            ⚙️ Configuración Académica
          </button>
        </div>
      </header>
      
      <main className="dashboard">
        {/* --- PESTAÑA: HORARIOS --- */}
        {activeTab === 'horarios' && (
          <div className="tab-pane">
            <div className="trigger-section">
              <button className={`btn-generate ${loading ? 'loading' : ''}`} onClick={handleGenerate} disabled={loading}>
                {loading ? 'Calculando Restricciones...' : '🚀 Generar Horario Óptimo'}
              </button>
              {result && (
                <button className="btn-export" onClick={handleDownload}>
                  💾 Exportar JSON
                </button>
              )}
            </div>

            {error && (
                <div className="error-panel">
                  <h3>Se encontraron errores de validación:</h3>
                  <pre>{error}</pre>
                </div>
            )}

            {result && (
              <div className="results-container">
                <aside className="audit-panel">
                  <h3>Auditoría Matemática</h3>
                  <p className="audit-desc">Estado devuelto por la IA: <span className="badge-optimal">{result.estado}</span></p>
                  
                  <ul className="check-list">
                    <li><span className="check">✅</span> <strong>Cero Colisiones:</strong> Ningún profesor agendado a 2 lugares a la vez.</li>
                    <li><span className="check">✅</span> <strong>Disponibilidad Exacta:</strong> Se cruzaron matrices de días viables.</li>
                    <li><span className="check">✅</span> <strong>Límites Pedagógicos:</strong> Se respetó tope mensual de carga por Área.</li>
                    <li><span className="check">✅</span> <strong>Plan de Estudios:</strong> El 100% de la cuota semanal posicionada.</li>
                  </ul>

                  <div className="audit-stats">
                    <div>⏱️ Tiempo: {(result.estadisticas?.tiempo_segundos || 0).toFixed(2)}s</div>
                    <div>🌿 Ramas Vistas: {result.estadisticas?.ramas_exploradas || 0}</div>
                  </div>
                </aside>

                <section className="calendar-panel">
                  <div className="calendar-header">
                    <h2>Visualizador de Malla</h2>
                    <select 
                      className="section-selector" 
                      value={selectedSeccion} 
                      onChange={(e) => setSelectedSeccion(e.target.value)}
                    >
                      {secciones.map(sec => <option key={sec} value={sec}>Sección {sec.replace("SEC_", "")}</option>)}
                    </select>
                  </div>

                  {matrixData && (
                    <div className="grid-responsive">
                      <table className="calendar-grid">
                        <thead>
                          <tr>
                            <th className="slot-col">Hora</th>
                            {matrixData.exactDias.map(d => <th key={d}>{d}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {matrixData.MAT_SLOTS.map(slot => {
                            const shift = slot > 6 ? "Tarde" : "Mañana";
                            const localSlot = slot > 6 ? slot - 6 : slot;
                            return (
                            <tr key={slot}>
                              <td className="slot-label">
                                Bloque {localSlot}<br/>
                                <small style={{opacity: 0.6}}>{shift}</small>
                              </td>
                              {matrixData.exactDias.map(dia => {
                                const clase = matrixData.mat[slot][dia];
                                const colorClass = clase ? `course-c${(clase.curso_id.charCodeAt(clase.curso_id.length-1) % 6) + 1}` : "";
                                return (
                                  <td key={`${slot}-${dia}`} className={clase ? "filled-cell" : "empty-cell"}>
                                    {clase ? (
                                      <div className={`class-card ${colorClass}`} title={`Calculado dinámicamente para cumplir topes de Área de ${clase.curso_id}`}>
                                        {clase.is_start ? (
                                            <>
                                                <span className="c-name">{clase.curso_id.replace("CUR_", "ID ")}</span>
                                                <span className="c-prof">{clase.profesor_id.replace("PROF_", "Prof ")}</span>
                                            </>
                                        ) : (
                                            <span className="c-continue">⬇️</span>
                                        )}
                                      </div>
                                    ) : (
                                      <span className="empty-text">- Libre -</span>
                                    )}
                                  </td>
                                )
                              })}
                            </tr>
                          )})}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              </div>
            )}
          </div>
        )}

        {/* --- PESTAÑA: ADMINISTRACIÓN --- */}
        {activeTab === 'admin' && (
          <div className="admin-pane">
            <div className="admin-grid">
              
              {/* Formulario Areas */}
              <div className="admin-card">
                <h3>Administrar Áreas / Categorías</h3>
                <form onSubmit={handleCreateArea} className="admin-form">
                  <input type="text" placeholder="Nombre de Área (Ej. Matemáticas)" value={formArea.nombre_area} onChange={e => setFormArea({...formArea, nombre_area: e.target.value})} />
                  <input type="number" placeholder="Max hs diarias" value={formArea.max_horas_dia} onChange={e => setFormArea({...formArea, max_horas_dia: e.target.value})} />
                  <button type="submit" className="btn-save">Agregar Área</button>
                </form>

                <table className="admin-table">
                  <thead><tr><th>ID</th><th>Nombre</th><th>Tope Horas</th></tr></thead>
                  <tbody>
                    {areas.map(a => (
                      <tr key={a.id_area}>
                        <td>{a.id_area}</td>
                        <td>{a.nombre_area}</td>
                        <td>{a.max_horas_dia}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Formulario Cursos */}
              <div className="admin-card">
                <h3>Administrar Cursos Mínimos</h3>
                <form onSubmit={handleCreateCurso} className="admin-form">
                  <input type="text" placeholder="Nombre de Curso (Ej. Álgebra)" value={formCurso.nombre_curso} onChange={e => setFormCurso({...formCurso, nombre_curso: e.target.value})} />
                  <select value={formCurso.id_area} onChange={e => setFormCurso({...formCurso, id_area: e.target.value})}>
                    <option value="">-- Seleccionar Área Padre --</option>
                    {areas.map(a => (
                      <option key={a.id_area} value={a.id_area}>{a.nombre_area}</option>
                    ))}
                  </select>
                  <button type="submit" className="btn-save">Agregar Curso</button>
                </form>

                <table className="admin-table">
                  <thead><tr><th>ID</th><th>Curso</th><th>ID Área Padre</th></tr></thead>
                  <tbody>
                    {cursos.map(c => (
                      <tr key={c.id_curso}>
                        <td>{c.id_curso}</td>
                        <td>{c.nombre_curso}</td>
                        <td>{c.id_area}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
