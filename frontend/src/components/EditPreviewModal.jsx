import { useState } from 'react';

export default function EditPreviewModal({ moveData, validation, cursoNombre, profNombre, seccionInfo, onConfirm, onCancel }) {
  const [horasDestino, setHorasDestino] = useState(moveData.horasDestino);
  const [sending, setSending] = useState(false);

  if (!moveData || !validation) return null;

  const hasConflicts = validation.conflicts && validation.conflicts.length > 0;
  const hasWarnings = validation.warnings && validation.warnings.length > 0;
  const isSwap = validation.isSwap && validation.swapInfo;

  const cursoName = cursoNombre[moveData.cursoId] || moveData.cursoId;
  const profName = profNombre[moveData.profesorId] || moveData.profesorId;
  const secName = seccionInfo[moveData.seccionId] || moveData.seccionId;

  const handleConfirm = async () => {
    setSending(true);
    await onConfirm({ ...moveData, horasDestino });
    setSending(false);
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content edit-preview-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{isSwap ? 'Intercambiar Asignaciones' : 'Mover Asignacion'}</h3>
          <button className="modal-close" onClick={onCancel}>&times;</button>
        </div>

        <div className="modal-body">
          {isSwap ? (
            <>
              <div className="swap-summary">
                <div className="swap-card swap-card-a">
                  <span className="swap-label">A</span>
                  <strong>{cursoName}</strong>
                  <span className="swap-detail">{moveData.diaOrigen} Bloque {moveData.slotOrigen + 1}</span>
                  <span className="swap-arrow">&#10132;</span>
                  <span className="swap-detail">{moveData.diaDestino} Bloque {moveData.slotDestino + 1}</span>
                </div>
                <div className="swap-card swap-card-b">
                  <span className="swap-label">B</span>
                  <strong>{validation.swapInfo.swap_curso_nombre}</strong>
                  <span className="swap-detail">{moveData.diaDestino} Bloque {moveData.slotDestino + 1}</span>
                  <span className="swap-arrow">&#10132;</span>
                  <span className="swap-detail">{moveData.diaOrigen} Bloque {moveData.slotOrigen + 1}</span>
                </div>
              </div>
              <div className="move-info">
                <span>{validation.swapInfo.swap_seccion_nombre} &mdash; {validation.swapInfo.swap_profesor_nombre}</span>
              </div>
            </>
          ) : (
            <>
              <div className="move-summary">
                <div className="move-from">
                  <span className="move-label">Desde</span>
                  <span className="move-detail">
                    {moveData.diaOrigen} Bloque {moveData.slotOrigen + 1}
                    {moveData.horasOrigen > 1 && `-${moveData.slotOrigen + moveData.horasOrigen}`}
                  </span>
                </div>
                <span className="move-arrow">&#10132;</span>
                <div className="move-to">
                  <span className="move-label">Hasta</span>
                  <span className="move-detail">
                    {moveData.diaDestino} Bloque {moveData.slotDestino + 1}
                    {horasDestino > 1 && `-${moveData.slotDestino + horasDestino}`}
                  </span>
                </div>
              </div>
              <div className="move-info">
                <span><b>{cursoName}</b> &mdash; {profName} &mdash; {secName}</span>
              </div>
              <div className="move-duration">
                <label>Duracion destino (bloques):</label>
                <div className="duration-buttons">
                  {[1, 2, 3, 4].map(h => (
                    <button
                      key={h}
                      className={`duration-btn ${horasDestino === h ? 'active' : ''}`}
                      onClick={() => setHorasDestino(h)}
                      disabled={h > moveData.maxBlocksDestino}
                    >
                      {h}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {hasConflicts && (
            <div className="validation-section conflicts">
              <h4>Conflictos</h4>
              <ul>
                {validation.conflicts.map((c, i) => (
                  <li key={i} className="conflict-item">{c}</li>
                ))}
              </ul>
            </div>
          )}

          {hasWarnings && (
            <div className="validation-section warnings">
              <h4>Advertencias</h4>
              <ul>
                {validation.warnings.map((w, i) => (
                  <li key={i} className="warning-item">{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-cancel" onClick={onCancel}>Cancelar</button>
          <button
            className="btn-confirm"
            onClick={handleConfirm}
            disabled={hasConflicts || sending}
          >
            {sending ? 'Aplicando...' : isSwap ? 'Confirmar Intercambio' : 'Confirmar Movimiento'}
          </button>
        </div>
      </div>
    </div>
  );
}
