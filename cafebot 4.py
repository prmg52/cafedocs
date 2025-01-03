# c 87 по 160 стр
user_cart = {}
order_counter = 1


@router.callback_query(F.data == 'redact_quantity')
async def edit_quantity_handler(callback: CallbackQuery):
    """
    Обработчик для редактирования количества товаров в корзине.

    Если корзина пуста, отправляет уведомление пользователю.
    Если корзина не пуста, показывает список товаров для редактирования.
    """
    user_cart = cart.user_carts.get(callback.from_user.id, {})
    if not user_cart:
        # Сообщение пользователю о пустой корзине
        await callback.answer('Ваша корзина пуста.')
        return
    # Вывод сообщения с кнопками для редактирования товаров
    await callback.message.edit_text(
        text='Выберите товар для редактирования:',
        reply_markup=await kb.create_edit_quantity_buttons(user_cart)
    )


@router.callback_query(F.data.startswith('edit_'))
async def edit_product_handler(callback: CallbackQuery):
    """
    Обработчик выбора конкретного товара для изменения его количества.

    Отправляет сообщение с кнопками для изменения количества выбранного товара.
    """
    product = callback.data[len('edit_'):].replace('_', ' ')
    # Отправка сообщения с кнопками изменения количества для выбранного товара
    await callback.message.edit_text(
        text=f"Изменение количества для {product}:",
        reply_markup=await kb.quantity_buttons(product)
    )


@router.callback_query(F.data.startswith('increase_'))
async def increase_quantity_handler(callback: CallbackQuery):
    """
    Обработчик для увеличения количества выбранного товара.

    Увеличивает количество товара на единицу и обновляет интерфейс.
    """
    product = callback.data[len('increase_'):]
    cart.edit_quantity(callback.from_user.id, product, change=1)
    # Сообщение пользователю об увеличении количества
    await callback.answer('Количество увеличено.')
    # Обновление кнопок изменения количества
    await callback.message.edit_reply_markup(reply_markup=await kb.quantity_buttons(product))


@router.callback_query(F.data.startswith('decrease_'))
async def decrease_quantity_handler(callback: CallbackQuery):
    """
    Обработчик для уменьшения количества выбранного товара.

    Уменьшает количество товара на единицу. Если количество достигает нуля,
    удаляет товар из корзины и обновляет список товаров для редактирования.
    """
    product = callback.data[len('decrease_'):]
    cart.edit_quantity(callback.from_user.id, product, change=-1)
    if product not in cart.user_carts[callback.from_user.id]:
        # Удаление товара из корзины
        await callback.message.edit_text(
            text='Выберите товар для редактирования:',
            reply_markup=await kb.create_edit_quantity_buttons(
                cart.user_carts[callback.from_user.id]
            )
        )
        # Уведомление об удалении товара
        await callback.answer('Товар удалён из корзины.')
    else:
        # Уведомление об уменьшении количества
        await callback.answer('Количество уменьшено.')
        # Обновление кнопок изменения количества
        await callback.message.edit_reply_markup(reply_markup=await kb.quantity_buttons(product))


@router.callback_query(F.data == 'pay_cart')
async def pay_cart_handler(callback: CallbackQuery):
    """
    Обработчик оплаты корзины.

    Проверяет наличие товаров в корзине. Если корзина пуста, уведомляет пользователя.
    Если товары есть, формирует заказ, выводит его в консоль и очищает корзину.
    """
    global order_counter
    user_id = callback.from_user.id
    cart_content = cart.user_carts.get(user_id)
    if not cart_content:
        # Уведомление о пустой корзине
        await callback.answer('Корзина пуста, нечего оплачивать.')
        return

    # Расчет общей стоимости и детализации заказа
    total_price = cart.get_total_price(user_id)
    order_details = '\n'.join(
        f"- {product}: {info['quantity']} шт. x {info['price']} руб = {info['quantity'] * info['price']} руб"
        for product, info in cart_content.items()
    )

    # Формирование информации о заказе
    order_info = (f"У вас новый заказ:\n"
                  f"Номер заказа: {order_counter}\n"
                  f"Имя покупателя: {callback.from_user.first_name or 'Неизвестно'}\n"
                  f"ID покупателя: {user_id}\n"
                  f"Состав заказа:\n{order_details}\n"
                  f"Общая стоимость: {total_price} руб\n")

    # Вывод информации о заказе в консоль
    print(order_info)
    # Очистка корзины пользователя
    cart.clear(user_id)
    # Уведомление об успешной оплате
    await callback.message.edit_text(
        text=f'Спасибо за оплату! Ваш номер заказа: {order_counter}',
        reply_markup=await kb.to_new_order()
    )
    order_counter += 1



