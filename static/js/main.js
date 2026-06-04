function dismissAlert(alertId) {
    const alertEl = document.getElementById(alertId);
    if (alertEl) {
        alertEl.style.opacity = '0';
        setTimeout(() => {
            alertEl.remove();
        }, 300);
    }
}

function confirmDelete(button, bookTitle) {
    const message = `Apakah Anda yakin ingin menghapus buku "${bookTitle}"?`;
    if (confirm(message)) {
        button.closest('form').submit();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach((alert) => {
        alert.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

function copyHash() {
    const hashElement = document.getElementById('digestHash');
    if (hashElement) {
        const hashText = hashElement.innerText;
        navigator.clipboard.writeText(hashText).then(() => {
            alert('Hash SHA-256 berhasil disalin!');
        });
    }
}
