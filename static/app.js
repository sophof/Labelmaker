import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const DEFAULT_BASE_COLOR = document.body.dataset.baseColor;
const DEFAULT_TEXT_COLOR = document.body.dataset.textColor;

// --- 3D preview setup ---
const container = document.getElementById('preview');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(devicePixelRatio);
renderer.setClearColor(0x1a1a1a);
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
camera.position.set(0, -80, 60);

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const dir = new THREE.DirectionalLight(0xffffff, 1.2);
dir.position.set(1, -1, 2);
scene.add(dir);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

let meshBase = null, meshText = null;

function resize() {
  const w = container.clientWidth, h = container.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(container);
resize();

(function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
})();

const loader = new STLLoader();
const matBase = new THREE.MeshPhongMaterial({ color: 0xffffff });
const matText = new THREE.MeshPhongMaterial({ color: 0x000000 });

function fitCamera(size) {
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim * 2.5;
  camera.position.set(0, -dist * 0.8, dist * 0.6);
  controls.target.set(0, 0, 0);
  controls.update();
}

function loadSTLs(baseUrl, textUrl, baseColor, textColor) {
  if (meshBase) { scene.remove(meshBase); meshBase = null; }
  if (meshText) { scene.remove(meshText); meshText = null; }

  matBase.color.set(baseColor);
  matText.color.set(textColor);

  loader.load(baseUrl, geo => {
    geo.computeBoundingBox();
    const center = new THREE.Vector3();
    const size = new THREE.Vector3();
    geo.boundingBox.getCenter(center);
    geo.boundingBox.getSize(size);
    geo.translate(-center.x, -center.y, -center.z);
    meshBase = new THREE.Mesh(geo, matBase);
    scene.add(meshBase);
    fitCamera(size);

    if (textUrl) {
      loader.load(textUrl, geoT => {
        geoT.translate(-center.x, -center.y, -center.z);
        meshText = new THREE.Mesh(geoT, matText);
        scene.add(meshText);
      });
    }
  });
}

// --- System/box/style data ---
let systemsData = [];

async function loadSystems() {
  const res = await fetch('/systems');
  systemsData = await res.json();

  const sysSelect = document.getElementById('system-select');
  sysSelect.innerHTML = systemsData.map(s =>
    `<option value="${s.id}">${s.name}</option>`
  ).join('');
  onSystemChange();
}

function onSystemChange() {
  const sysId = document.getElementById('system-select').value;

  const saved = localStorage.getItem(`colors_${sysId}`);
  if (saved) {
    const {base_color, text_color} = JSON.parse(saved);
    document.getElementById('base-color').value = base_color;
    document.getElementById('text-color').value = text_color;
  } else {
    document.getElementById('base-color').value = DEFAULT_BASE_COLOR;
    document.getElementById('text-color').value = DEFAULT_TEXT_COLOR;
  }

  const sys = systemsData.find(s => s.id === sysId);
  const boxSelect = document.getElementById('box-select');
  boxSelect.innerHTML = (sys?.boxes || []).map(b =>
    `<option value="${b.id}">${b.name}</option>`
  ).join('');
  onBoxChange();
}

function onBoxChange() {
  const sysId = document.getElementById('system-select').value;
  const boxId = document.getElementById('box-select').value;
  const sys = systemsData.find(s => s.id === sysId);
  const box = sys?.boxes.find(b => b.id === boxId);
  const labels = box?.labels || [];

  const styleSelect = document.getElementById('style-select');
  styleSelect.innerHTML = labels.map(l =>
    `<option value="${l.style}">${l.style_name}</option>`
  ).join('');
  document.getElementById('style-field').style.display = labels.length > 1 ? '' : 'none';

  // Populate advanced settings dropdowns from first label's params
  const firstLabel = labels[0];
  if (firstLabel) populateAdvancedParams(firstLabel.params);
}