# c 163 по 218 стр
@router.callback_query(F.data == 'clear_cart')
async def clear_cart_handler(callback: CallbackQuery):
    """
    Обработчик запроса на очистку корзины.

    Показывает подтверждающее сообщение с кнопками для подтверждения или отмены очистки корзины.
    """
    await callback.message.edit_text(
        text='Вы уверены, что хотите очистить корзину?',
        reply_markup=await kb.create_clear_cart_buttons()
    )


@router.callback_query(F.data == 'confirm_clear_cart')
async def confirm_clear_cart(callback: CallbackQuery):
    """
    Обработчик подтверждения очистки корзины.

    Очищает корзину пользователя и уведомляет его об успешной операции.
    """
    cart.clear(callback.from_user.id)
    await callback.message.edit_text(text='Корзина успешно очищена.')


@router.message(F.text == 'Корзина')
async def cart_handler(message: Message):
    """
    Обработчик команды 'Корзина'.

    Показывает содержимое корзины пользователя с соответствующими кнопками.
    """
    cart_info = cart.show(message.from_user.id)
    await message.reply(cart_info, reply_markup=await kb.cart_buttons())


@router.callback_query(F.data.in_({'selected_Перейти_в_корзину', 'back_to_cart'}))
async def back_to_cart_handler(callback: CallbackQuery):
    """
    Обработчик для возврата в корзину.

    Отображает текущее содержимое корзины пользователя с кнопками управления.
    """
    cart_info = cart.show(callback.from_user.id)
    await callback.message.edit_text(cart_info, reply_markup=await kb.cart_buttons())


class ProductFilter(BaseFilter):
    """
    Фильтр для обработки выбора товаров.

    Проверяет, содержится ли выбранный товар в списке доступных товаров.
    """

    def __init__(self, products: dict):
        self.products = products

    async def __call__(self, callback: CallbackQuery) -> bool:
        """
        Проверяет, относится ли входящий callback к доступным товарам.

        Args:
            callback (CallbackQuery): Входящий callback

        Returns:
            bool: True, если товар найден в списке, иначе False.
        """
        data = callback.data
        if data.startswith("selected_"):
            product_name = data[len("selected_"):]  # Убираем префикс "selected_"
            product_name = product_name.replace('_', ' ')
            return product_name in self.products  # Проверяем, есть ли ключ в словаре
        return False


@router.callback_query(ProductFilter(products))
async def handle_product_selection(callback: CallbackQuery):
    """
    Обработчик выбора товара.

    Добавляет выбранный товар в корзину, уведомляет пользователя и обновляет информацию о корзине.
    """
    product_name = callback.data[len("selected_"):]
    product_name = product_name.replace('_', ' ')
    product_price = products[product_name]
    cart.add(callback.from_user.id, product_name, product_price)
    # Уведомление пользователя о добавлении товара
    await callback.answer(f"{product_name} добавлен в корзину")
    # Обновление информации о корзине
    cart_info = cart.show(callback.from_user.id)
    await callback.message.edit_text(cart_info, reply_markup=await kb.added())


@router.message(F.text == 'Меню')
async def menu(message: Message):
    """
    Обработчик команды 'Меню'.

    Отображает разделы меню с кнопками для выбора.
    """
    await message.reply(text='Выберите раздел меню', reply_markup=await kb.options())


@router.callback_query(F.data.in_({'selected_🔙Выбор_раздела', 'selected_Сделать_еще_заказ'}))
async def menu(callback: CallbackQuery):
    """
    Обработчик для возврата к разделам меню.

    Показывает сообщение с кнопками выбора разделов.
    """
    await callback.message.edit_text(text='Выберите раздел меню', reply_markup=await kb.options())




# c 220 по 337 стр
@router.callback_query(F.data.in_({'selected_Основное_меню', 'selected_🔙Основное_меню'}))
async def main_menu(callback: CallbackQuery):
    """
    Обработчик выбора основного меню.

    Уведомляет пользователя о выборе и отображает категории основного меню с кнопками.
    """
    await callback.answer(text='Вы выбрали основное меню')
    await callback.message.edit_text(
        text='Выберите категорию:',
        reply_markup=await kb.create_buttons(selected_Основное_меню)
    )


