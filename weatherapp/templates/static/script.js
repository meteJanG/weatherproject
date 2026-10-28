console.log("Script başarıyla yüklendi.");

// Elementlerin Tanımlanması
const openBtn = document.getElementById('openPopupBtn');
const closeBtn = document.getElementById('closePopupBtn');
const popup = document.getElementById('outfitPopup');

const helpBtn = document.getElementById('helpBtn');
const helpPopup = document.getElementById('helpPopup');
const closeHelpPopupBtn = document.getElementById('closeHelpPopupBtn');
const dontShowCheckbox = document.getElementById('dontShowCheckbox');

const uploadContainer = document.getElementById('uploadContainer');
const outfitInput = document.getElementById('outfitInput');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const previewContainer = document.getElementById('previewContainer');
const outfitPreview = document.getElementById('outfitPreview');
const retakeBtn = document.getElementById('retakeBtn');
const analyzeBtn = document.getElementById('analyzeBtn');

// --- 1. Soru İşareti "Bir Daha Gösterme" Mantığı ---
if (localStorage.getItem('hideHelpBtn') === 'true') {
    if (helpBtn) helpBtn.style.display = 'none';
}

if (helpBtn && helpPopup) {
    helpBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        helpPopup.classList.add('active');
    });
}

if (closeHelpPopupBtn && helpPopup) {
    closeHelpPopupBtn.addEventListener('click', () => {
        helpPopup.classList.remove('active');
    });
}

if (helpPopup) {
    helpPopup.addEventListener('click', (e) => {
        if (e.target === helpPopup) {
            helpPopup.classList.remove('active');
        }
    });
}

if (dontShowCheckbox) {
    dontShowCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            localStorage.setItem('hideHelpBtn', 'true');
            if (helpBtn) helpBtn.style.display = 'none';
            if (helpPopup) helpPopup.classList.remove('active');
        }
    });
}

// --- 2. Kıyafet Pop-up Açma / Kapama ---
if (openBtn && popup) {
    openBtn.addEventListener('click', () => {
        popup.classList.add('active');
    });
}

if (closeBtn && popup) {
    closeBtn.addEventListener('click', () => {
        popup.classList.remove('active');
    });
}

if (popup) {
    popup.addEventListener('click', (e) => {
        if (e.target === popup) {
            popup.classList.remove('active');
        }
    });
}

// --- 3. Kamera / Fotoğraf Yükleme İşlemleri ---
if (uploadContainer && outfitInput) {
    uploadContainer.addEventListener('click', () => {
        outfitInput.click();
    });
}

if (outfitInput) {
    outfitInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                if (outfitPreview) outfitPreview.src = event.target.result;
                if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';
                if (previewContainer) previewContainer.style.display = 'flex';
                if (analyzeBtn) analyzeBtn.removeAttribute('disabled');
            }
            reader.readAsDataURL(file);
        }
    });
}

if (retakeBtn) {
    retakeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (outfitInput) outfitInput.value = '';
        if (outfitPreview) outfitPreview.src = '';
        if (previewContainer) previewContainer.style.display = 'none';
        if (uploadPlaceholder) uploadPlaceholder.style.display = 'block';
        if (analyzeBtn) analyzeBtn.setAttribute('disabled', 'true');
    });
}