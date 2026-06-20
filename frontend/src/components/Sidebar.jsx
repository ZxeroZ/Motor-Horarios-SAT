export default function Sidebar({ activeTab, setActiveTab, user, isDevUnlocked, fakeSearch, onFakeSearch, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon"><span className="material-icons-outlined">school</span></div>
        <h2>Timetable OS</h2>
      </div>
      <div className="sidebar-user">
        <div className="user-avatar">{user?.nombre?.charAt(0) || 'U'}</div>
        <div className="user-info">
          <div className="user-name">{user?.nombre}</div>
          <div className="user-role">Administrador</div>
        </div>
      </div>
      
      <div style={{marginBottom: '1.5rem'}}>
        <input 
          type="text" 
          placeholder="Buscar..." 
          value={fakeSearch}
          onChange={onFakeSearch}
          style={{
            width: '100%', padding: '0.8rem', borderRadius: '12px', 
            background: 'var(--bg-panel-light)', border: '1px solid var(--border-color)', 
            color: 'var(--text-main)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box'
          }}
        />
      </div>

      <nav className="sidebar-nav">
        <button className={`nav-item ${activeTab === 'horarios' ? 'active' : ''}`} onClick={() => setActiveTab('horarios')}>
          <span className="material-icons-outlined">calendar_month</span> Malla Horaria
        </button>
        <button className={`nav-item ${activeTab === 'historial' ? 'active' : ''}`} onClick={() => setActiveTab('historial')}>
          <span className="material-icons-outlined">history</span> Historial
        </button>
        <button className={`nav-item ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>
          <span className="material-icons-outlined">settings</span> Configuración
        </button>
        {isDevUnlocked && (
          <button className={`nav-item ${activeTab === 'dev-tools' ? 'active' : ''}`} onClick={() => setActiveTab('dev-tools')}>
            <span className="material-icons-outlined">build</span> Developer Tools
          </button>
        )}
        <div className="nav-spacer"></div>
        <button className="nav-item text-danger" onClick={onLogout}>
          <span className="material-icons-outlined">logout</span> Cerrar Sesión
        </button>
      </nav>
    </aside>
  );
}
