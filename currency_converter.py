import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from threading import Thread

class CurrencyConverter:
    """Основной класс приложения конвертера валют"""

    # API ключ (бесплатный, зарегистрируйтесь на https://app.exchangerate-api.com/sign-up)
    API_KEY = "ваш_api_ключ"  # Замените на свой ключ
    API_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/"

    # Список популярных валют
    CURRENCIES = [
        "USD", "EUR", "RUB", "GBP", "CNY", "JPY",
        "CAD", "CHF", "AUD", "TRY", "UAH", "KZT"
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Данные для конвертации
        self.exchange_rates = {}
        self.history = []
        self.history_file = "history.json"

        # Загрузка истории
        self.load_history()

        # Создание интерфейса
        self.create_widgets()

        # Загрузка курсов валют при старте
        self.update_rates()

    def create_widgets(self):
        """Создание GUI интерфейса"""

        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Заголовок
        title_label = ttk.Label(main_frame, text="💱 Конвертер валют",
                                font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Информация о курсах
        self.status_label = ttk.Label(main_frame, text="Загрузка курсов валют...",
                                      foreground="blue")
        self.status_label.grid(row=1, column=0, columnspan=4, pady=5)

        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0,
                                                            columnspan=4, sticky=(tk.W, tk.E), pady=10)

        # Фрейм для конвертации
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация", padding="10")
        convert_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)

        # Сумма
        ttk.Label(convert_frame, text="Сумма:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(convert_frame, font=("Arial", 12), width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        # Из валюты
        ttk.Label(convert_frame, text="Из валюты:", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5)
        self.from_currency = ttk.Combobox(convert_frame, values=self.CURRENCIES,
                                          font=("Arial", 12), width=8, state="readonly")
        self.from_currency.grid(row=0, column=3, padx=5, pady=5)
        self.from_currency.set("USD")

        # Стрелка
        ttk.Label(convert_frame, text="→", font=("Arial", 16)).grid(row=0, column=4, padx=5, pady=5)

        # В валюту
        ttk.Label(convert_frame, text="В валюту:", font=("Arial", 12)).grid(row=0, column=5, padx=5, pady=5)
        self.to_currency = ttk.Combobox(convert_frame, values=self.CURRENCIES,
                                        font=("Arial", 12), width=8, state="readonly")
        self.to_currency.grid(row=0, column=6, padx=5, pady=5)
        self.to_currency.set("EUR")

        # Кнопка конвертации
        self.convert_btn = ttk.Button(convert_frame, text="Конвертировать",
                                      command=self.convert_currency, width=15)
        self.convert_btn.grid(row=0, column=7, padx=10, pady=5)

        # Результат конвертации
        self.result_label = ttk.Label(convert_frame, text="", font=("Arial", 14, "bold"),
                                      foreground="green")
        self.result_label.grid(row=1, column=0, columnspan=8, pady=10)

        # Фрейм для истории
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Таблица истории
        columns = ("Дата", "Сумма", "Из", "В", "Результат", "Курс")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)

        # Настройка колонок
        widths = [150, 100, 70, 70, 120, 100]
        for col, width in zip(columns, widths):
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=width)

        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Кнопки управления историей
        button_frame = ttk.Frame(history_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Очистить историю",
                   command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Обновить курсы",
                   command=self.update_rates).pack(side=tk.LEFT, padx=5)

        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        # Привязка клавиши Enter к конвертации
        self.amount_entry.bind('<Return>', lambda event: self.convert_currency())

    def update_rates(self):
        """Обновление курсов валют из API"""
        self.convert_btn.config(state="disabled", text="Загрузка...")
        self.status_label.config(text="Загрузка курсов валют...", foreground="blue")

        # Запуск в отдельном потоке
        Thread(target=self._fetch_rates, daemon=True).start()

    def _fetch_rates(self):
        """Получение курсов валют из API"""
        try:
            # Используем USD как базовую валюту
            response = requests.get(f"{self.API_URL}USD", timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("result") == "success":
                self.exchange_rates = data.get("conversion_rates", {})
                self.root.after(0, self._on_rates_success)
            else:
                self.root.after(0, self._on_rates_error, "API вернул ошибку")

        except requests.exceptions.RequestException as e:
            self.root.after(0, self._on_rates_error, f"Ошибка сети: {str(e)}")
        except Exception as e:
            self.root.after(0, self._on_rates_error, f"Ошибка: {str(e)}")

    def _on_rates_success(self):
        """Обработка успешной загрузки курсов"""
        self.convert_btn.config(state="normal", text="Конвертировать")
        self.status_label.config(text=f"✅ Курсы обновлены ({datetime.now().strftime('%H:%M:%S')})",
                                 foreground="green")
        messagebox.showinfo("Успех", "Курсы валют успешно обновлены!")

    def _on_rates_error(self, error_msg):
        """Обработка ошибки загрузки курсов"""
        self.convert_btn.config(state="normal", text="Конвертировать")
        self.status_label.config(text="❌ Ошибка загрузки курсов", foreground="red")
        messagebox.showerror("Ошибка", f"Не удалось загрузить курсы валют:\n{error_msg}")

    def convert_currency(self):
        """Конвертация валюты"""
        # Проверка наличия курсов
        if not self.exchange_rates:
            messagebox.showwarning("Предупреждение", "Сначала обновите курсы валют")
            return

        # Получение и валидация суммы
        try:
            amount = float(self.amount_entry.get().replace(',', '.'))

            # Негативный тест: отрицательная сумма
            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом!")
                return

        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число!")
            return

        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        # Проверка наличия курсов для выбранных валют
        if from_curr not in self.exchange_rates or to_curr not in self.exchange_rates:
            messagebox.showerror("Ошибка", "Курс для выбранной валюты не найден!")
            return

        # Конвертация
        try:
            # Сначала конвертируем в USD (базовая валюта), затем в целевую
            if from_curr == "USD":
                usd_amount = amount
            else:
                usd_amount = amount / self.exchange_rates[from_curr]

            if to_curr == "USD":
                result = usd_amount
            else:
                result = usd_amount * self.exchange_rates[to_curr]

            # Округление до 2 знаков
            result = round(result, 2)

            # Отображение результата
            self.result_label.config(
                text=f"{amount:.2f} {from_curr} = {result:.2f} {to_curr}"
            )

            # Сохранение в историю
            rate = self.exchange_rates[to_curr] / self.exchange_rates[from_curr]
            self.add_to_history(amount, from_curr, to_curr, result, round(rate, 4))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка конвертации: {str(e)}")

    def add_to_history(self, amount, from_curr, to_curr, result, rate):
        """Добавление записи в историю"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": result,
            "rate": rate
        }

        self.history.append(entry)

        # Ограничение истории (последние 100 записей)
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # Обновление таблицы
        self.update_history_display()

        # Сохранение в файл
        self.save_history()

    def update_history_display(self):
        """Обновление отображения истории"""
        # Очистка таблицы
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Добавление записей (от новых к старым)
        for entry in reversed(self.history):
            self.history_tree.insert("", 0, values=(
                entry["timestamp"],
                f"{entry['amount']:.2f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.2f}",
                f"{entry['rate']:.4f}"
            ))

    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    def load_history(self):
        """Загрузка истории из JSON файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки истории: {e}")
                self.history = []

    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.update_history_display()
            self.save_history()
            messagebox.showinfo("Успех", "История очищена")

def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
