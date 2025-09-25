from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from aiogram import F, Router

from tele_store.keyboards.inline.add_category_confirm_menu import (
    add_category_confirm_keyboard,
)
from tele_store.keyboards.inline.add_item_confirm_menu import add_item_confirm_keyboard
from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.states.states import AddNewCategory, AddNewItem

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)


@router.message(AddNewItem.name)
async def add_new_item_name(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        await message.answer("❌ Название не может быть пустым. Введите снова:")
        return

    await state.update_data(name=text)
    await state.set_state(AddNewItem.description)
    await message.answer("Опишите товар:", reply_markup=cancel_key())


@router.message(AddNewItem.description)
async def add_new_item_description(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        await message.answer("❌ Описание не может быть пустым. Введите снова:")
        return

    await state.update_data(description=text)
    await state.set_state(AddNewItem.price)
    await message.answer(
        "Введите цену товара (число больше 0):", reply_markup=cancel_key()
    )


@router.message(AddNewItem.price)
async def add_new_item_price(message: Message, state: FSMContext) -> None:
    try:
        price = Decimal(message.text.strip())
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Неверный формат цены. Введите число больше 0:")
        return

    await state.update_data(price=price)
    await state.set_state(AddNewItem.category_id)
    await message.answer(
        "Укажите категорию товара числом (ID):", reply_markup=cancel_key()
    )


@router.message(AddNewItem.category_id)
async def add_new_item_category(message: Message, state: FSMContext) -> None:
    text = message.text.strip()

    if not text.isdigit():
        await message.answer("❌ Категория должна быть числом (ID). Введите снова:")
        return

    category_id = int(text)
    if category_id <= 0:
        await message.answer(
            "❌ ID категории должен быть положительным числом. Введите снова:"
        )
        return

    await state.update_data(category_id=category_id)
    await state.set_state(AddNewItem.photo_file_id)
    await message.answer("Отправьте фото товара:", reply_markup=cancel_key())


@router.message(AddNewItem.photo_file_id, F.photo)
async def add_new_item_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await state.set_state(AddNewItem.confirm)

    data = await state.get_data()
    preview = (
        f"📦 <b>Новый товар</b>\n\n"
        f"Название: {data['name']}\n"
        f"Описание: {data['description']}\n"
        f"Цена: {data['price']}\n"
        f"Категория: {data['category_id']}\n\n"
        "Подтвердить добавление?"
    )
    await message.answer_photo(
        photo.file_id, caption=preview, reply_markup=add_item_confirm_keyboard()
    )


@router.message(AddNewItem.photo_file_id)
async def add_new_item_photo_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("❌ Нужно отправить именно фото. Попробуйте снова.")


@router.message(AddNewCategory.name)
async def add_new_category_name(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        await message.answer("❌ Название не может быть пустым. Введите снова:")
        return

    await state.update_data(name=text)
    await state.set_state(AddNewCategory.description)
    await message.answer("Опишите категорию:", reply_markup=cancel_key())


@router.message(AddNewCategory.description)
async def add_new_category_description(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        await message.answer("❌ Описание не может быть пустым. Введите снова:")
        return

    await state.update_data(description=text)
    await state.set_state(AddNewCategory.confirm)
    data = await state.get_data()
    preview = (
        f"📦 <b>Новая категория</b>\n\n"
        f"Название: {data['name']}\n"
        f"Описание: {data['description']}\n"
        "Подтвердить добавление?"
    )
    await message.answer(text=preview, reply_markup=add_category_confirm_keyboard())
