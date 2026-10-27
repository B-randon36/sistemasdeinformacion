// Aplicación Principal SPA - AGRO PERUVIAN FOODS S.A.C.
// Balanced Scorecard Enterprise & Odoo 17 ERP

document.addEventListener('DOMContentLoaded', async () => {
  await app.init();
});

const app = {
  async init() {
    this.bindEvents();
    await this.loadInitialCatalogs();

    // Si no hay usuario logueado, usar por defecto el Admin demostrativo
    if (!state.currentUser) {
      state.setUser({
        id: 1,
        username: 'admin',
        nombre: 'Ing. Jean Paul Ramos',
        rol: 'ADMIN',
        area: 'Dirección de Estrategia y TI'
      }, 'demo_token_admin');
    }

    this.updateUserUI();
    this.switchView('dashboard');
  },

  async loadInitialCatalogs() {
    try {
      const [periodos, modulos] = await Promise.all([
        api.getPeriodos(),
        api.getModulosOdoo()
      ]);
      state.periods = periodos;
      state.modulosOdoo = modulos;

      const activo = periodos.find(p => p.activo);
      if (activo) state.activePeriod = activo.codigo;

      this.populatePeriodSelects();
      this.populateModuleSelects();
    } catch (err) {
      console.error('Error cargando catálogos:', err);
    }
  },

  populatePeriodSelects() {
    const selects = document.querySelectorAll('.period-select-sync');
    selects.forEach(sel => {
      sel.innerHTML = state.periods.map(p => `
        <option value="${p.codigo}" ${p.codigo === state.activePeriod ? 'selected' : ''}>
          ${p.nombre} ${p.activo ? '★ (Oficial)' : ''}
        </option>
      `).join('');
    });
  },

  populateModuleSelects() {
    const selects = document.querySelectorAll('.module-select-sync');
    selects.forEach(sel => {
      const includeAll = sel.getAttribute('data-include-all') === 'true';
      let options = includeAll ? '<option value="TODOS">Todos los Módulos Odoo 17</option>' : '<option value="">Seleccione Módulo Odoo...</option>';
      options += state.modulosOdoo.map(m => `
        <option value="${m.id}" data-codigo="${m.codigo}" data-nombre="${m.nombre_modulo_odoo}">
          ${m.nombre_modulo_odoo} [${m.modelo_tecnico}]
        </option>
      `).join('');
      sel.innerHTML = options;
    });
  },

  bindEvents() {
    // Navegación Sidebar
    document.querySelectorAll('[data-view]').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const targetView = el.getAttribute('data-view');
        this.switchView(targetView);
      });
    });

    // Selector de Período Global
    const globalPeriodSelect = document.getElementById('global-period-select');
    if (globalPeriodSelect) {
      globalPeriodSelect.addEventListener('change', async (e) => {
        state.setActivePeriod(e.target.value);
        state.showToast(`Período cambiado a ${e.target.value}`, 'info');
        await this.refreshCurrentView();
      });
    }

    // Botones de Sincronización Odoo 17
    document.querySelectorAll('.btn-sync-odoo').forEach(btn => {
      btn.addEventListener('click', () => this.ejecutarSincronizacionOdoo());
    });

    // Logout
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
      btnLogout.addEventListener('click', () => this.logout());
    }
  },

  updateUserUI() {
    const u = state.currentUser;
    if (!u) return;

    const nameEl = document.getElementById('user-display-name');
    const roleEl = document.getElementById('user-display-role');
    const areaEl = document.getElementById('user-display-area');

    if (nameEl) nameEl.textContent = u.nombre;
    if (roleEl) {
      roleEl.textContent = u.rol;
      roleEl.className = `text-xs font-semibold px-2 py-0.5 rounded-full ${
        u.rol === 'ADMIN' ? 'bg-purple-100 text-purple-700' :
        u.rol === 'GERENTE' ? 'bg-blue-100 text-blue-700' :
        'bg-emerald-100 text-emerald-700'
      }`;
    }
    if (areaEl) areaEl.textContent = u.area || 'Operaciones';

    // Restricciones de interfaz según rol
    const adminOnlyEls = document.querySelectorAll('.admin-only');
    adminOnlyEls.forEach(el => {
      el.style.display = u.rol === 'ADMIN' ? '' : 'none';
    });
  },

  async switchView(viewName) {
    state.currentView = viewName;

    // Actualizar sidebar activo
    document.querySelectorAll('.sidebar-link').forEach(link => {
      if (link.getAttribute('data-view') === viewName) {
        link.classList.add('active', 'bg-blue-500/10', 'text-blue-500', 'border-r-4', 'border-blue-500');
        link.classList.remove('text-slate-400');
      } else {
        link.classList.remove('active', 'bg-blue-500/10', 'text-blue-500', 'border-r-4', 'border-blue-500');
        link.classList.add('text-slate-400');
      }
    });

    // Ocultar todas las vistas
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));

    // Mostrar vista objetivo
    const targetSec = document.getElementById(`view-${viewName}`);
    if (targetSec) {
      targetSec.classList.remove('hidden');
    }

    // Cargar datos de la vista
    await this.refreshCurrentView();
  },

  async refreshCurrentView() {
    const v = state.currentView;
    if (v === 'dashboard') await this.renderDashboard();
    else if (v === 'mapa') await this.renderMapaEstrategico();
    else if (v === 'objetivos') await this.renderObjetivos();
    else if (v === 'kpis') await this.renderKpis();
    else if (v === 'mediciones') await this.renderMediciones();
    else if (v === 'iniciativas') await this.renderIniciativas();
    else if (v === 'reportes') await this.renderReportes();
    else if (v === 'admin') await this.renderAdmin();
  },

  // ==========================================
  // 1. MÓDULO DASHBOARD EJECUTIVO
  // ==========================================
  async renderDashboard() {
    try {
      const data = await api.getDashboardMetrics(
        state.activePeriod,
        state.filters.dashboard.modulo,
        state.filters.dashboard.responsable
      );

      // Tarjetas ejecutivas
      document.getElementById('dash-cumplimiento-global').textContent = `${data.cumplimiento_global}%`;
      document.getElementById('dash-total-objetivos').textContent = data.total_objetivos;
      document.getElementById('dash-total-kpis').textContent = data.total_kpis;
      document.getElementById('dash-total-iniciativas').textContent = data.total_iniciativas;

      document.getElementById('dash-badge-cumplidos').textContent = data.total_cumplidos;
      document.getElementById('dash-badge-alerta').textContent = data.total_alerta;
      document.getElementById('dash-badge-criticos').textContent = data.total_criticos;
      document.getElementById('dash-badge-sindatos').textContent = data.total_sin_datos;

      // Barra de progreso global
      const progressGlobal = document.getElementById('dash-progress-global');
      if (progressGlobal) {
        progressGlobal.style.width = `${Math.min(100, data.cumplimiento_global)}%`;
        progressGlobal.className = `h-2.5 rounded-full transition-all duration-500 ${
          data.cumplimiento_global >= 90 ? 'bg-emerald-500' :
          data.cumplimiento_global >= 75 ? 'bg-amber-500' : 'bg-rose-500'
        }`;
      }

      // Gráficos Chart.js
      charts.renderPerspectivasRadar('chart-radar-perspectivas', data.perspectivas);
      charts.renderTendenciaHistorica('chart-line-tendencia', data.historico_tendencia);
      charts.renderSemaforosDoughnut('chart-doughnut-semaforos', {
        cumplidos: data.total_cumplidos,
        alerta: data.total_alerta,
        criticos: data.total_criticos,
        sin_datos: data.total_sin_datos
      });
      charts.renderDesempenoModulos('chart-bar-modulos', data.desempeno_modulos);

      // Tabla de indicadores que requieren atención
      const tbodyAtencion = document.getElementById('dash-tbody-atencion');
      if (tbodyAtencion) {
        if (!data.indicadores_atencion.length) {
          tbodyAtencion.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-400">¡Excelente! No hay indicadores críticos o en riesgo que requieran atención urgente.</td></tr>`;
        } else {
          tbodyAtencion.innerHTML = data.indicadores_atencion.map(k => `
            <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
              <td class="py-3 px-4 font-semibold text-slate-800">
                <span class="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600 mr-1.5">${k.codigo}</span>
                ${k.nombre}
              </td>
              <td class="py-3 px-4">
                <span class="inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                  <i class="fas fa-cube text-slate-400 mr-1"></i> ${k.modulo_odoo}
                </span>
                <span class="block text-[10px] text-slate-400 font-mono mt-0.5">${k.modelo_odoo}</span>
              </td>
              <td class="py-3 px-4 text-right">
                <span class="text-xs text-slate-500 block">Meta: ${k.meta} ${k.unidad}</span>
                <span class="font-bold text-slate-800">${k.valor_actual !== null ? k.valor_actual : 'N/A'} ${k.unidad}</span>
              </td>
              <td class="py-3 px-4 text-center">
                <span class="font-bold ${k.porcentaje_cumplimiento >= 75 ? 'text-amber-600' : 'text-rose-600'}">
                  ${k.porcentaje_cumplimiento !== null ? `${k.porcentaje_cumplimiento}%` : 'S/D'}
                </span>
              </td>
              <td class="py-3 px-4 text-center">
                ${this.renderSemaforoBadge(k.semaforo)}
              </td>
              <td class="py-3 px-4 text-right">
                <button onclick="app.abrirModalMedicionRapida(${k.id}, '${k.codigo}', '${k.nombre.replace(/'/g, "\\'")}', '${k.unidad}')" class="text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 font-semibold px-2.5 py-1.5 rounded-lg transition-colors">
                  <i class="fas fa-plus mr-1"></i> Medir
                </button>
              </td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Error renderizando dashboard:', err);
      state.showToast('Error cargando métricas ejecutivas', 'error');
    }
  },

  // ==========================================
  // 2. MÓDULO MAPA ESTRATÉGICO
  // ==========================================
  async renderMapaEstrategico() {
    try {
      const data = await api.getMapaEstrategico();
      const container = document.getElementById('mapa-perspectivas-container');
      if (!container) return;

      const perspectiveThemes = {
        FINANCIERA: { bg: 'border-l-4 border-blue-500 bg-blue-50/30', header: 'text-blue-900 bg-blue-100/60', icon: 'fa-dollar-sign text-blue-600' },
        CLIENTE: { bg: 'border-l-4 border-emerald-500 bg-emerald-50/30', header: 'text-emerald-900 bg-emerald-100/60', icon: 'fa-users text-emerald-600' },
        PROCESOS_INTERNOS: { bg: 'border-l-4 border-amber-500 bg-amber-50/30', header: 'text-amber-900 bg-amber-100/60', icon: 'fa-cogs text-amber-600' },
        APRENDIZAJE: { bg: 'border-l-4 border-indigo-500 bg-indigo-50/30', header: 'text-indigo-900 bg-indigo-100/60', icon: 'fa-graduation-cap text-indigo-600' }
      };

      container.innerHTML = data.perspectivas.map(p => {
        const theme = perspectiveThemes[p.id] || perspectiveThemes.FINANCIERA;
        return `
          <div class="rounded-2xl p-5 mb-6 ${theme.bg} shadow-sm border border-slate-200/80">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-white shadow-sm border border-slate-200">
                  <i class="fas ${theme.icon} text-lg"></i>
                </div>
                <div>
                  <h3 class="font-bold text-lg text-slate-800">${p.nombre}</h3>
                  <span class="text-xs text-slate-500">${p.objetivos.length} Objetivos Estratégicos</span>
                </div>
              </div>
            </div>

            <!-- Fila de Objetivos de la Perspectiva -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              ${p.objetivos.map(obj => `
                <div onclick="app.abrirModalDetalleObjetivo(${obj.id})" class="map-card bg-white rounded-xl p-4 border border-slate-200 shadow-sm cursor-pointer hover:border-blue-400 relative group">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">${obj.codigo}</span>
                    ${this.renderSemaforoDot(obj.semaforo)}
                  </div>
                  <h4 class="font-semibold text-slate-800 text-sm line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
                    ${obj.nombre}
                  </h4>
                  <div class="flex items-center justify-between text-xs text-slate-500 mb-2">
                    <span class="inline-flex items-center bg-slate-50 px-2 py-0.5 rounded text-[11px]">
                      <i class="fas fa-cube text-slate-400 mr-1"></i> ${obj.modulo_odoo_nombre.split(' ')[0]}
                    </span>
                    <span class="font-semibold text-slate-700">${obj.avance_calculado}%</span>
                  </div>
                  <!-- Mini Barra de Avance -->
                  <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div class="h-1.5 rounded-full ${
                      obj.avance_calculado >= 90 ? 'bg-emerald-500' :
                      obj.avance_calculado >= 75 ? 'bg-amber-500' : 'bg-rose-500'
                    }" style="width: ${Math.min(100, obj.avance_calculado)}%"></div>
                  </div>
                  <div class="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                    <span>${obj.kpis_count} KPIs | ${obj.iniciativas_count} Inic.</span>
                    <span class="font-mono">${obj.modulo_odoo_modelo}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('Error renderizando mapa:', err);
    }
  },

  async abrirModalDetalleObjetivo(id) {
    try {
      const obj = await api.getObjetivo(id);
      const modal = document.getElementById('modal-detalle-objetivo');
      if (!modal) return;

      document.getElementById('mod-obj-codigo').textContent = obj.codigo;
      document.getElementById('mod-obj-nombre').textContent = obj.nombre;
      document.getElementById('mod-obj-perspectiva').textContent = obj.perspectiva;
      document.getElementById('mod-obj-modulo').textContent = `${obj.modulo_nombre} (${obj.modulo_modelo})`;
      document.getElementById('mod-obj-responsable').textContent = obj.responsable;
      document.getElementById('mod-obj-avance').textContent = `${obj.avance_calculado}%`;
      document.getElementById('mod-obj-ponderacion').textContent = `${obj.ponderacion}%`;

      // Causa-Efecto padre
      const padreContainer = document.getElementById('mod-obj-causa-efecto');
      if (padreContainer) {
        if (obj.objetivo_padre_codigo) {
          padreContainer.innerHTML = `
            <div class="bg-indigo-50 border border-indigo-200 rounded-xl p-3 flex items-center space-x-3">
              <i class="fas fa-arrow-up text-indigo-500 text-lg"></i>
              <div>
                <span class="text-xs text-indigo-600 font-semibold block">Impulsado por (Causa Directa):</span>
                <span class="text-xs font-bold text-slate-800">[${obj.objetivo_padre_codigo}] ${obj.objetivo_padre_nombre}</span>
              </div>
            </div>
          `;
        } else {
          padreContainer.innerHTML = `<span class="text-xs text-slate-400 italic">Objetivo de base estratégica (sin predecesor directo)</span>`;
        }
      }

      // KPIs asociados
      const kpisContainer = document.getElementById('mod-obj-kpis-list');
      if (kpisContainer) {
        kpisContainer.innerHTML = obj.kpis.map(k => `
          <div class="p-3 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
            <div>
              <div class="flex items-center space-x-2">
                <span class="text-xs font-mono font-bold bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700">${k.codigo}</span>
                <span class="text-xs font-semibold text-slate-800">${k.nombre}</span>
              </div>
              <span class="text-[11px] text-slate-500">Modelo Odoo: <code class="text-slate-700">${k.modelo_odoo}</code> | Meta: ${k.meta} ${k.unidad}</span>
            </div>
            <div class="text-right">
              <span class="text-xs font-bold ${k.porcentaje_cumplimiento >= 75 ? 'text-slate-800' : 'text-rose-600'}">
                ${k.valor_actual !== null ? k.valor_actual : 'S/D'} ${k.unidad} (${k.porcentaje_cumplimiento || 0}%)
              </span>
              <div class="mt-1">${this.renderSemaforoBadge(k.semaforo)}</div>
            </div>
          </div>
        `).join('') || '<p class="text-xs text-slate-400">Sin KPIs asignados.</p>';
      }

      // Iniciativas
      const inicContainer = document.getElementById('mod-obj-iniciativas-list');
      if (inicContainer) {
        inicContainer.innerHTML = obj.iniciativas.map(i => `
          <div class="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between">
            <div>
              <span class="text-xs font-bold text-slate-800">${i.nombre}</span>
              <span class="block text-[11px] text-slate-500">Presupuesto: S/ ${i.presupuesto.toLocaleString()} | Resp: ${i.responsable}</span>
            </div>
            <div class="text-right">
              <span class="text-xs font-bold text-blue-600">${i.porcentaje_avance}% avance</span>
              <span class="block text-[10px] uppercase font-semibold text-slate-500">${i.estado}</span>
            </div>
          </div>
        `).join('') || '<p class="text-xs text-slate-400">Sin iniciativas registradas.</p>';
      }

      modal.classList.remove('hidden');
    } catch (err) {
      console.error(err);
      state.showToast('Error abriendo detalle de objetivo', 'error');
    }
  },

  // ==========================================
  // 3. GESTIÓN DE OBJETIVOS ESTRATÉGICOS (CRUD)
  // ==========================================
  async renderObjetivos() {
    try {
      const filters = {};
      if (state.filters.objetivos.perspectiva !== 'TODAS') filters.perspectiva = state.filters.objetivos.perspectiva;
      if (state.filters.objetivos.prioridad !== 'TODAS') filters.prioridad = state.filters.objetivos.prioridad;
      if (state.filters.objetivos.search) filters.search = state.filters.objetivos.search;

      const objetivos = await api.getObjetivos(filters);
      const tbody = document.getElementById('objetivos-table-body');
      if (!tbody) return;

      tbody.innerHTML = objetivos.map(o => `
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
          <td class="py-3 px-4 font-mono font-bold text-xs text-blue-600">${o.codigo}</td>
          <td class="py-3 px-4">
            <span class="font-semibold text-slate-800 text-sm block">${o.nombre}</span>
            <span class="text-xs text-slate-400">${o.descripcion || ''}</span>
          </td>
          <td class="py-3 px-4 text-xs font-medium text-slate-600">${o.perspectiva}</td>
          <td class="py-3 px-4">
            <span class="text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-700">${o.modulo_nombre || 'N/A'}</span>
          </td>
          <td class="py-3 px-4 text-xs font-semibold text-slate-700 text-center">${o.ponderacion}%</td>
          <td class="py-3 px-4 text-center">
            <div class="flex items-center justify-center space-x-2">
              <span class="text-xs font-bold text-slate-800">${o.avance_calculado}%</span>
              ${this.renderSemaforoDot(o.semaforo)}
            </div>
          </td>
          <td class="py-3 px-4 text-right space-x-2">
            <button onclick="app.editarObjetivo(${o.id})" class="text-slate-500 hover:text-blue-600 text-xs font-semibold p-1.5"><i class="fas fa-edit"></i></button>
            <button onclick="app.confirmarEliminarObjetivo(${o.id}, '${o.codigo}')" class="admin-only text-slate-400 hover:text-rose-600 text-xs font-semibold p-1.5"><i class="fas fa-trash"></i></button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  },

  abrirModalNuevoObjetivo() {
    document.getElementById('form-objetivo-id').value = '';
    document.getElementById('form-objetivo-codigo').value = '';
    document.getElementById('form-objetivo-nombre').value = '';
    document.getElementById('form-objetivo-descripcion').value = '';
    document.getElementById('form-objetivo-responsable').value = '';
    document.getElementById('form-objetivo-ponderacion').value = '25';
    document.getElementById('modal-objetivo-title').textContent = 'Nuevo Objetivo Estratégico';
    document.getElementById('modal-form-objetivo').classList.remove('hidden');
  },

  async editarObjetivo(id) {
    const obj = await api.getObjetivo(id);
    document.getElementById('form-objetivo-id').value = obj.id;
    document.getElementById('form-objetivo-codigo').value = obj.codigo;
    document.getElementById('form-objetivo-nombre').value = obj.nombre;
    document.getElementById('form-objetivo-descripcion').value = obj.descripcion || '';
    document.getElementById('form-objetivo-perspectiva').value = obj.perspectiva;
    document.getElementById('form-objetivo-modulo').value = obj.modulo_odoo_id || '';
    document.getElementById('form-objetivo-responsable').value = obj.responsable || '';
    document.getElementById('form-objetivo-prioridad').value = obj.prioridad;
    document.getElementById('form-objetivo-ponderacion').value = obj.ponderacion;
    document.getElementById('modal-objetivo-title').textContent = 'Editar Objetivo Estratégico';
    document.getElementById('modal-form-objetivo').classList.remove('hidden');
  },

  async guardarObjetivo(e) {
    e.preventDefault();
    const id = document.getElementById('form-objetivo-id').value;
    const data = {
      codigo: document.getElementById('form-objetivo-codigo').value.trim(),
      nombre: document.getElementById('form-objetivo-nombre').value.trim(),
      descripcion: document.getElementById('form-objetivo-descripcion').value.trim(),
      perspectiva: document.getElementById('form-objetivo-perspectiva').value,
      modulo_odoo_id: parseInt(document.getElementById('form-objetivo-modulo').value) || null,
      responsable: document.getElementById('form-objetivo-responsable').value.trim(),
      prioridad: document.getElementById('form-objetivo-prioridad').value,
      ponderacion: parseFloat(document.getElementById('form-objetivo-ponderacion').value) || 25.0
    };

    try {
      if (id) {
        await api.updateObjetivo(id, data);
        state.showToast('Objetivo actualizado correctamente');
      } else {
        await api.createObjetivo(data);
        state.showToast('Objetivo creado exitosamente');
      }
      document.getElementById('modal-form-objetivo').classList.add('hidden');
      await this.renderObjetivos();
    } catch (err) {
      state.showToast(err.message, 'error');
    }
  },

  async confirmarEliminarObjetivo(id, codigo) {
    if (confirm(`¿Está seguro de eliminar el objetivo ${codigo}? Esta acción afectará los cálculos del BSC.`)) {
      try {
        await api.deleteObjetivo(id);
        state.showToast(`Objetivo ${codigo} eliminado exitosamente`);
        await this.renderObjetivos();
      } catch (err) {
        state.showToast('Error al eliminar objetivo', 'error');
      }
    }
  },

  // ==========================================
  // 4. GESTIÓN DE INDICADORES KPI (CRUD + CHART)
  // ==========================================
  async renderKpis() {
    try {
      const filters = {};
      if (state.filters.kpis.perspectiva !== 'TODAS') filters.perspectiva = state.filters.kpis.perspectiva;
      if (state.filters.kpis.modulo !== 'TODOS') filters.modulo_odoo = state.filters.kpis.modulo;
      if (state.filters.kpis.semaforo !== 'TODOS') filters.semaforo = state.filters.kpis.semaforo;
      if (state.filters.kpis.sentido !== 'TODOS') filters.sentido = state.filters.kpis.sentido;
      if (state.filters.kpis.search) filters.search = state.filters.kpis.search;

      const kpis = await api.getKpis(filters);
      const tbody = document.getElementById('kpis-table-body');
      if (!tbody) return;

      tbody.innerHTML = kpis.map(k => `
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
          <td class="py-3 px-4 font-mono font-bold text-xs text-blue-600">${k.codigo}</td>
          <td class="py-3 px-4">
            <span class="font-semibold text-slate-800 text-sm block">${k.nombre}</span>
            <span class="text-xs text-slate-400">${k.formula || ''}</span>
          </td>
          <td class="py-3 px-4">
            <span class="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">${k.modulo_odoo}</span>
            <span class="block text-[10px] text-slate-400 font-mono">${k.modelo_odoo}</span>
          </td>
          <td class="py-3 px-4 text-xs font-semibold text-slate-700 text-center">${k.sentido.replace('_', ' ')}</td>
          <td class="py-3 px-4 text-xs font-bold text-slate-700 text-right">${k.meta} ${k.unidad}</td>
          <td class="py-3 px-4 text-xs font-extrabold text-slate-900 text-right">${k.valor_actual !== null ? k.valor_actual : 'S/D'} ${k.unidad}</td>
          <td class="py-3 px-4 text-xs font-bold text-center ${k.porcentaje_cumplimiento >= 75 ? 'text-slate-800' : 'text-rose-600'}">
            ${k.porcentaje_cumplimiento !== null ? `${k.porcentaje_cumplimiento}%` : 'S/D'}
          </td>
          <td class="py-3 px-4 text-center">
            ${this.renderSemaforoBadge(k.semaforo)}
          </td>
          <td class="py-3 px-4 text-right space-x-1">
            <button onclick="app.abrirModalHistorialKpi(${k.id})" title="Ver Evolución Histórica" class="text-blue-500 hover:text-blue-700 p-1.5"><i class="fas fa-chart-line"></i></button>
            <button onclick="app.abrirModalMedicionRapida(${k.id}, '${k.codigo}', '${k.nombre.replace(/'/g, "\\'")}', '${k.unidad}')" title="Registrar Medición" class="text-emerald-500 hover:text-emerald-700 p-1.5"><i class="fas fa-plus-circle"></i></button>
            <button onclick="app.editarKpi(${k.id})" title="Editar KPI" class="text-slate-500 hover:text-blue-600 p-1.5"><i class="fas fa-edit"></i></button>
            <button onclick="app.confirmarEliminarKpi(${k.id}, '${k.codigo}')" title="Eliminar KPI" class="admin-only text-slate-400 hover:text-rose-600 p-1.5"><i class="fas fa-trash"></i></button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  },

  async abrirModalHistorialKpi(id) {
    try {
      const data = await api.getKpiHistorial(id);
      document.getElementById('hist-kpi-codigo').textContent = data.codigo;
      document.getElementById('hist-kpi-nombre').textContent = data.nombre;
      document.getElementById('hist-kpi-meta').textContent = `${data.meta} ${data.unidad}`;
      document.getElementById('hist-kpi-modulo').textContent = `${data.modulo_odoo} [${data.modelo_odoo}]`;

      charts.renderKpiHistorial('chart-kpi-historial', data);

      const tbody = document.getElementById('hist-kpi-table-body');
      if (tbody) {
        tbody.innerHTML = data.mediciones.map(m => `
          <tr class="border-b border-slate-100 text-xs">
            <td class="py-2 px-3 font-semibold text-slate-700">${m.periodo}</td>
            <td class="py-2 px-3 text-slate-500">${m.fecha}</td>
            <td class="py-2 px-3 font-bold text-slate-800 text-right">${m.valor_obtenido} ${m.unidad}</td>
            <td class="py-2 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${m.origen === 'ODOO_17_SYNC' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}">
                ${m.origen}
              </span>
            </td>
            <td class="py-2 px-3 text-slate-600">${m.observaciones || ''}</td>
          </tr>
        `).join('') || '<tr><td colspan="5" class="py-4 text-center text-slate-400">Sin historial registrado</td></tr>';
      }

      document.getElementById('modal-kpi-historial').classList.remove('hidden');
    } catch (err) {
      console.error(err);
      state.showToast('Error cargando historial de KPI', 'error');
    }
  },

  async abrirModalNuevoKpi() {
    const objetivos = await api.getObjetivos();
    const selObj = document.getElementById('form-kpi-objetivo');
    selObj.innerHTML = objetivos.map(o => `<option value="${o.id}">[${o.codigo}] ${o.nombre}</option>`).join('');

    document.getElementById('form-kpi-id').value = '';
    document.getElementById('form-kpi-codigo').value = '';
    document.getElementById('form-kpi-nombre').value = '';
    document.getElementById('form-kpi-formula').value = '';
    document.getElementById('form-kpi-meta').value = '100';
    document.getElementById('form-kpi-umbral-verde').value = '90';
    document.getElementById('form-kpi-umbral-amarillo').value = '75';
    document.getElementById('modal-form-kpi').classList.remove('hidden');
  },

  async editarKpi(id) {
    const kpi = await api.getKpi(id);
    const objetivos = await api.getObjetivos();
    const selObj = document.getElementById('form-kpi-objetivo');
    selObj.innerHTML = objetivos.map(o => `<option value="${o.id}" ${o.id === kpi.objetivo_id ? 'selected' : ''}>[${o.codigo}] ${o.nombre}</option>`).join('');

    document.getElementById('form-kpi-id').value = kpi.id;
    document.getElementById('form-kpi-codigo').value = kpi.codigo;
    document.getElementById('form-kpi-nombre').value = kpi.nombre;
    document.getElementById('form-kpi-formula').value = kpi.formula || '';
    document.getElementById('form-kpi-unidad').value = kpi.unidad;
    document.getElementById('form-kpi-modulo').value = kpi.modulo_odoo;
    document.getElementById('form-kpi-modelo').value = kpi.modelo_odoo;
    document.getElementById('form-kpi-sentido').value = kpi.sentido;
    document.getElementById('form-kpi-meta').value = kpi.meta;
    document.getElementById('form-kpi-umbral-verde').value = kpi.umbral_verde;
    document.getElementById('form-kpi-umbral-amarillo').value = kpi.umbral_amarillo;
    document.getElementById('form-kpi-responsable').value = kpi.responsable || '';

    document.getElementById('modal-form-kpi').classList.remove('hidden');
  },

  async guardarKpi(e) {
    e.preventDefault();
    const id = document.getElementById('form-kpi-id').value;
    const data = {
      codigo: document.getElementById('form-kpi-codigo').value.trim(),
      nombre: document.getElementById('form-kpi-nombre').value.trim(),
      formula: document.getElementById('form-kpi-formula').value.trim(),
      unidad: document.getElementById('form-kpi-unidad').value,
      objetivo_id: parseInt(document.getElementById('form-kpi-objetivo').value),
      modulo_odoo: document.getElementById('form-kpi-modulo').value.trim(),
      modelo_odoo: document.getElementById('form-kpi-modelo').value.trim(),
      sentido: document.getElementById('form-kpi-sentido').value,
      meta: parseFloat(document.getElementById('form-kpi-meta').value),
      umbral_verde: parseFloat(document.getElementById('form-kpi-umbral-verde').value),
      umbral_amarillo: parseFloat(document.getElementById('form-kpi-umbral-amarillo').value),
      responsable: document.getElementById('form-kpi-responsable').value.trim()
    };

    try {
      if (id) {
        await api.updateKpi(id, data);
        state.showToast('KPI actualizado correctamente');
      } else {
        await api.createKpi(data);
        state.showToast('KPI creado exitosamente');
      }
      document.getElementById('modal-form-kpi').classList.add('hidden');
      await this.renderKpis();
    } catch (err) {
      state.showToast(err.message, 'error');
    }
  },

  async confirmarEliminarKpi(id, codigo) {
    if (confirm(`¿Eliminar KPI ${codigo}? Todas sus mediciones serán removidas.`)) {
      try {
        await api.deleteKpi(id);
        state.showToast(`KPI ${codigo} eliminado exitosamente`);
        await this.renderKpis();
      } catch (err) {
        state.showToast('Error al eliminar KPI', 'error');
      }
    }
  },

  // ==========================================
  // 5. REGISTRO DE RESULTADOS (MEDICIONES)
  // ==========================================
  async renderMediciones() {
    try {
      const kpis = await api.getKpis();
      const selKpi = document.getElementById('form-med-kpi');
      if (selKpi) {
        selKpi.innerHTML = '<option value="">Seleccione KPI a medir...</option>' + kpis.map(k => `
          <option value="${k.id}" data-unidad="${k.unidad}" data-sentido="${k.sentido}" data-meta="${k.meta}">
            [${k.codigo}] ${k.nombre} (Meta: ${k.meta} ${k.unidad})
          </option>
        `).join('');
      }

      const filters = {};
      if (state.filters.mediciones.origen !== 'TODOS') filters.origen = state.filters.mediciones.origen;

      const mediciones = await api.getMediciones(filters);
      const tbody = document.getElementById('mediciones-table-body');
      if (!tbody) return;

      tbody.innerHTML = mediciones.map(m => `
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors text-xs">
          <td class="py-3 px-4 font-bold text-slate-800">${m.periodo}</td>
          <td class="py-3 px-4 text-slate-500">${m.fecha}</td>
          <td class="py-3 px-4 font-semibold text-slate-700">KPI #${m.kpi_id}</td>
          <td class="py-3 px-4 font-extrabold text-slate-900 text-right">${m.valor_obtenido}</td>
          <td class="py-3 px-4">
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
              m.origen === 'ODOO_17_SYNC' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-700'
            }">
              <i class="fas ${m.origen === 'ODOO_17_SYNC' ? 'fa-sync-alt' : 'fa-pen'} mr-1"></i> ${m.origen}
            </span>
          </td>
          <td class="py-3 px-4 text-slate-500 max-w-xs truncate">${m.observaciones || ''}</td>
          <td class="py-3 px-4 text-slate-600">${m.responsable || ''}</td>
          <td class="py-3 px-4 text-right">
            <button onclick="app.eliminarMedicion(${m.id})" class="text-slate-400 hover:text-rose-600 p-1"><i class="fas fa-trash"></i></button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  },

  abrirModalMedicionRapida(kpiId, kpiCodigo, kpiNombre, kpiUnidad) {
    const selKpi = document.getElementById('form-med-kpi');
    if (selKpi) selKpi.value = kpiId;
    document.getElementById('form-med-fecha').value = new Date().toISOString().split('T')[0];
    document.getElementById('form-med-responsable').value = state.currentUser ? state.currentUser.nombre : '';
    document.getElementById('modal-registro-medicion').classList.remove('hidden');
  },

  async guardarMedicion(e) {
    e.preventDefault();
    const data = {
      kpi_id: parseInt(document.getElementById('form-med-kpi').value),
      periodo: document.getElementById('form-med-periodo').value,
      fecha: document.getElementById('form-med-fecha').value,
      valor_obtenido: parseFloat(document.getElementById('form-med-valor').value),
      observaciones: document.getElementById('form-med-observaciones').value.trim(),
      responsable: document.getElementById('form-med-responsable').value.trim(),
      origen: 'MANUAL'
    };

    try {
      await api.createMedicion(data);
      state.showToast('Medición registrada y BSC recalculado automáticamente');
      document.getElementById('modal-registro-medicion').classList.add('hidden');
      await this.refreshCurrentView();
    } catch (err) {
      state.showToast(err.message, 'error');
    }
  },

  async eliminarMedicion(id) {
    if (confirm('¿Eliminar esta medición? El semáforo del KPI será recalculado automáticamente.')) {
      try {
        await api.deleteMedicion(id);
        state.showToast('Medición eliminada y scorecard actualizado');
        await this.renderMediciones();
      } catch (err) {
        state.showToast('Error eliminando medición', 'error');
      }
    }
  },

  // ==========================================
  // 6. SINCRONIZACIÓN ODOO 17 ERP (XML-RPC / FALLBACK)
  // ==========================================
  async ejecutarSincronizacionOdoo() {
    const modal = document.getElementById('modal-sync-odoo-status');
    const logsEl = document.getElementById('sync-odoo-logs');
    if (modal) modal.classList.remove('hidden');
    if (logsEl) {
      logsEl.innerHTML = `
        <div class="flex items-center space-x-3 text-blue-600 mb-2">
          <i class="fas fa-spinner fa-spin text-lg"></i>
          <span class="font-semibold text-sm">Conectando con servidor Odoo 17 ERP (agroperuvian_db)...</span>
        </div>
        <p class="text-xs text-slate-500 font-mono">Modelos consultados: sale.order, crm.lead, mrp.production, pos.session, purchase.order...</p>
      `;
    }

    try {
      const res = await api.syncOdoo(state.activePeriod);
      setTimeout(() => {
        if (logsEl) {
          logsEl.innerHTML = `
            <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-3 mb-3 text-emerald-800">
              <div class="flex items-center space-x-2 font-bold text-sm mb-1">
                <i class="fas fa-check-circle text-emerald-600 text-base"></i>
                <span>${res.mensaje}</span>
              </div>
              <p class="text-xs text-emerald-700">Modo de integración: <strong>${res.origen}</strong></p>
            </div>
            <div class="max-h-60 overflow-y-auto space-y-2">
              ${res.detalles.map(d => `
                <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                  <div>
                    <span class="font-bold text-slate-800">[${d.kpi_codigo}] ${d.kpi_nombre}</span>
                    <span class="block text-[11px] text-slate-500">${d.glosa}</span>
                  </div>
                  <div class="text-right">
                    <span class="font-extrabold text-blue-600">${d.valor_obtenido} ${d.unidad}</span>
                    <span class="block text-[10px] text-slate-400 font-mono">${d.modelo_odoo}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          `;
        }
        state.showToast('¡Sincronización con Odoo 17 completada exitosamente!', 'success');
        this.refreshCurrentView();
      }, 800);
    } catch (err) {
      if (logsEl) {
        logsEl.innerHTML = `
          <div class="bg-rose-50 border border-rose-200 rounded-xl p-3 text-rose-800">
            <span class="font-bold text-sm">Error en sincronización:</span>
            <p class="text-xs mt-1">${err.message}</p>
          </div>
        `;
      }
    }
  },

  // ==========================================
  // 7. INICIATIVAS ESTRATÉGICAS
  // ==========================================
  async renderIniciativas() {
    try {
      const [iniciativas, resumen] = await Promise.all([
        api.getIniciativas({ estado: state.filters.iniciativas.estado }),
        api.getIniciativasResumen()
      ]);

      // Resumen
      document.getElementById('inic-presupuesto-total').textContent = `S/ ${resumen.presupuesto_total.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`;
      document.getElementById('inic-avance-promedio').textContent = `${resumen.promedio_avance}%`;
      document.getElementById('inic-count-ejecucion').textContent = resumen.en_ejecucion;
      document.getElementById('inic-count-retrasadas').textContent = resumen.retrasadas;
      document.getElementById('inic-count-finalizadas').textContent = resumen.finalizadas;

      const container = document.getElementById('iniciativas-cards-container');
      if (!container) return;

      container.innerHTML = iniciativas.map(i => `
        <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-blue-300 transition-all">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-mono font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">${i.codigo}</span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${
              i.estado === 'FINALIZADA' ? 'bg-emerald-100 text-emerald-700' :
              i.estado === 'RETRASADA' ? 'bg-rose-100 text-rose-700' : 'bg-blue-100 text-blue-700'
            }">
              ${i.estado.replace('_', ' ')}
            </span>
          </div>
          <h4 class="font-bold text-slate-800 text-base mb-2">${i.nombre}</h4>
          <p class="text-xs text-slate-500 mb-4 line-clamp-2">${i.descripcion || ''}</p>

          <div class="bg-slate-50 rounded-xl p-3 mb-4 space-y-1.5 text-xs">
            <div class="flex justify-between text-slate-600">
              <span>Presupuesto Invertido:</span>
              <strong class="text-slate-800">S/ ${i.presupuesto.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</strong>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>Módulo Odoo 17:</span>
              <span class="font-medium text-slate-700">${i.modulo_odoo || 'General'}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>Responsable:</span>
              <span class="font-medium text-slate-700">${i.responsable || 'Equipo'}</span>
            </div>
          </div>

          <!-- Barra de avance -->
          <div class="mb-4">
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-600">Porcentaje de Avance</span>
              <span class="text-blue-600">${i.porcentaje_avance}%</span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2">
              <div class="h-2 rounded-full ${
                i.porcentaje_avance >= 100 ? 'bg-emerald-500' :
                i.estado === 'RETRASADA' ? 'bg-rose-500' : 'bg-blue-500'
              }" style="width: ${i.porcentaje_avance}%"></div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
            <span class="text-[11px] text-slate-400">Plazo: ${i.fecha_fin || 'Sin fecha'}</span>
            <div class="space-x-1">
              <button onclick="app.editarIniciativa(${i.id})" class="text-slate-500 hover:text-blue-600 font-semibold p-1"><i class="fas fa-edit"></i></button>
              <button onclick="app.eliminarIniciativa(${i.id}, '${i.codigo}')" class="admin-only text-slate-400 hover:text-rose-600 font-semibold p-1"><i class="fas fa-trash"></i></button>
            </div>
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  },

  async abrirModalNuevaIniciativa() {
    const objetivos = await api.getObjetivos();
    const selObj = document.getElementById('form-inic-objetivo');
    selObj.innerHTML = objetivos.map(o => `<option value="${o.id}">[${o.codigo}] ${o.nombre}</option>`).join('');

    document.getElementById('form-inic-id').value = '';
    document.getElementById('form-inic-codigo').value = '';
    document.getElementById('form-inic-nombre').value = '';
    document.getElementById('form-inic-descripcion').value = '';
    document.getElementById('form-inic-presupuesto').value = '20000';
    document.getElementById('form-inic-avance').value = '0';
    document.getElementById('modal-form-iniciativa').classList.remove('hidden');
  },

  async editarIniciativa(id) {
    const iniciativas = await api.getIniciativas();
    const ini = iniciativas.find(i => i.id === id);
    if (!ini) return;

    const objetivos = await api.getObjetivos();
    const selObj = document.getElementById('form-inic-objetivo');
    selObj.innerHTML = objetivos.map(o => `<option value="${o.id}" ${o.id === ini.objetivo_id ? 'selected' : ''}>[${o.codigo}] ${o.nombre}</option>`).join('');

    document.getElementById('form-inic-id').value = ini.id;
    document.getElementById('form-inic-codigo').value = ini.codigo;
    document.getElementById('form-inic-nombre').value = ini.nombre;
    document.getElementById('form-inic-descripcion').value = ini.descripcion || '';
    document.getElementById('form-inic-presupuesto').value = ini.presupuesto;
    document.getElementById('form-inic-avance').value = ini.porcentaje_avance;
    document.getElementById('form-inic-estado').value = ini.estado;
    document.getElementById('form-inic-modulo').value = ini.modulo_odoo || '';
    document.getElementById('form-inic-responsable').value = ini.responsable || '';

    document.getElementById('modal-form-iniciativa').classList.remove('hidden');
  },

  async guardarIniciativa(e) {
    e.preventDefault();
    const id = document.getElementById('form-inic-id').value;
    const data = {
      codigo: document.getElementById('form-inic-codigo').value.trim(),
      nombre: document.getElementById('form-inic-nombre').value.trim(),
      descripcion: document.getElementById('form-inic-descripcion').value.trim(),
      objetivo_id: parseInt(document.getElementById('form-inic-objetivo').value),
      presupuesto: parseFloat(document.getElementById('form-inic-presupuesto').value) || 0.0,
      porcentaje_avance: parseFloat(document.getElementById('form-inic-avance').value) || 0.0,
      estado: document.getElementById('form-inic-estado').value,
      modulo_odoo: document.getElementById('form-inic-modulo').value.trim(),
      responsable: document.getElementById('form-inic-responsable').value.trim()
    };

    try {
      if (id) {
        await api.updateIniciativa(id, data);
        state.showToast('Iniciativa estratégica actualizada');
      } else {
        await api.createIniciativa(data);
        state.showToast('Iniciativa creada exitosamente');
      }
      document.getElementById('modal-form-iniciativa').classList.add('hidden');
      await this.renderIniciativas();
    } catch (err) {
      state.showToast(err.message, 'error');
    }
  },

  async eliminarIniciativa(id, codigo) {
    if (confirm(`¿Eliminar la iniciativa ${codigo}?`)) {
      try {
        await api.deleteIniciativa(id);
        state.showToast(`Iniciativa ${codigo} eliminada exitosamente`);
        await this.renderIniciativas();
      } catch (err) {
        state.showToast('Error al eliminar iniciativa', 'error');
      }
    }
  },

  // ==========================================
  // 8. REPORTES EJECUTIVOS (CSV & PRINT/PDF)
  // ==========================================
  async renderReportes() {
    try {
      const data = await api.getReporteConsolidado({ periodo: state.activePeriod });
      document.getElementById('rep-periodo-badge').textContent = data.periodo;
      document.getElementById('rep-global-pct').textContent = `${data.resumen_ejecutivo.cumplimiento_global}%`;

      const tbody = document.getElementById('rep-kpis-table-body');
      if (tbody) {
        tbody.innerHTML = data.kpis.map(k => `
          <tr class="border-b border-slate-200 text-xs">
            <td class="py-2.5 px-3 font-mono font-bold text-slate-700">${k.codigo}</td>
            <td class="py-2.5 px-3 font-medium text-slate-800">${k.nombre}</td>
            <td class="py-2.5 px-3 text-slate-600">${k.perspectiva}</td>
            <td class="py-2.5 px-3 text-slate-600">${k.modulo_odoo}</td>
            <td class="py-2.5 px-3 text-right text-slate-700 font-semibold">${k.meta} ${k.unidad}</td>
            <td class="py-2.5 px-3 text-right font-extrabold text-slate-900">${k.valor_actual !== null ? k.valor_actual : 'S/D'} ${k.unidad}</td>
            <td class="py-2.5 px-3 text-center font-bold">${k.porcentaje_cumplimiento !== null ? `${k.porcentaje_cumplimiento}%` : 'S/D'}</td>
            <td class="py-2.5 px-3 text-center">${this.renderSemaforoBadge(k.semaforo)}</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error(err);
    }
  },

  exportarCSV() {
    const url = `/api/v1/reportes/export-csv?periodo=${state.activePeriod}`;
    window.open(url, '_blank');
  },

  imprimirPDF() {
    window.print();
  },

  // ==========================================
  // 9. ADMINISTRACIÓN DEL SISTEMA
  // ==========================================
  async renderAdmin() {
    try {
      const [usuarios, periodos, modulos, statusSync] = await Promise.all([
        api.getUsuarios(),
        api.getPeriodos(),
        api.getModulosOdoo(),
        api.getSyncStatus()
      ]);

      // Tabla de Usuarios
      const tbodyUsers = document.getElementById('admin-users-table-body');
      if (tbodyUsers) {
        tbodyUsers.innerHTML = usuarios.map(u => `
          <tr class="border-b border-slate-100 text-xs">
            <td class="py-2.5 px-3 font-mono font-bold text-blue-600">${u.username}</td>
            <td class="py-2.5 px-3 font-semibold text-slate-800">${u.nombre}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded-full font-bold ${
                u.rol === 'ADMIN' ? 'bg-purple-100 text-purple-700' :
                u.rol === 'GERENTE' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'
              }">${u.rol}</span>
            </td>
            <td class="py-2.5 px-3 text-slate-600">${u.area || ''}</td>
            <td class="py-2.5 px-3 text-right">
              ${u.username !== 'admin' ? `
                <button onclick="app.eliminarUsuario(${u.id})" class="text-rose-500 hover:text-rose-700"><i class="fas fa-trash"></i></button>
              ` : '<span class="text-slate-300 text-[10px]">Protegido</span>'}
            </td>
          </tr>
        `).join('');
      }

      // Tabla de Períodos
      const tbodyPer = document.getElementById('admin-periodos-table-body');
      if (tbodyPer) {
        tbodyPer.innerHTML = periodos.map(p => `
          <tr class="border-b border-slate-100 text-xs">
            <td class="py-2.5 px-3 font-mono font-bold text-slate-800">${p.codigo}</td>
            <td class="py-2.5 px-3 font-semibold text-slate-800">${p.nombre}</td>
            <td class="py-2.5 px-3 text-center">
              ${p.activo ? '<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">Activo Oficial</span>' : '<span class="text-slate-400">Histórico</span>'}
            </td>
            <td class="py-2.5 px-3 text-right">
              ${!p.activo ? `
                <button onclick="app.activarPeriodo(${p.id})" class="text-xs bg-blue-50 text-blue-600 font-semibold px-2 py-1 rounded hover:bg-blue-100">Fijar Activo</button>
              ` : ''}
            </td>
          </tr>
        `).join('');
      }

      // Tabla de Módulos Odoo
      const tbodyMod = document.getElementById('admin-modulos-table-body');
      if (tbodyMod) {
        tbodyMod.innerHTML = modulos.map(m => `
          <tr class="border-b border-slate-100 text-xs">
            <td class="py-2.5 px-3 font-mono font-bold text-purple-600">${m.codigo}</td>
            <td class="py-2.5 px-3 font-semibold text-slate-800">${m.nombre_modulo_odoo}</td>
            <td class="py-2.5 px-3 font-mono text-slate-600">${m.modelo_tecnico}</td>
            <td class="py-2.5 px-3 text-slate-600">${m.responsable}</td>
          </tr>
        `).join('');
      }

      // Panel Diagnóstico
      const diagOdooEl = document.getElementById('diag-odoo-status');
      if (diagOdooEl) {
        diagOdooEl.innerHTML = `
          <div class="p-4 rounded-xl border ${statusSync.odoo_17.conectado ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'}">
            <div class="flex items-center space-x-2 font-bold ${statusSync.odoo_17.conectado ? 'text-emerald-800' : 'text-amber-800'} mb-1">
              <i class="fas ${statusSync.odoo_17.conectado ? 'fa-check-circle' : 'fa-info-circle'}"></i>
              <span>Odoo 17 ERP (agroperuvian_db): ${statusSync.odoo_17.modo}</span>
            </div>
            <p class="text-xs text-slate-600">${statusSync.odoo_17.mensaje}</p>
            <p class="text-[11px] font-mono text-slate-400 mt-1">Host: ${statusSync.configuracion.odoo_url} | DB: ${statusSync.configuracion.odoo_db}</p>
          </div>
        `;
      }
    } catch (err) {
      console.error(err);
    }
  },

  async activarPeriodo(id) {
    try {
      await api.activarPeriodo(id);
      state.showToast('Período oficial activado exitosamente');
      await this.loadInitialCatalogs();
      await this.renderAdmin();
    } catch (err) {
      state.showToast('Error activando período', 'error');
    }
  },

  async eliminarUsuario(id) {
    if (confirm('¿Eliminar este usuario del sistema?')) {
      try {
        await api.deleteUsuario(id);
        state.showToast('Usuario eliminado exitosamente');
        await this.renderAdmin();
      } catch (err) {
        state.showToast(err.message, 'error');
      }
    }
  },

  // ==========================================
  // DEMO LOGIN QUICK SWITCHER
  // ==========================================
  cambiarUsuarioDemo(username, password) {
    api.login(username, password)
      .then(res => {
        state.setUser(res.user, res.access_token);
        this.updateUserUI();
        state.showToast(`Sesión iniciada como ${res.user.nombre} (${res.user.rol})`, 'success');
        this.refreshCurrentView();
      })
      .catch(err => {
        state.showToast(err.message, 'error');
      });
  },

  logout() {
    state.setUser(null, null);
    state.showToast('Sesión cerrada. Seleccione una cuenta demo para continuar.', 'info');
    document.getElementById('modal-login-demo').classList.remove('hidden');
  },

  // Helper visual Semáforos
  renderSemaforoBadge(semaforo) {
    if (semaforo === 'CUMPLIDO') {
      return '<span class="inline-flex items-center text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800"><span class="pulse-dot bg-emerald-500 mr-1.5"></span> CUMPLIDO</span>';
    } else if (semaforo === 'EN_ALERTA') {
      return '<span class="inline-flex items-center text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800"><span class="pulse-dot bg-amber-500 mr-1.5"></span> EN ALERTA</span>';
    } else if (semaforo === 'CRITICO') {
      return '<span class="inline-flex items-center text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800"><span class="pulse-dot bg-rose-500 mr-1.5"></span> CRÍTICO</span>';
    }
    return '<span class="inline-flex items-center text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600"><span class="w-2 h-2 rounded-full bg-slate-400 mr-1.5"></span> SIN DATOS</span>';
  },

  renderSemaforoDot(semaforo) {
    if (semaforo === 'CUMPLIDO') return '<span class="w-3 h-3 rounded-full bg-emerald-500 shadow-sm" title="Cumplido"></span>';
    if (semaforo === 'EN_ALERTA') return '<span class="w-3 h-3 rounded-full bg-amber-500 shadow-sm" title="En Alerta"></span>';
    if (semaforo === 'CRITICO') return '<span class="w-3 h-3 rounded-full bg-rose-500 shadow-sm" title="Crítico"></span>';
    return '<span class="w-3 h-3 rounded-full bg-slate-400 shadow-sm" title="Sin Datos"></span>';
  }
};
