export default function Toast({ toasts }) {
  return (
    <div style={{position:'fixed', top:'20px', right:'20px', zIndex:9999, display:'flex', flexDirection:'column', gap:'8px'}}>
      {toasts.map(t => (
        <div key={t.id} style={{
          padding:'12px 20px', borderRadius:'10px', color:'white', fontWeight:'600',
          fontSize:'0.9rem', boxShadow:'0 4px 12px rgba(0,0,0,0.15)',
          animation:'toastIn 0.3s ease', minWidth:'200px',
          background: t.type === 'error' ? '#ef4444' : t.type === 'info' ? '#3b82f6' : '#10b981'
        }}>
          {t.message}
        </div>
      ))}
    </div>
  );
}