function populateAdvancedParams(params) {
  const fontSelect = document.getElementById('param-font');
  if (params.font?.options) {
    fontSelect.innerHTML = params.font.options.map(o =>
      `<option value="${o}"${o === params.font.value ? ' selected' : ''}>${o}</option>`
    ).join('');
  }

  const tsSelect = document.getElementById('param-text_style');
  if (params.text_style?.options) {
    tsSelect.innerHTML = params.text_style.options.map(o =>
      `<option value="${o}"${o === params.text_style.value ? ' selected' : ''}>${o}</option>`
    ).join('');
  }

  const boldEl = document.getElementById('param-bold');
  if (params.bold !== undefined) boldEl.checked = params.bold.value ?? params.bold.default ?? true;

  const italicEl = document.getElementById('param-italic');
  if (params.italic !== undefined) italicEl.checked = params.italic.value ?? params.italic.default ?? false;

  const fsEl = document.getElementById('param-font_size');
  if (params.font_size !== undefined) fsEl.value = params.font_size.value ?? params.font_size.default ?? 6;

  const sepEl = document.getElementById('param-column_separator');
  if (params.column_separator !== undefined) sepEl.value = params.column_separator.value ?? params.column_separator.default ?? '|';
}

// --- Grid state ---
let gridState = { rows: 1, cols: 1, cells: [['']] };

function renderGrid() {
  const grid = document.getElementById('label-grid');
  grid.style.gridTemplateColumns = `repeat(${gridState.cols}, 1fr)`;
  grid.innerHTML = '';
  for (let r = 0; r < gridState.rows; r++) {
    for (let c = 0; c < gridState.cols; c++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'grid-cell';
      input.dataset.r = r;
      input.dataset.c = c;
      input.value = gridState.cells[r]?.[c] ?? '';
      input.placeholder = gridState.rows === 1 && gridState.cols === 1 ? 'Label text' : `R${r+1} C${c+1}`;
      input.addEventListener('input', e => {
        if (!gridState.cells[r]) gridState.cells[r] = [];
        gridState.cells[r][c] = e.target.value;
      });
      grid.appendChild(input);
    }
  }
}

function addRow() {
  gridState.rows++;
  gridState.cells.push(Array(gridState.cols).fill(''));
  renderGrid();
}

function removeLastRow() {
  if (gridState.rows <= 1) return;
  gridState.rows--;
  gridState.cells.pop();
  renderGrid();
}

function addCol() {
  gridState.cols++;
  for (const row of gridState.cells) row.push('');
  renderGrid();
}

function removeLastCol() {
  if (gridState.cols <= 1) return;
  gridState.cols--;
  for (const row of gridState.cells) row.pop();
  renderGrid();
}

function getTextValue() {
  // Column-major: col0row0\ncol0row1|col1row0\ncol1row1
  const cols = [];
  for (let c = 0; c < gridState.cols; c++) {
    const colRows = [];
    for (let r = 0; r < gridState.rows; r++) {
      colRows.push(gridState.cells[r]?.[c] ?? '');
    }
    cols.push(colRows.join('\n'));
  }
  return cols.join('|');
}

function loadIntoGrid(text) {
  const sep = document.getElementById('param-column_separator').value || '|';
  const colStrings = text.includes(sep) ? text.split(sep) : [text];
  const cols = colStrings.map(c => c.split('\n'));
  const numCols = cols.length;
  const numRows = Math.max(...cols.map(c => c.length));
  gridState = {
    rows: numRows,
    cols: numCols,
    cells: Array.from({ length: numRows }, (_, r) =>
      Array.from({ length: numCols }, (_, c) => cols[c]?.[r] ?? '')
    ),
  };
  renderGrid();
}

// --- Label list (snapshots) ---
let labelList = [];

function currentSnapshot() {
  const sysId = document.getElementById('system-select').value;
  const boxId = document.getElementById('box-select').value;
  const styleId = document.getElementById('style-select').value;
  const baseColor = document.getElementById('base-color').value;
  const textColor = document.getElementById('text-color').value;
  localStorage.setItem(`colors_${sysId}`, JSON.stringify({ base_color: baseColor, text_color: textColor }));
  return {
    system_id: sysId,
    box_id: boxId,
    style_id: styleId,
    text: getTextValue(),
    font: document.getElementById('param-font').value,
    bold: document.getElementById('param-bold').checked,
    italic: document.getElementById('param-italic').checked,
    font_size: parseFloat(document.getElementById('param-font_size').value),
    text_style: document.getElementById('param-text_style').value,
    base_color: baseColor,
    text_color: textColor,
    column_separator: document.getElementById('param-column_separator').value || '|',
  };
}

