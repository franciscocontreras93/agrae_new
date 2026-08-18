const $ = (selector) => document.querySelector(selector);
const panels = [...document.querySelectorAll('.panel')];
const steps = [...document.querySelectorAll('.step')];
let current = 0;
let selectedFile = null;
let pollTimer = null;

function showStep(index) {
  current = Math.max(0, Math.min(index, panels.length - 1));
  panels.forEach((panel, i) => panel.classList.toggle('active', i === current));
  steps.forEach((step, i) => {
    step.classList.toggle('active', i === current);
    step.toggleAttribute('aria-current', i === current);
  });
  window.scrollTo({ top: Math.max(0, $('.workspace').offsetTop - 24), behavior: 'smooth' });
}

function humanSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function setFile(file) {
  if (!file || !file.name.toLowerCase().endsWith('.zip')) {
    alert('Selecciona una exportación CNH comprimida en ZIP.');
    return;
  }
  selectedFile = file;
  $('#file-name').textContent = file.name;
  $('#file-size').textContent = humanSize(file.size);
  $('#file-card').classList.remove('hidden');
  $('#dropzone').classList.add('hidden');
  $('#summary-file').textContent = file.name;
}

function validateStep(index) {
  if (index === 0 && !selectedFile) {
    $('#dropzone').classList.add('drag');
    setTimeout(() => $('#dropzone').classList.remove('drag'), 700);
    return false;
  }
  if (index === 1 && !$('#accept-hypotheses').checked) {
    $('.check-row').scrollIntoView({ behavior: 'smooth', block: 'center' });
    $('.check-row').animate?.([{ background: '#fbf4e4' }, { background: 'transparent' }], { duration: 700 });
    return false;
  }
  return true;
}

steps.forEach((step, i) => step.addEventListener('click', () => {
  if (i <= current || (i > current && validateStep(current))) showStep(i);
}));
document.querySelectorAll('.next').forEach(button => button.addEventListener('click', () => {
  if (validateStep(current)) showStep(current + 1);
}));
document.querySelectorAll('.back').forEach(button => button.addEventListener('click', () => showStep(current - 1)));

const input = $('#source-file');
const dropzone = $('#dropzone');
input.addEventListener('change', () => setFile(input.files[0]));
['dragenter', 'dragover'].forEach(name => dropzone.addEventListener(name, event => { event.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave', 'drop'].forEach(name => dropzone.addEventListener(name, event => { event.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', event => setFile(event.dataTransfer.files[0]));
$('#remove-file').addEventListener('click', () => {
  selectedFile = null; input.value = ''; $('#file-card').classList.add('hidden'); dropzone.classList.remove('hidden');
});
$('#crs').addEventListener('change', event => $('#summary-crs').textContent = event.target.value);

function setProgress(value, stage) {
  $('#progress-card').classList.remove('hidden');
  $('#progress-bar').style.width = `${value}%`;
  $('#progress-percent').textContent = `${value}%`;
  $('#progress-stage').textContent = stage;
}

async function pollJob(job) {
  try {
    const response = await fetch(`/api/jobs/${job.id}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo consultar el proceso.');
    setProgress(data.progress, data.stage);
    if (data.status === 'completed') {
      clearInterval(pollTimer); pollTimer = null;
      $('#progress-card').classList.add('hidden');
      $('#result-card').classList.remove('hidden');
      const summary = data.report.summary;
      $('#metric-points').textContent = summary.points.toLocaleString('es-ES');
      $('#metric-yields').textContent = summary.yield_12_count.toLocaleString('es-ES');
      $('#metric-plausible').textContent = `${summary.yield_12_plausible_pct}%`;
      $('#download-link').href = data.download_url;
    } else if (data.status === 'failed') {
      throw new Error(data.error || 'La conversión ha fallado.');
    }
  } catch (error) {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
    $('#error-message').textContent = error.message;
    $('#error-card').classList.remove('hidden');
    $('#export-button').disabled = false;
  }
}

$('#export-button').addEventListener('click', async () => {
  if (!selectedFile || !$('#accept-hypotheses').checked) { showStep(selectedFile ? 1 : 0); return; }
  $('#export-button').disabled = true;
  $('#result-card').classList.add('hidden');
  $('#error-card').classList.add('hidden');
  setProgress(1, 'Cargando archivo local');
  const form = new FormData();
  form.append('file', selectedFile);
  form.append('crs', $('#crs').value);
  form.append('accept_hypotheses', 'true');
  try {
    const response = await fetch('/api/jobs', { method: 'POST', body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo iniciar la conversión.');
    await pollJob(data);
    pollTimer = setInterval(() => pollJob(data), 1500);
  } catch (error) {
    $('#error-message').textContent = error.message;
    $('#error-card').classList.remove('hidden');
    $('#progress-card').classList.add('hidden');
    $('#export-button').disabled = false;
  }
});
