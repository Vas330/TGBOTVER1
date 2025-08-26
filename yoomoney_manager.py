# yoomoney_manager.py - менеджер платежей через YooMoney
import qrcode
from io import BytesIO
import uuid
from datetime import datetime, timedelta


class YooMoneyManager:
    def __init__(self, shop_id: str, secret_key: str):
        """Инициализация YooMoney менеджера

        Args:
            shop_id: ID магазина в YooMoney
            secret_key: Секретный ключ магазина
        """
        self.shop_id = shop_id
        self.secret_key = secret_key

    def generate_payment_data(self, order_id: str, amount: float, description: str) -> dict:
        """Генерирует данные для платежа

        Args:
            order_id: ID заказа
            amount: Сумма платежа
            description: Описание платежа

        Returns:
            dict: Данные для платежа
        """
        payment_id = str(uuid.uuid4())

        payment_data = {
            'payment_id': payment_id,
            'order_id': order_id,
            'amount': amount,
            'description': description,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),  # Действителен 24 часа
            'status': 'pending'
        }

        return payment_data

    def generate_qr_code(self, payment_data: dict) -> BytesIO:
        """Генерирует QR-код для оплаты

        Args:
            payment_data: Данные платежа

        Returns:
            BytesIO: QR-код в виде изображения
        """
        # Формируем URL для оплаты YooMoney
        payment_url = self._create_payment_url(payment_data)

        # Создаем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)

        # Генерируем изображение
        img = qr.make_image(fill_color="black", back_color="white")

        # Конвертируем в BytesIO
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)

        return bio

    def _create_payment_url(self, payment_data: dict) -> str:
        """Создает URL для оплаты YooMoney

        Args:
            payment_data: Данные платежа

        Returns:
            str: URL для оплаты
        """
        # Для прямых переводов на кошелек YooMoney
        # Используем ваш номер кошелька: 4100 1192 9714 3661
        wallet_number = "410011929714361"  # Ваш номер кошелька без пробелов

        # Базовый URL YooMoney для переводов на кошелек
        base_url = "https://yoomoney.ru/quickpay/confirm.xml"

        # Параметры платежа
        params = {
            'receiver': wallet_number,
            'quickpay-form': 'small',
            'targets': payment_data['description'],
            'sum': payment_data['amount'],
            'label': payment_data['payment_id'],
            'comment': f"Заказ {payment_data['order_id']}"
        }

        # Формируем URL с параметрами
        url_params = '&'.join([f"{key}={value}" for key, value in params.items()])
        payment_url = f"{base_url}?{url_params}"

        return payment_url

    def create_payment_message(self, payment_data: dict, order_title: str) -> str:
        """Создает текст сообщения с информацией об оплате

        Args:
            payment_data: Данные платежа
            order_title: Название заказа

        Returns:
            str: Текст сообщения
        """
        message = f"""💳 ОПЛАТА ЗАКАЗА

📋 Заказ: {order_title}
💰 Сумма: {payment_data['amount']:.0f} руб.
🆔 Номер платежа: {payment_data['payment_id'][:8]}...

📱 Отсканируйте QR-код для оплаты через YooMoney
⏰ Действителен до: {payment_data['expires_at'].strftime('%d.%m.%Y %H:%M')}

После оплаты напишите слово "оплатил" для подтверждения."""

        return message

    def verify_payment(self, payment_id: str) -> bool:
        """Проверяет статус платежа

        Note: В реальном приложении здесь должна быть интеграция с API YooMoney
        для проверки статуса платежа. Сейчас возвращаем True для демонстрации.

        Args:
            payment_id: ID платежа

        Returns:
            bool: Статус оплаты
        """
        # В реальном приложении здесь будет запрос к API YooMoney
        # Пока возвращаем True для тестирования
        return True

    def get_payment_info(self, payment_id: str) -> dict:
        """Получает информацию о платеже

        Args:
            payment_id: ID платежа

        Returns:
            dict: Информация о платеже
        """
        # В реальном приложении здесь будет запрос к API YooMoney
        return {
            'payment_id': payment_id,
            'status': 'succeeded',
            'paid_at': datetime.now(),
            'amount': 0.0
        }