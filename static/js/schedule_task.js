document.addEventListener('DOMContentLoaded', () => {
    console.log("Додаток завантажено.");
});

/**
 * Функція для планування завдання
 */
async function scheduleTask() {
    const actionType = document.getElementById('actionType').value;
    const scheduleTime = parseFloat(document.getElementById('scheduleTime').value);

    if (!scheduleTime || scheduleTime < 1) {
        alert('Будь ласка, введіть коректний час у хвилинах.');
        return;
    }

    try {
        const response = await fetch('/schedule_task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionType, time_in_minutes: scheduleTime }),
        });

        const result = await response.json();
        alert(result.message || 'Завдання заплановано.');
    } catch (error) {
        console.error('Error scheduling task:', error);
        alert('Помилка під час планування завдання.');
    }
}

/**
 * Виконання підтвердженої дії
 */
function confirmAndSendAction(action) {
    const actionMessages = {
        shutdown: 'Ви впевнені, що хочете вимкнути комп\'ютер?',
        restart: 'Ви впевнені, що хочете перезавантажити комп\'ютер?',
        sleep: 'Ви впевнені, що хочете перевести комп\'ютер у режим сну?',
    };

    if (confirm(actionMessages[action])) {
        sendAction(action);
    }
}

/**
 * Відправлення POST-запиту для виконання дії
 */
async function sendAction(action) {
    try {
        const response = await fetch(`/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        const data = await response.json();
        alert(data.message || 'Дія виконана.');
    } catch (error) {
        console.error(`Error performing action (${action}):`, error);
        alert('Помилка під час виконання дії.');
    }
}

/**
 * Відкриття програми
 */
async function openProgram() {
    const programName = prompt("Введіть назву програми для відкриття (наприклад, notepad.exe):");
    if (programName) {
        showLoading();
        try {
            const response = await fetch('/open_program', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ program_name: programName }),
            });

            const data = await response.json();
            alert(data.message || 'Програма відкрита.');
        } catch (error) {
            console.error('Error opening program:', error);
            alert('Помилка під час відкриття програми.');
        } finally {
            hideLoading();
        }
    }
}

/**
 * Закриття програми
 */
async function closeProgram() {
    const programName = prompt("Введіть назву програми для закриття (наприклад, notepad.exe):");
    if (programName) {
        try {
            const response = await fetch('/close_program', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ program_name: programName }),
            });

            const data = await response.json();
            alert(data.message || 'Програма закрита.');
        } catch (error) {
            console.error('Error closing program:', error);
            alert('Помилка під час закриття програми.');
        }
    }
}

/**
 * Ввімкнення комп'ютера
 */
async function wakeComputer() {
    const macAddress = "D8-BB-C1-96-7B-26";

    if (confirm(`Ви впевнені, що хочете ввімкнути комп'ютер з MAC-адресою ${macAddress}?`)) {
        try {
            const response = await fetch('/wake_computer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mac: macAddress }),
            });

            const data = await response.json();
            alert(data.message || 'Комп\'ютер ввімкнено.');
        } catch (error) {
            console.error('Error waking computer:', error);
            alert('Помилка під час ввімкнення комп\'ютера.');
        }
    }
}

/**
 * Встановлення гучності
 */
async function setVolume() {
    const volumeSlider = document.getElementById('volumeSlider');
    const volumeLevel = parseFloat(volumeSlider.value);

    if (isNaN(volumeLevel) || volumeLevel < 0.0 || volumeLevel > 1.0) {
        alert('Будь ласка, введіть гучність у діапазоні від 0.0 до 1.0.');
        return;
    }

    try {
        const response = await fetch('/set_volume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ volume_level: volumeLevel }),
        });

        const result = await response.json();
        alert(result.message || 'Гучність встановлена.');
    } catch (error) {
        console.error('Error setting volume:', error);
        alert('Помилка під час встановлення гучності.');
    }
}

/**
 * Показ індикатора завантаження
 */
function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'loading';
    loader.textContent = 'Завантаження...';
    loader.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 20px;
        border-radius: 10px;
        font-size: 18px;
        z-index: 1000;
    `;
    document.body.appendChild(loader);
}

/**
 * Приховування індикатора завантаження
 */
function hideLoading() {
    const loader = document.getElementById('loading');
    if (loader) loader.remove();
}