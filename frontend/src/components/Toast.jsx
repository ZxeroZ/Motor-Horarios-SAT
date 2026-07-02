export default function Toast({ toasts }) {
  return (
    <div style={{position:'fixed', top:'20px', right:'20px', zIndex:9999, display:'flex', flexDirection:'column', gap:'8px'}}>
      {toasts.map(t => (
        <div key={t.id} style={{
          padding:'12px 20px', borderRadius:'10px', color:'white', fontWeight:'600',
          fontSize:'0.88rem', boxShadow:'0 4px 16px rgba(0,0,0,0.15)',
          animation:'toastIn 0.3s ease', minWidth:'200px',
          display: 'flex', alignItems: 'center', gap: '8px',
          background: t.type === 'error' ? '#d94452' : t.type === 'info' ? '#5b5fc7' : '#3aaf6c'
        }}>
          <span className="material-icons-outlined" style={{fontSize: '1.1rem'}}>
            {t.type === 'error' ? 'error' : t.type === 'info' ? 'info' : 'check_circle'}
          </span>
          {t.message}
        </div>
      ))}
    </div>
  );
}
