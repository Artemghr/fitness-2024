from flask import Flask, jsonify, request, abort, render_template_string
from datetime import datetime, timezone
import json
import os

app = Flask(__name__)

# Абсолютные пути к файлам
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SCHEDULE_FILE = os.path.join(BASE_DIR, 'schedule.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.txt')

# Загрузка расписания из файла или инициализация по умолчанию
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            try:
                schedule = json.load(f)
                print(f"Загружено расписание из {SCHEDULE_FILE}.")
                return schedule
            except json.JSONDecodeError:
                print("Ошибка при загрузке schedule.json. Используется расписание по умолчанию.")
                return []
    else:
        default_schedule = [
            {
                "id": 1,
                "name": "Йога",
                "instructor": "Анна Иванова",
                "datetime": "2024-05-01T10:00:00",
                "capacity": 20,
                "registered": 15
            },
            {
                "id": 2,
                "name": "Пилатес",
                "instructor": "Игорь Смирнов",
                "datetime": "2024-05-01T12:00:00",
                "capacity": 15,
                "registered": 10
            },
            {
                "id": 3,
                "name": "Кардио",
                "instructor": "Мария Петрова",
                "datetime": "2024-05-01T14:00:00",
                "capacity": 25,
                "registered": 20
            }
        ]
        save_schedule(default_schedule)
        print(f"Создано стандартное расписание в {SCHEDULE_FILE}.")
        return default_schedule

# Сохранение расписания в файл
def save_schedule(schedule):
    try:
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=4)
        print(f"Расписание сохранено в {SCHEDULE_FILE}.")
    except Exception as e:
        print(f"Ошибка при сохранении расписания: {e}")

# Загрузка расписания при старте
classes_schedule = load_schedule()

# Список записей на тренировки (будет загружаться из users.txt)
registrations = []

# Загрузка регистраций из users.txt
def load_registrations():
    registrations = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    registration = json.loads(line.strip())
                    registrations.append(registration)
                except json.JSONDecodeError:
                    print("Некорректная строка в users.txt, пропущена.")
                    continue
        print(f"Загружено {len(registrations)} регистраций из {USERS_FILE}.")
    else:
        print(f"{USERS_FILE} не существует. Создаётся новый файл.")
    return registrations

