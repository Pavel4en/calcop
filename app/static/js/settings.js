// Глобальные переменные и элементы DOM
let currentNormValues = {};
let currentNorm = null;

// Функция переключения боковой панели
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar-menu');
    const mainContent = document.getElementById('main-content');
    const burgerButton = document.getElementById('burger-button');
    
    if (sidebar.style.display === 'none') {
        sidebar.style.display = 'block';
        mainContent.classList.remove('is-12');
        mainContent.classList.add('is-10');
        burgerButton.classList.add('is-active');
    } else {
        sidebar.style.display = 'none';
        mainContent.classList.remove('is-10');
        mainContent.classList.add('is-12');
        burgerButton.classList.remove('is-active');
    }
}

// Функция переключения вкладок
function switchTab(tabId) {
    // Находим все вкладки и панели
    const tabItems = document.querySelectorAll('.tabs li');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // Убираем активный класс со всех вкладок
    tabItems.forEach(function(item) {
        item.classList.remove('is-active');
    });
    
    // Скрываем все панели
    tabPanes.forEach(function(pane) {
        pane.style.display = 'none';
    });
    
    // Устанавливаем активный класс на нужную вкладку
    document.getElementById('tab-' + tabId.replace('-tab', '')).classList.add('is-active');
    
    // Показываем нужную панель
    document.getElementById(tabId).style.display = 'block';
    
    // Если это вкладка норм, загружаем данные
    if (tabId === 'norms-tab') {
        loadNorms();
    }
}