function applySnapshot(snap) {
  // Restore system/box selectors
  document.getElementById('system-select').value = snap.system_id;
  onSystemChange();
  document.getElementById('box-select').value = snap.box_id;
  onBoxChange();
  document.getElementById('style-select').value = snap.style_id;

  // Restore colors
  document.getElementById('base-color').value = snap.base_color;
  document.getElementById('text-color').value = snap.text_color;

  // Restore advanced settings
  document.getElementById('param-font').value = snap.font;
  document.getElementById('param-bold').checked = snap.bold;
  document.getElementById('param-italic').checked = snap.italic;
  document.getElementById('param-font_size').value = snap.font_size;
  document.getElementById('param-text_style').value = snap.text_style;
  document.getElementById('param-column_separator').value = snap.column_separator;

  loadIntoGrid(snap.text);
}

function updateListCount() {
  document.getElementById('list-count').textContent = labelList.length;
}

function renderListEntries() {
  const container = document.getElementById('list-entries');
  if (labelList.length === 0) {
    container.innerHTML = '<p style="color:#888;font-size:0.85rem;padding:8px 0">No labels saved yet.</p>';
    return;
  }
  container.innerHTML = '';
  labelList.forEach((snap, idx) => {
    const displayText = snap.text.replace(/\n/g, ' / ');
    const entry = document.createElement('div');
    entry.className = 'list-entry';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'list-entry-text';
    input.value = displayText;
    input.addEventListener('change', e => {
      // Decode display format back to encoded: ' / ' → '\n'
      labelList[idx].text = e.target.value.replace(/ \/ /g, '\n');
    });

    const editBtn = document.createElement('button');
    editBtn.className = 'btn-secondary btn-small';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => {
      applySnapshot(labelList[idx]);
      closeListModal();
    });

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-secondary btn-small btn-danger';
    removeBtn.textContent = '✕';
    removeBtn.addEventListener('click', () => {
      labelList.splice(idx, 1);
      updateListCount();
      renderListEntries();
    });

    entry.appendChild(input);
    entry.appendChild(editBtn);
    entry.appendChild(removeBtn);
    container.appendChild(entry);
  });
}

function saveToList() {
  labelList.push(currentSnapshot());
  updateListCount();
}

// --- Generate / download ---
async function generate() {
  const btn = document.getElementById('generate-btn');
  const status = document.getElementById('status');

  btn.disabled = true;
  btn.textContent = 'Generating…';
  status.textContent = '';
  status.className = '';

  try {
    const snap = currentSnapshot();
    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(snap),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    loadSTLs(data.base_stl_url, data.text_stl_url ?? null, snap.base_color, snap.text_color);

    if (data.warnings?.length) {
      status.className = 'warning';
      status.textContent = '⚠ ' + data.warnings.join(' · ');
    } else {
      status.textContent = 'Done.';
    }
  } catch (e) {
    status.className = '';
    status.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate label';
  }
}

