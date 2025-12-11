// script.js //

$(document).ready(function() {
    function removeOverlay() {
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
        $('body').css({
            'overflow': 'auto',
            'padding-right': '0',
            'position': 'relative'
        });
        $('.modal.show').modal('hide');
    }
    removeOverlay();
    setInterval(removeOverlay, 1000);
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // ===== CONFIRMACIÓN PARA ELIMINAR =====
    $('.btn-eliminar, .btn-danger[href*="delete"]').on('click', function(e) {
        if (!confirm('¿Estás seguro de que quieres eliminar este registro?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // ===== AUTO-CERRAR ALERTS =====
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // ===== BÚSQUEDA EN TIEMPO REAL =====
    $('.search-input').on('keyup', function() {
        const searchText = $(this).val().toLowerCase();
        const tableId = $(this).data('table');
        
        if (tableId) {
            $(`#${tableId} tbody tr`).each(function() {
                const rowText = $(this).text().toLowerCase();
                $(this).toggle(rowText.includes(searchText));
            });
        }
    });
    
    // ===== CALCULAR TOTALES AUTOMÁTICOS =====
    $('.calculate-total').on('input', function() {
        const precio = parseFloat($('#id_precio').val()) || 0;
        const cantidad = parseInt($('#id_cantidad').val()) || 0;
        const total = precio * cantidad;
        
        if ($('#totalVenta').length) {
            $('#totalVenta').val(total.toFixed(2));
        }
    });
    
    // ===== TOGGLE DE FILTROS =====
    $('.filter-toggle').on('click', function() {
        const target = $(this).data('target');
        $(target).toggleClass('d-none');
    });
    
    // ===== EXPORTAR A EXCEL =====
    $('.export-excel').on('click', function() {
        const tableId = $(this).data('table');
        exportTableToExcel(tableId);
    });
    
    // ===== MANEJO DE PESTAÑAS CON LOCALSTORAGE =====
    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
        const tabId = $(e.target).attr('href');
        localStorage.setItem('activeTab', tabId);
    });
    
    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        $(`a[href="${activeTab}"]`).tab('show');
    }
    
    // ===== FORM VALIDATION =====
    $('.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // ===== AUTO-REFRESH TOGGLE =====
    $('#autoRefreshToggle').on('change', function() {
        if ($(this).is(':checked')) {
            autoRefreshInterval = setInterval(function() {
                location.reload();
            }, 30000);
            showToast('info', 'Actualización automática activada', 'La página se actualizará cada 30 segundos');
        } else {
            clearInterval(autoRefreshInterval);
            showToast('info', 'Actualización automática', 'Desactivada');
        }
    });
});

// ===== FUNCIONES GLOBALES =====
function exportTableToExcel(tableId, filename = '') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = [];
        
        cells.forEach(cell => {
            if (!cell.classList.contains('acciones-col')) {
                rowData.push(`"${cell.textContent.trim().replace(/"/g, '""')}"`);
            }
        });
        
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = filename || `${tableId}_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function showToast(type, title, message) {
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    let toastContainer = $('.toast-container');
    if (!toastContainer.length) {
        $('body').append('<div class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
        toastContainer = $('.toast-container');
    }
    
    toastContainer.append(toastHtml);
    const toastElement = $(`#${toastId}`);
    const toast = new bootstrap.Toast(toastElement[0], { delay: 3000 });
    toast.show();
    
    toastElement.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// Función para formatear números como moneda
function formatCurrency(value) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-AR');
}

// Inicializar cuando se carga la página
window.addEventListener('load', function() {
    setTimeout(removeOverlay, 100);
});