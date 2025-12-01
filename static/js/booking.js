class BookingManager {
    constructor() {
        this.selectedSeats = new Set();
        this.seatPrice = parseInt(document.getElementById('seat-price').dataset.price);
        this.sessionId = parseInt(document.getElementById('session-id').dataset.id);
        this.maxSeats = 10; // Максимальна кількість місць
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupFormValidation();
    }
    
    bindEvents() {
        // Обробник вибору місць
        document.querySelectorAll('.seat-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleSeatSelection(e));
        });
        
        // Обробник форми
        document.getElementById('booking-form').addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Обробник підтвердження бронювання
        document.getElementById('confirm-booking').addEventListener('click', () => this.confirmBooking());
    }
    
    setupFormValidation() {
        const form = document.getElementById('booking-form');
        const inputs = form.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (input.checkValidity()) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                } else {
                    input.classList.remove('is-valid');
                    input.classList.add('is-invalid');
                }
            });
        });
    }
    
    handleSeatSelection(event) {
        const checkbox = event.target;
        const seatId = checkbox.dataset.seatId;
        const seatLabel = checkbox.nextElementSibling;
        
        if (checkbox.checked) {
            if (this.selectedSeats.size >= this.maxSeats) {
                checkbox.checked = false;
                this.showMaxSeatsWarning();
                return;
            }
            
            this.selectedSeats.add(seatId);
            seatLabel.classList.remove('btn-outline-primary');
            seatLabel.classList.add('btn-warning');
        } else {
            this.selectedSeats.delete(seatId);
            seatLabel.classList.remove('btn-warning');
            seatLabel.classList.add('btn-outline-primary');
        }
        
        this.updateBookingSummary();
        this.hideMaxSeatsWarning();
    }
    
    showMaxSeatsWarning() {
        const warning = document.getElementById('max-seats-warning');
        warning.classList.remove('d-none');
        
        // Автоматично приховати попередження через 3 секунди
        setTimeout(() => {
            this.hideMaxSeatsWarning();
        }, 3000);
    }
    
    hideMaxSeatsWarning() {
        const warning = document.getElementById('max-seats-warning');
        warning.classList.add('d-none');
    }
    
    updateBookingSummary() {
        const seatsCount = this.selectedSeats.size;
        const totalPrice = seatsCount * this.seatPrice;
        
        const selectedSeatsDiv = document.getElementById('selected-seats');
        const bookingSummary = document.getElementById('booking-summary');
        const bookingForm = document.getElementById('booking-form');
        
        if (seatsCount > 0) {
            const seatLabels = Array.from(this.selectedSeats).map(id => {
                const checkbox = document.querySelector(`[data-seat-id="${id}"]`);
                const row = checkbox.dataset.row;
                const seat = checkbox.dataset.seat;
                return `${row}-${seat}`;
            }).join(', ');
            
            selectedSeatsDiv.innerHTML = `<strong>Обрані місця:</strong> ${seatLabels}`;
            
            document.getElementById('seats-count').textContent = seatsCount;
            document.getElementById('total-price').textContent = totalPrice;
            
            bookingSummary.classList.remove('d-none');
            bookingForm.classList.remove('d-none');
            
            // Оновити модальне вікно
            this.updateConfirmationModal(seatLabels, seatsCount, totalPrice);
        } else {
            selectedSeatsDiv.innerHTML = '<p class="text-muted">Оберіть місця зліва</p>';
            bookingSummary.classList.add('d-none');
            bookingForm.classList.add('d-none');
        }
    }
    
    updateConfirmationModal(seatLabels, seatsCount, totalPrice) {
        const modalDetails = document.getElementById('modal-booking-details');
        modalDetails.innerHTML = `
            <div class="alert alert-info">
                <p><strong>Місця:</strong> ${seatLabels}</p>
                <p><strong>Кількість:</strong> ${seatsCount} квитків</p>
                <p><strong>Загальна сума:</strong> ${totalPrice} грн</p>
            </div>
        `;
    }
    
    async handleFormSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        
        // Перевірка валідності форми
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Показати модальне вікно підтвердження
        const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
        modal.show();
    }
    
    async confirmBooking() {
        const submitButton = document.getElementById('submit-btn');
        const confirmButton = document.getElementById('confirm-booking');
        const originalText = submitButton.textContent;
        
        submitButton.textContent = 'Бронюємо...';
        submitButton.disabled = true;
        confirmButton.textContent = 'Бронюємо...';
        confirmButton.disabled = true;
        
        const formData = {
            session_id: this.sessionId,
            customer_email: document.getElementById('customer_email').value,
            customer_name: document.getElementById('customer_name').value,
            selected_seats: Array.from(this.selectedSeats).map(id => parseInt(id))
        };
        
        try {
            const response = await fetch('/api/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            // Закрити модальне вікно
            const modal = bootstrap.Modal.getInstance(document.getElementById('confirmationModal'));
            modal.hide();
            
            if (result.success) {
                this.showSuccessMessage(result.booking_code, formData.customer_email);
            } else {
                this.showErrorMessage(result.message);
            }
        } catch (error) {
            this.showErrorMessage('Помилка бронювання: ' + error.message);
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            confirmButton.textContent = 'Так, забронювати';
            confirmButton.disabled = false;
        }
    }
    
    showSuccessMessage(bookingCode, email) {
        const message = `✅ Бронювання успішне!\n\nВаш код: ${bookingCode}\nДеталі надіслано на: ${email}\n\nНатисніть OK для переходу до деталей бронювання.`;
        
        if (confirm(message)) {
            window.location.href = `/booking/${bookingCode}`;
        } else {
            window.location.href = '/';
        }
    }
    
    showErrorMessage(message) {
        alert('❌ ' + message);
    }
    
    async loadSeatMap() {
        const loader = document.getElementById('loading-spinner');
        const container = document.getElementById('seats-container');
        
        loader.style.display = 'block';
        container.style.opacity = '0.5';
        
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/seats`);
            const seats = await response.json();
            this.renderSeatMap(seats);
        } catch (error) {
            console.error('Помилка завантаження схеми місць:', error);
            this.showErrorMessage('Не вдалося завантажити схему місць');
        } finally {
            loader.style.display = 'none';
            container.style.opacity = '1';
        }
    }
    
    renderSeatMap(seats) {
        // Цей метод може бути використаний для динамічного оновлення схеми місць
        console.log('Оновлення схеми місць:', seats);
    }
}

// Ініціалізація при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    window.bookingManager = new BookingManager();
});