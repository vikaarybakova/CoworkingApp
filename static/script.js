// =====================================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// =====================================================
let revenueChart = null;
let reportChart = null;

// =====================================================
// НАВИГАЦИЯ (с активным пунктом меню)
// =====================================================
document.querySelectorAll('.nav-menu a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const section = this.dataset.section;

        document.querySelectorAll('.nav-menu a').forEach(l => l.classList.remove('active'));
        this.classList.add('active');

        document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
        document.getElementById(section + '-section').classList.add('active');

        if (section === 'bookings') loadBookings();
        if (section === 'dashboard') loadDashboard();
        if (section === 'coworkings') loadCoworkings();
        if (section === 'promotions') loadPromotions();
    });
});

// =====================================================
// ДАШБОРД

function loadDashboard() {
    fetch('/api/coworkings')
        .then(r => r.json())
        .then(data => document.getElementById('total-coworkings').textContent = data.length)
        .catch(() => document.getElementById('total-coworkings').textContent = '0');

    fetch('/api/admin/bookings?status=confirmed')
        .then(r => r.json())
        .then(data => document.getElementById('active-bookings').textContent = data.length)
        .catch(() => document.getElementById('active-bookings').textContent = '0');

    fetch('/api/admin/reports/revenue?coworking_id=1&days=30')
        .then(r => r.json())
        .then(data => {
            document.getElementById('revenue-month').textContent = data.total_revenue.toFixed(2) + ' ₽';
        })
        .catch(() => document.getElementById('revenue-month').textContent = '0 ₽');

    fetch('/api/admin/reports/occupancy?coworking_id=1&days=1')
        .then(r => r.json())
        .then(data => {
            if (data.values && data.values.length > 0) {
                document.getElementById('occupancy-today').textContent = data.values[data.values.length - 1] + '%';
            } else {
                document.getElementById('occupancy-today').textContent = '0%';
            }
        })
        .catch(() => document.getElementById('occupancy-today').textContent = '0%');

    fetch('/api/admin/reports/revenue/daily?coworking_id=1&days=7')
        .then(r => r.json())
        .then(data => {
            const canvas = document.getElementById('revenueChart');
            if (!canvas) {
                console.error('Canvas revenueChart не найден');
                return;
            }
            const ctx = canvas.getContext('2d');
            if (revenueChart) revenueChart.destroy();
            revenueChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                    datasets: [{
                        label: 'Выручка (₽)',
                        data: data.values || [12000, 14500, 13200, 15800, 17100, 18900, 24000],
                        borderColor: '#009688',
                        backgroundColor: 'rgba(0,150,136,0.1)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { position: 'top' } }
                }
            });
        })
        .catch(err => console.error('Ошибка графика выручки:', err));
}

// =====================================================
// ОТЧЁТЫ (график загруженности)
// =====================================================
function loadReports() {
    const coworkingId = document.getElementById('report-coworking')?.value || 1;

    fetch(`/api/admin/reports/occupancy?coworking_id=${coworkingId}&days=7`)
        .then(r => r.json())
        .then(data => {
            const canvas = document.getElementById('reportChart');
            if (!canvas) {
                console.error('Canvas reportChart не найден');
                return;
            }
            const ctx = canvas.getContext('2d');
            if (reportChart) reportChart.destroy();
            reportChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                    datasets: [{
                        label: 'Загруженность (%)',
                        data: data.values || [35, 42, 38, 55, 48, 62, 45],
                        backgroundColor: '#009688',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { position: 'top' } }
                }
            });
        })
        .catch(err => console.error('Ошибка графика загруженности:', err));
}

