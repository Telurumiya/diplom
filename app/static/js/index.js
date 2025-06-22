/**
 * Базовый URL API из конфигурации.
 * @type {string}
 */
const API_URL = 'http://localhost:8000/api';
let pollingInterval;
let lastDocumentsHash = '';

/**
 * Проверяет авторизацию пользователя.
 * @returns {Promise<void>}
 */
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/user/profile`, {
            credentials: 'include' // Отправляем cookies
        });
        if (!response.ok) throw new Error('Не авторизован');
    } catch (err) {
        window.location.href = 'login.html';
    }
}

/**
 * Получаем элементы DOM.
 * @type {HTMLElement}
 */
const uploadArea = document.querySelector('.file-upload');
const fileInput = document.getElementById('fileInput');

/**
 * Обработчики событий для drag and drop.
 */
['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, unhighlight, false);
});

/**
 * Подсвечивает зону загрузки при drag and drop.
 * @param {Event} e - Событие.
 */
function highlight(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('highlight');
}

/**
 * Снимает подсветку с зоны загрузки.
 * @param {Event} e - Событие.
 */
function unhighlight(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('highlight');
}

/**
 * Обрабатывает событие drop для загрузки файла.
 * @param {DragEvent} e - Событие drop.
 */
function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length) {
        // Проверяем, что файл имеет правильное расширение
        if (!files[0].name.endsWith('.docx')) {
            document.getElementById('error').textContent = 'Поддерживаются только файлы .docx';
            document.getElementById('error').classList.remove('hidden');
            return;
        }

        // Устанавливаем файл в input
        fileInput.files = files;

        // Триггерим событие change для обработки файла
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    }
}

/**
 * Обрабатывает изменение выбранного файла.
 */
document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const errorEl = document.getElementById('error');

    if (file) {
        // Проверка типа файла
        if (!file.name.endsWith('.docx')) {
            errorEl.textContent = 'Поддерживаются только файлы .docx';
            errorEl.classList.remove('hidden');
            return;
        }

        // Если все проверки пройдены
        errorEl.classList.add('hidden');
        filePreview.classList.remove('hidden');
        fileName.textContent = file.name;
        uploadArea.classList.add('hidden');
        previewArea.classList.remove('hidden');
    }
});

/**
 * Очищает выбранный файл.
 */
document.getElementById('clearBtn').addEventListener('click', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');
    const filePreview = document.getElementById('filePreview');

    fileInput.value = '';
    filePreview.classList.add('hidden');
    previewArea.classList.add('hidden');
    uploadArea.classList.remove('hidden');

    // Скрываем сообщение об ошибке
    document.getElementById('error').classList.add('hidden');
});

/**
 * Форматирует дату в строковый формат.
 * @param {string} dateString - Дата в формате ISO.
 * @returns {string} Отформатированная дата.
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Загружает список документов с сервера.
 * @returns {Promise<void>}
 */
async function loadDocuments() {
    try {
        const response = await fetch(`${API_URL}/documents/all?page=1&limit=10`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка при загрузке документов');
        const documents = await response.json();

        // Сортируем документы по дате загрузки (убывание)
        documents.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));

        // Вычисляем хэш текущих документов
        const currentHash = JSON.stringify(documents.map(doc => ({
            id: doc.id,
            status: doc.status,
            error_count: doc.error_count,
            uploaded_at: doc.uploaded_at,
            filename: doc.filename
        })));

        // Если хэш изменился, обновляем таблицу
        if (currentHash !== lastDocumentsHash) {
            renderDocuments(documents);
            lastDocumentsHash = currentHash;
        }
    } catch (err) {
        document.getElementById('error').textContent = err.message;
        document.getElementById('error').classList.remove('hidden');
    }
}

/**
 * Константа для сообщения о пустом списке документов.
 * @type {string}
 */
const EMPTY_DOCUMENTS_MESSAGE = 'Список документов пуст';

/**
 * Отрисовывает таблицу документов.
 * @param {Array<Object>} documents - Список документов для отображения.
 */
function renderDocuments(documents) {
    const tbody = document.getElementById('documentsBody');
    tbody.innerHTML = '';

    if (documents.length === 0) {
        // Отображаем сообщение, если список документов пуст
        const tr = document.createElement('tr');
        tr.classList.add('empty-row');
        tr.innerHTML = `
            <td colspan="6" class="empty-message">${EMPTY_DOCUMENTS_MESSAGE}</td>
        `;
        tbody.appendChild(tr);
        return;
    }

    const STATUS_MAP = {
        'В обработке': { class: 'PENDING', display: 'В обработке' },
        'Проверен': { class: 'CHECKED', display: 'Проверен' },
        'Ошибка': { class: 'FAILED', display: 'Ошибка' }
    };

    documents.forEach(doc => {
        const tr = document.createElement('tr');
        const statusInfo = STATUS_MAP[doc.status] || { class: 'pending', display: doc.status };
        tr.classList.add('doc-row');
        tr.innerHTML = `
            <td class="px-6 py-4 text-left border-r border-gray-200">${doc.filename}</td>
            <td class="px-6 py-4 text-left border-r border-gray-200">
                <span class="status-cell status-${statusInfo.class}">${statusInfo.display}</span>
            </td>
            <td class="px-6 py-4 text-left border-r border-gray-200 error-count-cell ${doc.error_count > 0 ? '' : 'disabled'}" data-doc-id="${doc.id}">${doc.error_count ?? '—'}</td>
            <td class="px-6 py-4 text-left border-r border-gray-200">${formatDate(doc.uploaded_at)}</td>
            <td class="px-6 py-4 text-left border-r border-gray-200">
                <div class="flex space-x-4">
                    <a href="#" onclick="downloadDocument(${doc.id}, 'Оригинал'); return false;"
                       class="text-blue-600 hover:text-blue-800">Оригинал</a>
                    ${doc.new_filepath ?
                      `<a href="#" onclick="downloadDocument(${doc.id}, 'Проверенный'); return false;"
                         class="text-blue-600 hover:text-blue-800">Проверенный</a>` :
                      '<span class="text-gray-400">—</span>'}
                </div>
            </td>
            <td class="px-6 py-4 text-left">
                <a href="#" onclick="deleteDocument(${doc.id}); return false;"
                   class="text-red-600 hover:text-red-800">Удалить</a>
            </td>
        `;

        tr.onclick = async (e) => {
            if (e.target.tagName === 'A') return;

            // Проверяем, что клик был по ячейке с количеством ошибок
            const errorCountCell = e.target.closest('.error-count-cell');
            if (!errorCountCell) return;

            // Проверяем, существует ли следующая строка с деталями
            const nextRow = tr.nextElementSibling;
            if (nextRow?.classList.contains('details-row')) {
                nextRow.remove();
                return;
            }

            try {
                const response = await fetch(`${API_URL}/documents/${doc.id}`, {
                    credentials: 'include'
                });
                if (!response.ok) throw new Error('Ошибка при получении данных');
                const documentData = await response.json();

                const errorHtml = renderErrorDetails(documentData);
                const detailsTr = document.createElement('tr');
                detailsTr.classList.add('details-row');
                detailsTr.innerHTML = `<td colspan="6">${errorHtml}</td>`;
                tr.after(detailsTr);
            } catch (err) {
                alert('Ошибка загрузки информации о документе: ' + err.message);
            }
        };

        tbody.appendChild(tr);
    });
}

/**
 * Обрабатывает загрузку документа.
 */
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const errorEl = document.getElementById('error');
    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');
    if (!fileInput.files[0]) {
        errorEl.textContent = 'Выберите файл';
        errorEl.classList.remove('hidden');
        return;
    }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    try {
        const response = await fetch(`${API_URL}/documents/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка при загрузке файла');
        fileInput.value = '';
        errorEl.classList.add('hidden');
        previewArea.classList.add('hidden');
        uploadArea.classList.remove('hidden');

        await loadDocuments();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.remove('hidden');
    }
});