// Функция загрузки норм
function loadNorms() {
    const tbody = document.getElementById('norms-table-body');
    tbody.innerHTML = '<tr><td colspan="5" class="has-text-centered">Загрузка данных...</td></tr>';
    
    // Выполняем GET-запрос на API
    fetch('/settings/api/norms')
        .then(response => {
            if (!response.ok) {
                throw new Error('HTTP error ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Loaded norms:', data);
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="has-text-centered">Нет данных</td></tr>';
                return;
            }
            
            data.forEach(norm => {
                const tr = document.createElement('tr');
                
                // ID
                const tdId = document.createElement('td');
                tdId.textContent = norm.id;
                tr.appendChild(tdId);
                
                // Название
                const tdName = document.createElement('td');
                tdName.textContent = norm.name;
                tr.appendChild(tdName);
                
                // Значение
                const tdValue = document.createElement('td');
                tdValue.textContent = norm.value;
                tr.appendChild(tdValue);
                
                // Блокировка
                const tdLocked = document.createElement('td');
                const lockIcon = document.createElement('span');
                lockIcon.className = 'icon';
                const icon = document.createElement('i');
                icon.className = norm.locked ? 'fas fa-lock has-text-danger' : 'fas fa-unlock has-text-success';
                lockIcon.appendChild(icon);
                tdLocked.appendChild(lockIcon);
                tr.appendChild(tdLocked);
                
                // Действия
                const tdActions = document.createElement('td');
                
                // Кнопка редактирования
                const editButton = document.createElement('button');
                editButton.className = 'button is-small is-info mr-1';
                editButton.innerHTML = '<span class="icon"><i class="fas fa-edit"></i></span>';
                editButton.title = 'Редактировать';
                editButton.onclick = function() { openEditNormModal(norm); };
                tdActions.appendChild(editButton);
                
                // Кнопка удаления
                const deleteButton = document.createElement('button');
                deleteButton.className = 'button is-small is-danger';
                deleteButton.innerHTML = '<span class="icon"><i class="fas fa-trash"></i></span>';
                deleteButton.title = 'Удалить';
                deleteButton.onclick = function() { openDeleteConfirmModal(norm); };
                tdActions.appendChild(deleteButton);
                
                tr.appendChild(tdActions);
                
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки норм:', error);
            tbody.innerHTML = '<tr><td colspan="5" class="has-text-centered has-text-danger">Ошибка загрузки данных</td></tr>';
        });
}

// Открытие модального окна редактирования нормы
function openEditNormModal(norm) {
    currentNorm = norm;
    
    document.getElementById('norm-modal-title').textContent = 'Редактирование нормы';
    document.getElementById('norm-id').value = norm.id;
    document.getElementById('norm-name').value = norm.name;
    document.getElementById('norm-value').value = norm.value;
    document.getElementById('norm-locked').checked = norm.locked;
    
    document.getElementById('norm-modal').classList.add('is-active');
}

// Закрытие модального окна нормы
function closeNormModal() {
    document.getElementById('norm-modal').classList.remove('is-active');
}

// Сохранение нормы
function saveNorm() {
    const form = document.getElementById('norm-form');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const normId = document.getElementById('norm-id').value;
    const normName = document.getElementById('norm-name').value;
    const normValue = document.getElementById('norm-value').value;
    const normLocked = document.getElementById('norm-locked').checked;
    
    const normData = {
        name: normName,
        value: parseFloat(normValue),
        locked: normLocked
    };
    
    const isEdit = normId !== '';
    const url = isEdit ? `/settings/api/norms/${normId}` : '/settings/api/norms';
    const method = isEdit ? 'PUT' : 'POST';
    
    console.log(`Saving norm: ${method} ${url}`, normData);
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(normData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Error ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Save response:', data);
        closeNormModal();
        loadNorms();
        
        showNotification(isEdit ? 'Норма успешно обновлена' : 'Норма успешно добавлена');
    })
    .catch(error => {
        console.error('Ошибка сохранения нормы:', error);
        alert('Произошла ошибка при сохранении нормы: ' + error.message);
    });
}

// Открытие модального окна подтверждения удаления
function openDeleteConfirmModal(norm) {
    currentNorm = norm;
    
    document.getElementById('delete-norm-name').textContent = norm.name;
    document.getElementById('delete-norm-id').value = norm.id;
    
    document.getElementById('confirm-delete-modal').classList.add('is-active');
}

// Закрытие модального окна подтверждения удаления
function closeConfirmModal() {
    document.getElementById('confirm-delete-modal').classList.remove('is-active');
}

// Удаление нормы
function deleteNorm() {
    const normId = document.getElementById('delete-norm-id').value;
    
    console.log(`Deleting norm: ${normId}`);
    
    fetch(`/settings/api/norms/${normId}`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Delete response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Error ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Delete response:', data);
        closeConfirmModal();
        loadNorms();
        
        showNotification('Норма успешно удалена');
    })
    .catch(error => {
        console.error('Ошибка удаления нормы:', error);
        alert('Произошла ошибка при удалении нормы: ' + error.message);
    });
}

// Показ уведомления
function showNotification(message) {
    const flashMessages = document.getElementById('flash-messages');
    
    const notification = document.createElement('div');
    notification.className = 'notification flash-message is-success';
    notification.setAttribute('data-autodismiss', '');
    
    const deleteButton = document.createElement('button');
    deleteButton.className = 'delete';
    deleteButton.onclick = function() {
        notification.parentNode.removeChild(notification);
    };
    
    notification.appendChild(deleteButton);
    notification.appendChild(document.createTextNode(message));
    
    flashMessages.appendChild(notification);
    
    // Автоматическое исчезновение уведомления
    setTimeout(function() {
        notification.style.opacity = '0';
        setTimeout(function() {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 500);
    }, 3000);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация обработчика для кнопки добавления нормы
    document.getElementById('add-norm-button').onclick = function() {
        document.getElementById('norm-modal-title').textContent = 'Добавление нормы';
        document.getElementById('norm-id').value = '';
        document.getElementById('norm-name').value = '';
        document.getElementById('norm-value').value = '';
        document.getElementById('norm-locked').checked = false;
        
        document.getElementById('norm-modal').classList.add('is-active');
    };
});