export default function HistoryPanel({ snapshots, editingSnapshot, snapshotName, setSnapshotName, setEditingSnapshot, onLoad, onRename, onDelete }) {
  return (
    <div style={{background: '#ffffff', padding: '1.75rem', borderRadius: 'var(--border-radius-lg)', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border-color)'}}>
      <h2 style={{marginTop: 0, marginBottom: '1.5rem', fontWeight: '700', letterSpacing: '-0.02em'}}>Historial de Horarios</h2>
      {snapshots.length === 0 ? (
        <div style={{textAlign: 'center', padding: '3rem 2rem', color: 'var(--text-muted)'}}>
          <span className="material-icons-outlined" style={{fontSize: '3rem', opacity: 0.3, display: 'block', marginBottom: '1rem'}}>history</span>
          <p style={{margin: 0}}>No hay horarios generados todavia.</p>
        </div>
      ) : (
        <div style={{display: 'flex', flexDirection: 'column', gap: '10px'}}>
          {snapshots.map(s => (
            <div key={s.id_snapshot} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '1rem 1.25rem', borderRadius: '12px',
              background: s.is_active ? 'rgba(91, 95, 199, 0.04)' : '#fafbfd',
              border: s.is_active ? '1.5px solid var(--accent)' : '1px solid var(--border-color)',
              flexWrap: 'wrap', gap: '10px',
              transition: 'all 0.15s ease'
            }}>
              <div style={{display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '200px'}}>
                {s.is_active && (
                  <span className="material-icons-outlined" style={{
                    color: 'var(--accent)',
                    fontSize: '1.2rem',
                    animation: 'pulse 2s ease-in-out infinite'
                  }}>check_circle</span>
                )}
                {editingSnapshot === s.id_snapshot ? (
                  <div style={{display: 'flex', gap: '6px', alignItems: 'center'}}>
                    <input type="text" value={snapshotName} onChange={e => setSnapshotName(e.target.value)}
                      style={{padding: '5px 10px', borderRadius: '8px', border: '1.5px solid var(--accent)', fontSize: '0.88rem', background: '#ffffff', color: 'var(--text-main)', outline: 'none'}}
                      onKeyDown={e => e.key === 'Enter' && onRename(s.id_snapshot)} autoFocus />
                    <button className="btn-save" style={{padding: '5px 12px', fontSize: '0.78rem'}} onClick={() => onRename(s.id_snapshot)}>OK</button>
                    <button className="btn-save btn-dark" style={{padding: '5px 12px', fontSize: '0.78rem'}} onClick={() => setEditingSnapshot(null)}>X</button>
                  </div>
                ) : (
                  <div>
                    <div style={{display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap'}}>
                      <strong style={{fontSize: '0.95rem', color: 'var(--text-main)'}}>{s.nombre}</strong>
                      {s.es_editada && (
                        <span style={{
                          fontSize: '0.65rem', color: '#ffffff', background: '#8b7ec8',
                          padding: '2px 8px', borderRadius: '10px', fontWeight: '600',
                          textTransform: 'uppercase', letterSpacing: '0.3px'
                        }}>Editada</span>
                      )}
                      {s.is_active && (
                        <span style={{
                          fontSize: '0.65rem', color: 'var(--accent)', background: 'var(--accent-light)',
                          padding: '2px 8px', borderRadius: '10px', fontWeight: '600',
                          textTransform: 'uppercase', letterSpacing: '0.3px',
                          animation: 'pulse 2s ease-in-out infinite'
                        }}>Activo</span>
                      )}
                    </div>
                    <div style={{fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px'}}>
                      {s.asignaciones_count} clases &middot; {s.tiempo_segundos?.toFixed(1) || 0}s
                      {s.created_at && (
                        <span style={{marginLeft: '8px', opacity: 0.7}}>
                          &middot; {new Date(s.created_at).toLocaleDateString('es-ES', {day: '2-digit', month: 'short', year: 'numeric'})}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
              <div style={{display: 'flex', gap: '6px'}}>
                <button className="btn-save" style={{padding: '6px 14px', fontSize: '0.78rem'}} onClick={() => onLoad(s.id_snapshot)}>
                  <span className="material-icons-outlined" style={{fontSize: '0.95rem', verticalAlign: 'middle', marginRight: '4px'}}>open_in_new</span>Cargar
                </button>
                <button className="btn-save btn-accent" style={{padding: '6px 14px', fontSize: '0.78rem'}} onClick={() => { setEditingSnapshot(s.id_snapshot); setSnapshotName(s.nombre); }}>
                  <span className="material-icons-outlined" style={{fontSize: '0.95rem', verticalAlign: 'middle', marginRight: '4px'}}>edit</span>Renombrar
                </button>
                <button className="btn-save btn-danger" style={{padding: '6px 14px', fontSize: '0.78rem'}} onClick={() => onDelete(s.id_snapshot, s.nombre)}>
                  <span className="material-icons-outlined" style={{fontSize: '0.95rem', verticalAlign: 'middle'}}>delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
