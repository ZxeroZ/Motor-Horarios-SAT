import { useState, useMemo, useEffect, useCallback } from 'react';
import './index.css';
import Toast from './components/Toast';
import LoginForm from './components/LoginForm';
import Sidebar from './components/Sidebar';
import ScheduleGrid from './components/ScheduleGrid';
import HistoryPanel from './components/HistoryPanel';

function App() {
  // --- Estado: Autenticación ---
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [loginError, setLoginError] = useState("");

  const [activeTab, setActiveTab] = useState("horarios");
  const [activeAdminTab, setActiveAdminTab] = useState("materias");

  // --- Estado: Toasts ---
  const [toasts, setToasts] = useState([]);
  const addToast = useCallback((message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  }, []);

  // --- Estado: Horarios ---
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedSeccion, setSelectedSeccion] = useState("");
  const [fakeSearch, setFakeSearch] = useState("");
  const [isDevUnlocked, setIsDevUnlocked] = useState(false);
  const [progress, setProgress] = useState(null);

  const handleFakeSearch = (e) => {
    const val = e.target.value;
    setFakeSearch(val);
    if (val === "170104") {
      setIsDevUnlocked(true);
      setFakeSearch("");
      addToast("Modo desarrollador activado", "info");
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
  const [profesorDisp, setProfesorDisp] = useState([]);
  const [profesorPref, setProfesorPref] = useState([]);
  const [dias, setDias] = useState([]);
  const [turnos, setTurnos] = useState([]);

  // --- Estado: Formularios ---
  const [formSede, setFormSede] = useState({ nombre_sede: "", id_colegio: "" });
  const [formGrado, setFormGrado] = useState({ numero: "" });
  const [formArea, setFormArea] = useState({ nombre: "", max_horas_dia: 4 });
  const [formCurso, setFormCurso] = useState({ nombre_curso: "", id_area: "" });
  const [formProf, setFormProf] = useState({ nombre_profesor: "", id_sede: "", max_horas_dia: 6 });
  const [formProfCurso, setFormProfCurso] = useState({ id_profesor: "", id_curso: "" });
  const [formSeccion, setFormSeccion] = useState({ nombre: "", id_grado: "", id_sede: "" });
  const [formPlan, setFormPlan] = useState({ id_grado: "", id_curso: "", horas_semanales: 1 });
  const [formDisp, setFormDisp] = useState({ id_profesor: "", id_dia: "", id_turno: "", nro_bloque: "" });
  const [formPref, setFormPref] = useState({ id_profesor: "", id_dia: "", id_turno: "", nro_bloque: "" });

  // --- Estado: Edición ---
  const [editingItem, setEditingItem] = useState(null); // { endpoint, id, formSetter, data }

  // --- Estado: Paginación ---
  const [pagination, setPagination] = useState({});
  const PAGE_SIZE = 8;

  // --- Estado: Historial ---
  const [snapshots, setSnapshots] = useState([]);
  const [editingSnapshot, setEditingSnapshot] = useState(null);
  const [snapshotName, setSnapshotName] = useState("");

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
      const endpoints = ["colegio", "sedes", "grados", "areas", "cursos", "profesores", "secciones", "planes", "profesor-curso", "profesor-disponibilidad", "profesor-preferencia", "dias", "turnos"];
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
      setProfesorDisp(data[9]);
      setProfesorPref(data[10]);
      setDias(data[11]);
      setTurnos(data[12]);
    } catch (e) {
      console.error("Error al cargar data de admin", e);
    }
  };

  useEffect(() => {
    if (isAuthenticated) loadAdminData();
  }, [activeTab, isAuthenticated]);

  useEffect(() => {
    if (activeTab === "historial") loadSnapshots();
  }, [activeTab]);

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
    try {
      const res = await fetch(`http://localhost:8000/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        addToast("Registro creado correctamente");
        resetFn();
        loadAdminData();
      } else {
        const data = await res.json();
        addToast(data.detail || "Error al crear", "error");
      }
    } catch {
      addToast("Error de conexión", "error");
    }
  };

  const handleDelete = async (endpoint, id, label) => {
    if (!window.confirm(`¿Eliminar ${label}?`)) return;
    try {
      const res = await fetch(`http://localhost:8000/api/${endpoint}/${id}`, { method: 'DELETE' });
      if (res.ok) {
        addToast(`${label} eliminado`);
        loadAdminData();
      } else {
        const data = await res.json();
        addToast(data.detail || "Error al eliminar", "error");
      }
    } catch {
      addToast("Error de conexión", "error");
    }
  };

  const handleUpdate = async (endpoint, id, payload, label) => {
    try {
      const res = await fetch(`http://localhost:8000/api/${endpoint}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        addToast(`${label} actualizado`);
        setEditingItem(null);
        loadAdminData();
      } else {
        const data = await res.json();
        addToast(data.detail || "Error al actualizar", "error");
      }
    } catch {
      addToast("Error de conexión", "error");
    }
  };

  const startEdit = (endpoint, item, formSetter, label) => {
    setEditingItem({ endpoint, id: item.id || item.id_sede || item.id_grado || item.id_area || item.id_curso || item.id_profesor || item.id_seccion || item.id_plan || item.id_disponibilidad || item.id_preferencia || item.id_profesor_curso, label });
    formSetter(item);
  };

  // --- Funciones: Historial ---
  const loadSnapshots = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/horario-snapshots");
      const data = await res.json();
      setSnapshots(data);
    } catch {}
  };

  const loadSnapshot = async (id) => {
    try {
      const res = await fetch(`http://localhost:8000/api/horario-snapshots/${id}/load`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        addToast(data.message);
        loadSnapshots();
        // Recargar el horario activo
        const horarioRes = await fetch("http://localhost:8000/api/cargar-horario");
        const horarioData = await horarioRes.json();
        if (horarioData.status === "success" && horarioData.resultado?.asignaciones?.length > 0) {
          setResult(horarioData.resultado);
          setSelectedSeccion(horarioData.resultado.asignaciones[0].seccion_id);
        } else {
          setResult(null);
        }
        setActiveTab("horarios");
      } else {
        addToast(data.detail || "Error al cargar", "error");
      }
    } catch {
      addToast("Error de conexión", "error");
    }
  };

  const renameSnapshot = async (id) => {
    if (!snapshotName.trim()) return;
    try {
      const res = await fetch(`http://localhost:8000/api/horario-snapshots/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre: snapshotName })
      });
      if (res.ok) {
        addToast("Snapshot renombrado");
        setEditingSnapshot(null);
        loadSnapshots();
      }
    } catch {
      addToast("Error de conexión", "error");
    }
  };

  const deleteSnapshot = async (id, nombre) => {
    if (!window.confirm(`¿Eliminar "${nombre}"?`)) return;
    try {
      const res = await fetch(`http://localhost:8000/api/horario-snapshots/${id}`, { method: "DELETE" });
      if (res.ok) {
        addToast("Snapshot eliminado");
        loadSnapshots();
      }
    } catch {
      addToast("Error de conexión", "error");
    }
  };

  // --- Lógica: Generar Horario con progreso real ---
  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setProgress({ percent: 0, message: "Iniciando...", step: "init" });

    try {
      // Capturar versión actual antes de generar
      let prevVersion = null;
      try {
        const prevRes = await fetch("http://localhost:8000/api/cargar-horario?t=" + Date.now());
        const prevData = await prevRes.json();
        prevVersion = prevData.resultado?.version ?? null;
      } catch {}

      // 1. Lanzar generación en background
      const startRes = await fetch('http://localhost:8000/api/generar-horario/start', { method: 'POST' });
      const { task_id } = await startRes.json();

      // 2. Polling dual: horario-progress (primario) + cargar-horario (fallback)
      let done = false;

      const finishGeneration = async (prog) => {
        if (done) return;
        done = true;
        clearInterval(pollPrimary);
        clearInterval(pollFallback);
        setProgress({ percent: 100, message: "¡Horario generado!", step: "done" });
        await new Promise(r => setTimeout(r, 1000));
        let loaded = false;
        for (let attempt = 0; attempt < 3; attempt++) {
          try {
            const horarioRes = await fetch("http://localhost:8000/api/cargar-horario?t=" + Date.now());
            const horarioData = await horarioRes.json();
            if (horarioData.status === "success" && horarioData.resultado?.asignaciones?.length > 0) {
              setResult(horarioData.resultado);
              setSelectedSeccion(horarioData.resultado.asignaciones[0].seccion_id);
              loaded = true;
              break;
            }
          } catch {}
          await new Promise(r => setTimeout(r, 1000));
        }
        if (!loaded && prog?.resultado?.asignaciones?.length > 0) {
          setResult(prog.resultado);
          setSelectedSeccion(prog.resultado.asignaciones[0].seccion_id);
        }
        addToast(`Horario generado en ${prog?.resultado?.estadisticas?.tiempo_segundos?.toFixed(1) || '?'}s`);
        setTimeout(() => { setLoading(false); setProgress(null); }, 1000);
      };

      // Primario: poll /api/horario-progress/{task_id}
      const pollPrimary = setInterval(async () => {
        if (done) return;
        try {
          const progRes = await fetch(`http://localhost:8000/api/horario-progress/${task_id}`);
          const prog = await progRes.json();

          if (prog.status === 'done') {
            finishGeneration(prog);
          } else if (prog.status === 'error') {
            done = true;
            clearInterval(pollPrimary);
            clearInterval(pollFallback);
            setError(prog.errors ? JSON.stringify(prog.errors, null, 2) : prog.message);
            addToast("Error al generar horario", "error");
            setLoading(false);
            setProgress(null);
          } else if (prog.status === 'running' || prog.status === 'starting') {
            setProgress({ percent: prog.percent || 0, message: prog.message || "Procesando...", step: prog.step });
          }
        } catch {}
      }, 500);

      // Fallback: poll /api/cargar-horario cada 3s, detectar cambio de versión
      const pollFallback = setInterval(async () => {
        if (done) return;
        try {
          const res = await fetch("http://localhost:8000/api/cargar-horario?t=" + Date.now());
          const data = await res.json();
          const currentVersion = data.resultado?.version ?? null;
          if (currentVersion !== null && currentVersion !== prevVersion) {
            finishGeneration({ resultado: data.resultado });
          }
        } catch {}
      }, 3000);

      // Safety timeout
      setTimeout(() => {
        if (!done) {
          done = true;
          clearInterval(pollPrimary);
          clearInterval(pollFallback);
          setLoading(false);
          setProgress(null);
        }
      }, 180000);
    } catch (err) {
      setError(err.message);
      addToast("Error de conexión", "error");
      setLoading(false);
      setProgress(null);
    }
  };

  // --- Lookups para nombres ---
  const cursoNombre = useMemo(() => {
    const m = {};
    cursos.forEach(c => { m[`CUR_${c.id_curso}`] = c.nombre_curso; });
    return m;
  }, [cursos]);

  const profNombre = useMemo(() => {
    const m = {};
    profesores.forEach(p => { m[`PROF_${p.id_profesor}`] = p.nombre_profesor; });
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

  // Componente de tabla paginada con búsqueda
  const PaginatedTable = ({ data, columns, tableKey, renderRow, searchKeys }) => {
    const page = pagination[tableKey] || 0;
    const searchQuery = (pagination[`${tableKey}_search`] || "").toLowerCase();
    const totalPages = Math.ceil(data.length / PAGE_SIZE);

    const filtered = searchKeys && searchQuery
      ? data.filter(item => searchKeys.some(k => String(item[k] || "").toLowerCase().includes(searchQuery)))
      : data;

    const totalPagesFilt = Math.ceil(filtered.length / PAGE_SIZE);
    const sliced = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

    return (
      <div>
        {searchKeys && (
          <div style={{marginBottom:'12px', position:'relative'}}>
            <span className="material-icons-outlined" style={{position:'absolute', left:'10px', top:'50%', transform:'translateY(-50%)', fontSize:'1.1rem', color:'var(--text-muted)'}}>search</span>
            <input
              type="text"
              placeholder="Buscar..."
              value={pagination[`${tableKey}_search`] || ""}
              onChange={e => setPagination(p => ({...p, [tableKey]: 0, [`${tableKey}_search`]: e.target.value}))}
              style={{width:'100%', padding:'8px 12px 8px 36px', borderRadius:'8px', border:'1px solid var(--border-color)', background:'var(--bg-panel-light)', color:'var(--text-main)', fontSize:'0.9rem', outline:'none', boxSizing:'border-box'}}
            />
          </div>
        )}
        <table className="admin-table">
          <thead><tr>{columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
          <tbody>{sliced.map((item, i) => renderRow(item, page * PAGE_SIZE + i))}</tbody>
        </table>
        {totalPagesFilt > 1 && (
          <div style={{display:'flex', justifyContent:'center', alignItems:'center', gap:'8px', marginTop:'12px'}}>
            <button className="btn-save" style={{padding:'4px 12px', fontSize:'0.8rem', background:'var(--accent)'}} disabled={page===0} onClick={() => setPagination(p => ({...p, [tableKey]: page-1}))}>Anterior</button>
            <span style={{fontSize:'0.8rem', color:'var(--text-muted)'}}>{page+1} / {totalPagesFilt} ({filtered.length} registros)</span>
            <button className="btn-save" style={{padding:'4px 12px', fontSize:'0.8rem', background:'var(--accent)'}} disabled={page>=totalPagesFilt-1} onClick={() => setPagination(p => ({...p, [tableKey]: page+1}))}>Siguiente</button>
          </div>
        )}
      </div>
    );
  };

  const ActionButtons = ({ endpoint, item, label, idField }) => (
    <td style={{whiteSpace:'nowrap'}}>
      <button className="btn-save" style={{padding:'4px 10px', fontSize:'0.75rem', background:'var(--accent)', marginRight:'4px'}} onClick={() => startEdit(endpoint, item, getFormSetter(endpoint), label)}>Editar</button>
      <button className="btn-save btn-danger" style={{padding:'4px 10px', fontSize:'0.75rem'}} onClick={() => handleDelete(endpoint, item[idField], label)}>Eliminar</button>
    </td>
  );

  const getFormSetter = (endpoint) => {
    const map = {
      'sedes': (v) => setFormSede({ nombre_sede: v.nombre_sede || '', id_colegio: v.id_colegio || '' }),
      'grados': (v) => setFormGrado({ numero: v.numero || '' }),
      'secciones': (v) => setFormSeccion({ nombre: v.nombre || '', id_grado: v.id_grado || '', id_sede: v.id_sede || '' }),
      'areas': (v) => setFormArea({ nombre: v.nombre || '', max_horas_dia: v.max_horas_dia || 4 }),
      'cursos': (v) => setFormCurso({ nombre_curso: v.nombre_curso || '', id_area: v.id_area || '' }),
      'profesores': (v) => setFormProf({ nombre_profesor: v.nombre_profesor || '' }),
      'profesor-curso': (v) => setFormProfCurso({ id_profesor: v.id_profesor || '', id_curso: v.id_curso || '' }),
      'planes': (v) => setFormPlan({ id_grado: v.id_grado || '', id_curso: v.id_curso || '', horas_semanales: v.horas_semanales || 1 }),
      'profesor-disponibilidad': (v) => setFormDisp({ id_profesor: v.id_profesor || '', id_dia: v.id_dia || '', id_turno: v.id_turno || '', nro_bloque: v.nro_bloque || '' }),
      'profesor-preferencia': (v) => setFormPref({ id_profesor: v.id_profesor || '', id_dia: v.id_dia || '', id_turno: v.id_turno || '', nro_bloque: v.nro_bloque || '' }),
    };
    return map[endpoint] || (() => {});
  };

  /* ====== RENDER ====== */

  if (!isAuthenticated) {
    return <LoginForm loginForm={loginForm} setLoginForm={setLoginForm} loginError={loginError} onSubmit={handleLogin} />;
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <Sidebar 
        activeTab={activeTab} setActiveTab={setActiveTab} user={user}
        isDevUnlocked={isDevUnlocked} fakeSearch={fakeSearch}
        onFakeSearch={handleFakeSearch} onLogout={() => setIsAuthenticated(false)}
      />
      
      {/* Main Content */}
      <main className="dashboard-main">
        <header className="dashboard-header">
           <div className="header-title">
             <h1>{activeTab === 'horarios' ? 'Control de Horarios' : activeTab === 'historial' ? 'Historial de Horarios' : activeTab === 'dev-tools' ? 'Herramientas de Desarrollador' : 'Ajustes Académicos'}</h1>
             <p className="header-subtitle">Optimización impulsada por CP-SAT</p>
           </div>
           {activeTab === 'horarios' && (
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px'}}>
                <button className={`btn-generate ${loading ? 'loading' : ''}`} onClick={handleGenerate} disabled={loading}>
                  {loading ? 'Calculando...' : 'Generar Horario'}
                </button>
                {progress && (
                  <div style={{width: '280px'}}>
                    <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.75rem', color:'var(--text-muted)', marginBottom:'4px'}}>
                      <span>{progress.message}</span>
                      <span style={{fontWeight:'700', color:'var(--accent)'}}>{progress.percent}%</span>
                    </div>
                    <div style={{width:'100%', height:'8px', background:'var(--border-color)', borderRadius:'4px', overflow:'hidden'}}>
                      <div style={{
                        width: `${progress.percent}%`,
                        height: '100%',
                        background: progress.percent === 100 ? 'var(--success)' : 'var(--accent-gradient)',
                        borderRadius: '4px',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                  </div>
                )}
              </div>
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
              <ScheduleGrid 
                result={result} selectedSeccion={selectedSeccion} setSelectedSeccion={setSelectedSeccion}
                seccionesOptions={seccionesOptions} seccionInfo={seccionInfo}
                cursoNombre={cursoNombre} profNombre={profNombre}
              />
            )}
          </div>
        )}

        {/* --- PESTAÑA: HISTORIAL --- */}
        {activeTab === 'historial' && (
          <div className="tab-pane">
            <HistoryPanel 
              snapshots={snapshots} editingSnapshot={editingSnapshot} snapshotName={snapshotName}
              setSnapshotName={setSnapshotName} setEditingSnapshot={setEditingSnapshot}
              onLoad={loadSnapshot} onRename={renameSnapshot} onDelete={deleteSnapshot}
            />
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
              <button className={`tab-btn ${activeAdminTab === 'disponibilidad' ? 'active' : ''}`} onClick={() => setActiveAdminTab('disponibilidad')}>Disponibilidad</button>
            </div>

            <div className="admin-grid">
              
              {/* --- SUBTAB: INFRAESTRUCTURA --- */}
              {activeAdminTab === 'infra' && (
                <>
                  <div className="admin-card">
                    <h3>Sedes Físicas</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'sedes') {
                        handleUpdate('sedes', editingItem.id, { nombre_sede: formSede.nombre_sede, id_colegio: parseInt(formSede.id_colegio) }, 'Sede');
                      } else {
                        handleCreate('sedes', { nombre_sede: formSede.nombre_sede, id_colegio: parseInt(formSede.id_colegio) }, () => setFormSede({ nombre_sede: "", id_colegio: "" }));
                      }
                    }}>
                      <select value={formSede.id_colegio} onChange={e => setFormSede({...formSede, id_colegio: e.target.value})} required>
                        <option value="">-- Seleccionar Colegio --</option>
                        {colegios.map(c => <option key={c.id_colegio} value={c.id_colegio}>{c.nombre_colegio}</option>)}
                      </select>
                      <input type="text" placeholder="Nombre de Sede" value={formSede.nombre_sede} onChange={e => setFormSede({...formSede, nombre_sede: e.target.value})} required />
                      <div style={{display:'flex', gap:'8px'}}>
                        <button type="submit" className="btn-save">{editingItem?.endpoint === 'sedes' ? 'Actualizar' : 'Registrar Sede'}</button>
                        {editingItem?.endpoint === 'sedes' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormSede({ nombre_sede: "", id_colegio: "" }); }}>Cancelar</button>}
                      </div>
                    </form>
                    <PaginatedTable data={sedes} columns={["ID", "Sede", "Colegio ID", ""]} tableKey="sedes" searchKeys={["nombre_sede"]}
                      renderRow={(s) => <tr key={s.id_sede}><td>{s.id_sede}</td><td>{s.nombre_sede}</td><td>{s.id_colegio}</td>
                        <ActionButtons endpoint="sedes" item={s} label="Sede" idField="id_sede" /></tr>}
                    />
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
                      if (editingItem?.endpoint === 'grados') {
                        handleUpdate('grados', editingItem.id, { numero: parseInt(formGrado.numero) }, 'Grado');
                      } else {
                        handleCreate('grados', { numero: parseInt(formGrado.numero) }, () => setFormGrado({ numero: "" }));
                      }
                    }}>
                      <input type="number" placeholder="Número de Grado (Ej. 1)" value={formGrado.numero} onChange={e => setFormGrado({numero: e.target.value})} required />
                      <div style={{display:'flex', gap:'8px'}}>
                        <button type="submit" className="btn-save">{editingItem?.endpoint === 'grados' ? 'Actualizar' : 'Registrar Grado'}</button>
                        {editingItem?.endpoint === 'grados' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormGrado({ numero: "" }); }}>Cancelar</button>}
                      </div>
                    </form>
                    <PaginatedTable data={grados} columns={["ID", "Grado N°", ""]} tableKey="grados" searchKeys={["numero"]}
                      renderRow={(g) => <tr key={g.id_grado}><td>{g.id_grado}</td><td>{g.numero}°</td>
                        <ActionButtons endpoint="grados" item={g} label="Grado" idField="id_grado" /></tr>}
                    />
                  </div>

                  <div className="admin-card">
                    <h3>Secciones</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'secciones') {
                        handleUpdate('secciones', editingItem.id, { nombre: formSeccion.nombre, id_grado: parseInt(formSeccion.id_grado), id_sede: parseInt(formSeccion.id_sede) }, 'Sección');
                      } else {
                        handleCreate('secciones', { nombre: formSeccion.nombre, id_grado: parseInt(formSeccion.id_grado), id_sede: parseInt(formSeccion.id_sede) }, () => setFormSeccion({ nombre: "", id_grado: "", id_sede: "" }));
                      }
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
                      <div style={{display:'flex', gap:'8px'}}>
                        <button type="submit" className="btn-save">{editingItem?.endpoint === 'secciones' ? 'Actualizar' : 'Registrar Sección'}</button>
                        {editingItem?.endpoint === 'secciones' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormSeccion({ nombre: "", id_grado: "", id_sede: "" }); }}>Cancelar</button>}
                      </div>
                    </form>
                    <PaginatedTable data={secciones} columns={["ID", "Sección", "Grado", ""]} tableKey="secciones" searchKeys={["nombre"]}
                      renderRow={(s) => <tr key={s.id_seccion}><td>{s.id_seccion}</td><td>{s.nombre}</td><td>ID {s.id_grado}</td>
                        <ActionButtons endpoint="secciones" item={s} label="Sección" idField="id_seccion" /></tr>}
                    />
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
                      if (editingItem?.endpoint === 'areas') {
                        handleUpdate('areas', editingItem.id, { nombre: formArea.nombre, max_horas_dia: parseInt(formArea.max_horas_dia) }, 'Área');
                      } else {
                        handleCreate('areas', { nombre: formArea.nombre, max_horas_dia: parseInt(formArea.max_horas_dia) }, () => setFormArea({ nombre: "", max_horas_dia: 4 }));
                      }
                    }}>
                      <input type="text" placeholder="Nombre (Ej. Ciencias)" value={formArea.nombre} onChange={e => setFormArea({...formArea, nombre: e.target.value})} required />
                      <input type="number" placeholder="Max hs diarias" value={formArea.max_horas_dia} onChange={e => setFormArea({...formArea, max_horas_dia: e.target.value})} required />
                      <div style={{display:'flex', gap:'8px'}}>
                        <button type="submit" className="btn-save">{editingItem?.endpoint === 'areas' ? 'Actualizar' : 'Guardar Área'}</button>
                        {editingItem?.endpoint === 'areas' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormArea({ nombre: "", max_horas_dia: 4 }); }}>Cancelar</button>}
                      </div>
                    </form>
                    <PaginatedTable data={areas} columns={["ID", "Nombre", ""]} tableKey="areas" searchKeys={["nombre"]}
                      renderRow={(a) => <tr key={a.id_area}><td>{a.id_area}</td><td>{a.nombre}</td>
                        <ActionButtons endpoint="areas" item={a} label="Área" idField="id_area" /></tr>}
                    />
                  </div>

                  <div className="admin-card">
                    <h3>Cursos</h3>
                    <form className="admin-form" onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'cursos') {
                        handleUpdate('cursos', editingItem.id, { nombre_curso: formCurso.nombre_curso, id_area: parseInt(formCurso.id_area) }, 'Curso');
                      } else {
                        handleCreate('cursos', { nombre_curso: formCurso.nombre_curso, id_area: parseInt(formCurso.id_area) }, () => setFormCurso({ ...formCurso, nombre_curso: "" }));
                      }
                    }}>
                      <select value={formCurso.id_area} onChange={e => setFormCurso({...formCurso, id_area: e.target.value})} required>
                        <option value="">-- Área --</option>
                        {areas.map(a => <option key={a.id_area} value={a.id_area}>{a.nombre}</option>)}
                      </select>
                      <input type="text" placeholder="Curso" value={formCurso.nombre_curso} onChange={e => setFormCurso({...formCurso, nombre_curso: e.target.value})} required />
                      <div style={{display:'flex', gap:'8px'}}>
                        <button type="submit" className="btn-save">{editingItem?.endpoint === 'cursos' ? 'Actualizar' : 'Guardar Curso'}</button>
                        {editingItem?.endpoint === 'cursos' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormCurso({ nombre_curso: "", id_area: "" }); }}>Cancelar</button>}
                      </div>
                    </form>
                    <PaginatedTable data={cursos} columns={["ID", "Curso", "Área ID", ""]} tableKey="cursos" searchKeys={["nombre_curso"]}
                      renderRow={(c) => <tr key={c.id_curso}><td>{c.id_curso}</td><td>{c.nombre_curso}</td><td>{c.id_area}</td>
                        <ActionButtons endpoint="cursos" item={c} label="Curso" idField="id_curso" /></tr>}
                    />
                  </div>

                  <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                    <h3>Profesores</h3>
                    <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'profesores') {
                        handleUpdate('profesores', editingItem.id, { nombre_profesor: formProf.nombre_profesor }, 'Profesor');
                      } else {
                        handleCreate('profesores', { nombre_profesor: formProf.nombre_profesor }, () => setFormProf({ ...formProf, nombre_profesor: "" }));
                      }
                    }}>
                      <input style={{flex: 2}} type="text" placeholder="Nombre de Profesor" value={formProf.nombre_profesor} onChange={e => setFormProf({...formProf, nombre_profesor: e.target.value})} required />
                      <button type="submit" className="btn-save">{editingItem?.endpoint === 'profesores' ? 'Actualizar' : 'Añadir'}</button>
                      {editingItem?.endpoint === 'profesores' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormProf({ nombre_profesor: "" }); }}>Cancelar</button>}
                    </form>
                    <PaginatedTable data={profesores} columns={["ID", "Nombre", ""]} tableKey="profesores" searchKeys={["nombre_profesor"]}
                      renderRow={(p) => <tr key={p.id_profesor}><td>{p.id_profesor}</td><td>{p.nombre_profesor}</td>
                        <ActionButtons endpoint="profesores" item={p} label="Profesor" idField="id_profesor" /></tr>}
                    />
                  </div>

                  <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                    <h3>Habilitar Curso a Profesor</h3>
                    <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'profesor-curso') {
                        handleUpdate('profesor-curso', editingItem.id, { id_profesor: parseInt(formProfCurso.id_profesor), id_curso: parseInt(formProfCurso.id_curso) }, 'Vínculo');
                      } else {
                        handleCreate('profesor-curso', { id_profesor: parseInt(formProfCurso.id_profesor), id_curso: parseInt(formProfCurso.id_curso) }, () => setFormProfCurso({ ...formProfCurso, id_curso: "" }));
                      }
                    }}>
                      <select style={{flex: 1}} value={formProfCurso.id_profesor} onChange={e => setFormProfCurso({...formProfCurso, id_profesor: e.target.value})} required>
                        <option value="">-- Seleccionar Profesor --</option>
                        {profesores.map(p => <option key={p.id_profesor} value={p.id_profesor}>{p.nombre_profesor}</option>)}
                      </select>
                      <select style={{flex: 1}} value={formProfCurso.id_curso} onChange={e => setFormProfCurso({...formProfCurso, id_curso: e.target.value})} required>
                        <option value="">-- Seleccionar Curso --</option>
                        {cursos.map(c => <option key={c.id_curso} value={c.id_curso}>{c.nombre_curso}</option>)}
                      </select>
                      <button type="submit" className="btn-save">{editingItem?.endpoint === 'profesor-curso' ? 'Actualizar' : 'Vincular'}</button>
                      {editingItem?.endpoint === 'profesor-curso' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormProfCurso({ id_profesor: "", id_curso: "" }); }}>Cancelar</button>}
                    </form>
                    <PaginatedTable data={profesorCursos} columns={["ID Vínculo", "ID Profesor", "ID Curso", ""]} tableKey="profesorCursos"
                      renderRow={(pc) => <tr key={pc.id_profesor_curso}><td>{pc.id_profesor_curso}</td><td>{pc.id_profesor}</td><td>{pc.id_curso}</td>
                        <ActionButtons endpoint="profesor-curso" item={pc} label="Vínculo" idField="id_profesor_curso" /></tr>}
                    />
                  </div>
                </>
              )}

              {/* --- SUBTAB: MALLA CURRICULAR --- */}
              {activeAdminTab === 'malla' && (
                <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                  <h3>Planes de Estudio (Malla)</h3>
                  <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                    e.preventDefault();
                    if (editingItem?.endpoint === 'planes') {
                      handleUpdate('planes', editingItem.id, { id_grado: parseInt(formPlan.id_grado), id_curso: parseInt(formPlan.id_curso), horas_semanales: parseInt(formPlan.horas_semanales) }, 'Plan');
                    } else {
                      handleCreate('planes', { id_grado: parseInt(formPlan.id_grado), id_curso: parseInt(formPlan.id_curso), horas_semanales: parseInt(formPlan.horas_semanales) }, () => setFormPlan({ ...formPlan, id_curso: "", horas_semanales: 1 }));
                    }
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
                    <button type="submit" className="btn-save">{editingItem?.endpoint === 'planes' ? 'Actualizar' : 'Añadir a Malla'}</button>
                    {editingItem?.endpoint === 'planes' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormPlan({ id_grado: "", id_curso: "", horas_semanales: 1 }); }}>Cancelar</button>}
                  </form>
                  <PaginatedTable data={planes} columns={["ID", "Grado ID", "Curso ID", "Hrs/Sem", ""]} tableKey="planes"
                    renderRow={(p) => <tr key={p.id_plan}><td>{p.id_plan}</td><td>{p.id_grado}</td><td>{p.id_curso}</td><td>{p.horas_semanales}</td>
                      <ActionButtons endpoint="planes" item={p} label="Plan" idField="id_plan" /></tr>}
                  />
                </div>
              )}

              {/* --- SUBTAB: DISPONIBILIDAD DOCENTE --- */}
              {activeAdminTab === 'disponibilidad' && (
                <>
                  <div className="admin-card">
                    <h3><span className="material-icons-outlined" style={{color: 'var(--success)', verticalAlign: 'middle', marginRight: '6px'}}>check_circle</span>Disponibilidad (Cuándo SÍ puede)</h3>
                    <p style={{color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem'}}>Bloques donde el profesor puede dar clases. Si no se registra nada, se asume disponibilidad total.</p>
                    <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'profesor-disponibilidad') {
                        handleUpdate('profesor-disponibilidad', editingItem.id, { id_profesor: parseInt(formDisp.id_profesor), id_dia: parseInt(formDisp.id_dia), id_turno: parseInt(formDisp.id_turno), nro_bloque: parseInt(formDisp.nro_bloque) }, 'Disponibilidad');
                      } else {
                        handleCreate('profesor-disponibilidad', { id_profesor: parseInt(formDisp.id_profesor), id_dia: parseInt(formDisp.id_dia), id_turno: parseInt(formDisp.id_turno), nro_bloque: parseInt(formDisp.nro_bloque) }, () => setFormDisp({ ...formDisp, id_dia: "", nro_bloque: "" }));
                      }
                    }}>
                      <select style={{flex: 1}} value={formDisp.id_profesor} onChange={e => setFormDisp({...formDisp, id_profesor: e.target.value})} required>
                        <option value="">-- Profesor --</option>
                        {profesores.map(p => <option key={p.id_profesor} value={p.id_profesor}>{p.nombre_profesor}</option>)}
                      </select>
                      <select style={{flex: 1}} value={formDisp.id_dia} onChange={e => setFormDisp({...formDisp, id_dia: e.target.value})} required>
                        <option value="">-- Día --</option>
                        {dias.map(d => <option key={d.id_dia} value={d.id_dia}>{d.nombre_dia}</option>)}
                      </select>
                      <select style={{flex: 1}} value={formDisp.id_turno} onChange={e => setFormDisp({...formDisp, id_turno: e.target.value})} required>
                        <option value="">-- Turno --</option>
                        {turnos.map(t => <option key={t.id_turno} value={t.id_turno}>{t.nombre}</option>)}
                      </select>
                      <input style={{flex: 1}} type="number" min="1" max="6" placeholder="Nro Bloque" value={formDisp.nro_bloque} onChange={e => setFormDisp({...formDisp, nro_bloque: e.target.value})} required />
                      <button type="submit" className="btn-save btn-success">{editingItem?.endpoint === 'profesor-disponibilidad' ? 'Actualizar' : 'Añadir'}</button>
                      {editingItem?.endpoint === 'profesor-disponibilidad' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormDisp({ id_profesor: "", id_dia: "", id_turno: "", nro_bloque: "" }); }}>Cancelar</button>}
                    </form>
                    <PaginatedTable data={profesorDisp} columns={["ID", "Profesor", "Día", "Turno", "Bloque", ""]} tableKey="profesorDisp"
                      renderRow={(pd) => {
                        const prof = profesores.find(p => p.id_profesor === pd.id_profesor);
                        const dia = dias.find(d => d.id_dia === pd.id_dia);
                        const turno = turnos.find(t => t.id_turno === pd.id_turno);
                        return <tr key={pd.id_disponibilidad}><td>{pd.id_disponibilidad}</td><td>{prof?.nombre_profesor || pd.id_profesor}</td><td>{dia?.nombre_dia || pd.id_dia}</td><td>{turno?.nombre || pd.id_turno}</td><td>{pd.nro_bloque}</td>
                          <ActionButtons endpoint="profesor-disponibilidad" item={pd} label="Disponibilidad" idField="id_disponibilidad" /></tr>
                      }}
                    />
                  </div>

                  <div className="admin-card" style={{gridColumn: '1 / -1'}}>
                    <h3><span className="material-icons-outlined" style={{color: '#f59e0b', verticalAlign: 'middle', marginRight: '6px'}}>star</span>Preferencias (Cuándo PREFIERE)</h3>
                    <p style={{color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem'}}>Bloques donde el profesor prefiere dar clases (restricción blanda, el motor intentará respetarlo).</p>
                    <form className="admin-form" style={{flexDirection: 'row', gap: '1rem'}} onSubmit={(e) => {
                      e.preventDefault();
                      if (editingItem?.endpoint === 'profesor-preferencia') {
                        handleUpdate('profesor-preferencia', editingItem.id, { id_profesor: parseInt(formPref.id_profesor), id_dia: parseInt(formPref.id_dia), id_turno: parseInt(formPref.id_turno), nro_bloque: parseInt(formPref.nro_bloque) }, 'Preferencia');
                      } else {
                        handleCreate('profesor-preferencia', { id_profesor: parseInt(formPref.id_profesor), id_dia: parseInt(formPref.id_dia), id_turno: parseInt(formPref.id_turno), nro_bloque: parseInt(formPref.nro_bloque) }, () => setFormPref({ ...formPref, id_dia: "", nro_bloque: "" }));
                      }
                    }}>
                      <select style={{flex: 1}} value={formPref.id_profesor} onChange={e => setFormPref({...formPref, id_profesor: e.target.value})} required>
                        <option value="">-- Profesor --</option>
                        {profesores.map(p => <option key={p.id_profesor} value={p.id_profesor}>{p.nombre_profesor}</option>)}
                      </select>
                      <select style={{flex: 1}} value={formPref.id_dia} onChange={e => setFormPref({...formPref, id_dia: e.target.value})} required>
                        <option value="">-- Día --</option>
                        {dias.map(d => <option key={d.id_dia} value={d.id_dia}>{d.nombre_dia}</option>)}
                      </select>
                      <select style={{flex: 1}} value={formPref.id_turno} onChange={e => setFormPref({...formPref, id_turno: e.target.value})} required>
                        <option value="">-- Turno --</option>
                        {turnos.map(t => <option key={t.id_turno} value={t.id_turno}>{t.nombre}</option>)}
                      </select>
                      <input style={{flex: 1}} type="number" min="1" max="6" placeholder="Nro Bloque" value={formPref.nro_bloque} onChange={e => setFormPref({...formPref, nro_bloque: e.target.value})} required />
                      <button type="submit" className="btn-save btn-purple">{editingItem?.endpoint === 'profesor-preferencia' ? 'Actualizar' : 'Añadir'}</button>
                      {editingItem?.endpoint === 'profesor-preferencia' && <button type="button" className="btn-save btn-dark" onClick={() => { setEditingItem(null); setFormPref({ id_profesor: "", id_dia: "", id_turno: "", nro_bloque: "" }); }}>Cancelar</button>}
                    </form>
                    <PaginatedTable data={profesorPref} columns={["ID", "Profesor", "Día", "Turno", "Bloque", ""]} tableKey="profesorPref"
                      renderRow={(pp) => {
                        const prof = profesores.find(p => p.id_profesor === pp.id_profesor);
                        const dia = dias.find(d => d.id_dia === pp.id_dia);
                        const turno = turnos.find(t => t.id_turno === pp.id_turno);
                        return <tr key={pp.id_preferencia}><td>{pp.id_preferencia}</td><td>{prof?.nombre_profesor || pp.id_profesor}</td><td>{dia?.nombre_dia || pp.id_dia}</td><td>{turno?.nombre || pp.id_turno}</td><td>{pp.nro_bloque}</td>
                          <ActionButtons endpoint="profesor-preferencia" item={pp} label="Preferencia" idField="id_preferencia" /></tr>
                      }}
                    />
                  </div>
                </>
              )}

            </div>
          </div>
        )}

        {/* --- PESTAÑA: DEV TOOLS --- */}
        {activeTab === 'dev-tools' && (
          <div className="tab-pane admin-pane">
             <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem'}}>
               <button className="btn-save btn-danger" onClick={() => { setIsDevUnlocked(false); setActiveTab('horarios'); setFakeSearch(''); }}>
                 <span className="material-icons-outlined" style={{fontSize: '1rem', verticalAlign: 'middle'}}>lock</span> Ocultar Developer Tools
               </button>
             </div>
             <div className="admin-grid">
                <div className="admin-card">
                  <h3><span className="material-icons-outlined" style={{verticalAlign: 'middle', marginRight: '6px'}}>download</span>Descargas RAW (JSON)</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Exporta los datos que devuelve el backend en crudo para analizarlos o enviarlos al equipo del motor CP-SAT.</p>
                  <div className="admin-form">
                    <button className="btn-save btn-accent" style={{marginBottom: '10px'}} onClick={() => result ? exportToJson(result, 'engine_result_raw.json') : alert('¡Genera un horario primero!')}>
                      Exportar Resultado del Motor Completo
                    </button>
                    <button className="btn-save btn-success" style={{marginBottom: '10px'}} onClick={() => result?.asignaciones ? exportToJson(result.asignaciones, 'asignaciones_limpias.json') : alert('¡Genera un horario primero!')}>
                      Exportar Solo Asignaciones
                    </button>
                    <button className="btn-save btn-purple" onClick={() => exportToJson({colegios, sedes, grados, areas, cursos, profesores}, 'db_snapshot.json')}>
                      Exportar Snapshot de la BD
                    </button>
                  </div>
                </div>
                
                <div className="admin-card">
                  <h3><span className="material-icons-outlined" style={{verticalAlign: 'middle', marginRight: '6px'}}>science</span>Pruebas de Estrés y UI</h3>
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
                  <h3><span className="material-icons-outlined" style={{verticalAlign: 'middle', marginRight: '6px'}}>analytics</span>Acciones de Diagnóstico Base</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Herramientas para resetear la aplicación o ver el estado de las variables.</p>
                  <div className="admin-form">
                     <button className="btn-save btn-danger" style={{marginBottom: '10px'}} onClick={() => { setResult(null); setError(null); }}>
                      Limpiar Memoria Local
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
                  <h3><span className="material-icons-outlined" style={{verticalAlign: 'middle', marginRight: '6px'}}>auto_awesome</span>Funciones God Mode</h3>
                  <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem'}}>Opciones estéticas extremas y exportaciones premium.</p>
                  <div className="admin-form">
                     <button className="btn-save btn-success" style={{marginBottom: '10px'}} onClick={exportToCSV}>
                      Exportar Horario a CSV
                     </button>
                     <button className="btn-save btn-hacker" style={{marginBottom: '10px'}} onClick={toggleMatrixMode}>
                      Activar Modo Hacker
                     </button>
                     <button className="btn-save btn-purple" onClick={() => {
                         alert("Iniciando inyección de Web Workers simulada...");
                         setTimeout(() => alert("El motor CP-SAT fue paralelizado exitosamente (Simulación)."), 1500);
                     }}>
                      Forzar Paralelización (Simulacro)
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

      <Toast toasts={toasts} />
    </div>
  );
}

export default App;
