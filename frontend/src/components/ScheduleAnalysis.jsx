import { useState, useEffect } from 'react';

export default function ScheduleAnalysis() {
  const [summary, setSummary] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);

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
    } catch {
      setError('No se pudo conectar al servidor. Verificá que el backend esté activo.');
    }
    setLoading(false);
  };

  const handleAIAnalysis = async () => {
    setAiLoading(true);
    setAiError(null);
    setAiAnalysis(null);
    try {
      const res = await fetch('http://localhost:8000/api/horario-ai-analysis', {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setAiAnalysis(data.analisis);
      } else {
        setAiError(data.detail || 'Error al obtener análisis de la IA');
      }
    } catch {
      setAiError('No se pudo conectar con el servidor. Verificá que el backend esté activo.');
    }
    setAiLoading(false);
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

  if (!summary || !analysis) return null;

  const { metricas, carga_por_dia, profesores } = summary;
  const { problemas_detectados, sugerencias } = analysis;

  // Build executive summary
  const totalBloques = metricas.total_clases;
  const totalHoras = Object.values(carga_por_dia).reduce((a, b) => a + b, 0);
  const numProf = metricas.total_profesores;
  const numSec = metricas.total_secciones;
  const estado = metricas.estado || 'N/A';

  const estadoLabel = {
    'OPTIMAL': 'una solución óptima',
    'FEASIBLE': 'una solución válida',
    'INFEASIBLE': 'un problema (sin solución)',
    'UNKNOWN': 'un resultado inconcluso'
  }[estado] || 'un resultado';

  const tiempo = metricas.tiempo_segundos;
  const tiempoStr = tiempo < 1 ? 'menos de 1 segundo' : tiempo < 60 ? `${tiempo.toFixed(1)} segundos` : `${(tiempo / 60).toFixed(1)} minutos`;

  // Build director-friendly problems
  const problemasDirector = [];
  if (problemas_detectados && problemas_detectados.length > 0) {
    problemas_detectados.forEach((p) => {
      const match = p.match(/^(.+?): (\d+)h en (\w+) \(promedio ([\d.]+)h\/día\)/);
      if (match) {
        const [, nombre, horas, dia, promedio] = match;
        const horasNum = parseInt(horas);
        const promedioNum = parseFloat(promedio);
        const exceso = horasNum - Math.round(promedioNum);
        const profesor = profesores.find(pr => pr.nombre === nombre);
        const cursos = profesor ? profesor.cursos.join(', ') : '';
        let severidad = 'advertencia';
        let accion = '';
        if (horasNum >= 7) {
          severidad = 'urgente';
          accion = `Distribuir al menos ${Math.ceil(exceso / 2)} horas en otro día para evitar cansancio y mejorar la calidad de enseñanza.`;
        } else {
          accion = `Considerar mover ${exceso > 2 ? 2 : 1} hora(s) a otro día con menos carga.`;
        }
        problemasDirector.push({
          nombre,
          horas: horasNum,
          dia,
          promedio: promedioNum,
          cursos,
          severidad,
          accion,
          texto: `${nombre} tiene ${horasNum} horas de clase concentradas un solo día (${dia}), cuando lo ideal serían máximo ${Math.round(promedioNum) + 2} horas. Esto puede generar cansancio y afectar la calidad de las clases.`
        });
      }
    });
  }

  // Build distribution insight
  const diasOrden = ['Lunes', 'Martes', 'Miercoles', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Sabado', 'Domingo'];
  const diasOrdenados = Object.entries(carga_por_dia)
    .sort((a, b) => diasOrden.indexOf(a[0]) - diasOrden.indexOf(b[0]));
  const maxDia = diasOrdenados.reduce((a, b) => b[1] > a[1] ? b : a, diasOrdenados[0]);
  const minDia = diasOrdenados.reduce((a, b) => a[1] < b[1] ? a : b, diasOrdenados[0]);
  const promedioDia = totalHoras / Object.keys(carga_por_dia).length;
  const diasActivos = Object.keys(carga_por_dia).length;

  return (
    <div className="analysis-container">
      {/* Executive Summary */}
      <div className="executive-summary">
        <div className="exec-icon">
          {problemasDirector.length === 0 ? (
            <span className="material-icons-outlined">check_circle</span>
          ) : problemasDirector.some(p => p.severidad === 'urgente') ? (
            <span className="material-icons-outlined">warning</span>
          ) : (
            <span className="material-icons-outlined">info</span>
          )}
        </div>
        <div className="exec-text">
          <p>
            Se programaron <strong>{totalBloques} clases</strong> ({totalHoras} horas/semana) para{' '}
            <strong>{numSec} secciones</strong> con <strong>{numProf} profesores</strong>.{' '}
            El motor encontró {estadoLabel} en {tiempoStr}.
            {problemasDirector.length === 0
              ? ' No se detectaron problemas. El horario está listo para usar.'
              : ` Se detectaron ${problemasDirector.length} punto${problemasDirector.length > 1 ? 's' : ''} de atención.`
            }
          </p>
        </div>
      </div>

      {/* AI Analysis Button */}
      <div className="ai-section">
        <button
          className="ai-button"
          onClick={handleAIAnalysis}
          disabled={aiLoading}
        >
          {aiLoading ? (
            <>
              <span className="material-icons-outlined spinning">hourglass_empty</span>
              Analizando con IA...
            </>
          ) : (
            <>
              <span className="material-icons-outlined">auto_awesome</span>
              Analizar con IA
            </>
          )}
        </button>
        {aiError && (
          <div className="ai-error">
            <span className="material-icons-outlined">error_outline</span>
            <p>{aiError}</p>
          </div>
        )}
        {aiAnalysis && (
          <div className="ai-response">
            <div className="ai-response-header">
              <span className="material-icons-outlined">auto_awesome</span>
              <h3>Análisis de Inteligencia Artificial</h3>
            </div>
            <div className="ai-response-content">
              {aiAnalysis.split('\n').map((line, i) => (
                <p key={i}>{line || '\u00A0'}</p>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">📚</span>
          <span className="stat-number">{totalBloques}</span>
          <span className="stat-label">Clases Programadas</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">👨‍🏫</span>
          <span className="stat-number">{numProf}</span>
          <span className="stat-label">Profesores</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🏫</span>
          <span className="stat-number">{numSec}</span>
          <span className="stat-label">Secciones</span>
        </div>
        <div className={`stat-card ${estado === 'OPTIMAL' ? 'stat-success' : estado === 'INFEASIBLE' ? 'stat-danger' : 'stat-warning'}`}>
          <span className="stat-icon">{estado === 'OPTIMAL' ? '✅' : estado === 'INFEASIBLE' ? '❌' : '⚠️'}</span>
          <span className="stat-number">{estado}</span>
          <span className="stat-label">Estado del Motor</span>
        </div>
      </div>

      {/* Problems - Director Friendly */}
      {problemasDirector.length > 0 && (
        <div className="problems-section">
          <h3>Puntos de Atención</h3>
          <p className="section-subtitle">Situaciones que podrían mejorarse para un mejor horario</p>
          <div className="problems-list">
            {problemasDirector.map((p, idx) => (
              <div key={idx} className={`problem-card problem-${p.severidad}`}>
                <div className="problem-header">
                  <span className="material-icons-outlined">
                    {p.severidad === 'urgente' ? 'error' : 'info'}
                  </span>
                  <span className="problem-title">
                    {p.severidad === 'urgente' ? 'Sobrecarga' : 'Mejorable'} — {p.nombre}
                  </span>
                </div>
                <p className="problem-text">{p.texto}</p>
                {p.cursos && <p className="problem-detail">Dicta: {p.cursos}</p>}
                <div className="problem-action">
                  <span className="material-icons-outlined">arrow_forward</span>
                  <strong>Acción sugerida:</strong> {p.accion}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weekly Distribution */}
      {diasActivos > 1 && (
        <div className="distribution-section">
          <h3>Distribución Semanal</h3>
          <div className="distribution-bars">
            {diasOrdenados.map(([dia, horas]) => {
              const pct = (horas / maxDia[1]) * 100;
              const esMax = horas === maxDia[1];
              const esMin = horas === minDia[1] && horas < promedioDia * 0.5;
              return (
                <div key={dia} className={`dist-row ${esMax ? 'dist-max' : ''} ${esMin ? 'dist-min' : ''}`}>
                  <span className="dist-label">{dia}</span>
                  <div className="dist-bar-wrap">
                    <div className="dist-bar" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="dist-value">{horas}h</span>
                </div>
              );
            })}
          </div>
          <p className="distribution-note">
            {maxDia[1] > minDia[1] * 2
              ? `${maxDia[0]} es el día más cargado (${maxDia[1]}h) y ${minDia[0]} tiene muy poca actividad (${minDia[1]}h). Podría considerar redistribuir.`
              : `${maxDia[0]} es el día más cargado con ${maxDia[1]} horas.`
            }
          </p>
        </div>
      )}

      {/* No problems message */}
      {problemasDirector.length === 0 && (
        <div className="all-good-section">
          <span className="material-icons-outlined">thumb_up</span>
          <h3>¡Todo listo!</h3>
          <p>El horario está bien distribuido. No hay profesores con sobrecarga ni desequilibrios importantes.</p>
        </div>
      )}
    </div>
  );
}
