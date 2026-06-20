export default function LoginForm({ loginForm, setLoginForm, loginError, onSubmit }) {
  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Timetable Engine</h2>
        <p>Ingresa tus credenciales para acceder</p>
        <form className="login-form" onSubmit={onSubmit}>
          <input type="email" placeholder="Correo electrónico" value={loginForm.email} onChange={e => setLoginForm({...loginForm, email: e.target.value})} required />
          <input type="password" placeholder="Contraseña" value={loginForm.password} onChange={e => setLoginForm({...loginForm, password: e.target.value})} required />
          {loginError && <div style={{color: 'var(--danger)', fontSize: '0.9rem'}}>{loginError}</div>}
          <button type="submit" className="btn-primary">Iniciar Sesión</button>
        </form>
      </div>
    </div>
  );
}