// =====================================================
// БРОНИРОВАНИЯ
// =====================================================
function loadBookings() {
    const status = document.getElementById('booking-status-filter')?.value || '';
    let url = '/api/admin/bookings';
    if (status) url += '?status=' + status;

    fetch(url)
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('bookings-body');
            if (!data.length) {
                tbody.innerHTML = '<tr><td colspan="7">Нет бронирований</td></tr>';
                return;
            }
            let html = '';
            data.forEach(b => {
                let statusText = '', statusClass = '';
                switch(b.status) {
                    case 'pending': statusText = '⏳ Ожидает'; statusClass = 'status-pending'; break;
                    case 'confirmed': statusText = '✅ Подтверждено'; statusClass = 'status-confirmed'; break;
                    case 'completed': statusText = '✓ Завершено'; statusClass = 'status-completed'; break;
                    case 'cancelled': statusText = '❌ Отменено'; statusClass = 'status-cancelled'; break;
                    default: statusText = b.status; statusClass = '';
                }

                let actions = '';
                if (b.status === 'pending') {
                    actions += `<button class="btn btn-success" onclick="confirmBooking(${b.id})">✓ Подтвердить</button> `;
                }
                if (b.status !== 'cancelled' && b.status !== 'completed') {
                    actions += `<button class="btn btn-danger" onclick="cancelBooking(${b.id})">✕ Отменить</button>`;
                }
                if (b.status === 'completed') {
                    actions = '<span style="color:#6c757d;">✓ Завершено</span>';
                }

                html += `<tr>
                    <td>${b.id}</td>
                    <td>Коворкинг #${b.coworking_id}</td>
                    <td>${b.date}</td>
                    <td>${b.start_time} - ${b.end_time}</td>
                    <td><span class="${statusClass}">${statusText}</span></td>
                    <td>${b.total_price || 0} ₽</td>
                    <td>${actions}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        })
        .catch(() => {
            document.getElementById('bookings-body').innerHTML = '<tr><td colspan="7">Ошибка загрузки</td></tr>';
        });
}

function confirmBooking(id) {
    if (confirm('Подтвердить бронь #' + id + '?')) {
        fetch(`/api/admin/bookings/${id}/status?status=confirmed`, { method: 'PUT' })
            .then(() => { loadBookings(); loadDashboard(); });
    }
}

function cancelBooking(id) {
    if (confirm('Отменить бронь #' + id + '?')) {
        fetch(`/api/admin/bookings/${id}/status?status=cancelled`, { method: 'PUT' })
            .then(() => { loadBookings(); loadDashboard(); });
    }
}

// =====================================================
// КОВОРКИНГИ
// =====================================================
function loadCoworkings() {
    fetch('/api/coworkings')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('coworkings-body');
            if (!data.length) {
                tbody.innerHTML = '<tr><td colspan="5">Нет коворкингов</td></tr>';
                return;
            }
            let html = '';
            data.forEach(c => {
                html += `<tr>
                    <td>${c.id}</td>
                    <td>${c.name}</td>
                    <td>${c.address}</td>
                    <td>м. ${c.metro_station || '—'}</td>
                    <td>${c.min_price ? 'от ' + c.min_price + ' ₽/ч' : '—'}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        });
}

function showAddCoworkingForm() {
    document.getElementById('add-coworking-form').style.display = 'block';
}

function hideAddCoworkingForm() {
    document.getElementById('add-coworking-form').style.display = 'none';
}

function addCoworking() {
    var name = document.getElementById('new-name').value.trim();
    var address = document.getElementById('new-address').value.trim();
    if (!name || !address) {
        alert('Название и адрес обязательны для заполнения!');
        return;
    }

    var fd = new FormData();
    fd.append('name', name);
    fd.append('address', address);
    fd.append('metro_station', document.getElementById('new-metro').value);
    fd.append('phone', document.getElementById('new-phone').value);
    fd.append('working_hours', document.getElementById('new-hours').value);
    fd.append('description', document.getElementById('new-desc').value);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/admin/coworkings/add', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            alert('✓ Коворкинг успешно добавлен!');
            hideAddCoworkingForm();
            loadCoworkings();
            loadDashboard();
            // Очищаем форму
            document.getElementById('new-name').value = '';
            document.getElementById('new-address').value = '';
            document.getElementById('new-metro').value = '';
            document.getElementById('new-phone').value = '';
            document.getElementById('new-hours').value = '';
            document.getElementById('new-desc').value = '';
        } else {
            alert('Ошибка: ' + xhr.status + '\n' + xhr.responseText);
        }
    };
    xhr.onerror = function() {
        alert('Ошибка сети. Проверьте подключение к серверу.');
    };
    xhr.send(fd);
}

// =====================================================
// ПРОМОКОДЫ
// =====================================================
function loadPromotions() {
    fetch('/api/admin/promotions')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('promotions-body');
            if (!data.length) {
                tbody.innerHTML = '<tr><td colspan="5">Нет акций</td></tr>';
                return;
            }
            let html = '';
            data.forEach(p => {
                html += `<tr>
                    <td>${p.id}</td>
                    <td><b>${p.code}</b></td>
                    <td>${p.discount_percent}%</td>
                    <td>${p.valid_until || '—'}</td>
                    <td>${p.used_count || 0}/${p.max_uses || '∞'}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        });
}

function showAddPromoForm() {
    document.getElementById('add-promo-form').style.display = 'block';
}

function hideAddPromoForm() {
    document.getElementById('add-promo-form').style.display = 'none';
}

function addPromo() {
    const code = document.getElementById('promo-code').value;
    const discount = document.getElementById('promo-discount').value;
    if (!code || !discount) {
        alert('Заполните код и скидку!');
        return;
    }
    const fd = new FormData();
    fd.append('code', code);
    fd.append('discount_percent', discount);
    fd.append('valid_until', document.getElementById('promo-valid').value);

    fetch('/api/admin/promotions/add', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(() => {
            alert('Промокод создан!');
            hideAddPromoForm();
            loadPromotions();
        })
        .catch(() => alert('Ошибка'));
}

// =====================================================
// ЗАГРУЗКА ПРИ СТАРТЕ
// =====================================================
loadDashboard();