/* A presentation of committed artifacts; no metrics or bootstrap samples are recomputed. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const names = { auc_roc: 'AUC-ROC', aff_f1: 'Affiliation F1' };
  let data, left = 'auc_roc', right = 'aff_f1', tableMetric = 'auc_roc', selected = null;
  const svgNode = (tag, attributes, content) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (content !== undefined) node.textContent = content;
    return node;
  };
  const record = (metric, model) => data.retention.metrics[metric].models.find(row => row.model === model);
  document.querySelector('.theme-toggle').addEventListener('click', event => {
    const light = document.documentElement.dataset.theme !== 'light';
    document.documentElement.dataset.theme = light ? 'light' : 'dark';
    event.currentTarget.textContent = light ? 'Dark' : 'Light';
    event.currentTarget.setAttribute('aria-label', `Switch to ${light ? 'dark' : 'light'} theme`);
  });

  function describeSelection() {
    if (!selected) {
      byId('rank-selection').textContent = ['CNN', 'USAD'].map(model => `${model}: #${record(left, model).point_rank} → #${record(right, model).point_rank}`).join(' · ');
      return;
    }
    const a = record(left, selected), b = record(right, selected);
    byId('rank-selection').textContent = `${selected} · ${names[left]} #${a.point_rank} (mean ${a.mean_score.toFixed(6)}) → ${names[right]} #${b.point_rank} (mean ${b.mean_score.toFixed(6)}). 95% collection-bootstrap rank intervals: ${a.rank_lo}–${a.rank_hi} and ${b.rank_lo}–${b.rank_hi}.`;
  }

  function select(model) {
    selected = model;
    document.querySelectorAll('.rank-model').forEach(node => {
      node.classList.toggle('selected', node.dataset.model === model);
      node.setAttribute('aria-pressed', String(node.dataset.model === model));
    });
    document.querySelectorAll('#rank-table-body tr').forEach(row => { row.dataset.selected = String(row.dataset.model === model); });
    describeSelection();
  }

  function drawChart() {
    const chart = byId('rank-chart');
    chart.replaceChildren();
    byId('left-metric').textContent = names[left];
    byId('right-metric').textContent = names[right];
    for (const a of data.retention.metrics[left].models) {
      const b = record(right, a.model);
      const y1 = 26 + (a.point_rank - 1) * 21.6, y2 = 26 + (b.point_rank - 1) * 21.6;
      const path = `M150 ${y1} C340 ${y1} 510 ${y2} 700 ${y2}`;
      const group = svgNode('g', {
        class: `rank-model ${['CNN', 'USAD'].includes(a.model) ? 'emphasis' : ''}`,
        'data-model': a.model, role: 'button', tabindex: '0', 'aria-pressed': 'false',
        'aria-label': `Inspect ${a.model}: ${names[left]} rank ${a.point_rank}, ${names[right]} rank ${b.point_rank}`,
      });
      group.append(svgNode('path', { d: path }), svgNode('path', { d: path, class: 'hit-path', 'aria-hidden': 'true' }), svgNode('circle', { cx: 150, cy: y1, r: 2.8 }), svgNode('circle', { cx: 700, cy: y2, r: 2.8 }), svgNode('text', { x: 137, y: y1 + 4, 'text-anchor': 'end' }, a.model), svgNode('text', { x: 713, y: y2 + 4 }, a.model));
      group.addEventListener('click', () => select(a.model));
      group.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(a.model); }
      });
      chart.append(group);
    }
    if (selected) select(selected); else describeSelection();
  }

  function drawTable() {
    const rows = data.retention.metrics[tableMetric].models;
    const body = byId('rank-table-body');
    body.replaceChildren();
    document.querySelectorAll('[data-metric]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.metric === tableMetric)));
    byId('retention-summary').textContent = `${rows[0].model} keeps rank 1 in ${(rows[0].retention * 100).toFixed(1)}% of the ${data.retention.n_boot.toLocaleString('en-US')} recorded collection-bootstrap samples.`;
    for (const row of rows) {
      const tr = document.createElement('tr'); tr.dataset.model = row.model; tr.dataset.selected = String(selected === row.model);
      const first = document.createElement('td'), button = document.createElement('button');
      button.type = 'button'; button.textContent = row.model;
      button.setAttribute('aria-label', `Inspect ${row.model} in the rank chart`);
      button.addEventListener('click', () => { select(row.model); byId('rank-selection').scrollIntoView({ block: 'center' }); });
      first.append(button); tr.append(first);
      for (const value of [`#${row.point_rank}`, row.mean_score.toFixed(6), `${row.rank_lo}–${row.rank_hi}`, `${(row.retention * 100).toFixed(1)}%`]) {
        const cell = document.createElement('td'); cell.textContent = value; tr.append(cell);
      }
      body.append(tr);
    }
  }

  async function load() {
    byId('data-error').hidden = true;
    byId('swap-metrics').disabled = true;
    try {
      const response = await fetch('assets/recorded-ranks.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      data = await response.json();
      if (data.retention.metrics.auc_roc.models.length !== 25 || data.retention.metrics.aff_f1.models.length !== 25) throw new Error('Incomplete rank artifact');
      byId('flip-rate').replaceChildren(document.createTextNode((data.robustness.flip_rate.auc_vs_aff_f1 * 100).toFixed(1)));
      const percent = document.createElement('span'); percent.textContent = '%'; byId('flip-rate').append(percent);
      byId('null-rate').textContent = `${(data.robustness.flip_rate.random_ranking_null_mean * 100).toFixed(1)}%`;
      drawChart(); drawTable();
      byId('swap-metrics').disabled = false;
      document.documentElement.dataset.evidence = 'ready';
    } catch {
      byId('data-error').hidden = false;
      document.documentElement.dataset.evidence = 'error';
    }
  }
  byId('swap-metrics').addEventListener('click', () => { [left, right] = [right, left]; drawChart(); });
  byId('retry-data').addEventListener('click', load);
  byId('open-rank-table').addEventListener('click', () => { byId('rank-details').open = true; });
  document.querySelectorAll('[data-metric]').forEach(button => button.addEventListener('click', () => { if (data) { tableMetric = button.dataset.metric; drawTable(); } }));
  load();
})();