/**
 * Скачивает документ по его ID и типу.
 * @param {number} id - ID документа.
 * @param {string} docType - Тип документа ('Оригинал' или 'Проверенный').
 * @returns {Promise<void>}
 */
async function downloadDocument(id, docType) {
    try {
        const response = await fetch(`${API_URL}/documents/${id}/download?doc_type=${docType}`, {
            credentials: 'include'
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || 'Ошибка при скачивании');
        }
        // Получаем имя файла из заголовка или используем fallback
        let filename = 'document.docx';
        const disposition = response.headers.get('content-disposition');
        if (disposition) {
            const filenameRegex = /filename\*=UTF-8''([^;]+)/i;
            const match = filenameRegex.exec(disposition);
            if (match && match[1]) {
                filename = decodeURIComponent(match[1]);
            } else {
                const fallbackRegex = /filename="?([^"]+)"?/i;
                const fallbackMatch = fallbackRegex.exec(disposition);
                if (fallbackMatch && fallbackMatch[1]) {
                   filename = fallbackMatch[1];
                }
            }
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();

        // Очистка
        setTimeout(() => {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 100);
    } catch (err) {
        document.getElementById('error').textContent = err.message;
        document.getElementById('error').classList.remove('hidden');
    }
}

/**
 * Удаляет документ по его ID.
 * @param {number} id - ID документа.
 * @returns {Promise<void>}
 */
async function deleteDocument(id) {
    if (!confirm('Вы уверены, что хотите удалить документ?')) return;
    try {
        const response = await fetch(`${API_URL}/documents/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка при удалении');
        await loadDocuments();
    } catch (err) {
        document.getElementById('error').textContent = err.message;
        document.getElementById('error').classList.remove('hidden');
    }
}

/**
 * Выполняет выход из системы.
 * @returns {Promise<void>}
 */
async function logout() {
    try {
        const response = await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка при выходе');
        window.location.href = 'login.html';
    } catch (err) {
        document.getElementById('error').textContent = err.message;
        document.getElementById('error').classList.remove('hidden');
    }
}

/**
 * Запускает опрос сервера для проверки изменений в данных документов.
 */
function startPolling() {
    // Остановить предыдущий интервал, если он был
    if (pollingInterval) clearInterval(pollingInterval);

    // Установить новый интервал (например, каждые 5 секунд)
    pollingInterval = setInterval(loadDocuments, 5000); // 5 секунд
}

/**
 * Отрисовывает детали ошибок документа.
 * @param {Object} document - Данные документа.
 * @returns {string} HTML-код для отображения ошибок.
 */
function renderErrorDetails(document) {
    if (!document.errors || Object.keys(document.errors).length === 0) {
        return '<p>Нет ошибок в документе.</p>';
    }

    let html = '<div class="error-details">';
    for (const [type, errors] of Object.entries(document.errors)) {
        html += `
            <div class="error-group">
                <h3>${type} (${errors.length})</h3>
                <table class="error-table">
                    <thead>
                        <tr>
                            <th>Сообщение</th>
                            <th>Текст</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${errors.map(error => `
                            <tr>
                                <td>${error.message}</td>
                                <td>${error.paragraph_text}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    html += '</div>';
    return html;
}

/**
 * Инициализация приложения.
 */
checkAuth().then(() => {
    loadDocuments();
    startPolling();
});