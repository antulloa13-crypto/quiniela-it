/* ============================================================
   Quiniela Deportiva — JavaScript principal
   ============================================================ */

'use strict';

// ── CSRF token para peticiones AJAX ──────────────────────────
const csrfMeta = document.querySelector('meta[name="csrf-token"]');
const CSRF_TOKEN = csrfMeta ? csrfMeta.getAttribute('content') : '';

// ── Utilidades ────────────────────────────────────────────────

/**
 * Muestra un toast de feedback en la esquina inferior derecha.
 * @param {string} message - Texto a mostrar
 * @param {'success'|'danger'|'warning'|'info'} type
 */
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: 'check-circle-fill',
    danger:  'x-circle-fill',
    warning: 'exclamation-triangle-fill',
    info:    'info-circle-fill',
  };

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center text-bg-${type} border-0 show`;
  toastEl.setAttribute('role', 'alert');
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="bi bi-${icons[type] || 'info-circle'} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(toastEl);

  // Auto-remove after 3.5s
  setTimeout(() => {
    toastEl.classList.remove('show');
    setTimeout(() => toastEl.remove(), 300);
  }, 3500);
}

// ── Temporizadores de cuenta regresiva ────────────────────────

/**
 * Formatea segundos totales en HH:MM:SS o DD h MM m.
 */
function formatCountdown(totalSeconds) {
  if (totalSeconds <= 0) return 'BLOQUEADO';
  const days    = Math.floor(totalSeconds / 86400);
  const hours   = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs    = totalSeconds % 60;

  if (days > 0) {
    return `${days}d ${String(hours).padStart(2, '0')}h ${String(minutes).padStart(2, '0')}m`;
  }
  if (hours > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Inicializa todos los contadores en la página.
 * Lee atributos data-year, data-month, data-day, data-hour, data-minute.
 */
function initCountdowns() {
  const timers = document.querySelectorAll('[data-countdown]');
  if (!timers.length) return;

  function tick() {
    const nowMs = Date.now();

    timers.forEach(el => {
      const targetMs = parseInt(el.getAttribute('data-countdown'), 10);
      const diff     = Math.floor((targetMs - nowMs) / 1000);

      el.textContent = formatCountdown(Math.max(0, diff));

      if (diff <= 0) {
        el.classList.add('bg-secondary');
        el.classList.remove('bg-warning', 'bg-danger', 'bg-info', 'text-dark');
        lockExpiredCards(el);
      } else if (diff < 300) {          // < 5 min → urgente
        el.classList.add('bg-danger', 'countdown-urgent');
        el.classList.remove('bg-warning', 'bg-info', 'text-dark');
      } else if (diff < 3600) {         // < 1 hora → advertencia
        el.classList.add('bg-warning', 'text-dark');
        el.classList.remove('bg-danger', 'bg-info', 'countdown-urgent');
      }
    });
  }

  tick();
  setInterval(tick, 1000);
}

/**
 * Bloquea el card del partido cuando el contador llega a 0 en tiempo real.
 */
function lockExpiredCards(timerEl) {
  const card = timerEl.closest('.partido-card');
  if (!card || card.classList.contains('locked')) return;

  card.classList.add('locked');

  const btnGroup = card.querySelector('.pronostico-btn-group');
  if (btnGroup) {
    btnGroup.querySelectorAll('.pronostico-btn').forEach(btn => {
      btn.disabled = true;
    });
    const lockMsg = document.createElement('div');
    lockMsg.className = 'text-center text-muted small mt-2';
    lockMsg.innerHTML = '<i class="bi bi-lock-fill me-1"></i>Pronósticos bloqueados';
    btnGroup.after(lockMsg);
  }
}

// ── Pronósticos (participante) ────────────────────────────────

/**
 * Guarda un pronóstico vía AJAX.
 * @param {number} partidoId
 * @param {string} pronostico - 'equipo_a' | 'empate' | 'equipo_b'
 * @param {HTMLElement} clickedBtn - botón que originó la acción
 */
async function guardarPronostico(partidoId, pronostico, clickedBtn) {
  const card     = clickedBtn.closest('.partido-card');
  const allBtns  = card ? card.querySelectorAll('.pronostico-btn') : [];

  // Feedback visual inmediato
  allBtns.forEach(b => b.disabled = true);
  const originalText = clickedBtn.innerHTML;
  clickedBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando…';

  try {
    const body = new URLSearchParams({ pronostico });
    const resp = await fetch(`/pronostico/${partidoId}`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': CSRF_TOKEN,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    });

    const data = await resp.json();

    if (data.success) {
      // Actualizar estilo de botones
      allBtns.forEach(b => {
        b.classList.remove('selected', 'selected-empate');
      });

      if (pronostico === 'empate') {
        clickedBtn.classList.add('selected-empate');
      } else {
        clickedBtn.classList.add('selected');
      }

      showToast(data.message, 'success');

      // Actualizar indicador de pronóstico guardado en el card
      const savedIndicator = card.querySelector('.pronostico-saved-label');
      if (savedIndicator) {
        savedIndicator.textContent = data.label;
        savedIndicator.closest('.pronostico-saved')?.classList.remove('d-none');
      }
    } else {
      showToast(data.message, 'danger');
    }
  } catch (err) {
    showToast('Error de conexión. Inténtalo de nuevo.', 'danger');
    console.error(err);
  } finally {
    clickedBtn.innerHTML = originalText;
    allBtns.forEach(b => b.disabled = false);
  }
}

// ── Formulario de resultados (admin) ─────────────────────────

/**
 * Resalta la opción seleccionada en las tarjetas de resultado.
 */
function initResultadoRadios() {
  document.querySelectorAll('.resultado-form').forEach(form => {
    form.querySelectorAll('.resultado-option').forEach(option => {
      const radio = option.querySelector('input[type="radio"]');
      if (radio && radio.checked) {
        option.classList.add('selected-option');
      }
      option.addEventListener('click', () => {
        form.querySelectorAll('.resultado-option').forEach(o => o.classList.remove('selected-option'));
        option.classList.add('selected-option');
        if (radio) radio.checked = true;
      });
    });
  });
}

// ── Confirmaciones de eliminación ────────────────────────────

function initDeleteConfirm() {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('submit', function (e) {
      const msg = el.getAttribute('data-confirm') || '¿Estás seguro de que deseas eliminar este elemento?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
}

// ── Toggle visibilidad contraseña ────────────────────────────

function initPasswordToggle() {
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-toggle-password');
      const input    = document.getElementById(targetId);
      const icon     = btn.querySelector('i');
      if (!input) return;

      if (input.type === 'password') {
        input.type = 'text';
        icon && icon.classList.replace('bi-eye', 'bi-eye-slash');
      } else {
        input.type = 'password';
        icon && icon.classList.replace('bi-eye-slash', 'bi-eye');
      }
    });
  });
}

// ── Auto-dismiss de alertas ───────────────────────────────────

function initAlertAutoDismiss() {
  document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert && bsAlert.close();
    }, 4000);
  });
}

// ── Validación de formularios ────────────────────────────────

function initFormValidation() {
  document.querySelectorAll('form[data-validate]').forEach(form => {
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });
}

// ── Inicialización ────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initCountdowns();
  initResultadoRadios();
  initDeleteConfirm();
  initPasswordToggle();
  initAlertAutoDismiss();
  initFormValidation();

  // Exponer función global para los botones de pronóstico
  window.guardarPronostico = guardarPronostico;
});
