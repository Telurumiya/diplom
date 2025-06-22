
        const API_URL = 'http://localhost:8000/api';
        document.getElementById('signupForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const error = document.getElementById('error');

            if (!email || !username || !password) {
                error.classList.remove('hidden');
                document.querySelector('.auth-container').classList.add('shake');
                return;
            }

            try {
                const response = await fetch(`${API_URL}/auth/signup`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, username, password }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    error.textContent = errorData.detail || 'Ошибка при регистрации';
                    error.classList.remove('hidden');
                    document.querySelector('.auth-container').classList.add('shake');
                    return;
                }

                window.location.href = '/diplom1/app/static/login.html';
            } catch (err) {
                error.textContent = 'Произошла ошибка. Попробуйте снова.';
                error.classList.remove('hidden');
                document.querySelector('.auth-container').classList.add('shake');
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
