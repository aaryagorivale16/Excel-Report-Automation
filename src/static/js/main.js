/**
 * EduMetrics - Client-Side Interactive Engine
 * Handles Drag & Drop, Pre-flight CSV Validation, Real-Time Filtering, and Charting
 * Zero emojis - Pure Typography & SVG iconography
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Setup Drag and Drop File Handlers with Pre-flight CSV Validation
  setupDropzone('attendance_dropzone', 'attendance_file', 'att_preview', ['StudentID', 'Name', 'Date', 'Status']);
  setupDropzone('marks_dropzone', 'marks_file', 'marks_preview', ['StudentID', 'Name', 'Subject', 'Marks', 'MaxMarks']);

  // 2. Setup Student Roster Table Search & Filtering
  setupTableFiltering();

  // 3. Setup Settings Sliders & Grade Boundary Sync
  setupSettingsSync();
});

/**
 * Configure drag-and-drop dropzones and parse CSV headers instantly
 */
function setupDropzone(dropzoneId, inputId, previewId, requiredHeaders) {
  const dropzone = document.getElementById(dropzoneId);
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);

  if (!dropzone || !input || !preview) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-active');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-active');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      input.files = files;
      validateAndPreviewCSV(files[0], preview, requiredHeaders);
    }
  });

  input.addEventListener('change', () => {
    if (input.files.length > 0) {
      validateAndPreviewCSV(input.files[0], preview, requiredHeaders);
    }
  });
}

/**
 * Inspects CSV headers and gives instantaneous feedback to the user without any emojis
 */
function validateAndPreviewCSV(file, previewEl, requiredHeaders) {
  previewEl.style.display = 'block';
  previewEl.innerHTML = `<span style="color: var(--color-text-muted);">Reading ${escapeHTML(file.name)}...</span>`;

  const reader = new FileReader();
  reader.onload = (e) => {
    const text = e.target.result;
    const lines = text.split(/\r\n|\n/).filter(line => line.trim().length > 0);
    
    if (lines.length === 0) {
      previewEl.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span class="chic-badge badge-alert">File is empty</span>
        </div>
      `;
      return;
    }

    // Split headers
    const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));
    const missing = requiredHeaders.filter(req => !headers.some(h => h.toLowerCase() === req.toLowerCase()));

    const fileSizeKB = (file.size / 1024).toFixed(1);
    const dataRows = lines.length - 1;

    let statusBadge = missing.length === 0
      ? `<span class="chic-badge badge-pass">Valid Schema</span>`
      : `<span class="chic-badge badge-alert">Missing: ${escapeHTML(missing.join(', '))}</span>`;

    let pillsHtml = requiredHeaders.map(req => {
      const exists = headers.some(h => h.toLowerCase() === req.toLowerCase());
      return `<span class="chic-badge ${exists ? 'badge-sage' : 'badge-alert'}" style="font-size: 0.72rem; margin-right: 0.35rem;">
        ${req}
      </span>`;
    }).join(' ');

    previewEl.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 0.65rem; width: 100%;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <strong style="color: var(--color-text-dark);">${escapeHTML(file.name)}</strong>
            <span style="color: var(--color-text-muted); font-size: 0.75rem; margin-left: 0.5rem;">(${fileSizeKB} KB • ~${dataRows} rows)</span>
          </div>
          ${statusBadge}
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.25rem;">
          ${pillsHtml}
        </div>
      </div>
    `;
  };

  reader.onerror = () => {
    previewEl.innerHTML = `<span class="chic-badge badge-alert">Could not read file</span>`;
  };

  // Read first 20KB for fast preview
  const blob = file.slice(0, 20480);
  reader.readAsText(blob);
}

/**
 * Filter Student Roster Table
 */
function setupTableFiltering() {
  const searchInput = document.getElementById('rosterSearch');
  const table = document.getElementById('studentRosterTable');
  const filterPills = document.querySelectorAll('.roster-filter-btn');

  if (!searchInput || !table) return;

  let activeFilter = 'all';

  function applyFilters() {
    const query = searchInput.value.toLowerCase().trim();
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
      const text = row.innerText.toLowerCase();
      const status = row.getAttribute('data-status') || '';
      const attendanceFlag = row.getAttribute('data-low-attendance') === 'true';
      const isTopper = row.getAttribute('data-topper') === 'true';

      const matchesSearch = query === '' || text.includes(query);
      let matchesCategory = true;

      if (activeFilter === 'pass') {
        matchesCategory = (status.toLowerCase() === 'pass');
      } else if (activeFilter === 'fail') {
        matchesCategory = (status.toLowerCase() === 'fail');
      } else if (activeFilter === 'low_att') {
        matchesCategory = attendanceFlag;
      } else if (activeFilter === 'topper') {
        matchesCategory = isTopper;
      }

      row.style.display = (matchesSearch && matchesCategory) ? '' : 'none';
    });
  }

  searchInput.addEventListener('input', applyFilters);

  if (filterPills) {
    filterPills.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        filterPills.forEach(b => {
          b.classList.remove('active');
          b.classList.remove('pill-btn-olive');
          b.classList.add('pill-btn-outline');
        });
        btn.classList.add('active');
        btn.classList.remove('pill-btn-outline');
        btn.classList.add('pill-btn-olive');
        activeFilter = btn.getAttribute('data-filter') || 'all';
        applyFilters();
      });
    });
  }
}

/**
 * Dynamic settings sliders synchronization
 */
function setupSettingsSync() {
  const attSlider = document.getElementById('setting_att_threshold');
  const attDisplay = document.getElementById('display_att_threshold');
  const passSlider = document.getElementById('setting_pass_percentage');
  const passDisplay = document.getElementById('display_pass_percentage');

  if (attSlider && attDisplay) {
    attSlider.addEventListener('input', () => {
      attDisplay.innerText = attSlider.value + '%';
      updateRuleSummary();
    });
  }

  if (passSlider && passDisplay) {
    passSlider.addEventListener('input', () => {
      passDisplay.innerText = passSlider.value + '%';
      updateRuleSummary();
    });
  }

  function updateRuleSummary() {
    const summaryAtt = document.getElementById('rule_summary_att');
    const summaryPass = document.getElementById('rule_summary_pass');
    if (summaryAtt && attSlider) summaryAtt.innerText = attSlider.value + '%';
    if (summaryPass && passSlider) summaryPass.innerText = passSlider.value + '%';
  }
}

function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