async function _runBatch(btn, download) {
  const status = document.getElementById('status');

  if (labelList.length === 0) {
    status.textContent = 'Label list is empty.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Generating…';
  status.textContent = '';
  status.className = '';

  try {
    const res = await fetch('/generate-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(labelList),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    if (download) {
      const a = document.createElement('a');
      a.href = data['3mf_url'];
      a.download = '';
      a.click();
    }
    loadSTLs(data.base_stl_url, data.text_stl_url ?? null, labelList[0].base_color, labelList[0].text_color);

    if (data.warnings?.length) {
      status.className = 'warning';
      status.textContent = '⚠ ' + data.warnings.join(' · ');
    } else {
      const n = labelList.length;
      status.textContent = download
        ? `Downloaded ${n} label${n > 1 ? 's' : ''}.`
        : `Preview: ${n} label${n > 1 ? 's' : ''}.`;
    }
  } catch (e) {
    status.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = download ? 'Download list' : 'Generate list';
  }
}

async function downloadBatch() {
  await _runBatch(document.getElementById('download-batch-btn'), true);
}

async function generateList() {
  await _runBatch(document.getElementById('generate-list-btn'), false);
}

async function downloadList() {
  await _runBatch(document.getElementById('download-list-btn'), true);
}

// --- Color helpers ---
function hexLuminance(hex) {
  const lin = c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  const r = lin(parseInt(hex.slice(1, 3), 16) / 255);
  const g = lin(parseInt(hex.slice(3, 5), 16) / 255);
  const b = lin(parseInt(hex.slice(5, 7), 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function autoTextColor() {
  const base = document.getElementById('base-color').value;
  document.getElementById('text-color').value = hexLuminance(base) > 0.179 ? '#000000' : '#ffffff';
}

// --- Modal helpers ---
function openAdvancedModal() { document.getElementById('advanced-modal').style.display = 'flex'; }
function closeAdvancedModal() { document.getElementById('advanced-modal').style.display = 'none'; }
function openListModal() { renderListEntries(); document.getElementById('list-modal').style.display = 'flex'; }
function closeListModal() { document.getElementById('list-modal').style.display = 'none'; }
function openToolsModal() { document.getElementById('tools-modal').style.display = 'flex'; }
function closeToolsModal() { document.getElementById('tools-modal').style.display = 'none'; }

// --- Font sampler ---
async function generateFontSampler() {
  const btn = document.getElementById('font-sampler-btn');
  const status = document.getElementById('status');

  btn.disabled = true;
  btn.textContent = 'Generating…';

  try {
    const snap = currentSnapshot();
    const res = await fetch('/generate-font-sampler', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(snap),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    const a = document.createElement('a');
    a.href = data['3mf_url'];
    a.download = '';
    a.click();
    loadSTLs(data.base_stl_url, data.text_stl_url ?? null, snap.base_color, snap.text_color);
    closeToolsModal();
    status.textContent = 'Font sampler downloaded.';
  } catch (e) {
    status.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate font sampler';
  }
}

// --- Event wiring ---
document.getElementById('system-select').addEventListener('change', onSystemChange);
document.getElementById('box-select').addEventListener('change', onBoxChange);
document.getElementById('add-row-btn').addEventListener('click', addRow);
document.getElementById('add-col-btn').addEventListener('click', addCol);
document.getElementById('remove-row-btn').addEventListener('click', removeLastRow);
document.getElementById('remove-col-btn').addEventListener('click', removeLastCol);
document.getElementById('generate-btn').addEventListener('click', generate);
document.getElementById('save-btn').addEventListener('click', saveToList);
document.getElementById('generate-list-btn').addEventListener('click', generateList);
document.getElementById('download-list-btn').addEventListener('click', downloadList);
document.getElementById('auto-color-btn').addEventListener('click', autoTextColor);

document.getElementById('advanced-open-btn').addEventListener('click', openAdvancedModal);
document.getElementById('advanced-close-btn').addEventListener('click', closeAdvancedModal);
document.getElementById('advanced-backdrop').addEventListener('click', closeAdvancedModal);

document.getElementById('list-open-btn').addEventListener('click', openListModal);
document.getElementById('list-close-btn').addEventListener('click', closeListModal);
document.getElementById('list-backdrop').addEventListener('click', closeListModal);
document.getElementById('list-clear-btn').addEventListener('click', () => {
  labelList = [];
  updateListCount();
  renderListEntries();
});
document.getElementById('download-batch-btn').addEventListener('click', downloadBatch);

document.getElementById('tools-open-btn').addEventListener('click', openToolsModal);
document.getElementById('tools-close-btn').addEventListener('click', closeToolsModal);
document.getElementById('tools-backdrop').addEventListener('click', closeToolsModal);
document.getElementById('font-sampler-btn').addEventListener('click', generateFontSampler);

// --- Init ---
renderGrid();
loadSystems();
