// API Client para Balanced Scorecard - AGRO PERUVIAN FOODS S.A.C.
const API_BASE = '/api/v1';

const api = {
  // Autenticación
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al iniciar sesión');
    }
    return res.json();
  },

  async getDemoUsers() {
    const res = await fetch(`${API_BASE}/auth/demo-users`);
    return res.json();
  },

  // Dashboard
  async getDashboardMetrics(periodo = '', modulo = '', responsable = '') {
    const params = new URLSearchParams();
    if (periodo) params.append('periodo', periodo);
    if (modulo) params.append('modulo', modulo);
    if (responsable) params.append('responsable', responsable);
    const res = await fetch(`${API_BASE}/dashboard/metrics?${params.toString()}`);
    return res.json();
  },

  // Objetivos Estratégicos
  async getObjetivos(filters = {}) {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${API_BASE}/objetivos?${params.toString()}`);
    return res.json();
  },

  async getObjetivo(id) {
    const res = await fetch(`${API_BASE}/objetivos/${id}`);
    return res.json();
  },

  async getMapaEstrategico() {
    const res = await fetch(`${API_BASE}/objetivos/tree/map`);
    return res.json();
  },

  async createObjetivo(data) {
    const res = await fetch(`${API_BASE}/objetivos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al crear objetivo');
    }
    return res.json();
  },

  async updateObjetivo(id, data) {
    const res = await fetch(`${API_BASE}/objetivos/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al actualizar objetivo');
    }
    return res.json();
  },

  async deleteObjetivo(id) {
    const res = await fetch(`${API_BASE}/objetivos/${id}`, { method: 'DELETE' });
    return res.json();
  },

  // Indicadores KPI
  async getKpis(filters = {}) {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${API_BASE}/kpis?${params.toString()}`);
    return res.json();
  },

  async getKpi(id) {
    const res = await fetch(`${API_BASE}/kpis/${id}`);
    return res.json();
  },

  async getKpiHistorial(id) {
    const res = await fetch(`${API_BASE}/kpis/${id}/historial`);
    return res.json();
  },

  async createKpi(data) {
    const res = await fetch(`${API_BASE}/kpis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al crear KPI');
    }
    return res.json();
  },

  async updateKpi(id, data) {
    const res = await fetch(`${API_BASE}/kpis/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al actualizar KPI');
    }
    return res.json();
  },

  async deleteKpi(id) {
    const res = await fetch(`${API_BASE}/kpis/${id}`, { method: 'DELETE' });
    return res.json();
  },

  // Mediciones
  async getMediciones(filters = {}) {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${API_BASE}/mediciones?${params.toString()}`);
    return res.json();
  },

  async createMedicion(data) {
    const res = await fetch(`${API_BASE}/mediciones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al registrar medición');
    }
    return res.json();
  },

  async updateMedicion(id, data) {
    const res = await fetch(`${API_BASE}/mediciones/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al editar medición');
    }
    return res.json();
  },

  async deleteMedicion(id) {
    const res = await fetch(`${API_BASE}/mediciones/${id}`, { method: 'DELETE' });
    return res.json();
  },

  // Iniciativas
  async getIniciativas(filters = {}) {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${API_BASE}/iniciativas?${params.toString()}`);
    return res.json();
  },

  async getIniciativasResumen() {
    const res = await fetch(`${API_BASE}/iniciativas/resumen`);
    return res.json();
  },

  async createIniciativa(data) {
    const res = await fetch(`${API_BASE}/iniciativas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al crear iniciativa');
    }
    return res.json();
  },

  async updateIniciativa(id, data) {
    const res = await fetch(`${API_BASE}/iniciativas/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error al actualizar iniciativa');
    }
    return res.json();
  },

  async deleteIniciativa(id) {
    const res = await fetch(`${API_BASE}/iniciativas/${id}`, { method: 'DELETE' });
    return res.json();
  },

  // Odoo 17 Sync & Diagnóstico
  async syncOdoo(periodo = '') {
    const params = periodo ? `?periodo=${periodo}` : '';
    const res = await fetch(`${API_BASE}/bsc/sync-odoo${params}`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error en sincronización Odoo 17');
    }
    return res.json();
  },

  async getSyncStatus() {
    const res = await fetch(`${API_BASE}/bsc/sync-status`);
    return res.json();
  },

  async getSyncLogs() {
    const res = await fetch(`${API_BASE}/bsc/sync-logs`);
    return res.json();
  },

  // Reportes
  async getReporteConsolidado(filters = {}) {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${API_BASE}/reportes/consolidado?${params.toString()}`);
    return res.json();
  },

  // Admin
  async getUsuarios() {
    const res = await fetch(`${API_BASE}/admin/usuarios`);
    return res.json();
  },

  async createUsuario(data) {
    const res = await fetch(`${API_BASE}/admin/usuarios`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async deleteUsuario(id) {
    const res = await fetch(`${API_BASE}/admin/usuarios/${id}`, { method: 'DELETE' });
    return res.json();
  },

  async getPeriodos() {
    const res = await fetch(`${API_BASE}/admin/periodos`);
    return res.json();
  },

  async createPeriodo(data) {
    const res = await fetch(`${API_BASE}/admin/periodos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async activarPeriodo(id) {
    const res = await fetch(`${API_BASE}/admin/periodos/${id}/activar`, { method: 'PUT' });
    return res.json();
  },

  async getModulosOdoo() {
    const res = await fetch(`${API_BASE}/admin/modulos-odoo`);
    return res.json();
  }
};