@router.callback_query(F.data.in_({'selected_Напитки_и_десерты', 'selected_🔙Напитки_и_десерты'}))
async def handle_drinks_desserts(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Напитки и десерты'.

    Уведомляет пользователя и отображает список доступных напитков и десертов.
    """
    await callback.answer(text='Вы выбрали напитки и десерты')
    await callback.message.edit_text(
        text='Выберите напиток или десерт:',
        reply_markup=await kb.create_buttons(selected_Напитки_и_десерты)
    )


@router.callback_query(F.data == 'selected_Комплексные_обеды')
async def set_meals(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Комплексные обеды'.

    Уведомляет пользователя и отображает меню с описанием и ценами комплексных обедов.
    """
    await callback.answer(text='Вы выбрали комплексные обеды')
    await callback.message.edit_text(
        text='''Комплексный обед №1 - 
Традиционный уют
Состав:
1. Борщ (400 мл)
2. Цезарь с курицей (200 г)
3. Куриное филе (200 г)
4. Картофельное пюре (200 г)

Цена: 950 руб.

Комплексный обед №2 - 
Средиземноморский вкус
Состав:
1. Крем-суп из тыквы (300 мл)
2. Греческий салат (250 г)
3. Свинина в соусе BBQ (250 г)
4. Рис с овощами (180 г)

Цена: 1070 руб.

Комплексный обед №3 - 
Гурманский рай
Состав:
1. Том Ям (350 мл)
2. Салат Оливье (220 г)
3. Стейк из говядины (250 г)
4. Овощи на гриле (220 г)

Цена: 1350 руб.''',
        reply_markup=await kb.create_buttons(selected_Комплексные_обеды)
    )


@router.callback_query(F.data == 'selected_Суп')
async def soup(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Супы'.

    Уведомляет пользователя и отображает меню супов с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали супы')
    await callback.message.edit_text(
        text='''Крем-суп из тыквы
Нежный крем-суп из запечённой тыквы, с добавлением сливок и лёгкими нотками мускатного ореха.
Объем порции: 300 мл
Цена: 250 руб. 

Том Ям
Тайский острый суп с креветками и грибами в кокосовом молоке, с ароматом лайма и лемонграсса
Объем порции: 350 мл
Цена: 250 руб. 

Минестроне
Итальянский овощной суп с пастой или рисом, приготовленный на основе сезонных овощей
Объем порции: 400 мл
Цена: 220 руб. 

Борщ
Классический свекольный суп на мясном бульоне с капустой и картофелем, подаётся со сметаной
Объем порции: 400 мл
Цена: 200 руб. ''',
        reply_markup=await kb.create_buttons(selected_Суп)
    )


@router.callback_query(F.data == 'selected_Салат')
async def salad(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Салаты'.

    Уведомляет пользователя и отображает меню салатов с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали салаты')
    await callback.message.edit_text(
        text='''Цезарь с курицей
Классический салат с куриной грудкой, листьями салата ромэн, пармезаном, сухариками и соусом цезарь.
Объем порции: 200 г
Цена: 150 руб. 

Греческий салат
Свежие овощи (помидоры, огурцы, болгарский перец) с оливками, фетой и орегано, заправленный оливковым маслом.
Объем порции: 250 г
Цена: 120 руб. 

Оливье
Традиционный салат с отварным картофелем, морковью, солёными огурцами, яйцом, горошком и майонезом.
Объем порции: 220 г
Цена: 100 руб. 

Салат с тунцом
Лёгкий салат из микса зелёных листьев, тунца, отварных яиц, черри и оливок с оливковым маслом.
Объем порции: 180 г
Цена: 120 руб. ''',
        reply_markup=await kb.create_buttons(selected_Салат)
    )


@router.callback_query(F.data == 'selected_Мясное_блюдо')
async def meat(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Мясные блюда'.

    Уведомляет пользователя и отображает меню мясных блюд с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали мясные блюда')
    await callback.message.edit_text(
        text='''Стейк из говядины
Сочный стейк средней прожарки, подается с ароматным травяным маслом или соусом.
Объем порции: 250 г
Цена: 350 руб. 

Куриное филе
Запечённое куриное филе с травами и специями, подаётся с лёгким соусом.
Объем порции: 200 г
Цена: 200 руб. 

Свинина в соусе BBQ
Обжаренные кусочки свинины, тушенные в пряном соусе BBQ до мягкости и сочности.
Объем порции: 250 г
Цена: 250 руб. 

Котлеты по-домашнему
Домашние мясные котлеты из говядины и свинины, обжаренные до золотистой корочки.
Объем порции: 180 г
Цена: 200 руб. ''',
        reply_markup=await kb.create_buttons(selected_Мясное_блюдо)
    )



# c 340 и до конца
@router.callback_query(F.data == 'selected_Гарнир')
async def side_dishes(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Гарниры'.

    Уведомляет пользователя и отображает меню гарниров с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали гарниры')
    await callback.message.edit_text(
        text='''Картофельное пюре
Нежное картофельное пюре с добавлением сливок и масла.
Объем порции: 200 г
Цена: 150 руб. 

Рис с овощами
Белый рис, обжаренный с морковью, горошком и кукурузой, с лёгкими специями.
Объем порции: 180 г
Цена: 140 руб. 

Гречневая каша
Классическая гречневая каша, приготовленная на воде или бульоне, слегка посоленная.
Объем порции: 200 г
Цена: 130 руб. 

Овощи на гриле
Ассорти из обжаренных на гриле овощей: кабачки, баклажаны, перец и грибы, с добавлением специй.
Объем порции: 220 г
Цена: 180 руб.''',
        reply_markup=await kb.create_buttons(selected_Гарнир)
    )


@router.callback_query(F.data == 'selected_Десерты')
async def desserts(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Десерты'.

    Уведомляет пользователя и отображает меню десертов с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали десерты')
    await callback.message.edit_text(
        text='''Чизкейк Нью-Йорк
Классический чизкейк на основе сливочного сыра, с мягкой текстурой и печёной корочкой.
Объем порции: 150 г 
Цена: 300 руб. 

Тирамису
Итальянский десерт с кремом маскарпоне, пропитанный кофе и украшенный какао.
Объем порции: 120 г
Цена: 280 руб. 

Шоколадный фондан
Тёплый шоколадный пирог с жидким центром, подаётся с шариком ванильного мороженого.
Объем порции: 120 г 
Цена: 350 руб. 

Ягодный тарт
Лёгкий пирог с основой из песочного теста и начинкой из свежих ягод и крема.
Объем порции: 130 г 
Цена: 250 руб. ''',
        reply_markup=await kb.create_buttons(selected_Десерт)
    )


@router.callback_query(F.data == 'selected_Холодные_напитки')
async def cold_drinks(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Холодные напитки'.

    Уведомляет пользователя и отображает меню холодных напитков с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали холодные напитки')
    await callback.message.edit_text(
        text='''Домашний лимонад
Освежающий лимонад с мятой, лимоном и натуральными фруктовыми добавками.
Объем: 300 мл
Цена: 150 руб. 

Морс клюквенный
Классический клюквенный морс, приготовленный из свежих ягод и слегка подслащенный.
Объем: 250 мл
Цена: 120 руб. 

Айсти с лимоном
Холодный черный чай с добавлением свежего лимона и мяты для бодрости.
Объем: 300 мл
Цена: 130 руб. 

Апельсиновый фреш
Свежевыжатый сок из апельсинов для быстрого заряда витаминами и энергией.
Объем: 200 мл
Цена: 200 руб. ''',
        reply_markup=await kb.create_buttons(selected_Холодные_напитки)
    )


@router.callback_query(F.data == 'selected_Горячие_напитки')
async def hot_drinks(callback: CallbackQuery):
    """
    Обработчик выбора раздела 'Горячие напитки'.

    Уведомляет пользователя и отображает меню горячих напитков с описанием и ценами.
    """
    await callback.answer(text='Вы выбрали горячие напитки')
    await callback.message.edit_text(
        text='''Американо
Классический черный кофе средней крепости, приготовленный на основе эспрессо.
Объем: 200 мл
Цена: 100 руб. 

Капучино
Кофе с мягким вкусом, покрытый нежной пенкой из взбитого молока.
Объем: 250 мл
Цена: 150 руб. 

Чай чёрный/зелёный
Классический чёрный или зелёный чай, заваренный из натуральных чайных листьев.
Объем: 300 мл
Цена: 80 руб. 

Какао с маршмеллоу
Горячий шоколадный напиток, украшенный мягкими маршмеллоу, для сладкого уюта.
Объем: 250 мл
Цена: 180 руб. ''',
        reply_markup=await kb.create_buttons(selected_Горячие_напитки)
    )