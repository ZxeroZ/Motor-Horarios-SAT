import { useState, useEffect } from 'react';

export default function ScheduleAnalysis() {
  const [summary, setSummary] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, analysisRes] = await Promise.all([
        fetch('http://localhost:8000/api/horario-summary'),
        fetch('http://localhost:8000/api/horario-analysis')
      ]);
      
      const summaryData = await summaryRes.json();
      const analysisData = await analysisRes.json();
      
      if (summaryData.error) {
        setError(summaryData.error);
      } else {
        setSummary(summaryData);
        setAnalysis(analysisData);
      }
    } catch (err) {
      setError('Error al cargar los datos del horario');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="analysis-container">
        <div className="analysis-loading">
          <span className="material-icons-outlined spinning">refresh</span>
          <p>Cargando análisis del horario...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-container">
        <div className="analysis-error">
          <span className="material-icons-outlined">error_outline</span>
          <p>{error}</p>
          <button onClick={loadData} className="btn-save">Reintentar</button>
        </div>
      </div>
    );
  }

  if (!summary || !analysis) {
    return null;
  }

  const { metricas, carga_por_dia, carga_por_turno, profesores, secciones } = summary;
  const { explicaciones_metricas, problemas_detectados, sugerencias, resumen_rapido } = analysis;

  return (
    <div className="analysis-container">
      {/* Header */}
      <div className="analysis-header">
        <h2>Análisis del Horario</h2>
        <button onClick={loadData} className="btn-save">
          <span className="material-icons-outlined" style={{fontSize: '1rem', verticalAlign: 'middle', marginRight: '4px'}}>refresh</span>
          Actualizar
        </button>
      </div>

      {/* Resumen Rápido */}
      <div className="analysis-section">
        <h3>Resumen Rápido</h3>
        <div className="quick-stats">
          <div className="stat-card">
            <span className="stat-value">{metricas.total_clases}</span>
            <span className="stat-label">Total Clases</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{metricas.total_profesores}</span>
            <span className="stat-label">Profesores</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{metricas.total_secciones}</span>
            <span className="stat-label">Secciones</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{metricas.tiempo_segundos}s</span>
            <span className="stat-label">Tiempo Cálculo</span>
          </div>
        </div>
      </div>

      {/* Métricas y Explicaciones */}
      <div className="analysis-section">
        <h3>Métricas del Motor</h3>
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="metric-label">Estado:</span>
            <span className={`metric-value status-${metricas.estado?.toLowerCase()}`}>{metricas.estado}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Ramas Exploradas:</span>
            <span className="metric-value">{metricas.ramas_exploradas?.toLocaleString() || 0}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Conflictos:</span>
            <span className="metric-value">{metricas.conflictos || 0}</span>
          </div>
        </div>
        <div className="explanations-list">
          {explicaciones_metricas.map((exp, idx) => (
            <div key={idx} className="explanation-item">
              <span className="material-icons-outlined">info</span>
              <p>{exp}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Carga por Día */}
      <div className="analysis-section">
        <h3>Carga por Día</h3>
        <div className="charge-bars">
          {Object.entries(carga_por_dia).map(([dia, horas]) => (
            <div key={dia} className="charge-bar-item">
              <span className="bar-label">{dia}</span>
              <div className="bar-container">
                <div 
                  className="bar-fill" 
                  style={{ width: `${(horas / Math.max(...Object.values(carga_por_dia))) * 100}%` }}
                />
              </div>
              <span className="bar-value">{horas}h</span>
            </div>
          ))}
        </div>
      </div>

      {/* Carga por Turno */}
      <div className="analysis-section">
        <h3>Carga por Turno</h3>
        <div className="turn-cards">
          {Object.entries(carga_por_turno).map(([turno, horas]) => (
            <div key={turno} className="turn-card">
              <span className="turn-name">{turno}</span>
              <span className="turn-hours">{horas} horas</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Profesores */}
      <div className="analysis-section">
        <h3>Profesores (por carga)</h3>
        <div className="professor-list">
          {profesores.slice(0, 10).map((prof, idx) => (
            <div key={idx} className="professor-item">
              <div className="prof-header">
                <span className="prof-name">{prof.nombre}</span>
                <span className="prof-hours">{prof.horas_semana}h/semana</span>
              </div>
              <div className="prof-details">
                <span>Cursos: {prof.cursos.join(', ')}</span>
                <span>Secciones: {prof.secciones.join(', ')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Problemas Detectados */}
      {problemas_detectados.length > 0 && (
        <div className="analysis-section problems-section">
          <h3>Problemas Detectados</h3>
          <div className="problems-list">
            {problemas_detectados.map((problema, idx) => (
              <div key={idx} className="problem-item">
                <span className="material-icons-outlined">warning</span>
                <p>{problema}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sugerencias */}
      {sugerencias.length > 0 && (
        <div className="analysis-section suggestions-section">
          <h3>Sugerencias</h3>
          <div className="suggestions-list">
            {[...new Set(sugerencias)].map((sugerencia, idx) => (
              <div key={idx} className="suggestion-item">
                <span className="material-icons-outlined">lightbulb</span>
                <p>{sugerencia}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Secciones */}
      <div className="analysis-section">
        <h3>Resumen por Secciones</h3>
        <div className="sections-grid">
          {secciones.map((sec, idx) => (
            <div key={idx} className="section-card">
              <h4>{sec.nombre}</h4>
              <p className="section-hours">{sec.clases} clases/semana</p>
              <div className="section-days">
                {Object.entries(sec.dias).map(([dia, horas]) => (
                  <span key={dia} className="day-badge">{dia}: {horas}h</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
