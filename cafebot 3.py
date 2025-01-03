"""
Модуль для обработки запросов пользователя в боте для заказа еды.

Этот модуль содержит обработчики команд и событий, связанных с меню, корзиной покупок, редактированием товаров в корзине,
и обработкой платежей. Он включает:
- Приветственное сообщение и доступ к основному меню при запуске бота.
- Возможность добавлять, редактировать и удалять товары из корзины.
- Показ содержимого корзины и оформление заказа с суммой покупки.
- Возможность очистки корзины и оплаты заказа.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, BaseFilter
import app.keyboard as kb
from app.cart import cart

router = Router()

# Стартовая команда
@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обрабатывает команду /start.

    Отправляет пользователю приветственное сообщение с его именем и предоставляет доступ к основному меню.

    Args:
        message (Message): Объект сообщения от пользователя, содержащий команду /start.
    """
    await message.answer(
        text=f'Здравствуйте, {message.from_user.first_name}\nЧтобы сделать заказ, нажмите "Меню"',
        reply_markup=await kb.main()
    )

# Списки с полным меню
# Перечисления разделов меню и вложенных категорий
selected_Основное_меню = ['Суп', 'Гарнир', 'Салат', 'Мясное блюдо', '🔙Выбор раздела']
selected_Суп = ['Крем-суп из тыквы', 'Том Ям', 'Минестроне', 'Борщ', '🔙Основное меню']
selected_Салат = ['Цезарь с курицей', 'Греческий салат', 'Оливье', 'Салат с тунцом', '🔙Основное меню']
selected_Мясное_блюдо = ['Стейк из говядины', 'Куриное филе', 'Свинина в соусе BBQ', 'Котлеты по-домашнему', '🔙Основное меню']
selected_Гарнир = ['Картофельное пюре', 'Рис с овощами', 'Гречневая каша', 'Овощи на гриле', '🔙Основное меню']
selected_Комплексные_обеды = ['Традиционный уют', 'Средиземноморский вкус', 'Гурманский рай', '🔙Выбор раздела']
selected_Напитки_и_десерты = ['Горячие напитки', 'Холодные напитки', 'Десерты', '🔙Выбор раздела']
selected_Горячие_напитки = ['Американо', 'Капучино', 'Чай чёрный/зелёный', 'Какао с маршмеллоу', '🔙Напитки и десерты']
selected_Холодные_напитки = ['Домашний лимонад', 'Морс клюквенный', 'Айсти с лимоном', 'Апельсиновый фреш', '🔙Напитки и десерты']
selected_Десерт = ['Чизкейк', 'Тирамису', 'Шоколадный фондан', 'Ягодный тарт', '🔙Напитки и десерты']

# Словарь с продуктами и их ценами
# Ключи — названия продуктов, значения — их стоимость в рублях
products = {
    'Крем-суп из тыквы': 250,
    'Том Ям': 350,
    'Минестроне': 300,
    'Борщ': 200,
    'Цезарь с курицей': 270,
    'Греческий салат': 240,
    'Оливье': 220,
    'Салат с тунцом': 320,
    'Стейк из говядины': 700,
    'Куриное филе': 500,
    'Свинина в соусе BBQ': 550,
    'Котлеты по-домашнему': 400,
    'Картофельное пюре': 100,
    'Рис с овощами': 120,
    'Гречневая каша': 110,
    'Овощи на гриле': 150,
    'Американо': 100,
    'Капучино': 150,
    'Чай чёрный/зелёный': 80,
    'Какао с маршмеллоу': 130,
    'Домашний лимонад': 120,
    'Морс клюквенный': 100,
    'Айсти с лимоном': 90,
    'Апельсиновый фреш': 200,
    'Чизкейк': 300,
    'Тирамису': 350,
    'Шоколадный фондан': 400,
    'Ягодный тарт': 320,
}

# Функция для получения текста меню по заданному разделу
def get_menu_text(category):
    """
    Формирует текст для отображения меню в зависимости от выбранной категории.

    Args:
        category (str): Название категории (например, 'Суп', 'Гарнир').

    Returns:
        str: Отформатированный текст меню с перечислением доступных продуктов.
    """
    items = globals().get(f'selected_{category}', [])
    return '\n'.join(items)

# Функция для обработки нажатий на кнопки меню
@router.callback_query(F.data.startswith("menu_"))
async def process_menu_callback(callback_query: CallbackQuery):
    """
    Обрабатывает нажатия кнопок в меню.

    Определяет категорию по полученным данным и отправляет пользователю текст меню с кнопками.

    Args:
        callback_query (CallbackQuery): Объект нажатия кнопки в меню.
    """
    category = callback_query.data.split("_")[1]
    menu_text = get_menu_text(category)
    await callback_query.message.edit_text(
        text=menu_text,
        reply_markup=await kb.menu(category)
    )

# Обработчик для добавления продукта в корзину
@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback_query: CallbackQuery):
    """
    Добавляет выбранный продукт в корзину пользователя.

    Args:
        callback_query (CallbackQuery): Объект нажатия кнопки на добавление продукта.
    """
    product_name = callback_query.data.split("_")[1]
    product_price = products.get(product_name, 0)
    cart.add(callback_query.from_user.id, product_name, product_price)
    await callback_query.answer(f"{product_name} добавлен в корзину.")

# Обработчик для очистки корзины
@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback_query: CallbackQuery):
    """
    Очищает корзину пользователя.

    Args:
        callback_query (CallbackQuery): Объект нажатия кнопки очистки корзины.
    """
    cart.clear(callback_query.from_user.id)
    await callback_query.answer("Корзина очищена.")

# Обработчик для оформления заказа
@router.callback_query(F.data == "checkout")
async def checkout(callback_query: CallbackQuery):
    """
    Оформляет заказ пользователя.

    Выводит содержимое корзины с общей суммой и предложением оплатить.

    Args:
        callback_query (CallbackQuery): Объект нажатия кнопки оформления заказа.
    """
    order, total_price = cart.get_order(callback_query.from_user.id)
    if not order:
        await callback_query.answer("Корзина пуста.")
    else:
        await callback_query.message.edit_text(
            text=f"Ваш заказ:\n{order}\nСумма: {total_price} руб.",
            reply_markup=await kb.payment()
        )
# Обработчик для подтверждения оплаты
@router.callback_query(F.data == "pay")
async def process_payment(callback_query: CallbackQuery):
    """
    Подтверждает оплату заказа.

    Завершает процесс заказа и отправляет пользователю сообщение об успешной оплате.

    Args:
        callback_query (CallbackQuery): Объект нажатия кнопки оплаты.
    """
    cart.clear(callback_query.from_user.id)  # Очистка корзины после успешной оплаты
    await callback_query.message.edit_text(
        text="Оплата прошла успешно! Спасибо за заказ."
    )

# Общий обработчик неизвестных команд
@router.message()
async def fallback(message: Message):
    """
    Обрабатывает неизвестные команды или текстовые сообщения.

    Выводит сообщение с предложением использовать доступное меню.

    Args:
        message (Message): Объект сообщения от пользователя.
    """
    await message.answer(
        text="Извините, я вас не понял. Используйте меню для взаимодействия."
    )

# Регистрация всех обработчиков в маршрутизаторе
def setup(router: Router):
    """
    Регистрирует все обработчики в маршрутизаторе.

    Args:
        router (Router): Объект маршрутизатора для регистрации обработчиков.
    """
