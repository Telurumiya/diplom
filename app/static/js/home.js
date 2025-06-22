const API_URL = 'http://localhost:8000/api';

// Проверка авторизации
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/user/profile`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Не авторизован');
        // Если авторизован, перенаправляем на index.html
        window.location.href = 'index.html';
    } catch (err) {
        // Пользователь не авторизован, остаемся на странице
    }
}

// Получаем элементы DOM
const uploadArea = document.querySelector('.file-upload');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const clearBtn = document.getElementById('clearBtn');
const previewArea = document.getElementById('previewArea');
const fileName = document.getElementById('fileName');
const errorEl = document.getElementById('error');

// Обработчики событий для drag and drop
['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, unhighlight, false);
});

// Функция для подсветки зоны
function highlight(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('highlight');
}

// Функция для снятия подсветки
function unhighlight(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('highlight');
}

// Обработка сброса файла
uploadArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length) {
        // Проверяем, что файл имеет правильное расширение
        if (!files[0].name.endsWith('.docx')) {
            errorEl.textContent = 'Поддерживаются только файлы .docx';
            errorEl.classList.remove('hidden');
            return;
        }

        // Устанавливаем файл в input
        fileInput.files = files;

        // Триггерим событие change для обработки файла
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    }
}

// Обработка выбора файла
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        // Проверка типа файла
        if (!file.name.endsWith('.docx')) {
            errorEl.textContent = 'Поддерживаются только файлы .docx';
            errorEl.classList.remove('hidden');
            return;
        }

        // Если все проверки пройдены
        errorEl.classList.add('hidden');
        previewArea.classList.remove('hidden');
        uploadArea.classList.add('hidden');
        fileName.textContent = file.name;
    }
});

// Очистка выбранного файла
clearBtn.addEventListener('click', () => {
    fileInput.value = '';
    previewArea.classList.add('hidden');
    uploadArea.classList.remove('hidden');
    errorEl.classList.add('hidden');
});

// Обработка загрузки файла
uploadBtn.addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_URL}/user/profile`, {
            credentials: 'include'
        });
        if (!response.ok) {
            // Если не авторизован, перенаправляем на login.html с redirect
            window.location.href = 'login.html?redirect=index.html';
            return;
        }
        // Если авторизован, перенаправляем на index.html
        window.location.href = 'index.html';
    } catch (err) {
        // Если ошибка при проверке авторизации, перенаправляем на login.html
        window.location.href = 'login.html?redirect=index.html';
    }
});

// Инициализация
checkAuth();