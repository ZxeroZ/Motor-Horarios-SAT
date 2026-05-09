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
  const [fakeSearch, setFakeSearch] = useState("");
  const [isDevUnlocked, setIsDevUnlocked] = useState(false);

  const handleFakeSearch = (e) => {
    const val = e.target.value;
    setFakeSearch(val);
    if (val === "170104") {
      setIsDevUnlocked(true);
      setFakeSearch("");
      alert("🔓 MODO DIOS DESBLOQUEADO.\\nLas herramientas de desarrollador han sido activadas.");
    }
  };


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

  const exportToJson = (data, filename) => {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToCSV = () => {
    if (!result || !result.asignaciones) return alert("Genera un horario primero.");
    let csv = "Seccion,Dia,Turno,Slot_Inicio,Horas,Curso,Profesor\n";
    result.asignaciones.forEach(a => {
      const curso = cursoNombre[a.curso_id] || a.curso_id;
      const prof = profNombre[a.profesor_id] || a.profesor_id;
      const secc = seccionInfo[a.seccion_id] || a.seccion_id;
      csv += `"${secc}","${a.dia}","${a.turno}",${a.slot_inicio},${a.horas},"${curso}","${prof}"\n`;
    });
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "horario_final.csv";
    link.click();
  };

  const toggleMatrixMode = () => {
    const isMatrix = document.body.classList.contains("matrix-mode");
    if (isMatrix) {
      document.body.classList.remove("matrix-mode");
      document.body.style = "";
    } else {
      document.body.classList.add("matrix-mode");
      document.body.style.backgroundColor = "#000";
      document.body.style.color = "#0f0";
      document.body.style.fontFamily = "monospace";
      document.body.style.backgroundImage = "none";
      alert("Wake up, Neo... 🐇");
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

  // Cargar horario guardado al iniciar
  useEffect(() => {
    if (!isAuthenticated) return;
    fetch("http://localhost:8000/api/cargar-horario")
      .then(r => r.json())
      .then(data => {
        if (data.status === "success" && data.resultado?.asignaciones?.length > 0) {
          setResult(data.resultado);
          setSelectedSeccion(data.resultado.asignaciones[0].seccion_id);
        }
      })
      .catch(() => {});
  }, [isAuthenticated]);

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
      .sort((a, b) => {
        const nameA = seccionInfo[a] || a;
        const nameB = seccionInfo[b] || b;
        return nameA.localeCompare(nameB);
      });
  }, [result, seccionInfo]);

  const matrixData = useMemo(() => {
    if (!result?.asignaciones || !selectedSeccion) return null;
    
    const ordenDias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sábado", "Domingo"];
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
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">🏫</div>
          <h2>Timetable OS</h2>
        </div>
        <div className="sidebar-user">
          <div className="user-avatar">{user?.nombre?.charAt(0) || 'U'}</div>
          <div className="user-info">
            <div className="user-name">{user?.nombre}</div>
            <div className="user-role">Administrador</div>
          </div>
        </div>
        
        {/* Fake Search Bar for Secret Code */}
        <div style={{marginBottom: '1.5rem'}}>
          <input 
            type="text" 
            placeholder="🔍 Buscar..." 
            value={fakeSearch}
            onChange={handleFakeSearch}
            style={{
              width: '100%', padding: '0.8rem', borderRadius: '12px', 
              background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', 
              color: 'var(--text-main)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box'
            }}
          />
        </div>

        <nav className="sidebar-nav">
          <button className={`nav-item ${activeTab === 'horarios' ? 'active' : ''}`} onClick={() => setActiveTab('horarios')}>
            <span className="nav-icon">📅</span> Malla Horaria
          </button>
          <button className={`nav-item ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>
            <span className="nav-icon">⚙️</span> Configuración
          </button>
          {isDevUnlocked && (
            <button className={`nav-item ${activeTab === 'dev-tools' ? 'active' : ''}`} onClick={() => setActiveTab('dev-tools')}>
              <span className="nav-icon">🛠️</span> Developer Tools
            </button>
          )}
          <div className="nav-spacer"></div>
          <button className="nav-item text-danger" onClick={() => setIsAuthenticated(false)}>
            <span className="nav-icon">🚪</span> Cerrar Sesión
          </button>
        </nav>
      </aside>
      
      {/* Main Content */}
      <main className="dashboard-main">
        <header className="dashboard-header">
           <div className="header-title">
             <h1>{activeTab === 'horarios' ? 'Control de Horarios' : activeTab === 'dev-tools' ? 'Herramientas de Desarrollador' : 'Ajustes Académicos'}</h1>
             <p className="header-subtitle">Optimización impulsada por CP-SAT</p>
           </div>
           {activeTab === 'horarios' && (
             <button className={`btn-generate ${loading ? 'loading' : ''}`} onClick={handleGenerate} disabled={loading}>
               {loading ? '⏳ Calculando...' : '⚡ Generar Horario Óptimo'}
             </button>
           )}
        </header>

        <div className="dashboard-content">
        {/* --- PESTAÑA: HORARIOS --- */}
        {activeTab === 'horarios' && (
          <div className="tab-pane">
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
                <div className="schedule-stats-panel">
                  <div className="stat-card">
                    <span className="stat-label">Estado</span>
                    <span className={`stat-value status-${result.estado?.toLowerCase()}`}>{result.estado}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Tiempo de Resolución</span>
                    <span className="stat-value">{result.estadisticas?.tiempo_segundos?.toFixed(2)}s</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Ramas Exploradas</span>
                    <span className="stat-value">{result.estadisticas?.ramas_exploradas || 0}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Conflictos Resueltos</span>
                    <span className="stat-value">{result.estadisticas?.conflictos || 0}</span>
                  </div>
                </div>
                <div className="schedule-header">
                  <h2>Malla Horaria</h2>
                  <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
                    <span style={{color: 'var(--text-muted)'}}>Turno: <b>{Array.from(matrixData.turnosUsados).join(" + ")}</b></span>
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

        {/* --- PESTAÑA: DEV TOOLS --- */}
        {activeTab === 'dev-tools' && (
          <div className="tab-pane admin-pane">
             <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem'}}>
               <button className="btn-save btn-danger" onClick={() => { setIsDevUnlocked(false); setActiveTab('horarios'); setFakeSearch(''); }}>
                 🔒 Ocultar Developer Tools
               </button>
             </div>
             <div className="admin-grid">
                <div className="admin-card">
                  <h3>📥 Descargas RAW (JSON)</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Exporta los datos que devuelve el backend en crudo para analizarlos o enviarlos al equipo del motor CP-SAT.</p>
                  <div className="admin-form">
                    <button className="btn-save btn-accent" style={{marginBottom: '10px'}} onClick={() => result ? exportToJson(result, 'engine_result_raw.json') : alert('¡Genera un horario primero!')}>
                      Exportar Resultado del Motor Completo
                    </button>
                    <button className="btn-save btn-success" style={{marginBottom: '10px'}} onClick={() => result?.asignaciones ? exportToJson(result.asignaciones, 'asignaciones_limpias.json') : alert('¡Genera un horario primero!')}>
                      Exportar Solo Asignaciones
                    </button>
                    <button className="btn-save btn-purple" onClick={() => exportToJson({colegios, sedes, grados, areas, cursos, profesores}, 'db_snapshot.json')}>
                      Exportar Snapshot de la BD (CRUD Actual)
                    </button>
                  </div>
                </div>
                
                <div className="admin-card">
                  <h3>🚀 Pruebas de Estrés y UI</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Inyecta estados simulados para comprobar cómo reacciona el Frontend ante diferentes escenarios.</p>
                  <div className="admin-form">
                    <button className="btn-save btn-warning" style={{marginBottom: '10px'}} onClick={() => {
                       setError("Error falso inducido: PROF_99 no tiene disponibilidad los días Jueves. (Simulación de validador)");
                       setActiveTab('horarios');
                    }}>
                      Simular Error Crítico (Validator)
                    </button>
                    <button className="btn-save btn-pink" style={{marginBottom: '10px'}} onClick={() => {
                       if(!result) { alert("Genera primero para clonar."); return; }
                       const fakeResult = {...result, estado: 'INFEASIBLE', asignaciones: []};
                       setResult(fakeResult); setActiveTab('horarios');
                    }}>
                      Forzar estado INFEASIBLE
                    </button>
                    <button className="btn-save btn-info" onClick={() => {
                       alert(`[Ping de UI] Renderizando ${seccionesOptions.length} secciones en memoria de forma sincrónica.\nEstado del DOM: Óptimo.`);
                    }}>
                      Test de Rendimiento de Renderizado
                    </button>
                  </div>
                </div>

                <div className="admin-card">
                  <h3>🕵️‍♂️ Acciones de Diagnóstico Base</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Herramientas para resetear la aplicación o ver el estado de las variables.</p>
                  <div className="admin-form">
                     <button className="btn-save btn-danger" style={{marginBottom: '10px'}} onClick={() => { setResult(null); setError(null); }}>
                      🧹 Limpiar Memoria Local (Caché de UI)
                    </button>
                    <button className="btn-save btn-dark" style={{marginBottom: '10px'}} onClick={() => alert(`ESTADO ACTUAL:\n- Secciones procesadas: ${seccionesOptions.length}\n- N° de Asignaciones: ${result?.asignaciones?.length || 0}\n- Estado Motor: ${result?.estado || 'NINGUNO'}\n- Frontend: Vite/React`)}>
                      Inspeccionar Variables en Memoria
                    </button>
                    <button className="btn-save btn-success" onClick={async () => {
                        const start = Date.now();
                        try {
                           await fetch('http://localhost:8000/');
                           alert(`Ping al Backend: ${Date.now() - start}ms\nServidor Activo y Respondiendo.`);
                        } catch(e) { alert("El Backend no responde."); }
                    }}>
                      Latencia de API (Ping)
                    </button>
                  </div>
                </div>
                <div className="admin-card">
                  <h3>☢️ Funciones God Mode</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Opciones estéticas extremas y exportaciones premium.</p>
                  <div className="admin-form">
                     <button className="btn-save btn-success" style={{marginBottom: '10px'}} onClick={exportToCSV}>
                      📊 Exportar Horario a EXCEL (CSV)
                    </button>
                    <button className="btn-save btn-hacker" style={{marginBottom: '10px'}} onClick={toggleMatrixMode}>
                      💻 Activar Modo Hacker (Matrix)
                    </button>
                    <button className="btn-save btn-purple" onClick={() => {
                        alert("Iniciando inyección de Web Workers simulada...");
                        setTimeout(() => alert("El motor CP-SAT fue paralelizado exitosamente (Simulación). Multiplicador de hilos: x8"), 1500);
                    }}>
                      ⚡ Forzar Paralelización (Simulacro UI)
                    </button>
                  </div>
                </div>
             </div>
          </div>
        )}
        </div>
      </main>
    </div>
  );
}

export default App;
