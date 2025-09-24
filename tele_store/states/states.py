from aiogram.fsm.state import State, StatesGroup


class RegNewUser(StatesGroup):
    name = State()
    phone_number = State()
    address = State()
    delivery_method = State()
    confirm = State()


class AddNewItem(StatesGroup):
    name = State()
    description = State()
    price = State()
    category_id = State()
    photo_file_id = State()
    confirm = State()