registrations = load_registrations()

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Фитнес-Зал</title>
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- Bootstrap Icons -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body {
                background-color: #f8f9fa;
            }
            .container {
                margin-top: 50px;
                margin-bottom: 50px;
            }
            .class-card:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                transition: 0.3s;
            }
            .modal-header {
                background-color: #0d6efd;
                color: white;
            }
            .btn-custom {
                transition: transform 0.2s;
            }
            .btn-custom:hover {
                transform: scale(1.05);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mb-4">Расписание Занятий</h1>
            <div id="schedule" class="row row-cols-1 row-cols-md-2 g-4"></div>
            <div class="text-center mt-4">
                <button id="add-schedule-button" class="btn btn-primary btn-lg btn-custom">
                    <i class="bi bi-plus-circle"></i> Добавить Расписание
                </button>
            </div>
        </div>
    
        <!-- Форма регистрации -->
        <div id="registration-form" class="modal fade" tabindex="-1" aria-labelledby="registrationModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="registrationModalLabel">Оформить Регистрацию</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Закрыть"></button>
                    </div>
                    <div class="modal-body">
                        <form id="form">
                            <input type="hidden" id="class_id" name="class_id">
                            <div class="mb-3">
                                <label for="user_name" class="form-label">Имя</label>
                                <input type="text" class="form-control" id="user_name" name="user_name" required>
                            </div>
                            <div class="mb-3">
                                <label for="phone_number" class="form-label">Номер Телефона</label>
                                <input type="tel" class="form-control" id="phone_number" name="phone_number" required pattern="\+?\d{10,15}" placeholder="+79876543210">
                                <div class="form-text">Формат: +1234567890</div>
                            </div>
                            <button type="submit" class="btn btn-success btn-custom">
                                <i class="bi bi-check-circle"></i> Зарегистрироваться
                            </button>
                        </form>
                        <div id="form-message" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    
        <!-- Форма добавления расписания -->
        <div id="add-schedule-form" class="modal fade" tabindex="-1" aria-labelledby="addScheduleModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addScheduleModalLabel">Добавить Новое Занятие</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Закрыть"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-schedule">
                            <div class="mb-3">
                                <label for="name" class="form-label">Название Занятия</label>
                                <input type="text" class="form-control" id="name" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label for="instructor" class="form-label">Инструктор</label>
                                <input type="text" class="form-control" id="instructor" name="instructor" required>
                            </div>
                            <div class="mb-3">
                                <label for="datetime" class="form-label">Дата и Время</label>
                                <input type="datetime-local" class="form-control" id="datetime" name="datetime" required>
                            </div>
                            <div class="mb-3">
                                <label for="capacity" class="form-label">Вместимость</label>
                                <input type="number" class="form-control" id="capacity" name="capacity" min="1" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-custom">
                                <i class="bi bi-plus-circle"></i> Добавить Занятие
                            </button>
                        </form>
                        <div id="add-schedule-message" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    
        <!-- Bootstrap JS and dependencies -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const scheduleDiv = document.getElementById('schedule');
                const registrationModal = new bootstrap.Modal(document.getElementById('registration-form'));
                const addScheduleModal = new bootstrap.Modal(document.getElementById('add-schedule-form'));
                const form = document.getElementById('form');
                const formMessage = document.getElementById('form-message');
                const addScheduleButton = document.getElementById('add-schedule-button');
                const addScheduleForm = document.getElementById('add-schedule');
                const addScheduleMessage = document.getElementById('add-schedule-message');
            
                // Функция для загрузки расписания
                function loadSchedule() {
                    fetch('/api/schedule')
                        .then(response => response.json())
                        .then(data => {
                            scheduleDiv.innerHTML = ''; // Очистить текущие карточки
                            data.forEach(cls => {
                                const col = document.createElement('div');
                                col.className = 'col';
                
                                const card = document.createElement('div');
                                card.className = 'card h-100';
                
                                const cardBody = document.createElement('div');
                                cardBody.className = 'card-body';
                
                                const cardTitle = document.createElement('h5');
                                cardTitle.className = 'card-title';
                                cardTitle.textContent = cls.name;
                
                                const instructor = document.createElement('p');
                                instructor.className = 'card-text';
                                instructor.innerHTML = `<strong>Инструктор:</strong> ${cls.instructor}`;
                
                                const datetime = document.createElement('p');
                                datetime.className = 'card-text';
                                const date = new Date(cls.datetime);
                                datetime.innerHTML = `<strong>Дата и Время:</strong> ${date.toLocaleString()}`;
                
                                const capacity = document.createElement('p');
                                capacity.className = 'card-text';
                                capacity.innerHTML = `<strong>Вместимость:</strong> ${cls.capacity}`;
                
                                const registered = document.createElement('p');
                                registered.className = 'card-text';
                                registered.innerHTML = `<strong>Зарегистрировано:</strong> ${cls.registered}`;
                
                                cardBody.appendChild(cardTitle);
                                cardBody.appendChild(instructor);
                                cardBody.appendChild(datetime);
                                cardBody.appendChild(capacity);
                                cardBody.appendChild(registered);
                
                                const cardFooter = document.createElement('div');
                                cardFooter.className = 'card-footer text-center';
                
                                const button = document.createElement('button');
                                button.className = 'btn btn-success btn-custom';
                                button.innerHTML = '<i class="bi bi-person-plus-fill"></i> Оформить';
                                button.onclick = () => openRegistrationModal(cls.id);
                
                                cardFooter.appendChild(button);
                
                                card.appendChild(cardBody);
                                card.appendChild(cardFooter);
                
                                col.appendChild(card);
                                scheduleDiv.appendChild(col);
                            });
                        })
                        .catch(error => {
                            console.error('Ошибка при загрузке расписания:', error);
                            scheduleDiv.innerHTML = '<p>Не удалось загрузить расписание.</p>';
                        });
                }
            
                loadSchedule(); // Загрузить расписание при загрузке страницы
            
                // Функция открытия модального окна регистрации
                function openRegistrationModal(class_id) {
                    document.getElementById('class_id').value = class_id;
                    formMessage.innerHTML = '';
                    form.reset();
                    registrationModal.show();
                }
            
                // Функция открытия модального окна добавления расписания
                function openAddScheduleModal() {
                    addScheduleMessage.innerHTML = '';
                    addScheduleForm.reset();
                    addScheduleModal.show();
                }
            
                // Обработчик кнопки добавления расписания
                addScheduleButton.addEventListener('click', openAddScheduleModal);
            
                // Обработка отправки формы регистрации
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
            
                    const class_id = document.getElementById('class_id').value;
                    const user_name = document.getElementById('user_name').value.trim();
                    const phone_number = document.getElementById('phone_number').value.trim();
            
                    // Простая валидация
                    if (!user_name || !phone_number) {
                        formMessage.innerHTML = '<div class="alert alert-danger" role="alert">Пожалуйста, заполните все поля.</div>';
                        return;
                    }
            
                    // Отправка данных на сервер
                    fetch('/api/register_web', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ class_id: parseInt(class_id), user_name, phone_number })
                    })
                    .then(response => response.json().then(data => ({status: response.status, body: data})))
                    .then(result => {
                        if (result.status === 201) {
                            formMessage.innerHTML = '<div class="alert alert-success" role="alert">Регистрация прошла успешно!</div>';
                            // Обновить расписание
                            setTimeout(() => {
                                registrationModal.hide();
                                loadSchedule();
                            }, 1500);
                        } else {
                            formMessage.innerHTML = `<div class="alert alert-danger" role="alert">${result.body.message || 'Ошибка при регистрации.'}</div>`;
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка при регистрации:', error);
                        formMessage.innerHTML = '<div class="alert alert-danger" role="alert">Произошла ошибка. Пожалуйста, попробуйте позже.</div>';
                    });
                });
            
                // Обработка отправки формы добавления расписания
                addScheduleForm.addEventListener('submit', function(e) {
                    e.preventDefault();
            
                    const name = document.getElementById('name').value.trim();
                    const instructor = document.getElementById('instructor').value.trim();
                    const datetime = document.getElementById('datetime').value;
                    const capacity = parseInt(document.getElementById('capacity').value);
            
                    // Простая валидация
                    if (!name || !instructor || !datetime || !capacity) {
                        addScheduleMessage.innerHTML = '<div class="alert alert-danger" role="alert">Пожалуйста, заполните все поля.</div>';
                        return;
                    }
            
                    // Преобразование datetime в ISO формат
                    const datetimeISO = new Date(datetime).toISOString();
            
                    // Отправка данных на сервер
                    fetch('/api/schedule', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ name, instructor, datetime: datetimeISO, capacity })
                    })
                    .then(response => response.json().then(data => ({status: response.status, body: data})))
                    .then(result => {
                        if (result.status === 201) {
                            addScheduleMessage.innerHTML = '<div class="alert alert-success" role="alert">Занятие успешно добавлено!</div>';
                            // Обновить расписание
                            setTimeout(() => {
                                addScheduleModal.hide();
                                loadSchedule();
                            }, 1500);
                        } else {
                            addScheduleMessage.innerHTML = `<div class="alert alert-danger" role="alert">${result.body.message || 'Ошибка при добавлении занятия.'}</div>`;
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка при добавлении занятия:', error);
                        addScheduleMessage.innerHTML = '<div class="alert alert-danger" role="alert">Произошла ошибка. Пожалуйста, попробуйте позже.</div>';
                    });
                });
            });
        </script>
    </body>
    </html>
    """, classes_schedule=classes_schedule)

# Получение расписания
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    return jsonify(classes_schedule), 200

# Добавление нового занятия
@app.route('/api/schedule', methods=['POST'])
def add_schedule():
    if not request.json:
        abort(400, description="Некорректный запрос. Требуется JSON с полями 'name', 'instructor', 'datetime', 'capacity'.")

    required_fields = ['name', 'instructor', 'datetime', 'capacity']
    for field in required_fields:
        if field not in request.json:
            abort(400, description=f"Отсутствует поле '{field}'.")

    name = request.json['name']
    instructor = request.json['instructor']
    datetime_str = request.json['datetime']
    capacity = request.json['capacity']

    # Валидация данных
    try:
        # Проверка формата даты и времени
        datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', ''))
    except ValueError:
        abort(400, description="Некорректный формат 'datetime'. Используйте ISO формат, например '2024-05-01T10:00:00'.")
    
    if not isinstance(capacity, int) or capacity <= 0:
        abort(400, description="'capacity' должно быть положительным целым числом.")

    # Генерация нового ID
    new_id = max([cls['id'] for cls in classes_schedule], default=0) + 1

    new_class = {
        "id": new_id,
        "name": name,
        "instructor": instructor,
        "datetime": datetime_str,
        "capacity": capacity,
        "registered": 0
    }

    classes_schedule.append(new_class)
    save_schedule(classes_schedule)

    return jsonify(new_class), 201

# Регистрация через API (существующий эндпоинт)
@app.route('/api/register', methods=['POST'])
def register_class():
    if not request.json or 'class_id' not in request.json or 'user_name' not in request.json:
        abort(400, description="Некорректный запрос. Требуются 'class_id' и 'user_name'.")

    class_id = request.json['class_id']
    user_name = request.json['user_name']

    # Поиск занятия по ID
    fitness_class = next((cls for cls in classes_schedule if cls['id'] == class_id), None)
    if not fitness_class:
        abort(404, description="Занятие не найдено.")

    if fitness_class['registered'] >= fitness_class['capacity']:
        abort(400, description="Места на занятие закончились.")

    # Создание записи
    registration = {
        "registration_id": len(registrations) + 1,
        "class_id": class_id,
        "user_name": user_name,
        "registration_time": datetime.now(timezone.utc).isoformat()
    }
    registrations.append(registration)

    # Обновление количества зарегистрированных
    fitness_class['registered'] += 1
    save_schedule(classes_schedule)

    return jsonify(registration), 201

# Регистрация через веб-интерфейс
@app.route('/api/register_web', methods=['POST'])
def register_web():
    if not request.json or 'class_id' not in request.json or 'user_name' not in request.json or 'phone_number' not in request.json:
        abort(400, description="Некорректный запрос. Требуются 'class_id', 'user_name' и 'phone_number'.")

    class_id = request.json['class_id']
    user_name = request.json['user_name']
    phone_number = request.json['phone_number']

    # Поиск занятия по ID
    fitness_class = next((cls for cls in classes_schedule if cls['id'] == class_id), None)
    if not fitness_class:
        abort(404, description="Занятие не найдено.")

    if fitness_class['registered'] >= fitness_class['capacity']:
        abort(400, description="Места на занятие закончились.")

    # Обновление количества зарегистрированных
    fitness_class['registered'] += 1
    save_schedule(classes_schedule)

    # Создание записи
    registration = {
        "registration_id": len(registrations) + 1,
        "class_id": class_id,
        "user_name": user_name,
        "phone_number": phone_number,
        "registration_time": datetime.now(timezone.utc).isoformat()
    }
    registrations.append(registration)

    # Сохранение в users.txt
    try:
        with open(USERS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registration, ensure_ascii=False) + '\n')
        print(f"Регистрация записана в {USERS_FILE}: {registration}")
    except Exception as e:
        # Отмена изменения зарегистрированных, если не удалось сохранить
        fitness_class['registered'] -= 1
        save_schedule(classes_schedule)
        print(f"Ошибка при сохранении в users.txt: {e}")
        abort(500, description="Ошибка при сохранении данных.")

    return jsonify({"message": "Регистрация успешна!"}), 201

# Получение всех регистраций
@app.route('/api/registrations', methods=['GET'])
def get_registrations():
    return jsonify(registrations), 200

# Обработка ошибок
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": error.description}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": error.description}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server Error", "message": error.description}), 500

if __name__ == '__main__':
    # Убедимся, что users.txt существует
    if not os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                print(f"{USERS_FILE} создан.")
        except Exception as e:
            print(f"Не удалось создать {USERS_FILE}: {e}")
    
    # Убедимся, что schedule.json существует
    if not os.path.exists(SCHEDULE_FILE):
        save_schedule(classes_schedule)
        print(f"{SCHEDULE_FILE} создан с начальным расписанием.")
    
    app.run(debug=True)
