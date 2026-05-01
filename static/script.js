// --- DOM Elements ---
const uploadSection = document.getElementById('uploadSection');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

const stagedPreview = document.getElementById('stagedPreview');
const stagedImage = document.getElementById('stagedImage');
const processBtn = document.getElementById('processBtn');
const cancelUploadBtn = document.getElementById('cancelUploadBtn');

const resultPreview = document.getElementById('resultPreview');
const resultImage = document.getElementById('resultImage');
const emptyState = document.getElementById('emptyState');

const loadingOverlay = document.getElementById('loadingOverlay');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');
const toastContainer = document.getElementById('toastContainer');

// --- Modal & Zoom Elements ---
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const modalClose = document.getElementById('modalClose');
const modalImageContainer = document.getElementById('modalImageContainer');

const zoomInBtn = document.getElementById('zoomInBtn');
const zoomOutBtn = document.getElementById('zoomOutBtn');
const zoomResetBtn = document.getElementById('zoomResetBtn');

let currentResultFilename = null;
let currentFileToProcess = null;

// --- Zoom & Pan State Variables ---
let currentScale = 1;
let currentTranslateX = 0;
let currentTranslateY = 0;
let isDragging = false;
let startDragX = 0;
let startDragY = 0;

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 5;
const ZOOM_STEP = 0.2;

// --- Upload Area Events ---
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// --- Phase 1: Stage the File ---
function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('File size must be less than 10MB', 'error');
        return;
    }

    currentFileToProcess = file;
    const objectUrl = URL.createObjectURL(file);
    stagedImage.src = objectUrl;

    uploadSection.classList.add('hidden');
    stagedPreview.classList.remove('hidden');
    
    resultPreview.classList.add('hidden');
    emptyState.classList.remove('hidden');
}

// --- Phase 2: Process the File ---
processBtn.addEventListener('click', async () => {
    if (!currentFileToProcess) return;

    showLoading(true);

    try {
        const formData = new FormData();
        formData.append('file', currentFileToProcess);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!data.success) {
            showToast(data.error || 'Upload failed', 'error');
            showLoading(false);
            return;
        }

        updatePreview(data);
        showToast('Document enhanced successfully!', 'success');

    } catch (error) {
        console.error('Error:', error);
        showToast('An error occurred during processing', 'error');
    } finally {
        showLoading(false);
    }
});

// --- Phase 1B: Cancel Staging ---
cancelUploadBtn.addEventListener('click', () => {
    currentFileToProcess = null;
    stagedImage.src = '';
    
    uploadSection.classList.remove('hidden');
    stagedPreview.classList.add('hidden');
    fileInput.value = ''; 
});

// --- Result Actions ---
downloadBtn.addEventListener('click', () => {
    if (currentResultFilename) {
        const link = document.createElement('a');
        link.href = `/api/download/${encodeURIComponent(currentResultFilename)}`;
        link.download = currentResultFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

resetBtn.addEventListener('click', () => {
    resetUI();
});

function updatePreview(data) {
    resultImage.src = data.result;
    resultPreview.classList.remove('hidden');
    emptyState.classList.add('hidden');
    currentResultFilename = data.resultFilename;

    setTimeout(() => {
        resultPreview.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function resetUI() {
    uploadSection.classList.remove('hidden');
    stagedPreview.classList.add('hidden');
    stagedImage.src = '';
    currentFileToProcess = null;
    fileInput.value = '';

    resultPreview.classList.add('hidden');
    emptyState.classList.remove('hidden');
    currentResultFilename = null;
}

// ============================================================================
// 🌟 ADVANCED FULLSCREEN MODAL (ZOOM & PAN LOGIC) 🌟
// ============================================================================

function updateImageTransform() {
    modalImage.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px) scale(${currentScale})`;
}

function resetZoomAndPan() {
    currentScale = 1;
    currentTranslateX = 0;
    currentTranslateY = 0;
    modalImage.style.transition = 'transform 0.25s ease-out'; // Smooth reset
    updateImageTransform();
}

function openModal(imageSrc) {
    if (!imageSrc) return;
    modalImage.src = imageSrc;
    resetZoomAndPan();
    imageModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    imageModal.classList.remove('show');
    document.body.style.overflow = '';
    setTimeout(() => { modalImage.src = ''; }, 300);
}

// Trigger Modal Opens
stagedImage.addEventListener('click', () => openModal(stagedImage.src));
resultImage.addEventListener('click', () => openModal(resultImage.src));

// Close Modal Events
modalClose.addEventListener('click', closeModal);
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && imageModal.classList.contains('show')) closeModal();
});

// --- Mouse Wheel Zooming ---
modalImageContainer.addEventListener('wheel', (e) => {
    e.preventDefault(); // Prevent page scroll
    
    // Determine zoom direction
    const delta = e.deltaY * -0.001; 
    const newScale = Math.min(Math.max(MIN_ZOOM, currentScale + delta), MAX_ZOOM);
    
    currentScale = newScale;
    modalImage.style.transition = 'transform 0.1s ease-out'; // Snappy zoom
    updateImageTransform();
}, { passive: false });

// --- Manual Button Zooming ---
zoomInBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // Prevent closing modal
    currentScale = Math.min(MAX_ZOOM, currentScale + ZOOM_STEP);
    modalImage.style.transition = 'transform 0.2s ease-out';
    updateImageTransform();
});

zoomOutBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    currentScale = Math.max(MIN_ZOOM, currentScale - ZOOM_STEP);
    modalImage.style.transition = 'transform 0.2s ease-out';
    updateImageTransform();
});

zoomResetBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resetZoomAndPan();
});

// --- Mouse Drag Panning ---
modalImageContainer.addEventListener('mousedown', (e) => {
    // Only allow drag if we are zoomed in, or if user left clicks
    if (e.button !== 0) return; 
    e.preventDefault();

    isDragging = true;
    startDragX = e.clientX - currentTranslateX;
    startDragY = e.clientY - currentTranslateY;
    
    // Remove transition during drag for 1:1 movement
    modalImage.style.transition = 'none'; 
    modalImageContainer.style.cursor = 'grabbing';
});

window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    currentTranslateX = e.clientX - startDragX;
    currentTranslateY = e.clientY - startDragY;
    updateImageTransform();
});

window.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        modalImageContainer.style.cursor = 'grab';
    }
});

// Prevent closing modal when clicking directly on the image or controls
modalImage.addEventListener('click', (e) => e.stopPropagation());
document.querySelector('.modal-zoom-controls').addEventListener('click', (e) => e.stopPropagation());

// Close modal when clicking strictly on the background container
modalImageContainer.addEventListener('click', (e) => {
    if (e.target === modalImageContainer && !isDragging) {
        closeModal();
    }
});

// --- Utilities ---
function showLoading(show) {
    if (show) loadingOverlay.classList.remove('hidden');
    else loadingOverlay.classList.add('hidden');
}

function showToast(message, type = 'success', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<div class="toast-message">${escapeHtml(message)}</div><button class="toast-close">&times;</button>`;
    toastContainer.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, duration);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    emptyState.classList.remove('hidden');
    resultPreview.classList.add('hidden');
    stagedPreview.classList.add('hidden');
});