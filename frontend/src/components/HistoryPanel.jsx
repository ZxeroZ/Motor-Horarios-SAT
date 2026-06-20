export default function HistoryPanel({ snapshots, editingSnapshot, snapshotName, setSnapshotName, setEditingSnapshot, onLoad, onRename, onDelete }) {
  return (
    <div style={{background: 'var(--bg-card)', padding: '2rem', borderRadius: 'var(--border-radius-lg)', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border-color)'}}>
      <h2 style={{marginTop: 0, marginBottom: '1.5rem'}}>Historial de Horarios</h2>
      {snapshots.length === 0 ? (
        <p style={{color: 'var(--text-muted)', textAlign: 'center', padding: '2rem'}}>No hay horarios generados todavía.</p>
      ) : (
        <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
          {snapshots.map(s => (
            <div key={s.id_snapshot} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '1rem 1.5rem', borderRadius: '12px',
              background: s.is_active ? 'rgba(59,130,246,0.08)' : 'var(--bg-panel-light)',
              border: s.is_active ? '2px solid var(--accent)' : '1px solid var(--border-color)',
              flexWrap: 'wrap', gap: '10px'
            }}>
              <div style={{display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '200px'}}>
                {s.is_active && <span className="material-icons-outlined" style={{color: 'var(--accent)'}}>check_circle</span>}
                {editingSnapshot === s.id_snapshot ? (
                  <div style={{display: 'flex', gap: '6px', alignItems: 'center'}}>
                    <input type="text" value={snapshotName} onChange={e => setSnapshotName(e.target.value)}
                      style={{padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem', background: 'var(--bg-card)', color: 'var(--text-main)'}}
                      onKeyDown={e => e.key === 'Enter' && onRename(s.id_snapshot)} autoFocus />
                    <button className="btn-save" style={{padding: '4px 10px', fontSize: '0.75rem'}} onClick={() => onRename(s.id_snapshot)}>OK</button>
                    <button className="btn-save btn-dark" style={{padding: '4px 10px', fontSize: '0.75rem'}} onClick={() => setEditingSnapshot(null)}>X</button>
                  </div>
                ) : (
                  <div>
                    <strong style={{fontSize: '1rem'}}>{s.nombre}</strong>
                    <span style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '8px'}}>
                      {s.asignaciones_count} clases | {s.tiempo_segundos?.toFixed(1) || 0}s
                    </span>
                    {s.is_active && <span style={{fontSize: '0.75rem', color: 'var(--accent)', marginLeft: '8px', fontWeight: '600'}}>ACTIVO</span>}
                  </div>
                )}
              </div>
              <div style={{display: 'flex', gap: '6px'}}>
                <button className="btn-save" style={{padding: '6px 14px', fontSize: '0.8rem'}} onClick={() => onLoad(s.id_snapshot)}>
                  <span className="material-icons-outlined" style={{fontSize: '1rem', verticalAlign: 'middle', marginRight: '4px'}}>open_in_new</span>Cargar
                </button>
                <button className="btn-save btn-accent" style={{padding: '6px 14px', fontSize: '0.8rem'}} onClick={() => { setEditingSnapshot(s.id_snapshot); setSnapshotName(s.nombre); }}>
                  <span className="material-icons-outlined" style={{fontSize: '1rem', verticalAlign: 'middle', marginRight: '4px'}}>edit</span>Renombrar
                </button>
                <button className="btn-save btn-danger" style={{padding: '6px 14px', fontSize: '0.8rem'}} onClick={() => onDelete(s.id_snapshot, s.nombre)}>
                  <span className="material-icons-outlined" style={{fontSize: '1rem', verticalAlign: 'middle', marginRight: '4px'}}>delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
