// Administrador de Gráficos Chart.js - AGRO PERUVIAN FOODS S.A.C.
const charts = {
  instances: {},

  destroyChart(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  // 1. Gráfico Radar de Cumplimiento por Perspectiva BSC
  renderPerspectivasRadar(canvasId, perspectivas) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = ['Financiera', 'Cliente', 'Procesos Internos', 'Aprendizaje y Crecimiento'];
    const values = [
      perspectivas.FINANCIERA?.avance || 0,
      perspectivas.CLIENTE?.avance || 0,
      perspectivas.PROCESOS_INTERNOS?.avance || 0,
      perspectivas.APRENDIZAJE?.avance || 0
    ];

    this.instances[canvasId] = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [{
          label: '% Cumplimiento Actual',
          data: values,
          fill: true,
          backgroundColor: 'rgba(16, 185, 129, 0.25)',
          borderColor: '#10b981',
          pointBackgroundColor: '#059669',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#059669',
          borderWidth: 2.5
        }, {
          label: 'Meta Óptima (100%)',
          data: [100, 100, 100, 100],
          fill: false,
          borderColor: 'rgba(148, 163, 184, 0.6)',
          borderDash: [5, 5],
          pointRadius: 0,
          borderWidth: 1.5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            angleLines: { color: 'rgba(203, 213, 225, 0.5)' },
            grid: { color: 'rgba(226, 232, 240, 0.7)' },
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: {
              stepSize: 20,
              backdropColor: 'transparent',
              font: { size: 10 }
            },
            pointLabels: {
              font: { family: 'Inter', size: 11, weight: '600' },
              color: '#334155'
            }
          }
        },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.raw}%`
            }
          }
        }
      }
    });
  },

  // 2. Gráfico de Tendencia Histórica de Cumplimiento (Mayo a Octubre 2026)
  renderTendenciaHistorica(canvasId, tendencia) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = tendencia.map(t => t.nombre_periodo.replace(' 2026', ''));
    const values = tendencia.map(t => t.cumplimiento_promedio);

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.35)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: '% Cumplimiento Promedio Global',
          data: values,
          fill: true,
          backgroundColor: gradient,
          borderColor: '#3b82f6',
          borderWidth: 3,
          tension: 0.35,
          pointBackgroundColor: '#1d4ed8',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Cumplimiento: ${ctx.raw}%`
            }
          }
        },
        scales: {
          y: {
            suggestedMin: 50,
            suggestedMax: 100,
            grid: { color: 'rgba(241, 245, 249, 1)' },
            ticks: {
              callback: (v) => `${v}%`,
              font: { size: 11 }
            }
          },
          x: {
            grid: { display: false },
            ticks: { font: { size: 11, weight: '500' } }
          }
        }
      }
    });
  },

  // 3. Gráfico Doughnut de Estado de Semáforos
  renderSemaforosDoughnut(canvasId, semaforos) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dataValues = [
      semaforos.cumplidos || 0,
      semaforos.alerta || 0,
      semaforos.criticos || 0,
      semaforos.sin_datos || 0
    ];

    this.instances[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Cumplidos (Verde)', 'En Alerta (Amarillo)', 'Críticos (Rojo)', 'Sin Datos (Gris)'],
        datasets: [{
          data: dataValues,
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#94a3b8'],
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, padding: 12, font: { size: 11 } }
          }
        }
      }
    });
  },

  // 4. Gráfico de Barras Horizontales por Módulo Odoo 17
  renderDesempenoModulos(canvasId, modulosData) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const items = Object.values(modulosData);
    const labels = items.map(m => m.nombre.split(' ')[0]);
    const values = items.map(m => m.cumplimiento_promedio);

    // Colores dinámicos según el valor
    const bgColors = values.map(v => {
      if (v >= 90) return '#10b981';
      if (v >= 75) return '#f59e0b';
      if (v > 0) return '#ef4444';
      return '#94a3b8';
    });

    this.instances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: '% Cumplimiento',
          data: values,
          backgroundColor: bgColors,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (ctx) => items[ctx[0].dataIndex].nombre,
              label: (ctx) => `Cumplimiento: ${ctx.raw}% (${items[ctx.dataIndex].kpis_count} KPIs)`
            }
          }
        },
        scales: {
          x: {
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: { callback: (v) => `${v}%` }
          },
          y: {
            grid: { display: false },
            ticks: { font: { size: 11, weight: '600' } }
          }
        }
      }
    });
  },

  // 5. Gráfico de Evolución Histórica de un KPI Específico (Modal)
  renderKpiHistorial(canvasId, kpiHistorial) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = kpiHistorial.mediciones.map(m => m.periodo);
    const values = kpiHistorial.mediciones.map(m => m.valor_obtenido);
    const metaValues = Array(labels.length).fill(kpiHistorial.meta);

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: `Valor Obtenido (${kpiHistorial.unidad})`,
            data: values,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.15)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.3,
            pointRadius: 5,
            pointBackgroundColor: '#1d4ed8'
          },
          {
            label: `Meta (${kpiHistorial.meta} ${kpiHistorial.unidad})`,
            data: metaValues,
            borderColor: '#10b981',
            borderWidth: 2,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 14 } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} ${kpiHistorial.unidad}`
            }
          }
        },
        scales: {
          y: {
            grid: { color: 'rgba(241, 245, 249, 1)' }
          }
        }
      }
    });
  }
};
