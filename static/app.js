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

function loadSTLs(baseUrl, textUrl, baseColor, textColor) {
  if (meshBase) { scene.remove(meshBase); meshBase = null; }
  if (meshText) { scene.remove(meshText); meshText = null; }

  matBase.color.set(baseColor);
  matText.color.set(textColor);

  loader.load(baseUrl, geo => {
    geo.computeBoundingBox();
    const center = new THREE.Vector3();
    geo.boundingBox.getCenter(center);
    geo.translate(-center.x, -center.y, -center.z);
    meshBase = new THREE.Mesh(geo, matBase);
    scene.add(meshBase);

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
let boxParams = {};
const BOX_PARAM_KEYS = new Set(['width', 'height', 'depth', 'side_margin']);

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
  onStyleChange();
}

function onStyleChange() {
  const sysId = document.getElementById('system-select').value;
  const boxId = document.getElementById('box-select').value;
  const styleId = document.getElementById('style-select').value;
  const sys = systemsData.find(s => s.id === sysId);
  const box = sys?.boxes.find(b => b.id === boxId);
  const label = box?.labels.find(l => l.style === styleId);
  renderParams(label?.params || {});
}

function renderParams(params) {
  boxParams = {};
  for (const [key, p] of Object.entries(params)) {
    if (BOX_PARAM_KEYS.has(key)) boxParams[key] = p.value ?? p.default;
  }

  const grid = document.getElementById('params-grid');
  grid.innerHTML = Object.entries(params)
    .filter(([key]) => !BOX_PARAM_KEYS.has(key) && key !== 'column_separator')
    .map(([key, p]) => {
      const unitLabel = p.unit ? ` (${p.unit})` : '';
      const fullWidth = p.type === 'str' ? ' style="grid-column: 1 / -1"' : '';
      let input;
      if (p.type === 'str' && p.options?.length) {
        const opts = p.options.map(o => `<option value="${o}"${o === p.value ? ' selected' : ''}>${o}</option>`).join('');
        input = `<select id="param-${key}">${opts}</select>`;
      } else if (p.type === 'str') {
        input = `<input type="text" id="param-${key}" value="${p.value}" />`;
      } else {
        input = `<input type="number" id="param-${key}" value="${p.value}" step="any" />`;
      }
      return `<div class="field"${fullWidth}><label>${p.label}${unitLabel}</label>${input}</div>`;
    }).join('');
}

function getParams() {
  const grid = document.getElementById('params-grid');
  const result = {};
  for (const el of grid.querySelectorAll('input, select')) {
    const key = el.id.replace('param-', '');
    result[key] = el.type === 'number' ? parseFloat(el.value) : el.value;
  }
  return result;
}

async function generate() {
  const btn = document.getElementById('generate-btn');
  const status = document.getElementById('status');
  const dlBtn = document.getElementById('download-btn');

  btn.disabled = true;
  btn.textContent = 'Generating…';
  dlBtn.classList.remove('has-warning');
  dlBtn.textContent = 'Download 3MF';
  status.textContent = '';
  status.className = '';
  dlBtn.style.display = 'none';

  try {
    const styleId = document.getElementById('style-select').value;
    const sysId = document.getElementById('system-select').value;
    const baseColor = document.getElementById('base-color').value;
    const textColor = document.getElementById('text-color').value;
    const separator = document.getElementById('multicolumn-toggle').checked
      ? document.getElementById('column-separator').value
      : '';

    localStorage.setItem(`colors_${sysId}`, JSON.stringify({base_color: baseColor, text_color: textColor}));

    const body = {
      text: document.getElementById('text').value,
      style: styleId,
      params: { ...boxParams, ...getParams(), column_separator: separator },
      base_color: baseColor,
      text_color: textColor,
    };

    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    loadSTLs(data.base_stl_url, data.text_stl_url, data.base_color, data.text_color);
    dlBtn.href = data['3mf_url'];
    dlBtn.style.display = 'block';
    if (data.warnings?.length) {
      status.className = 'warning';
      status.textContent = '⚠ ' + data.warnings.join(' · ');
      dlBtn.classList.add('has-warning');
      dlBtn.textContent = '⚠ Download 3MF';
    } else {
      status.className = '';
      status.textContent = 'Done.';
    }
  } catch (e) {
    status.className = '';
    status.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate';
  }
}

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

function onMulticolumnToggle() {
  const on = document.getElementById('multicolumn-toggle').checked;
  document.getElementById('separator-field').style.display = on ? '' : 'none';
}

// --- Batch modal ---

function openBatchModal() {
  document.getElementById('batch-modal').style.display = 'flex';
  if (document.getElementById('batch-list').children.length === 0) {
    addBatchEntry('');
  }
}

function closeBatchModal() {
  document.getElementById('batch-modal').style.display = 'none';
}

function addBatchEntry(text = '') {
  const list = document.getElementById('batch-list');
  const entry = document.createElement('div');
  entry.className = 'batch-entry';
  const ta = document.createElement('textarea');
  ta.className = 'batch-text';
  ta.rows = 2;
  ta.value = text;
  const removeBtn = document.createElement('button');
  removeBtn.className = 'batch-remove-btn';
  removeBtn.title = 'Remove';
  removeBtn.textContent = '✕';
  removeBtn.addEventListener('click', () => entry.remove());
  entry.appendChild(ta);
  entry.appendChild(removeBtn);
  list.appendChild(entry);
  ta.focus();
}

function addCurrentToBatch() {
  addBatchEntry(document.getElementById('text').value);
  openBatchModal();
}

async function generateBatch() {
  const texts = [...document.querySelectorAll('.batch-text')]
    .map(el => el.value)
    .filter(t => t.trim());
  if (texts.length === 0) return;

  const btn = document.getElementById('batch-generate-btn');
  const status = document.getElementById('batch-status');
  const dlBtn = document.getElementById('batch-download-btn');

  btn.disabled = true;
  btn.textContent = `Generating ${texts.length} label${texts.length > 1 ? 's' : ''}…`;
  dlBtn.style.display = 'none';
  status.textContent = '';

  try {
    const body = {
      texts,
      style: document.getElementById('style-select').value,
      params: {
        ...boxParams,
        ...getParams(),
        column_separator: document.getElementById('multicolumn-toggle').checked
          ? document.getElementById('column-separator').value
          : '',
      },
      base_color: document.getElementById('base-color').value,
      text_color: document.getElementById('text-color').value,
    };

    const res = await fetch('/generate-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    dlBtn.href = data['3mf_url'];
    dlBtn.style.display = 'block';
    status.textContent = `Done — ${texts.length} label${texts.length > 1 ? 's' : ''}.`;
  } catch (e) {
    status.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate batch 3MF';
  }
}

document.getElementById('system-select').addEventListener('change', onSystemChange);
document.getElementById('box-select').addEventListener('change', onBoxChange);
document.getElementById('style-select').addEventListener('change', onStyleChange);
document.getElementById('auto-color-btn').addEventListener('click', autoTextColor);
document.getElementById('multicolumn-toggle').addEventListener('change', onMulticolumnToggle);
document.getElementById('generate-btn').addEventListener('click', generate);
document.getElementById('batch-open-btn').addEventListener('click', openBatchModal);
document.getElementById('add-to-batch-btn').addEventListener('click', addCurrentToBatch);
document.getElementById('batch-close-btn').addEventListener('click', closeBatchModal);
document.getElementById('batch-backdrop').addEventListener('click', closeBatchModal);
document.getElementById('batch-add-btn').addEventListener('click', () => addBatchEntry(''));
document.getElementById('batch-clear-btn').addEventListener('click', () => {
  document.getElementById('batch-list').innerHTML = '';
  document.getElementById('batch-download-btn').style.display = 'none';
  document.getElementById('batch-status').textContent = '';
});
document.getElementById('batch-generate-btn').addEventListener('click', generateBatch);

loadSystems();
