"""Finite State Machine (FSM) states for chat-based Writing and Speaking practice."""

from aiogram.fsm.state import State, StatesGroup


class ExamSessionStates(StatesGroup):
    """Step-by-step FSM states for practising Writing or Speaking in Telegram."""

    choosing_exam_type = State()
    choosing_exam_mode = State()
    submitting_writing_task_1 = State()
    submitting_writing_task_2 = State()
    answering_speaking = State()


__all__ = ["ExamSessionStates"]
