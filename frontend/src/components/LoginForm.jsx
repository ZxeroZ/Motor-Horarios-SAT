export default function LoginForm({ loginForm, setLoginForm, loginError, onSubmit }) {
  return (
    <div className="login-container">
      <div className="login-card">
        <div style={{
          width: '56px', height: '56px',
          background: 'var(--accent-gradient)',
          borderRadius: '14px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 1rem',
          boxShadow: '0 4px 12px rgba(91, 95, 199, 0.3)'
        }}>
          <span className="material-icons-outlined" style={{color: 'white', fontSize: '1.6rem'}}>school</span>
        </div>
        <h2>Timetable Engine</h2>
        <p>Ingresa tus credenciales para acceder</p>
        <form className="login-form" onSubmit={onSubmit}>
          <div style={{position: 'relative'}}>
            <span className="material-icons-outlined" style={{
              position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
              fontSize: '1.1rem', color: 'var(--text-muted)', opacity: 0.6
            }}>email</span>
            <input
              type="email"
              placeholder="Correo electronico"
              value={loginForm.email}
              onChange={e => setLoginForm({...loginForm, email: e.target.value})}
              required
              style={{paddingLeft: '38px'}}
            />
          </div>
          <div style={{position: 'relative'}}>
            <span className="material-icons-outlined" style={{
              position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
              fontSize: '1.1rem', color: 'var(--text-muted)', opacity: 0.6
            }}>lock</span>
            <input
              type="password"
              placeholder="Contrasena"
              value={loginForm.password}
              onChange={e => setLoginForm({...loginForm, password: e.target.value})}
              required
              style={{paddingLeft: '38px'}}
            />
          </div>
          {loginError && (
            <div style={{
              color: 'var(--danger)', fontSize: '0.85rem',
              background: 'rgba(217, 68, 82, 0.06)',
              padding: '8px 12px', borderRadius: '8px',
              borderLeft: '3px solid var(--danger)'
            }}>{loginError}</div>
          )}
          <button type="submit" className="btn-primary" style={{marginTop: '0.5rem'}}>
            Iniciar Sesion
          </button>
        </form>
      </div>
    </div>
  );
}
