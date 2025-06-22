const form = document.getElementById('loginForm');
const identifier = document.getElementById('identifier');
const password = document.getElementById('password');
const error = document.getElementById('error');

// Обработчик для формы
form.addEventListener('submit', function(e) {
    e.preventDefault();
    let valid = true;

    if (identifier.value.trim() === '') {
        identifier.classList.add('shake');
        valid = false;
    } else {
        identifier.classList.remove('shake');
    }

    if (password.value.trim() === '') {
        password.classList.add('shake');
        valid = false;
    } else {
        password.classList.remove('shake');
    }

    if (valid) {
        // Выполнение дальнейших действий при успешной проверке
    }
});

// Обработчик для иконки глаза
const togglePassword = document.getElementById('togglePassword');
const passwordInput = document.getElementById('password');

togglePassword.addEventListener('click', function() {
    // Переключаем тип поля с 'password' на 'text' и наоборот
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;

    // Меняем иконку в зависимости от состояния поля
    if (type === 'password') {
        this.innerHTML = '<i class="fas fa-eye-slash"></i>'; // Закрытый глаз
    } else {
        this.innerHTML = '<i class="fas fa-eye"></i>'; // Открытый глаз
    }
});

// Базовый URL API из config.py
const API_URL = 'http://localhost:8000/api';

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const identifier = document.getElementById('identifier').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('error');
    errorEl.textContent = '';
    errorEl.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ identifier, password }),
            credentials: 'include' // Отправляем cookies (access_token_cookie, refresh_token_cookie)
        });

        if (!response.ok) {
            const errorData = await response.json();

            // Показываем пользователю понятное сообщение
            let errorMessage = 'Ошибка входа';
            if (errorData.detail) {
                errorMessage = errorData.detail;
            }

            throw new Error(errorMessage);
        }
        // Получаем параметр redirect из URL
        const urlParams = new URLSearchParams(window.location.search);
        const redirect = urlParams.get('redirect') || 'index.html';
        // Перенаправление на указанную страницу
        window.location.href = redirect;
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = 'block';

        // Анимация ошибки (опционально)
        document.querySelector('.auth-container').classList.add('shake');
        setTimeout(() => {
            document.querySelector('.auth-container').classList.remove('shake');
        }, 500);
    }
});