import { useState, useMemo, useEffect } from 'react';
import './index.css';

function App() {
  // --- Estado: Autenticación ---
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [loginError, setLoginError] = useState("");

  const [activeTab, setActiveTab] = useState("horarios");
  const [activeAdminTab, setActiveAdminTab] = useState("materias"); // sub-tab

  // --- Estado: Horarios ---
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedSeccion, setSelectedSeccion] = useState("");

  // --- Estado: Data de BD ---
  const [colegios, setColegios] = useState([]);
  const [sedes, setSedes] = useState([]);
  const [grados, setGrados] = useState([]);
  const [areas, setAreas] = useState([]);
  const [cursos, setCursos] = useState([]);
  const [profesores, setProfesores] = useState([]);
  const [secciones, setSecciones] = useState([]);
  const [planes, setPlanes] = useState([]);
  const [profesorCursos, setProfesorCursos] = useState([]);

  // --- Estado: Formularios ---
  const [formSede, setFormSede] = useState({ nombre_sede: "", id_colegio: "" });
  const [formGrado, setFormGrado] = useState({ numero: "" });
  const [formArea, setFormArea] = useState({ nombre: "", max_horas_dia: 4 });
  const [formCurso, setFormCurso] = useState({ nombre_curso: "", id_area: "" });
  const [formProf, setFormProf] = useState({ nombre_profesor: "", id_sede: "", max_horas_dia: 6 });
  const [formProfCurso, setFormProfCurso] = useState({ id_profesor: "", id_curso: "" });
  const [formSeccion, setFormSeccion] = useState({ nombre: "", id_grado: "", id_sede: "" });
  const [formPlan, setFormPlan] = useState({ id_grado: "", id_curso: "", horas_semanales: 1 });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginForm)
      });
      const data = await res.json();
      if (res.ok) {
        setIsAuthenticated(true);
        setUser(data.user);
      } else {
        setLoginError(data.detail || "Error al iniciar sesión");
      }
    } catch (err) {
      setLoginError("Error de conexión con el servidor");
    }
  };

  const loadAdminData = async () => {
    try {
      const endpoints = ["colegio", "sedes", "grados", "areas", "cursos", "profesores", "secciones", "planes", "profesor-curso"];
      const responses = await Promise.all(endpoints.map(ep => fetch(`http://localhost:8000/api/${ep}`)));
      const data = await Promise.all(responses.map(r => r.json()));
      
      setColegios(data[0]);
      setSedes(data[1]);
      setGrados(data[2]);
      setAreas(data[3]);
      setCursos(data[4]);
      setProfesores(data[5]);
      setSecciones(data[6]);
      setPlanes(data[7]);
      setProfesorCursos(data[8]);
    } catch (e) {
      console.error("Error al cargar data de admin", e);
    }
  };

  useEffect(() => {
    if (isAuthenticated) loadAdminData();
  }, [activeTab, isAuthenticated]);

  // --- Manejadores de Creación ---
  const handleCreate = async (endpoint, payload, resetFn) => {
    await fetch(`http://localhost:8000/api/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    resetFn();
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

  // --- Lookups para nombres ---
  const cursoNombre = useMemo(() => {
    const m = {};
    cursos.forEach(c => { m[`CUR_${c.id_curso}`] = c.nombre_curso; });
    return m;
  }, [cursos]);

  const profNombre = useMemo(() => {
    const m = {};
    profesores.forEach(p => { m[`PROF_${p.id_profesores}`] = p.nombre_profesor; });
    return m;
  }, [profesores]);

  const seccionInfo = useMemo(() => {
    const m = {};
    secciones.forEach(sec => {
      const grado = grados.find(g => g.id_grado === sec.id_grado);
      const sede = sedes.find(s => s.id_sede === sec.id_sede);
      m[`SEC_${sec.id_seccion}`] = `${sec.nombre} (${sede?.nombre_sede || ''})`;
    });
    return m;
  }, [secciones, grados, sedes]);

  const seccionesOptions = useMemo(() => {
    if (!result?.asignaciones) return [];
    return Array.from(new Set(result.asignaciones.map(a => a.seccion_id)))
      .sort((a, b) => parseInt(a.replace("SEC_", "")) - parseInt(b.replace("SEC_", "")));
  }, [result]);

  const matrixData = useMemo(() => {
    if (!result?.asignaciones || !selectedSeccion) return null;
    
    const ordenDias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"];
    const secAsig = result.asignaciones.filter(a => a.seccion_id === selectedSeccion);
    const exactDias = Array.from(new Set(secAsig.map(a => a.dia)))
      .sort((a, b) => ordenDias.indexOf(a) - ordenDias.indexOf(b));
    
    // Detectar turno de esta sección
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

  // Color estable por curso_id
  const getCourseColor = (cursoId) => {
    const num = parseInt(cursoId.replace("CUR_", "")) || 0;
    return `course-c${num % 18}`;
  };

  /* ====== RENDER ====== */

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h2>Timetable Engine</h2>
          <p>Ingresa tus credenciales para acceder</p>
          <form className="login-form" onSubmit={handleLogin}>
            <input type="email" placeholder="Correo electrónico" value={loginForm.email} onChange={e => setLoginForm({...loginForm, email: e.target.value})} required />
            <input type="password" placeholder="Contraseña" value={loginForm.password} onChange={e => setLoginForm({...loginForm, password: e.target.value})} required />
            {loginError && <div style={{color: 'var(--danger)', fontSize: '0.9rem'}}>{loginError}</div>}
            <button type="submit" className="btn-primary">Iniciar Sesión</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header className="hero">
        <h1>¡Hola, {user?.nombre}! 👋</h1>
        <p>Centro de Control - Algoritmo CP-SAT</p>
        
        <div className="tabs">
          <button className={`tab-btn ${activeTab === 'horarios' ? 'active' : ''}`} onClick={() => setActiveTab('horarios')}>Vista de Horarios</button>
          <button className={`tab-btn ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>Configuración Académica</button>
          <button className="tab-btn" onClick={() => setIsAuthenticated(false)}>Cerrar Sesión</button>
        </div>
      </header>
      
      <main>
        {/* --- PESTAÑA: HORARIOS --- */}
        {activeTab === 'horarios' && (
          <div className="tab-pane">
            <div className="trigger-section">
              <button className={`btn-generate ${loading ? 'loading' : ''}`} onClick={handleGenerate} disabled={loading}>
                {loading ? 'Calculando Restricciones...' : 'Generar Horario Óptimo'}
              </button>
            </div>
            {error && (
                <div style={{color: 'var(--danger)', background: '#fee2e2', padding: '1rem', borderRadius: '16px'}}>
                  <h3>Se encontraron errores de validación:</h3>
                  <pre>{error}</pre>
                </div>
            )}
            {result && result.asignaciones && result.asignaciones.length === 0 && (
                <div style={{color: 'var(--text-main)', background: '#fffbeb', border: '1px solid #fde68a', padding: '1rem', borderRadius: '16px', textAlign: 'center', marginTop: '1rem'}}>
                  <h3>¡Horario Vacío!</h3>
                  <p>El motor calculó el horario con éxito, pero no programó ninguna clase.</p>
                </div>
            )}
            {result && matrixData && result.asignaciones.length > 0 && (
              <div style={{background: 'var(--bg-panel)', padding: '2rem', borderRadius: '24px', boxShadow: 'var(--shadow-sm)'}}>
                <div className="schedule-header">
                  <h2>📅 Malla Horaria</h2>
                  <select className="schedule-select" value={selectedSeccion} onChange={(e) => setSelectedSeccion(e.target.value)}>
                    {seccionesOptions.map(sec => (
                      <option key={sec} value={sec}>{seccionInfo[sec] || sec}</option>
                    ))}
                  </select>
                </div>
                <div className="schedule-stats">
                  <span>📊 Estado: <b>{result.estado}</b></span>
                  <span>⏱ {result.estadisticas?.tiempo_segundos?.toFixed(2)}s</span>
                  <span>🔀 Turno: <b>{Array.from(matrixData.turnosUsados).join(" + ")}</b></span>
                  <span>📝 {result.asignaciones.filter(a => a.seccion_id === selectedSeccion).length} clases</span>
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
                                <div className={`class-card ${getCourseColor(clase.curso_id)}`}>
                                  {clase.is_start ? (
                                      <><strong style={{fontSize:'0.95rem'}}>{cursoNombre[clase.curso_id] || clase.curso_id}</strong><span style={{fontSize:'0.8rem', opacity: 0.85, marginTop: '2px'}}>{profNombre[clase.profesor_id] || clase.profesor_id}</span></>
                                  ) : (<span style={{fontSize: '0.8rem', opacity: 0.7}}>↓ continúa</span>)}
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
            )}
          </div>
        )}

        {/* --- PESTAÑA: ADMINISTRACIÓN --- */}
        {activeTab === 'admin' && (
          <div className="admin-pane">
            
            <div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', justifyContent: 'center'}}>
              <button className={`tab-btn ${activeAdminTab === 'infra' ? 'active' : ''}`} onClick={() => setActiveAdminTab('infra')}>Infraestructura</button>
              <button className={`tab-btn ${activeAdminTab === 'jerarquia' ? 'active' : ''}`} onClick={() => setActiveAdminTab('jerarquia')}>Jerarquía</button>
              <button className={`tab-btn ${activeAdminTab === 'materias' ? 'active' : ''}`} onClick={() => setActiveAdminTab('materias')}>Materias & Profes</button>
              <button className={`tab-btn ${activeAdminTab === 'malla' ? 'active' : ''}`} onClick={() => setActiveAdminTab('malla')}>Malla Curricular</button>
            </div>

            <div className="admin-grid">
              
              {/* --- SUBTAB: INFRAESTRUCTURA --- */}
              {activeAdminTab === 'infra' && (
                <>
                  <div className="admin-card">
                    <h3>Sedes Físicas</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('sedes', { nombre_sede: formSede.nombre_sede, id_colegio: parseInt(formSede.id_colegio) }, () => setFormSede({ nombre_sede: "", id_colegio: "" }))
                    }}>
                      <select value={formSede.id_colegio} onChange={e => setFormSede({...formSede, id_colegio: e.target.value})} required>
                        <option value="">-- Seleccionar Colegio --</option>
                        {colegios.map(c => <option key={c.id_colegio} value={c.id_colegio}>{c.nombre_colegio}</option>)}
                      </select>
                      <input type="text" placeholder="Nombre de Sede" value={formSede.nombre_sede} onChange={e => setFormSede({...formSede, nombre_sede: e.target.value})} required />
                      <button type="submit" className="btn-save">Registrar Sede</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID</th><th>Sede</th><th>Colegio ID</th></tr></thead>
                      <tbody>{sedes.map(s => <tr key={s.id_sede}><td>{s.id_sede}</td><td>{s.nombre_sede}</td><td>{s.id_colegio}</td></tr>)}</tbody>
                    </table>
                  </div>
                </>
              )}

              {/* --- SUBTAB: JERARQUÍA --- */}
              {activeAdminTab === 'jerarquia' && (
                <>
                  <div className="admin-card">
                    <h3>Grados</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('grados', { numero: parseInt(formGrado.numero) }, () => setFormGrado({ numero: "" }))
                    }}>
                      <input type="number" placeholder="Número de Grado (Ej. 1)" value={formGrado.numero} onChange={e => setFormGrado({numero: e.target.value})} required />
                      <button type="submit" className="btn-save">Registrar Grado</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID</th><th>Grado N°</th></tr></thead>
                      <tbody>{grados.map(g => <tr key={g.id_grado}><td>{g.id_grado}</td><td>{g.numero}°</td></tr>)}</tbody>
                    </table>
                  </div>

                  <div className="admin-card">
                    <h3>Secciones</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('secciones', { nombre: formSeccion.nombre, id_grado: parseInt(formSeccion.id_grado), id_sede: parseInt(formSeccion.id_sede) }, () => setFormSeccion({ nombre: "", id_grado: "", id_sede: "" }))
                    }}>
                      <select value={formSeccion.id_sede} onChange={e => setFormSeccion({...formSeccion, id_sede: e.target.value})} required>
                        <option value="">-- Sede --</option>
                        {sedes.map(s => <option key={s.id_sede} value={s.id_sede}>{s.nombre_sede}</option>)}
                      </select>
                      <select value={formSeccion.id_grado} onChange={e => setFormSeccion({...formSeccion, id_grado: e.target.value})} required>
                        <option value="">-- Grado --</option>
                        {grados.map(g => <option key={g.id_grado} value={g.id_grado}>{g.numero}°</option>)}
                      </select>
                      <input type="text" placeholder="Sección (Ej. A)" value={formSeccion.nombre} onChange={e => setFormSeccion({...formSeccion, nombre: e.target.value})} required />
                      <button type="submit" className="btn-save">Registrar Sección</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID</th><th>Sección</th><th>Grado</th></tr></thead>
                      <tbody>{secciones.map(s => <tr key={s.id_seccion}><td>{s.id_seccion}</td><td>{s.nombre}</td><td>ID {s.id_grado}</td></tr>)}</tbody>
                    </table>
                  </div>
                </>
              )}

              {/* --- SUBTAB: MATERIAS Y PROFESORES --- */}
              {activeAdminTab === 'materias' && (
                <>
                  <div className="admin-card">
                    <h3>Áreas (Categorías)</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('areas', { nombre: formArea.nombre, max_horas_dia: parseInt(formArea.max_horas_dia) }, () => setFormArea({ nombre: "", max_horas_dia: 4 }))
                    }}>
                      <input type="text" placeholder="Nombre (Ej. Ciencias)" value={formArea.nombre} onChange={e => setFormArea({...formArea, nombre: e.target.value})} required />
                      <input type="number" placeholder="Max hs diarias" value={formArea.max_horas_dia} onChange={e => setFormArea({...formArea, max_horas_dia: e.target.value})} required />
                      <button type="submit" className="btn-save">Guardar Área</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID</th><th>Nombre</th></tr></thead>
                      <tbody>{areas.map(a => <tr key={a.id_area}><td>{a.id_area}</td><td>{a.nombre}</td></tr>)}</tbody>
                    </table>
                  </div>

                  <div className="admin-card">
                    <h3>Cursos</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('cursos', { nombre_curso: formCurso.nombre_curso, id_area: parseInt(formCurso.id_area) }, () => setFormCurso({ ...formCurso, nombre_curso: "" }))
                    }}>
                      <select value={formCurso.id_area} onChange={e => setFormCurso({...formCurso, id_area: e.target.value})} required>
                        <option value="">-- Área --</option>
                        {areas.map(a => <option key={a.id_area} value={a.id_area}>{a.nombre}</option>)}
                      </select>
                      <input type="text" placeholder="Curso" value={formCurso.nombre_curso} onChange={e => setFormCurso({...formCurso, nombre_curso: e.target.value})} required />
                      <button type="submit" className="btn-save">Guardar Curso</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID</th><th>Curso</th><th>Área ID</th></tr></thead>
                      <tbody>{cursos.map(c => <tr key={c.id_curso}><td>{c.id_curso}</td><td>{c.nombre_curso}</td><td>{c.id_area}</td></tr>)}</tbody>
                    </table>
                  </div>

                  <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                    <h3>Profesores</h3>
                    <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('profesores', { nombre_profesor: formProf.nombre_profesor, id_sede: parseInt(formProf.id_sede), max_horas_dia: parseInt(formProf.max_horas_dia) }, () => setFormProf({ ...formProf, nombre_profesor: "" }))
                    }}>
                      <select style={{flex: 1}} value={formProf.id_sede} onChange={e => setFormProf({...formProf, id_sede: e.target.value})} required>
                        <option value="">-- Sede --</option>
                        {sedes.map(s => <option key={s.id_sede} value={s.id_sede}>{s.nombre_sede}</option>)}
                      </select>
                      <input style={{flex: 2}} type="text" placeholder="Nombre de Profesor" value={formProf.nombre_profesor} onChange={e => setFormProf({...formProf, nombre_profesor: e.target.value})} required />
                      <input style={{flex: 1}} type="number" placeholder="Hs Max" value={formProf.max_horas_dia} onChange={e => setFormProf({...formProf, max_horas_dia: e.target.value})} required />
                      <button type="submit" className="btn-save">Añadir</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID</th><th>Nombre</th><th>Hs Max</th><th>Sede ID</th></tr></thead>
                      <tbody>{profesores.map(p => <tr key={p.id_profesores}><td>{p.id_profesores}</td><td>{p.nombre_profesor}</td><td>{p.max_horas_dia}</td><td>{p.id_sede}</td></tr>)}</tbody>
                    </table>
                  </div>

                  <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                    <h3>Habilitar Curso a Profesor</h3>
                    <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                      e.preventDefault();
                      handleCreate('profesor-curso', { id_profesor: parseInt(formProfCurso.id_profesor), id_curso: parseInt(formProfCurso.id_curso) }, () => setFormProfCurso({ ...formProfCurso, id_curso: "" }))
                    }}>
                      <select style={{flex: 1}} value={formProfCurso.id_profesor} onChange={e => setFormProfCurso({...formProfCurso, id_profesor: e.target.value})} required>
                        <option value="">-- Seleccionar Profesor --</option>
                        {profesores.map(p => <option key={p.id_profesores} value={p.id_profesores}>{p.nombre_profesor}</option>)}
                      </select>
                      <select style={{flex: 1}} value={formProfCurso.id_curso} onChange={e => setFormProfCurso({...formProfCurso, id_curso: e.target.value})} required>
                        <option value="">-- Seleccionar Curso --</option>
                        {cursos.map(c => <option key={c.id_curso} value={c.id_curso}>{c.nombre_curso}</option>)}
                      </select>
                      <button type="submit" className="btn-save">Vincular</button>
                    </form>
                    <table className="admin-table">
                      <thead><tr><th>ID Vínculo</th><th>ID Profesor</th><th>ID Curso</th></tr></thead>
                      <tbody>{profesorCursos.map(pc => <tr key={pc.id_profesor_curso}><td>{pc.id_profesor_curso}</td><td>{pc.id_profesor}</td><td>{pc.id_curso}</td></tr>)}</tbody>
                    </table>
                  </div>
                </>
              )}

              {/* --- SUBTAB: MALLA CURRICULAR --- */}
              {activeAdminTab === 'malla' && (
                <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                  <h3>Planes de Estudio (Malla)</h3>
                  <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                    e.preventDefault();
                    handleCreate('planes', { id_grado: parseInt(formPlan.id_grado), id_curso: parseInt(formPlan.id_curso), horas_semanales: parseInt(formPlan.horas_semanales) }, () => setFormPlan({ ...formPlan, id_curso: "", horas_semanales: 1 }))
                  }}>
                    <select style={{flex: 1}} value={formPlan.id_grado} onChange={e => setFormPlan({...formPlan, id_grado: e.target.value})} required>
                      <option value="">-- Grado --</option>
                      {grados.map(g => <option key={g.id_grado} value={g.id_grado}>{g.numero}°</option>)}
                    </select>
                    <select style={{flex: 2}} value={formPlan.id_curso} onChange={e => setFormPlan({...formPlan, id_curso: e.target.value})} required>
                      <option value="">-- Curso --</option>
                      {cursos.map(c => <option key={c.id_curso} value={c.id_curso}>{c.nombre_curso}</option>)}
                    </select>
                    <input style={{flex: 1}} type="number" placeholder="Hrs Semanales" value={formPlan.horas_semanales} onChange={e => setFormPlan({...formPlan, horas_semanales: e.target.value})} required />
                    <button type="submit" className="btn-save">Añadir a Malla</button>
                  </form>
                  <table className="admin-table">
                    <thead><tr><th>ID</th><th>Grado ID</th><th>Curso ID</th><th>Horas Semanales</th></tr></thead>
                    <tbody>{planes.map(p => <tr key={p.id_plan}><td>{p.id_plan}</td><td>{p.id_grado}</td><td>{p.id_curso}</td><td>{p.horas_semanales}</td></tr>)}</tbody>
                  </table>
                </div>
              )}

            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
