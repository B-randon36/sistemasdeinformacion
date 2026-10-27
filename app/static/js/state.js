// Gestión de Estado Global - AGRO PERUVIAN FOODS S.A.C.
const state = {
  currentUser: JSON.parse(localStorage.getItem('agro_bsc_user')) || null,
  token: localStorage.getItem('agro_bsc_token') || null,
  activePeriod: '2026-10',
  periods: [],
  modulosOdoo: [],
  currentView: 'dashboard',
  filters: {
    dashboard: { modulo: '', responsable: '' },
    objetivos: { perspectiva: 'TODAS', modulo: '', prioridad: 'TODAS', search: '' },
    kpis: { perspectiva: 'TODAS', modulo: 'TODOS', semaforo: 'TODOS', sentido: 'TODOS', search: '' },
    mediciones: { kpi_id: '', origen: 'TODOS' },
    iniciativas: { estado: 'TODOS', modulo: 'TODOS', search: '' }
  },

  setUser(user, token) {
    this.currentUser = user;
    this.token = token;
    if (user) {
      localStorage.setItem('agro_bsc_user', JSON.stringify(user));
      localStorage.setItem('agro_bsc_token', token);
    } else {
      localStorage.removeItem('agro_bsc_user');
      localStorage.removeItem('agro_bsc_token');
    }
  },

  setActivePeriod(codigo) {
    this.activePeriod = codigo;
    const periodSelects = document.querySelectorAll('.period-select-sync');
    periodSelects.forEach(el => el.value = codigo);
  },

  showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const colors = {
      success: 'bg-emerald-600 text-white border-emerald-700',
      error: 'bg-rose-600 text-white border-rose-700',
      warning: 'bg-amber-500 text-white border-amber-600',
      info: 'bg-blue-600 text-white border-blue-700'
    };
    const icons = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-triangle',
      warning: 'fa-exclamation-circle',
      info: 'fa-info-circle'
    };

    toast.className = `flex items-center space-x-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all transform duration-300 translate-y-2 opacity-0 ${colors[type] || colors.info}`;
    toast.innerHTML = `
      <i class="fas ${icons[type] || icons.info} text-lg"></i>
      <span class="flex-1">${message}</span>
      <button class="text-white hover:text-slate-200" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};
